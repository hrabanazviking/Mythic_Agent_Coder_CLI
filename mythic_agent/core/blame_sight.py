"""Blame and history sight (roadmap slice M-092).

Part IV - The Editor's Hand. The roadmap's words:
``"why is this line like this?" - blame + the
journal's own record of the session that wrote it.``

What already shipped, and what this slice adds:

* Git already knows who last touched every line, and
  the tool already keeps its own records: the
  EditJournal (M-072's line) remembers each edit the
  agent applied, and every session records its events.
  But the two halves never met. A user staring at a
  strange line could run raw ``git blame`` outside the
  tool and get a commit hash with no story, or dig
  through session records with no line to anchor them
  to. Neither road answers the question actually
  asked: *why is this line like this?*
* This slice is that answer, as a pure layer. It
  parses ``git blame --porcelain`` - the stable,
  machine-readable form - into one record per line
  (commit, author, time, summary, the line itself),
  and it matches a line against journal entries (the
  tool's own record of its edits and session events):
  the entries that name the same file and cover the
  same line name the session that wrote it. Blame
  says which commit; the journal says which session.
  This module runs no git, reads no journal and
  writes nothing; the agent layer owns the real
  ``git blame`` run and the real journal read.

Honesty rules, enforced here and pinned by tests:

* **Blame is parsed, never invented.** Porcelain the
  parser cannot read raises in plain words - a header
  with no content line, a content line with no header,
  a commit whose author record never arrived. No line
  is ever attributed to a commit or an author the
  porcelain did not name.
* **Not committed yet is said out loud.** A line the
  working tree has not committed blames to the
  all-zero commit; it is flagged ``uncommitted`` and
  the explanation says the working tree wrote it and
  git names no commit - never dressed up as history.
* **The journal speaks only where it reaches.** A
  journal entry names the writing session only when
  it names the same file *and* covers the line. A
  file-level record (no line span) is reported as
  exactly that - the journal holds records for the
  file but none that covers this line - and when no
  record reaches the line, the answer says blame
  alone speaks. A session is never guessed.
* **Newest record wins, in journal order.** Journal
  entries arrive in the order they were written; the
  last line-covering entry is the most recent touch,
  and it is the one named.
* **The setting is a gate, not a guess.** With
  ``blame_sight`` off, asking through the agent layer
  refuses and says so; the pure parsing and matching
  stays available. A malformed stored setting raises,
  never defaults silently.
"""

from __future__ import annotations

__all__ = [
    "BLAME_SIGHT_SLICE",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "UNCOMMITTED_COMMIT",
    "USAGE",
    "Any",
    "BlameLine",
    "BlameRun",
    "BoolChange",
    "Dict",
    "HistorySight",
    "JournalMatch",
    "List",
    "Optional",
    "Tuple",
    "blame_line",
    "blame_runs",
    "enabled_from_config",
    "explain_line",
    "format_blame",
    "format_blame_sight",
    "format_history_sight",
    "format_setting_change",
    "journal_span",
    "match_journal",
    "parse_blame_args",
    "parse_blame_porcelain",
    "set_enabled",
]

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

#: The slice that owns this module.
BLAME_SIGHT_SLICE = "M-092"

#: The config key the blame-sight gate lives under.
SETTING_KEY = "blame_sight"

#: The all-zero commit git blame gives uncommitted lines.
UNCOMMITTED_COMMIT = "0" * 40

#: The setting explained in plain words.
PLAIN_EXPLANATION = (
    "Blame and history sight: ask why a line is the "
    "way it is, and two records answer together. Git "
    "blame names the commit that last touched the "
    "line - its author, its date, its summary, the "
    "line's own text - read from blame's porcelain "
    "form, never guessed. The tool's own journal is "
    "then matched against the same file and line: an "
    "entry that names the file and covers the line "
    "names the session that wrote it, so the answer "
    "can say which session, in which commit. Where "
    "the journal does not reach the line, the answer "
    "says so and blame alone speaks; a line that is "
    "not committed yet is named as the working tree's "
    "own, with no commit invented for it."
)

