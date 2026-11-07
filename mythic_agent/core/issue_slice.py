"""Issue-to-slice (All-Features roadmap slice M-083).

Part IV — The Editor's Hand. The roadmap's words: a GitHub
issue (or Samverk issue, Part X) becomes a planned slice with
acceptance checks drafted from its text.

What already shipped, and what this slice adds:

* The GitHub road (``integrations/github.py``, Slice 36)
  shells out to the user's own ``gh`` binary: it can list
  issues and create PRs, but nothing turned an issue into
  planned work — an issue was a line in a list, not a slice.
* Part X's Samverk bridge (M-242) will give Volmarr's own
  forge "repos, issues, and PRs ... with the same craft as
  GitHub's (Part IV), once Samverk's own road provides the
  surfaces". That road has not been built, and this slice
  does not invent it: the issue source is a *seam* — a small
  registry naming each source, whether it can fetch today,
  and the slice that owns its road. ``github`` fetches now;
  ``samverk`` is named, with its owning road (Part X,
  M-242), and fetching through it refuses honestly until
  that road provides the surfaces.
* This slice is the planning layer over the seam: an issue,
  from any source the seam can fetch, becomes a planned
  slice in the house's own format — the roadmap slice's
  shape (title, summary, status) from M-017's
  ``core/roadmap_slices.py``, carrying its source reference
  and a set of acceptance checks drafted from the issue's
  own text. Planning writes nothing and files nothing: the
  planned slice is product output data for a human (or a
  later campaign road) to take up, never an edit to the
  campaign's roadmap file.

Honesty rules, enforced here and pinned by the slice's
tests:

* **Every acceptance check is traced to the issue's own
  words.** A check is drafted only from text the issue
  actually carries — a task-list item in its body, a bullet
  under an acceptance heading in its body, or (when the
  body carries neither) the issue's title itself — and
  every check records the verbatim excerpt it was drafted
  from. A check whose excerpt does not appear in the
  issue's title or body is refused at validation: this
  layer never invents a requirement the issue did not
  state.
* **The seam never invents a source's internals.** The
  Samverk source is named for Part X (its bridge is
  M-242); fetching a Samverk issue today refuses, naming
  that road — it never guesses at Samverk's surfaces,
  and the GitHub road is the only fetcher wired.
* **Fetching is the seam's job, planning is pure.** The
  GitHub fetcher rides the existing ``gh`` wrapper; tests
  inject a fake fetcher, so no test ever makes a live
  call. Given the same issue, planning always drafts the
  same slice.
* **The planned slice wears the house format.** Its record
  carries the roadmap slice's keys (title, summary,
  status — ``planned``, a state the campaign ledger does
  not use for its own road, so a planned slice can never
  be mistaken for a banked or queued roadmap slice) plus
  its source reference and its checks.
* **The setting is a gate, not a guess.** With
  ``issue_to_slice`` off, planning through the agent layer
  refuses and says so; the pure planning maths stays
  available. A malformed stored setting raises, never
  defaults silently.
"""

from __future__ import annotations

__all__ = [
    "CHECK_KINDS",
    "ISSUE_SLICE_SLICE",
    "PLAIN_EXPLANATION",
    "PLANNED_STATUS",
    "SAMVERK_ROAD",
    "SETTING_KEY",
    "SOURCES",
    "USAGE",
    "AcceptanceCheck",
    "Any",
    "BoolChange",
    "Callable",
    "Dict",
    "IssueRecord",
    "IssueSourceUnavailable",
    "List",
    "Optional",
    "PlannedSlice",
    "Sequence",
    "SourceInfo",
    "Tuple",
    "available_sources",
    "draft_acceptance_checks",
    "enabled_from_config",
    "fetch_issue",
    "format_issue_slice",
    "format_plan",
    "format_plan_record",
    "format_setting_change",
    "issue_from_github_record",
    "issue_from_record",
    "parse_issueslice_args",
    "plan_slice",
    "set_enabled",
    "validate_checks_trace",
]

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

#: The slice that owns this module.
ISSUE_SLICE_SLICE = "M-083"

#: The config key the issue-to-slice gate lives under.
SETTING_KEY = "issue_to_slice"

#: The roadmap slice that owns the Samverk bridge (Part X).
SAMVERK_ROAD = "M-242"

#: The status a planned slice carries. The campaign ledger
#: (M-017) knows only ``done`` and ``queued``; ``planned``
#: is deliberately outside that set, so a planned slice is
#: never mistaken for a slice of the approved road itself.
PLANNED_STATUS = "planned"

