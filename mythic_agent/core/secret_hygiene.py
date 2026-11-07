"""Secret hygiene in action (All-Features roadmap slice M-110).

Part V - Autonomy & Safety. The roadmap's words:
``the coder never echoes secrets, redacts known key
shapes from outputs and logs, and refuses to commit
files matching secret patterns (with the file named,
content never shown).``

What already shipped, and what this slice adds:

* The tree already scans text for credential shapes
  (``mythic_agent/core/secrets_audit.py``:
  ``scan_secrets`` finds credential-like spans by
  kind and ``mask_text`` replaces them) and already
  masks configured credentials, URL credentials and
  detected secrets on the logging / export road
  (``mythic_agent/core/redaction.py``:
  ``redact_text``, ``SecretRedactor``,
  ``protect_logging``). Keys themselves live in
  Kista, never in config (``key_custody.py``,
  M-032), and the mass-edit guard already treats
  ``.env`` / credential / key paths as sensitive
  (``mass_edit_guard.py``). The auto-commit road
  (``auto_commit.py``, M-078) judges branch, message
  and file set - but nothing in the tree holds
  hygiene as validated session data, and no road
  screens a file for commit by secret shape.
* This slice is that missing hygiene layer, as a
  pure layer in the exact sibling shape: the known
  secret shapes held as validated data, a redaction
  function built on the shipped scanner, a
  file-screening judge that names the file and the
  pattern kinds only, a refusal record shaped as
  session news, and a small in-memory registry
  model with deterministic ids. This module writes
  no file, runs no subprocess, changes no setting
  and imports no agent / UI code; the agent layer
  owns holding the registry for a session, feeding
  outputs and logs through the redaction road, and
  screening files on the real commit road.

Honesty rules, enforced here and pinned by tests:

* **A secret is never echoed.** Redaction replaces
  a matched span with one fixed marker; a screening
  verdict, a record and every formatter name the
  file and the pattern kinds only - never the
  content, never a fragment of it, not even the
  masked head-and-tail preview the audit scanner
  carries for its own reports.
* **The shapes are mechanical, never guessed.**
  A text shape is one the shipped scanner defines,
  a ``.env``-style assignment is a line naming a
  secret word (key / token / secret / password /
  credential) with a value of eight or more
  characters, and a file shape is a filename the
  tree already treats as sensitive. A named
  assignment with a placeholder value may still be
  flagged - for a commit refusal that is the safe
  direction, and it is stated here, not hidden.
* **The vocabularies are closed.** A pattern kind
  is one of the named kinds and a screening status
  one of the named statuses. Any other word
  refuses plainly instead of being guessed at.
* **A verdict never disagrees with itself.** A
  screening is refused exactly when it carries at
  least one kind, and clean exactly when it
  carries none; a screening built with a status
  that contradicts its kinds refuses.
* **Status is never carried by colour or symbol
  alone.** Every formatter states a screening's
  status and kinds in words.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Optional, Tuple

from .secrets_audit import scan_secrets

__all__ = [
    "PLAIN_EXPLANATION",
    "REDACTION_MARKER",
    "SECRET_HYGIENE_SLICE",
    "SECRET_KINDS",
    "SECRET_PATTERNS",
    "SCREENING_STATUSES",
    "USAGE",
    "FileScreening",
    "HygieneRegistry",
    "Screening",
    "SecretPattern",
    "build_pattern",
    "build_screening",
    "filename_kinds",
    "format_hygiene_record",
    "format_pattern",
    "format_patterns",
    "format_record",
    "format_screening",
    "format_screenings",
    "format_secrets_screen",
    "hygiene_record",
    "normalize_hygiene_id",
    "normalize_pattern_basis",
    "normalize_secret_kind",
    "normalize_screening_status",
    "parse_secrets_args",
    "pattern_for_kind",
    "redact_secrets",
    "screen_file",
    "secret_kinds_in",
    "validate_pattern",
    "validate_screening",
]

SECRET_HYGIENE_SLICE = "M-110"

#: The one fixed marker a redacted secret is
#: replaced with. It names no part of the secret.
REDACTION_MARKER = "[REDACTED]"

#: The secret pattern kinds, in a fixed order:
#: the provider and token shapes the shipped
#: scanner defines, then the assignment shape and
#: the filename shape this slice adds.
SECRET_KINDS = (
    "openai_key", "anthropic_key", "github_token",
    "aws_access_key", "aws_secret_key", "stripe_key",
    "slack_token", "google_api_key", "xai_key",
    "bearer_token", "url_credentials", "private_key",
    "generic_secret", "env_assignment", "secret_file",
)

#: The screening statuses: a file is clean, or its
#: commit is refused. No third word exists.
SCREENING_STATUSES = ("clean", "refused")

PLAIN_EXPLANATION = (
    "Secret hygiene: the coder never echoes a "
    "secret. Known key and token shapes in outputs "
    "and logs are replaced with one fixed marker, "
    "and a file whose name or text matches a secret "
    "pattern is refused for commit - the verdict "
    "names the file and the pattern kinds only, and "
    "the content is never shown. This layer holds "
    "the shapes, the redaction and the screenings "
    "as data only; it writes no file, runs no "
    "command and changes no setting itself - the "
    "agent layer feeds real outputs through it and "
    "screens files on the real commit road."
)

USAGE = (
    "Usage: /secrets, /secrets show, "
    "/secrets show <screening>, "
    "/secrets check <file>"
)

_KIND_LABELS = {
    "openai_key": "OpenAI-style API key",
    "anthropic_key": "Anthropic-style API key",
    "github_token": "GitHub token",
    "aws_access_key": "AWS access key",
    "aws_secret_key": "AWS secret key",
    "stripe_key": "Stripe key",
    "slack_token": "Slack token",
    "google_api_key": "Google API key",
    "xai_key": "xAI API key",
    "bearer_token": "bearer token",
    "url_credentials": "credentials in a URL",
    "private_key": "private key header",
    "generic_secret": "named secret assignment",
    "env_assignment": ".env-style secret assignment",
    "secret_file": "secret file name",
}

_KIND_BASES = {
    kind: "text" for kind in SECRET_KINDS
}
_KIND_BASES["secret_file"] = "filename"

_KIND_WORDS = {
    "openai_key": "openai_key", "openai": "openai_key",
    "anthropic_key": "anthropic_key",
    "anthropic": "anthropic_key",
    "github_token": "github_token", "github": "github_token",
    "github_pat": "github_token",
    "aws_access_key": "aws_access_key",
    "aws_access": "aws_access_key",
    "aws_secret_key": "aws_secret_key",
    "aws_secret": "aws_secret_key",
    "stripe_key": "stripe_key", "stripe": "stripe_key",
    "slack_token": "slack_token", "slack": "slack_token",
    "google_api_key": "google_api_key",
    "google": "google_api_key",
    "xai_key": "xai_key", "xai": "xai_key",
    "bearer_token": "bearer_token", "bearer": "bearer_token",
    "url_credentials": "url_credentials",
    "url": "url_credentials",
    "private_key": "private_key", "private": "private_key",
    "generic_secret": "generic_secret",
    "generic": "generic_secret",
    "env_assignment": "env_assignment", "env": "env_assignment",
    "dotenv": "env_assignment",
    "secret_file": "secret_file", "file": "secret_file",
    "filename": "secret_file",
}

_STATUS_WORDS = {
    "clean": "clean", "clear": "clean", "ok": "clean",
    "safe": "clean", "passed": "clean",
    "refused": "refused", "blocked": "refused",
    "denied": "refused", "rejected": "refused",
}

_BASIS_WORDS = {
    "text": "text", "content": "text",
    "filename": "filename", "name": "filename",
    "file": "filename",
}

_SCREENING_KEYS = frozenset({
    "screening_id", "id", "filename", "file", "path", "name",
    "kinds", "kind", "patterns", "pattern",
    "status", "verdict", "result",
})

_PATTERN_KEYS = frozenset({"kind", "label", "basis"})

_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_.")

#: A .env-style assignment: a line naming a secret
#: word, an equals sign, and a value of eight or
#: more non-space characters. The value is group 2;
#: only its span is ever used, never its text.
_ENV_ASSIGNMENT = re.compile(
    r"(?m)^[ \t]*(?:export[ \t]+)?"
    r"([A-Za-z_][A-Za-z0-9_]*"
    r"(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL)"
    r"[A-Za-z0-9_]*)[ \t]*=[ \t]*[\"']?([^\s\"']{8,})")

#: File names the tree already treats as carrying
#: secrets (the mass-edit guard's sensitive names,
#: widened with the common key-file endings).
_SECRET_BASENAMES = frozenset({
    ".env", "credentials", "id_rsa", "id_dsa",
    "id_ecdsa", "id_ed25519",
})
_SECRET_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".kdbx")


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
                f"a secret record names two different {what}")
    return first


def normalize_hygiene_id(value: Any) -> str:
    """The canonical screening id a word names.

    A screening id is one word of letters, digits,
    dashes, underscores and dots, read with its
    case kept. Anything else raises.
    """
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and all(ch in _ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"a screening id must be a non-empty word of letters, "
        f"digits, dashes, underscores and dots, got {value!r}")


def normalize_secret_kind(value: Any) -> str:
    """The canonical secret pattern kind a word names.

    Reads every kind in SECRET_KINDS plus its short
    spellings (``openai``, ``github``, ``bearer``,
    ``env``, ``file`` and kin), case-insensitively,
    with dashes and spaces read as underscores.
    Any other word refuses: the kinds are a closed
    vocabulary.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace(
            "-", "_").replace(" ", "_")
        if wanted in _KIND_WORDS:
            return _KIND_WORDS[wanted]
    raise ValueError(
        "a secret kind must be one of %s, got %r"
        % ("/".join(SECRET_KINDS), value))


