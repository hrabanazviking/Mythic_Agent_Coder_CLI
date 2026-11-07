"""PR craft (All-Features roadmap slice M-082).

Part IV — The Editor's Hand. The roadmap's words: create,
review, and respond to pull requests — review comments
fetched as tasks; a review pass posts only at the user's
word (sending as the user is a standing pause-line).

What already shipped, and what this slice adds:

* The elder GitHub integration
  (``integrations/github.py``, Slice 36) shells out to the
  user's own ``gh`` CLI for a bare PR create, an issue list,
  a runs list, and one comment post — each one sending the
  moment it is called, with no draft stage and no
  user-word gate, and nothing that fetches a PR or its
  review comments.
* This slice is the craft layer over that road: a pull
  request is fetched as data, its review comments are
  fetched and turned into tasks (one task per comment),
  and the three sends — creating a PR, posting a review,
  posting a reply — are each prepared first as a draft
  that sends nothing, and post only when the draft
  carries the user's own recorded word.

Honesty rules, enforced here and pinned by the slice's
tests:

* **Drafts send nothing.** Preparing a PR draft, a review
  draft, or a reply draft is purely local work: no GitHub
  call is made, and the draft is data that can be shown,
  recorded, and only then posted.
* **Posting is the user's word, never the agent's.**
  Every post road refuses a draft that carries no
  recorded user word, and refuses before the GitHub
  runner is touched — nothing is sent, and the refusal
  says why. The word itself is never written into any
  record or journal event; records carry only that a word
  was recorded (``armed``), never its text.
* **Review comments become tasks, faithfully.** Each
  fetched comment or review-with-words becomes exactly
  one task carrying its PR number, comment id, author,
  body, and place (file and line when the comment carries
  them) — a comment is never merged, summarised, or
  dropped silently; a review with no words carries no
  task, because there is nothing to act on.
* **Line notes ride in the review body.** The ``gh``
  review road posts one body, so a review draft's line
  notes are listed in that body by file and line — they
  are delivered with the review, never silently held back
  and never presented as threaded inline comments.
* **One runner seam.** All GitHub traffic goes through a
  single injectable runner (argv in, stdout out) whose
  real form is the user's own ``gh`` CLI — auth stays
  exactly where the user configured it, no credentials
  pass through Mythic, and tests fake the whole road: no
  test in this slice makes a live GitHub call.
* **The setting is a gate, not a guess.** With
  ``pr_craft`` off, the agent layer refuses to fetch or
  post and says so; the pure draft maths stays available.
  A malformed stored setting raises, never defaults
  silently.
"""

from __future__ import annotations

__all__ = [
    "PR_CRAFT_SLICE",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "USAGE",
    "VERDICTS",
    "Any",
    "BoolChange",
    "Callable",
    "Dict",
    "LineNote",
    "List",
    "Optional",
    "PRDraft",
    "PullRequest",
    "ReplyDraft",
    "ReviewComment",
    "ReviewDraft",
    "Runner",
    "Sequence",
    "Tuple",
    "arm_pr_draft",
    "arm_reply_draft",
    "arm_review_draft",
    "comments_to_tasks",
    "enabled_from_config",
    "fetch_pull_request",
    "fetch_review_comments",
    "format_pr_craft",
    "format_pull_request",
    "format_setting_change",
    "format_tasks",
    "parse_prcraft_args",
    "parse_pull_request",
    "parse_review_comments",
    "post_pr",
    "post_reply",
    "post_review",
    "prepare_pr",
    "prepare_reply",
    "prepare_review",
    "set_enabled",
]

import json
from dataclasses import dataclass, replace
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

#: The slice that owns this module.
PR_CRAFT_SLICE = "M-082"

#: The config key the PR-craft gate lives under.
SETTING_KEY = "pr_craft"

#: Every verdict a review draft may carry.
VERDICTS: Tuple[str, ...] = ("approve", "comment", "request_changes")

#: A GitHub runner: gh argv in, stdout text out. The real
#: runner is the user's own ``gh`` CLI (see
#: ``integrations.github``); tests inject a fake.
Runner = Callable[[Sequence[str]], str]