#: How an acceptance check was drafted from the issue.
#: ``checklist`` — a task-list item in the body;
#: ``acceptance`` — a bullet under an acceptance heading;
#: ``title`` — the fallback: the issue's own title.
CHECK_KINDS: Tuple[str, ...] = ("checklist", "acceptance", "title")

#: The setting explained in plain words — the sentence
#: every surface shows.
PLAIN_EXPLANATION = (
    "Issue-to-slice: a GitHub issue becomes a planned "
    "slice — a title, a summary, and acceptance checks — "
    "in the same shape as a roadmap slice. Every "
    "acceptance check is drafted from the issue's own "
    "words: a task-list item in its body, a bullet under "
    "its acceptance heading, or, when the body carries "
    "neither, the issue's title itself; each check keeps "
    "the exact words it was drafted from, so nothing is "
    "ever invented that the issue did not say. The issue "
    "source is a seam: GitHub fetches today through the "
    "gh road, and the Samverk source is named for Part X "
    "(its bridge is M-242) — fetching a Samverk issue "
    "refuses honestly until that road provides the "
    "surfaces. Planning files nothing and changes no "
    "roadmap: the planned slice is output for a human to "
    "take up, and it is recorded on the session journal."
)

USAGE = ("Usage: /issueslice, /issueslice on, "
         "/issueslice off, or /issueslice github <number>")


class IssueSourceUnavailable(RuntimeError):
    """A named issue source cannot fetch yet (its road is unbuilt)."""


@dataclass(frozen=True)
class SourceInfo:
    """One named issue source on the seam."""

    name: str
    available: bool
    road: str
    note: str


#: The seam's registry: every source an issue may come
#: from, whether it can fetch today, and the slice that
#: owns its road. GitHub is Part IV's road (this slice,
#: over Slice 36's gh wrapper); Samverk is Part X's
#: bridge (M-242) and is named only — never invented.
SOURCES: Tuple[SourceInfo, ...] = (
    SourceInfo(
        name="github", available=True, road="M-083",
        note="fetches through the gh CLI road "
             "(integrations/github.py)"),
    SourceInfo(
        name="samverk", available=False, road=SAMVERK_ROAD,
        note="Part X's Samverk bridge: repos, issues, and "
             "PRs with the same craft as GitHub's, once "
             "Samverk's own road provides the surfaces"),
)


def available_sources() -> Tuple[SourceInfo, ...]:
    """Every source on the seam, in registry order."""
    return SOURCES


def _source_info(source: str) -> SourceInfo:
    for info in SOURCES:
        if info.name == source:
            return info
    raise ValueError(
        f"unknown issue source {source!r}; the seam knows "
        + ", ".join(info.name for info in SOURCES))


@dataclass(frozen=True)
class IssueRecord:
    """One issue, as data, from any source on the seam.

    ``labels`` are plain names (the GitHub fetcher flattens
    gh's ``[{"name": ...}]`` shape on the way in). ``body``
    is the issue's text exactly as its source carried it —
    the acceptance checks are drafted from it, verbatim.
    """

    source: str
    number: int
    title: str
    body: str
    state: str
    labels: Tuple[str, ...] = ()
    url: str = ""

    def source_ref(self) -> str:
        return f"{self.source}#{self.number}"


def _labels_from(raw: Any) -> Tuple[str, ...]:
    labels: List[str] = []
    for item in raw or ():
        if isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str) and name:
                labels.append(name)
        elif isinstance(item, str) and item:
            labels.append(item)
    return tuple(labels)


def issue_from_record(record: Dict[str, Any],
                      source: str = "github") -> IssueRecord:
    """Build an IssueRecord from a plain fetched record.

    The record is the shape a fetcher returns: ``number``,
    ``title``, and optionally ``body``, ``state``,
    ``labels``, and ``url``. A record without a usable
    number or title refuses — an issue that cannot be
    named cannot become a slice.
    """
    _source_info(source)
    if not isinstance(record, dict):
        raise ValueError("an issue record must be a mapping")
    number = record.get("number")
    if not isinstance(number, int) or number < 1:
        raise ValueError(
            f"an issue needs a number of 1 or more, got {number!r}")
    title = record.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("an issue needs a non-empty title")
    body = record.get("body") or ""
    if not isinstance(body, str):
        raise ValueError("an issue body must be text")
    state = record.get("state") or "open"
    if not isinstance(state, str) or not state:
        raise ValueError("an issue state must be non-empty text")
    url = record.get("url") or ""
    if not isinstance(url, str):
        raise ValueError("an issue url must be text")
    return IssueRecord(source=source, number=number,
                       title=title.strip(), body=body,
                       state=state,
                       labels=_labels_from(record.get("labels")),
                       url=url)


