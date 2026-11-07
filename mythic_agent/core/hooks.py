"""Hooks - the full lifecycle (roadmap slice M-101).

Part V - Autonomy & Safety. The roadmap's words:
``pre/post tool, pre/post edit, on-test, on-commit,
on-session events running user scripts; hook output
can block with a reason the coder must answer.``

What already shipped, and what this slice adds:

* The gap audit names ``core/lifecycle.py`` as this
  slice's basis. That module is a cooperative thread
  lifecycle registry: it registers worker threads
  with stop signals and shuts them down within a
  bounded budget. It knows nothing about user
  scripts, names no lifecycle event a tool, edit,
  test run, commit or session could fire, and judges
  no script's result. No hooks module, no hooks
  setting and no hook surface exists in the tree.
* This slice is that missing lifecycle, as a pure
  layer: the seven hook events as data, a hook
  (one event, one user script command, an optional
  name, an enabled flag, a bounded timeout) validated
  as data, a mechanical verdict for one finished
  hook run - allow, block, or error - read from the
  run's exit code and its JSON output alone, and a
  block shaped as news, with the reason the coder
  must answer. This module writes no file, changes
  no setting and runs no script itself; the agent
  layer owns holding the configured hooks, running
  a hook's command when its event fires, asking
  this layer to judge the result, and publishing a
  block as session news.

Honesty rules, enforced here and pinned by tests:

* **Decisions are mechanical.** A verdict reads the
  exit code and the JSON output record - nothing
  else. Exit 0 allows; exit 2 blocks; a JSON record
  saying block blocks at any exit code; any other
  non-zero exit is an error, never dressed up as
  an allow and never silently a block.
* **A block carries its reason.** The reason comes
  from the hook's own words - the JSON record's
  reason, else stderr, else stdout. A block that
  gives no reason still blocks, with the fallback
  reason stated plainly, so the coder always has a
  reason it must answer.
* **An error blocks only where blocking is honest.**
  A hook that fails before the act (pre_tool,
  pre_edit) or at a gate (on_test, on_commit) stops
  the act - the check it guarded did not pass. A
  hook that fails after the act (post_tool,
  post_edit, on_session) cannot rewrite what already
  happened: its error is news only.
* **Malformed refuses.** An unknown event, an empty
  command, an out-of-range timeout and unknown keys
  in a hook mapping all raise instead of being
  skipped or guessed at; one bad hook refuses the
  whole configured list rather than silently
  narrowing what the user wrote.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple

__all__ = [
    "DECISIONS",
    "ERROR_BLOCKING_EVENTS",
    "HOOK_EVENTS",
    "HOOKS_SLICE",
    "NO_REASON",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "USAGE",
    "Hook",
    "HookVerdict",
    "block_record",
    "build_hook",
    "build_hooks",
    "evaluate_result",
    "format_block",
    "format_hook",
    "format_hooks",
    "format_verdict",
    "hook_label",
    "hooks_from_config",
    "normalize_event",
    "parse_hook_output",
    "parse_hooks_args",
    "select_hooks",
    "validate_hook",
    "validate_hooks",
]

HOOKS_SLICE = "M-101"

SETTING_KEY = "hooks"

#: The seven lifecycle events a hook can ride on,
#: in lifecycle order.
HOOK_EVENTS = (
    "pre_tool",
    "post_tool",
    "pre_edit",
    "post_edit",
    "on_test",
    "on_commit",
    "on_session",
)

DECISIONS = ("allow", "block", "error")

#: Events where a hook *error* also blocks: the act
#: has not happened yet (pre_*) or the event is a
#: gate the work must pass (on_test, on_commit).
#: Errors at the remaining events are news only.
ERROR_BLOCKING_EVENTS = frozenset(
    {"pre_tool", "pre_edit", "on_test", "on_commit"})

#: The reason a block carries when the hook gave none.
NO_REASON = "the hook blocked giving no reason"

PLAIN_EXPLANATION = (
    "Hooks are user scripts the lifecycle runs at "
    "seven events - pre_tool, post_tool, pre_edit, "
    "post_edit, on_test, on_commit and on_session. "
    "A hook's exit code and JSON output judge its "
    "run mechanically: exit 0 allows, exit 2 blocks, "
    "a JSON block blocks at any exit code, and any "
    "other failure is an error - blocking before "
    "the act or at a gate, news only after it. A "
    "block is news carrying the reason the coder "
    "must answer. This layer judges and formats "
    "only; it runs no script itself."
)

USAGE = (
    "Usage: /hooks, /hooks list, /hooks show, "
    "/hooks show <event>, /hooks check <event>"
)

_HOOK_KEYS = frozenset(
    {"event", "command", "script", "name", "enabled",
     "timeout_seconds", "timeout"})


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def normalize_event(value: Any) -> str:
    """The canonical event a word names, or a refusal.

    Event words read case-insensitively, with dashes
    read as underscores (``pre-tool`` is
    ``pre_tool``). An unknown event raises - a hook
    on an event this layer does not name is never
    guessed at.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in HOOK_EVENTS:
            return wanted
    raise ValueError(
        "a hook event must be one of %s, got %r"
        % ("/".join(HOOK_EVENTS), value))