USAGE = ("Usage: /blame, /blame on, /blame off, "
         "/blame <path>, or /blame <path> <line>")

_HEADER_RE = re.compile(
    r"^([0-9a-f]{40}) (\d+) (\d+)(?: (\d+))?$")


@dataclass(frozen=True)
class BlameLine:
    """One blamed line: who, when, and the line itself.

    ``line_no`` is the line's number in the current
    file (the porcelain final number); ``orig_no`` is
    its number in the commit that wrote it. The two
    differ when later commits moved the line.
    """

    commit: str
    author: str
    author_mail: str
    author_time: int
    summary: str
    filename: str
    orig_no: int
    line_no: int
    text: str

    @property
    def short_commit(self) -> str:
        return self.commit[:7]

    @property
    def uncommitted(self) -> bool:
        return self.commit == UNCOMMITTED_COMMIT

    def record(self) -> Dict[str, Any]:
        return {"commit": self.commit,
                "short_commit": self.short_commit,
                "author": self.author,
                "author_mail": self.author_mail,
                "author_time": self.author_time,
                "summary": self.summary,
                "filename": self.filename,
                "orig_no": self.orig_no,
                "line_no": self.line_no,
                "text": self.text,
                "uncommitted": self.uncommitted}


def parse_blame_porcelain(text: str) -> Tuple[BlameLine, ...]:
    """Parse ``git blame --porcelain`` output.

    Porcelain gives the full commit record (author,
    time, summary, filename) on the first line of a
    run and bare headers after it; the record is
    cached per commit, so every line is attributed
    from its own commit's record. Anything the parser
    cannot read raises - blame is never invented.
    """
    entries: List[BlameLine] = []
    cache: Dict[str, Dict[str, Any]] = {}
    filename = ""
    pending: Optional[Dict[str, Any]] = None
    for raw in text.splitlines():
        header = _HEADER_RE.match(raw)
        if header is not None:
            if pending is not None:
                raise ValueError(
                    "blame porcelain: a header arrived "
                    "before the previous line's content")
            pending = {"commit": header.group(1),
                       "orig_no": int(header.group(2)),
                       "line_no": int(header.group(3))}
            continue
        if raw.startswith("\t"):
            if pending is None:
                raise ValueError(
                    "blame porcelain: a content line "
                    "arrived with no header before it")
            commit = pending["commit"]
            meta = cache.get(commit, {})
            if "author" not in meta:
                raise ValueError(
                    "blame porcelain: commit "
                    f"{commit[:7]} carries no author "
                    "record; its lines cannot be blamed")
            entries.append(BlameLine(
                commit=commit,
                author=str(meta["author"]),
                author_mail=str(meta.get("author_mail", "")),
                author_time=int(meta.get("author_time", 0)),
                summary=str(meta.get("summary", "")),
                filename=filename,
                orig_no=pending["orig_no"],
                line_no=pending["line_no"],
                text=raw[1:]))
            pending = None
            continue
        if pending is None:
            raise ValueError(
                f"blame porcelain: unreadable line {raw!r}")
        key, _, value = raw.partition(" ")
        if key == "filename":
            filename = value
        elif key in ("author", "author-mail", "author-time",
                     "summary"):
            meta = cache.setdefault(pending["commit"], {})
            if key == "author-time":
                try:
                    meta["author_time"] = int(value)
                except ValueError:
                    raise ValueError(
                        "blame porcelain: author-time "
                        f"{value!r} is not a number") from None
            else:
                meta[key.replace("-", "_")] = value
    if pending is not None:
        raise ValueError(
            "blame porcelain: the last header has no "
            "content line")
    return tuple(entries)


def blame_line(lines: Tuple[BlameLine, ...],
               line_no: int) -> BlameLine:
    """The blamed entry for one 1-based line number.

    A line the blame does not cover raises - the
    answer names the file's true length rather than
    blaming a line that is not there.
    """
    if line_no < 1:
        raise ValueError(
            f"line numbers start at 1; got {line_no}")
    for entry in lines:
        if entry.line_no == line_no:
            return entry
    raise ValueError(
        f"line {line_no} is outside the blamed file "
        f"({len(lines)} lines)")


