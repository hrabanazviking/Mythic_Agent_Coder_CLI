"""Multi-repo workspaces (All-Features roadmap slice M-113).

Part V - Autonomy & Safety. The roadmap's words:
``several repos under one session with per-repo
policies; cross-repo changes are one change set,
reviewed whole.``

What already shipped, and what this slice adds:

* A workspace already has a portable identity and
  contained file resolution
  (``mythic_agent/core/workspace.py`` -
  ``canonical_workspace_root`` / ``workspace_id`` /
  ``resolve_file``): one directory, one identity.
  Nothing held *several* repos under one session.
* The elder ``core/policy.py`` ``ToolPolicy``
  knows three modes (read-only, ask, trusted) and
  permission profiles name a session posture
  (``permission_profiles.py``, M-095), but no
  policy was held *per repo*: a session spanning
  a careful repo and a scratch repo had one answer
  for both.
* Change sets are already a named, reviewable
  unit across files, reviewed file by file and
  applied all-or-nothing in memory first
  (``change_sets.py``, M-084,
  ``start_change_set`` / ``decide`` /
  ``attach_evidence`` / ``apply_change_set``).
  Nothing grouped edits *across repos* into that
  one unit: a cross-repo change was several sets,
  reviewed piecemeal, with no whole to review.
* This slice is that missing workspace layer, as
  a pure layer in the exact sibling shape: a repo
  entry and its per-repo policy held as validated
  data, a workspace of several repos under one
  session held as validated data, a cross-repo
  change set built ON the M-084 machinery (its
  edits are one ``ChangeSet``, prefixed by repo,
  decided and planned by M-084's own roads,
  unchanged), a cross-repo record shaped as
  session news, and a small in-memory registry
  model with deterministic ids. This module
  opens no repo, writes no file, changes no
  setting and imports no agent / UI code; the
  agent layer owns holding the registry for a
  session.

Honesty rules, enforced here and pinned by tests:

* **No repo is invented.** A workspace holds only
  the repos it was built naming; a repo id no
  held repo carries refuses plainly, in words,
  wherever it is asked for - never guessed at,
  never defaulted to another repo.
* **Per-repo policy is data, judged as data.**
  Each repo's policy names its mode (the elder
  policy road's own three: read_only, ask,
  trusted), the branch its work targets, and
  whether its changes require review. A
  read_only repo refuses a change-set member
  plainly, naming the repo - its policy is
  enforced at build time, not discovered at
  apply time.
* **Cross-repo changes are ONE change set.**
  Every member edit, from every repo, lives in
  a single M-084 ``ChangeSet`` under one name;
  it is decided file by file and planned whole
  by M-084's all-or-nothing road: one undecided
  file or one stale file refuses the whole set
  and nothing is planned for any repo. There is
  no road here that applies one repo's part
  alone.
* **One repo, one root; one file, one edit.**
  A workspace naming one repo id twice, or two
  repos at one root, refuses at construction;
  a set naming one file in one repo twice
  refuses through M-084's own rule.
* **Status is never carried by colour or symbol
  alone.** Every formatter states each repo's
  policy and each set's decision counts in
  words.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, List, Optional, Tuple

from .change_sets import (
    ChangeSet,
    attach_evidence,
    decide,
    make_edit,
    start_change_set,
)
from .change_sets import apply_change_set as _apply_m084

__all__ = [
    "MODE_PHRASES",
    "MULTI_REPO_SLICE",
    "PLAIN_EXPLANATION",
    "POLICY_MODES",
    "USAGE",
    "CrossRepoChangeSet",
    "CrossSet",
    "MultiRepoRegistry",
    "MultiRepoWorkspace",
    "Policy",
    "Repo",
    "RepoEntry",
    "RepoPolicy",
    "Workspace",
    "build_cross_repo_change_set",
    "build_policy",
    "build_repo",
    "build_workspace",
    "format_cross_set",
    "format_multi_repo_record",
    "format_multi_repo_screen",
    "format_record",
    "format_repo",
    "format_repos",
    "format_set",
    "format_sets",
    "multi_repo_record",
    "normalize_branch",
    "normalize_policy_mode",
    "normalize_repo_id",
    "normalize_set_id",
    "parse_multirepo_args",
    "plan_cross_repo_change_set",
    "plain_words",
    "validate_policy",
    "validate_repo",
    "validate_workspace",
]

MULTI_REPO_SLICE = "M-113"

#: The elder policy road's three modes, one per
#: repo: what this session may do in that repo.
POLICY_MODES = ("read_only", "ask", "trusted")

#: Each mode, said in plain words.
MODE_PHRASES = {
    "read_only": "read-only (no changes)",
    "ask": "ask before changes",
    "trusted": "trusted for changes",
}

_MODE_WORDS = {
    "read_only": "read_only", "readonly": "read_only",
    "read-only": "read_only", "read": "read_only",
    "ask": "ask", "ask_first": "ask",
    "trusted": "trusted", "trust": "trusted",
    "full": "trusted",
}

PLAIN_EXPLANATION = (
    "Multi-repo workspaces: several repos live "
    "under one session, each with its own policy "
    "- its mode (read-only, ask, or trusted, the "
    "elder policy road's three), the branch its "
    "work targets, and whether its changes "
    "require review. A change that spans repos "
    "is ONE change set (the M-084 machinery, "
    "unchanged): every file in every repo is "
    "decided under one name and the set is "
    "planned whole, all-or-nothing - one "
    "undecided or stale file refuses the whole "
    "set for every repo, and no repo's part ever "
    "applies alone. A repo this session does not "
    "hold refuses plainly; a read-only repo "
    "refuses a change-set member at build time. "
    "This layer holds the workspace and its sets "
    "as data only; the agent layer holds them "
    "for a session."
)

USAGE = (
    "Usage: /multirepo, /multirepo show, "
    "/multirepo show <set>, /multirepo repos"
)

_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_.")

_REPO_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz0123456789_-")

_BRANCH_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_./")


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _pick(mapping: Dict[str, Any], names: Tuple[str, ...],
          what: str) -> Any:
    """One field from its spellings, or a refusal on conflict."""
    found = [name for name in names if name in mapping]
    if not found:
        return None
    first = mapping[found[0]]
    for name in found[1:]:
        if mapping[name] != first:
            raise ValueError(
                f"a multi-repo record names two different {what}")
    return first


def normalize_policy_mode(value: Any) -> str:
    """The canonical per-repo policy mode a word names.

    Reads the elder policy road's three modes
    (and their short spellings), case-insensitively.
    Any other word refuses: the modes are a closed
    vocabulary of three.
    """
    if isinstance(value, str):
        wanted = value.strip().lower()
        if wanted in _MODE_WORDS:
            return _MODE_WORDS[wanted]
    raise ValueError(
        "a repo policy mode must be one of %s, got %r"
        % ("/".join(POLICY_MODES), value))


def normalize_repo_id(value: Any) -> str:
    """The canonical repo id a word names.

    A repo id is lowercase letters, digits,
    underscores and dashes, read case-insensitively
    with spaces read as dashes. Anything else
    raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace(" ", "-")
        if wanted and all(
                ch in _REPO_ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"a repo id must be a word of lowercase letters, "
        f"digits, underscores and dashes, got {value!r}")