def _clean_timeout(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"a hook timeout must be whole seconds, got {value!r}")
    if value < 1 or value > 600:
        raise ValueError(
            f"a hook timeout must be 1..600 seconds, got {value!r}")
    return value


# ---------------------------------------------------------------------
# The hook: one event, one user script, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Hook:
    """One hook: a user script command riding one event.

    Constructing one validates it - an unknown event,
    an empty command, a non-bool enabled flag and an
    out-of-range timeout all raise - so a Hook that
    exists is a hook the lifecycle could run.
    """

    event: str
    command: str
    name: str = ""
    enabled: bool = True
    timeout_seconds: int = 30

    def __post_init__(self) -> None:
        object.__setattr__(self, "event", normalize_event(self.event))
        object.__setattr__(
            self, "command", _clean_text(self.command, "a hook command"))
        if not isinstance(self.name, str):
            raise ValueError(f"a hook name must be text, got {self.name!r}")
        object.__setattr__(self, "name", self.name.strip())
        if not isinstance(self.enabled, bool):
            raise ValueError(
                f"a hook's enabled flag must be true or false, "
                f"got {self.enabled!r}")
        object.__setattr__(
            self, "timeout_seconds", _clean_timeout(self.timeout_seconds))

    @property
    def label(self) -> str:
        """The hook's name, or its command when unnamed."""
        return self.name or self.command

    def to_record(self) -> Dict[str, Any]:
        return {
            "event": self.event,
            "command": self.command,
            "name": self.name,
            "enabled": self.enabled,
            "timeout_seconds": self.timeout_seconds,
        }


def hook_label(hook: Any) -> str:
    """The label one hook is judged and reported under."""
    if isinstance(hook, Hook):
        return hook.label
    if isinstance(hook, str) and hook.strip():
        return hook.strip()
    raise ValueError(f"a hook label needs a hook, got {hook!r}")


def validate_hook(spec: Any) -> Hook:
    """Validate one hook mapping into a Hook.

    The mapping names an ``event`` and a ``command``
    (or ``script``); ``name``, ``enabled`` and
    ``timeout_seconds`` (or ``timeout``) may ride
    along. Naming both spellings of one field with
    different values refuses, and unknown keys
    refuse - a hook is never repaired by guessing.
    """
    if isinstance(spec, Hook):
        return spec
    if not isinstance(spec, dict):
        raise ValueError("a hook must be a mapping")
    unknown = set(spec) - _HOOK_KEYS
    if unknown:
        raise ValueError(
            "unknown hook keys: %s" % ", ".join(sorted(unknown)))
    if "event" not in spec:
        raise ValueError("a hook is missing its event")
    command = spec.get("command", spec.get("script"))
    if command is None:
        raise ValueError("a hook is missing its command")
    if "command" in spec and "script" in spec \
            and spec["command"] != spec["script"]:
        raise ValueError("a hook names two different commands")
    timeout = spec.get("timeout_seconds", spec.get("timeout", 30))
    if "timeout_seconds" in spec and "timeout" in spec \
            and spec["timeout_seconds"] != spec["timeout"]:
        raise ValueError("a hook names two different timeouts")
    return Hook(
        event=spec["event"], command=command,
        name=spec.get("name", ""),
        enabled=spec.get("enabled", True),
        timeout_seconds=timeout)


def build_hook(event: Any, command: Any, name: Any = "",
               enabled: Any = True,
               timeout_seconds: Any = 30) -> Hook:
    """Build one validated hook from its pieces."""
    return Hook(event=event, command=command, name=name,
                enabled=enabled, timeout_seconds=timeout_seconds)


def validate_hooks(specs: Any) -> Tuple[Hook, ...]:
    """Validate a whole hook list, in listed order.

    ``None`` is the empty list. Every hook must
    validate; one malformed hook refuses the whole
    list rather than silently narrowing what the
    user configured.
    """
    if specs is None:
        return ()
    if isinstance(specs, (str, bytes)) or not isinstance(
            specs, (list, tuple)):
        raise ValueError("hooks must be a list of hooks")
    return tuple(validate_hook(spec) for spec in specs)


#: The list builder under its building name.
build_hooks = validate_hooks


def hooks_from_config(config: Dict[str, Any]) -> Tuple[Hook, ...]:
    """The hooks *config* holds, validated whole.

    The hooks ride under ``hooks`` as a list of hook
    mappings; absent means no hooks are configured.
    A malformed stored hook raises - stored data is
    never silently narrowed.
    """
    if not isinstance(config, dict):
        raise ValueError(f"hooks config must be a mapping, got {config!r}")
    return validate_hooks(config.get(SETTING_KEY))