#: The setting explained in plain words — the sentence
#: every surface shows.
PLAIN_EXPLANATION = (
    "PR craft: pull requests are created, reviewed, and "
    "answered from inside Mythic. A pull request is "
    "fetched as data, and its review comments are fetched "
    "and turned into tasks — one task per comment, "
    "carrying the comment's author, words, and place. "
    "Drafts are prepared locally and send nothing: a PR "
    "draft, a review draft (approve, comment, or request "
    "changes, with line notes), and a reply draft. "
    "Anything that would send as you — creating the PR, "
    "posting the review, posting the reply — posts only "
    "at your word: the draft must carry your own recorded "
    "word before the post road will run at all, and with "
    "no word recorded the post refuses and nothing is "
    "sent. Line notes ride in the review's body, listed "
    "by file and line, because the gh review road posts "
    "one body. All GitHub traffic rides your own gh CLI "
    "through one runner seam, so your auth stays where "
    "you configured it."
)

USAGE = ("Usage: /prcraft, /prcraft on, /prcraft off, "
         "or /prcraft tasks <pr-number>")

_PR_FIELDS = (
    "number,title,body,baseRefName,headRefName,state,"
    "isDraft,url,author,comments,reviews")

_VERDICT_FLAGS = {
    "approve": "--approve",
    "comment": "--comment",
    "request_changes": "--request-changes",
}


def _check_number(number: Any) -> int:
    if not isinstance(number, int) or isinstance(number, bool) \
            or number < 1:
        raise ValueError(f"a PR number is a positive integer; got {number!r}")
    return number


def _author_of(raw: Any) -> str:
    if isinstance(raw, dict):
        return str(raw.get("login") or "")
    return str(raw or "")


@dataclass(frozen=True)
class PullRequest:
    """One pull request, as data."""

    number: int
    title: str
    body: str
    base: str
    head: str
    state: str
    draft: bool
    url: str
    author: str

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "pr_fetched", "number": self.number,
                "title": self.title, "base": self.base,
                "head": self.head, "state": self.state,
                "draft": self.draft, "url": self.url,
                "author": self.author,
                "session_id": session_id, "journaled": journaled}


@dataclass(frozen=True)
class ReviewComment:
    """One fetched review comment (or review with words).

    ``kind`` is ``comment`` for a plain PR comment and
    ``review`` for a review pass that carried words.
    ``path`` / ``line`` name the comment's place when it
    carries one; a general comment has an empty path and
    no line.
    """

    comment_id: str
    pr_number: int
    author: str
    body: str
    kind: str = "comment"
    path: str = ""
    line: Optional[int] = None
    url: str = ""

    def task(self) -> Dict[str, Any]:
        """This comment as a task, in plain data."""
        place = self.path or "general"
        return {
            "task_id": f"pr-{self.pr_number}-comment-{self.comment_id}",
            "name": (f"Review PR #{self.pr_number}: "
                     f"{place}"
                     + (f":{self.line}" if self.line else "")),
            "state": "queued",
            "kind": "review_comment",
            "pr_number": self.pr_number,
            "comment_id": self.comment_id,
            "comment_kind": self.kind,
            "author": self.author,
            "body": self.body,
            "path": self.path,
            "line": self.line,
            "url": self.url,
        }


@dataclass(frozen=True)
class LineNote:
    """One line note carried by a review draft."""

    path: str
    line: int
    body: str


def _check_word(word: Any) -> str:
    if not isinstance(word, str) or not word.strip():
        raise ValueError(
            "posting as the user needs the user's own word "
            "recorded on the draft — no word was given; "
            "nothing was sent")
    return word.strip()


def _require_word(word: str, what: str) -> None:
    if not word:
        raise ValueError(
            f"a {what} posts only at the user's word — no "
            "word is recorded on this draft; nothing was sent")


