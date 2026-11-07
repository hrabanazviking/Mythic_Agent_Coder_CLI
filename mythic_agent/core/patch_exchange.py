"""Patch export/import (roadmap slice M-089).

Part IV - The Editor's Hand. The roadmap's words: a
change set as a portable patch file with its evidence
header - the hand-off format between machines and
between agents.

What already shipped, and what this slice adds:

* M-084 (``core/change_sets.py``): a change set is a
  named, reviewable unit across files - one edit per
  file in an M-071 concrete format, each file decided
  accept or reject on its own, the whole set judged in
  memory through M-071's unchanged strict appliers, and
  its test evidence carried as data. A change set lived
  only inside one session on one machine: there was no
  way to hand the reviewed set - name, edits, decisions
  and evidence together - to another machine or another
  agent and have it land there with the same strictness.
* This slice is that hand-off format. Export writes one
  portable text file: a magic line, a checksummed JSON
  evidence header (the set's name, its evidence record
  or an honest none, the accepted files with their
  formats, byte counts and SHA-256 payload anchors, and
  the rejected files named as rejected - never silently
  dropped), then each accepted edit's payload carried
  byte-exact under a length-headed section. Import
  parses the file back, proves every checksum and
  anchor before trusting a single payload, rebuilds the
  change set through M-084's own roads (so every
  M-084/M-071 rule still holds), and plans it through
  M-084's ``apply_change_set`` unchanged - one stale
  file on the receiving tree refuses the whole import
  and nothing is planned. This module writes no file:
  it works on patch text and in-memory trees; the agent
  layer owns the real files and the session events.

Honesty rules, enforced here and pinned by tests:

* **Only a fully decided set exports.** A file still
  pending refuses the export and is named - a patch
  file never carries an undecided file as if decided.
* **Rejected files are named, never hidden.** They
  carry no payload and can never land, but the header
  lists them as rejected so the receiver sees the whole
  review, not just the part that travelled.
* **Evidence is a header, never decoration.** The
  set's evidence record rides the header verbatim,
  verdict computed by M-084 from its counts; a set
  with no evidence exports with evidence recorded as
  none, and the import says so plainly.
* **Nothing is trusted before it is proven.** The
  header checksum, every payload's byte count and
  SHA-256 anchor, the magic line and the format
  version are all verified at parse time; any mismatch
  refuses the whole file and names the failure. Bytes
  after the last section refuse - a patch file is
  exactly its sections, nothing smuggled behind them.
* **No fuzz, ever, on either side.** Export takes the
  set as decided; import judges through M-071's strict
  appliers unchanged, via M-084's planner.
* **The setting is a gate, not a guess.** With
  ``patch_exchange`` off, exports and imports through
  the agent layer refuse and say so; the pure format
  maths stays available. A malformed stored setting
  raises, never defaults silently.
"""

from __future__ import annotations

__all__ = [
    "MAGIC",
    "PATCH_EXCHANGE_SLICE",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "USAGE",
    "Any",
    "BoolChange",
    "ChangeSet",
    "Dict",
    "List",
    "Optional",
    "PatchFile",
    "Tuple",
    "enabled_from_config",
    "export_patch",
    "format_patch",
    "format_patch_exchange",
    "format_setting_change",
    "import_patch",
    "parse_patch_args",
    "parse_patch",
    "set_enabled",
]

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .change_sets import (
    ChangeSet,
    attach_evidence,
    decide,
    make_edit,
    make_evidence,
    start_change_set,
)
from .change_sets import apply_change_set as _plan_change_set

#: The slice that owns this module.
PATCH_EXCHANGE_SLICE = "M-089"

#: The config key the patch-exchange gate lives under.
SETTING_KEY = "patch_exchange"

#: First line of every patch file, with its version.
MAGIC = "MYTHIC-PATCH/1"