def select_hooks(hooks: Sequence[Hook], event: Any) -> Tuple[Hook, ...]:
    """The enabled hooks for *event*, in listed order.

    A disabled hook never fires, and the order the
    hooks were configured in is the order they run
    in - selection preserves it exactly.
    """
    wanted = normalize_event(event)
    selected = validate_hooks(list(hooks)) if hooks is not None else ()
    return tuple(
        hook for hook in selected
        if hook.event == wanted and hook.enabled)


# ---------------------------------------------------------------------
# Judging one finished run: output parsing, then the verdict.
# ---------------------------------------------------------------------


def _json_record(text: str) -> Optional[Dict[str, Any]]:
    """One JSON object read from *text*, or None.

    The whole text, then each line, then the span
    from the first brace to the last are tried - a
    hook may print its record amid other words, but
    prose that merely contains braces is not a
    record, and non-object JSON is not a record.
    """
    candidates = [text.strip()]
    candidates.extend(line.strip() for line in text.splitlines())
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start:end + 1])
    for candidate in candidates:
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except ValueError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _record_reason(record: Dict[str, Any]) -> str:
    for key in ("reason", "message", "detail"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def parse_hook_output(stdout: Any = "", stderr: Any = "") -> Tuple[str, str]:
    """The (decision, reason) a hook's JSON output states.

    Stdout is read first, then stderr. A record with
    ``decision`` ``"block"``, or ``"block": true``,
    states a block; a record with ``decision``
    ``"allow"`` states an allow. The reason rides
    under ``reason`` (or ``message`` / ``detail``).
    Output with no such record states nothing and
    returns ``("", "")`` - the exit code then judges
    the run alone.
    """
    for text in (stdout, stderr):
        if text is None:
            continue
        if not isinstance(text, str):
            raise ValueError(f"hook output must be text, got {text!r}")
        if not text.strip():
            continue
        record = _json_record(text)
        if record is None:
            continue
        reason = _record_reason(record)
        decision = record.get("decision")
        if isinstance(decision, str):
            wanted = decision.strip().lower()
            if wanted == "block":
                return ("block", reason)
            if wanted == "allow":
                return ("allow", reason)
        if record.get("block") is True:
            return ("block", reason)
    return ("", "")


@dataclass(frozen=True)
class HookVerdict:
    """The judgement of one finished hook run, as data.

    ``decision`` is allow, block or error; ``blocks``
    says whether the work stops - true for every
    block, and for an error only at an event in
    ``ERROR_BLOCKING_EVENTS``.
    """

    event: str
    hook: str
    decision: str
    reason: str
    exit_code: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "event", normalize_event(self.event))
        object.__setattr__(
            self, "hook", _clean_text(self.hook, "a hook label"))
        if self.decision not in DECISIONS:
            raise ValueError(
                "a hook decision must be one of %s, got %r"
                % ("/".join(DECISIONS), self.decision))
        if not isinstance(self.reason, str):
            raise ValueError(f"a verdict reason must be text, got {self.reason!r}")
        object.__setattr__(self, "reason", self.reason.strip())
        if isinstance(self.exit_code, bool) \
                or not isinstance(self.exit_code, int):
            raise ValueError(
                f"a hook exit code must be a whole number, "
                f"got {self.exit_code!r}")

    @property
    def blocks(self) -> bool:
        if self.decision == "block":
            return True
        if self.decision == "error":
            return self.event in ERROR_BLOCKING_EVENTS
        return False

    @property
    def allowed(self) -> bool:
        return self.decision == "allow"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "hook_verdict",
            "slice": HOOKS_SLICE,
            "event": self.event,
            "hook": self.hook,
            "decision": self.decision,
            "reason": self.reason,
            "exit_code": self.exit_code,
            "blocks": self.blocks,
        }