def normalize_set_id(value: Any) -> str:
    """The canonical cross-repo set id a word names.

    A set id is one word of letters, digits,
    dashes, underscores and dots, read with its
    case kept. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and all(ch in _ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"a set id must be a non-empty word of letters, "
        f"digits, dashes, underscores and dots, got {value!r}")


def normalize_branch(value: Any) -> str:
    """The branch name a policy targets, as data.

    A branch is one word of letters, digits,
    dashes, underscores, dots and slashes, with
    no leading or trailing slash and no empty
    segment. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and all(
                ch in _BRANCH_CHARS for ch in wanted) \
                and not wanted.startswith(("/", ".")) \
                and not wanted.endswith(("/", ".")) \
                and "//" not in wanted and ".." not in wanted:
            return wanted
    raise ValueError(
        f"a branch must be a branch name, got {value!r}")


# ---------------------------------------------------------------------
# The per-repo policy: one repo's rules, held as validated data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class RepoPolicy:
    """One repo's policy under this session, as data.

    ``mode`` is one of the elder policy road's
    three modes; ``branch`` names the branch this
    repo's work targets; ``requires_review`` says
    whether this repo's changes must be reviewed
    before they land. Constructing one validates
    it.
    """

    mode: str = "ask"
    branch: str = "main"
    requires_review: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "mode", normalize_policy_mode(self.mode))
        object.__setattr__(
            self, "branch", normalize_branch(self.branch))
        if not isinstance(self.requires_review, bool):
            raise ValueError(
                "requires_review must be true or false, got %r"
                % (self.requires_review,))

    @property
    def writable(self) -> bool:
        """Whether this policy ever allows a change."""
        return self.mode != "read_only"

    def to_record(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "branch": self.branch,
            "requires_review": self.requires_review,
            "writable": self.writable,
        }


#: The shorter word for a repo policy.
Policy = RepoPolicy

_POLICY_KEYS = frozenset({
    "mode", "permission", "branch", "target_branch",
    "requires_review", "review",
})


