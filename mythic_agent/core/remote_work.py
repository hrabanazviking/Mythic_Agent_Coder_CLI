"""Remote and SSH work (All-Features roadmap slice M-114).

Part V - Autonomy & Safety. The roadmap words:
``run the coder against a project on another
machine (Mimir, purplelongship) through one
connection - files and commands stay on that
machine.``

What already shipped, and what this slice adds:

* A workspace already has a portable identity
  and contained file resolution
  (``mythic_agent/core/workspace.py`` -
  ``canonical_workspace_root`` / ``workspace_id``
  / ``resolve_file``): one directory on THIS
  machine, one identity. Nothing described a
  project living on ANOTHER machine.
* Background jobs already hold a command as
  data (``mythic_agent/core/background_tasks.py``,
  M-103): an argv list of words, never a shell
  string, because a single string is the shape a
  shell would eval. Nothing held such a command
  as work meant for a remote machine, through a
  named connection, against a named remote
  workspace root.
* Multi-repo workspaces hold several repos
  under one session (``multi_repo.py``, M-113),
  but every root they name is a root the session
  itself can reach. Nothing held a target on
  another machine, where the files and the
  commands must STAY.
* This slice is that missing remote layer, as a
  pure layer in the exact sibling shape: a
  remote target and its ONE connection held as
  validated data, remote command plans as
  argv-data records and remote file-operation
  plans as data, a mechanical judge that
  validates a work plan against its target, a
  remote-work record shaped as session news,
  and a small in-memory registry model with
  deterministic ids. This module opens no
  connection, runs no subprocess, writes no
  file, changes no setting and imports no agent
  / UI code; the agent layer owns opening the
  one connection and carrying a judged plan out
  on the remote machine.

Honesty rules, enforced here and pinned by tests:

* **One target, one connection.** A target
  names exactly one connection description -
  its kind, how it authenticates, and the key
  file when the key road is the one named. A
  plan is judged against ONE target; a target
  this session does not hold refuses plainly,
  in words, wherever it is asked for - never
  guessed at, never defaulted to another
  machine.
* **Files and commands stay on that machine.**
  A work plan whose file operation would copy
  a file back to this machine refuses at judge
  time, plainly: the roadmap words are that
  files stay on the remote machine. A plan is
  never quietly rewritten to drop the copy -
  it refuses, and the refusal says why.
* **A command is argv data, never a shell
  string.** The M-103 lesson, carried whole: a
  remote command is a list of non-empty words.
  A single string - the shape a shell would
  eval - refuses, so no plan can smuggle in a
  command line to be interpreted later, here
  or on the remote machine.
* **Work stays inside the remote root.** A
  file path or a command working directory
  naming somewhere outside the target remote
  workspace root refuses at judge time: the
  coder runs against the project on that
  machine, not against the whole machine.
* **Status is never carried by colour or
  symbol alone.** Every formatter states each
  target connection and each plan step count
  in words.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, List, Optional, Tuple

__all__ = [
    "AUTH_METHODS",
    "AUTH_PHRASES",
    "CONNECTION_KINDS",
    "CONNECTION_PHRASES",
    "DEFAULT_PORT",
    "FILE_OP_KINDS",
    "FILE_OP_PHRASES",
    "PLAIN_EXPLANATION",
    "REMOTE_WORK_SLICE",
    "USAGE",
    "Command",
    "Connection",
    "FileOp",
    "Host",
    "Plan",
    "RemoteCommand",
    "RemoteConnection",
    "RemoteFileOp",
    "RemoteHost",
    "RemoteTarget",
    "RemoteWorkPlan",
    "RemoteWorkRegistry",
    "Target",
    "WorkPlan",
    "build_command",
    "build_connection",
    "build_file_op",
    "build_target",
    "build_work_plan",
    "format_plan",
    "format_plans",
    "format_record",
    "format_remote_record",
    "format_remote_screen",
    "format_target",
    "format_targets",
    "format_work_plan",
    "judge_work_plan",
    "normalize_address",
    "normalize_auth_method",
    "normalize_connection_kind",
    "normalize_file_op_kind",
    "normalize_plan_id",
    "normalize_port",
    "normalize_target_id",
    "normalize_user",
    "normalize_workspace_root",
    "parse_remote_args",
    "plain_words",
    "remote_work_record",
    "validate_command",
    "validate_connection",
    "validate_file_op",
    "validate_step",
    "validate_target",
    "validate_work_plan",
]

REMOTE_WORK_SLICE = "M-114"

#: The one connection kind a target names: the
#: coder reaches the other machine over SSH.
CONNECTION_KINDS = ("ssh",)

#: Each connection kind, said in plain words.
CONNECTION_PHRASES = {
    "ssh": "SSH (one secure shell connection)",
}

_KIND_WORDS = {
    "ssh": "ssh", "openssh": "ssh",
    "secure_shell": "ssh", "secure-shell": "ssh",
}

#: How the one connection proves who is calling.
AUTH_METHODS = ("agent", "key", "password")

#: Each auth method, said in plain words.
AUTH_PHRASES = {
    "agent": "the SSH agent",
    "key": "a key file",
    "password": "a password",
}

_AUTH_WORDS = {
    "agent": "agent", "ssh_agent": "agent",
    "ssh-agent": "agent",
    "key": "key", "key_file": "key",
    "keyfile": "key", "key-file": "key",
    "identity": "key", "identity_file": "key",
    "password": "password", "pass": "password",
}

#: The file operations a plan may name against
#: files that stay on the remote machine.
FILE_OP_KINDS = ("read", "write", "edit", "list")

#: Each file operation, said in plain words.
FILE_OP_PHRASES = {
    "read": "read a file on the remote machine",
    "write": "write a file on the remote machine",
    "edit": "edit a file on the remote machine",
    "list": "list a directory on the remote machine",
}

_FILE_OP_WORDS = {
    "read": "read", "view": "read", "cat": "read",
    "write": "write", "create": "write",
    "edit": "edit", "modify": "edit",
    "list": "list", "ls": "list", "dir": "list",
}

#: The port an SSH connection uses when a target
#: names none.
DEFAULT_PORT = 22

PLAIN_EXPLANATION = (
    "Remote and SSH work: the coder runs against "
    "a project on another machine - Mimir, "
    "purplelongship, any held target - through "
    "ONE connection to that machine, and files "
    "and commands stay on that machine. A target "
    "is held as data: its address, its user, its "
    "port, the workspace root the project lives "
    "under there, and the one connection (SSH, "
    "authenticating by agent, key file or "
    "password). A work plan is data too: remote "
    "commands as argv word lists (never a shell "
    "string, the M-103 rule) and file operations "
    "against the remote root. A plan is judged "
    "against its target before anything could "
    "run: an unknown target, a shell-string "
    "command, a step outside the remote root, or "
    "a file operation that would copy a file "
    "back to this machine all refuse plainly. "
    "This layer holds targets and plans as data "
    "only; the agent layer opens the connection "
    "and carries a judged plan out."
)

USAGE = (
    "Usage: /remote, /remote show, "
    "/remote show <plan>, /remote targets"
)

_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_.")

_TARGET_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz0123456789_-")

_ADDRESS_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-.")

_USER_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789_.-")


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
                f"a remote record names two different {what}")
    return first


def normalize_connection_kind(value: Any) -> str:
    """The canonical connection kind a word names.

    The closed vocabulary is the one kind the
    roadmap names - SSH - read case-insensitively
    with its long spellings. Any other word
    refuses: a target is reached one way, and
    that way is named, never guessed.
    """
    if isinstance(value, str):
        wanted = value.strip().lower()
        if wanted in _KIND_WORDS:
            return _KIND_WORDS[wanted]
    raise ValueError(
        "a connection kind must be one of %s, got %r"
        % ("/".join(CONNECTION_KINDS), value))


def normalize_auth_method(value: Any) -> str:
    """The canonical auth method a word names.

    Reads the three methods (and their short
    spellings), case-insensitively. Any other
    word refuses: how the connection proves who
    is calling is a closed vocabulary of three.
    """
    if isinstance(value, str):
        wanted = value.strip().lower()
        if wanted in _AUTH_WORDS:
            return _AUTH_WORDS[wanted]
    raise ValueError(
        "an auth method must be one of %s, got %r"
        % ("/".join(AUTH_METHODS), value))


def normalize_file_op_kind(value: Any) -> str:
    """The canonical file-operation kind a word names.

    Reads the four operations a plan may name
    against files on the remote machine (and
    their short spellings), case-insensitively.
    Any other word refuses - in particular there
    is no copy or download operation here: files
    stay on that machine.
    """
    if isinstance(value, str):
        wanted = value.strip().lower()
        if wanted in _FILE_OP_WORDS:
            return _FILE_OP_WORDS[wanted]
    raise ValueError(
        "a file operation must be one of %s, got %r"
        % ("/".join(FILE_OP_KINDS), value))


def normalize_target_id(value: Any) -> str:
    """The canonical target id a word names.

    A target id is lowercase letters, digits,
    underscores and dashes, read case-insensitively
    with spaces read as dashes. Anything else
    raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace(" ", "-")
        if wanted and all(
                ch in _TARGET_ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"a target id must be a word of lowercase letters, "
        f"digits, underscores and dashes, got {value!r}")


