"""Mid-session model switching (All-Features roadmap slice M-028).

Part II — The Provider Ocean — continues here. A live session can
change its model, or its provider, *without* losing the session, the
plan, or the crew — and the switch is a journal event, with the
reason when one is given.

This module is the pure resolution layer: given the current selection
and a requested change, it computes the new selection and validates
it *before* anything mutates. It performs no I/O (the agent layer
owns the config save and the session checkpoint), imports no
provider implementation, and knows providers only through the
M-019 registry data (``mythic_agent.core.provider_registry``).

Honesty rules, enforced here and pinned by the slice's tests:

* The live chat session speaks the OpenAI-compatible door (today's
  ``build_provider_client``). A provider switch is therefore offered
  only for registry doors that client can actually speak:
  ``openai_compatible`` entries, plus ``aesir_native`` (M-025 proved
  Aesir's ``/v1`` chat door is the OpenAI subset). Providers whose
  door is a native SDK (Anthropic, Google) or Ollama's own API are
  refused *plainly, with the reason* — their native adapters exist
  (M-021/M-022/M-023), but pretending the live session had switched
  to them would be a lie. Nothing is mutated on a refusal.
* A provider name resolves through the registry's aliases; an
  unknown name is refused with the registry's names, never guessed.
* A custom door (a bare base URL, the long-standing ``/model <name>
  <url>`` form) stays fully supported; its provider is recorded as
  ``None`` (a custom door has no registry name) unless the URL *is*
  a registry endpoint, in which case that provider is the truth.
* A provider with no model named gets its registry default model;
  a model named explicitly is taken as given (gateways serve far
  more than their static lists — M-026 — so the registry list is
  never used as a gate).
* The reason is free text: surrounding whitespace is stripped, an
  all-whitespace reason becomes ``None``, and a non-text reason is
  refused. The reason is recorded exactly once, on the journal
  event — never injected into the conversation.
"""

from __future__ import annotations

__all__ = [
    "SWITCHABLE_DIALECTS",
    "SWITCH_SLICE",
    "Any",
    "Dict",
    "Optional",
    "SwitchTarget",
    "Tuple",
    "format_switch_record",
    "infer_provider",
    "parse_switch_args",
    "resolve_switch",
]

import shlex
import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from .provider_registry import ProviderDef, load_registry

#: The slice that owns this module.
SWITCH_SLICE = "M-028"

#: Registry dialects the live chat session's client can speak: the
#: OpenAI-compatible doors, plus Aesir's native door whose chat route
#: is the OpenAI subset (M-025). Every other dialect is refused
#: plainly by :func:`resolve_switch`.
SWITCHABLE_DIALECTS = ("aesir_native", "openai_compatible")


def _valid_url(value: Any) -> bool:
    """True for an http(s) URL with a host (the config layer's rule)."""
    if not isinstance(value, str):
        return False
    try:
        parsed = urllib.parse.urlsplit(value)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname)


def _clean_reason(reason: Any) -> Optional[str]:
    """Normalise a switch *reason*: text or None, never blank text."""
    if reason is None:
        return None
    if not isinstance(reason, str):
        raise ValueError(
            f"Switch reason must be text, got {type(reason).__name__}")
    cleaned = reason.strip()
    return cleaned or None


@dataclass(frozen=True)
class SwitchTarget:
    """One validated model/provider selection change.

    ``from_*`` describes the selection in force before the switch,
    ``to_*`` the selection after it. A provider value of ``None``
    means a custom door: a base URL with no registry entry behind
    it. ``reason`` is the user's stated reason, or ``None``.
    """

    from_model: str
    from_base_url: str
    from_provider: Optional[str]
    to_model: str
    to_base_url: str
    to_provider: Optional[str]
    reason: Optional[str]

    def event(self) -> Dict[str, Any]:
        """The ``model_switched`` session-event payload for this switch."""
        return {
            "type": "model_switched",
            "from": {"model": self.from_model,
                     "base_url": self.from_base_url,
                     "provider": self.from_provider},
            "to": {"model": self.to_model,
                   "base_url": self.to_base_url,
                   "provider": self.to_provider},
            "reason": self.reason,
        }

    def record(self, session_id: Optional[str], journaled: bool) -> Dict[str, Any]:
        """The switch record the agent returns to its callers."""
        return {
            "from": {"model": self.from_model,
                     "base_url": self.from_base_url,
                     "provider": self.from_provider},
            "to": {"model": self.to_model,
                   "base_url": self.to_base_url,
                   "provider": self.to_provider},
            "reason": self.reason,
            "session_id": session_id,
            "journaled": journaled,
        }


