"""Edit-format plurality (All-Features roadmap slice M-071).

Part IV — The Editor's Hand — opens here. The coder no longer
has one way to change a file: it picks, per task and per model
strength, between whole-file, unified-diff, search-and-replace
blocks, and Aider-style architect/editor splitting — and the
choice is journaled.

What already shipped, and what this slice adds:

* ``mythic_agent.core.edits.EditJournal`` already writes a
  whole file atomically with a durable journal, and already
  replaces a block that matches exactly once. Unified diffs
  existed only as *previews* (``tools/smart_files.py``,
  ``integrations/lsp.py``, ``tools/structural_rewrite.py``) —
  nothing in the tree could apply one. Architect/editor
  splitting did not exist at all.
* This slice is the plurality layer over that machinery: the
  four formats as data, strict appliers for the three concrete
  formats, a per-task / per-model-strength choice, an
  architect/editor split for complex work, and the surfaces.
  Applied edits ride the existing EditJournal road through
  the agent layer — this module itself writes no file.

Honesty rules, enforced here and pinned by the slice's tests:

* **No fuzz, ever.** A unified-diff hunk applies only when
  its context and removed lines match the file exactly at
  the stated position; a search block applies only when it
  matches exactly once. A moved or changed target refuses
  cleanly and changes nothing — the bounded repair loop
  that retries with the true text is M-073's road, not a
  silent fuzzy match here.
* **Model strength is M-027 truth, never a guess.** A model
  is *strong* only when its capability record says its
  reasoning is known-true, *standard* only when its tool
  calling is known-true, and *unknown* otherwise — an
  unlisted model is unknown. Unknown strength always gets
  the safest format (whole-file): a model whose strength is
  not proven is never asked to produce a delicate diff.
* **The architect never edits.** In a split, the architect
  pass produces per-file intents only; the editor pass picks
  a concrete format per file and is the only side that can
  carry a payload. ``architect`` itself is not an appliable
  format — applying it refuses and says why.
* **Every choice carries its plain-words reason** and is
  journaled by the agent layer as an ``edit_format_chosen``
  session event; a pinned (non-auto) setting is honoured
  exactly, except that creating a file is always whole-file
  (a diff or a search block cannot create what is not there),
  and that override is named in the reason, never silent.
* A malformed stored setting raises instead of being
  guessed at, exactly like M-030/M-031's settings.
"""

from __future__ import annotations