#: The setting explained in plain words.
PLAIN_EXPLANATION = (
    "Patch export/import: a reviewed change set (M-084) "
    "becomes one portable patch file that can travel "
    "between machines and between agents. The file opens "
    "with its evidence header - the set's name, the test "
    "evidence record (or an honest none when no evidence "
    "was attached), every accepted file with its edit "
    "format, byte count and content anchor, and every "
    "rejected file named as rejected - sealed with a "
    "checksum. Each accepted edit's payload then rides "
    "byte-exact under its own length head. Import proves "
    "the checksum and every anchor before trusting a "
    "payload, rebuilds the set through the change-set "
    "roads, and judges it against the receiving tree "
    "through the same strict appliers as any edit (exact "
    "matches only, no fuzz, ever): one stale file refuses "
    "the whole import and nothing is written. Only a "
    "fully decided set can be exported - an undecided "
    "file refuses and is named."
)

USAGE = "Usage: /patch, /patch on, or /patch off"


def _anchor(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical(record: Dict[str, Any]) -> str:
    return json.dumps(record, sort_keys=True,
                      separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class PatchFile:
    """A parsed patch file: header truth + payloads.

    ``edits`` are the accepted files, in header order;
    ``rejected`` names the files the review rejected -
    they carry no payload and never land. ``evidence``
    is the M-084 evidence record dict, or None when the
    set carried none (recorded as none, never a pass).
    """

    name: str
    evidence: Optional[Dict[str, Any]]
    edits: Tuple[Any, ...]
    rejected: Tuple[str, ...]

    @property
    def file_count(self) -> int:
        return len(self.edits)

    def change_set(self) -> ChangeSet:
        """Rebuild the set through M-084's own roads."""
        result = start_change_set(self.name, list(self.edits))
        for index in range(len(self.edits)):
            result = decide(result, index, "accept")
        if self.evidence is not None:
            ev = self.evidence
            result = attach_evidence(result, make_evidence(
                ev["command"], ev["passed"], ev["failed"],
                ev.get("skipped", 0), ev.get("log_ref", "")))
        return result

    def record(self) -> Dict[str, Any]:
        return {"type": "patch_file", "slice": PATCH_EXCHANGE_SLICE,
                "name": self.name, "evidence": self.evidence,
                "files": [edit.path for edit in self.edits],
                "rejected": list(self.rejected)}


def export_patch(change_set: ChangeSet) -> str:
    """Write *change_set* as one portable patch text.

    The set must be fully decided: a pending file
    refuses and is named. Rejected files are listed in
    the header by path and carry no payload. Accepted
    payloads ride byte-exact (length-headed, in the
    set's own order), each named in the header with its
    format, UTF-8 byte count and SHA-256 anchor.
    """
    if not isinstance(change_set, ChangeSet):
        raise ValueError(
            "a patch is exported from a change set built "
            f"by the change-set road; got {change_set!r}")
    pending = change_set.undecided()
    if pending:
        names = ", ".join(
            f"{i} ({change_set.edits[i].path})" for i in pending)
        raise ValueError(
            f"file(s) {names} in change set "
            f"{change_set.name!r} are not decided yet - a "
            "patch file only carries a finished review; "
            "nothing was exported")
    accepted = []
    rejected: List[str] = []
    for edit, decision in zip(change_set.edits,
                              change_set.decisions):
        if decision == "reject":
            rejected.append(edit.path)
        else:
            accepted.append(edit)
    if not accepted:
        raise ValueError(
            f"change set {change_set.name!r} has every "
            "file rejected - there is no change to carry; "
            "nothing was exported")
    files = []
    sections = []
    for edit in accepted:
        raw = edit.payload.encode("utf-8")
        files.append({"path": edit.path, "format": edit.format_id,
                      "bytes": len(raw), "anchor": _anchor(edit.payload)})
        head = json.dumps(
            {"path": edit.path, "format": edit.format_id,
             "bytes": len(raw)}, sort_keys=True,
            separators=(",", ":"), ensure_ascii=False)
        sections.append(head + "\n" + edit.payload)
    header: Dict[str, Any] = {
        "type": "patch_header", "slice": PATCH_EXCHANGE_SLICE,
        "name": change_set.name,
        "evidence": (change_set.evidence.record()
                     if change_set.evidence is not None else None),
        "files": files, "rejected": rejected}
    sealed = dict(header)
    sealed["checksum"] = _anchor(_canonical(header))
    lines = [MAGIC, json.dumps(sealed, sort_keys=True,
                               separators=(",", ":"),
                               ensure_ascii=False)]
    lines.extend(sections)
    return "\n".join(lines) + "\n"


def parse_patch(text: Any) -> PatchFile:
    """Parse and prove a patch text before trusting it.

    Every proof runs here: the magic line, the header
    checksum, each section head against the header, each
    payload's byte count and anchor, and no bytes after
    the last section. Any failure refuses the whole
    file, naming the failure.
    """
    if not isinstance(text, str):
        raise ValueError("patch text must be a string")
    if not text.startswith(MAGIC + "\n"):
        raise ValueError(
            "this is not a patch file - its first line "
            f"must be {MAGIC}")
    rest = text[len(MAGIC) + 1:]
    head_line, _, body = rest.partition("\n")
    try:
        sealed = json.loads(head_line)
    except ValueError as exc:
        raise ValueError(
            f"the patch header does not parse - {exc}") from exc
    if not isinstance(sealed, dict) or \
            sealed.get("type") != "patch_header":
        raise ValueError("the patch header is not a patch header")
    checksum = sealed.pop("checksum", None)
    if checksum != _anchor(_canonical(sealed)):
        raise ValueError(
            "the patch header checksum does not match - "
            "the header was changed after export; nothing "
            "was trusted")
    if sealed.get("slice") != PATCH_EXCHANGE_SLICE:
        raise ValueError(
            f"the patch header names slice "
            f"{sealed.get('slice')!r}, not {PATCH_EXCHANGE_SLICE}")
    name = sealed.get("name")
    files = sealed.get("files")
    rejected = sealed.get("rejected")
    evidence = sealed.get("evidence")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("the patch header names no change set")
    if not isinstance(files, list) or not files:
        raise ValueError("the patch header lists no files")
    if not isinstance(rejected, list) or \
            not all(isinstance(p, str) for p in rejected):
        raise ValueError("the patch header's rejected list is wrong")
    if evidence is not None and not isinstance(evidence, dict):
        raise ValueError("the patch header's evidence is wrong")
    edits = []
    pos = 0
    for meta in files:
        if not isinstance(meta, dict):
            raise ValueError("a patch header file entry is wrong")
        head, sep, tail = body[pos:].partition("\n")
        if not sep:
            raise ValueError(
                f"the patch file ends before the section "
                f"for {meta.get('path')!r}")
        try:
            section = json.loads(head)
        except ValueError as exc:
            raise ValueError(
                f"a patch section head does not parse - {exc}"
            ) from exc
        if section.get("path") != meta.get("path") or \
                section.get("format") != meta.get("format") or \
                section.get("bytes") != meta.get("bytes"):
            raise ValueError(
                f"the section for {meta.get('path')!r} does "
                "not match the header - nothing was trusted")
        start = pos + len(head) + 1
        payload_bytes = body[start:].encode("utf-8")
        raw = payload_bytes[:meta["bytes"]]
        if len(raw) != meta["bytes"]:
            raise ValueError(
                f"the payload for {meta['path']} is cut "
                "short - nothing was trusted")
        try:
            payload = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(
                f"the payload for {meta['path']} is not "
                f"valid text at its stated length - {exc}"
            ) from exc
        if _anchor(payload) != meta.get("anchor"):
            raise ValueError(
                f"the payload for {meta['path']} does not "
                "match its header anchor - it was changed "
                "after export; nothing was trusted")
        edits.append(make_edit(meta["path"], meta["format"], payload))
        pos = start + len(payload)
        if body[pos:pos + 1] == "\n":
            pos += 1
    if body[pos:].strip():
        raise ValueError(
            "the patch file carries bytes after its last "
            "section - nothing was trusted")
    return PatchFile(name=name, evidence=evidence,
                     edits=tuple(edits), rejected=tuple(rejected))


def import_patch(text: Any, currents: Mapping[str, Any]
                 ) -> Tuple[Dict[str, str], Any]:
    """Plan a patch against the receiving tree.

    Parses (with every proof), rebuilds the set through
    M-084, and plans it through M-084's planner
    unchanged: returns (new texts by path, outcome) - a
    plan, never a write. One stale file refuses the
    whole import.
    """
    patch = parse_patch(text)
    return _plan_change_set(patch.change_set(), currents)


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The patch_exchange setting stored in *config*.

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
        return {"type": "patch_exchange_setting_changed",
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
            f"patch exchange is already "
            f"{'on' if before else 'off'}")
    return enabled, BoolChange(before=before, after=enabled)


def parse_patch_args(args: str) -> Dict[str, Any]:
    """Parse the /patch grammar both surfaces share.

    ``show`` / ``on`` / ``off`` stand alone; ``export``
    takes the change set's name as the rest of the line
    (names are free text); ``import`` takes the patch
    reference as the rest of the line.
    """
    text = (args or "").strip()
    if not text or text == "show":
        return {"action": "show"}
    if text == "on":
        return {"action": "on"}
    if text == "off":
        return {"action": "off"}
    parts = text.split(None, 1)
    if parts[0] == "export" and len(parts) == 2 and parts[1].strip():
        return {"action": "export", "name": parts[1].strip()}
    if parts[0] == "import" and len(parts) == 2 and parts[1].strip():
        return {"action": "import", "ref": parts[1].strip()}
    raise ValueError(
        f"usage: {USAGE} (or: patch export <set name>, "
        "patch import <patch file>)")


def format_setting_change(record: Dict[str, Any]) -> str:
    state = "on" if record.get("to") else "off"
    return f"Patch exchange is now {state}."


def format_patch(patch: Any) -> str:
    """Format one patch file (PatchFile or its record)."""
    if isinstance(patch, dict):
        name = patch.get("name")
        files = patch.get("files") or []
        rejected = patch.get("rejected") or []
        evidence = patch.get("evidence")
        lines = [f"Patch {name!r}: {len(files)} file(s)"]
        lines.extend(f"  {p}" for p in files)
    else:
        lines = [f"Patch {patch.name!r}: {patch.file_count} file(s)"]
        for edit in patch.edits:
            lines.append(
                f"  {edit.path} ({edit.format_id}, "
                f"anchor {_anchor(edit.payload)[:12]})")
        rejected = list(patch.rejected)
        evidence = patch.evidence
    if rejected:
        lines.append("  rejected in review, not carried: "
                     + ", ".join(rejected))
    if evidence is None:
        lines.append("  evidence: none attached - no test "
                     "evidence travelled with this patch")
    else:
        lines.append(
            f"  evidence: {evidence.get('verdict')} - "
            f"{evidence.get('passed')} passed, "
            f"{evidence.get('failed')} failed, "
            f"{evidence.get('skipped')} skipped "
            f"({evidence.get('command')})")
    return "\n".join(lines)


def format_patch_exchange(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /patch.

    Built from export_patch() / parse_patch() /
    import_patch(), so the show surface exercises the
    road it names: a decided set exports, the patch
    parses back proven, and it plans whole against a
    receiving tree.
    """
    enabled = enabled_from_config(config)
    lines = ["Patch export/import (M-089) - "
             + PLAIN_EXPLANATION, ""]
    lines.append(f"Setting: {'on' if enabled else 'off'} "
                 f"({SETTING_KEY}).")
    lines.append("")
    change = make_edit("src/app.py", "whole-file", "x = 2\n")
    change_set = decide(start_change_set("demo fix", [change]),
                        0, "accept")
    change_set = attach_evidence(change_set, make_evidence(
        "pytest -q", 12, 0, 1, "logs/demo.log"))
    text = export_patch(change_set)
    patch = parse_patch(text)
    lines.append(format_patch(patch))
    planned, outcome = import_patch(text, {"src/app.py": "x = 1\n"})
    lines.append("Plans whole on the receiving tree: "
                 + ", ".join(sorted(planned)) + ".")
    lines.append("")
    lines.append("Usage: /patch | /patch on | /patch off | "
                 "/patch export <set name> | "
                 "/patch import <patch file>")
    return "\n".join(lines)
