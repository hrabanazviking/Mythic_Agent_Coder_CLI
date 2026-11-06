"""Editor bridges lite (roadmap slice M-090).

Part IV - The Editor's Hand. The roadmap's words:
``$EDITOR`` round-trip for any file or prompt at any
approval point (the terminal user's oldest right).

What already shipped, and what this slice adds:

* The terminal and TUI roads ask for text in their own
  widgets: a prompt is typed into the chat box, an edit
  is approved in place, a file's new contents arrive as
  an edit payload. The user's own editor - the program
  they have lived in for years, named by ``$VISUAL`` or
  ``$EDITOR`` - was never offered as a road: there was
  no way to say "let me write that in my editor" for a
  file, for a prompt draft, or for the text standing at
  an approval point.
* This slice is that road, as a pure layer. It resolves
  the editor honestly (``VISUAL`` first, then
  ``EDITOR`` - the terminal's own precedence), builds
  the command line for a round-trip, prepares the text
  that travels (a file's true current text, or a prompt
  draft), names the scratch file the editor will open
  (a file keeps its own suffix, so the editor's syntax
  knowledge still applies; a prompt travels as prose),
  and judges what comes back: changed, unchanged, or
  emptied - each with its own honest consequence. The
  agent layer owns the real scratch file, the real
  process launch and the journal; this module launches
  nothing and writes nothing.

Honesty rules, enforced here and pinned by tests:

* **No editor configured is a refusal, not a guess.**
  With neither ``VISUAL`` nor ``EDITOR`` set (or set to
  whitespace), resolving refuses and names the remedy -
  no built-in editor is ever substituted silently.
* **The editor command is the user's own words.**
  The stored value is split the way a shell splits it
  (``code --wait`` is two words); a malformed value
  raises in the user's own terms, never half-parsed.
* **Unchanged means unchanged.** A round-trip whose
  text comes back byte-identical is judged unchanged
  and writes nothing - the editor was opened, nothing
  is pretended to have happened.
* **An emptied file refuses.** Emptying a file through
  the editor never silently truncates it to nothing:
  the judgement refuses and names the file. An emptied
  *prompt*, by the terminal's oldest convention, is a
  cancellation - the user cleared the draft on purpose
  - and is judged cancelled, never sent.
* **Anchors, not impressions.** Every round-trip
  carries the SHA-256 anchor of the text that went
  out; the judgement compares anchors, so "changed"
  is proven, not eyeballed.
* **The setting is a gate, not a guess.** With
  ``editor_bridge`` off, round-trips through the agent
  layer refuse and say so; the pure resolution and
  judgement maths stays available. A malformed stored
  setting raises, never defaults silently.
"""

from __future__ import annotations

__all__ = [
    "EDITOR_BRIDGE_SLICE",
    "NO_EDITOR_REMEDY",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "USAGE",
    "Any",
    "BoolChange",
    "Dict",
    "EditorChoice",
    "List",
    "Optional",
    "RoundTrip",
    "RoundTripOutcome",
    "Tuple",
    "editor_command",
    "enabled_from_config",
    "format_editor_bridge",
    "format_round_trip",
    "format_setting_change",
    "judge_round_trip",
    "parse_editor_args",
    "prepare_file_round_trip",
    "prepare_prompt_round_trip",
    "resolve_editor",
    "set_enabled",
]

import hashlib
import os
import shlex
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

#: The slice that owns this module.
EDITOR_BRIDGE_SLICE = "M-090"

#: The config key the editor-bridge gate lives under.
SETTING_KEY = "editor_bridge"

#: The remedy named whenever no editor is configured.
NO_EDITOR_REMEDY = (
    "no editor is configured: set VISUAL or EDITOR to "
    "your editor (for example EDITOR=nano) and try again"
)