@dataclass(frozen=True)
class BlameRun:
    """Consecutive lines blamed to one commit."""

    commit: str
    author: str
    start_line: int
    end_line: int

    @property
    def count(self) -> int:
        return self.end_line - self.start_line + 1

    def record(self) -> Dict[str, Any]:
        return {"commit": self.commit,
                "author": self.author,
                "start_line": self.start_line,
                "end_line": self.end_line,
                "count": self.count}


def blame_runs(lines: Tuple[BlameLine, ...],
               ) -> Tuple[BlameRun, ...]:
    """Group consecutive same-commit lines into runs."""
    runs: List[BlameRun] = []
    for entry in lines:
        if (runs and runs[-1].commit == entry.commit
                and runs[-1].end_line + 1 == entry.line_no):
            last = runs[-1]
            runs[-1] = BlameRun(
                commit=last.commit, author=last.author,
                start_line=last.start_line,
                end_line=entry.line_no)
        else:
            runs.append(BlameRun(
                commit=entry.commit, author=entry.author,
                start_line=entry.line_no,
                end_line=entry.line_no))
    return tuple(runs)


def _clean_path(path: Any) -> str:
    text = str(path or "")
    return text[2:] if text.startswith("./") else text


def journal_span(entry: Dict[str, Any],
                 ) -> Optional[Tuple[int, int]]:
    """The (first, last) lines a journal entry covers.

    ``line`` covers one line; ``start_line`` /
    ``end_line`` cover a span (either end alone covers
    that one line); ``lines`` covers its first-to-last.
    No line information at all returns None: the entry
    is a file-level record, and says nothing about any
    one line. Malformed line values raise.
    """
    if "line" in entry and entry["line"] is not None:
        line = entry["line"]
        if not isinstance(line, int) or line < 1:
            raise ValueError(
                f"journal entry line must be a positive "
                f"number; got {line!r}")
        return (line, line)
    if "lines" in entry and entry["lines"] is not None:
        values = entry["lines"]
        if (not isinstance(values, (list, tuple))
                or not values
                or not all(isinstance(x, int) and x >= 1
                           for x in values)):
            raise ValueError(
                "journal entry lines must be a non-empty "
                f"list of line numbers; got {values!r}")
        return (min(values), max(values))
    start = entry.get("start_line")
    end = entry.get("end_line")
    if start is None and end is None:
        return None
    for name, value in (("start_line", start),
                        ("end_line", end)):
        if value is not None and (
                not isinstance(value, int) or value < 1):
            raise ValueError(
                f"journal entry {name} must be a positive "
                f"number; got {value!r}")
    first = start if start is not None else end
    last = end if end is not None else start
    assert first is not None and last is not None
    return (min(first, last), max(first, last))


@dataclass(frozen=True)
class JournalMatch:
    """How the journal's record meets one line.

    ``line_entries`` cover the line itself;
    ``file_entries`` name the file but no line span.
    The named session is the last line-covering
    entry's - journal order is writing order, so the
    last is the newest touch.
    """

    line_entries: Tuple[Dict[str, Any], ...]
    file_entries: Tuple[Dict[str, Any], ...]

    @property
    def session(self) -> Optional[str]:
        for entry in reversed(self.line_entries):
            session = entry.get("session_id")
            if session:
                return str(session)
        return None


