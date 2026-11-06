"""Auto-commit discipline (All-Features roadmap slice M-078).

Part IV — The Editor's Hand. The roadmap's words: every
accepted edit set lands as its own commit with a written
message — on a working branch by default, never on the
user's protected branches unasked. (Aider's crown: the
discipline Aider is loved for, kept honestly.)

What already shipped, and what this slice adds:

* The edit roads (M-071 formats, M-072 anchored edits,
  M-073's repair loop, M-074's hunk review) write accepted
  edits through the EditJournal — but nothing landed those
  accepted edits in git. The one older helper,
  ``agents/tools.py``'s ``auto_git_commit``, commits a
  single file onto whatever branch happens to be checked
  out, protected or not, with no branch discipline at all.
* This slice is the discipline layer over git: a pure
  judgement — given the current branch, the accepted file
  set, and a written message — of exactly where a commit
  may land. The agent layer executes that judgement and
  nothing else; the commit itself is recorded on the
  session journal. This module runs no git and writes no
  file; it only judges, so the judgement can be proven
  without a repository.

Honesty rules, enforced here and pinned by the slice's
tests:

* **Every accepted edit set is its own commit.** One call,
  one commit, carrying exactly the accepted files — never
  a sweep of whatever else is dirty in the tree, and
  never folded into a neighbour's commit.
* **A commit carries a written message.** A blank or
  missing message refuses before anything is judged: an
  auto-commit with nothing to say for itself is not
  discipline, it is noise. The message the commit carries
  names the files it lands.
* **Protected branches are never committed to unasked.**
  ``main``, ``master``, ``development`` and ``develop``
  are protected by default, and the user may name more
  (or rename the set) in ``auto_commit_protected``. On a
  protected branch the default road is the working branch
  (``mythic/working`` unless the user names another):
  the commit is planned there, and the agent moves the
  accepted edits onto it. Committing onto a protected
  branch itself takes the user's explicit standing word —
  the ``auto_commit_allow_protected`` setting — and a
  commit that lands there under that word is recorded as
  on-protected, never disguised as anything else.
* **A detached head is not a branch.** With no branch
  checked out there is nowhere disciplined to land, and
  the plan refuses and says so.
* **The file set is judged, not trusted.** Absolute
  paths, ``..`` escapes, and anything under ``.git``
  refuse; duplicates are landed once. An empty set
  refuses — there is no such thing as an accepted edit
  set with no edits in it.
* **The settings are gates, not guesses.** ``auto_commit``
  ships OFF: turning it on is the user's standing word
  that accepted edit sets land as commits. Stored values
  of the wrong shape raise — never default silently.
"""

from __future__ import annotations

__all__ = [
    "ALLOW_PROTECTED_KEY",
    "AUTO_COMMIT_SLICE",
    "BRANCH_KEY",
    "DEFAULT_PROTECTED",
    "DEFAULT_WORKING_BRANCH",
    "PLAIN_EXPLANATION",
    "PROTECTED_KEY",
    "SETTING_KEY",
    "USAGE",
    "Any",
    "CommitOutcome",
    "CommitPlan",
    "Dict",
    "List",
    "Optional",
    "Sequence",
    "SettingChange",
    "Tuple",
    "allow_protected_from_config",
    "build_message",
    "enabled_from_config",
    "format_auto_commit",
    "format_commit_record",
    "format_plan",
    "format_setting_change",
    "is_protected",
    "parse_autocommit_args",
    "plan_commit",
    "protected_from_config",
    "set_allow_protected",
    "set_enabled",
    "validate_files",
    "validate_message",
    "working_branch_from_config",
]

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

#: The slice that owns this module.
AUTO_COMMIT_SLICE = "M-078"

#: The config key the auto-commit gate lives under.
SETTING_KEY = "auto_commit"

#: The config key for the explicit standing word that
#: permits committing onto a protected branch itself.
ALLOW_PROTECTED_KEY = "auto_commit_allow_protected"

#: The config key naming the working branch.
BRANCH_KEY = "auto_commit_branch"

#: The config key naming the user's protected branches.
PROTECTED_KEY = "auto_commit_protected"

#: Branches protected before the user names any: the
#: branches a coder must never land on unasked.
DEFAULT_PROTECTED: Tuple[str, ...] = (
    "main", "master", "development", "develop")

#: Where commits land by default when the current branch
#: may not be committed to.
DEFAULT_WORKING_BRANCH = "mythic/working"

