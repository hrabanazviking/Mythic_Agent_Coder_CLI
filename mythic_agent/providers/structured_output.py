"""Structured-output negotiation (Slice 041).

Schema -> request-payload transform per adapter family, plus a JSON-fence
fallback parse for providers without native ``json_mode``.

Design (mirrors :mod:`mythic_agent.providers.tool_negotiation`):

* :func:`negotiate` builds the native JSON-schema request fragment for a
  provider. It calls ``provider.require_capability("json_mode")`` first,
  so adapters without native JSON mode raise :class:`ProviderError`
  before any payload is built. Wire shapes:

  - OpenAI-family (``openai``, ``openrouter``, ``deepseek``, ``vllm``,
    ``lmstudio``, ``llama.cpp``, ``local-openai``): OpenAI chat
    ``response_format={"type": "json_schema", "json_schema": {...}}``.
    The OpenAI-compat ``chat()`` already passes ``response_format``
    through, so the fragment merges straight into ``chat(**kwargs)``.
  - ``ollama`` (native ``/api/chat`` API): ``{"format": <schema>}`` —
    Ollama accepts a full JSON schema as the ``format`` field.
  - ``google``: ``{"generation_config": {"response_mime_type":
    "application/json", "response_schema": <schema>}}`` — the
    documented Gemini shape; ``GoogleProvider.chat()`` passes
    ``generation_config`` through to ``generate_content``.
  - ``anthropic``: no native JSON mode in this codebase
    (``capabilities()["json_mode"]`` is False) — negotiation
    raises; use :func:`prepare` instead.

* :func:`prepare` is the convenience entry point: native providers get
  ``(messages, payload_fragment)``; providers without native JSON mode
  get the messages back with a schema-instruction system message
  appended and an empty fragment. Nothing is fabricated — the fallback
  asks the model for JSON explicitly.

* :func:`parse_json` decodes the assistant's reply. Native mode expects
  bare JSON. Fallback mode strips ```json fences and locates the first
  balanced ``{...}`` object, so models that wrap JSON in prose still
  parse. Malformed input raises :class:`ProviderError` (never a raw
  :class:`json.JSONDecodeError`).

No network is touched here; everything operates on in-memory shapes.
"""


from __future__ import annotations

__all__ = [
    "Provider",
    "ProviderError",
    "negotiate",
    "parse_json",
    "prepare",
    "system_prompt_fallback",
]

import json
from typing import Any

from .base import Provider, ProviderError


#: provider.name -> wire family for structured output.
_FAMILIES: dict[str, str] = {
    "openai": "openai",
    "openrouter": "openai",
    "deepseek": "openai",
    "vllm": "openai",
    "lmstudio": "openai",
    "llama.cpp": "openai",
    "local-openai": "openai",
    "google": "google",
    "gemini": "google",
    "ollama": "ollama",
}


def _family_of(provider: Provider) -> str:
    name = (getattr(provider, "name", "") or "").lower()
    return _FAMILIES.get(name, "unknown")


def _check_schema(schema: Any) -> dict[str, Any]:
    if not isinstance(schema, dict) or not schema:
        raise ProviderError(
            "schema must be a non-empty JSON-schema dict, "
            f"got {type(schema).__name__}")
    if not isinstance(schema.get("type"), str):
        raise ProviderError(
            "schema must define a string 'type' (a JSON-schema object)")
    return schema