def normalize_screening_status(value: Any) -> str:
    """The canonical screening status a word names.

    Reads ``clean`` (or ``clear`` / ``ok``) and
    ``refused`` (or ``blocked`` / ``denied``),
    case-insensitively. Any other word refuses:
    the statuses are a closed vocabulary.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace(
            "-", "_").replace(" ", "_")
        if wanted in _STATUS_WORDS:
            return _STATUS_WORDS[wanted]
    raise ValueError(
        "a screening status must be one of %s, got %r"
        % ("/".join(SCREENING_STATUSES), value))


def normalize_pattern_basis(value: Any) -> str:
    """The canonical pattern basis a word names.

    A shape is matched against a file's ``text``
    (or ``content``) or against its ``filename``
    (or ``name``). Any other word refuses.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace(
            "-", "_").replace(" ", "_")
        if wanted in _BASIS_WORDS:
            return _BASIS_WORDS[wanted]
    raise ValueError(
        "a pattern basis must be text or filename, "
        f"got {value!r}")


def _ordered_kinds(kinds: Any) -> Tuple[str, ...]:
    """Kind words normalised, deduplicated, in kind order."""
    if kinds is None:
        return ()
    if isinstance(kinds, str):
        kinds = (kinds,)
    if not isinstance(kinds, (list, tuple)):
        raise ValueError(
            f"secret kinds must be a list of kind words, "
            f"got {kinds!r}")
    named = {normalize_secret_kind(kind) for kind in kinds}
    return tuple(kind for kind in SECRET_KINDS if kind in named)


