"""Key custody via Kista (All-Features roadmap slice M-032).

Part II — The Provider Ocean — closes its key story here.
The campaign law is plain: **secrets live in Kista** — Volmarr's
own credential keeper — and config files hold references, never
secrets.

What already shipped, and what this slice adds:

* Today a provider key reaches the session in two ways: as a
  plaintext value stored per-endpoint in the config's
  ``api_keys`` mapping, or from the provider's environment
  variable (the registry's ``api_key_env``). The plaintext road
  is the one this slice retires: a config value may now be a
  **Kista reference** — ``kista:<name>`` — and every shipped
  key reader (the agent's ``resolve_api_key``, the audio
  helper, the MCP server) resolves that reference through
  Kista instead of finding a secret in the config.
* Kista itself lives outside this package; this slice is the
  protocol Mythic speaks to it. A reference resolves, in
  order, through: (1) Kista's vault file — a private JSON
  mapping of name to key, whose location the user names with
  the ``MYTHIC_KISTA_FILE`` environment variable (this package
  never chooses a vault location on its own, and the file is
  only ever written with private permissions, on the adoption
  road below); and (2) the environment Kista injects the key
  into, under the reference's own name. A name Kista does not
  hold resolves to None — it is never guessed, and no other
  door's key is ever substituted for it.
* **Status without secrets.** :func:`custody_entries` names,
  for every configured door, where its key lives — ``kista``,
  ``environment``, legacy ``plaintext``, ``missing``, or
  ``not-needed`` for loopback doors — and whether a key is
  present. It never returns, logs, or formats a key value.
* **Adoption.** A legacy plaintext key can be moved into
  Kista: :func:`adopt` deposits it in the vault file under
  the door's key name and the config is left holding only
  the reference. Adoption refuses — plainly, changing
  nothing — when the door already holds a reference, when
  there is no stored key to move, when no vault file is
  configured, or when Kista already holds a *different* key
  under the same name (two doors sharing one key name).
* **A missing key asks once, kindly.** When no key can be
  found, :func:`missing_key_message` is the one remedy every
  surface shows: it names the door, the Kista reference to
  add, and the environment variable — in plain words, once,
  at the moment the key is needed.

Honesty rules, enforced here and pinned by the slice's tests:

* A reference is a name, never a secret: names are validated
  (letters, digits, ``.``, ``_``, ``-``, ``/``), and a value
  that merely starts with the prefix but carries no valid
  name is a malformed reference and raises, never a key.
* Legacy plaintext entries keep working until they are
  adopted (nothing already shipped is removed) — but the
  status surface calls them what they are.
* A malformed vault file raises, naming the file; its
  contents are never echoed and never guessed around.
"""

from __future__ import annotations

__all__ = [
    "PLAIN_EXPLANATION",
    "REF_PREFIX",
    "VAULT_ENV",
    "Any",
    "CustodyChange",
    "CustodyEntry",
    "Dict",
    "List",
    "Optional",
    "Path",
    "Tuple",
    "adopt",
    "custody_entries",
    "deposit",
    "format_custody",
    "format_custody_change",
    "is_reference",
    "key_env_for",
    "load_vault",
    "make_reference",
    "missing_key_message",
    "parse_kista_args",
    "plan_adoption",
    "reference_name",
    "resolve_reference",
    "stored_key_for",
    "suggested_reference",
    "vault_path",
]

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit

from .model_switch import infer_provider
from .provider_registry import load_registry
from .storage import atomic_private_json

#: A config ``api_keys`` value starting with this prefix is a
#: Kista reference, not a secret.
REF_PREFIX = "kista:"

#: The environment variable naming Kista's vault file. This
#: package never invents a vault location: no variable, no
#: vault-file road (the environment road still resolves).
VAULT_ENV = "MYTHIC_KISTA_FILE"

#: A reference name is a name, never a secret: a short token of
#: letters, digits, and ``._/-``, no spaces, no key material.
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")

_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}