#: The discipline explained in plain words — the sentence
#: every surface shows.
PLAIN_EXPLANATION = (
    "Auto-commit discipline: every accepted edit set "
    "lands as its own commit with a written message — "
    "one edit set, one commit, carrying exactly the "
    "accepted files. By default the commit lands on a "
    "working branch: if you are on a protected branch "
    "(main, master, development, develop, and any you "
    "name), the edits are moved onto the working branch "
    "and committed there, never onto the protected "
    "branch itself. Committing onto a protected branch "
    "takes your explicit standing word (the "
    "auto_commit_allow_protected setting), and a commit "
    "that lands there is recorded as on-protected. A "
    "blank message, an empty file set, or a detached "
    "head refuses and commits nothing. The discipline "
    "ships off; turning it on is the standing word that "
    "accepted edit sets land as commits."
)

USAGE = ("Usage: /autocommit, /autocommit on, "
         "/autocommit off, /autocommit allow-protected, "
         "or /autocommit block-protected")


# ---------------------------------------------------------------------
# The settings: gates, read purely from config.
# ---------------------------------------------------------------------

def _bool_from_config(config: Dict[str, Any], key: str,
                      default: bool) -> bool:
    raw = config.get(key, default)
    if not isinstance(raw, bool):
        raise ValueError(
            f"{key} must be true or false, "
            f"got {type(raw).__name__}")
    return raw


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The auto-commit gate stored in *config*.

    Absent means False (the discipline ships off). A
    stored value that is not a bool raises — never
    guessed at.
    """
    return _bool_from_config(config, SETTING_KEY, False)


def allow_protected_from_config(config: Dict[str, Any]) -> bool:
    """The standing word for protected branches.

    Absent means False: no protected branch is committed
    to. A stored value that is not a bool raises.
    """
    return _bool_from_config(config, ALLOW_PROTECTED_KEY, False)


def protected_from_config(config: Dict[str, Any]
                          ) -> Tuple[str, ...]:
    """The protected branch names stored in *config*.

    Absent means :data:`DEFAULT_PROTECTED`. A stored
    value that is not a list of branch names raises —
    a malformed protection set must never quietly
    protect nothing.
    """
    raw = config.get(PROTECTED_KEY, None)
    if raw is None:
        return DEFAULT_PROTECTED
    if isinstance(raw, str) or not isinstance(raw, (list, tuple)):
        raise ValueError(
            f"{PROTECTED_KEY} must be a list of branch "
            f"names, got {type(raw).__name__}")
    names: List[str] = []
    for name in raw:
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"{PROTECTED_KEY} names branches; got {name!r}")
        names.append(name.strip())
    if not names:
        raise ValueError(
            f"{PROTECTED_KEY} names no branch — an empty "
            "protection set protects nothing; remove the "
            "key to use the default set")
    return tuple(names)


def working_branch_from_config(config: Dict[str, Any]) -> str:
    """The working branch named in *config*.

    Absent means :data:`DEFAULT_WORKING_BRANCH`. A stored
    value that cannot name a branch raises.
    """
    raw = config.get(BRANCH_KEY, DEFAULT_WORKING_BRANCH)
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(
            f"{BRANCH_KEY} must name a branch; got {raw!r}")
    return _validate_branch_name(raw.strip(), BRANCH_KEY)


def _validate_branch_name(name: str, what: str) -> str:
    if (any(ch.isspace() for ch in name) or ".." in name
            or name.startswith(("-", "/", ".")) or name.endswith("/")
            or name.endswith(".lock")):
        raise ValueError(f"{what} cannot name a branch: {name!r}")
    return name


def is_protected(config: Dict[str, Any], branch: str) -> bool:
    """True when *branch* is protected under *config*."""
    return branch in protected_from_config(config)


@dataclass(frozen=True)
class SettingChange:
    """A recorded change of one of the slice's settings."""

    key: str
    event_type: str
    before: Any
    after: Any

    def event(self) -> Dict[str, Any]:
        return {"type": self.event_type,
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": self.event_type, "key": self.key,
                "from": self.before, "to": self.after,
                "session_id": session_id, "journaled": journaled}


def _set_bool(config: Dict[str, Any], key: str, event_type: str,
              value: Any, label: str) -> Tuple[bool, SettingChange]:
    if not isinstance(value, bool):
        raise ValueError(f"{key} is turned on or off; got {value!r}")
    before = _bool_from_config(config, key, False)
    if value == before:
        raise ValueError(
            f"{label} is already {'on' if before else 'off'}")
    return value, SettingChange(
        key=key, event_type=event_type, before=before, after=value)


def set_enabled(config: Dict[str, Any],
                enabled: Any) -> Tuple[bool, SettingChange]:
    """Validate a gate change against *config*, purely."""
    return _set_bool(config, SETTING_KEY,
                     "auto_commit_setting_changed", enabled,
                     "auto-commit")