def evaluate_result(event: Any, hook: Any, exit_code: Any,
                    stdout: Any = "", stderr: Any = "") -> HookVerdict:
    """Judge one finished hook run, mechanically.

    A JSON block in the output blocks at any exit
    code, with the record's reason. Otherwise exit 0
    allows, exit 2 blocks (reason from stderr, then
    stdout, then the plain fallback), and any other
    non-zero exit is an error whose reason is the
    hook's own error words, or a plain statement of
    the exit code. A non-integer exit code raises -
    a run with no readable exit code is never judged
    by guessing.
    """
    canonical = normalize_event(event)
    label = hook_label(hook)
    if isinstance(exit_code, bool) or not isinstance(exit_code, int):
        raise ValueError(
            f"a hook exit code must be a whole number, got {exit_code!r}")
    out_text = "" if stdout is None else stdout
    err_text = "" if stderr is None else stderr
    if not isinstance(out_text, str) or not isinstance(err_text, str):
        raise ValueError("hook output must be text")
    decision, reason = parse_hook_output(out_text, err_text)
    if decision == "block":
        return HookVerdict(
            event=canonical, hook=label, decision="block",
            reason=reason or NO_REASON, exit_code=exit_code)
    if exit_code == 0:
        return HookVerdict(
            event=canonical, hook=label, decision="allow",
            reason=reason if decision == "allow" else "",
            exit_code=exit_code)
    if exit_code == 2:
        block_reason = err_text.strip() or out_text.strip() or NO_REASON
        return HookVerdict(
            event=canonical, hook=label, decision="block",
            reason=block_reason, exit_code=exit_code)
    error_reason = (
        err_text.strip() or out_text.strip()
        or f"the hook failed with exit code {exit_code}")
    return HookVerdict(
        event=canonical, hook=label, decision="error",
        reason=error_reason, exit_code=exit_code)


def block_record(verdict: Any) -> Optional[Dict[str, Any]]:
    """The news record of one blocking verdict, or None.

    A verdict that does not block is not news of a
    block and returns None - the agent layer
    publishes this record as a session event when
    it is not None, so a block can never be lost as
    a mere log line.
    """
    if not isinstance(verdict, HookVerdict):
        raise ValueError(f"block_record needs a hook verdict, got {verdict!r}")
    if not verdict.blocks:
        return None
    return {
        "type": "hook_block",
        "news": True,
        "event": verdict.event,
        "hook": verdict.hook,
        "reason": verdict.reason,
    }


# ---------------------------------------------------------------------
# The /hooks surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_hook(hook: Any) -> str:
    """One hook, in plain words, from the hook."""
    validated = validate_hook(hook)
    state = "enabled" if validated.enabled else "disabled"
    name = f" {validated.name!r}" if validated.name else ""
    return (
        f"{validated.event}:{name} {validated.command} "
        f"({state}, timeout {validated.timeout_seconds}s)")


def format_hooks(hooks: Any) -> str:
    """The configured hooks, in plain words, in order.

    Accepts a hook list or a whole config mapping.
    With no hooks configured the text starts with
    the plain statement of that fact.
    """
    if isinstance(hooks, dict):
        selected = hooks_from_config(hooks)
    else:
        selected = validate_hooks(hooks)
    if not selected:
        return (
            "Hooks: none configured. No user scripts "
            "run at any lifecycle event.")
    lines = [f"Hooks: {len(selected)} configured."]
    for hook in selected:
        lines.append(f"  {format_hook(hook)}")
    return "\n".join(lines)


def format_verdict(verdict: Any) -> str:
    """One verdict, in plain words, from the verdict."""
    if not isinstance(verdict, HookVerdict):
        raise ValueError(f"format_verdict needs a hook verdict, got {verdict!r}")
    if verdict.decision == "allow":
        return (
            f"Hook allowed: {verdict.event} hook {verdict.hook!r} "
            f"allowed the work (exit {verdict.exit_code}).")
    if verdict.decision == "block":
        return (
            f"Hook block: {verdict.event} hook {verdict.hook!r} "
            f"blocked - {verdict.reason}")
    stops = "blocks the work" if verdict.blocks else "news only"
    return (
        f"Hook error: {verdict.event} hook {verdict.hook!r} "
        f"failed (exit {verdict.exit_code}) - {verdict.reason} "
        f"({stops}).")


def format_block(verdict: Any) -> str:
    """One block as the headline the session shows.

    Accepts a blocking ``HookVerdict`` or its
    ``hook_block`` record; a verdict that does not
    block has no block headline and raises, exactly
    as an allowed reach has no refusal.
    """
    if isinstance(verdict, HookVerdict):
        record = block_record(verdict)
        if record is None:
            raise ValueError("this verdict does not block; there is no block")
        verdict = record
    if isinstance(verdict, dict) and verdict.get("type") == "hook_block":
        return (
            f"Hook block: {verdict['event']} hook {verdict['hook']!r} "
            f"blocked - {verdict['reason']}")
    raise ValueError("format_block needs a blocking hook verdict")


def parse_hooks_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /hooks grammar both surfaces share.

    No words (or ``list`` / ``show``) shows the
    hooks; ``show <event>`` and a bare event word
    show one event's hooks; ``check <event>`` asks
    which hooks would fire at that event. The event
    is validated and canonicalised here. Anything
    else is a usage error naming the grammar.
    Returns ``(action, event-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("list", "show"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "show" and len(words) == 2:
        try:
            return ("show", normalize_event(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head == "check" and len(words) == 2:
        try:
            return ("check", normalize_event(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if len(words) == 1:
        try:
            return ("show", normalize_event(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