__all__ = [
    "FORMAT_IDS",
    "PLAIN_EXPLANATION",
    "EDIT_FORMATS_SLICE",
    "SETTING_KEY",
    "SETTING_VALUES",
    "STRENGTHS",
    "TASK_KIND_IDS",
    "Any",
    "ArchitectSplit",
    "ArchitectStep",
    "Dict",
    "EditFormat",
    "EditFormatChange",
    "FormatChoice",
    "List",
    "Optional",
    "Sequence",
    "TaskKind",
    "Tuple",
    "apply_edit",
    "apply_search_replace",
    "apply_unified_diff",
    "apply_whole_file",
    "choose_format",
    "format_choice",
    "format_edit_formats",
    "format_setting_change",
    "get_format",
    "get_task_kind",
    "list_formats",
    "list_task_kinds",
    "model_strength",
    "parse_editformat_args",
    "plan_split",
    "set_setting",
    "setting_from_config",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .model_capabilities import ModelCapabilities, load_capabilities

#: The slice that owns this module.
EDIT_FORMATS_SLICE = "M-071"

#: The config key the preferred-format setting lives under.
SETTING_KEY = "edit_format"

#: The setting explained in plain words — the sentence every
#: surface shows.
PLAIN_EXPLANATION = (
    "Edit formats: Mythic can change a file four ways — "
    "rewrite the whole file, apply a unified diff, swap a "
    "search-and-replace block, or split the work Aider-style "
    "(an architect model plans, an editor model edits). With "
    "the setting on auto (the default), the coder picks per "
    "task and per model strength: a model whose strength is "
    "proven gets the cheaper diff formats, a model whose "
    "strength is unknown gets the safest whole-file rewrite, "
    "and complex work is split. Every pick is written into "
    "the session journal with its reason. Pin one format "
    "with /editformat <format>, or return to auto with "
    "/editformat auto."
)

USAGE = ("Usage: /editformat, /editformat auto, "
         "/editformat <format>, or /editformat <task-kind>")


@dataclass(frozen=True)
class EditFormat:
    """One way the coder can change a file.

    ``appliable`` is True only for the three concrete payload
    formats; ``architect`` is a split, never a payload.
    ``strength_floor`` names the weakest model strength the
    auto-choice may hand this format to.
    """

    id: str
    title: str
    plain: str
    appliable: bool
    strength_floor: str


#: The four formats, in roadmap order.
_FORMATS: Tuple[EditFormat, ...] = (
    EditFormat(
        "whole-file", "Whole-file",
        "The model writes the file's full new text. The "
        "safest format — nothing to mis-apply — and the "
        "costliest in tokens for a large file.",
        True, "unknown"),
    EditFormat(
        "unified-diff", "Unified-diff",
        "The model writes a unified diff; Mythic applies it "
        "only when every hunk's context matches the file "
        "exactly — no fuzz. Cheap for changes spread across "
        "a file, delicate for a weak model to produce.",
        True, "strong"),
    EditFormat(
        "search-replace", "Search-and-replace blocks",
        "The model writes Aider-style SEARCH/REPLACE blocks; "
        "each search text must match exactly once, the "
        "EditJournal law. Cheap and sturdy for targeted "
        "changes in one or a few places.",
        True, "standard"),
    EditFormat(
        "architect", "Architect/editor split",
        "Aider-style splitting: the architect pass plans "
        "per-file intents and never edits; the editor pass "
        "picks a concrete format per file and applies it. "
        "For complex work spanning several files.",
        False, "unknown"),
)

FORMAT_IDS: Tuple[str, ...] = tuple(f.id for f in _FORMATS)

#: Model strengths, weakest first. Strength is M-027 truth:
#: reasoning known-true is strong, tool_calling known-true
#: is standard, everything else (including unlisted) unknown.
STRENGTHS: Tuple[str, ...] = ("unknown", "standard", "strong")


@dataclass(frozen=True)
class TaskKind:
    """One kind of editing task the choice is made for."""

    id: str
    title: str
    plain: str


_TASK_KINDS: Tuple[TaskKind, ...] = (
    TaskKind("new-file", "New file",
             "Creating a file that does not exist yet."),
    TaskKind("rewrite", "Rewrite",
             "Most of an existing file changes."),
    TaskKind("small-fix", "Small fix",
             "A targeted change in one or a few places."),
    TaskKind("multi-site", "Multi-site change",
             "Changes spread across several places in a file."),
    TaskKind("complex", "Complex work",
             "Work spanning several files that needs a plan "
             "before any edit."),
)

TASK_KIND_IDS: Tuple[str, ...] = tuple(t.id for t in _TASK_KINDS)

#: Per-file change kinds an architect plan may name, mapped
#: onto task kinds for the editor's per-file choice.
_FILE_CHANGE_KINDS: Dict[str, str] = {
    "create": "new-file",
    "rewrite": "rewrite",
    "targeted": "small-fix",
    "multi-site": "multi-site",
}

#: Every value the setting may hold: auto, or one pinned format.
SETTING_VALUES: Tuple[str, ...] = ("auto",) + FORMAT_IDS


def list_formats() -> Tuple[EditFormat, ...]:
    """Every edit format, in roadmap order."""
    return _FORMATS


def get_format(format_id: str) -> EditFormat:
    """The format named *format_id* (ValueError if unknown)."""
    key = (format_id or "").strip()
    for fmt in _FORMATS:
        if fmt.id == key:
            return fmt
    raise ValueError(
        f"unknown edit format {format_id!r}; choose one of: "
        + ", ".join(FORMAT_IDS))


def list_task_kinds() -> Tuple[TaskKind, ...]:
    """Every task kind the choice is made for, in order."""
    return _TASK_KINDS


def get_task_kind(task_kind: str) -> TaskKind:
    """The task kind named *task_kind* (ValueError if unknown)."""
    key = (task_kind or "").strip()
    for kind in _TASK_KINDS:
        if kind.id == key:
            return kind
    raise ValueError(
        f"unknown edit task kind {task_kind!r}; choose one of: "
        + ", ".join(TASK_KIND_IDS))


def setting_from_config(config: Dict[str, Any]) -> str:
    """The stored edit-format setting: 'auto' or a pinned format.

    Absent means 'auto'. A malformed stored value raises —
    a setting is never guessed at.
    """
    value = config.get(SETTING_KEY, "auto")
    if value not in SETTING_VALUES:
        raise ValueError(
            f"{SETTING_KEY} must be one of: "
            + ", ".join(SETTING_VALUES) + f"; got {value!r}")
    return str(value)


@dataclass(frozen=True)
class EditFormatChange:
    """A recorded change of the pinned-format setting."""

    before: str
    after: str

    def event(self) -> Dict[str, Any]:
        return {"type": "edit_format_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "edit_format_setting_changed",
                "from": self.before, "to": self.after,
                "session_id": session_id, "journaled": journaled}


def set_setting(config: Dict[str, Any],
                value: str) -> Tuple[str, EditFormatChange]:
    """Validate setting *value* against *config*, purely.

    Returns the value and the change to journal. Refuses a
    no-change and any value outside SETTING_VALUES.
    """
    if value not in SETTING_VALUES:
        raise ValueError(
            f"{SETTING_KEY} must be one of: "
            + ", ".join(SETTING_VALUES) + f"; got {value!r}")
    before = setting_from_config(config)
    if value == before:
        raise ValueError(f"edit format setting is already {value}")
    return value, EditFormatChange(before=before, after=value)


def model_strength(model: Optional[str],
                   caps: Optional[ModelCapabilities] = None) -> str:
    """The proven strength of *model*, from M-027 truth.

    reasoning known-true -> 'strong'; tool_calling
    known-true -> 'standard'; anything else — unknown
    flags, no model, an unlisted model — -> 'unknown'.
    """
    if not model:
        return "unknown"
    truth = caps if caps is not None else load_capabilities()
    record = truth.for_model(model)
    if record.reasoning is True:
        return "strong"
    if record.tool_calling is True:
        return "standard"
    return "unknown"


@dataclass(frozen=True)
class FormatChoice:
    """One journaled pick: a format, for a task, with its reason."""

    format_id: str
    task_kind: str
    model: Optional[str]
    strength: str
    split: bool
    reason: str

    def event(self) -> Dict[str, Any]:
        return {"type": "edit_format_chosen",
                "format": self.format_id,
                "task_kind": self.task_kind,
                "model": self.model,
                "strength": self.strength,
                "split": self.split,
                "reason": self.reason}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {**self.event(), "session_id": session_id,
                "journaled": journaled}


def _meets_floor(strength: str, format_id: str) -> bool:
    """True when *strength* meets *format_id*'s strength floor.

    The floors are the formats' own data (``strength_floor``):
    the auto-choice may hand a format only to a model at least
    as strong as its floor, strengths ordered weakest first in
    STRENGTHS.
    """
    floor = get_format(format_id).strength_floor
    return STRENGTHS.index(strength) >= STRENGTHS.index(floor)


def _auto_format(task_kind: str, strength: str) -> Tuple[str, bool, str]:
    """The auto rule: (format_id, split, plain-words reason)."""
    if task_kind == "new-file":
        return ("whole-file", False,
                "a new file is written whole — there is nothing "
                "for a diff or a search block to match against")
    if task_kind == "rewrite":
        return ("whole-file", False,
                "most of the file changes, so the whole file is "
                "written — a diff would cost as much and risk more")
    if task_kind == "small-fix":
        if _meets_floor(strength, "search-replace"):
            return ("search-replace", False,
                    f"a targeted change and a {strength} model: "
                    "a search-and-replace block is cheap, and its "
                    "search text must match exactly once or refuse")
        return ("whole-file", False,
                "a targeted change, but the model's strength is "
                "unknown — the safest format wins: the whole file "
                "is written, so nothing delicate can mis-apply")
    if task_kind == "multi-site":
        if _meets_floor(strength, "unified-diff"):
            return ("unified-diff", False,
                    "changes spread across the file and a strong "
                    "model: a unified diff covers every site in "
                    "one payload, applied only on exact context")
        if _meets_floor(strength, "search-replace"):
            return ("search-replace", False,
                    "changes spread across the file and a "
                    "standard model: one search-and-replace block "
                    "per site — sturdier for this strength than "
                    "producing a whole diff")
        return ("whole-file", False,
                "changes spread across the file, but the "
                "model's strength is unknown — the safest "
                "format wins: the whole file is written")
    # complex
    return ("architect", True,
            "complex work spanning several files is split "
            "Aider-style: the architect plans per-file intents "
            "and never edits; the editor picks a concrete "
            f"format per file for a {strength} model")


def choose_format(task_kind: str, model: Optional[str] = None,
                  config: Optional[Dict[str, Any]] = None,
                  caps: Optional[ModelCapabilities] = None
                  ) -> FormatChoice:
    """Pick the edit format for *task_kind* and *model*.

    A pinned setting (from *config*) is honoured exactly,
    except creating a file, which is always whole-file —
    the override is named in the reason. Under 'auto' the
    pick follows the task and the model's proven strength.
    """
    kind = get_task_kind(task_kind)
    strength = model_strength(model, caps)
    pinned = setting_from_config(config) if config is not None else "auto"
    if pinned != "auto":
        if kind.id == "new-file" and pinned != "whole-file":
            return FormatChoice(
                format_id="whole-file", task_kind=kind.id,
                model=model, strength=strength, split=False,
                reason=(f"the setting pins {pinned}, but a new "
                        "file is always written whole — a diff, "
                        "a search block, or a split cannot "
                        "create what is not there"))
        return FormatChoice(
            format_id=pinned, task_kind=kind.id, model=model,
            strength=strength, split=(pinned == "architect"),
            reason=(f"the edit_format setting pins {pinned}; "
                    "a pinned format is honoured exactly"))
    format_id, split, reason = _auto_format(kind.id, strength)
    return FormatChoice(
        format_id=format_id, task_kind=kind.id, model=model,
        strength=strength, split=split, reason=reason)


@dataclass(frozen=True)
class ArchitectStep:
    """One file in a split: the architect's intent, the
    editor's concrete format. The architect side carries an
    intent and never a payload."""

    path: str
    change_kind: str
    intent: str
    format_id: str
    reason: str


@dataclass(frozen=True)
class ArchitectSplit:
    """A whole split: who plans, who edits, and the steps."""

    task_kind: str
    model: Optional[str]
    strength: str
    steps: Tuple[ArchitectStep, ...]
    reason: str

    def event(self) -> Dict[str, Any]:
        return {"type": "edit_format_chosen",
                "format": "architect",
                "task_kind": self.task_kind,
                "model": self.model,
                "strength": self.strength,
                "split": True,
                "files": [step.path for step in self.steps],
                "reason": self.reason}


def plan_split(files: Sequence[Tuple[str, str, str]],
               model: Optional[str] = None,
               caps: Optional[ModelCapabilities] = None
               ) -> ArchitectSplit:
    """Plan an architect/editor split over *files*.

    Each entry is ``(path, change_kind, intent)`` with
    change_kind one of create / rewrite / targeted /
    multi-site — the architect's per-file intent. The
    editor's concrete format per file is the auto choice
    for that file's change kind at the model's strength;
    it is never 'architect' itself.
    """
    if not files:
        raise ValueError("an architect split needs at least one file")
    strength = model_strength(model, caps)
    steps: List[ArchitectStep] = []
    seen: List[str] = []
    for path, change_kind, intent in files:
        if not isinstance(path, str) or not path:
            raise ValueError("each split step needs a file path")
        if path in seen:
            raise ValueError(f"split names {path!r} twice")
        seen.append(path)
        if change_kind not in _FILE_CHANGE_KINDS:
            raise ValueError(
                f"unknown change kind {change_kind!r} for {path}; "
                "choose one of: " + ", ".join(sorted(_FILE_CHANGE_KINDS)))
        if not isinstance(intent, str) or not intent:
            raise ValueError(f"split step for {path} needs an intent")
        task_kind = _FILE_CHANGE_KINDS[change_kind]
        format_id, _split, reason = _auto_format(task_kind, strength)
        steps.append(ArchitectStep(
            path=path, change_kind=change_kind, intent=intent,
            format_id=format_id,
            reason=f"editor's pick for a {change_kind} change: {reason}"))
    return ArchitectSplit(
        task_kind="complex", model=model, strength=strength,
        steps=tuple(steps),
        reason=("the architect planned "
                f"{len(steps)} file(s) and edits none of them; "
                "the editor applies each step in its concrete "
                "format"))


# ---------------------------------------------------------------------
# The appliers — pure text in, text out. No fuzz, ever.
# ---------------------------------------------------------------------

def apply_whole_file(current: Optional[str], payload: str) -> Tuple[str, int]:
    """Whole-file: the payload IS the new text. Units: 1."""
    if not isinstance(payload, str):
        raise ValueError("a whole-file payload must be text")
    return payload, 1


def _lines_and_ending(text: str) -> Tuple[List[str], bool]:
    if text == "":
        return [], False
    ending = text.endswith("\n")
    return (text[:-1] if ending else text).split("\n"), ending


def _join(lines: List[str], ending: bool) -> str:
    text = "\n".join(lines)
    return text + "\n" if ending and lines else text


_SEARCH = "<<<<<<< SEARCH"
_DIVIDER = "======="
_REPLACE = ">>>>>>> REPLACE"


def _parse_search_blocks(payload: str) -> List[Tuple[List[str], List[str]]]:
    lines = payload.split("\n")
    blocks: List[Tuple[List[str], List[str]]] = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == "":
            i += 1
            continue
        if lines[i] != _SEARCH:
            raise ValueError(
                "a search-and-replace payload is made of blocks "
                f"starting with {_SEARCH!r}; found {lines[i]!r}")
        i += 1
        search: List[str] = []
        while i < len(lines) and lines[i] != _DIVIDER:
            search.append(lines[i])
            i += 1
        if i >= len(lines):
            raise ValueError(f"a SEARCH block is missing its {_DIVIDER!r} line")
        i += 1
        replace: List[str] = []
        while i < len(lines) and lines[i] != _REPLACE:
            replace.append(lines[i])
            i += 1
        if i >= len(lines):
            raise ValueError(
                f"a SEARCH block is missing its {_REPLACE!r} line")
        i += 1
        blocks.append((search, replace))
    if not blocks:
        raise ValueError("the payload carries no SEARCH/REPLACE block")
    return blocks


def _find_block(lines: List[str], needle: List[str]) -> List[int]:
    if not needle:
        return []
    hits = []
    for start in range(0, len(lines) - len(needle) + 1):
        if lines[start:start + len(needle)] == needle:
            hits.append(start)
    return hits


def apply_search_replace(current: str, payload: str) -> Tuple[str, int]:
    """Apply Aider-style SEARCH/REPLACE blocks. Units: blocks.

    Each block's search lines must match exactly once, as a
    contiguous run — zero matches and several matches both
    refuse, and a refusal changes nothing (every block is
    judged against the evolving text in memory; the caller
    writes only on success). An empty SEARCH is allowed
    only into an empty file (creation).
    """
    if not isinstance(current, str) or not isinstance(payload, str):
        raise ValueError("search-and-replace works on text")
    blocks = _parse_search_blocks(payload)
    lines, ending = _lines_and_ending(current)
    for search, replace in blocks:
        if not search:
            if lines:
                raise ValueError(
                    "an empty SEARCH block can only create into "
                    "an empty file; name the text to replace")
            lines = list(replace)
            continue
        hits = _find_block(lines, search)
        if not hits:
            raise ValueError(
                "a SEARCH block matched nothing — the file does "
                "not hold that text; nothing was changed")
        if len(hits) > 1:
            raise ValueError(
                f"a SEARCH block matched {len(hits)} places — it "
                "must match exactly once; nothing was changed")
        start = hits[0]
        lines[start:start + len(search)] = replace
    return _join(lines, ending), len(blocks)


_HUNK_RE = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?:\s.*)?$")