def normalize_plan_id(value: Any) -> str:
    """The canonical work-plan id a word names.

    A plan id is one word of letters, digits,
    dashes, underscores and dots, read with its
    case kept. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and all(ch in _ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"a plan id must be a non-empty word of letters, "
        f"digits, dashes, underscores and dots, got {value!r}")


def normalize_address(value: Any) -> str:
    """The remote machine address a word names, as data.

    An address is a hostname or address word of
    letters, digits, dashes and dots, with no
    empty segment and no leading or trailing
    dash or dot in any segment. A port does not
    ride inside the address - it is its own
    field. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and all(
                ch in _ADDRESS_CHARS for ch in wanted):
            segments = wanted.split(".")
            if all(segment and not segment.startswith("-")
                   and not segment.endswith("-")
                   for segment in segments):
                return wanted
    raise ValueError(
        f"a remote address must be a hostname or address "
        f"word, got {value!r}")


def normalize_user(value: Any) -> str:
    """The remote user name a word names, as data.

    A user name is letters, digits, underscores,
    dashes and dots, beginning with a letter or
    an underscore. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and all(ch in _USER_CHARS for ch in wanted) \
                and (wanted[0].isalpha() or wanted[0] == "_"):
            return wanted
    raise ValueError(
        f"a remote user must be a user name, got {value!r}")


def normalize_port(value: Any) -> int:
    """The connection port a value names, as data.

    A port is a whole number from 1 to 65535,
    named as a number or as a word of digits. A
    boolean is not a port, and anything outside
    the range refuses.
    """
    if isinstance(value, bool):
        raise ValueError(f"a port must be a whole number, got {value!r}")
    if isinstance(value, str) and value.strip().isdigit():
        value = int(value.strip())
    if isinstance(value, int) and 1 <= value <= 65535:
        return value
    raise ValueError(
        f"a port must be a whole number from 1 to 65535, "
        f"got {value!r}")


def normalize_workspace_root(value: Any) -> str:
    """The remote workspace root a path names, as data.

    The root is an absolute path on the REMOTE
    machine: it begins with a slash, names no
    empty segment and no parent segment, and
    carries no trailing slash (the root itself,
    a single slash, is allowed whole). This
    layer holds the name as data - it never
    resolves the path anywhere.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted == "/":
            return wanted
        if wanted.startswith("/") and not wanted.endswith("/"):
            segments = wanted[1:].split("/")
            if all(segment and segment not in (".", "..")
                   for segment in segments):
                return wanted
    raise ValueError(
        f"a remote workspace root must be an absolute path "
        f"on the remote machine, got {value!r}")


