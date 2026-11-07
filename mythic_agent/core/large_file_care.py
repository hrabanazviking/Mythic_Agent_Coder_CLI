"""Large-file and binary care (roadmap slice M-087).

Part IV - The Editor's Hand. The roadmap's words:
big files edited by anchored chunks; binaries never
text-edited; size guards explain themselves.

What already shipped, and what this slice adds:

* The codebase already guards size in scattered
  places, each in its own words: the context producers
  refuse a file over 262,144 bytes whole (the repo map
  and the symbol graph), asset sight calls a file at
  or over 1,000,000 bytes a large file and describes
  binaries instead of dumping them, and the context
  readers treat a NUL byte as the mark of a binary.
  But the editor's hand itself had no such care: a
  whole-file edit road could be aimed at a file far
  too big to hold whole, and nothing in the edit road
  itself refused to text-edit a binary - a refusal,
  where one existed, arrived from some other tool,
  unexplained.
* This slice is the pure care layer for the edit
  road: a file's bytes are classified once, from the
  bytes themselves - binary or text, small or large -
  and the classification carries its own explanation
  (the file's size, the guard it crossed, and the
  road that applies). A large text file is edited by
  anchored chunks: the text is split on line
  boundaries into byte-bounded chunks, each carrying
  a content anchor in M-072's sense, and a chunk edit
  applies only when its anchor still matches the
  chunk the file holds now. This module writes no
  file: the agent layer asks it before editing, so a
  refusal or a chunk plan always lands before any
  byte moves.

Honesty rules, enforced here and pinned by tests:

* **Binaries are never text-edited.** A NUL byte in
  the sniffed head, or bytes that are not valid
  UTF-8 text, classify a file as binary, with the
  reason named (the offset, or the decode failure).
  The refusal holds whatever the setting says - the
  gate governs large-file care, never this refusal.
* **Size guards explain themselves.** Every
  classification names the file's exact size and the
  exact limit it was judged against, and says which
  road applies and why. No guard refuses or reroutes
  in silence, and no limit is invented here: the
  whole-file limit is the 262,144 bytes the context
  producers already enforce, and the large mark is
  asset sight's 1,000,000 bytes.
* **Large text is edited by anchored chunks only.**
  Over the whole-file limit, the whole-file road
  closes and the chunk road opens: chunks split on
  line boundaries (a line is never cut in half; one
  over-long line forms its own chunk), each chunk
  anchored by the SHA-256 of its exact text. A chunk
  edit whose anchor no longer matches refuses,
  naming the anchor it expected and the anchor the
  file holds now, and changes nothing.
* **The setting is a gate, not a guess.** With
  ``large_file_care`` off, large files are not
  chunk-edited through the agent layer - the refusal
  says the care is off - while small text edits and
  the binary refusal are untouched, and the pure
  classification maths stays available. A malformed
  stored setting raises.
"""

from __future__ import annotations

__all__ = [
    "BINARY_SNIFF_BYTES",
    "CHUNK_TARGET_BYTES",
    "LARGE_FILE_BYTES",
    "LARGE_FILE_CARE_SLICE",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "SHORT_HASH_LEN",
    "USAGE",
    "WHOLE_FILE_LIMIT_BYTES",
    "Any",
    "BoolChange",
    "Chunk",
    "Dict",
    "EditAssessment",
    "FileCareRecord",
    "List",
    "Optional",
    "Tuple",
    "apply_chunk_edit",
    "assess_edit",
    "chunk_anchor",
    "classify_bytes",
    "classify_text",
    "detect_binary",
    "enabled_from_config",
    "format_chunk_plan",
    "format_file_care",
    "format_large_file_care",
    "format_setting_change",
    "parse_largefile_args",
    "set_enabled",
    "split_chunks",
]

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

LARGE_FILE_CARE_SLICE = "M-087"
SETTING_KEY = "large_file_care"
USAGE = "largefile <path>"
PLAIN_EXPLANATION = (
    "Big files are edited by anchored chunks, never "
    "whole; binaries are never text-edited; and every "
    "size guard says the file's size, the limit it "
    "crossed, and the road that applies - in plain "
    "words, before any byte moves.")