def infer_provider(base_url: Any) -> Optional[str]:
    """The registry provider whose endpoint *base_url* is, or None.

    Inference is exact endpoint equality against the M-019 registry
    data — nothing fuzzier is claimed. A custom door (or a URL that
    is not a URL at all) has no provider: ``None``, never a guess.
    """
    if not isinstance(base_url, str) or not base_url:
        return None
    registry = load_registry()
    for entry in registry.providers:
        if entry.endpoint is not None and entry.endpoint == base_url:
            return entry.name
    return None


def _refuse_native(entry: ProviderDef) -> ValueError:
    """The plain refusal for a door the live session cannot speak."""
    return ValueError(
        f"Provider {entry.name!r} speaks the {entry.dialect} dialect, "
        "which the live chat session's client cannot use: the session "
        "speaks the OpenAI-compatible door, and this provider's native "
        "adapter is a separate surface. The session, its model and "
        "its provider are unchanged; pick an OpenAI-compatible "
        "provider, a model on the current door, or a custom door "
        "URL instead.")


def resolve_switch(current: Dict[str, Any], *, model: Any = None,
                   provider: Any = None, base_url: Any = None,
                   reason: Any = None) -> SwitchTarget:
    """Validate a requested switch against the *current* selection.

    ``current`` is the live config mapping (``model`` / ``base_url``
    are read from it). Exactly the requested fields change:

    * *provider* names a registry provider (aliases resolve): the
      new door is its registry endpoint and, with no explicit
      *model*, its registry default model. Dialects outside
      :data:`SWITCHABLE_DIALECTS` are refused plainly.
    * *base_url* names a custom door directly (it wins over
      *provider*'s endpoint when both are given, and the provider
      is then whatever that URL's endpoint truthfully is).
    * *model* alone changes only the model, on the current door.

    Raises :class:`ValueError` for every refusal, before anything
    has mutated: unknown provider, unswitchable dialect, empty
    model, invalid URL, or a request that names nothing to change.
    """
    cleaned_reason = _clean_reason(reason)
    from_model = current.get("model") or ""
    from_base_url = current.get("base_url") or ""
    from_provider = infer_provider(from_base_url)

    if model is not None and (not isinstance(model, str) or not model.strip()):
        raise ValueError("Model must be nonempty text")
    if base_url is not None and not _valid_url(base_url):
        raise ValueError(
            "Endpoint must be an HTTP(S) URL, "
            f"got {base_url!r}")

    entry: Optional[ProviderDef] = None
    if provider is not None:
        if not isinstance(provider, str) or not provider.strip():
            raise ValueError("Provider must be nonempty text")
        registry = load_registry()
        try:
            entry = registry.provider(provider)
        except KeyError:
            names = ", ".join(registry.names())
            raise ValueError(
                f"Unknown provider {provider!r}. "
                f"Registry providers: {names}") from None
        if entry.dialect not in SWITCHABLE_DIALECTS:
            raise _refuse_native(entry)

    if entry is None and model is None and base_url is None:
        raise ValueError(
            "Nothing to switch: name a model, a provider, or a door URL")

    if base_url is not None:
        to_base_url = base_url
        to_provider = infer_provider(base_url)
    elif entry is not None:
        # SWITCHABLE_DIALECTS entries always carry an endpoint: the
        # registry validator refuses an openai_compatible/aesir door
        # without one, and native doors never reach this line.
        to_base_url = entry.endpoint or ""
        to_provider = entry.name
    else:
        to_base_url = from_base_url
        to_provider = from_provider

    if model is not None:
        to_model = model.strip()
    elif entry is not None:
        to_model = entry.default_model
    else:
        to_model = from_model

    return SwitchTarget(
        from_model=from_model, from_base_url=from_base_url,
        from_provider=from_provider, to_model=to_model,
        to_base_url=to_base_url, to_provider=to_provider,
        reason=cleaned_reason)