def issue_from_github_record(record: Dict[str, Any]) -> IssueRecord:
    """Build an IssueRecord from a ``gh issue view`` record."""
    return issue_from_record(record, source="github")


@dataclass(frozen=True)
class AcceptanceCheck:
    """One acceptance check, drafted from an issue's text.

    ``text`` is the check as planned work states it;
    ``source_excerpt`` is the verbatim words of the issue
    it was drafted from, and ``kind`` says where in the
    issue those words stood. The excerpt is the check's
    provenance: it must appear in the issue's title or
    body, proven by :func:`validate_checks_trace`.
    """

    text: str
    kind: str
    source_excerpt: str


_TASK_ITEM_RE = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s+(.+?)\s*$")
_BULLET_RE = re.compile(r"^\s*(?:[-*]\s+|\d+[.)]\s+)(.+?)\s*$")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*$")


def draft_acceptance_checks(issue: IssueRecord
                            ) -> Tuple[AcceptanceCheck, ...]:
    """Draft acceptance checks from *issue*'s own text.

    In order: every task-list item in the body, then every
    bullet under a heading that names acceptance (a
    heading containing "acceptance", case-insensitive),
    deduplicated by check text. When the body carries
    neither, the single drafted check is the issue's title
    itself — the least a slice from this issue must do is
    the thing the issue's title asks for. No other text is
    ever drafted: a check this function cannot trace to
    the issue's words is a check it does not make.
    """
    checks: List[AcceptanceCheck] = []
    seen = set()

    def add(text: str, kind: str, excerpt: str) -> None:
        text = text.strip()
        if not text or text in seen:
            return
        seen.add(text)
        checks.append(AcceptanceCheck(
            text=text, kind=kind, source_excerpt=excerpt))

    lines = issue.body.splitlines()
    for line in lines:
        match = _TASK_ITEM_RE.match(line)
        if match:
            add(match.group(1), "checklist", match.group(1))
    in_acceptance = False
    for line in lines:
        heading = _HEADING_RE.match(line)
        if heading:
            in_acceptance = "acceptance" in heading.group(1).lower()
            continue
        if in_acceptance:
            if _TASK_ITEM_RE.match(line):
                continue  # already drafted as a checklist item
            bullet = _BULLET_RE.match(line)
            if bullet:
                add(bullet.group(1), "acceptance", bullet.group(1))
    if not checks:
        add(f"The issue's request is addressed: {issue.title}",
            "title", issue.title)
    return tuple(checks)


def validate_checks_trace(issue: IssueRecord,
                          checks: Sequence[AcceptanceCheck]
                          ) -> List[str]:
    """Problems with *checks* as drafts from *issue*.

    Every check's excerpt must appear verbatim in the
    issue's title or body, and its kind must be a known
    drafting road. An untraceable check is an invented
    requirement, and is named as one.
    """
    problems: List[str] = []
    haystack = issue.title + "\n" + issue.body
    for check in checks:
        if check.kind not in CHECK_KINDS:
            problems.append(
                f"check {check.text!r}: kind must be one of "
                f"{CHECK_KINDS}, got {check.kind!r}")
        if not check.source_excerpt or \
                check.source_excerpt not in haystack:
            problems.append(
                f"check {check.text!r}: its source excerpt "
                f"{check.source_excerpt!r} does not appear in "
                "the issue's title or body — an acceptance "
                "check may only be drafted from the issue's "
                "own words")
    return problems