def _check_remote_path(value: Any, what: str) -> str:
    """One remote path, as data: relative or absolute, no escape.

    A path names no empty segment, no parent
    segment and no backslash; whether an absolute
    path sits inside a target root is the
    judge road.
    """
    cleaned = _clean_text(value, what)
    if "\\" in cleaned:
        raise ValueError(f"{what} must be a remote path, got {value!r}")
    body = cleaned[1:] if cleaned.startswith("/") else cleaned
    if body:
        segments = body.split("/")
        if any(not segment or segment == ".."
               for segment in segments):
            raise ValueError(
                f"{what} must name no empty or parent segment, "
                f"got {value!r}")
    return cleaned


def _inside_root(path: str, root: str) -> bool:
    """Whether a judged path stays inside the remote root.

    A relative path with no parent segment (the
    construction rule) is read against the root
    and stays inside it; an absolute path must
    be the root itself or under it.
    """
    if not path.startswith("/"):
        return ".." not in path.split("/")
    if root == "/":
        return True
    return path == root or path.startswith(root + "/")


# ---------------------------------------------------------------------
# The connection: the ONE connection to a target, held as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class RemoteConnection:
    """The one connection a target is reached through, as data.

    ``kind`` is the closed vocabulary one kind -
    SSH; ``auth`` names how the connection proves
    who is calling; ``identity_file`` names the
    key file on THIS machine when, and only when,
    the key road is the one named (a key auth
    with no key file refuses, and a key file
    named under any other auth refuses - the
    description must not disagree with itself).
    This is a description only: constructing one
    opens nothing.
    """

    kind: str = "ssh"
    auth: str = "agent"
    identity_file: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind", normalize_connection_kind(self.kind))
        object.__setattr__(
            self, "auth", normalize_auth_method(self.auth))
        if self.identity_file is not None:
            object.__setattr__(
                self, "identity_file",
                _clean_text(self.identity_file, "an identity file"))
        if self.auth == "key" and not self.identity_file:
            raise ValueError(
                "a connection authenticating by key file must "
                "name its identity file")
        if self.auth != "key" and self.identity_file:
            raise ValueError(
                "an identity file belongs to key auth - this "
                "connection authenticates by %s" % (self.auth,))

    def to_record(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "auth": self.auth,
            "identity_file": self.identity_file,
        }


#: The shorter word for a remote connection.
Connection = RemoteConnection

_CONNECTION_KEYS = frozenset({
    "kind", "type", "auth", "auth_method", "method",
    "identity_file", "key_file", "identity",
})


def validate_connection(connection: Any) -> RemoteConnection:
    """Validate one connection description into a RemoteConnection.

    Accepts a RemoteConnection, None (the default
    SSH connection through the agent), or a
    mapping naming a ``kind`` (or ``type``), an
    ``auth`` (or ``auth_method`` / ``method``)
    and an ``identity_file`` (or ``key_file`` /
    ``identity``). Naming two spellings of one
    field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(connection, RemoteConnection):
        return connection
    if connection is None:
        return RemoteConnection()
    if not isinstance(connection, dict):
        raise ValueError(
            f"a connection must be a mapping, got {connection!r}")
    unknown = set(connection) - _CONNECTION_KEYS
    if unknown:
        raise ValueError(
            "unknown connection keys: %s" % ", ".join(sorted(unknown)))
    kwargs: Dict[str, Any] = {}
    kind = _pick(connection, ("kind", "type"), "connection kinds")
    if kind is not None:
        kwargs["kind"] = kind
    auth = _pick(
        connection, ("auth", "auth_method", "method"), "auth methods")
    if auth is not None:
        kwargs["auth"] = auth
    identity = _pick(
        connection, ("identity_file", "key_file", "identity"),
        "identity files")
    if identity is not None:
        kwargs["identity_file"] = identity
    return RemoteConnection(**kwargs)


def build_connection(connection: Any = None,
                     **kwargs: Any) -> RemoteConnection:
    """Build one validated connection from a mapping or field words."""
    if isinstance(connection, RemoteConnection) and not kwargs:
        return connection
    if isinstance(connection, dict) or connection is None:
        merged: Dict[str, Any] = {}
        if isinstance(connection, dict):
            merged.update(connection)
        merged.update(kwargs)
        return validate_connection(merged)
    raise ValueError(
        f"a connection must be a mapping, got {connection!r}")


# ---------------------------------------------------------------------
# The target: one machine and its project root, held as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class RemoteTarget:
    """One machine the coder can run against, as data.

    ``target_id`` names the machine in this
    session, ``address`` is where it is reached,
    ``user`` is who the connection logs in as,
    ``port`` is the connection port, and
    ``workspace_root`` is the absolute path on
    THAT machine under which the project lives -
    held as data, never resolved here.
    ``connection`` is the ONE connection
    description for this target. Constructing
    one validates it, and opens nothing.
    """

    target_id: str
    address: str
    user: str
    workspace_root: str
    port: int = DEFAULT_PORT
    label: str = ""
    connection: RemoteConnection = RemoteConnection()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "target_id", normalize_target_id(self.target_id))
        object.__setattr__(
            self, "address", normalize_address(self.address))
        object.__setattr__(
            self, "user", normalize_user(self.user))
        object.__setattr__(
            self, "workspace_root",
            normalize_workspace_root(self.workspace_root))
        object.__setattr__(
            self, "port", normalize_port(self.port))
        label = self.label.strip() if isinstance(
            self.label, str) else self.label
        if not isinstance(label, str):
            raise ValueError("a target label must be text")
        object.__setattr__(self, "label", label or self.target_id)
        object.__setattr__(
            self, "connection", validate_connection(self.connection))

    @property
    def display_label(self) -> str:
        return f"{self.target_id} ({self.label})"

    @property
    def connection_line(self) -> str:
        """Who is reached where, as one data line (display only)."""
        return f"{self.user}@{self.address}:{self.port}"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "remote_target",
            "slice": REMOTE_WORK_SLICE,
            "target_id": self.target_id,
            "address": self.address,
            "user": self.user,
            "port": self.port,
            "workspace_root": self.workspace_root,
            "label": self.label,
            "connection_line": self.connection_line,
            "connection": self.connection.to_record(),
        }


#: The target under its other roadmap word.
RemoteHost = RemoteTarget

#: The shorter word for a remote target.
Target = RemoteTarget

#: A target is also a host, in the roadmap words.
Host = RemoteTarget

_TARGET_KEYS = frozenset({
    "target_id", "id", "name", "host_id",
    "address", "host", "hostname",
    "user", "username", "login",
    "port", "workspace_root", "root", "remote_root", "path",
    "label", "title", "connection",
})


def validate_target(target: Any) -> RemoteTarget:
    """Validate one remote target into a RemoteTarget.

    Accepts a RemoteTarget or a mapping naming a
    ``target_id`` (or ``id`` / ``name`` /
    ``host_id``), an ``address`` (or ``host`` /
    ``hostname``), a ``user`` (or ``username`` /
    ``login``), a ``workspace_root`` (or ``root``
    / ``remote_root`` / ``path``), and optionally
    a ``port``, a ``label`` (or ``title``) and a
    ``connection``. Naming two spellings of one
    field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(target, RemoteTarget):
        return target
    if not isinstance(target, dict):
        raise ValueError(
            f"a remote target must be a mapping, got {target!r}")
    unknown = set(target) - _TARGET_KEYS
    if unknown:
        raise ValueError(
            "unknown target keys: %s" % ", ".join(sorted(unknown)))
    target_id = _pick(
        target, ("target_id", "id", "name", "host_id"), "target ids")
    address = _pick(
        target, ("address", "host", "hostname"), "addresses")
    user = _pick(target, ("user", "username", "login"), "users")
    root = _pick(
        target, ("workspace_root", "root", "remote_root", "path"),
        "workspace roots")
    if target_id is None or address is None \
            or user is None or root is None:
        raise ValueError(
            "a remote target must name its target_id, address, "
            "user and workspace_root")
    kwargs: Dict[str, Any] = {
        "target_id": target_id, "address": address,
        "user": user, "workspace_root": root}
    if "port" in target:
        kwargs["port"] = target["port"]
    label = _pick(target, ("label", "title"), "labels")
    if label is not None:
        kwargs["label"] = label
    if "connection" in target:
        kwargs["connection"] = target["connection"]
    return RemoteTarget(**kwargs)


