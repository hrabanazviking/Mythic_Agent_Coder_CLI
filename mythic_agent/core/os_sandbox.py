"""The OS sandbox: confinement plans and platform truth (M-097).

Part V - Autonomy & Safety. The roadmap's words:
``commands run under OS confinement (Linux
namespaces/seccomp, macOS sandbox-exec, Windows job
objects as far as each honestly goes) - no Docker,
ever; per-platform truth in the platform table.``

What already shipped, and what this slice adds:

* A guardrail runner already shipped as
  ``core/sandbox.py``: its ``Sandbox`` refuses a
  denylist of destructive commands, caps wall-clock
  time and address space (RLIMIT_AS), and marks a
  no-network run with the ``MYTHIC_SANDBOX_NO_NETWORK``
  environment marker (the ``MYTHIC_SANDBOX_*`` census
  markers live there). Those are guardrails around a
  process that still runs as the user, on the host,
  with the host's filesystem and namespaces. Nothing
  in the tree confined a command at the OS level, and
  nothing said, per platform, what confinement is
  honestly available.
* This slice is that confinement layer, as a pure
  layer, composing with the elder runner rather than
  replacing it: the elder runner still owns denylist,
  timeouts and memory caps; this module owns the
  confinement *plan* - the mechanism, the argv prefix
  or profile, the environment additions, and the
  network stance - plus the per-platform truth table
  that says how far each platform honestly goes. The
  plan's no-network environment additions carry the
  elder runner's own marker, so the two layers agree.
  This module writes no file, changes no setting and
  runs nothing itself; the agent layer owns joining a
  plan to the elder runner and actually executing
  commands under it.

The mechanisms, as plan data:

* **Linux** - namespaces via ``unshare`` (user,
  mount, pid, ipc and uts namespaces; a fresh net
  namespace when the network stance is deny), with a
  seccomp allowlist the runner applies through
  ``setpriv --seccomp-filter``; ``bwrap``
  (bubblewrap) is an accepted alternate launcher where
  present. Measured on this Linux box at authoring:
  ``unshare`` creates the namespaces and ``setpriv``
  offers ``--seccomp-filter``. The pure layer still
  runs nothing, so Linux support is *limited*, not
  proven: the namespace road is measured, the seccomp
  filter is plan data until the agent layer runs it.
* **macOS** - ``sandbox-exec`` with a generated SBPL
  profile: deny by default, explicit grants for
  process execution and file reads, and the network
  stance written into the profile itself. No macOS
  machine is available to this campaign, so support
  is *planned*: the profile is validated text, never
  measured here.
* **Windows** - Job Objects (kill-on-job-close,
  active-process and memory limits) through a native
  helper the agent layer still owes. Python's
  standard library offers no road to Job Objects, so
  a Windows plan honestly carries *no argv prefix*
  and ``confined`` is False; Job Objects also bound
  resources and the process tree only - they do not
  confine the filesystem or the network the way
  namespaces do. Support is *limited*.

Honesty rules, enforced here and pinned by tests:

* **No Docker, ever.** No plan, profile, mechanism
  or truth entry names docker or podman, and a
  command whose program is docker or podman refuses
  outright: the OS sandbox never launches a
  container runtime.
* **The network stance is explicit in every plan.**
  Every plan carries ``network`` as ``deny`` or
  ``allow`` and renders it; a Linux deny rides a
  fresh net namespace, a macOS deny is written into
  the SBPL profile, a Windows plan names the stance
  while honestly saying Job Objects cannot enforce
  it. There is no silent third state.
* **Unknown platforms refuse plainly.** A platform
  outside linux / macos / windows raises, naming the
  three known platforms; nothing is guessed.
* **The truth table never overclaims.** Support is
  ``proven``, ``limited`` or ``planned`` per
  platform with the reason attached. The validator
  refuses ``proven`` for any platform but Linux, and
  refuses it even there without a local-measured
  note; the shipped table claims ``proven`` nowhere
  - only Linux carries a measured note at all, and
  only for what the plan data itself states (the
  namespace road exists and was measured; the
  confinement run itself has not been).
* **A plan that cannot confine says so.** Where no
  runnable confinement exists (Windows today), the
  plan's ``confined`` is False and asking for a
  required confinement (``require_confined=True``)
  refuses plainly instead of dressing the plan up.
"""

