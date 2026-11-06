"""README and licence guardians (All-Features roadmap slice M-079).

Part IV — The Editor's Hand. The roadmap's words: the coder
*refuses* to overwrite a README (Volmarr's standing law) or
touch licence files without explicit word; the refusal is
built into the edit layer.

What already shipped, and what this slice adds:

* The edit layer already had strict judgement (M-071's format
  appliers, M-072's anchored appliers, M-073's repair loop,
  M-074's hunk review), and every one of those roads — plus
  the write_file / replace_file_content tool roads, the LSP
  workspace-edit road, the structural-rewrite road, and the
  formatter road — writes through one place:
  ``mythic_agent.core.edits.EditJournal``. Until this slice,
  nothing in that layer knew a README from any other file,
  or a licence file from any other file.
* This slice is the guardian at that layer: a pure judgement
  (this module — it writes no file) over the guarded names,
  enforced inside ``EditJournal.write`` itself, so every
  road that writes through the journal is guarded, and the
  agent layer classifies each apply by the operation it
  truly is before it reaches the journal.

The law, exactly:

* **A README is never overwritten.** Guarded names: a file
  whose basename is ``README`` or ``README.<anything>``
  (README.md, README.rst, readme.txt — case does not matter),
  at any depth in the workspace. A whole-file rewrite of an
  existing README — or a range/search edit whose target is
  the file's whole text, which is an overwrite wearing an
  in-place coat — refuses. So does deleting one.
* **Modifying a README in place is allowed.** A targeted
  replace, a partial anchored edit, a unified diff, a
  search-and-replace block, a reviewed hunk apply: these
  change the README where it stands and keep the rest of
  it — the campaign's own standing practice for READMEs
  (check what is there, then add and modify by hand, in
  place). Creating a README that does not exist yet is
  also allowed: it overwrites nothing.
* **Licence files are not touched at all without the
  user's explicit word.** Guarded names: a basename that
  is ``LICENSE``, ``LICENCE``, ``COPYING``, or ``NOTICE``,
  with any extension or suffix (LICENSE.md, LICENSE-MIT,
  LICENCE.txt, COPYING.LESSER, NOTICE.md). Create,
  overwrite, in-place edit, delete — every touch refuses.
* **The explicit word is a setting the user gives.**
  ``guardian_explicit_word`` (off by default) records it:
  ``/guardians word on`` gives the word, ``/guardians word
  off`` takes it back. With the word on record, the guarded
  operations above are allowed (and still journaled like
  any edit). The word is never inferred from a prompt, a
  file, or a model's say-so — only the setting carries it,
  and a malformed stored value raises, never defaults.
* **One exception rides with the standing law itself:**
  overwriting a README that is still a barely-anything
  stub (at most 5 non-empty lines and 200 characters — the
  starting-out stub the law names) is allowed, because
  there is nothing of the user's in it to lose. An empty
  file is a stub. The exception never extends to licence
  files.
* **A refusal changes nothing and says everything.** It
  names the file, the guard, the operation refused, and
  the road that lifts it. A no-change write (the new text
  is the old text) is not a touch and is not refused.
* **Undo is restoration, not an edit.** The journal's undo
  road restores the before-text of an edit the guardian
  already judged; it is not re-judged, so a guarded file's
  allowed in-place edits stay undoable.
"""

from __future__ import annotations

__all__ = [
    "GUARDED_KINDS",
    "GUARDIANS_SLICE",
    "LICENCE_STEMS",
    "OPERATIONS",
    "PLAIN_EXPLANATION",
    "SETTING_KEY",
    "STUB_MAX_CHARS",
    "STUB_MAX_LINES",
    "USAGE",
    "Any",
    "Dict",
    "GuardianRefusal",
    "GuardVerdict",
    "List",
    "Optional",
    "Tuple",
    "WordChange",
    "explicit_from_config",
    "format_guard_check",
    "format_guardians",
    "format_setting_change",
    "guard_kind",
    "guard_or_raise",
    "is_stub_readme",
    "judge",
    "parse_guardians_args",
    "set_explicit_word",
]

from dataclasses import dataclass
from pathlib import PurePath
from typing import Any, Dict, List, Optional, Tuple

#: The slice that owns this module.
GUARDIANS_SLICE = "M-079"

#: The config key the user's explicit word lives under.
SETTING_KEY = "guardian_explicit_word"

#: The guarded kinds, in the order they are judged.
GUARDED_KINDS: Tuple[str, ...] = ("readme", "licence")