def set_allow_protected(config: Dict[str, Any],
                        allowed: Any) -> Tuple[bool, SettingChange]:
    """Validate a protected-branch word change, purely."""
    return _set_bool(config, ALLOW_PROTECTED_KEY,
                     "auto_commit_protected_setting_changed", allowed,
                     "committing onto protected branches")


# ---------------------------------------------------------------------
# The judgement: where an accepted edit set may land.
# ---------------------------------------------------------------------

def validate_files(files: Sequence[str]) -> Tuple[str, ...]:
    """Judge an accepted edit set's file list.

    Returns the files as a tuple, duplicates landed once,
    each path proven relative, inside the tree, and not
    under ``.git``. Anything else refuses.
    """
    if isinstance(files, str) or not files:
        raise ValueError(
            "an accepted edit set names at least one file; "
            "got none — nothing was committed")
    judged: List[str] = []
    for name in files:
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"an edit set names files; got {name!r}")
        path = name.strip()
        if path.startswith("./"):
            path = path[2:]
        parts = [part for part in path.split("/") if part not in ("", ".")]
        if path.startswith("/") or ".." in parts:
            raise ValueError(
                f"an edit set file must live inside the "
                f"tree; {name!r} does not — nothing was committed")
        if parts and parts[0] == ".git":
            raise ValueError(
                f"an edit set never commits git's own "
                f"house; {name!r} refused")
        clean = "/".join(parts)
        if clean and clean not in judged:
            judged.append(clean)
    if not judged:
        raise ValueError(
            "an accepted edit set names at least one file; "
            "got none — nothing was committed")
    return tuple(judged)


def validate_message(message: str) -> str:
    """Judge a commit message: written, or refused.

    Returns the message stripped of surrounding blank
    space. A blank message refuses — a commit with
    nothing to say for itself is not discipline.
    """
    if not isinstance(message, str) or not message.strip():
        raise ValueError(
            "an auto-commit needs a written message; a "
            "blank message refuses — nothing was committed")
    return message.strip()


def build_message(summary: str,
                  files: Sequence[str]) -> str:
    """Compose the written message an accepted set carries.

    The caller's *summary* is the message's own words;
    the landed files are named beneath it, so the commit
    says what it carries. A blank summary refuses.
    """
    judged = validate_files(files)
    text = validate_message(summary)
    lines = [text, "", "Files:"]
    lines.extend(f"  - {name}" for name in judged)
    return "\n".join(lines)


@dataclass(frozen=True)
class CommitPlan:
    """Where one accepted edit set will land, as data.

    ``branch`` is the branch checked out now; the commit
    lands on ``target_branch``. ``switch_needed`` says the
    agent must move onto the target first (the protected
    road); ``on_protected`` says the target is a protected
    branch, landed on under the user's standing word and
    recorded as exactly that.
    """

    branch: str
    target_branch: str
    on_protected: bool
    switch_needed: bool
    files: Tuple[str, ...]
    message: str
    protected: Tuple[str, ...]

    def describe(self) -> Dict[str, Any]:
        return {"branch": self.branch,
                "target_branch": self.target_branch,
                "on_protected": self.on_protected,
                "switch_needed": self.switch_needed,
                "files": list(self.files),
                "message": self.message,
                "protected": list(self.protected)}


def plan_commit(config: Dict[str, Any], branch: str,
                files: Sequence[str], message: str) -> CommitPlan:
    """Judge where an accepted edit set may land.

    Pure: no git is run and nothing is written — the
    agent layer executes this plan and nothing else.
    On an ordinary branch the commit lands there. On a
    protected branch it lands on the working branch
    (a switch the agent must make), unless the user's
    standing word permits the protected branch itself.
    A detached head, a blank message, and a judged-bad
    file set all refuse.
    """
    judged_files = validate_files(files)
    judged_message = validate_message(message)
    if not isinstance(branch, str) or not branch.strip():
        raise ValueError(
            "auto-commit needs the current branch named; "
            "got none — nothing was committed")
    current = branch.strip()
    if current == "HEAD":
        raise ValueError(
            "auto-commit needs a branch checked out; a "
            "detached head is not a branch and has nowhere "
            "disciplined to land — nothing was committed")
    protected = protected_from_config(config)
    if current not in protected:
        return CommitPlan(
            branch=current, target_branch=current,
            on_protected=False, switch_needed=False,
            files=judged_files, message=judged_message,
            protected=protected)
    if allow_protected_from_config(config):
        return CommitPlan(
            branch=current, target_branch=current,
            on_protected=True, switch_needed=False,
            files=judged_files, message=judged_message,
            protected=protected)
    working = working_branch_from_config(config)
    if working in protected:
        raise ValueError(
            f"the working branch {working!r} is itself "
            "protected — name an unprotected working "
            f"branch in {BRANCH_KEY}; nothing was committed")
    return CommitPlan(
        branch=current, target_branch=working,
        on_protected=False, switch_needed=True,
        files=judged_files, message=judged_message,
        protected=protected)