from __future__ import annotations

import shlex
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "FORBIDDEN_LAUNCHERS",
    "NETWORK_STANCES",
    "OS_SANDBOX_SLICE",
    "PLAIN_EXPLANATION",
    "PLATFORMS",
    "PLATFORM_TRUTH",
    "SECCOMP_BASELINE_SYSCALLS",
    "SETTING_KEY",
    "SUPPORT_LEVELS",
    "TRUTH_KEYS",
    "USAGE",
    "ConfinementPlan",
    "GateChange",
    "PlatformTruthEntry",
    "build_confinement_plan",
    "confinement_plan_record",
    "current_platform",
    "enabled_from_config",
    "format_confinement_plan",
    "format_gate_change",
    "format_os_sandbox",
    "format_platform_truth",
    "normalize_platform",
    "parse_sandbox_args",
    "platform_truth_entry",
    "set_enabled",
    "truth_table",
    "validate_truth_records",
]

OS_SANDBOX_SLICE = "M-097"

SETTING_KEY = "os_sandbox"

PLATFORMS = ("linux", "macos", "windows")

SUPPORT_LEVELS = ("proven", "limited", "planned")

NETWORK_STANCES = ("deny", "allow")

#: Container runtimes this sandbox never names and never launches.
FORBIDDEN_LAUNCHERS = ("docker", "podman")

TRUTH_KEYS = frozenset(
    {"platform", "mechanism", "support", "reason", "evidence_kind"}
)

EVIDENCE_KINDS = ("local-measured", "none")

_PLATFORM_ALIASES = {
    "linux": "linux",
    "linux2": "linux",
    "gnu/linux": "linux",
    "macos": "macos",
    "mac": "macos",
    "darwin": "macos",
    "osx": "macos",
    "windows": "windows",
    "win": "windows",
    "win32": "windows",
}

#: The seccomp allowlist baseline, as plan data. The runner
#: turns these names into a setpriv seccomp filter file; the
#: pure layer only names them, it installs no filter.
SECCOMP_BASELINE_SYSCALLS = (
    "read", "write", "openat", "close", "fstat", "mmap",
    "mprotect", "munmap", "brk", "rt_sigaction",
    "rt_sigprocmask", "ioctl", "pread64", "pwrite64",
    "readv", "writev", "access", "pipe", "select",
    "sched_yield", "mremap", "msync", "mincore",
    "madvise", "dup", "dup2", "clone", "execve",
    "exit", "exit_group", "wait4", "fcntl", "flock",
    "fsync", "getcwd", "chdir", "rename", "mkdir",
    "rmdir", "unlink", "readlink", "chmod", "umask",
    "getpid", "getuid", "geteuid", "getgid", "getegid",
    "arch_prctl", "set_tid_address", "set_robust_list",
    "rseq", "prlimit64", "clock_gettime", "getrandom",
)

PLAIN_EXPLANATION = (
    "Commands run under the operating system's own "
    "confinement - Linux namespaces and seccomp, macOS "
    "sandbox-exec, Windows job objects, each as far as "
    "it honestly goes - never Docker. This layer plans "
    "the confinement and tells the per-platform truth "
    "about it; it runs nothing itself."
)

USAGE = (
    "Usage: /sandbox, /sandbox on, /sandbox off, "
    "/sandbox truth, /sandbox plan <command>, "
    "/sandbox plan <platform> -- <command>"
)


@dataclass(frozen=True)
class PlatformTruthEntry:
    """One platform's confinement truth: mechanism, level, reason."""

    platform: str
    mechanism: str
    support: str
    reason: str
    evidence_kind: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "mechanism": self.mechanism,
            "support": self.support,
            "reason": self.reason,
            "evidence_kind": self.evidence_kind,
        }


