"""Unified LLM provider abstraction layer (Slice 35).

Concrete providers live in :mod:`mythic_agent.providers.anthropic`,
:mod:`mythic_agent.providers.google` and
:mod:`mythic_agent.providers.ollama`. Use
:func:`mythic_agent.providers.registry.get_provider` to resolve a
provider by name.

The existing OpenAI-compatible path in ``mythic_agent.agents.llm`` is
untouched; this layer adds per-provider capability detection and
native adapters for providers whose APIs are not OpenAI-compatible.
"""