def build_target(target: Any = None, **kwargs: Any) -> RemoteTarget:
    """Build one validated target from a mapping or field words."""
    if isinstance(target, RemoteTarget) and not kwargs:
        return target
    if isinstance(target, dict) or target is None:
        merged: Dict[str, Any] = {}
        if isinstance(target, dict):
            merged.update(target)
        merged.update(kwargs)
        return validate_target(merged)
    raise ValueError(
        f"a remote target must be a mapping, got {target!r}")


# ---------------------------------------------------------------------
# The steps: one remote command and one remote file operation, as data.
# ---------------------------------------------------------------------


def _check_argv(value: Any) -> Tuple[str, ...]:
    """A remote command words, validated whole - the M-103 rule.

    A single string refuses outright - that is
    the shape a shell would eval, and a remote
    command is data. Every part must be non-empty
    text.
    """
    if isinstance(value, (str, bytes)):
        raise ValueError(
            "a remote command must be an argv list of words, "
            "not a shell string")
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a remote command must be an argv list, got {value!r}")
    parts = tuple(value)
    if not parts:
        raise ValueError("a remote command needs at least one word")
    cleaned = []
    for part in parts:
        if not isinstance(part, str) or not part.strip():
            raise ValueError(
                f"a remote command word must be non-empty text, "
                f"got {part!r}")
        cleaned.append(part.strip())
    return tuple(cleaned)


@dataclass(frozen=True)
class RemoteCommand:
    """One command to run on the remote machine, as data.

    ``argv`` is the command as a list of words -
    never a shell string (the M-103 rule, carried
    whole). ``cwd`` is the directory ON the
    remote machine the command runs in, named
    relative to the target workspace root or as
    an absolute remote path, or None for the
    root itself. ``label`` is the short human
    name reports use; when it is empty the
    command itself is the label. Constructing
    one validates it; running it is the agent
    layer work, through the one connection.
    """

    argv: Tuple[str, ...]
    cwd: Optional[str] = None
    label: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "argv", _check_argv(self.argv))
        if self.cwd is not None:
            object.__setattr__(
                self, "cwd",
                _check_remote_path(self.cwd, "a remote command cwd"))
        if not isinstance(self.label, str):
            raise ValueError(
                f"a command label must be text, got {self.label!r}")
        object.__setattr__(self, "label", self.label.strip())

    @property
    def command_text(self) -> str:
        """The command as one display line (display only)."""
        return " ".join(self.argv)

    @property
    def display_label(self) -> str:
        return self.label or self.command_text

    def to_record(self) -> Dict[str, Any]:
        return {
            "step": "command",
            "argv": list(self.argv),
            "cwd": self.cwd,
            "label": self.label,
        }


#: The shorter word for a remote command step.
Command = RemoteCommand

_COMMAND_KEYS = frozenset({"argv", "command", "cwd", "label", "name"})