_TRUTH_RECORDS: Tuple[Dict[str, Any], ...] = (
    {
        "platform": "linux",
        "mechanism": (
            "Linux namespaces via unshare (user, mount, pid, "
            "ipc, uts; a fresh net namespace when the network "
            "stance is deny) with a seccomp allowlist the "
            "runner applies through setpriv --seccomp-filter; "
            "bwrap (bubblewrap) is an accepted alternate "
            "launcher where present"
        ),
        "support": "limited",
        "reason": (
            "Measured on this Linux box at authoring: unshare "
            "creates user/mount/pid namespaces and setpriv "
            "offers --seccomp-filter, and bubblewrap 0.11.1 is "
            "present. But this pure layer runs nothing, so the "
            "seccomp filter is plan data and confinement "
            "itself is not proven here - the agent layer must "
            "run commands under the plan and measure it."
        ),
        "evidence_kind": "local-measured",
    },
    {
        "platform": "macos",
        "mechanism": (
            "sandbox-exec with a generated SBPL profile: deny "
            "by default, explicit grants for process execution "
            "and file reads, and the network stance written "
            "into the profile itself"
        ),
        "support": "planned",
        "reason": (
            "No macOS machine is available to this campaign, "
            "so the profile is plan data only - generated and "
            "validated as text, never measured on a real "
            "macOS host."
        ),
        "evidence_kind": "none",
    },
    {
        "platform": "windows",
        "mechanism": (
            "Windows Job Objects (kill-on-job-close, "
            "active-process and memory limits) through a "
            "native helper the agent layer still owes; "
            "Python's standard library offers no road to "
            "Job Objects, so a Windows plan carries no "
            "argv prefix"
        ),
        "support": "limited",
        "reason": (
            "Job Objects bound resources and the process "
            "tree; they do not confine the filesystem or "
            "the network the way namespaces do, and no "
            "Windows machine is available to measure "
            "even that."
        ),
        "evidence_kind": "none",
    },
)


def validate_truth_records(records: Any) -> List[str]:
    """Problems with a platform truth table, or an empty list.

    The law: exactly the three known platforms, once
    each; support from the fixed vocabulary; no
    mechanism naming a container runtime; ``proven``
    only for Linux and only with a local-measured note.
    """
    problems: List[str] = []
    if not isinstance(records, (list, tuple)) or not records:
        return ["platform truth must be a non-empty list of records"]
    seen: List[str] = []
    for record in records:
        if not isinstance(record, dict):
            problems.append(f"a truth record must be a mapping: {record!r}")
            continue
        unknown = set(record) - TRUTH_KEYS
        if unknown:
            problems.append(
                "a truth record names unknown keys: "
                + ", ".join(sorted(unknown)))
        missing = TRUTH_KEYS - set(record)
        if missing:
            problems.append(
                "a truth record is missing keys: "
                + ", ".join(sorted(missing)))
            continue
        platform = record["platform"]
        if platform not in PLATFORMS:
            problems.append(f"unknown truth platform: {platform!r}")
        elif platform in seen:
            problems.append(f"platform {platform!r} is tabled twice")
        seen.append(platform)
        if record["support"] not in SUPPORT_LEVELS:
            problems.append(
                f"truth support for {platform!r} must be one of "
                + "/".join(SUPPORT_LEVELS))
        if record["evidence_kind"] not in EVIDENCE_KINDS:
            problems.append(
                f"truth evidence_kind for {platform!r} must be one of "
                + "/".join(EVIDENCE_KINDS))
        if record["support"] == "proven":
            if platform != "linux":
                problems.append(
                    f"only linux may ever claim proven, not {platform!r}: "
                    "this campaign cannot measure the other platforms")
            elif record["evidence_kind"] != "local-measured":
                problems.append(
                    "a proven verdict requires a local-measured note")
        for key in ("mechanism", "reason"):
            value = record[key]
            if not isinstance(value, str) or not value.strip():
                problems.append(
                    f"truth {key} for {platform!r} must be non-empty text")
                continue
            lowered = value.lower()
            for launcher in FORBIDDEN_LAUNCHERS:
                if launcher in lowered:
                    problems.append(
                        f"truth {key} for {platform!r} names "
                        f"{launcher}: no Docker, ever")
    for platform in PLATFORMS:
        if platform not in seen:
            problems.append(f"platform {platform!r} is missing from the table")
    return problems


def truth_table() -> Tuple[PlatformTruthEntry, ...]:
    """The shipped platform truth table, validated whole."""
    problems = validate_truth_records(_TRUTH_RECORDS)
    if problems:
        raise ValueError(
            "platform truth table failed validation: " + "; ".join(problems))
    return tuple(
        PlatformTruthEntry(
            platform=r["platform"], mechanism=r["mechanism"],
            support=r["support"], reason=r["reason"],
            evidence_kind=r["evidence_kind"])
        for r in _TRUTH_RECORDS)


