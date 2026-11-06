"""Generated-code honesty (roadmap slice M-086).

Part IV - The Editor's Hand. The roadmap's words:
generated files are marked, their generator recorded;
hand-edits to generated files warn before saving.

What already shipped, and what this slice adds:

* The codebase already generates files in places (the
  roadmap data, the config catalogue, OWNERSHIP and
  PUBLIC_API inventories all say so on their faces),
  and generators elsewhere leave the same kinds of
  marks: a header naming the tool, a DO NOT EDIT line,
  an @generated tag. But nothing in the editor's hand
  read those marks: a generated file could be hand-
  edited like any other, the edit saved in silence,
  and the next regeneration quietly wiped it out -
  the loss discovered, if ever, long after the fact.
* This slice is the pure honesty layer for that: a
  file's text is classified from its own head - a
  marker in the opening lines, in a form generators
  actually leave - and the generator named in the
  marker is recorded as data, never guessed from the
  file's name or shape. A hand-edit assessed against
  a generated file carries a warning computed before
  any save: the file is generated, by whom, and the
  honest consequence (the next regeneration will
  overwrite the edit; edit the generator or its
  inputs instead). This module writes no file: the
  agent layer asks it before saving, so the warning
  always lands before the bytes, never after.

Honesty rules, enforced here and pinned by tests:

* **A marker is evidence, not a vibe.** Only an
  explicit marker in the first lines of the file
  classifies it as generated: a generated-by line,
  a DO NOT EDIT line, an @generated tag, or a
  code-generated-by line. Prose mentioning the word
  generated deep in a file, or a filename that merely
  looks generated, never classifies.
* **The generator is recorded or recorded as absent.**
  When a marker names its generator, that name rides
  the record exactly. When a marker names none (a
  bare DO NOT EDIT), the record says the generator
  is unknown - never a name invented to fill the gap.
* **Hand-edits warn before saving, always.** With the
  setting on, an edit to a generated file produces
  its warning as data before any write; the warning
  names the generator when known and states the
  overwrite consequence plainly. An unmarked file
  produces no warning - silence there is honest.
* **Marking is explicit and reversible in text.** The
  marker this layer writes for a newly generated file
  is one header line naming the generator, placed in
  the file's own comment style where one is known;
  a file already marked is never marked twice.
* **The setting is a gate, not a guess.** With
  ``generated_code`` off, edit warnings through the
  agent layer are not raised; the pure classification
  maths stays available. A malformed stored setting
  raises.
"""

from __future__ import annotations