#: The licence stems: a basename equal to one of these, or
#: carrying one as a prefix before '.', '-', or '_', is a
#: licence file (LICENSE, LICENSE-MIT, COPYING.LESSER...).
LICENCE_STEMS: Tuple[str, ...] = (
    "LICENSE", "LICENCE", "COPYING", "NOTICE")

#: Every operation the guardian judges. ``overwrite`` is a
#: whole-file rewrite (or an edit whose target is the whole
#: file); ``inplace`` changes part of a file where it stands.
OPERATIONS: Tuple[str, ...] = (
    "create", "overwrite", "inplace", "delete")

#: The barely-anything stub the standing law excepts: at
#: most this many non-empty lines and characters in total.
STUB_MAX_LINES = 5
STUB_MAX_CHARS = 200

#: The guardians explained in plain words — the sentence
#: every surface shows.
PLAIN_EXPLANATION = (
    "README and licence guardians: the coder refuses to "
    "overwrite a README — a whole-file rewrite of an "
    "existing README is refused, at any depth, whatever "
    "road the edit arrives by — and refuses to touch a "
    "licence file (LICENSE, LICENCE, COPYING, or NOTICE, "
    "with any extension or suffix) at all, unless the "
    "user has given their explicit word. Modifying a "
    "README in place — a targeted replace, a diff, a "
    "reviewed hunk — is allowed, because it changes the "
    "README where it stands and keeps the rest of it; "
    "creating a README that does not exist yet is allowed "
    "too, and so is overwriting a README that is still a "
    "barely-anything stub. The explicit word is the "
    "guardian_explicit_word setting: /guardians word on "
    "gives it, /guardians word off takes it back. A "
    "refusal changes nothing, and names the file, the "
    "guard, and the word that lifts it."
)

USAGE = ("Usage: /guardians, /guardians word on, "
         "/guardians word off, or /guardians check <path>")


def guard_kind(path: Any) -> Optional[str]:
    """The guard over *path*, from its basename alone.

    ``"readme"`` for README / README.<anything>,
    ``"licence"`` for a licence stem with any extension
    or suffix, ``None`` for anything else. Case never
    matters (readme.md and ReadMe.RST are READMEs), and
    the directory the file lives in never matters — the
    guard rides the name, at any depth.
    """
    name = PurePath(str(path).replace("\\", "/")).name.upper()
    if name == "README" or name.startswith("README."):
        return "readme"
    for stem in LICENCE_STEMS:
        if (name == stem or name.startswith(stem + ".")
                or name.startswith(stem + "-")
                or name.startswith(stem + "_")):
            return "licence"
    return None


def is_stub_readme(text: str) -> bool:
    """Is *text* the barely-anything stub the law excepts?

    An empty (or whitespace-only) file is a stub. Otherwise
    the text must hold at most STUB_MAX_LINES non-empty
    lines and at most STUB_MAX_CHARS characters in total
    once stripped — a title and a line or two, not a body
    of the user's work.
    """
    if not isinstance(text, str):
        raise ValueError("a README's text must be text")
    stripped = text.strip()
    if not stripped:
        return True
    lines = [line for line in stripped.splitlines() if line.strip()]
    return (len(lines) <= STUB_MAX_LINES
            and len(stripped) <= STUB_MAX_CHARS)


class GuardianRefusal(ValueError):
    """A guarded edit, refused. A ValueError, so every
    existing refusal road in the edit layer surfaces it
    unchanged; it carries the verdict that refused it."""

    def __init__(self, verdict: "GuardVerdict"):
        self.verdict = verdict
        super().__init__(verdict.refusal_text())


@dataclass(frozen=True)
class GuardVerdict:
    """One judged edit: the file, its guard, the operation,
    and whether the edit may proceed — with the plain-words
    reason either way."""

    path: str
    kind: Optional[str]
    operation: str
    allowed: bool
    explicit_word: bool
    reason: str

    def refusal_text(self) -> str:
        label = {"readme": "a README", "licence": "a licence file"}
        return (
            f"Guarded file refused: {self.path} is "
            f"{label.get(self.kind or '', 'a guarded file')} — "
            f"{self.reason}; nothing was changed. The user's "
            f"explicit word lifts this guard: /guardians word "
            f"on (setting {SETTING_KEY}).")

    def event(self) -> Dict[str, Any]:
        return {"type": "guardian_judged", "path": self.path,
                "kind": self.kind, "operation": self.operation,
                "allowed": self.allowed,
                "explicit_word": self.explicit_word}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {**self.event(), "reason": self.reason,
                "session_id": session_id, "journaled": journaled}