def validate_policy(policy: Any) -> RepoPolicy:
    """Validate one repo policy into a RepoPolicy.

    Accepts a RepoPolicy or a mapping naming a
    ``mode`` (or ``permission``), a ``branch``
    (or ``target_branch``) and ``requires_review``
    (or ``review``). Naming two spellings of one
    field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(policy, RepoPolicy):
        return policy
    if policy is None:
        return RepoPolicy()
    if not isinstance(policy, dict):
        raise ValueError(
            f"a repo policy must be a mapping, got {policy!r}")
    unknown = set(policy) - _POLICY_KEYS
    if unknown:
        raise ValueError(
            "unknown policy keys: %s" % ", ".join(sorted(unknown)))
    kwargs: Dict[str, Any] = {}
    mode = _pick(policy, ("mode", "permission"), "modes")
    if mode is not None:
        kwargs["mode"] = mode
    branch = _pick(policy, ("branch", "target_branch"), "branches")
    if branch is not None:
        kwargs["branch"] = branch
    review = _pick(
        policy, ("requires_review", "review"), "review flags")
    if review is not None:
        kwargs["requires_review"] = review
    return RepoPolicy(**kwargs)


def build_policy(policy: Any = None, **kwargs: Any) -> RepoPolicy:
    """Build one validated policy from a mapping or field words."""
    if isinstance(policy, RepoPolicy) and not kwargs:
        return policy
    if isinstance(policy, dict) or policy is None:
        merged: Dict[str, Any] = {}
        if isinstance(policy, dict):
            merged.update(policy)
        merged.update(kwargs)
        return validate_policy(merged)
    raise ValueError(
        f"a repo policy must be a mapping, got {policy!r}")


# ---------------------------------------------------------------------
# The repo entry: one held repo and its policy.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class RepoEntry:
    """One repo held under the session, as data.

    ``repo_id`` names the repo in this session,
    ``root`` is the repo's root as named when it
    was registered (this layer holds the name as
    data - canonical identity is workspace.py's
    road, walked by callers that touch the disk),
    ``label`` says the repo in plain words, and
    ``policy`` is its per-repo policy. Constructing
    one validates it.
    """

    repo_id: str
    root: str
    label: str = ""
    policy: RepoPolicy = RepoPolicy()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "repo_id", normalize_repo_id(self.repo_id))
        object.__setattr__(
            self, "root", _clean_text(self.root, "a repo root"))
        label = self.label.strip() if isinstance(
            self.label, str) else self.label
        if not isinstance(label, str):
            raise ValueError("a repo label must be text")
        object.__setattr__(self, "label", label or self.repo_id)
        object.__setattr__(
            self, "policy", validate_policy(self.policy))

    @property
    def display_label(self) -> str:
        return f"{self.repo_id} ({self.label})"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "multi_repo_repo",
            "slice": MULTI_REPO_SLICE,
            "repo_id": self.repo_id,
            "root": self.root,
            "label": self.label,
            "policy": self.policy.to_record(),
        }


#: The shorter word for a repo entry.
Repo = RepoEntry

_REPO_KEYS = frozenset({
    "repo_id", "id", "name", "root", "path",
    "label", "title", "policy",
})


def validate_repo(repo: Any) -> RepoEntry:
    """Validate one repo entry into a RepoEntry.

    Accepts a RepoEntry or a mapping naming a
    ``repo_id`` (or ``id`` / ``name``), a ``root``
    (or ``path``), optionally a ``label`` (or
    ``title``) and a ``policy``. Naming two
    spellings of one field with different values
    refuses, and unknown keys refuse.
    """
    if isinstance(repo, RepoEntry):
        return repo
    if not isinstance(repo, dict):
        raise ValueError(
            f"a repo entry must be a mapping, got {repo!r}")
    unknown = set(repo) - _REPO_KEYS
    if unknown:
        raise ValueError(
            "unknown repo keys: %s" % ", ".join(sorted(unknown)))
    repo_id = _pick(repo, ("repo_id", "id", "name"), "repo ids")
    root = _pick(repo, ("root", "path"), "roots")
    if repo_id is None or root is None:
        raise ValueError(
            "a repo entry must name its repo_id and root")
    kwargs: Dict[str, Any] = {"repo_id": repo_id, "root": root}
    label = _pick(repo, ("label", "title"), "labels")
    if label is not None:
        kwargs["label"] = label
    if "policy" in repo:
        kwargs["policy"] = repo["policy"]
    return RepoEntry(**kwargs)


def build_repo(repo: Any = None, **kwargs: Any) -> RepoEntry:
    """Build one validated repo entry from a mapping or words."""
    if isinstance(repo, RepoEntry) and not kwargs:
        return repo
    if isinstance(repo, dict) or repo is None:
        merged: Dict[str, Any] = {}
        if isinstance(repo, dict):
            merged.update(repo)
        merged.update(kwargs)
        return validate_repo(merged)
    raise ValueError(
        f"a repo entry must be a mapping, got {repo!r}")


# ---------------------------------------------------------------------
# The workspace: several repos under one session, held as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MultiRepoWorkspace:
    """Several repos under one session, as data.

    ``name`` names the workspace; ``repos`` is
    its held repos in the order named. One repo
    id names one repo and one root names one
    repo - a workspace built naming either twice
    refuses. Constructing one validates it.
    """

    name: str
    repos: Tuple[RepoEntry, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "name", _clean_text(self.name, "a workspace name"))
        if isinstance(self.repos, (str, bytes)) \
                or not isinstance(self.repos, (list, tuple)):
            raise ValueError("workspace repos must be a list of repos")
        cleaned = tuple(validate_repo(repo) for repo in self.repos)
        if not cleaned:
            raise ValueError(
                "a multi-repo workspace must hold at least one repo")
        ids = [repo.repo_id for repo in cleaned]
        if len(set(ids)) != len(ids):
            raise ValueError(
                "a workspace names one repo id twice - "
                "one repo id names one repo")
        roots = [repo.root for repo in cleaned]
        if len(set(roots)) != len(roots):
            raise ValueError(
                "a workspace names one root twice - "
                "one root names one repo")
        object.__setattr__(self, "repos", cleaned)

    @property
    def repo_ids(self) -> Tuple[str, ...]:
        return tuple(repo.repo_id for repo in self.repos)

    @property
    def repo_count(self) -> int:
        return len(self.repos)

    def repo_for(self, repo_id: Any) -> RepoEntry:
        """The one held repo an id names.

        An id no held repo carries refuses plainly:
        this session holds no such repo, and no
        other repo is ever substituted for it.
        """
        wanted = normalize_repo_id(repo_id)
        for repo in self.repos:
            if repo.repo_id == wanted:
                return repo
        raise ValueError(
            f"unknown repo: {wanted!r} - this workspace "
            f"holds {', '.join(self.repo_ids)}")

    def has_repo(self, repo_id: Any) -> bool:
        try:
            self.repo_for(repo_id)
        except ValueError:
            return False
        return True

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "multi_repo_workspace",
            "slice": MULTI_REPO_SLICE,
            "name": self.name,
            "repo_ids": list(self.repo_ids),
            "repos": [repo.to_record() for repo in self.repos],
        }


#: The shorter word for a multi-repo workspace.
Workspace = MultiRepoWorkspace

_WORKSPACE_KEYS = frozenset({
    "name", "workspace", "repos", "repositories",
})


def validate_workspace(workspace: Any) -> MultiRepoWorkspace:
    """Validate one workspace into a MultiRepoWorkspace.

    Accepts a MultiRepoWorkspace or a mapping
    naming a ``name`` (or ``workspace``) and
    ``repos`` (or ``repositories``). Naming two
    spellings of one field with different values
    refuses, and unknown keys refuse.
    """
    if isinstance(workspace, MultiRepoWorkspace):
        return workspace
    if not isinstance(workspace, dict):
        raise ValueError(
            f"a workspace must be a mapping, got {workspace!r}")
    unknown = set(workspace) - _WORKSPACE_KEYS
    if unknown:
        raise ValueError(
            "unknown workspace keys: %s" % ", ".join(sorted(unknown)))
    name = _pick(workspace, ("name", "workspace"), "names")
    repos = _pick(workspace, ("repos", "repositories"), "repos")
    if name is None or repos is None:
        raise ValueError(
            "a workspace must name its name and repos")
    return MultiRepoWorkspace(name=name, repos=repos)


def build_workspace(workspace: Any = None,
                    **kwargs: Any) -> MultiRepoWorkspace:
    """Build one validated workspace from a mapping or words."""
    if isinstance(workspace, MultiRepoWorkspace) and not kwargs:
        return workspace
    if isinstance(workspace, dict) or workspace is None:
        merged: Dict[str, Any] = {}
        if isinstance(workspace, dict):
            merged.update(workspace)
        merged.update(kwargs)
        return validate_workspace(merged)
    raise ValueError(
        f"a workspace must be a mapping, got {workspace!r}")


# ---------------------------------------------------------------------
# The cross-repo change set: ONE M-084 change set spanning repos.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CrossRepoChangeSet:
    """One change set spanning repos, reviewed whole.

    ``change_set`` is the one M-084 ``ChangeSet``
    holding every member edit from every repo,
    each path prefixed with its repo id
    (``<repo_id>/<path>``) so the set is a single
    reviewable unit on M-084's unchanged roads.
    ``repo_ids`` names the repos the set spans,
    in workspace order. Constructing one
    validates it against its own change set.
    """

    name: str
    workspace_name: str
    repo_ids: Tuple[str, ...]
    change_set: ChangeSet
    set_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "name", _clean_text(self.name, "a set name"))
        object.__setattr__(
            self, "workspace_name",
            _clean_text(self.workspace_name, "a workspace name"))
        if not isinstance(self.change_set, ChangeSet):
            raise ValueError(
                "a cross-repo set is built on an M-084 change set")
        if self.change_set.name != self.name:
            raise ValueError(
                "a cross-repo set and its change set must "
                "share one name")
        ids = tuple(normalize_repo_id(repo_id)
                    for repo_id in self.repo_ids)
        if not ids:
            raise ValueError(
                "a cross-repo set must span at least one repo")
        if len(set(ids)) != len(ids):
            raise ValueError("a cross-repo set names one repo twice")
        spanned = set()
        for edit in self.change_set.edits:
            head, sep, _ = edit.path.partition("/")
            if not sep or head not in ids:
                raise ValueError(
                    f"change set edit {edit.path!r} does not "
                    f"belong to a repo this set spans")
            spanned.add(head)
        if spanned != set(ids):
            raise ValueError(
                "a cross-repo set must hold at least one edit "
                "in every repo it names")
        object.__setattr__(self, "repo_ids", ids)
        if self.set_id is not None:
            object.__setattr__(
                self, "set_id", normalize_set_id(self.set_id))

    @property
    def display_label(self) -> str:
        name = self.set_id or "set"
        return f"{name} ({self.name})"

    def counts(self) -> Dict[str, int]:
        return self.change_set.counts()

    def undecided(self) -> List[int]:
        return self.change_set.undecided()

    @property
    def reviewed_whole(self) -> bool:
        """Whether every file in every repo is decided."""
        return not self.change_set.undecided()

    def decide_file(self, index: int, decision: str) -> "CrossRepoChangeSet":
        """Decide one file, on M-084's road, under the one name."""
        return replace(
            self, change_set=decide(self.change_set, index, decision))

    def attach(self, evidence: Any) -> "CrossRepoChangeSet":
        """Attach test evidence, on M-084's road."""
        return replace(
            self, change_set=attach_evidence(self.change_set, evidence))

    def to_record(self) -> Dict[str, Any]:
        counts = self.counts()
        return {
            "type": "multi_repo_change_set",
            "slice": MULTI_REPO_SLICE,
            "set_id": self.set_id,
            "name": self.name,
            "workspace": self.workspace_name,
            "repo_ids": list(self.repo_ids),
            "files": [edit.path for edit in self.change_set.edits],
            "decisions": list(self.change_set.decisions),
            "accepted": counts["accepted"],
            "rejected": counts["rejected"],
            "pending": counts["pending"],
            "reviewed_whole": self.reviewed_whole,
            "evidence": (self.change_set.evidence.record()
                         if self.change_set.evidence is not None
                         else None),
        }