def validate_command(command: Any) -> RemoteCommand:
    """Validate one remote command step into a RemoteCommand.

    Accepts a RemoteCommand or a mapping naming
    an ``argv`` (or ``command``) word list, an
    optional ``cwd`` and an optional ``label``
    (or ``name``). A shell string in place of the
    word list refuses (the M-103 rule), naming
    two spellings of one field with different
    values refuses, and unknown keys refuse.
    """
    if isinstance(command, RemoteCommand):
        return command
    if not isinstance(command, dict):
        raise ValueError(
            f"a remote command step must be a mapping, got {command!r}")
    unknown = set(command) - _COMMAND_KEYS
    if unknown:
        raise ValueError(
            "unknown command keys: %s" % ", ".join(sorted(unknown)))
    argv = _pick(command, ("argv", "command"), "commands")
    if argv is None:
        raise ValueError("a remote command step must name its argv")
    kwargs: Dict[str, Any] = {"argv": argv}
    if "cwd" in command:
        kwargs["cwd"] = command["cwd"]
    label = _pick(command, ("label", "name"), "labels")
    if label is not None:
        kwargs["label"] = label
    return RemoteCommand(**kwargs)


def build_command(argv: Any, cwd: Any = None,
                  label: Any = "") -> RemoteCommand:
    """Build one validated remote command step from its pieces."""
    return RemoteCommand(argv=argv, cwd=cwd, label=label)


@dataclass(frozen=True)
class RemoteFileOp:
    """One file operation on the remote machine, as data.

    ``kind`` is one of the four operations;
    ``path`` names the file or directory ON the
    remote machine, relative to the target
    workspace root or as an absolute remote
    path. ``local_copy`` records, as data,
    whether the operation would copy the file
    back to THIS machine - it is held honestly
    so the judge can refuse it plainly, because
    the roadmap words are that files stay on
    that machine. Constructing one validates it;
    carrying it out is the agent layer work.
    """

    kind: str
    path: str
    local_copy: bool = False
    label: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind", normalize_file_op_kind(self.kind))
        object.__setattr__(
            self, "path",
            _check_remote_path(self.path, "a remote file path"))
        if not isinstance(self.local_copy, bool):
            raise ValueError(
                "local_copy must be true or false, got %r"
                % (self.local_copy,))
        if not isinstance(self.label, str):
            raise ValueError(
                f"a file operation label must be text, "
                f"got {self.label!r}")
        object.__setattr__(self, "label", self.label.strip())

    @property
    def display_label(self) -> str:
        return self.label or f"{self.kind} {self.path}"

    def to_record(self) -> Dict[str, Any]:
        return {
            "step": "file_op",
            "kind": self.kind,
            "path": self.path,
            "local_copy": self.local_copy,
            "label": self.label,
        }


#: The shorter word for a remote file operation.
FileOp = RemoteFileOp

_FILE_OP_KEYS = frozenset({
    "kind", "op", "operation", "path", "file",
    "local_copy", "copy_local", "label", "name",
})


def validate_file_op(file_op: Any) -> RemoteFileOp:
    """Validate one remote file operation into a RemoteFileOp.

    Accepts a RemoteFileOp or a mapping naming a
    ``kind`` (or ``op`` / ``operation``), a
    ``path`` (or ``file``), optionally a
    ``local_copy`` (or ``copy_local``) flag and a
    ``label`` (or ``name``). Naming two spellings
    of one field with different values refuses,
    and unknown keys refuse.
    """
    if isinstance(file_op, RemoteFileOp):
        return file_op
    if not isinstance(file_op, dict):
        raise ValueError(
            f"a remote file operation must be a mapping, "
            f"got {file_op!r}")
    unknown = set(file_op) - _FILE_OP_KEYS
    if unknown:
        raise ValueError(
            "unknown file operation keys: %s"
            % ", ".join(sorted(unknown)))
    kind = _pick(file_op, ("kind", "op", "operation"), "kinds")
    path = _pick(file_op, ("path", "file"), "paths")
    if kind is None or path is None:
        raise ValueError(
            "a remote file operation must name its kind and path")
    kwargs: Dict[str, Any] = {"kind": kind, "path": path}
    local_copy = _pick(
        file_op, ("local_copy", "copy_local"), "local copy flags")
    if local_copy is not None:
        kwargs["local_copy"] = local_copy
    label = _pick(file_op, ("label", "name"), "labels")
    if label is not None:
        kwargs["label"] = label
    return RemoteFileOp(**kwargs)


def build_file_op(kind: Any, path: Any, local_copy: Any = False,
                  label: Any = "") -> RemoteFileOp:
    """Build one validated remote file operation from its pieces."""
    return RemoteFileOp(
        kind=kind, path=path, local_copy=local_copy, label=label)


def validate_step(step: Any):
    """Validate one plan step: a command step or a file operation.

    Accepts a RemoteCommand, a RemoteFileOp, or a
    mapping - a mapping naming an ``argv`` (or
    ``command``) is a command step, a mapping
    naming a ``kind`` / ``op`` with a ``path`` is
    a file operation, and a mapping naming both
    refuses as ambiguous rather than being
    guessed at.
    """
    if isinstance(step, (RemoteCommand, RemoteFileOp)):
        return step
    if isinstance(step, dict):
        has_command = "argv" in step or "command" in step
        has_file_op = bool(
            {"kind", "op", "operation", "path", "file"} & set(step))
        if has_command and has_file_op:
            raise ValueError(
                "a plan step names both a command and a file "
                "operation - one step is one kind of work")
        if has_command:
            return validate_command(step)
        if has_file_op:
            return validate_file_op(step)
    raise ValueError(
        f"a plan step must be a remote command or a remote "
        f"file operation, got {step!r}")