def judge(path: Any, operation: str, *, exists: bool = True,
          explicit_word: bool = False,
          current_text: Optional[str] = None) -> GuardVerdict:
    """Judge one edit against the guardians, purely.

    *operation* is one of OPERATIONS, classified by the
    road the edit arrives by (the agent layer classifies;
    the journal refuses an unclassified whole-file write
    to an existing file as an overwrite). *current_text*
    is the file's true current text, consulted only for
    the README stub exception.
    """
    shown = str(path)
    if operation not in OPERATIONS:
        raise ValueError(
            f"a guardian judges create, overwrite, inplace, "
            f"or delete; got {operation!r}")
    if not isinstance(explicit_word, bool):
        raise ValueError(
            f"the explicit word is given or not given; "
            f"got {explicit_word!r}")
    kind = guard_kind(shown)
    if kind is None:
        return GuardVerdict(
            shown, None, operation, True, explicit_word,
            "not a guarded file")
    if kind == "licence":
        if explicit_word:
            return GuardVerdict(
                shown, kind, operation, True, explicit_word,
                "the user's explicit word is on record, so "
                "this licence file may be touched")
        return GuardVerdict(
            shown, kind, operation, False, explicit_word,
            "licence files are not touched without the "
            "user's explicit word")
    # kind == "readme"
    if operation == "create":
        return GuardVerdict(
            shown, kind, operation, True, explicit_word,
            "creating a README overwrites nothing that "
            "already stands")
    if operation == "inplace":
        return GuardVerdict(
            shown, kind, operation, True, explicit_word,
            "an in-place edit modifies the README where it "
            "stands and keeps the rest of it")
    # overwrite or delete
    if explicit_word:
        return GuardVerdict(
            shown, kind, operation, True, explicit_word,
            "the user's explicit word is on record, so "
            "this README may be overwritten")
    if (operation == "overwrite" and current_text is not None
            and is_stub_readme(current_text)):
        return GuardVerdict(
            shown, kind, operation, True, explicit_word,
            "the README is still a barely-anything stub, "
            "the standing law's own exception")
    return GuardVerdict(
        shown, kind, operation, False, explicit_word,
        "a README is never overwritten (Volmarr's standing "
        "law) — edit it in place instead, or the user "
        "gives their explicit word")


def guard_or_raise(path: Any, operation: str, *, exists: bool = True,
                   explicit_word: bool = False,
                   current_text: Optional[str] = None
                   ) -> GuardVerdict:
    """Judge one edit and raise GuardianRefusal if refused.

    Returns the verdict when the edit may proceed, so the
    caller can record what was judged.
    """
    verdict = judge(path, operation, exists=exists,
                    explicit_word=explicit_word,
                    current_text=current_text)
    if not verdict.allowed:
        raise GuardianRefusal(verdict)
    return verdict


# ---------------------------------------------------------------------
# The explicit-word setting — off by default, validated, never guessed.
# ---------------------------------------------------------------------

def explicit_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """Has the user given their explicit word, per *config*?

    Absent means False — the word is never presumed. A
    stored value that is not a bool raises, never guessed
    at. This is a permission, not a gate: unlike the
    Part IV gates it ships OFF, because the standing law
    is the refusal and the word is the exception to it.
    """
    raw = (config or {}).get(SETTING_KEY, False)
    if not isinstance(raw, bool):
        raise ValueError(
            f"{SETTING_KEY} must be true or false, "
            f"got {type(raw).__name__}")
    return raw


@dataclass(frozen=True)
class WordChange:
    """A recorded change of the explicit-word setting."""

    before: bool
    after: bool

    def event(self) -> Dict[str, Any]:
        return {"type": "guardian_word_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "guardian_word_changed",
                "from": self.before, "to": self.after,
                "session_id": session_id, "journaled": journaled}


def set_explicit_word(config: Dict[str, Any],
                      given: Any) -> Tuple[bool, WordChange]:
    """Validate an explicit-word change against *config*."""
    if not isinstance(given, bool):
        raise ValueError(
            f"the explicit word is given or not given; "
            f"got {given!r}")
    before = explicit_from_config(config)
    if given == before:
        raise ValueError(
            f"the explicit word is already "
            f"{'given' if before else 'not given'}")
    return given, WordChange(before=before, after=given)