#: The whole-file limit the context producers already
#: enforce (repo map / symbol graph MAX_*_FILE_BYTES).
WHOLE_FILE_LIMIT_BYTES = 262_144
#: Asset sight's mark: at or over this, a file is large.
LARGE_FILE_BYTES = 1_000_000
#: How much of a file's head the binary sniff reads.
BINARY_SNIFF_BYTES = 8_192
#: A chunk grows to at least this many bytes before it
#: closes (line boundaries only; a longer line rides
#: whole in its own chunk).
CHUNK_TARGET_BYTES = 32_768
#: How many hex digits of an anchor a surface shows.
SHORT_HASH_LEN = 12


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


def detect_binary(data: Any) -> Optional[str]:
    """Why *data* is binary, or None when it is text.

    A NUL byte in the first BINARY_SNIFF_BYTES bytes
    is the codebase's standing mark of a binary (the
    context producers judge the same way); bytes that
    do not decode as UTF-8 are not text this editor
    may rewrite either. The reason names the evidence
    exactly - the NUL's offset, or the decode failure
    and its byte. An empty file is text.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError("file bytes must be bytes")
    raw = bytes(data)
    head = raw[:BINARY_SNIFF_BYTES]
    offset = head.find(b"\x00")
    if offset != -1:
        return (f"NUL byte at offset {offset} in the first "
                f"{BINARY_SNIFF_BYTES} bytes")
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return (f"not valid UTF-8 text (decode fails at "
                f"byte {exc.start}: {exc.reason})")
    return None


@dataclass(frozen=True)
class FileCareRecord:
    """One file's size/binary classification, as data."""

    path: str
    size_bytes: int
    is_binary: bool
    binary_reason: Optional[str]
    size_class: str
    edit_mode: str
    explanation: str

    def record(self) -> Dict[str, Any]:
        return {"type": "file_care", "slice": LARGE_FILE_CARE_SLICE,
                "path": self.path, "size_bytes": self.size_bytes,
                "is_binary": self.is_binary,
                "binary_reason": self.binary_reason,
                "size_class": self.size_class,
                "edit_mode": self.edit_mode,
                "explanation": self.explanation}


def classify_bytes(path: Any, data: Any) -> FileCareRecord:
    """Classify one file from its true bytes.

    The explanation is part of the verdict: it names
    the size, the guard judged against, and the road
    that applies, so no surface has to guess why.
    """
    clean = _validate_path(path)
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError("file bytes must be bytes")
    raw = bytes(data)
    size = len(raw)
    reason = detect_binary(raw)
    if reason is not None:
        explanation = (
            f"{clean} is binary ({reason}); binaries are "
            f"never text-edited. Its size is {size} bytes; "
            f"describe it or replace it whole through a "
            f"binary-aware road instead.")
        return FileCareRecord(
            path=clean, size_bytes=size, is_binary=True,
            binary_reason=reason, size_class="binary",
            edit_mode="refused", explanation=explanation)
    if size <= WHOLE_FILE_LIMIT_BYTES:
        explanation = (
            f"{clean} is {size} bytes of text, at or under "
            f"the whole-file limit of {WHOLE_FILE_LIMIT_BYTES} "
            f"bytes; the whole-file edit road applies.")
        return FileCareRecord(
            path=clean, size_bytes=size, is_binary=False,
            binary_reason=None, size_class="small",
            edit_mode="whole_file", explanation=explanation)
    large_note = (
        f" It is also at or over the large-file mark of "
        f"{LARGE_FILE_BYTES} bytes." if size >= LARGE_FILE_BYTES else "")
    explanation = (
        f"{clean} is {size} bytes of text, over the "
        f"whole-file limit of {WHOLE_FILE_LIMIT_BYTES} "
        f"bytes, so the whole-file road is closed; it is "
        f"edited by anchored chunks instead.{large_note}")
    return FileCareRecord(
        path=clean, size_bytes=size, is_binary=False,
        binary_reason=None, size_class="large",
        edit_mode="anchored_chunks", explanation=explanation)