#: Custody explained in plain words — the text every surface
#: shows. Keys belong in Kista; the config holds pointers.
PLAIN_EXPLANATION = (
    "Key custody: your API keys live in Kista, your own "
    "credential keeper — never in Mythic's config files. The "
    "config holds only a reference like kista:DEEPSEEK_API_KEY, "
    "and Mythic asks Kista for the key when a provider needs "
    "it. A key Kista does not hold is reported as missing, in "
    "plain words, once — it is never guessed and no other "
    "door's key is used in its place. A key still stored as "
    "plain text in the config keeps working, and /kista adopt "
    "moves it into Kista and leaves only the reference behind."
)


# ----------------------------------------------------------------------
# References
# ----------------------------------------------------------------------


def is_reference(value: Any) -> bool:
    """True when *value* is a string carrying the Kista prefix."""
    return isinstance(value, str) and value.startswith(REF_PREFIX)


def reference_name(value: Any) -> str:
    """The name a Kista reference points at (ValueError if malformed).

    A reference is ``kista:<name>`` where the name matches the
    name grammar. Anything else with the prefix — an empty
    name, spaces, key-like material — is a malformed reference
    and raises: it is surfaced, never treated as a key.
    """
    if not is_reference(value):
        raise ValueError(f"Not a Kista reference: {value!r}")
    name = value[len(REF_PREFIX):].strip()
    if not _NAME_RE.match(name):
        raise ValueError(
            f"Malformed Kista reference {value!r}: name a key "
            "with letters, digits, and . _ - / only, e.g. "
            "kista:DEEPSEEK_API_KEY.")
    return name


def make_reference(name: Any) -> str:
    """The reference string for a key *name* (validated)."""
    if not isinstance(name, str) or not _NAME_RE.match(name.strip()):
        raise ValueError(
            f"A Kista key name must be letters, digits, and "
            f". _ - / only, got {name!r}.")
    return REF_PREFIX + name.strip()


def key_env_for(base_url: Any) -> str:
    """The key environment variable name for a door.

    The M-019 registry answers first: the provider whose
    endpoint matches the door exactly names its own
    ``api_key_env``. For a custom door no registry entry owns,
    the long-standing endpoint heuristics answer (DeepSeek,
    OpenRouter, Anthropic by host, OpenAI as the compatible
    default) — the same names the session has always used.
    """
    if isinstance(base_url, str) and base_url.strip():
        provider = infer_provider(base_url)
        if provider is not None:
            entry = load_registry().provider(provider)
            if entry.api_key_env:
                return entry.api_key_env
        lowered = base_url.lower()
        if "deepseek" in lowered:
            return "DEEPSEEK_API_KEY"
        if "openrouter" in lowered:
            return "OPENROUTER_API_KEY"
        if "anthropic" in lowered:
            return "ANTHROPIC_API_KEY"
    return "OPENAI_API_KEY"


def suggested_reference(base_url: Any) -> str:
    """The Kista reference a door's key should live under."""
    return make_reference(key_env_for(base_url))


# ----------------------------------------------------------------------
# Kista's doors: the vault file and the injected environment
# ----------------------------------------------------------------------


def vault_path(explicit: Any = None, environ: Any = None) -> Optional[Path]:
    """Kista's vault file, or None when none is configured.

    *explicit* wins; otherwise the ``MYTHIC_KISTA_FILE``
    environment variable names the file. No variable means
    this package does not go looking for a vault on its own.
    """
    env = os.environ if environ is None else environ
    raw = explicit if explicit else env.get(VAULT_ENV)
    if not raw:
        return None
    return Path(str(raw)).expanduser()