# ---------------------------------------------------------------------
# The shapes: the known secret patterns, as validated data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SecretPattern:
    """One known secret shape, as data.

    ``kind`` names the shape in the closed
    vocabulary, ``label`` says it in plain words,
    and ``basis`` names what the shape is matched
    against - a file's text, or its filename.
    Constructing one validates it.
    """

    kind: str
    label: str
    basis: str = "text"

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind", normalize_secret_kind(self.kind))
        object.__setattr__(
            self, "label", _clean_text(self.label, "a label"))
        object.__setattr__(
            self, "basis", normalize_pattern_basis(self.basis))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "secret_pattern",
            "slice": SECRET_HYGIENE_SLICE,
            "kind": self.kind,
            "label": self.label,
            "basis": self.basis,
        }


#: Every known shape, as data, in kind order. The
#: text shapes are the shipped scanner's shapes;
#: the assignment and filename shapes are this
#: slice's mechanical additions, named above.
SECRET_PATTERNS: Tuple[SecretPattern, ...] = tuple(
    SecretPattern(
        kind=kind, label=_KIND_LABELS[kind],
        basis=_KIND_BASES[kind])
    for kind in SECRET_KINDS)


def pattern_for_kind(kind: Any) -> SecretPattern:
    """The one held pattern a kind word names."""
    wanted = normalize_secret_kind(kind)
    for pattern in SECRET_PATTERNS:
        if pattern.kind == wanted:
            return pattern
    raise ValueError(f"unknown secret kind: {wanted!r}")