#: The shipped, validated truth table.
PLATFORM_TRUTH = truth_table()


def platform_truth_entry(platform: Any) -> PlatformTruthEntry:
    """The truth entry for one platform (aliases resolved)."""
    wanted = normalize_platform(platform)
    for entry in PLATFORM_TRUTH:
        if entry.platform == wanted:
            return entry
    raise ValueError(f"no truth entry for platform {wanted!r}")


def normalize_platform(name: Any) -> str:
    """One canonical platform name, or a plain refusal.

    Aliases (darwin, win32, osx, ...) resolve to the
    three known platforms. Anything else refuses,
    naming the known three - never a guess.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("a platform must be a non-empty string")
    wanted = _PLATFORM_ALIASES.get(name.strip().lower())
    if wanted is None:
        raise ValueError(
            f"unknown platform {name!r}: this sandbox knows "
            + ", ".join(PLATFORMS))
    return wanted


def current_platform() -> str:
    """The platform this process is running on, canonically."""
    return normalize_platform(sys.platform)


@dataclass(frozen=True)
class ConfinementPlan:
    """One command's confinement plan: mechanism, prefix, stance.

    ``argv_prefix`` is what the runner puts in front of
    the command (empty on Windows, where no honest
    prefix exists yet); ``profile_text`` carries the
    macOS SBPL profile (None elsewhere); ``confined``
    says whether a runnable OS confinement exists in
    the plan at all; ``network`` is always explicit.
    """

    platform: str
    mechanism: str
    support: str
    command: Tuple[str, ...]
    argv_prefix: Tuple[str, ...]
    profile_text: Optional[str]
    env_additions: Tuple[Tuple[str, str], ...]
    network: str
    confined: bool
    enforcement_notes: Tuple[str, ...]
    explanation: str

    def argv(self) -> Tuple[str, ...]:
        """The full argv the runner would execute."""
        return tuple(self.argv_prefix) + tuple(self.command)

    def env(self) -> Dict[str, str]:
        return dict(self.env_additions)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "os_sandbox_plan",
            "slice": OS_SANDBOX_SLICE,
            "platform": self.platform,
            "mechanism": self.mechanism,
            "support": self.support,
            "command": list(self.command),
            "argv": list(self.argv()),
            "argv_prefix": list(self.argv_prefix),
            "profile_text": self.profile_text,
            "env": self.env(),
            "network": self.network,
            "confined": self.confined,
            "enforcement_notes": list(self.enforcement_notes),
            "explanation": self.explanation,
        }


def _command_argv(command: Any) -> Tuple[str, ...]:
    if isinstance(command, str):
        if not command.strip():
            raise ValueError("a sandboxed command must not be empty")
        try:
            parts = shlex.split(command)
        except ValueError as exc:
            raise ValueError(f"could not parse the command: {exc}") from exc
    elif isinstance(command, (list, tuple)):
        parts = list(command)
        for part in parts:
            if not isinstance(part, str) or not part:
                raise ValueError("every command part must be non-empty text")
    else:
        raise ValueError("a sandboxed command must be text or a list of parts")
    if not parts:
        raise ValueError("a sandboxed command must not be empty")
    program = parts[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
    if program in FORBIDDEN_LAUNCHERS:
        raise ValueError(
            f"refused: the OS sandbox never launches {program} - "
            "no Docker, ever; commands run under the operating "
            "system's own confinement instead")
    return tuple(parts)


def _macos_profile(network: str) -> str:
    network_line = ("(deny network*)" if network == "deny"
                    else "(allow network*)")
    return "\n".join([
        "(version 1)",
        "(deny default)",
        "(allow process-exec)",
        "(allow process-fork)",
        "(allow file-read*)",
        "(allow sysctl-read)",
        "(allow mach-lookup)",
        network_line,
    ])


def build_confinement_plan(
    command: Any,
    *,
    platform: Any = None,
    network: Any = "deny",
    require_confined: Any = False,
) -> ConfinementPlan:
    """Build the confinement plan for *command*, purely.

    ``platform`` defaults to the platform this process
    runs on; ``network`` is ``deny`` unless ``allow``
    is asked for in so many words. With
    ``require_confined=True``, a platform whose plan
    carries no runnable measured confinement refuses
    plainly instead of returning a dressed-up plan.
    Nothing is executed, written or changed here.
    """
    argv_command = _command_argv(command)
    if network not in NETWORK_STANCES:
        raise ValueError(
            "a confinement plan's network stance must be one of "
            + "/".join(NETWORK_STANCES) + f", got {network!r}")
    wanted = current_platform() if platform is None else normalize_platform(platform)
    entry = platform_truth_entry(wanted)
    env: Dict[str, str] = {
        "MYTHIC_OS_SANDBOX": "1",
        "MYTHIC_OS_SANDBOX_PLATFORM": wanted,
    }
    if network == "deny":
        # The elder runner's own no-network marker, so the
        # guardrail layer and this plan agree on the stance.
        env["MYTHIC_SANDBOX_NO_NETWORK"] = "1"
    env_items = tuple(sorted(env.items()))
    cmd_text = " ".join(argv_command)
    if wanted == "linux":
        prefix: Tuple[str, ...] = (
            "unshare", "--user", "--map-root-user", "--mount",
            "--pid", "--ipc", "--uts", "--fork")
        if network == "deny":
            prefix = prefix + ("--net",)
        notes = (
            "seccomp allowlist (plan data): the runner renders "
            "SECCOMP_BASELINE_SYSCALLS into a filter file and "
            "applies it with setpriv --seccomp-filter",
            "bubblewrap (bwrap) is an accepted alternate launcher "
            "for the same namespace plan where present",
            "the elder Sandbox guardrails (denylist, timeout, "
            "memory cap) still apply inside the namespaces",
        )
        plan = ConfinementPlan(
            platform=wanted, mechanism=entry.mechanism,
            support=entry.support, command=argv_command,
            argv_prefix=prefix, profile_text=None,
            env_additions=env_items, network=network, confined=True,
            enforcement_notes=notes,
            explanation=(
                f"Linux confinement for {cmd_text!r}: namespaces "
                f"via unshare (user, mount, pid, ipc, uts"
                + (", plus a fresh net namespace - network denied"
                   if network == "deny" else " - network allowed")
                + "), with a seccomp allowlist the runner applies "
                "via setpriv. Support: limited - the namespace "
                "road is measured on this box, the run itself is "
                "the agent layer's to prove."))
    elif wanted == "macos":
        profile = _macos_profile(network)
        plan = ConfinementPlan(
            platform=wanted, mechanism=entry.mechanism,
            support=entry.support, command=argv_command,
            argv_prefix=("sandbox-exec", "-p", profile),
            profile_text=profile, env_additions=env_items,
            network=network, confined=True,
            enforcement_notes=(
                "the SBPL profile is deny-by-default; file writes "
                "are not granted by this baseline profile",
                "the elder Sandbox guardrails (denylist, timeout, "
                "memory cap) still apply inside the profile",
            ),
            explanation=(
                f"macOS confinement for {cmd_text!r}: sandbox-exec "
                f"with a deny-default SBPL profile; network "
                f"{network} is written into the profile itself. "
                "Support: planned - no macOS machine is available "
                "to measure this profile, so it is plan data only."))
    else:  # windows
        plan = ConfinementPlan(
            platform=wanted, mechanism=entry.mechanism,
            support=entry.support, command=argv_command,
            argv_prefix=(), profile_text=None,
            env_additions=env_items, network=network, confined=False,
            enforcement_notes=(
                "job object limits (plan data): kill-on-job-close, "
                "one active-process tree, a memory ceiling - set "
                "by a native helper that does not ship yet",
                "job objects cannot enforce the network stance or "
                "confine the filesystem; the stance is recorded, "
                "not enforced, on this platform",
            ),
            explanation=(
                f"Windows plan for {cmd_text!r}: Job Objects via a "
                "native helper that is still owed, so this plan "
                "carries no argv prefix and confines nothing yet "
                f"(network {network} is recorded, not enforced). "
                "Support: limited - resources and the process "
                "tree only, unmeasured on any Windows machine."))
    if require_confined is True and (
            not plan.confined or plan.support == "planned"):
        raise ValueError(
            f"refused: {wanted} cannot confine this command yet "
            f"(support: {plan.support}) - {entry.reason}")
    return plan


def confinement_plan_record(plan: ConfinementPlan) -> Dict[str, Any]:
    """The journal-shaped record of one confinement plan."""
    return plan.to_record()


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The os_sandbox gate stored in *config*.

    Absent means True (the gate ships on). A stored
    value that is not a bool raises - never guessed at.
    With the gate off, the agent layer runs commands
    under the elder guardrails only, and says so; the
    pure plans and the truth table stay readable.
    """
    raw = config.get(SETTING_KEY, True)
    if not isinstance(raw, bool):
        raise ValueError(
            f"{SETTING_KEY} must be true or false, "
            f"got {type(raw).__name__}")
    return raw


