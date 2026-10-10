"""Tool-call payload negotiation and response parsing (Slice R-040).

:func:`negotiate` builds the tool-definition payload for a provider,
choosing the wire format by ``provider.name``: OpenAI-style
``{"tools": [{"type": "function", "function": {...}}]}`` for
OpenAI-family providers, Anthropic-style
``{"tools": [{"name": ..., "description": ..., "input_schema": ...}]}``
for Anthropic. Providers whose name is not in the explicit mapping
fall back to the OpenAI style (documented: the OpenAI function-calling
shape is the de-facto lingua franca that most compatible endpoints —
OpenRouter, DeepSeek, vLLM, llama.cpp, Ollama — accept).

:func:`parse_tool_calls` normalizes the assistant's tool-call response
— OpenAI ``choices[0].message.tool_calls`` deltas or Anthropic
``tool_use`` content blocks — into :class:`base.ToolCall` records.
Malformed input raises :class:`ProviderError`.

Stubbed only: no network is touched here; both functions operate on
in-memory shapes.
"""


from __future__ import annotations

__all__ = [
    "Provider",
    "ProviderError",
    "ToolCall",
    "negotiate",
    "parse_tool_calls",
]

import json
from typing import Any

from .base import Provider, ProviderError, ToolCall


#: Explicit provider.name -> wire family mapping. Anything else falls
#: back to the OpenAI function-calling shape (documented above).
_TOOL_FAMILIES: dict[str, str] = {
    "anthropic": "anthropic",
    "claude": "anthropic",
}


def _family_of(provider: Provider) -> str:
    """Return ``"anthropic"`` or ``"openai"`` for ``provider``."""
    name = (getattr(provider, "name", "") or "").lower()
    return _TOOL_FAMILIES.get(name, "openai")


def _check_tool_spec(index: int, tool: Any) -> dict[str, Any]:
    if not isinstance(tool, dict):
        raise ProviderError(
            f"tools[{index}] must be a dict, got {type(tool).__name__}")
    name = tool.get("name")
    if not isinstance(name, str) or not name:
        raise ProviderError(
            f"tools[{index}] must define a non-empty string 'name'")
    parameters = tool.get("parameters", {"type": "object"})
    if not isinstance(parameters, dict):
        raise ProviderError(
            f"tools[{index}]['parameters'] must be a JSON-schema dict")
    description = tool.get("description", "")
    if not isinstance(description, str):
        raise ProviderError(
            f"tools[{index}]['description'] must be a string")
    return {"name": name, "description": description,
            "parameters": parameters}


def negotiate(provider: Provider, tools: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the tool-definition payload for ``provider``.

    Calls ``provider.require_capability("tool_calling")`` first, so
    providers without tool support raise :class:`ProviderError` before
    any payload is built. Returns the wire payload dict (ready to merge
    into a chat request).
    """
    provider.require_capability("tool_calling")
    if not isinstance(tools, list) or not tools:
        raise ProviderError("tools must be a non-empty list of tool specs")
    specs = [_check_tool_spec(i, tool) for i, tool in enumerate(tools)]
    if _family_of(provider) == "anthropic":
        return {"tools": [
            {"name": spec["name"],
             "description": spec["description"],
             "input_schema": spec["parameters"]}
            for spec in specs
        ]}
    return {"tools": [
        {"type": "function",
         "function": {"name": spec["name"],
                      "description": spec["description"],
                      "parameters": spec["parameters"]}}
        for spec in specs
    ]}


def _parse_openai_tool_calls(raw: dict[str, Any]) -> list[ToolCall]:
    try:
        message = raw["choices"][0]["message"]
        entries = message.get("tool_calls") or []
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError(
            "Malformed OpenAI tool-call response: "
            "expected choices[0].message.tool_calls.") from exc
    if not isinstance(entries, list):
        raise ProviderError(
            "Malformed OpenAI tool-call response: 'tool_calls' is not a list.")
    calls: list[ToolCall] = []
    for index, entry in enumerate(entries):
        where = f"tool_calls[{index}]"
        try:
            function = entry["function"]
            name = function["name"]
            raw_args = function.get("arguments", "{}")
        except (KeyError, TypeError) as exc:
            raise ProviderError(
                f"Malformed OpenAI {where}: expected function.name/"
                "function.arguments.") from exc
        if not isinstance(name, str) or not name:
            raise ProviderError(f"Malformed OpenAI {where}: empty name.")
        if isinstance(raw_args, dict):
            arguments = raw_args
        elif isinstance(raw_args, str):
            try:
                arguments = json.loads(raw_args) if raw_args.strip() else {}
            except ValueError as exc:
                raise ProviderError(
                    f"Malformed OpenAI {where}: arguments are not valid "
                    "JSON.") from exc
        else:
            raise ProviderError(
                f"Malformed OpenAI {where}: arguments must be a JSON "
                "string or dict.")
        if not isinstance(arguments, dict):
            raise ProviderError(
                f"Malformed OpenAI {where}: arguments must decode to a "
                "JSON object.")
        calls.append(ToolCall(id=str(entry.get("id", "")),
                              name=name, arguments=arguments))
    return calls


def _parse_anthropic_tool_calls(raw: dict[str, Any]) -> list[ToolCall]:
    try:
        blocks = raw["content"]
    except (KeyError, TypeError) as exc:
        raise ProviderError(
            "Malformed Anthropic tool-call response: "
            "expected a 'content' block list.") from exc
    if not isinstance(blocks, list):
        raise ProviderError(
            "Malformed Anthropic tool-call response: 'content' is not a list.")
    calls: list[ToolCall] = []
    for block in blocks:
        if not isinstance(block, dict) or block.get("type") != "tool_use":
            continue
        call_id = block.get("id", "")
        name = block.get("name", "")
        arguments = block.get("input", {})
        if not isinstance(name, str) or not name:
            raise ProviderError(
                "Malformed Anthropic tool_use block: empty name.")
        if not isinstance(arguments, dict):
            raise ProviderError(
                "Malformed Anthropic tool_use block: 'input' must be a "
                "JSON object.")
        calls.append(ToolCall(id=str(call_id), name=name,
                              arguments=arguments))
    return calls


def parse_tool_calls(provider: Provider, raw: Any) -> list[ToolCall]:
    """Normalize a raw tool-call response into :class:`ToolCall` records.

    OpenAI-family: ``raw["choices"][0]["message"]["tool_calls"]`` (the
    ``function.arguments`` JSON string is decoded to a dict).
    Anthropic: ``raw["content"]`` blocks with ``type == "tool_use"``.
    Malformed input raises :class:`ProviderError`.
    """
    if not isinstance(raw, dict):
        raise ProviderError(
            f"Malformed tool-call response: expected a dict, "
            f"got {type(raw).__name__}.")
    if _family_of(provider) == "anthropic":
        return _parse_anthropic_tool_calls(raw)
    return _parse_openai_tool_calls(raw)