#: The shorter word for a cross-repo change set.
CrossSet = CrossRepoChangeSet

_MEMBER_KEYS = frozenset({
    "repo_id", "repo", "path", "file",
    "format_id", "format", "payload", "text",
})


def build_cross_repo_change_set(
        workspace: Any, name: Any,
        members: Any) -> CrossRepoChangeSet:
    """Build ONE change set spanning repos, reviewed whole.

    ``workspace`` is the session's held workspace
    (a MultiRepoWorkspace or its mapping);
    ``members`` is a list of mappings, each naming
    a ``repo_id`` (or ``repo``), a ``path`` (or
    ``file``), a ``format_id`` (or ``format``) and
    a ``payload`` (or ``text``) - each member is
    built by M-084's ``make_edit`` unchanged, its
    path prefixed with its repo id. A member
    naming a repo the workspace does not hold
    refuses plainly; a member for a read-only
    repo refuses plainly, naming that repo's
    policy; one file named twice in one repo
    refuses through M-084's own one-file-one-edit
    rule. The set spans exactly the repos its
    members touch, in workspace order.
    """
    held = validate_workspace(workspace)
    set_name = _clean_text(name, "a set name")
    if isinstance(members, (str, bytes)) \
            or not isinstance(members, (list, tuple)):
        raise ValueError("cross-repo members must be a list")
    if not members:
        raise ValueError(
            "a cross-repo change set needs at least one member edit")
    edits = []
    touched = []
    for member in members:
        if not isinstance(member, dict):
            raise ValueError(
                f"a cross-repo member must be a mapping, got {member!r}")
        unknown = set(member) - _MEMBER_KEYS
        if unknown:
            raise ValueError(
                "unknown member keys: %s" % ", ".join(sorted(unknown)))
        repo_id = _pick(member, ("repo_id", "repo"), "repo ids")
        path = _pick(member, ("path", "file"), "paths")
        format_id = _pick(member, ("format_id", "format"), "formats")
        payload = _pick(member, ("payload", "text"), "payloads")
        if repo_id is None or path is None \
                or format_id is None or payload is None:
            raise ValueError(
                "a cross-repo member must name its repo_id, "
                "path, format_id and payload")
        repo = held.repo_for(repo_id)
        if not repo.policy.writable:
            raise ValueError(
                f"repo {repo.repo_id!r} is read-only under its "
                f"policy - it refuses a change-set member; "
                f"no set was built")
        edits.append(make_edit(
            f"{repo.repo_id}/{path}", format_id, payload))
        if repo.repo_id not in touched:
            touched.append(repo.repo_id)
    ordered = tuple(repo_id for repo_id in held.repo_ids
                    if repo_id in touched)
    change_set = start_change_set(set_name, edits)
    return CrossRepoChangeSet(
        name=set_name, workspace_name=held.name,
        repo_ids=ordered, change_set=change_set)