def validate_pattern(pattern: Any) -> SecretPattern:
    """Validate one secret pattern into a SecretPattern.

    Accepts a SecretPattern or a mapping naming a
    ``kind`` and a ``label``, and optionally a
    ``basis``. Unknown keys refuse.
    """
    if isinstance(pattern, SecretPattern):
        return pattern
    if not isinstance(pattern, dict):
        raise ValueError(
            f"a secret pattern must be a mapping, got {pattern!r}")
    unknown = set(pattern) - _PATTERN_KEYS
    if unknown:
        raise ValueError(
            "unknown secret pattern keys: %s"
            % ", ".join(sorted(unknown)))
    if "kind" not in pattern or "label" not in pattern:
        raise ValueError(
            "a secret pattern must name its kind and label")
    return SecretPattern(
        kind=pattern["kind"], label=pattern["label"],
        basis=pattern.get("basis", "text"))


def build_pattern(pattern: Any = None, **kwargs: Any) -> SecretPattern:
    """Build one validated secret pattern from a mapping or words."""
    if isinstance(pattern, SecretPattern) and not kwargs:
        return pattern
    if isinstance(pattern, dict) or pattern is None:
        merged: Dict[str, Any] = {}
        if isinstance(pattern, dict):
            merged.update(pattern)
        merged.update(kwargs)
        return validate_pattern(merged)
    raise ValueError(
        f"a secret pattern must be a mapping, got {pattern!r}")


# ---------------------------------------------------------------------
# Finding shapes in text, and redacting them.
# ---------------------------------------------------------------------


def _secret_spans(text: str) -> List[Tuple[int, int, str]]:
    """(start, end, kind) spans of secret-shaped text.

    The shipped scanner's findings plus this
    slice's assignment shape, overlaps resolved
    with the longest span winning, ordered by
    position. The secret text itself is read only
    to locate its span - it is never returned.
    """
    raw: List[Tuple[int, int, str]] = []
    for finding in scan_secrets(text):
        raw.append((finding.start, finding.end, finding.kind))
    for match in _ENV_ASSIGNMENT.finditer(text):
        start, end = match.span(2)
        raw.append((start, end, "env_assignment"))
    raw.sort(key=lambda span: (span[0], -(span[1] - span[0])))
    spans: List[Tuple[int, int, str]] = []
    for span in raw:
        if spans and span[0] < spans[-1][1]:
            continue
        spans.append(span)
    return spans


def secret_kinds_in(text: Any) -> Tuple[str, ...]:
    """The secret kinds a text carries, in kind order.

    Names kinds only - a caller learns what shapes
    a text holds, never the secret itself. Text
    that is not text refuses.
    """
    if not isinstance(text, str):
        raise ValueError(f"text to screen must be text, got {text!r}")
    if not text:
        return ()
    named = {kind for _start, _end, kind in _secret_spans(text)}
    return tuple(kind for kind in SECRET_KINDS if kind in named)


def redact_secrets(text: Any, marker: Any = REDACTION_MARKER) -> str:
    """Text with every secret-shaped span replaced by the marker.

    Built on the shipped scanner plus the
    assignment shape: the returned text can never
    contain a matched secret, because the whole
    matched span is replaced. Ordinary text is
    returned untouched. The marker is one fixed
    word of the caller's naming, never a fragment
    of any secret.
    """
    if not isinstance(text, str):
        raise ValueError(f"text to redact must be text, got {text!r}")
    fixed = _clean_text(marker, "a redaction marker")
    if not text:
        return text
    spans = _secret_spans(text)
    if not spans:
        return text
    parts: List[str] = []
    cursor = 0
    for start, end, _kind in spans:
        parts.append(text[cursor:start])
        parts.append(fixed)
        cursor = end
    parts.append(text[cursor:])
    return "".join(parts)


# ---------------------------------------------------------------------
# The screening: one file judged, the verdict as data.
# ---------------------------------------------------------------------