@dataclass(frozen=True)
class PRDraft:
    """A prepared pull request. Preparation sends nothing.

    ``word`` is the user's own recorded word authorising
    the post; it is never written into any record — records
    carry only ``armed``.
    """

    title: str
    body: str
    base: str
    head: str
    draft: bool = False
    word: str = ""

    @property
    def armed(self) -> bool:
        return bool(self.word)

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "pr_draft_prepared", "title": self.title,
                "base": self.base, "head": self.head,
                "draft": self.draft, "armed": self.armed,
                "session_id": session_id, "journaled": journaled}

    def post_record(self, session_id: Optional[str],
                    journaled: bool,
                    posted: Dict[str, Any]) -> Dict[str, Any]:
        return {"type": "pr_posted",
                "number": posted.get("number"),
                "url": posted.get("url"),
                "title": posted.get("title", self.title),
                "state": posted.get("state"),
                "armed": True,
                "session_id": session_id, "journaled": journaled}


@dataclass(frozen=True)
class ReviewDraft:
    """A prepared review pass. Preparation sends nothing."""

    pr_number: int
    verdict: str
    body: str
    notes: Tuple[LineNote, ...] = ()
    word: str = ""

    @property
    def armed(self) -> bool:
        return bool(self.word)

    def review_body(self) -> str:
        """The body that posts: the words, then the line notes.

        The gh review road posts one body, so the notes are
        listed in it by file and line — delivered with the
        review, never held back.
        """
        if not self.notes:
            return self.body
        lines = [self.body] if self.body else []
        if lines:
            lines.append("")
        lines.append("Line notes:")
        for note in self.notes:
            lines.append(f"- {note.path}:{note.line} — {note.body}")
        return "\n".join(lines)

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "pr_review_draft_prepared",
                "pr_number": self.pr_number,
                "verdict": self.verdict,
                "notes": len(self.notes), "armed": self.armed,
                "session_id": session_id, "journaled": journaled}

    def post_record(self, session_id: Optional[str],
                    journaled: bool) -> Dict[str, Any]:
        return {"type": "pr_review_posted",
                "pr_number": self.pr_number,
                "verdict": self.verdict,
                "notes": len(self.notes), "armed": True,
                "session_id": session_id, "journaled": journaled}


@dataclass(frozen=True)
class ReplyDraft:
    """A prepared reply to one review comment."""

    pr_number: int
    comment_id: str
    body: str
    word: str = ""

    @property
    def armed(self) -> bool:
        return bool(self.word)

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "pr_reply_draft_prepared",
                "pr_number": self.pr_number,
                "comment_id": self.comment_id,
                "armed": self.armed,
                "session_id": session_id, "journaled": journaled}

    def post_record(self, session_id: Optional[str],
                    journaled: bool) -> Dict[str, Any]:
        return {"type": "pr_reply_posted",
                "pr_number": self.pr_number,
                "comment_id": self.comment_id, "armed": True,
                "session_id": session_id, "journaled": journaled}


# ---------------------------------------------------------------------
# Fetching: a PR as data, its review comments as tasks.
# ---------------------------------------------------------------------

def _view_args(number: int) -> List[str]:
    return ["pr", "view", str(_check_number(number)),
            "--json", _PR_FIELDS]


def _loads(payload: str) -> Dict[str, Any]:
    try:
        data = json.loads(payload)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "the GitHub road returned data that is not JSON; "
            "nothing was made of it") from exc
    if not isinstance(data, dict):
        raise ValueError(
            "the GitHub road returned JSON that is not a PR "
            "record; nothing was made of it")
    return data


def parse_pull_request(payload: str) -> PullRequest:
    """Parse ``gh pr view --json`` output into a PullRequest."""
    data = _loads(payload)
    return PullRequest(
        number=_check_number(data.get("number")),
        title=str(data.get("title") or ""),
        body=str(data.get("body") or ""),
        base=str(data.get("baseRefName") or ""),
        head=str(data.get("headRefName") or ""),
        state=str(data.get("state") or ""),
        draft=bool(data.get("isDraft")),
        url=str(data.get("url") or ""),
        author=_author_of(data.get("author")))