def plan_cross_repo_change_set(
        cross: Any, currents_by_repo: Any):
    """Plan a cross-repo set whole, on M-084's road.

    ``currents_by_repo`` maps each repo id to its
    files' true current texts (a path absent, or
    mapped to None, is a file that does not exist
    yet). Every repo the set spans must be named -
    a missing repo refuses plainly rather than
    planning against a guessed empty tree. The
    planning itself is M-084's ``apply_change_set``
    unchanged: all-or-nothing, so one undecided or
    stale file refuses the whole set for every
    repo and nothing is planned at all. Returns
    ``(new texts by repo, outcome)`` - a plan,
    never a write.
    """
    if not isinstance(cross, CrossRepoChangeSet):
        raise ValueError("planning needs a cross-repo change set")
    if not isinstance(currents_by_repo, dict):
        raise ValueError("currents must be named per repo")
    flat: Dict[str, Optional[str]] = {}
    for repo_id in cross.repo_ids:
        if repo_id not in currents_by_repo:
            raise ValueError(
                f"no current texts were named for repo "
                f"{repo_id!r} - a cross-repo set is planned "
                f"whole or not at all")
        per_repo = currents_by_repo[repo_id]
        if not isinstance(per_repo, dict):
            raise ValueError(
                f"currents for repo {repo_id!r} must be a mapping")
        for path, text in per_repo.items():
            flat[f"{repo_id}/{path}"] = text
    new_texts, outcome = _apply_m084(cross.change_set, flat)
    by_repo: Dict[str, Dict[str, str]] = {}
    for full_path, text in new_texts.items():
        repo_id, _, path = full_path.partition("/")
        by_repo.setdefault(repo_id, {})[path] = text
    return by_repo, outcome