def classify_text(path: Any, text: Any) -> FileCareRecord:
    """Classify one file from its text (UTF-8 bytes)."""
    if not isinstance(text, str):
        raise ValueError("file text must be a string")
    return classify_bytes(path, text.encode("utf-8"))


def chunk_anchor(text: str) -> str:
    """The full SHA-256 anchor of one chunk's exact text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Chunk:
    """One anchored chunk of a large file's text."""

    index: int
    start_line: int
    end_line: int
    anchor: str
    text: str

    def record(self) -> Dict[str, Any]:
        return {"index": self.index, "start_line": self.start_line,
                "end_line": self.end_line,
                "anchor": self.anchor[:SHORT_HASH_LEN],
                "bytes": len(self.text.encode("utf-8"))}


def split_chunks(text: Any) -> List[Chunk]:
    """Split *text* into anchored, line-bound chunks.

    Chunks close on line boundaries once they reach
    CHUNK_TARGET_BYTES; a line longer than the target
    forms its own chunk whole - a line is never cut.
    Line numbers are 1-based and contiguous. An empty
    text has no chunks.
    """
    if not isinstance(text, str):
        raise ValueError("file text must be a string")
    if text == "":
        return []
    lines = text.splitlines(keepends=True)
    chunks: List[Chunk] = []
    current: List[str] = []
    current_bytes = 0
    start_line = 1
    for number, line in enumerate(lines, 1):
        current.append(line)
        current_bytes += len(line.encode("utf-8"))
        if current_bytes >= CHUNK_TARGET_BYTES:
            body = "".join(current)
            chunks.append(Chunk(
                index=len(chunks), start_line=start_line,
                end_line=number, anchor=chunk_anchor(body),
                text=body))
            current = []
            current_bytes = 0
            start_line = number + 1
    if current:
        body = "".join(current)
        chunks.append(Chunk(
            index=len(chunks), start_line=start_line,
            end_line=len(lines), anchor=chunk_anchor(body),
            text=body))
    return chunks


def _check_anchor(given: Any, actual: str, index: int) -> None:
    if not isinstance(given, str):
        raise ValueError("anchor must be a string")
    candidate = given.strip().lower()
    if (len(candidate) < SHORT_HASH_LEN
            or any(c not in "0123456789abcdef" for c in candidate)):
        raise ValueError(
            f"anchor must be hex of at least {SHORT_HASH_LEN} "
            f"digits, got {given!r}")
    if not actual.startswith(candidate):
        raise ValueError(
            f"chunk {index} anchor mismatch: expected "
            f"{candidate[:SHORT_HASH_LEN]}, the file now holds "
            f"{actual[:SHORT_HASH_LEN]} - the chunk moved or "
            f"changed; nothing was written")


def apply_chunk_edit(text: Any, chunk_index: Any, anchor: Any,
                     replacement: Any) -> str:
    """Replace one anchored chunk, or refuse cleanly.

    The anchor is recomputed from the file's text as
    it stands now (M-072's law): a match applies the
    replacement to that chunk only; a mismatch names
    both anchors and changes nothing.
    """
    if not isinstance(text, str):
        raise ValueError("file text must be a string")
    if not isinstance(replacement, str):
        raise ValueError("replacement must be a string")
    chunks = split_chunks(text)
    if not isinstance(chunk_index, int) or isinstance(chunk_index, bool):
        raise ValueError("chunk index must be an integer")
    if chunk_index < 0 or chunk_index >= len(chunks):
        raise ValueError(
            f"chunk index {chunk_index} is out of range: the "
            f"file splits into {len(chunks)} chunk(s)")
    chunk = chunks[chunk_index]
    _check_anchor(anchor, chunk.anchor, chunk_index)
    parts = [c.text for c in chunks]
    parts[chunk_index] = replacement
    return "".join(parts)


@dataclass(frozen=True)
class EditAssessment:
    """One edit assessed against a file's care record."""

    path: str
    edit_mode: str
    allowed: bool
    warns: bool
    warning: Optional[str]

    def record(self) -> Dict[str, Any]:
        return {"type": "file_care_assessment",
                "slice": LARGE_FILE_CARE_SLICE, "path": self.path,
                "edit_mode": self.edit_mode, "allowed": self.allowed,
                "warns": self.warns, "warning": self.warning}