def apply_unified_diff(current: str, payload: str) -> Tuple[str, int]:
    """Apply a unified diff strictly. Units: hunks.

    Every hunk's context and removed lines must match the
    file exactly at the position the hunk states (shifted
    by earlier hunks) — no fuzz, no offset search. A stale
    hunk refuses and changes nothing.
    """
    if not isinstance(current, str) or not isinstance(payload, str):
        raise ValueError("a unified diff works on text")
    raw = payload.split("\n")
    lines, ending = _lines_and_ending(current)
    hunks = 0
    offset = 0
    i = 0
    while i < len(raw):
        line = raw[i]
        if line.startswith("--- ") or line.startswith("+++ "):
            i += 1
            continue
        match = _HUNK_RE.match(line)
        if match is None:
            if line.strip() == "":
                i += 1
                continue
            raise ValueError(f"not a unified diff: line {line!r}")
        old_start = int(match.group(1))
        old_count = int(match.group(2)) if match.group(2) else 1
        new_count = int(match.group(4)) if match.group(4) else 1
        i += 1
        old_side: List[str] = []
        new_side: List[str] = []
        while i < len(raw) and not raw[i].startswith("@@ "):
            body = raw[i]
            if body.startswith("\\"):
                i += 1
                continue
            if body == "" and (len(old_side) >= old_count
                               and len(new_side) >= new_count):
                break
            prefix, text = (body[0], body[1:]) if body else (" ", "")
            if prefix == " ":
                old_side.append(text)
                new_side.append(text)
            elif prefix == "-":
                old_side.append(text)
            elif prefix == "+":
                new_side.append(text)
            else:
                raise ValueError(f"not a unified diff: line {body!r}")
            i += 1
            if len(old_side) >= old_count and len(new_side) >= new_count:
                break
        if len(old_side) != old_count or len(new_side) != new_count:
            raise ValueError(
                "a hunk's line counts do not match its header — "
                "the diff is malformed; nothing was changed")
        at = (old_start - 1 if old_count else old_start) + offset
        if at < 0 or at > len(lines):
            raise ValueError(
                "a hunk lands outside the file — the diff is "
                "stale; nothing was changed")
        if lines[at:at + len(old_side)] != old_side:
            raise ValueError(
                "a hunk's context does not match the file — "
                "the file changed since the diff was made; "
                "nothing was changed (no fuzz, ever)")
        lines[at:at + len(old_side)] = new_side
        offset += len(new_side) - len(old_side)
        hunks += 1
    if not hunks:
        raise ValueError("the payload carries no diff hunk")
    return _join(lines, ending), hunks