# ---------------------------------------------------------------------
# The news record: one cross-repo set, shaped as session news.
# ---------------------------------------------------------------------


def plain_words(cross: Any) -> str:
    """One cross-repo set, in plain words - reviewed whole.

    The headline always names the set, the repos
    it spans and its decision counts in words: a
    set still holding undecided files is stated
    as not yet reviewed whole, never as ready.
    """
    if not isinstance(cross, CrossRepoChangeSet):
        raise ValueError("plain words need a cross-repo change set")
    counts = cross.counts()
    repos = ", ".join(cross.repo_ids)
    files = len(cross.change_set.edits)
    if cross.reviewed_whole:
        return (
            f"Cross-repo change set {cross.name!r} spans "
            f"{len(cross.repo_ids)} repos ({repos}) with "
            f"{files} files - reviewed whole as one change "
            f"set: {counts['accepted']} accepted, "
            f"{counts['rejected']} rejected, none undecided.")
    return (
        f"Cross-repo change set {cross.name!r} spans "
        f"{len(cross.repo_ids)} repos ({repos}) with "
        f"{files} files - not yet reviewed whole: "
        f"{counts['pending']} of {files} files still "
        f"undecided, and nothing applies until every "
        f"file in every repo is decided.")


def multi_repo_record(cross: Any) -> Dict[str, Any]:
    """The session-news record of one cross-repo set.

    Every held cross-repo set yields a record -
    the agent layer publishes this record as a
    session event, so a cross-repo change is
    announced in plain words in its headline,
    never lost as a mere log line. The record
    names the set, its workspace, its repos, its
    files and its decision counts.
    """
    if not isinstance(cross, CrossRepoChangeSet):
        raise ValueError("a record needs a cross-repo change set")
    record = cross.to_record()
    return {
        "type": "multi_repo_change_set",
        "news": True,
        "slice": MULTI_REPO_SLICE,
        "set_id": record["set_id"],
        "name": record["name"],
        "workspace": record["workspace"],
        "repo_ids": record["repo_ids"],
        "files": record["files"],
        "accepted": record["accepted"],
        "rejected": record["rejected"],
        "pending": record["pending"],
        "reviewed_whole": record["reviewed_whole"],
        "headline": plain_words(cross),
    }