def assess_edit(record: FileCareRecord, *,
                config: Optional[Dict[str, Any]] = None) -> EditAssessment:
    """Assess one text edit against a care record.

    A binary refuses outright, whatever the gate
    says. A large text file allows the chunk road
    and warns onto it, naming the whole-file limit;
    with the gate off, the chunk road closes and the
    refusal says so. A small text file allows the
    whole-file road in silence - silence there is
    honest.
    """
    if record.is_binary:
        return EditAssessment(
            path=record.path, edit_mode="refused", allowed=False,
            warns=True, warning=record.explanation)
    if record.edit_mode == "anchored_chunks":
        enabled = True if config is None else enabled_from_config(config)
        if not enabled:
            return EditAssessment(
                path=record.path, edit_mode="refused", allowed=False,
                warns=True,
                warning=(f"{record.path} is {record.size_bytes} "
                         f"bytes, over the whole-file limit of "
                         f"{WHOLE_FILE_LIMIT_BYTES} bytes, and "
                         f"large-file care is off, so it is not "
                         f"edited here; turn large_file_care on "
                         f"to edit it by anchored chunks."))
        return EditAssessment(
            path=record.path, edit_mode="anchored_chunks",
            allowed=True, warns=True, warning=record.explanation)
    return EditAssessment(
        path=record.path, edit_mode=record.edit_mode,
        allowed=True, warns=False, warning=None)


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The large_file_care setting stored in *config*.

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
        return {"type": "large_file_care_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "large_file_care_setting_changed",
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
            f"large-file care is already "
            f"{'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The /largefile surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_largefile_args(args: str) -> Dict[str, Any]:
    """Parse the /largefile grammar both surfaces share.

    ``show`` / ``on`` / ``off`` steer the gate; one
    path word classifies that file; anything else is
    a usage error naming the grammar.
    """
    words = (args or "").split()
    if not words or words == ["show"]:
        return {"action": "show"}
    if words == ["on"]:
        return {"action": "on"}
    if words == ["off"]:
        return {"action": "off"}
    if len(words) == 1:
        return {"action": "check", "path": _validate_path(words[0])}
    raise ValueError(
        f"usage: {USAGE} (or: largefile show|on|off)")


def format_setting_change(record: Dict[str, Any]) -> str:
    state = "on" if record.get("to") else "off"
    return f"Large-file care is now {state}."


def format_file_care(record: Any) -> str:
    """Format one classification, dataclass or dict.

    The agent layer returns ``FileCareRecord.record()``
    dicts; both shapes format identically here, so the
    two roads never disagree about a file's care.
    """
    if isinstance(record, dict):
        return str(record.get("explanation") or "")
    return record.explanation


def format_chunk_plan(chunks: List[Chunk]) -> str:
    """The chunk plan of one large file, in plain words."""
    if not chunks:
        return "No chunks: the file is empty."
    lines = [f"{len(chunks)} anchored chunk(s):"]
    for chunk in chunks:
        lines.append(
            f"chunk {chunk.index}: lines {chunk.start_line}-"
            f"{chunk.end_line}, anchor "
            f"{chunk.anchor[:SHORT_HASH_LEN]}, "
            f"{len(chunk.text.encode('utf-8'))} bytes")
    return "\n".join(lines)


def format_large_file_care(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /largefile.

    Built from classify_bytes() / split_chunks(), so
    the show surface exercises the care road it names:
    a small file on the whole-file road, a large file
    on the chunk road, and a binary refused.
    """
    enabled = enabled_from_config(config)
    lines = ["Large-file and binary care (M-087) - "
             + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    lines.append("")
    small = classify_text("src/app.py", "x = 1\n")
    lines.append(format_file_care(small))
    large_text = "line\n" * 60_000
    large = classify_text("data/big.txt", large_text)
    lines.append(format_file_care(large))
    lines.append(format_chunk_plan(split_chunks(large_text)))
    binary = classify_bytes("img/logo.png",
                            b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
    lines.append(format_file_care(binary))
    lines.append("")
    lines.append("Usage: /largefile | /largefile on | "
                 "/largefile off | /largefile <path>")
    return "\n".join(lines)