def parse_switch_args(text: Any) -> Dict[str, Any]:
    """Parse the ``/model`` slash-command argument string.

    Grammar (flags may be combined with the legacy positionals, but
    a field given twice — positionally and by flag — is a usage
    error, never a silent winner)::

        /model                                  -> {} (show current)
        /model <model> [url]                    -> legacy positional
        /model --provider <name> [--model <model>]
               [--base-url <url>] [--reason <words...>]

    ``--reason`` consumes the rest of the line. Returns a dict with
    keys ``model``, ``provider``, ``base_url``, ``reason`` (values
    ``None`` when not given). Raises :class:`ValueError` on a usage
    error (unknown flag, missing flag value, too many positionals).
    """
    if text is None:
        text = ""
    if not isinstance(text, str):
        raise ValueError(
            f"Switch arguments must be text, got {type(text).__name__}")
    try:
        tokens = shlex.split(text)
    except ValueError as exc:
        raise ValueError(f"Could not parse switch arguments: {exc}") from exc
    parsed: Dict[str, Any] = {"model": None, "provider": None,
                              "base_url": None, "reason": None}
    positionals: list = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "--reason":
            rest = tokens[index + 1:]
            if not rest:
                raise ValueError("--reason needs the reason text after it")
            parsed["reason"] = " ".join(rest)
            index = len(tokens)
        elif token in ("--provider", "--model", "--base-url"):
            if index + 1 >= len(tokens):
                raise ValueError(f"{token} needs a value after it")
            key = {"--provider": "provider", "--model": "model",
                   "--base-url": "base_url"}[token]
            if parsed[key] is not None:
                raise ValueError(f"{token} was given twice")
            parsed[key] = tokens[index + 1]
            index += 2
        elif token.startswith("--"):
            raise ValueError(
                f"Unknown switch flag {token!r}; use --provider, "
                "--model, --base-url or --reason")
        else:
            positionals.append(token)
            index += 1
    if len(positionals) > 2:
        raise ValueError(
            "Usage: /model <model> [url] — too many bare words; "
            "use --reason for an explanation with spaces")
    if positionals:
        if parsed["model"] is not None:
            raise ValueError(
                "Model given both as a bare word and with --model; "
                "give it once")
        parsed["model"] = positionals[0]
    if len(positionals) == 2:
        if parsed["base_url"] is not None:
            raise ValueError(
                "Door URL given both as a bare word and with "
                "--base-url; give it once")
        parsed["base_url"] = positionals[1]
    return parsed


def format_switch_record(record: Dict[str, Any]) -> str:
    """One plain sentence describing a completed switch.

    Names the old and new selection, the surviving session when
    there is one, and the reason when one was given — the sentence
    both slash surfaces show, so they can never drift apart.
    """
    before, after = record["from"], record["to"]
    def _describe(side: Dict[str, Any]) -> str:
        label = f"{side['model']}"
        if side.get("provider"):
            label += f" via {side['provider']}"
        return f"{label} ({side['base_url']})"
    text = (f"Model changed from {_describe(before)} "
            f"to {_describe(after)}.")
    if record.get("session_id"):
        text += (f" Session {record['session_id']} kept — its "
                 "history, plan and crew are unchanged.")
    if record.get("reason"):
        text += f" Reason: {record['reason']}"
    return text