def fetch_pull_request(runner: Runner, number: int) -> PullRequest:
    """Fetch PR *number* through *runner*, as data."""
    return parse_pull_request(runner(_view_args(number)))


def parse_review_comments(payload: str,
                          pr_number: int) -> Tuple[ReviewComment, ...]:
    """Parse the comments + reviews of a ``gh pr view`` payload.

    Plain comments keep any file/line place they carry; a
    review becomes a comment record only when it carries
    words — a wordless review (a bare approval) has nothing
    to act on and honestly makes no task.
    """
    _check_number(pr_number)
    data = _loads(payload)
    comments: List[ReviewComment] = []
    for raw in data.get("comments") or []:
        if not isinstance(raw, dict):
            continue
        line = raw.get("line")
        comments.append(ReviewComment(
            comment_id=str(raw.get("id") or ""),
            pr_number=pr_number,
            author=_author_of(raw.get("author")),
            body=str(raw.get("body") or ""),
            kind="comment",
            path=str(raw.get("path") or ""),
            line=line if isinstance(line, int) else None,
            url=str(raw.get("url") or "")))
    for raw in data.get("reviews") or []:
        if not isinstance(raw, dict):
            continue
        body = str(raw.get("body") or "")
        if not body.strip():
            continue
        comments.append(ReviewComment(
            comment_id=str(raw.get("id") or ""),
            pr_number=pr_number,
            author=_author_of(raw.get("author")),
            body=body, kind="review",
            url=str(raw.get("url") or "")))
    return tuple(comments)


def fetch_review_comments(runner: Runner,
                          number: int) -> Tuple[ReviewComment, ...]:
    """Fetch PR *number*'s review comments through *runner*."""
    return parse_review_comments(runner(_view_args(number)), number)


def comments_to_tasks(
        comments: Sequence[ReviewComment]) -> List[Dict[str, Any]]:
    """Every fetched comment, as exactly one task."""
    return [comment.task() for comment in comments]


# ---------------------------------------------------------------------
# Drafts and the user-word gate: prepare, arm, post.
# ---------------------------------------------------------------------

def prepare_pr(title: str, body: str, base: str, head: str,
               draft: bool = False) -> PRDraft:
    """Prepare a PR draft. Purely local — nothing is sent."""
    if not isinstance(title, str) or not title.strip():
        raise ValueError("a PR draft needs a title")
    if not isinstance(base, str) or not base.strip():
        raise ValueError("a PR draft needs a base branch")
    if not isinstance(head, str) or not head.strip():
        raise ValueError("a PR draft needs a head branch")
    return PRDraft(title=title, body=body or "", base=base,
                   head=head, draft=bool(draft))


def arm_pr_draft(draft: PRDraft, word: Any) -> PRDraft:
    """Record the user's own word on a PR draft."""
    return replace(draft, word=_check_word(word))


def post_pr(runner: Runner, draft: PRDraft) -> Dict[str, Any]:
    """Create the PR a draft prepares — only at the user's word.

    A draft with no recorded word refuses here, before the
    runner is touched: nothing is sent.
    """
    _require_word(draft.word, "PR creation")
    args = ["pr", "create", "--title", draft.title,
            "--body", draft.body, "--base", draft.base,
            "--head", draft.head,
            "--json", "number,url,title,state"]
    if draft.draft:
        args.append("--draft")
    return _loads(runner(args))


def prepare_review(pr_number: int, verdict: str, body: str,
                   notes: Sequence[Any] = ()) -> ReviewDraft:
    """Prepare a review draft. Purely local — nothing is sent.

    *notes* are ``(path, line, body)`` triples or LineNote
    values. A comment or request-changes verdict needs
    words; an approval may stand on its own.
    """
    _check_number(pr_number)
    if verdict not in VERDICTS:
        raise ValueError(
            f"a review verdict is one of {', '.join(VERDICTS)}; "
            f"got {verdict!r}")
    if verdict != "approve" and not (body or "").strip():
        raise ValueError(
            f"a {verdict} review needs words — an empty "
            "review would send nothing worth sending")
    line_notes: List[LineNote] = []
    for note in notes:
        if isinstance(note, LineNote):
            line_notes.append(note)
            continue
        path, line, note_body = note
        if not isinstance(line, int) or isinstance(line, bool) \
                or line < 1:
            raise ValueError(
                f"a line note needs a positive line; got {line!r}")
        if not str(path).strip() or not str(note_body).strip():
            raise ValueError("a line note needs a file and words")
        line_notes.append(LineNote(path=str(path), line=line,
                                   body=str(note_body)))
    return ReviewDraft(pr_number=pr_number, verdict=verdict,
                       body=body or "", notes=tuple(line_notes))