@dataclass(frozen=True)
class CommitOutcome:
    """What one auto-commit did, in counted plain data."""

    committed: bool
    branch: str
    target_branch: str
    on_protected: bool
    switched: bool
    files: Tuple[str, ...]
    message: str
    commit: Optional[str] = None
    reason: str = ""

    def event(self) -> Dict[str, Any]:
        return {"type": "auto_commit_committed",
                "committed": self.committed,
                "branch": self.branch,
                "target_branch": self.target_branch,
                "on_protected": self.on_protected,
                "switched": self.switched,
                "files": list(self.files),
                "message": self.message,
                "commit": self.commit,
                "reason": self.reason}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {**self.event(), "session_id": session_id,
                "journaled": journaled}


# ---------------------------------------------------------------------
# The /autocommit surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_autocommit_args(args: str) -> Dict[str, Any]:
    """Parse ``/autocommit`` arguments.

    /autocommit                -> show
    /autocommit on             -> turn the gate on
    /autocommit off            -> turn the gate off
    /autocommit allow-protected -> standing word: protected
                                   branches may be committed to
    /autocommit block-protected -> withdraw that word
    """
    text = (args or "").strip()
    if not text:
        return {"action": "show"}
    if text == "on":
        return {"action": "setting", "enabled": True}
    if text == "off":
        return {"action": "setting", "enabled": False}
    if text == "allow-protected":
        return {"action": "protected_setting", "allowed": True}
    if text == "block-protected":
        return {"action": "protected_setting", "allowed": False}
    raise ValueError(USAGE)


def format_setting_change(record: Dict[str, Any]) -> str:
    """A setting change record, in plain words."""
    word = {True: "on", False: "off"}
    if record.get("key") == ALLOW_PROTECTED_KEY:
        named = {True: "allowed", False: "blocked"}
        return ("Auto-commit on protected branches: "
                f"{named[record['from']]} -> {named[record['to']]}.")
    return (f"Auto-commit: {word[record['from']]} -> "
            f"{word[record['to']]}.")


def format_plan(plan: CommitPlan) -> str:
    """A commit plan, in plain words."""
    subject = plan.message.splitlines()[0]
    if plan.on_protected:
        landing = (f"lands on protected branch "
                   f"{plan.target_branch!r} itself, under your "
                   "standing word, and is recorded as on-protected")
    elif plan.switch_needed:
        landing = (f"moves from protected branch {plan.branch!r} "
                   f"onto working branch {plan.target_branch!r} "
                   "and lands there")
    else:
        landing = f"lands on branch {plan.target_branch!r}"
    return (f"Commit plan: {len(plan.files)} file(s) "
            f"({', '.join(plan.files)}) with message "
            f"{subject!r} {landing}.")


def format_commit_record(record: Dict[str, Any]) -> str:
    """An auto-commit outcome record, in plain words."""
    if not record["committed"]:
        return f"Auto-commit: nothing committed — {record['reason']}"
    subject = record["message"].splitlines()[0]
    where = record["target_branch"]
    if record["on_protected"]:
        where += " (protected, under your standing word)"
    elif record["switched"]:
        where += f" (moved from {record['branch']})"
    return (f"Auto-commit: committed {record['commit']} on "
            f"{where} — {subject!r} "
            f"({len(record['files'])} file(s)).")


def format_auto_commit(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /autocommit.

    Built from plan_commit() / build_message() /
    format_plan() over sample branches, so every public
    road this module offers is exercised by its own show
    surface: an edit set on an ordinary branch lands
    there; the same set on a protected branch is planned
    onto the working branch instead.
    """
    enabled = enabled_from_config(config)
    allowed = allow_protected_from_config(config)
    protected = protected_from_config(config)
    working = working_branch_from_config(config)
    lines = ["Auto-commit discipline (M-078) — "
             + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}). Protected branches: "
                 f"{', '.join(protected)}. Working branch: "
                 f"{working}. Committing onto a protected "
                 f"branch is {'allowed' if allowed else 'blocked'} "
                 f"({ALLOW_PROTECTED_KEY}).")
    lines.append("")
    message = build_message("Fix the login redirect",
                            ["app.py", "test_app.py"])
    plan = plan_commit(config, "feature/login",
                       ["app.py", "test_app.py"], message)
    lines.append("On an ordinary branch: " + format_plan(plan))
    default_road = dict(config)
    default_road[ALLOW_PROTECTED_KEY] = False
    plan = plan_commit(default_road, protected[0],
                       ["app.py", "test_app.py"], message)
    lines.append("On a protected branch, by default: "
                 + format_plan(plan))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)