# ---------------------------------------------------------------------
# The registry model: a session's repos and cross-repo sets, ids
# deterministic.
# ---------------------------------------------------------------------


class MultiRepoRegistry:
    """An in-memory, storage-neutral multi-repo registry.

    Repos are held in the order registered, under
    their repo ids (a duplicate id refuses), and
    cross-repo sets are held in the order built.
    Set ids are deterministic: a caller-supplied
    id is used as given (a duplicate refuses), and
    an unsupplied id is the next ``set-N`` in
    sequence, skipping any number a supplied id
    already took - no randomness a test cannot
    pin. Storage beyond memory is the agent
    layer's concern; this model is neutral.
    """

    def __init__(self) -> None:
        self._repos: Dict[str, RepoEntry] = {}
        self._sets: Dict[str, CrossRepoChangeSet] = {}
        self._next = 1

    # -- repos -------------------------------------------------------

    def register_repo(self, repo: Any = None,
                      **kwargs: Any) -> RepoEntry:
        """Hold one repo for the session, under its repo id."""
        entry = build_repo(repo, **kwargs) if (repo is not None or kwargs) \
            else build_repo(repo)
        if entry.repo_id in self._repos:
            raise ValueError(
                f"a repo named {entry.repo_id!r} is already held")
        self._repos[entry.repo_id] = entry
        return entry

    def get_repo(self, repo_id: Any) -> RepoEntry:
        """The held repo one id names; an unknown id refuses plainly."""
        wanted = normalize_repo_id(repo_id)
        if wanted not in self._repos:
            if self._repos:
                raise ValueError(
                    f"unknown repo: {wanted!r} - this session "
                    f"holds {', '.join(self._repos)}")
            raise ValueError(
                f"unknown repo: {wanted!r} - this session "
                f"holds no repos")
        return self._repos[wanted]

    def list_repos(self) -> Tuple[RepoEntry, ...]:
        """Every held repo, in the order registered, as a tuple."""
        return tuple(self._repos.values())

    def workspace(self, name: Any) -> MultiRepoWorkspace:
        """The held repos as one workspace under ``name``."""
        return MultiRepoWorkspace(
            name=name, repos=tuple(self._repos.values()))

    # -- cross-repo sets ----------------------------------------------

    def _fresh_id(self) -> str:
        while f"set-{self._next}" in self._sets:
            self._next += 1
        set_id = f"set-{self._next}"
        self._next += 1
        return set_id

    def register(self, cross: Any) -> CrossRepoChangeSet:
        """Hold one cross-repo set, under its id or a fresh one."""
        if not isinstance(cross, CrossRepoChangeSet):
            raise ValueError("the registry holds cross-repo change sets")
        if cross.set_id is None:
            cross = replace(cross, set_id=self._fresh_id())
        elif cross.set_id in self._sets:
            raise ValueError(
                f"a cross-repo set named {cross.set_id!r} "
                f"already exists")
        self._sets[cross.set_id] = cross
        return cross

    def build_and_register(self, workspace: Any, name: Any,
                           members: Any) -> CrossRepoChangeSet:
        """Build one cross-repo set and hold it, in one move."""
        return self.register(
            build_cross_repo_change_set(workspace, name, members))

    def get(self, set_id: Any) -> CrossRepoChangeSet:
        """The set one id names; an unknown id raises KeyError."""
        wanted = normalize_set_id(set_id)
        if wanted not in self._sets:
            raise KeyError(f"unknown cross-repo set: {wanted!r}")
        return self._sets[wanted]

    def list_sets(self) -> Tuple[CrossRepoChangeSet, ...]:
        """Every held set, in the order built, as a tuple."""
        return tuple(self._sets.values())

    def __len__(self) -> int:
        return len(self._sets)

    def record(self, set_id: Any) -> Dict[str, Any]:
        """One held set's session-news record."""
        return multi_repo_record(self.get(set_id))


# ---------------------------------------------------------------------
# The /multirepo surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_repo(repo: Any) -> str:
    """One held repo, in plain words: its policy stated whole."""
    current = validate_repo(repo)
    policy = current.policy
    review = "review required" if policy.requires_review \
        else "no review required"
    return (
        f"{current.repo_id}: {current.label} at {current.root} - "
        f"{MODE_PHRASES[policy.mode]}, branch {policy.branch}, "
        f"{review}.")