def arm_review_draft(draft: ReviewDraft, word: Any) -> ReviewDraft:
    """Record the user's own word on a review draft."""
    return replace(draft, word=_check_word(word))


def post_review(runner: Runner, draft: ReviewDraft) -> None:
    """Post the review a draft prepares — only at the user's word."""
    _require_word(draft.word, "review")
    args = ["pr", "review", str(draft.pr_number),
            _VERDICT_FLAGS[draft.verdict]]
    body = draft.review_body()
    if body:
        args += ["--body", body]
    runner(args)


def prepare_reply(pr_number: int, comment_id: Any,
                  body: str) -> ReplyDraft:
    """Prepare a reply draft. Purely local — nothing is sent."""
    _check_number(pr_number)
    if not str(comment_id or "").strip():
        raise ValueError("a reply needs the comment it answers")
    if not (body or "").strip():
        raise ValueError("a reply needs words")
    return ReplyDraft(pr_number=pr_number,
                      comment_id=str(comment_id), body=body)


def arm_reply_draft(draft: ReplyDraft, word: Any) -> ReplyDraft:
    """Record the user's own word on a reply draft."""
    return replace(draft, word=_check_word(word))


def post_reply(runner: Runner, draft: ReplyDraft) -> None:
    """Post the reply a draft prepares — only at the user's word.

    The reply posts as a comment on the PR, carrying the
    answered comment's id in the record; the gh comment
    road has no threaded-reply form, and none is pretended.
    """
    _require_word(draft.word, "reply")
    runner(["pr", "comment", str(draft.pr_number),
            "--body", draft.body])


# ---------------------------------------------------------------------
# The gate setting.
# ---------------------------------------------------------------------