@dataclass(frozen=True)
class GateChange:
    """A recorded change of the os_sandbox gate."""

    before: bool
    after: bool

    def event(self) -> Dict[str, Any]:
        return {"type": "os_sandbox_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "os_sandbox_setting_changed",
                "from": self.before, "to": self.after,
                "session_id": session_id, "journaled": journaled}


def set_enabled(config: Dict[str, Any],
                enabled: Any) -> Tuple[bool, GateChange]:
    """Validate a gate change against *config*, purely."""
    if not isinstance(enabled, bool):
        raise ValueError(
            f"{SETTING_KEY} is turned on or off; got {enabled!r}")
    before = enabled_from_config(config)
    if enabled == before:
        raise ValueError(
            f"the OS sandbox is already {'on' if before else 'off'}")
    return enabled, GateChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The /sandbox surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_sandbox_args(args: str) -> Dict[str, Any]:
    """Parse the /sandbox grammar both surfaces share.

    No words (or ``show``) shows the slice; ``on`` /
    ``off`` steer the gate; ``truth`` asks for the
    platform truth table; ``plan <command...>`` builds
    a plan for the current platform; ``plan <platform>
    -- <command...>`` names the platform. Anything
    else is a usage error naming the grammar.
    """
    text = (args or "").strip()
    if not text or text == "show":
        return {"action": "show"}
    if text == "on":
        return {"action": "on"}
    if text == "off":
        return {"action": "off"}
    if text == "truth":
        return {"action": "truth"}
    words = text.split()
    if words[0] == "plan":
        rest = words[1:]
        if not rest:
            raise ValueError(USAGE)
        if "--" in rest:
            cut = rest.index("--")
            head, tail = rest[:cut], rest[cut + 1:]
            if len(head) != 1 or not tail:
                raise ValueError(USAGE)
            return {"action": "plan",
                    "platform": normalize_platform(head[0]),
                    "command": tail}
        return {"action": "plan", "platform": None, "command": rest}
    raise ValueError(USAGE)