__all__ = [
    "PLAIN_EXPLANATION",
    "GENERATED_CODE_SLICE",
    "SETTING_KEY",
    "USAGE",
    "Any",
    "BoolChange",
    "Dict",
    "EditAssessment",
    "GeneratedRecord",
    "List",
    "Marker",
    "Optional",
    "Tuple",
    "assess_edit",
    "classify_text",
    "detect_marker",
    "enabled_from_config",
    "format_edit_warning",
    "format_generated_code",
    "format_generated_record",
    "format_setting_change",
    "marker_header",
    "parse_generated_args",
    "register_generated",
    "set_enabled",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

GENERATED_CODE_SLICE = "M-086"
SETTING_KEY = "generated_code"
USAGE = "generated <path>"
PLAIN_EXPLANATION = (
    "Generated files say so on their faces: the mark "
    "is read, the generator is recorded, and a hand "
    "edit to a generated file warns before it saves - "
    "because the next regeneration would erase it.")
HEAD_LINES = 12

_BY_RE = re.compile(
    r"(?:code\s+)?generated\s+by\s+([^\n\r\[\]<>{}]+)", re.IGNORECASE)
_FILE_RE = re.compile(
    r"this\s+file\s+is\s+(?:auto[- ]?)?generated\b[^\n\r]*?"
    r"(?:by\s+([^\n\r\[\]<>{}]+))?", re.IGNORECASE)
_TAG_RE = re.compile(r"@generated\b(?:\s+(\S[^\n\r]*))?", re.IGNORECASE)
_DO_NOT_EDIT_RE = re.compile(r"do\s+not\s+edit\b", re.IGNORECASE)


@dataclass(frozen=True)
class Marker:
    """One explicit generated marker found in a file head."""

    line_number: int
    line_text: str
    form: str
    generator: Optional[str]

    def record(self) -> Dict[str, Any]:
        return {"line": self.line_number, "form": self.form,
                "generator": self.generator,
                "text": self.line_text.strip()}


def _clean_generator(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    name = raw.strip().strip("*#/<>- ").strip()
    name = re.sub(r"\s+", " ", name)
    if name.endswith("."):
        name = name[:-1].strip()
    return name or None


def detect_marker(text: Any) -> Optional[Marker]:
    """The first explicit generated marker in a file head.

    Only the first HEAD_LINES lines are evidence. A
    generated-by line, a this-file-is-generated line,
    an @generated tag, or a DO NOT EDIT line counts;
    anything else, and anything deeper in the file,
    does not. The generator is the name the marker
    itself carries, cleaned of comment decoration.
    """
    if not isinstance(text, str):
        raise ValueError("file text must be a string")
    for number, line in enumerate(text.splitlines()[:HEAD_LINES], 1):
        match = _BY_RE.search(line)
        if match:
            return Marker(line_number=number, line_text=line,
                          form="generated_by",
                          generator=_clean_generator(match.group(1)))
        match = _FILE_RE.search(line)
        if match:
            gen = _clean_generator(match.group(1)) if match.group(1) else None
            return Marker(line_number=number, line_text=line,
                          form="file_is_generated", generator=gen)
        match = _TAG_RE.search(line)
        if match:
            gen = _clean_generator(match.group(1)) if match.group(1) else None
            return Marker(line_number=number, line_text=line,
                          form="generated_tag", generator=gen)
        if _DO_NOT_EDIT_RE.search(line):
            return Marker(line_number=number, line_text=line,
                          form="do_not_edit", generator=None)
    return None


@dataclass(frozen=True)
class GeneratedRecord:
    """One file's generated classification, as data."""

    path: str
    is_generated: bool
    generator: Optional[str]
    marker: Optional[Marker]

    def record(self) -> Dict[str, Any]:
        return {"type": "generated_file", "slice": GENERATED_CODE_SLICE,
                "path": self.path, "is_generated": self.is_generated,
                "generator": self.generator,
                "marker": self.marker.record() if self.marker else None}


def _validate_path(raw: Any) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("path must be a non-empty string")
    path = raw.strip()
    if path.startswith("/") or path.startswith("\\"):
        raise ValueError(f"path must be repo-relative: {raw!r}")
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"path must be a clean repo-relative path: {raw!r}")
    return path


def classify_text(path: Any, text: Any) -> GeneratedRecord:
    """Classify one file from its own head text."""
    clean = _validate_path(path)
    marker = detect_marker(text)
    if marker is None:
        return GeneratedRecord(path=clean, is_generated=False,
                               generator=None, marker=None)
    return GeneratedRecord(path=clean, is_generated=True,
                           generator=marker.generator, marker=marker)


def register_generated(path: Any, generator: Any, *,
                       text: Any = "") -> GeneratedRecord:
    """Record a file as generated by a named generator.

    The generator name is required and recorded exactly
    (whitespace cleaned). When the file's current text
    already carries a marker, that marker governs and
    a conflicting generator name refuses - the record
    never silently disagrees with the file's own face.
    """
    clean = _validate_path(path)
    if not isinstance(generator, str) or not generator.strip():
        raise ValueError("generator must be a non-empty string")
    name = _clean_generator(generator)
    if not name:
        raise ValueError("generator must be a non-empty string")
    existing = detect_marker(text) if isinstance(text, str) else None
    if existing is not None:
        if existing.generator and existing.generator != name:
            raise ValueError(
                f"{clean} is already marked generated by "
                f"{existing.generator}, not {name}")
        return GeneratedRecord(path=clean, is_generated=True,
                               generator=existing.generator or name,
                               marker=existing)
    return GeneratedRecord(path=clean, is_generated=True,
                           generator=name, marker=None)


_COMMENT_PREFIX = {".py": "# ", ".sh": "# ", ".yaml": "# ", ".yml": "# ",
                   ".toml": "# ", ".js": "// ", ".ts": "// ",
                   ".java": "// ", ".c": "// ", ".go": "// ",
                   ".rs": "// ", ".md": "", ".txt": "", ".sql": "-- "}


def marker_header(path: Any, generator: Any) -> str:
    """The one header line that marks a file as generated.

    Written in the file's own comment style where one is
    known, plain otherwise. The line names the generator
    and carries the do-not-edit warning in one breath.
    """
    clean = _validate_path(path)
    name = _clean_generator(generator if isinstance(generator, str) else None)
    if not name:
        raise ValueError("generator must be a non-empty string")
    suffix = clean.rsplit(".", 1)[-1] if "." in clean else ""
    prefix = _COMMENT_PREFIX.get("." + suffix.lower(), "")
    return (f"{prefix}Generated by {name} - do not edit by hand; "
            f"regenerate instead.")


@dataclass(frozen=True)
class EditAssessment:
    """A hand-edit assessed before saving, as data."""

    path: str
    is_generated: bool
    generator: Optional[str]
    warns: bool
    warning: Optional[str]

    def record(self) -> Dict[str, Any]:
        return {"type": "generated_edit_assessment",
                "slice": GENERATED_CODE_SLICE, "path": self.path,
                "is_generated": self.is_generated,
                "generator": self.generator, "warns": self.warns,
                "warning": self.warning}


def assess_edit(record: GeneratedRecord, *,
                config: Optional[Dict[str, Any]] = None) -> EditAssessment:
    """Assess one hand-edit to one classified file.

    A generated file warns, before saving, naming its
    generator when known and stating the overwrite
    consequence. An unmarked file does not warn. With
    the generated_code setting off, no warning is
    raised even for a generated file - the gate is
    the user's word - but the classification itself
    still rides the assessment, never hidden.
    """
    warns = False
    warning = None
    if record.is_generated:
        enabled = True if config is None else enabled_from_config(config)
        if enabled:
            warns = True
            who = (f" by {record.generator}" if record.generator
                   else " (its generator is not recorded)")
            warning = (
                f"{record.path} is a generated file{who}: a hand "
                f"edit will be overwritten the next time it is "
                f"regenerated - edit the generator or its inputs "
                f"instead, or regenerate after editing.")
    return EditAssessment(path=record.path,
                          is_generated=record.is_generated,
                          generator=record.generator,
                          warns=warns, warning=warning)


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The generated_code setting stored in *config*.

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
        return {"type": "generated_code_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "generated_code_setting_changed",
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
            f"generated-code honesty is already "
            f"{'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The /generated surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_generated_args(args: str) -> Dict[str, Any]:
    """Parse the /generated grammar both surfaces share.

    ``show`` / ``on`` / ``off`` steer the gate; one path
    word classifies that file; ``mark <path> <words>``
    records a generator named by the remaining words;
    anything else is a usage error naming the grammar.
    """
    words = (args or "").split()
    if not words or words == ["show"]:
        return {"action": "show"}
    if words == ["on"]:
        return {"action": "on"}
    if words == ["off"]:
        return {"action": "off"}
    if words[0] == "mark":
        if len(words) < 3:
            raise ValueError(
                f"usage: generated mark <path> <generator> "
                f"(or: {USAGE} | generated show|on|off)")
        return {"action": "mark", "path": _validate_path(words[1]),
                "generator": " ".join(words[2:])}
    if len(words) == 1:
        return {"action": "check", "path": _validate_path(words[0])}
    raise ValueError(
        f"usage: {USAGE} (or: generated show|on|off | "
        f"generated mark <path> <generator>)")


def format_setting_change(record: Dict[str, Any]) -> str:
    state = "on" if record.get("to") else "off"
    return f"Generated-code honesty is now {state}."


def format_generated_record(record: GeneratedRecord) -> str:
    if not record.is_generated:
        return f"{record.path}: not marked as generated."
    who = record.generator or "unknown generator"
    lines = [f"{record.path}: generated by {who}."]
    if record.marker is not None:
        lines.append(
            f"Marker (line {record.marker.line_number}, "
            f"{record.marker.form}): {record.marker.line_text.strip()}")
    return "\n".join(lines)


def format_edit_warning(assessment: EditAssessment) -> str:
    if not assessment.warns:
        return f"{assessment.path}: no generated-file warning."
    return f"Warning before saving: {assessment.warning}"


def format_generated_code(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /generated.

    Built from classify_text() / assess_edit(), so the
    show surface exercises the honesty road it names:
    a worked example in which a marked file's hand-edit
    warns, naming its generator.
    """
    enabled = enabled_from_config(config)
    lines = ["Generated-code honesty (M-086) - "
             + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    lines.append("")
    record = classify_text(
        "build/output.py",
        "# Generated by build_tool v2 - do not edit by hand\nx = 1\n")
    lines.append("A sample file, as it is classified:")
    lines.append(format_generated_record(record))
    lines.append(format_edit_warning(assess_edit(record, config=config)))
    lines.append("")
    lines.append("Usage: /generated | /generated on | /generated off | "
                 "/generated <path> | "
                 "/generated mark <path> <generator>")
    return "\n".join(lines)