# ---------------------------------------------------------------------
# The /guardians surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------

def parse_guardians_args(args: str) -> Dict[str, Any]:
    """Parse ``/guardians`` arguments.

    /guardians            -> show
    /guardians word on    -> give the explicit word
    /guardians word off   -> take the explicit word back
    /guardians check <p>  -> judge a path, every operation
    """
    text = (args or "").strip()
    if not text:
        return {"action": "show"}
    if text == "word on":
        return {"action": "setting", "enabled": True}
    if text == "word off":
        return {"action": "setting", "enabled": False}
    if text.startswith("check ") and text[6:].strip():
        return {"action": "check", "path": text[6:].strip()}
    raise ValueError(USAGE)


def format_setting_change(record: Dict[str, Any]) -> str:
    """An explicit-word change record, in plain words."""
    word = {True: "given", False: "not given"}
    return (f"Guardian explicit word: {word[record['from']]} "
            f"-> {word[record['to']]}.")


def _verdict_line(verdict: GuardVerdict) -> str:
    mark = "allowed" if verdict.allowed else "REFUSED"
    return (f"  {verdict.operation}: {mark} — {verdict.reason}")


def format_guard_check(config: Dict[str, Any], path: str) -> str:
    """One path judged under every operation, in plain words."""
    kind = guard_kind(path)
    word = explicit_from_config(config)
    lines = [f"Guardian check — {path}:"]
    lines.append(
        f"Guard: {kind if kind else 'none'}; explicit word: "
        f"{'given' if word else 'not given'} ({SETTING_KEY}).")
    for operation in OPERATIONS:
        lines.append(_verdict_line(judge(
            path, operation, explicit_word=word)))
    if kind == "readme":
        lines.append(
            "Note: an overwrite of a README that is still a "
            "barely-anything stub is allowed without the "
            "word; the check cannot see the file's text, so "
            "it judges the standing text case.")
    return "\n".join(lines)


_REAL_README = (
    "# The Longhouse\n\nA real README the user wrote and "
    "kept, with sections, history, and hard-won words — "
    "far past any stub, and exactly what the standing "
    "law protects from being overwritten by a coder who "
    "did not read it first.\n")


def format_guardians(config: Dict[str, Any]) -> str:
    """The whole slice, in plain words, for /guardians.

    Built from guard_kind() / judge() / is_stub_readme()
    / format_guard_check(), so every public road this
    module offers is exercised by its own show surface:
    a real README's overwrite refused while its in-place
    edit is allowed, a stub's overwrite allowed, a licence
    file refused at every operation, and an ordinary file
    judged free.
    """
    word = explicit_from_config(config)
    lines = ["README and licence guardians (M-079) — "
             + PLAIN_EXPLANATION, ""]
    lines.append(f"Explicit word: {'given' if word else 'not given'} "
                 f"({SETTING_KEY}).")
    lines.append("")
    lines.append("The guarded names, judged by basename:")
    for sample in ("README.md", "docs/guide/README.rst",
                   "LICENSE", "LICENSE-MIT", "LICENCE.txt",
                   "COPYING.LESSER", "NOTICE.md", "src/app.py"):
        lines.append(f"  {sample}: {guard_kind(sample) or 'unguarded'}")
    lines.append("")
    refused = judge("README.md", "overwrite",
                    current_text=_REAL_README)
    lines.append(
        f"Overwrite the sample README ("
        f"{len(_REAL_README.strip().splitlines())} lines of "
        f"real text): {'allowed' if refused.allowed else 'REFUSED'} "
        f"— {refused.reason}.")
    inplace = judge("README.md", "inplace",
                    current_text=_REAL_README)
    lines.append(
        f"Edit that same README in place: "
        f"{'allowed' if inplace.allowed else 'REFUSED'} — "
        f"{inplace.reason}.")
    stub = "# New Project\n\nTODO: write this.\n"
    lines.append(
        f"The sample stub {stub.splitlines()[0]!r} "
        f"({len(stub.strip().splitlines())} lines) is a stub: "
        f"{is_stub_readme(stub)} — overwriting it is "
        f"{'allowed' if judge('README.md', 'overwrite', current_text=stub).allowed else 'REFUSED'}.")
    licence = judge("LICENSE", "inplace")
    lines.append(
        f"Touch LICENSE in place: "
        f"{'allowed' if licence.allowed else 'REFUSED'} — "
        f"{licence.reason}.")
    lines.append("")
    lines.append(format_guard_check(config, "README.md"))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)