def load_vault(path: Any) -> Dict[str, str]:
    """Read a Kista vault file: a JSON mapping of name to key.

    A missing file is an empty vault. A malformed file — not
    JSON, not an object, or holding a non-string value —
    raises ValueError naming the file; its contents are never
    echoed and never guessed around.
    """
    vault_file = Path(path)
    if not vault_file.exists():
        return {}
    try:
        data = json.loads(vault_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(
            f"Kista vault file {vault_file} could not be read "
            f"as JSON ({type(exc).__name__}); fix or replace "
            "the file — no key was guessed.") from exc
    if not isinstance(data, dict) or not all(
            isinstance(k, str) and isinstance(v, str)
            for k, v in data.items()):
        raise ValueError(
            f"Kista vault file {vault_file} must hold a JSON "
            "object mapping key names to key strings; no key "
            "was guessed.")
    return dict(data)


def deposit(path: Any, name: str, secret: str) -> str:
    """Write *secret* into Kista's vault file under *name*.

    The file is written with private permissions (the storage
    layer's atomic private write), and an existing entry under
    the same name with the same value is kept as-is. Returns
    the name deposited under.
    """
    if not isinstance(secret, str) or not secret:
        raise ValueError("There is no key to deposit in Kista.")
    validated = reference_name(make_reference(name))
    vault_file = Path(path)
    vault = load_vault(vault_file)
    vault[validated] = secret
    atomic_private_json(vault_file, vault)
    return validated


def resolve_reference(value: Any, *, environ: Any = None,
                      vault_file: Any = None) -> Optional[str]:
    """The key a Kista reference points at, or None.

    Kista's vault file answers first, then the environment
    under the reference's own name. A name Kista does not hold
    returns None — never another door's key, never a guess.
    """
    name = reference_name(value)
    env = os.environ if environ is None else environ
    path = vault_path(vault_file, env)
    if path is not None:
        vault = load_vault(path)
        if vault.get(name):
            return vault[name]
    candidate = env.get(name)
    return candidate if candidate else None


def stored_key_for(config: Dict[str, Any], base_url: Any, *,
                   environ: Any = None,
                   vault_file: Any = None) -> Optional[str]:
    """The usable key stored for a door, if any.

    A Kista reference resolves through Kista; a legacy
    plaintext value is itself (kept working until adopted);
    nothing stored is None. This is the one stored-key read
    every shipped caller (agent, audio, MCP server) shares.
    """
    stored = (config.get("api_keys") or {}).get(base_url)
    if not stored:
        return None
    if is_reference(stored):
        return resolve_reference(stored, environ=environ,
                                 vault_file=vault_file)
    return stored if isinstance(stored, str) else None


# ----------------------------------------------------------------------
# Custody status — where each key lives, never what it is
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class CustodyEntry:
    """One door's custody: where its key lives, and whether one is held.

    ``custody`` is one of ``kista`` / ``environment`` /
    ``plaintext`` / ``missing`` / ``not-needed``. No field ever
    carries a key value.
    """

    base_url: str
    provider: Optional[str]
    custody: str
    reference: Optional[str]
    env_name: str
    present: bool

    def record(self) -> Dict[str, Any]:
        """This entry as a plain mapping."""
        return {"base_url": self.base_url,
                "provider": self.provider,
                "custody": self.custody,
                "reference": self.reference,
                "env_name": self.env_name,
                "present": self.present}

    def describe(self) -> str:
        """One plain line: the door and where its key lives."""
        label = self.base_url
        if self.provider:
            label += f" ({self.provider})"
        if self.custody == "kista":
            state = (f"key in Kista as {self.reference}"
                     if self.present else
                     f"Kista reference {self.reference}, but "
                     "Kista holds no key under that name yet")
        elif self.custody == "environment":
            state = f"key from the {self.env_name} environment variable"
        elif self.custody == "plaintext":
            state = ("key stored as plain text in the config "
                     "(legacy — /kista adopt moves it into Kista)")
        elif self.custody == "not-needed":
            state = "local door — no key needed"
        else:
            state = (f"no key held — add it to Kista as "
                     f"{suggested_reference(self.base_url)}, or "
                     f"export {self.env_name}")
        return f"{label}: {state}"


def _is_loopback(base_url: Any) -> bool:
    if not isinstance(base_url, str):
        return False
    try:
        return urlsplit(base_url).hostname in _LOOPBACK_HOSTS
    except ValueError:
        return False


def custody_entries(config: Dict[str, Any], *, environ: Any = None,
                    vault_file: Any = None) -> Tuple[CustodyEntry, ...]:
    """Every configured door's custody, in config order.

    One entry per ``api_keys`` door, plus the session's
    current door when it stores no key of its own (answered
    from the environment, from loopback, or as missing). A
    malformed stored reference raises — a custody the user
    cannot read back truthfully must surface, not vanish.
    """
    env = os.environ if environ is None else environ
    entries: List[CustodyEntry] = []
    seen = set()
    stored_map = config.get("api_keys") or {}
    if not isinstance(stored_map, dict):
        raise ValueError("api_keys must be a mapping of door to key "
                         "or Kista reference.")
    for base_url, stored in stored_map.items():
        seen.add(base_url)
        env_name = key_env_for(base_url)
        if is_reference(stored):
            name = reference_name(stored)
            key = resolve_reference(stored, environ=env,
                                    vault_file=vault_file)
            entries.append(CustodyEntry(
                base_url=base_url,
                provider=infer_provider(base_url),
                custody="kista", reference=stored,
                env_name=env_name, present=key is not None))
        elif isinstance(stored, str) and stored:
            entries.append(CustodyEntry(
                base_url=base_url,
                provider=infer_provider(base_url),
                custody="plaintext", reference=None,
                env_name=env_name, present=True))
        else:
            raise ValueError(
                f"The stored key for {base_url} is not text; "
                "fix the config entry — its value was not shown.")
    current = config.get("base_url")
    if isinstance(current, str) and current and current not in seen:
        env_name = key_env_for(current)
        if _is_loopback(current):
            custody, present = "not-needed", True
        elif env.get(env_name):
            custody, present = "environment", True
        else:
            custody, present = "missing", False
        entries.append(CustodyEntry(
            base_url=current, provider=infer_provider(current),
            custody=custody, reference=None,
            env_name=env_name, present=present))
    return tuple(entries)


# ----------------------------------------------------------------------
# Adoption — a legacy plaintext key moves into Kista
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class CustodyChange:
    """One adoption: the door, and the reference it now holds."""

    base_url: str
    reference: str

    def event(self) -> Dict[str, Any]:
        """The session-event payload (door + reference, never a key)."""
        return {"type": "key_custody_changed",
                "base_url": self.base_url,
                "reference": self.reference}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        """The change record the agent returns to its callers."""
        return {"kind": "kista", "base_url": self.base_url,
                "reference": self.reference,
                "session_id": session_id, "journaled": journaled}


def plan_adoption(config: Dict[str, Any], base_url: Any = None, *,
                  environ: Any = None,
                  vault_file: Any = None) -> CustodyChange:
    """Validate an adoption without moving anything.

    Raises plainly — changing nothing — when the door already
    holds a Kista reference, when it stores no key to move,
    when no vault file is configured, or when Kista already
    holds a different key under the door's key name.
    """
    target = base_url or config.get("base_url")
    if not isinstance(target, str) or not target.strip():
        raise ValueError("Name the door whose key should move "
                         "into Kista (its base URL).")
    stored = (config.get("api_keys") or {}).get(target)
    if is_reference(stored):
        raise ValueError(
            f"The key for {target} already lives in Kista as "
            f"{stored}; nothing moves.")
    if not isinstance(stored, str) or not stored:
        raise ValueError(
            f"No key is stored for {target}, so there is "
            "nothing to move into Kista. Add the key to Kista "
            f"as {suggested_reference(target)}, or export "
            f"{key_env_for(target)}.")
    path = vault_path(vault_file, environ)
    if path is None:
        raise ValueError(
            f"Kista's vault file is not configured, so the key "
            f"for {target} stays where it is. Set {VAULT_ENV} "
            "to your Kista vault file, then adopt again.")
    name = key_env_for(target)
    existing = load_vault(path).get(name)
    if existing is not None and existing != stored:
        raise ValueError(
            f"Kista already holds a different key under "
            f"{name} (another door uses that name); adoption "
            "was refused so neither key is overwritten.")
    return CustodyChange(base_url=target,
                         reference=make_reference(name))


def adopt(config: Dict[str, Any], base_url: Any = None, *,
          environ: Any = None,
          vault_file: Any = None) -> Tuple[str, CustodyChange]:
    """Move a door's stored plaintext key into Kista.

    Validates with :func:`plan_adoption`, deposits the key in
    the vault file under the door's key name, and returns
    ``(reference, change)``. Pure regarding *config*: the
    caller writes the reference into the config and saves it —
    the config never holds the secret again once it does.
    """
    change = plan_adoption(config, base_url, environ=environ,
                           vault_file=vault_file)
    target = change.base_url
    stored = (config.get("api_keys") or {})[target]
    path = vault_path(vault_file, environ)
    deposit(path, key_env_for(target), stored)
    return change.reference, change


# ----------------------------------------------------------------------
# The missing-key remedy, and the /kista grammar + formatters
# ----------------------------------------------------------------------


def missing_key_message(base_url: Any) -> str:
    """The one plain remedy shown when a door has no key.

    It asks once, kindly: it names the door, the Kista
    reference to add, and the environment variable — and it
    never invents a key. Loopback doors need no key at all.
    """
    if _is_loopback(base_url):
        return (f"No API key is needed for {base_url}: local "
                "loopback endpoints need no key.")
    return (
        f"No API key configured for {base_url}. Add it to Kista "
        f"as {suggested_reference(base_url)} — Mythic's config "
        "holds only that reference, never the key — or export "
        f"{key_env_for(base_url)}. That is the one thing "
        "needed; nothing else changes.")


def parse_kista_args(text: Any) -> Dict[str, Any]:
    """Parse the ``/kista`` slash-command argument string.

    Grammar::

        /kista                  -> show custody for every door
        /kista adopt            -> adopt the current door's key
        /kista adopt <base-url> -> adopt that door's key

    Returns a dict with keys ``action`` (``show`` / ``adopt``)
    and ``base_url``. Raises :class:`ValueError` on a usage
    error.
    """
    if text is None:
        text = ""
    if not isinstance(text, str):
        raise ValueError(
            f"Kista arguments must be text, got {type(text).__name__}")
    parsed: Dict[str, Any] = {"action": "show", "base_url": None}
    stripped = text.strip()
    if not stripped:
        return parsed
    head, _, rest = stripped.partition(" ")
    if head.lower() == "show" and not rest.strip():
        return parsed
    if head.lower() == "adopt":
        parsed["action"] = "adopt"
        target = rest.strip()
        if target:
            if " " in target:
                raise ValueError(
                    "Usage: /kista, /kista adopt, or "
                    "/kista adopt <base-url>")
            parsed["base_url"] = target
        return parsed
    raise ValueError(
        "Usage: /kista, /kista adopt, or /kista adopt <base-url>")


def format_custody(config: Dict[str, Any], *, environ: Any = None,
                   vault_file: Any = None) -> str:
    """The visible custody board: every door, where its key lives."""
    path = vault_path(vault_file, environ)
    lines = [
        "Key custody (Kista):",
        PLAIN_EXPLANATION,
        ("  Kista vault file: " + str(path)
         if path is not None else
         "  Kista vault file: not configured "
         f"(set {VAULT_ENV} to name it) — references still "
         "resolve from the environment."),
        "  Doors:",
    ]
    entries = custody_entries(config, environ=environ,
                              vault_file=vault_file)
    if entries:
        for entry in entries:
            lines.append(f"    {entry.describe()}")
    else:
        lines.append("    No doors are configured yet.")
    lines.append(
        "  Move a plain-text key into Kista with /kista adopt; "
        "the config keeps only its reference.")
    return "\n".join(lines)


def format_custody_change(record: Dict[str, Any]) -> str:
    """One plain sentence describing a completed adoption."""
    text = (f"The key for {record['base_url']} now lives in "
            f"Kista as {record['reference']}; the config file "
            "holds only that reference.")
    if record.get("session_id"):
        text += f" Recorded on session {record['session_id']}."
    return text