def filename_kinds(filename: Any) -> Tuple[str, ...]:
    """The kinds a filename alone carries: secret file, or none.

    Mechanical only, on the names the tree already
    treats as sensitive: a ``.env`` file (or one of
    its named variants), a credentials or key-identity
    file, a key file by ending, a path under ``.ssh``,
    or a name carrying the word secret.
    """
    name = _clean_text(filename, "a filename")
    parts = [part.lower() for part in name.split("/") if part]
    if not parts:
        return ()
    base = parts[-1]
    if base in _SECRET_BASENAMES:
        return ("secret_file",)
    if base.startswith(".env."):
        return ("secret_file",)
    if base.endswith(_SECRET_SUFFIXES):
        return ("secret_file",)
    if "secret" in base or ".ssh" in parts:
        return ("secret_file",)
    return ()


@dataclass(frozen=True)
class FileScreening:
    """One file's hygiene verdict: the file, its kinds, its status.

    ``filename`` names the file - it is the only
    fact about the file any record carries, besides
    the pattern ``kinds`` its name or text matched.
    The file's content is never a field here: a
    screening that exists can be stored, logged and
    shown without ever leaking what it screened.
    ``status`` is refused exactly when kinds are
    named and clean exactly when none are; a
    status named against its kinds refuses on
    construction, so a verdict can never disagree
    with itself. Constructing one validates it.
    """

    filename: str
    kinds: Tuple[str, ...] = ()
    status: Optional[str] = None
    screening_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "filename",
            _clean_text(self.filename, "a filename"))
        object.__setattr__(self, "kinds", _ordered_kinds(self.kinds))
        judged = "refused" if self.kinds else "clean"
        if self.status is None:
            object.__setattr__(self, "status", judged)
        else:
            named = normalize_screening_status(self.status)
            if named != judged:
                raise ValueError(
                    f"a screening with kinds {list(self.kinds)!r} "
                    f"is {judged}, not {named}")
            object.__setattr__(self, "status", named)
        if self.screening_id is not None:
            object.__setattr__(
                self, "screening_id",
                normalize_hygiene_id(self.screening_id))

    @property
    def refused(self) -> bool:
        return self.status == "refused"

    @property
    def display_label(self) -> str:
        name = self.screening_id or "screening"
        return f"{name} ({self.filename}: {self.status})"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "secret_screening",
            "slice": SECRET_HYGIENE_SLICE,
            "screening_id": self.screening_id,
            "filename": self.filename,
            "status": self.status,
            "kinds": list(self.kinds),
        }


#: The shorter word for a file screening - its verdict.
Screening = FileScreening


def validate_screening(screening: Any) -> FileScreening:
    """Validate one screening into a FileScreening.

    Accepts a FileScreening or a mapping naming a
    ``filename`` (or ``file`` / ``path`` / ``name``)
    - required - and optionally ``kinds`` (or
    ``kind`` / ``patterns`` / ``pattern``), a
    ``status`` (or ``verdict`` / ``result``) that
    must agree with those kinds, and a
    ``screening_id`` (or ``id``). Naming two
    spellings of one field with different values
    refuses, and unknown keys refuse.
    """
    if isinstance(screening, FileScreening):
        return screening
    if not isinstance(screening, dict):
        raise ValueError(
            f"a screening must be a mapping, got {screening!r}")
    unknown = set(screening) - _SCREENING_KEYS
    if unknown:
        raise ValueError(
            "unknown screening keys: %s"
            % ", ".join(sorted(unknown)))
    filename = _pick(
        screening, ("filename", "file", "path", "name"), "filenames")
    if filename is None:
        raise ValueError("a screening must name its file")
    kwargs: Dict[str, Any] = {"filename": filename}
    kinds = _pick(
        screening, ("kinds", "kind", "patterns", "pattern"), "kinds")
    if kinds is not None:
        kwargs["kinds"] = kinds
    status = _pick(
        screening, ("status", "verdict", "result"), "statuses")
    if status is not None:
        kwargs["status"] = status
    screening_id = _pick(screening, ("screening_id", "id"), "ids")
    if screening_id is not None:
        kwargs["screening_id"] = screening_id
    return FileScreening(**kwargs)


def build_screening(screening: Any = None, **kwargs: Any) -> FileScreening:
    """Build one validated screening from a mapping or field words."""
    if isinstance(screening, FileScreening) and not kwargs:
        return screening
    if isinstance(screening, dict) or screening is None:
        merged: Dict[str, Any] = {}
        if isinstance(screening, dict):
            merged.update(screening)
        merged.update(kwargs)
        return validate_screening(merged)
    raise ValueError(
        f"a screening must be a mapping, got {screening!r}")