def apply_edit(format_id: str, current: Optional[str],
               payload: str) -> Tuple[str, int]:
    """Apply *payload* in format *format_id* to *current*.

    Returns (new_text, units applied). 'architect' refuses:
    a split is planned, then its concrete formats applied.
    A missing file (current None) is an empty file.
    """
    fmt = get_format(format_id)
    if not fmt.appliable:
        raise ValueError(
            "the architect format is a split, not a payload: "
            "plan it with the architect, then apply the "
            "editor's concrete format per file")
    text = current if current is not None else ""
    if fmt.id == "whole-file":
        return apply_whole_file(text, payload)
    if fmt.id == "unified-diff":
        return apply_unified_diff(text, payload)
    return apply_search_replace(text, payload)


# ---------------------------------------------------------------------
# The /editformat surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_editformat_args(args: str) -> Dict[str, Any]:
    """Parse ``/editformat`` arguments.

    /editformat                -> show
    /editformat auto           -> pin the setting back to auto
    /editformat <format>       -> pin that format
    /editformat <task-kind>    -> choose for that kind of work
    """
    text = (args or "").strip()
    if not text:
        return {"action": "show"}
    parts = text.split()
    if len(parts) != 1:
        raise ValueError(USAGE + " (one word at a time)")
    word = parts[0]
    if word in SETTING_VALUES:
        return {"action": "setting", "value": word}
    if word in TASK_KIND_IDS:
        return {"action": "choose", "task_kind": word}
    raise ValueError(
        f"unknown /editformat word {word!r}; " + USAGE)