#: The setting explained in plain words.
PLAIN_EXPLANATION = (
    "Editor bridges lite: at any point where text is "
    "about to be used - a file you are editing, a prompt "
    "you are drafting, the text standing at an approval "
    "point - the text can take a round-trip through your "
    "own editor instead. The editor is the one your "
    "terminal already names: VISUAL first, then EDITOR, "
    "split the way a shell splits it, so 'code --wait' "
    "works as written. The text travels to a scratch "
    "file (a real file keeps its own suffix, so your "
    "editor's syntax knowledge still applies; a prompt "
    "travels as prose), you edit and save, and what "
    "comes back is judged by its content anchor: "
    "byte-identical comes back as unchanged and writes "
    "nothing, changed text comes back as the new text, "
    "an emptied file refuses rather than silently "
    "truncating it, and an emptied prompt is a "
    "cancellation - the draft was cleared on purpose. "
    "With no editor configured the bridge refuses and "
    "names the remedy; no built-in editor is ever "
    "substituted silently."
)

USAGE = ("Usage: /editor, /editor on, /editor off, "
         "/editor file <path>, or /editor prompt")


def _anchor(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EditorChoice:
    """The resolved editor: whose word named it + argv.

    ``source`` is the variable that won (``VISUAL`` or
    ``EDITOR``); ``argv`` is the command split the way a
    shell splits it, ready to have a path appended.
    """

    source: str
    raw: str
    argv: Tuple[str, ...]

    @property
    def name(self) -> str:
        return self.argv[0]


def resolve_editor(environ: Dict[str, str]) -> EditorChoice:
    """Resolve the user's editor from *environ*.

    ``VISUAL`` wins over ``EDITOR`` (the terminal's own
    precedence). A variable set to whitespace counts as
    unset. With neither set, raises naming the remedy -
    no editor is ever guessed. A value a shell could
    not split raises in the same words.
    """
    for source in ("VISUAL", "EDITOR"):
        raw = environ.get(source)
        if raw is None or not raw.strip():
            continue
        try:
            argv = shlex.split(raw)
        except ValueError as exc:
            raise ValueError(
                f"{source}={raw!r} cannot be split into a "
                f"command: {exc}") from exc
        if not argv:
            continue
        return EditorChoice(source=source, raw=raw,
                            argv=tuple(argv))
    raise ValueError(NO_EDITOR_REMEDY)


def editor_command(environ: Dict[str, str],
                   scratch_path: str) -> List[str]:
    """The full command line for one round-trip."""
    choice = resolve_editor(environ)
    return [*choice.argv, scratch_path]


@dataclass(frozen=True)
class RoundTrip:
    """Text prepared for a round-trip through the editor.

    ``kind`` is ``file`` or ``prompt``; ``label`` is the
    file's path or the prompt's context (for example the
    approval point it stands at). ``anchor`` proves what
    went out.
    """

    kind: str
    label: str
    original: str
    anchor: str

    @property
    def scratch_name(self) -> str:
        """The scratch file's name for this round-trip.

        A file keeps its own suffix (the editor's syntax
        knowledge still applies); a prompt travels as
        markdown prose. The anchor prefix keeps two
        round-trips of different texts from colliding.
        """
        if self.kind == "file":
            suffix = os.path.splitext(self.label)[1] or ".txt"
        else:
            suffix = ".md"
        return f"mythic-editor-{self.anchor[:12]}{suffix}"

    def record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "label": self.label,
                "anchor": self.anchor,
                "bytes": len(self.original.encode("utf-8")),
                "scratch_name": self.scratch_name}


def prepare_file_round_trip(path: str,
                            current_text: str) -> RoundTrip:
    """Prepare a file's true current text for the editor."""
    if not path or not path.strip():
        raise ValueError("a file round-trip needs a path")
    return RoundTrip(kind="file", label=path,
                     original=current_text,
                     anchor=_anchor(current_text))


def prepare_prompt_round_trip(label: str,
                              draft_text: str) -> RoundTrip:
    """Prepare a prompt draft for the editor.

    *label* names where the prompt stands - a chat draft
    or an approval point - so the return judgement can
    name what was being written.
    """
    if not label or not label.strip():
        raise ValueError("a prompt round-trip needs a label")
    return RoundTrip(kind="prompt", label=label,
                     original=draft_text,
                     anchor=_anchor(draft_text))