def _require_screening(screening: Any) -> FileScreening:
    if isinstance(screening, FileScreening):
        return screening
    return validate_screening(screening)


def screen_file(filename: Any, text: Any = "") -> FileScreening:
    """Judge one file for commit: its name and its text, mechanically.

    The verdict names the file and every pattern
    kind its name or text matches, in kind order -
    and nothing else: the text is read only to
    locate shapes in it and is never carried into
    the verdict. No kinds means clean; any kind
    means the commit is refused.
    """
    name = _clean_text(filename, "a filename")
    body = "" if text is None else text
    if not isinstance(body, str):
        raise ValueError(
            f"a file's text must be text, got {text!r}")
    kinds = set(filename_kinds(name))
    kinds.update(secret_kinds_in(body))
    ordered = tuple(kind for kind in SECRET_KINDS if kind in kinds)
    return FileScreening(filename=name, kinds=ordered)


# ---------------------------------------------------------------------
# The refusal record: one refused screening, shaped as session news.
# ---------------------------------------------------------------------


def _refusal_headline(screening: FileScreening) -> str:
    labels = ", ".join(_KIND_LABELS[kind] for kind in screening.kinds)
    return (
        f"Commit refused for {screening.filename}: "
        f"secret pattern found ({labels}). "
        f"The file is named; its content is never shown.")


def hygiene_record(screening: Any) -> Optional[Dict[str, Any]]:
    """The session-news record of one refused screening, or None.

    A refused screening is always news - the agent
    layer publishes this record as a session event,
    so a refusal can never be lost as a mere log
    line. A clean screening owes no news and yields
    None, the budget-paused pattern. The record
    names the file and the pattern kinds only.
    """
    checked = _require_screening(screening)
    if not checked.refused:
        return None
    return {
        "type": "secret_refusal",
        "news": True,
        "slice": SECRET_HYGIENE_SLICE,
        "screening_id": checked.screening_id,
        "filename": checked.filename,
        "status": checked.status,
        "kinds": list(checked.kinds),
        "headline": _refusal_headline(checked),
    }


# ---------------------------------------------------------------------
# The registry model: screenings held for a session, ids deterministic.
# ---------------------------------------------------------------------


class HygieneRegistry:
    """An in-memory, storage-neutral registry of file screenings.

    Screenings are held in the order judged. Ids
    are deterministic: a caller-supplied id is used
    as given (a duplicate refuses), and an
    unsupplied id is the next ``hygiene-N`` in
    sequence, skipping any number a supplied id
    already took - no randomness a test cannot pin.
    Storage beyond memory is the agent layer's
    concern; this model is neutral.
    """

    def __init__(self) -> None:
        self._screenings: Dict[str, FileScreening] = {}
        self._next = 1

    def _fresh_id(self) -> str:
        while f"hygiene-{self._next}" in self._screenings:
            self._next += 1
        screening_id = f"hygiene-{self._next}"
        self._next += 1
        return screening_id

    def register(self, screening: Any = None, **kwargs: Any) -> FileScreening:
        """Hold one screening, under its id or a fresh deterministic one."""
        if kwargs and isinstance(screening, (FileScreening, dict)):
            validated = build_screening(screening, **kwargs)
        elif kwargs and screening is None:
            validated = build_screening(**kwargs)
        else:
            if kwargs:
                raise ValueError(
                    "a screening is named twice: as a record "
                    "and as field words")
            validated = _require_screening(screening)
        if validated.screening_id is None:
            validated = replace(
                validated, screening_id=self._fresh_id())
        elif validated.screening_id in self._screenings:
            raise ValueError(
                f"a screening named {validated.screening_id!r} "
                f"already exists")
        self._screenings[validated.screening_id] = validated
        return validated

    def screen(self, filename: Any, text: Any = "") -> FileScreening:
        """Judge one file and hold its verdict."""
        return self.register(screen_file(filename, text))

    def get(self, screening_id: Any) -> FileScreening:
        """The screening one id names; an unknown id raises KeyError."""
        wanted = normalize_hygiene_id(screening_id)
        if wanted not in self._screenings:
            raise KeyError(f"unknown screening: {wanted!r}")
        return self._screenings[wanted]

    def list_screenings(self) -> Tuple[FileScreening, ...]:
        """Every held screening, in the order judged, as a tuple."""
        return tuple(self._screenings.values())

    def __len__(self) -> int:
        return len(self._screenings)

    def record(self, screening_id: Any) -> Optional[Dict[str, Any]]:
        """One held screening's refusal record, or None when clean."""
        return hygiene_record(self.get(screening_id))