def format_choice(choice: FormatChoice) -> str:
    """One choice, in plain words, with its reason."""
    return (f"Edit format for {choice.task_kind}: {choice.format_id} "
            f"(model {choice.model or 'none'}, strength "
            f"{choice.strength}) — {choice.reason}.")


def format_setting_change(record: Dict[str, Any]) -> str:
    """A setting change record, in plain words."""
    return (f"Edit format setting: {record['from']} -> "
            f"{record['to']}.")


def format_edit_formats(config: Dict[str, Any]) -> str:
    """The whole plurality, in plain words, for /editformat.

    Built from list_formats() / list_task_kinds() /
    setting_from_config() / model_strength() /
    choose_format() / plan_split(), so every public road
    this module offers is exercised by its own show surface.
    """
    setting = setting_from_config(config)
    model = config.get("model")
    strength = model_strength(model)
    lines = ["Edit formats (M-071) — " + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {setting}. Current model: "
                 f"{model or 'none'} (strength {strength}).")
    lines.append("")
    lines.append("The four formats:")
    for fmt in list_formats():
        lines.append(f"  {fmt.id} — {fmt.title} "
                     f"(strength floor: {fmt.strength_floor}): "
                     f"{fmt.plain}")
    lines.append("")
    lines.append("Auto picks for this model:")
    for kind in list_task_kinds():
        choice = choose_format(kind.id, model=model, config=config)
        lines.append(f"  {kind.id} ({kind.title}): "
                     f"{choice.format_id} — {kind.plain}")
    lines.append("")
    split = plan_split(
        [("app.py", "targeted", "fix the paging off-by-one"),
         ("new_mod.py", "create", "hold the new helper")],
        model=model)
    lines.append("A split, as the editor would run it:")
    for step in split.steps:
        lines.append(f"  {step.path} ({step.change_kind}): "
                     f"{step.format_id} — {step.intent}")
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)