def _repos_from(source: Any) -> Tuple[RepoEntry, ...]:
    if source is None:
        return ()
    if isinstance(source, MultiRepoRegistry):
        return source.list_repos()
    if isinstance(source, MultiRepoWorkspace):
        return source.repos
    if isinstance(source, (RepoEntry, dict)):
        return (validate_repo(source),)
    if isinstance(source, (list, tuple)):
        return tuple(validate_repo(item) for item in source)
    raise ValueError("repos must be a registry, workspace or list")


def format_repos(source: Any = None) -> str:
    """The held repos, in plain words, in registration order.

    With no repos at all the text starts with the
    plain statement of that fact.
    """
    repos = _repos_from(source)
    if not repos:
        return (
            "Multi-repo workspace: no repos held. "
            "No repo is held for this session.")
    lines = [f"Multi-repo workspace: {len(repos)} repos held."]
    for repo in repos:
        lines.append(f"  {format_repo(repo)}")
    return "\n".join(lines)


def format_cross_set(cross: Any) -> str:
    """One cross-repo set, in plain words: counts always stated."""
    if not isinstance(cross, CrossRepoChangeSet):
        raise ValueError("formatting needs a cross-repo change set")
    name = cross.set_id or "set"
    counts = cross.counts()
    state = "reviewed whole" if cross.reviewed_whole \
        else "not yet reviewed whole"
    lines = [
        f"{name}: {cross.name!r} spans "
        f"{', '.join(cross.repo_ids)} - {state} "
        f"({counts['accepted']} accepted, "
        f"{counts['rejected']} rejected, "
        f"{counts['pending']} undecided)."]
    for index, edit in enumerate(cross.change_set.edits):
        lines.append(
            f"  file {index}: {edit.path} ({edit.format_id}) "
            f"[{cross.change_set.decision(index)}]")
    evidence = cross.change_set.evidence
    if evidence is None:
        lines.append("  Test evidence: none attached.")
    else:
        record = evidence.record()
        lines.append(
            f"  Test evidence: {record['verdict']} - "
            f"{record['passed']} passed, {record['failed']} "
            f"failed, {record['skipped']} skipped "
            f"from {record['command']!r}.")
    return "\n".join(lines)


#: The cross-set formatter under the set's own short name.
format_set = format_cross_set


def _sets_from(source: Any) -> Tuple[CrossRepoChangeSet, ...]:
    if source is None:
        return ()
    if isinstance(source, MultiRepoRegistry):
        return source.list_sets()
    if isinstance(source, CrossRepoChangeSet):
        return (source,)
    if isinstance(source, (list, tuple)):
        result = []
        for item in source:
            if not isinstance(item, CrossRepoChangeSet):
                raise ValueError("held sets must be cross-repo sets")
            result.append(item)
        return tuple(result)
    raise ValueError("sets must be a registry or a list of sets")


def format_sets(source: Any = None) -> str:
    """The held cross-repo sets, in plain words, in build order.

    With no sets at all the text starts with the
    plain statement of that fact.
    """
    sets = _sets_from(source)
    if not sets:
        return (
            "Cross-repo change sets: no sets held. "
            "No cross-repo change is held.")
    lines = [f"Cross-repo change sets: {len(sets)} held."]
    for cross in sets:
        head = format_cross_set(cross).splitlines()[0]
        lines.append(f"  {head}")
    return "\n".join(lines)


def format_multi_repo_record(record: Any) -> str:
    """One cross-repo news record as its plain headline."""
    if isinstance(record, dict) \
            and record.get("type") == "multi_repo_change_set":
        return str(record["headline"])
    raise ValueError("format_multi_repo_record needs a set record")


#: The set record's formatter under its own name.
format_record = format_multi_repo_record


def format_multi_repo_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /multirepo."""
    lines = [
        "Multi-repo workspaces (M-113) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_repos(source))
    lines.append("")
    lines.append(format_sets(source))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


_GRAMMAR_WORDS = ("show", "repos")


def parse_multirepo_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /multirepo grammar both surfaces share.

    No words (or ``show``) shows the workspace and
    its sets; ``show <set>`` and a bare set id show
    one set; ``repos`` shows the held repos alone.
    A grammar word in the wrong shape is a usage
    error naming the grammar, never a set id.
    Returns ``(action, target-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None \
        else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() == "show":
        return ("show", None)
    if text.lower() == "repos":
        return ("repos", None)
    words = text.split()
    head = words[0].lower()
    if head == "show" and len(words) == 2:
        if words[1].lower() in _GRAMMAR_WORDS:
            raise ValueError(USAGE)
        try:
            return ("show", normalize_set_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head in _GRAMMAR_WORDS or len(words) != 1:
        raise ValueError(USAGE)
    try:
        return ("show", normalize_set_id(words[0]))
    except ValueError:
        raise ValueError(USAGE) from None