# ---------------------------------------------------------------------
# The work plan: ordered steps against ONE target, held as data,
# and the mechanical judge that validates a plan against its target.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class RemoteWorkPlan:
    """One plan of remote work against one target, as data.

    ``name`` names the plan; ``target_id`` names
    the ONE target it runs against; ``steps`` is
    its ordered steps - remote commands (argv
    data) and remote file operations. The plan
    as built is data only; whether it may run
    against a named target is the judge road
    (:func:`judge_work_plan`). Constructing one
    validates its own shape.
    """

    name: str
    target_id: str
    steps: Tuple[Any, ...] = ()
    plan_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "name", _clean_text(self.name, "a plan name"))
        object.__setattr__(
            self, "target_id", normalize_target_id(self.target_id))
        if isinstance(self.steps, (str, bytes)) \
                or not isinstance(self.steps, (list, tuple)):
            raise ValueError("plan steps must be a list of steps")
        cleaned = tuple(validate_step(step) for step in self.steps)
        if not cleaned:
            raise ValueError(
                "a remote work plan needs at least one step")
        object.__setattr__(self, "steps", cleaned)
        if self.plan_id is not None:
            object.__setattr__(
                self, "plan_id", normalize_plan_id(self.plan_id))

    @property
    def display_label(self) -> str:
        name = self.plan_id or "plan"
        return f"{name} ({self.name})"

    @property
    def command_steps(self) -> Tuple[RemoteCommand, ...]:
        return tuple(
            step for step in self.steps
            if isinstance(step, RemoteCommand))

    @property
    def file_steps(self) -> Tuple[RemoteFileOp, ...]:
        return tuple(
            step for step in self.steps
            if isinstance(step, RemoteFileOp))

    @property
    def stays_on_remote(self) -> bool:
        """Whether every step keeps files on the remote machine."""
        return all(
            not step.local_copy for step in self.file_steps)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "remote_work_plan",
            "slice": REMOTE_WORK_SLICE,
            "plan_id": self.plan_id,
            "name": self.name,
            "target_id": self.target_id,
            "steps": [step.to_record() for step in self.steps],
            "command_count": len(self.command_steps),
            "file_op_count": len(self.file_steps),
            "stays_on_remote": self.stays_on_remote,
        }


#: The shorter words for a remote work plan.
WorkPlan = RemoteWorkPlan
Plan = RemoteWorkPlan

_PLAN_KEYS = frozenset({
    "name", "plan", "target_id", "target", "host",
    "steps", "work", "plan_id", "id",
})


def validate_work_plan(plan: Any) -> RemoteWorkPlan:
    """Validate one work plan into a RemoteWorkPlan.

    Accepts a RemoteWorkPlan or a mapping naming
    a ``name`` (or ``plan``), a ``target_id``
    (or ``target`` / ``host``), ``steps`` (or
    ``work``) and optionally a ``plan_id`` (or
    ``id``). Naming two spellings of one field
    with different values refuses, and unknown
    keys refuse.
    """
    if isinstance(plan, RemoteWorkPlan):
        return plan
    if not isinstance(plan, dict):
        raise ValueError(
            f"a remote work plan must be a mapping, got {plan!r}")
    unknown = set(plan) - _PLAN_KEYS
    if unknown:
        raise ValueError(
            "unknown plan keys: %s" % ", ".join(sorted(unknown)))
    name = _pick(plan, ("name", "plan"), "names")
    target_id = _pick(
        plan, ("target_id", "target", "host"), "target ids")
    steps = _pick(plan, ("steps", "work"), "steps")
    if name is None or target_id is None or steps is None:
        raise ValueError(
            "a remote work plan must name its name, target_id "
            "and steps")
    kwargs: Dict[str, Any] = {
        "name": name, "target_id": target_id, "steps": steps}
    plan_id = _pick(plan, ("plan_id", "id"), "plan ids")
    if plan_id is not None:
        kwargs["plan_id"] = plan_id
    return RemoteWorkPlan(**kwargs)


def build_work_plan(plan: Any = None, **kwargs: Any) -> RemoteWorkPlan:
    """Build one validated work plan from a mapping or field words."""
    if isinstance(plan, RemoteWorkPlan) and not kwargs:
        return plan
    if isinstance(plan, dict) or plan is None:
        merged: Dict[str, Any] = {}
        if isinstance(plan, dict):
            merged.update(plan)
        merged.update(kwargs)
        return validate_work_plan(merged)
    raise ValueError(
        f"a remote work plan must be a mapping, got {plan!r}")


def judge_work_plan(plan: Any, target: Any) -> RemoteWorkPlan:
    """Judge one work plan against its target, mechanically.

    ``target`` is the plan ONE target - a
    RemoteTarget, or a RemoteWorkRegistry holding
    targets (the plan target id is read from the
    registry, and an id it does not hold refuses
    plainly, naming the targets actually held).
    The judge reads data only and returns the
    plan unchanged when it may run; it refuses
    plainly when:

    * the plan names a different target than the
      one it is judged against, or a target no
      registry holds;
    * a file operation would copy a file back to
      this machine - files stay on that machine;
    * a file path or a command working directory
      names somewhere outside the target remote
      workspace root.

    A shell-string command never reaches the
    judge: it refuses when its step is built
    (the M-103 rule). Judging opens no
    connection and runs nothing.
    """
    judged = validate_work_plan(plan)
    if isinstance(target, RemoteWorkRegistry):
        held = target.get_target(judged.target_id)
    else:
        held = validate_target(target)
        if held.target_id != judged.target_id:
            raise ValueError(
                f"plan {judged.name!r} names target "
                f"{judged.target_id!r} - it cannot be judged "
                f"against target {held.target_id!r}; one plan "
                f"runs against one target")
    root = held.workspace_root
    for step in judged.steps:
        if isinstance(step, RemoteFileOp):
            if step.local_copy:
                raise ValueError(
                    f"file operation {step.kind} {step.path!r} "
                    f"would copy a file back to this machine - "
                    f"files stay on {held.target_id!r}; no plan "
                    f"was judged")
            if not _inside_root(step.path, root):
                raise ValueError(
                    f"file operation {step.kind} {step.path!r} "
                    f"names a path outside the remote workspace "
                    f"root {root!r} on {held.target_id!r}")
        elif isinstance(step, RemoteCommand):
            if step.cwd is not None and not _inside_root(step.cwd, root):
                raise ValueError(
                    f"command {step.command_text!r} would run "
                    f"in {step.cwd!r}, outside the remote "
                    f"workspace root {root!r} on "
                    f"{held.target_id!r}")
    return judged