@dataclass(frozen=True)
class PlannedSlice:
    """An issue, planned as a slice in the house format.

    Carries the roadmap slice's shape (M-017): ``title``,
    ``summary``, and ``status`` — here always ``planned``.
    Around that core it carries its provenance: the source
    it came from, the issue's number, url, and labels, and
    the acceptance checks drafted from the issue's text.
    """

    title: str
    summary: str
    status: str
    source: str
    number: int
    url: str
    labels: Tuple[str, ...]
    acceptance_checks: Tuple[AcceptanceCheck, ...]

    def source_ref(self) -> str:
        return f"{self.source}#{self.number}"

    def to_record(self) -> Dict[str, Any]:
        """The planned slice as a plain record (data out).

        The roadmap slice's keys come first — title,
        summary, status — then the source reference and
        the drafted checks, each with its provenance.
        """
        return {
            "title": self.title,
            "summary": self.summary,
            "status": self.status,
            "source": self.source,
            "number": self.number,
            "source_ref": self.source_ref(),
            "url": self.url,
            "labels": list(self.labels),
            "acceptance_checks": [
                {"text": check.text, "kind": check.kind,
                 "source_excerpt": check.source_excerpt}
                for check in self.acceptance_checks],
        }

    def event(self) -> Dict[str, Any]:
        return {"type": "issue_slice_planned",
                "source": self.source, "number": self.number,
                "source_ref": self.source_ref(),
                "title": self.title, "status": self.status,
                "checks": len(self.acceptance_checks)}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {**self.to_record(), "session_id": session_id,
                "journaled": journaled}


def _summary_from(issue: IssueRecord) -> str:
    """The planned slice's summary, from the issue itself.

    The body's first plain line — not a heading, not a
    task-list item, not blank — trimmed to one line. An
    issue with no such line is summarised by its title.
    Either way the summary is the issue's own words.
    """
    for line in issue.body.splitlines():
        text = line.strip()
        if not text or _HEADING_RE.match(line) \
                or _TASK_ITEM_RE.match(line):
            continue
        if len(text) > 200:
            text = text[:197].rstrip() + "..."
        return text
    return issue.title


def plan_slice(issue: IssueRecord) -> PlannedSlice:
    """Plan *issue* as a slice: pure, and proven traceable.

    Drafts the acceptance checks from the issue's text and
    proves every one of them traces to that text before
    the slice is returned — a plan whose checks cannot be
    traced is refused here, never handed on.
    """
    if not isinstance(issue, IssueRecord):
        raise ValueError("planning works on an issue record")
    checks = draft_acceptance_checks(issue)
    problems = validate_checks_trace(issue, checks)
    if problems:
        raise ValueError("; ".join(problems))
    return PlannedSlice(
        title=issue.title, summary=_summary_from(issue),
        status=PLANNED_STATUS, source=issue.source,
        number=issue.number, url=issue.url,
        labels=issue.labels, acceptance_checks=checks)


def _github_fetcher(number: int) -> Dict[str, Any]:
    """The seam's GitHub fetcher: the existing gh road."""
    from ..integrations.github import view_issue

    return view_issue(number)


def _samverk_fetcher(number: int) -> Dict[str, Any]:
    """The seam's Samverk placeholder: named, never invented."""
    raise IssueSourceUnavailable(
        f"the Samverk issue source is Part X's road "
        f"({SAMVERK_ROAD} Samverk bridge) and cannot fetch "
        f"yet: Samverk's own road does not yet provide the "
        f"surfaces — nothing was fetched")


_FETCHERS: Dict[str, Callable[[int], Dict[str, Any]]] = {
    "github": _github_fetcher,
    "samverk": _samverk_fetcher,
}


def fetch_issue(source: str, number: int,
                fetcher: Optional[Callable[[int], Dict[str, Any]]]
                = None) -> IssueRecord:
    """Fetch issue *number* from *source* through the seam.

    *fetcher* is the seam's test door: a callable taking a
    number and returning a plain record, exactly as the
    real fetchers return. Without one, the source's own
    fetcher runs — GitHub's ``gh`` road today; Samverk
    refuses, naming Part X's road (M-242).
    """
    info = _source_info(source)
    if not isinstance(number, int) or number < 1:
        raise ValueError(
            f"an issue number must be 1 or more, got {number!r}")
    if fetcher is None:
        if not info.available:
            raise IssueSourceUnavailable(
                f"the {source} issue source is {info.road}'s "
                f"road and cannot fetch yet — {info.note}; "
                "nothing was fetched")
        fetcher = _FETCHERS[source]
    return issue_from_record(fetcher(number), source=source)


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The issue-to-slice setting stored in *config*.

    Absent means True (the setting ships on). A stored
    value that is not a bool raises — never guessed at.
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
        return {"type": "issue_slice_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "issue_slice_setting_changed",
                "from": self.before, "to": self.after,
                "session_id": session_id, "journaled": journaled}