def match_journal(entries: Any, path: str,
                  line_no: int) -> JournalMatch:
    """Match journal *entries* against one file + line.

    Every entry must be a record (a dict) naming its
    file under ``path``; a record that is not raises.
    Entries for other files are simply not this line's
    history and are passed over.
    """
    wanted = _clean_path(path)
    line_hits: List[Dict[str, Any]] = []
    file_hits: List[Dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError(
                "journal entries must be records; got "
                f"{type(entry).__name__}")
        if _clean_path(entry.get("path")) != wanted:
            continue
        span = journal_span(entry)
        if span is None:
            file_hits.append(entry)
        elif span[0] <= line_no <= span[1]:
            line_hits.append(entry)
    return JournalMatch(line_entries=tuple(line_hits),
                        file_entries=tuple(file_hits))


@dataclass(frozen=True)
class HistorySight:
    """One line's whole answer: blame + journal record."""

    path: str
    line_no: int
    text: str
    commit: str
    author: str
    author_time: int
    summary: str
    uncommitted: bool
    journal_session: Optional[str]
    journal_line_records: int
    journal_file_records: int
    journal_note: str

    @property
    def short_commit(self) -> str:
        return self.commit[:7]

    def record(self) -> Dict[str, Any]:
        return {"type": "blame_sight", "path": self.path,
                "line_no": self.line_no, "text": self.text,
                "commit": self.commit,
                "short_commit": self.short_commit,
                "author": self.author,
                "author_time": self.author_time,
                "summary": self.summary,
                "uncommitted": self.uncommitted,
                "journal_session": self.journal_session,
                "journal_line_records":
                    self.journal_line_records,
                "journal_file_records":
                    self.journal_file_records,
                "journal_note": self.journal_note}


def explain_line(lines: Tuple[BlameLine, ...], line_no: int,
                 journal_entries: Any = (),
                 ) -> HistorySight:
    """Answer "why is this line like this?" for one line.

    Blame names the commit; the journal match names
    the session when one of its records covers the
    line, and the note says exactly how far the
    journal reaches when it does not.
    """
    entry = blame_line(lines, line_no)
    match = match_journal(journal_entries, entry.filename,
                          line_no)
    session = match.session
    if session is not None:
        note = ("the journal's own record names session "
                f"{session} as the session that wrote "
                "this line")
    elif match.line_entries:
        note = ("the journal holds "
                f"{len(match.line_entries)} record(s) "
                "covering this line, but none names its "
                "session - blame alone names the writer")
    elif match.file_entries:
        note = ("the journal holds "
                f"{len(match.file_entries)} record(s) "
                "for this file, but none covers this "
                "line - blame alone speaks for this line")
    else:
        note = ("no journal record covers this line - "
                "blame alone speaks for this line")
    if entry.uncommitted:
        note = ("this line is not committed yet - the "
                "working tree wrote it and git blame "
                "names no commit; " + note)
    return HistorySight(
        path=entry.filename, line_no=line_no,
        text=entry.text, commit=entry.commit,
        author=entry.author, author_time=entry.author_time,
        summary=entry.summary,
        uncommitted=entry.uncommitted,
        journal_session=session,
        journal_line_records=len(match.line_entries),
        journal_file_records=len(match.file_entries),
        journal_note=note)


def _date(author_time: int) -> str:
    if author_time <= 0:
        return "an unknown date"
    return datetime.fromtimestamp(
        author_time, timezone.utc).strftime("%Y-%m-%d")


def format_history_sight(sight: HistorySight) -> str:
    """One line's answer, in plain words."""
    lines = [f"Line {sight.line_no} of {sight.path}: "
             f"{sight.text}"]
    if sight.uncommitted:
        lines.append(
            "Blame: not committed yet - no commit, no "
            "author; the working tree holds this line.")
    else:
        lines.append(
            f"Blame: commit {sight.short_commit} by "
            f"{sight.author} on {_date(sight.author_time)}"
            f" - {sight.summary}")
    lines.append(f"Journal: {sight.journal_note}.")
    return "\n".join(lines)


def format_blame(lines: Tuple[BlameLine, ...],
                 path: Optional[str] = None) -> str:
    """A whole file's blame, counted and signed.

    The header counts lines, commits and authors from
    the blame itself; every line carries its commit's
    short hash and author in words, so the sight reads
    without colour.
    """
    name = path or (lines[0].filename if lines else "the file")
    commits = {x.commit for x in lines}
    authors = {x.author for x in lines}
    rendered = [
        f"Blame for {name}: {len(lines)} lines, "
        f"{len(commits)} commits, {len(authors)} authors"]
    for entry in lines:
        marker = " (not committed yet)" if entry.uncommitted else ""
        rendered.append(
            f"{entry.line_no:>4} {entry.short_commit} "
            f"{entry.author}: {entry.text}{marker}")
    return "\n".join(rendered)


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The blame_sight setting stored in *config*.

    Absent means True (the setting ships on). A stored
    value that is not a bool raises - never guessed at.
    """
    raw = config.get(SETTING_KEY, True)
    if not isinstance(raw, bool):
        raise ValueError(
            f"{SETTING_KEY} must be true or false, "
            f"got {type(raw).__name__}")
    return raw


@dataclass(frozen=True)
class BoolChange:
    """A recorded change of the gate setting."""

    before: bool
    after: bool

    def event(self) -> Dict[str, Any]:
        return {"type": "blame_sight_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {**self.event(), "session_id": session_id,
                "journaled": journaled}


def set_enabled(config: Dict[str, Any],
                enabled: Any) -> Tuple[bool, BoolChange]:
    """Validate a gate change against *config*, purely."""
    if not isinstance(enabled, bool):
        raise ValueError(
            f"{SETTING_KEY} is turned on or off; got {enabled!r}")
    before = enabled_from_config(config)
    if enabled == before:
        raise ValueError(
            f"blame sight is already "
            f"{'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


def _line_number(token: str) -> int:
    try:
        number = int(token)
    except ValueError:
        raise ValueError(f"usage: {USAGE}") from None
    if number < 1:
        raise ValueError(
            f"line numbers start at 1; got {number}")
    return number


def parse_blame_args(args: str) -> Dict[str, Any]:
    """Parse the /blame grammar both surfaces share.

    ``show`` / ``on`` / ``off`` stand alone; a path
    asks for the whole file's blame; a path and a
    line number (or ``path:line``) ask why that one
    line is the way it is.
    """
    text = (args or "").strip()
    if not text or text == "show":
        return {"action": "show"}
    if text == "on":
        return {"action": "on"}
    if text == "off":
        return {"action": "off"}
    parts = text.split()
    if len(parts) == 1:
        token = parts[0]
        if ":" in token:
            path, _, tail = token.rpartition(":")
            if path and tail.isdigit():
                return {"action": "blame", "path": path,
                        "line": _line_number(tail)}
        return {"action": "blame", "path": token, "line": None}
    if len(parts) == 2:
        return {"action": "blame", "path": parts[0],
                "line": _line_number(parts[1])}
    raise ValueError(f"usage: {USAGE}")


def format_setting_change(record: Dict[str, Any]) -> str:
    state = "on" if record.get("to") else "off"
    return f"Blame sight is now {state}."


_DEMO_COMMIT_A = "a" * 40
_DEMO_COMMIT_B = "b" * 40

_DEMO_PORCELAIN = (
    f"{_DEMO_COMMIT_A} 1 1 2\n"
    "author Ada Example\n"
    "author-mail <ada@example.invalid>\n"
    "author-time 1793984433\n"
    "author-tz -0500\n"
    "summary open the file with its first line\n"
    "filename demo.py\n"
    "\tfirst = 1\n"
    f"{_DEMO_COMMIT_A} 2 2\n"
    "\tsecond = 2\n"
    f"{_DEMO_COMMIT_B} 1 3 1\n"
    "author Ben Example\n"
    "author-mail <ben@example.invalid>\n"
    "author-time 1794070833\n"
    "author-tz -0500\n"
    "summary the third line arrives later\n"
    "filename demo.py\n"
    "\tthird = 3\n"
)

_DEMO_JOURNAL = (
    {"type": "edit_applied", "path": "demo.py", "line": 2,
     "session_id": "demo-session"},
)


def format_blame_sight(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /blame.

    Built from parse_blame_porcelain() / explain_line()
    / format_*(), so the show surface exercises the
    road it names: a demo file blamed, and its second
    line explained by blame and journal together.
    """
    enabled = enabled_from_config(config)
    lines = ["Blame and history sight (M-092) - "
             + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    lines.append("")
    blamed = parse_blame_porcelain(_DEMO_PORCELAIN)
    lines.append(format_blame(blamed))
    lines.append("")
    lines.append(format_history_sight(
        explain_line(blamed, 2, _DEMO_JOURNAL)))
    return "\n".join(lines)