# ---------------------------------------------------------------------
# The news record: one remote work plan, shaped as session news.
# ---------------------------------------------------------------------


def plain_words(plan: Any) -> str:
    """One remote work plan, in plain words - judged or not, said honestly.

    The headline always names the plan, its one
    target and its step counts in words. A plan
    whose steps all stay on the remote machine
    is stated as such; a plan naming a local
    copy is stated as one that would bring a
    file back - and that refuses under this
    slice rule - never as ready work.
    """
    if not isinstance(plan, RemoteWorkPlan):
        raise ValueError("plain words need a remote work plan")
    commands = len(plan.command_steps)
    files = len(plan.file_steps)
    if plan.stays_on_remote:
        return (
            f"Remote work plan {plan.name!r} runs against "
            f"{plan.target_id!r} through its one connection: "
            f"{commands} commands and {files} file operations, "
            f"and every file and command stays on that machine.")
    return (
        f"Remote work plan {plan.name!r} names "
        f"{plan.target_id!r} with {commands} commands and "
        f"{files} file operations - but one file operation "
        f"would copy a file back to this machine, and files "
        f"stay on that machine: this plan refuses as named.")


def remote_work_record(plan: Any) -> Dict[str, Any]:
    """The session-news record of one remote work plan.

    Every held remote work plan yields a record -
    the agent layer publishes this record as a
    session event, so remote work is announced in
    plain words in its headline, never lost as a
    mere log line. The record names the plan, its
    one target, its steps and its counts.
    """
    if not isinstance(plan, RemoteWorkPlan):
        raise ValueError("a record needs a remote work plan")
    record = plan.to_record()
    return {
        "type": "remote_work_plan",
        "news": True,
        "slice": REMOTE_WORK_SLICE,
        "plan_id": record["plan_id"],
        "name": record["name"],
        "target_id": record["target_id"],
        "steps": record["steps"],
        "command_count": record["command_count"],
        "file_op_count": record["file_op_count"],
        "stays_on_remote": record["stays_on_remote"],
        "headline": plain_words(plan),
    }


# ---------------------------------------------------------------------
# The registry model: a session targets and work plans, ids
# deterministic.
# ---------------------------------------------------------------------


class RemoteWorkRegistry:
    """An in-memory, storage-neutral remote-work registry.

    Targets are held in the order registered,
    under their target ids (a duplicate id
    refuses), and work plans are held in the
    order built. Plan ids are deterministic: a
    caller-supplied id is used as given (a
    duplicate refuses), and an unsupplied id is
    the next ``plan-N`` in sequence, skipping
    any number a supplied id already took - no
    randomness a test cannot pin. Storage beyond
    memory is the agent layer concern; this
    model is neutral.
    """

    def __init__(self) -> None:
        self._targets: Dict[str, RemoteTarget] = {}
        self._plans: Dict[str, RemoteWorkPlan] = {}
        self._next = 1

    # -- targets -------------------------------------------------------

    def register_target(self, target: Any = None,
                        **kwargs: Any) -> RemoteTarget:
        """Hold one target for the session, under its target id."""
        entry = build_target(target, **kwargs) if (
            target is not None or kwargs) else build_target(target)
        if entry.target_id in self._targets:
            raise ValueError(
                f"a target named {entry.target_id!r} is already held")
        self._targets[entry.target_id] = entry
        return entry

    def get_target(self, target_id: Any) -> RemoteTarget:
        """The held target one id names; an unknown id refuses plainly."""
        wanted = normalize_target_id(target_id)
        if wanted not in self._targets:
            if self._targets:
                raise ValueError(
                    f"unknown target: {wanted!r} - this session "
                    f"holds {', '.join(self._targets)}")
            raise ValueError(
                f"unknown target: {wanted!r} - this session "
                f"holds no targets")
        return self._targets[wanted]

    def list_targets(self) -> Tuple[RemoteTarget, ...]:
        """Every held target, in the order registered, as a tuple."""
        return tuple(self._targets.values())

    # -- work plans ------------------------------------------------------

    def _fresh_id(self) -> str:
        while f"plan-{self._next}" in self._plans:
            self._next += 1
        plan_id = f"plan-{self._next}"
        self._next += 1
        return plan_id

    def register(self, plan: Any) -> RemoteWorkPlan:
        """Hold one work plan, under its id or a fresh one."""
        if not isinstance(plan, RemoteWorkPlan):
            raise ValueError("the registry holds remote work plans")
        if plan.plan_id is None:
            plan = replace(plan, plan_id=self._fresh_id())
        elif plan.plan_id in self._plans:
            raise ValueError(
                f"a remote work plan named {plan.plan_id!r} "
                f"already exists")
        self._plans[plan.plan_id] = plan
        return plan

    def build_and_register(self, target: Any, name: Any,
                           steps: Any) -> RemoteWorkPlan:
        """Build one work plan, judge it against its target, and hold it.

        ``target`` names the ONE target - a held
        target id or a RemoteTarget. The plan is
        built naming that target and judged by
        :func:`judge_work_plan` in one move: an
        unknown target, a step outside the remote
        root, or a file operation that would copy
        a file back to this machine refuses, and
        nothing is held.
        """
        held = target if isinstance(target, RemoteTarget) \
            else self.get_target(target)
        plan = build_work_plan(
            name=name, target_id=held.target_id, steps=steps)
        return self.register(judge_work_plan(plan, held))

    def get(self, plan_id: Any) -> RemoteWorkPlan:
        """The plan one id names; an unknown id raises KeyError."""
        wanted = normalize_plan_id(plan_id)
        if wanted not in self._plans:
            raise KeyError(f"unknown remote work plan: {wanted!r}")
        return self._plans[wanted]

    def list_plans(self) -> Tuple[RemoteWorkPlan, ...]:
        """Every held plan, in the order built, as a tuple."""
        return tuple(self._plans.values())

    def __len__(self) -> int:
        return len(self._plans)

    def record(self, plan_id: Any) -> Dict[str, Any]:
        """One held plan session-news record."""
        return remote_work_record(self.get(plan_id))