def set_enabled(config: Dict[str, Any],
                enabled: Any) -> Tuple[bool, BoolChange]:
    """Validate a gate change against *config*, purely."""
    if not isinstance(enabled, bool):
        raise ValueError(
            f"{SETTING_KEY} is turned on or off; got {enabled!r}")
    before = enabled_from_config(config)
    if enabled == before:
        raise ValueError(
            f"issue-to-slice is already "
            f"{'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The /issueslice surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_issueslice_args(args: str) -> Dict[str, Any]:
    """Parse ``/issueslice`` arguments.

    /issueslice              -> show
    /issueslice on           -> turn the gate on
    /issueslice off          -> turn the gate off
    /issueslice github 42    -> plan GitHub issue 42
    /issueslice samverk 7    -> plan Samverk issue 7 (the
                                seam refuses honestly today)
    """
    text = (args or "").strip()
    if not text:
        return {"action": "show"}
    if text == "on":
        return {"action": "setting", "enabled": True}
    if text == "off":
        return {"action": "setting", "enabled": False}
    parts = text.split()
    if len(parts) == 2:
        source, raw_number = parts
        _source_info(source)  # an unknown source refuses here
        digits = raw_number.lstrip("#")
        if digits.isdigit() and int(digits) >= 1:
            return {"action": "plan", "source": source,
                    "number": int(digits)}
    raise ValueError(USAGE)


def format_setting_change(record: Dict[str, Any]) -> str:
    """A setting change record, in plain words."""
    word = {True: "on", False: "off"}
    return (f"Issue-to-slice: {word[record['from']]} -> "
            f"{word[record['to']]}.")


def format_plan(plan: PlannedSlice) -> str:
    """A planned slice, in plain words, checks and all."""
    lines = [
        f"Planned slice from {plan.source_ref()}: {plan.title}",
        f"Summary: {plan.summary}",
        f"Status: {plan.status}",
    ]
    if plan.url:
        lines.append(f"Issue: {plan.url}")
    if plan.labels:
        lines.append(f"Labels: {', '.join(plan.labels)}")
    lines.append(
        f"Acceptance checks ({len(plan.acceptance_checks)}), "
        "each drafted from the issue's own words:")
    for check in plan.acceptance_checks:
        lines.append(
            f"  - [{check.kind}] {check.text} "
            f"(from the issue: {check.source_excerpt!r})")
    return "\n".join(lines)


def format_plan_record(record: Dict[str, Any]) -> str:
    """A planned slice's record, in plain words.

    The record is :meth:`PlannedSlice.to_record`'s shape —
    what the agent layer hands the surfaces — rendered
    exactly as :func:`format_plan` renders the slice.
    """
    lines = [
        f"Planned slice from {record['source_ref']}: "
        f"{record['title']}",
        f"Summary: {record['summary']}",
        f"Status: {record['status']}",
    ]
    if record.get("url"):
        lines.append(f"Issue: {record['url']}")
    if record.get("labels"):
        lines.append(f"Labels: {', '.join(record['labels'])}")
    checks = record.get("acceptance_checks") or []
    lines.append(
        f"Acceptance checks ({len(checks)}), "
        "each drafted from the issue's own words:")
    for check in checks:
        lines.append(
            f"  - [{check['kind']}] {check['text']} "
            f"(from the issue: {check['source_excerpt']!r})")
    return "\n".join(lines)


_SAMPLE_ISSUE = IssueRecord(
    source="github", number=7,
    title="Fix the crash on an empty file",
    body=("Opening an empty file crashes the editor.\n"
          "\n"
          "- [ ] An empty file opens without crashing\n"
          "- [ ] A file with one line still opens\n"
          "\n"
          "## Acceptance\n"
          "\n"
          "- The crash report names the empty-file case\n"),
    state="open", labels=("bug",),
    url="https://github.com/example/repo/issues/7")


def format_issue_slice(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /issueslice.

    Built from available_sources() / plan_slice() /
    format_plan(), so every public road this module offers
    is exercised by its own show surface: the seam's
    registry (GitHub live, Samverk named for Part X), and
    a sample GitHub issue planned into a slice whose every
    check is quoted from the sample issue's own text.
    """
    enabled = enabled_from_config(config)
    lines = ["Issue-to-slice (M-083) — " + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    lines.append("")
    lines.append("Issue sources on the seam:")
    for info in available_sources():
        state = "available now" if info.available \
            else f"not yet — {info.road}'s road"
        lines.append(
            f"  {info.name}: {state} ({info.note})")
    lines.append("")
    lines.append("A sample GitHub issue, planned:")
    lines.append(format_plan(plan_slice(_SAMPLE_ISSUE)))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)