def format_gate_change(record: Dict[str, Any]) -> str:
    state = "on" if record.get("to") else "off"
    return f"The OS sandbox is now {state}."


def format_confinement_plan(plan: ConfinementPlan) -> str:
    """One plan, in plain words, from the plan itself."""
    lines = [plan.explanation]
    lines.append(f"Platform: {plan.platform} (support: {plan.support})")
    lines.append(f"Network: {plan.network} (explicit in every plan)")
    if plan.argv_prefix:
        lines.append("Would run: " + " ".join(plan.argv()))
    else:
        lines.append(
            "Would run: no confined argv exists for this platform yet")
    if plan.profile_text is not None:
        lines.append("Profile:")
        lines.append(plan.profile_text)
    for note in plan.enforcement_notes:
        lines.append(f"  - {note}")
    return "\n".join(lines)


def format_platform_truth() -> str:
    """The truth table, in plain words, from the table itself."""
    lines = ["OS sandbox platform truth (M-097):"]
    for entry in PLATFORM_TRUTH:
        lines.append(
            f"  {entry.platform}: {entry.support} - {entry.mechanism}")
        lines.append(f"    Why: {entry.reason}")
    return "\n".join(lines)


def format_os_sandbox(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /sandbox.

    Built from the truth table and a sample Linux plan,
    so the show surface exercises the plan road it
    names and can never drift from the table.
    """
    enabled = enabled_from_config(config)
    lines = ["The OS sandbox (M-097) - " + PLAIN_EXPLANATION, ""]
    lines.append(
        f"Setting: {'on' if enabled else 'off'} ({SETTING_KEY}).")
    lines.append("")
    lines.append(format_platform_truth())
    lines.append("")
    sample = build_confinement_plan(
        "git status", platform="linux", network="deny")
    lines.append(format_confinement_plan(sample))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)