def negotiate(
    provider: Provider,
    schema: dict[str, Any],
    *,
    name: str = "response",
    strict: bool = False,
) -> dict[str, Any]:
    """Build the native JSON-schema request fragment for ``provider``.

    Calls ``provider.require_capability("json_mode")`` first. Returns a
    dict ready to merge into ``chat(**kwargs)``. ``name`` labels the
    schema for the OpenAI wire shape; ``strict`` is passed through to
    the OpenAI ``json_schema`` wrapper.
    """
    provider.require_capability("json_mode")
    schema = _check_schema(schema)
    if not isinstance(name, str) or not name:
        raise ProviderError("schema 'name' must be a non-empty string")
    family = _family_of(provider)
    if family == "openai":
        return {"response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": name,
                "schema": schema,
                "strict": bool(strict),
            },
        }}
    if family == "ollama":
        return {"format": schema}
    if family == "google":
        return {"generation_config": {
            "response_mime_type": "application/json",
            "response_schema": schema,
        }}
    raise ProviderError(
        f"Provider {provider.name!r}: structured-output wire shape "
        "unknown; json_mode was advertised but no mapping exists.")


def system_prompt_fallback(schema: dict[str, Any]) -> str:
    """Instruction text injected for providers without native json_mode.

    Asks the model to answer with exactly one JSON object matching
    ``schema`` and no surrounding prose, so :func:`parse_json` in
    fallback mode can recover it.
    """
    schema = _check_schema(schema)
    compact = json.dumps(schema, separators=(",", ":"))
    return (
        "You must answer with exactly one JSON object and nothing else. "
        "No markdown fences, no prose before or after. The object must "
        f"conform to this JSON Schema: {compact}")


def prepare(
    provider: Provider,
    messages: list[dict[str, Any]],
    schema: dict[str, Any],
    *,
    name: str = "response",
    strict: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Negotiate structured output, with fallback for non-native providers.

    Returns ``(messages, payload_fragment)``:

    * providers with native ``json_mode``: ``messages`` unchanged and
      the :func:`negotiate` fragment (merge into ``chat(**kwargs)``);
    * providers without: ``messages`` plus a system message carrying
      :func:`system_prompt_fallback`, and an empty fragment.

    ``messages`` is validated with
    :meth:`Provider.validate_messages` first; the returned list is a
    new list (the caller's list is never mutated).
    """
    messages = Provider.validate_messages(messages)
    _check_schema(schema)
    if provider.capabilities().get("json_mode", False):
        return list(messages), negotiate(
            provider, schema, name=name, strict=strict)
    instructed = list(messages) + [{
        "role": "system",
        "content": system_prompt_fallback(schema),
    }]
    return instructed, {}


def _strip_fences(text: str) -> str:
    """Remove one layer of ```json / ``` fences, if present."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        # Drop the opening fence line (``` or ```json ...).
        lines = lines[1:]
        # Drop a trailing bare ``` line.
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped


def _first_json_object(text: str) -> str:
    """Return the first balanced ``{...}`` substring of ``text``.

    Raises :class:`ProviderError` when no balanced object exists.
    String literals and escapes are honored so braces inside strings
    do not end the scan early.
    """
    start = text.find("{")
    if start < 0:
        raise ProviderError(
            "No JSON object found in the model reply (fallback parse).")
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    raise ProviderError(
        "Unbalanced braces in the model reply (fallback parse).")


def parse_json(provider: Provider, text: str, *, native: bool | None = None
               ) -> dict[str, Any]:
    """Decode the assistant's structured-output reply to a dict.

    ``native=None`` (default) follows the provider's ``json_mode``
    capability: native providers parse with strict :func:`json.loads`;
    non-native providers use the fence-stripping fallback. Pass
    ``native=True``/``False`` to force either path (tests use this).
    Malformed input raises :class:`ProviderError`.
    """
    if not isinstance(text, str) or not text.strip():
        raise ProviderError("Cannot parse structured output from empty text.")
    if native is None:
        native = bool(provider.capabilities().get("json_mode", False))
    candidate = text.strip() if native else _first_json_object(
        _strip_fences(text))
    try:
        decoded = json.loads(candidate)
    except ValueError as exc:
        raise ProviderError(
            f"Structured-output reply is not valid JSON: {exc}") from exc
    if not isinstance(decoded, dict):
        raise ProviderError(
            "Structured-output reply decoded to "
            f"{type(decoded).__name__}, expected a JSON object.")
    return decoded