def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The PR-craft setting stored in *config*.

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
        return {"type": "pr_craft_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "pr_craft_setting_changed",
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
            f"PR craft is already {'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The /prcraft surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_prcraft_args(args: str) -> Dict[str, Any]:
    """Parse ``/prcraft`` arguments.

    /prcraft            -> show
    /prcraft on         -> turn the gate on
    /prcraft off        -> turn the gate off
    /prcraft tasks <n>  -> fetch PR <n>'s review comments as tasks
    """
    text = (args or "").strip()
    if not text:
        return {"action": "show"}
    if text == "on":
        return {"action": "setting", "enabled": True}
    if text == "off":
        return {"action": "setting", "enabled": False}
    parts = text.split()
    if len(parts) == 2 and parts[0] == "tasks":
        try:
            number = int(parts[1])
        except ValueError:
            raise ValueError(USAGE) from None
        return {"action": "tasks", "number": _check_number(number)}
    raise ValueError(USAGE)


def format_setting_change(record: Dict[str, Any]) -> str:
    """A setting change record, in plain words."""
    word = {True: "on", False: "off"}
    return (f"PR craft: {word[record['from']]} -> "
            f"{word[record['to']]}.")


def format_pull_request(pr: PullRequest) -> str:
    """A fetched pull request, in plain words."""
    state = pr.state + (" (draft)" if pr.draft else "")
    return (f"PR #{pr.number}: {pr.title} [{state}]\n"
            f"  {pr.head} -> {pr.base} by {pr.author or 'unknown'}\n"
            f"  {pr.url}")


def format_tasks(tasks: Sequence[Dict[str, Any]]) -> str:
    """Fetched review-comment tasks, in plain words."""
    if not tasks:
        return "No review comments were fetched — no tasks."
    lines = [f"Review tasks — {len(tasks)} comment(s) fetched as tasks:"]
    for task in tasks:
        place = task["path"] or "general"
        if task["line"]:
            place += f":{task['line']}"
        lines.append(
            f"  [{task['state']}] {task['task_id']} — "
            f"{task['author'] or 'unknown'} on {place}: "
            f"{task['body']}")
    return "\n".join(lines)


_SAMPLE_PR = {
    "number": 7, "title": "Add the forge bellows",
    "body": "Bellows for the forge.",
    "baseRefName": "main", "headRefName": "feature/bellows",
    "state": "OPEN", "isDraft": False,
    "url": "https://example.invalid/pr/7",
    "author": {"login": "volmarr"},
    "comments": [
        {"id": "c1", "author": {"login": "reviewer-a"},
         "body": "The handle needs a guard.",
         "path": "forge/bellows.py", "line": 42,
         "url": "https://example.invalid/pr/7#c1"},
        {"id": "c2", "author": {"login": "reviewer-b"},
         "body": "Overall shape looks right.",
         "url": "https://example.invalid/pr/7#c2"},
    ],
    "reviews": [
        {"id": "r1", "author": {"login": "reviewer-a"},
         "body": "Close — one guard short of ready.",
         "state": "CHANGES_REQUESTED"},
        {"id": "r2", "author": {"login": "reviewer-b"},
         "body": "", "state": "APPROVED"},
    ],
}

_SAMPLE_CREATED = {
    "number": 8, "url": "https://example.invalid/pr/8",
    "title": "Add the forge bellows", "state": "OPEN"}


def _sample_runner(args: Sequence[str]) -> str:
    """The worked example's fake GitHub road — no live call."""
    if list(args[:2]) == ["pr", "view"]:
        return json.dumps(_SAMPLE_PR)
    if list(args[:2]) == ["pr", "create"]:
        return json.dumps(_SAMPLE_CREATED)
    return ""


def format_pr_craft(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /prcraft.

    Built from fetch_pull_request() /
    fetch_review_comments() / comments_to_tasks() /
    prepare_review() / post_review() / prepare_pr() /
    post_pr() / prepare_reply() / post_reply() over a fake
    sample GitHub road, so every public road this module
    offers is exercised by its own show surface — and the
    sample makes no live call. The worked example shows
    the gate honestly: a review draft with no recorded
    word refuses to post, and the same draft armed with
    the user's word posts (to the fake road).
    """
    enabled = enabled_from_config(config)
    lines = ["PR craft (M-082) — " + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    lines.append("")
    pr = fetch_pull_request(_sample_runner, 7)
    lines.append("Sample fetch (fake GitHub road):")
    lines.append(format_pull_request(pr))
    tasks = comments_to_tasks(fetch_review_comments(_sample_runner, 7))
    lines.append(format_tasks(tasks))
    lines.append("")
    draft = prepare_review(
        7, "request_changes", "One guard short of ready.",
        notes=[("forge/bellows.py", 42, "Add a handle guard.")])
    try:
        post_review(_sample_runner, draft)
        lines.append("UNARMED DRAFT POSTED — the gate is broken.")
    except ValueError:
        lines.append(
            "A review draft with no recorded word refuses "
            "to post: nothing was sent.")
    post_review(_sample_runner, arm_review_draft(draft, "post it"))
    lines.append(
        "The same draft, armed with the user's word "
        "('post it'), posts its request-changes review — "
        "its line note rides in the review body:")
    lines.append(draft.review_body())
    created = post_pr(_sample_runner, arm_pr_draft(
        prepare_pr("Add the forge bellows", "Bellows for the forge.",
                   "main", "feature/bellows"), "open it"))
    lines.append(
        f"A PR draft armed with the user's word creates "
        f"PR #{created['number']} ({created['url']}).")
    post_reply(_sample_runner, arm_reply_draft(
        prepare_reply(7, "c1", "Guard added — thank you."),
        "answer it"))
    lines.append(
        "A reply draft armed with the user's word posts "
        "its answer on PR #7.")
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)