# ---------------------------------------------------------------------
# The /remote surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_target(target: Any) -> str:
    """One held target, in plain words: its one connection stated whole."""
    current = validate_target(target)
    connection = current.connection
    line = (
        f"{current.target_id}: {current.label} at "
        f"{current.connection_line} - "
        f"{CONNECTION_PHRASES[connection.kind]} through "
        f"{AUTH_PHRASES[connection.auth]}")
    if connection.identity_file:
        line += f" ({connection.identity_file})"
    line += (
        f", workspace root {current.workspace_root} "
        f"on that machine.")
    return line


def _targets_from(source: Any) -> Tuple[RemoteTarget, ...]:
    if source is None:
        return ()
    if isinstance(source, RemoteWorkRegistry):
        return source.list_targets()
    if isinstance(source, (RemoteTarget, dict)):
        return (validate_target(source),)
    if isinstance(source, (list, tuple)):
        return tuple(validate_target(item) for item in source)
    raise ValueError("targets must be a registry, target or list")


def format_targets(source: Any = None) -> str:
    """The held targets, in plain words, in registration order.

    With no targets at all the text starts with
    the plain statement of that fact.
    """
    targets = _targets_from(source)
    if not targets:
        return (
            "Remote work: no targets held. "
            "No remote machine is held for this session.")
    lines = [f"Remote work: {len(targets)} targets held."]
    for target in targets:
        lines.append(f"  {format_target(target)}")
    return "\n".join(lines)


def format_work_plan(plan: Any) -> str:
    """One remote work plan, in plain words: step counts always stated."""
    if not isinstance(plan, RemoteWorkPlan):
        raise ValueError("formatting needs a remote work plan")
    name = plan.plan_id or "plan"
    counts = (
        f"{len(plan.command_steps)} commands, "
        f"{len(plan.file_steps)} file operations")
    stay = "files and commands stay on that machine" \
        if plan.stays_on_remote else \
        "one file operation would copy a file back to " \
        "this machine - this plan refuses as named"
    lines = [
        f"{name}: {plan.name!r} against {plan.target_id} - "
        f"{counts}; {stay}."]
    for index, step in enumerate(plan.steps):
        if isinstance(step, RemoteCommand):
            where = f" in {step.cwd}" if step.cwd else ""
            lines.append(
                f"  step {index}: command {step.command_text!r}"
                f"{where} [runs on {plan.target_id}]")
        else:
            lines.append(
                f"  step {index}: {FILE_OP_PHRASES[step.kind]}: "
                f"{step.path} [stays on {plan.target_id}]")
    return "\n".join(lines)


#: The plan formatter under the plan short name.
format_plan = format_work_plan


def _plans_from(source: Any) -> Tuple[RemoteWorkPlan, ...]:
    if source is None:
        return ()
    if isinstance(source, RemoteWorkRegistry):
        return source.list_plans()
    if isinstance(source, RemoteWorkPlan):
        return (source,)
    if isinstance(source, (list, tuple)):
        result = []
        for item in source:
            if not isinstance(item, RemoteWorkPlan):
                raise ValueError("held plans must be remote work plans")
            result.append(item)
        return tuple(result)
    raise ValueError("plans must be a registry or a list of plans")


def format_plans(source: Any = None) -> str:
    """The held work plans, in plain words, in build order.

    With no plans at all the text starts with the
    plain statement of that fact.
    """
    plans = _plans_from(source)
    if not plans:
        return (
            "Remote work plans: no plans held. "
            "No remote work is held.")
    lines = [f"Remote work plans: {len(plans)} held."]
    for plan in plans:
        head = format_work_plan(plan).splitlines()[0]
        lines.append(f"  {head}")
    return "\n".join(lines)


def format_remote_record(record: Any) -> str:
    """One remote-work news record as its plain headline."""
    if isinstance(record, dict) \
            and record.get("type") == "remote_work_plan":
        return str(record["headline"])
    raise ValueError("format_remote_record needs a plan record")


#: The plan record formatter under its own name.
format_record = format_remote_record


def format_remote_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /remote."""
    lines = [
        "Remote and SSH work (M-114) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_targets(source))
    lines.append("")
    lines.append(format_plans(source))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


_GRAMMAR_WORDS = ("show", "targets")


def parse_remote_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /remote grammar both surfaces share.

    No words (or ``show``) shows the targets and
    their plans; ``show <plan>`` and a bare plan
    id show one plan; ``targets`` shows the held
    targets alone. A grammar word in the wrong
    shape is a usage error naming the grammar,
    never a plan id. Returns
    ``(action, target-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None \
        else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() == "show":
        return ("show", None)
    if text.lower() == "targets":
        return ("targets", None)
    words = text.split()
    head = words[0].lower()
    if head == "show" and len(words) == 2:
        if words[1].lower() in _GRAMMAR_WORDS:
            raise ValueError(USAGE)
        try:
            return ("show", normalize_plan_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head in _GRAMMAR_WORDS or len(words) != 1:
        raise ValueError(USAGE)
    try:
        return ("show", normalize_plan_id(words[0]))
    except ValueError:
        raise ValueError(USAGE) from None