# ---------------------------------------------------------------------
# The /secrets surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def _screenings_from(source: Any) -> Tuple[FileScreening, ...]:
    """The screenings a source holds, in the order judged.

    A source is a HygieneRegistry, a list of
    screenings (or screening mappings), one
    screening, or nothing at all.
    """
    if source is None:
        return ()
    if isinstance(source, HygieneRegistry):
        return source.list_screenings()
    if isinstance(source, (FileScreening, dict)):
        return (_require_screening(source),)
    if isinstance(source, (list, tuple)):
        return tuple(_require_screening(item) for item in source)
    raise ValueError(
        "secret screenings must be a registry or a list of screenings")


def format_pattern(pattern: Any) -> str:
    """One secret pattern, in plain words: kind, label and basis."""
    current = validate_pattern(pattern)
    return f"{current.kind}: {current.label} ({current.basis} shape)."


def format_patterns() -> str:
    """Every known secret shape, in plain words, in kind order."""
    lines = [f"Secret patterns: {len(SECRET_PATTERNS)} known."]
    for pattern in SECRET_PATTERNS:
        lines.append(f"  {format_pattern(pattern)}")
    return "\n".join(lines)


def format_screening(screening: Any) -> str:
    """One screening, in plain words: file, status and kinds stated."""
    current = _require_screening(screening)
    name = current.screening_id or "screening"
    if not current.refused:
        return (
            f"{name}: {current.filename} - clean: "
            f"no secret pattern found.")
    labels = ", ".join(_KIND_LABELS[kind] for kind in current.kinds)
    return (
        f"{name}: {current.filename} - commit refused: "
        f"secret pattern found ({labels}). "
        f"Content is never shown.")


def format_screenings(source: Any = None) -> str:
    """The held screenings, in plain words, in the order judged.

    With no screenings at all the text starts with
    the plain statement of that fact. Every line
    states its screening's status in words.
    """
    screenings = _screenings_from(source)
    if not screenings:
        return "Secret hygiene: no files screened. No screening is held."
    lines = [f"Secret hygiene: {len(screenings)} screened."]
    for screening in screenings:
        lines.append(f"  {format_screening(screening)}")
    return "\n".join(lines)


def format_hygiene_record(record: Any) -> str:
    """One secret-refusal news record as its plain headline."""
    if isinstance(record, dict) \
            and record.get("type") == "secret_refusal":
        return str(record["headline"])
    raise ValueError("format_hygiene_record needs a refusal record")


#: The refusal record's formatter under its own name.
format_record = format_hygiene_record


def format_secrets_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /secrets."""
    lines = ["Secret hygiene (M-110) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_patterns())
    lines.append("")
    lines.append(format_screenings(source))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


_GRAMMAR_WORDS = ("show", "status", "check")


def parse_secrets_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /secrets grammar both surfaces share.

    No words (or ``show`` / ``status``) shows the
    screenings; ``show <screening>`` and a bare
    screening id show one screening; ``check
    <file>`` screens one named file. A grammar word
    in the wrong shape - a bare kind word, a doubled
    word, ``check`` with no file - is a usage error
    naming the grammar, never a screening id.
    Returns ``(action, target-or-None)``: for
    ``show`` the target is a screening id, for
    ``check`` it is the filename to screen.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None \
        else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "status"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "check":
        if len(words) == 2:
            return ("check", words[1])
        raise ValueError(USAGE)
    if head in ("show", "status") and len(words) == 2:
        if words[1].lower() in _GRAMMAR_WORDS:
            raise ValueError(USAGE)
        try:
            return ("show", normalize_hygiene_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head in _GRAMMAR_WORDS or len(words) != 1:
        raise ValueError(USAGE)
    lowered = words[0].lower().replace("-", "_")
    if lowered in _KIND_WORDS:
        raise ValueError(USAGE)
    try:
        return ("show", normalize_hygiene_id(words[0]))
    except ValueError:
        raise ValueError(USAGE) from None