@dataclass(frozen=True)
class RoundTripOutcome:
    """The judgement of what came back from the editor.

    ``status`` is ``changed``, ``unchanged``,
    ``refused`` (an emptied file) or ``cancelled`` (an
    emptied prompt). ``text`` is the text to use - the
    new text when changed, the original when unchanged,
    and ``None`` when nothing may be used.
    """

    status: str
    text: Optional[str]
    reason: str

    def record(self, trip: RoundTrip) -> Dict[str, Any]:
        return {"type": "editor_round_trip",
                "kind": trip.kind, "label": trip.label,
                "status": self.status,
                "anchor_before": trip.anchor,
                "anchor_after": (
                    _anchor(self.text)
                    if self.text is not None else None),
                "reason": self.reason}


def judge_round_trip(trip: RoundTrip,
                     returned_text: str) -> RoundTripOutcome:
    """Judge the text that came back from the editor."""
    if _anchor(returned_text) == trip.anchor:
        return RoundTripOutcome(
            status="unchanged", text=trip.original,
            reason="the editor returned the text "
                   "byte-identical; nothing to write")
    if not returned_text.strip():
        if trip.kind == "file":
            return RoundTripOutcome(
                status="refused", text=None,
                reason=(f"the editor emptied {trip.label}; "
                        "a file is never silently truncated "
                        "to nothing - the original stands"))
        return RoundTripOutcome(
            status="cancelled", text=None,
            reason=(f"the {trip.label} draft came back "
                    "empty; an emptied prompt is a "
                    "cancellation, never sent"))
    return RoundTripOutcome(
        status="changed", text=returned_text,
        reason="the editor changed the text; the new "
               "text is the round-trip's result")


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The editor_bridge setting stored in *config*.

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
        return {"type": "editor_bridge_setting_changed",
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
            f"editor bridge is already "
            f"{'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


def parse_editor_args(args: str) -> Dict[str, Any]:
    """Parse the /editor grammar both surfaces share.

    ``show`` / ``on`` / ``off`` stand alone; ``file``
    takes the path as the rest of the line (paths are
    free text); ``prompt`` stands alone - the draft it
    round-trips is the surface's own current draft.
    """
    text = (args or "").strip()
    if not text or text == "show":
        return {"action": "show"}
    if text == "on":
        return {"action": "on"}
    if text == "off":
        return {"action": "off"}
    if text == "prompt":
        return {"action": "prompt"}
    parts = text.split(None, 1)
    if parts[0] == "file" and len(parts) == 2 and parts[1].strip():
        return {"action": "file", "path": parts[1].strip()}
    raise ValueError(f"usage: {USAGE}")


def format_setting_change(record: Dict[str, Any]) -> str:
    state = "on" if record.get("to") else "off"
    return f"Editor bridge is now {state}."


def format_round_trip(trip: RoundTrip,
                      outcome: RoundTripOutcome) -> str:
    """Format one judged round-trip for either surface."""
    lines = [f"Editor round-trip ({trip.kind}) {trip.label}: "
             f"{outcome.status}"]
    lines.append(f"  {outcome.reason}")
    if outcome.status == "changed":
        lines.append(
            f"  anchor {_anchor(trip.original)[:12]} -> "
            f"{_anchor(outcome.text or '')[:12]}")
    return "\n".join(lines)


def format_editor_bridge(config: Dict[str, Any],
                         environ: Optional[Dict[str, str]] = None,
                         ) -> str:
    """The whole slice, in plain words, for /editor.

    Built from resolve_editor() / prepare_*() /
    judge_round_trip(), so the show surface exercises
    the road it names: an editor resolves (or its
    absence is stated honestly), and a demo draft is
    prepared and judged changed.
    """
    enabled = enabled_from_config(config)
    lines = ["Editor bridges lite (M-090) - "
             + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    env = dict(os.environ) if environ is None else environ
    try:
        choice = resolve_editor(env)
    except ValueError:
        lines.append(f"Editor: none - {NO_EDITOR_REMEDY}.")
    else:
        lines.append(
            f"Editor: {choice.name} (from {choice.source}: "
            f"{choice.raw})")
    lines.append("")
    trip = prepare_prompt_round_trip("demo draft", "draft\n")
    outcome = judge_round_trip(trip, "draft, edited\n")
    lines.append(format_round_trip(trip, outcome))
    return "\n".join(lines)
