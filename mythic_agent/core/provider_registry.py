"""The provider registry as data (All-Features roadmap slice M-019).

Part II — The Provider Ocean — opens here. Every provider the app
ships is defined in ``mythic_agent/data/provider_registry.yaml``:
endpoint, auth style, model list, and capabilities, in a data file —
so a new OpenAI-compatible door is a registry entry, not a code
change (the universal adapter that consumes entries generically is
M-020). This module loads, validates, and renders that registry.

The honesty rules are enforced by :func:`validate_registry`:

* The registry cannot quietly gain or lose a door in this file
  alone: the slice's tests pin every entry against the live adapter
  classes in ``mythic_agent.providers`` (canonical name, default
  model, key env, endpoint default, live ``capabilities()``), so
  data and code cannot drift apart.
* ``endpoint`` is a real http(s) URL, or ``null`` — and ``null`` is
  allowed only for ``native_sdk`` providers, whose SDK owns the
  service address. No address is ever invented for them.
* ``auth_style`` and ``api_key_env`` must agree: a provider either
  reads its key from a named environment variable or needs none.
* The default model is always in the provider's own model list, and
  capabilities carry exactly the four contract flags
  (``mythic_agent.providers.base.Provider.CAPABILITY_FLAGS``) with
  boolean values.
* Aliases resolve to canonical names and never shadow one.
"""

from __future__ import annotations

__all__ = [
    "AUTH_STYLES",
    "CAPABILITY_FLAGS",
    "DIALECTS",
    "LOCALITIES",
    "REGISTRY_RESOURCE",
    "REGISTRY_SCHEMA",
    "REGISTRY_SLICE",
    "Any",
    "Dict",
    "List",
    "Optional",
    "ProviderDef",
    "ProviderRegistry",
    "Tuple",
    "load_registry",
    "render_markdown",
    "validate_registry",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the registry data file inside ``mythic_agent/data``.
REGISTRY_RESOURCE = "provider_registry.yaml"

#: The only schema this loader accepts.
REGISTRY_SCHEMA = "mythic.provider_registry/1"

#: The slice that owns this registry.
REGISTRY_SLICE = "M-019"

#: The provider dialects the registry knows.
DIALECTS = ("native_sdk", "ollama_native", "openai_compatible")

#: Where a provider's models live.
LOCALITIES = ("local", "remote")

#: How a provider authenticates: a key read from an env var, or none.
AUTH_STYLES = ("api_key_env", "none")

#: The capability contract flags, in contract order.
CAPABILITY_FLAGS = ("streaming", "tool_calling", "vision", "json_mode")

_ADAPTER_RE = re.compile(r"^[a-z_][a-z0-9_.]*:[A-Z][A-Za-z0-9]*$")
_ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_URL_RE = re.compile(r"^https?://\S+$")


@dataclass(frozen=True)
class ProviderDef:
    """One provider, as defined in the registry data."""

    name: str
    title: str
    adapter: str
    dialect: str
    locality: str
    endpoint: Optional[str]
    auth_style: str
    api_key_env: Optional[str]
    default_model: str
    models: Tuple[str, ...]
    capabilities: Tuple[Tuple[str, bool], ...]
    notes: str

    def capability(self, flag: str) -> bool:
        """The recorded value of capability *flag* (KeyError if absent)."""
        for name, value in self.capabilities:
            if name == flag:
                return value
        raise KeyError(f"no capability {flag!r}")


@dataclass(frozen=True)
class ProviderRegistry:
    """The validated registry: provider definitions plus aliases."""

    source_note: str
    extension_rule: str
    providers: Tuple[ProviderDef, ...]
    aliases: Tuple[Tuple[str, str], ...]

    def names(self) -> Tuple[str, ...]:
        """Every canonical provider name, in registry (sorted) order."""
        return tuple(p.name for p in self.providers)

    def provider(self, name: str) -> ProviderDef:
        """Return the provider named *name*, resolving aliases.

        Raises KeyError for a name that is neither canonical nor an
        alias — an unknown door is unknown, never guessed.
        """
        key = (name or "").strip().lower()
        canonical = dict(self.aliases).get(key, key)
        for provider in self.providers:
            if provider.name == canonical:
                return provider
        raise KeyError(f"no provider {name!r}")

    def by_dialect(self, dialect: str) -> Tuple[ProviderDef, ...]:
        """Every provider speaking *dialect*, in registry order."""
        return tuple(p for p in self.providers if p.dialect == dialect)

    def by_locality(self, locality: str) -> Tuple[ProviderDef, ...]:
        """Every provider whose models live at *locality*."""
        return tuple(p for p in self.providers if p.locality == locality)


def validate_registry(data: Any) -> List[str]:
    """Return a list of human-readable problems with registry *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"registry root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != REGISTRY_SCHEMA:
        problems.append(
            f"schema must be {REGISTRY_SCHEMA!r}, got {data.get('schema')!r}"
        )
    if data.get("registry_slice") != REGISTRY_SLICE:
        problems.append(
            f"registry_slice must be {REGISTRY_SLICE!r}, "
            f"got {data.get('registry_slice')!r}"
        )
    for key in ("source_note", "extension_rule"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")

    providers = data.get("providers")
    if not isinstance(providers, list) or not providers:
        problems.append("providers must be a non-empty list")
        return problems
    names: List[str] = []
    for entry in providers:
        if not isinstance(entry, dict):
            problems.append(f"provider entry is not a mapping: {entry!r}")
            continue
        name = entry.get("name")
        label = name if isinstance(name, str) and name else repr(entry)[:60]
        if not isinstance(name, str) or not name or name != name.strip().lower():
            problems.append(f"provider {label}: name must be a lowercase string")
        elif name in names:
            problems.append(f"provider {label}: duplicate provider name")
        else:
            names.append(name)
        if not isinstance(entry.get("title"), str) or not entry["title"]:
            problems.append(f"provider {label}: title must be non-empty")
        adapter = entry.get("adapter")
        if not isinstance(adapter, str) or not _ADAPTER_RE.match(adapter):
            problems.append(
                f"provider {label}: adapter must look like "
                f"'module.path:ClassName', got {adapter!r}"
            )
        dialect = entry.get("dialect")
        if dialect not in DIALECTS:
            problems.append(
                f"provider {label}: dialect must be one of {DIALECTS}, "
                f"got {dialect!r}"
            )
        if entry.get("locality") not in LOCALITIES:
            problems.append(
                f"provider {label}: locality must be one of {LOCALITIES}, "
                f"got {entry.get('locality')!r}"
            )
        endpoint = entry.get("endpoint")
        if dialect == "native_sdk":
            if endpoint is not None:
                problems.append(
                    f"provider {label}: native_sdk providers record endpoint "
                    "null (their SDK owns the service address); an address "
                    "must not be invented"
                )
        elif not isinstance(endpoint, str) or not _URL_RE.match(endpoint):
            problems.append(
                f"provider {label}: endpoint must be an http(s) URL, "
                f"got {endpoint!r}"
            )
        auth_style = entry.get("auth_style")
        if auth_style not in AUTH_STYLES:
            problems.append(
                f"provider {label}: auth_style must be one of {AUTH_STYLES}, "
                f"got {auth_style!r}"
            )
        key_env = entry.get("api_key_env")
        if auth_style == "api_key_env":
            if not isinstance(key_env, str) or not _ENV_RE.match(key_env):
                problems.append(
                    f"provider {label}: auth_style 'api_key_env' requires an "
                    f"api_key_env naming an env var, got {key_env!r}"
                )
        elif auth_style == "none" and key_env is not None:
            problems.append(
                f"provider {label}: auth_style 'none' requires api_key_env "
                f"null, got {key_env!r}"
            )
        models = entry.get("models")
        if (
            not isinstance(models, list)
            or not models
            or not all(isinstance(m, str) and m for m in models)
        ):
            problems.append(
                f"provider {label}: models must be a non-empty list of "
                "non-empty strings"
            )
            models = []
        elif len(set(models)) != len(models):
            problems.append(f"provider {label}: models must not repeat a model")
        default_model = entry.get("default_model")
        if not isinstance(default_model, str) or not default_model:
            problems.append(f"provider {label}: default_model must be non-empty")
        elif models and default_model not in models:
            problems.append(
                f"provider {label}: default_model {default_model!r} must be "
                "in its own models list"
            )
        capabilities = entry.get("capabilities")
        if not isinstance(capabilities, dict):
            problems.append(f"provider {label}: capabilities must be a mapping")
        else:
            if set(capabilities) != set(CAPABILITY_FLAGS):
                problems.append(
                    f"provider {label}: capabilities must carry exactly the "
                    f"flags {CAPABILITY_FLAGS}, got {sorted(capabilities)}"
                )
            if not all(isinstance(v, bool) for v in capabilities.values()):
                problems.append(
                    f"provider {label}: capability values must be boolean"
                )
        if not isinstance(entry.get("notes"), str) or not entry["notes"]:
            problems.append(f"provider {label}: notes must be non-empty")
    if names != sorted(names):
        problems.append(
            "providers must be listed in sorted name order (the order "
            "the runtime registry lists them in)"
        )

    aliases = data.get("aliases")
    if not isinstance(aliases, dict) or not aliases:
        problems.append("aliases must be a non-empty mapping")
    else:
        for alias, canonical in aliases.items():
            if canonical not in names:
                problems.append(
                    f"alias {alias!r}: target {canonical!r} is not a "
                    "registered provider"
                )
            if alias in names:
                problems.append(
                    f"alias {alias!r}: an alias must not shadow a "
                    "canonical provider name"
                )
    return problems


def _to_registry(data: Dict[str, Any]) -> ProviderRegistry:
    return ProviderRegistry(
        source_note=data["source_note"],
        extension_rule=data["extension_rule"],
        providers=tuple(
            ProviderDef(
                name=p["name"],
                title=p["title"],
                adapter=p["adapter"],
                dialect=p["dialect"],
                locality=p["locality"],
                endpoint=p["endpoint"],
                auth_style=p["auth_style"],
                api_key_env=p["api_key_env"],
                default_model=p["default_model"],
                models=tuple(p["models"]),
                capabilities=tuple(
                    (flag, p["capabilities"][flag]) for flag in CAPABILITY_FLAGS
                ),
                notes=p["notes"],
            )
            for p in data["providers"]
        ),
        aliases=tuple(sorted(data["aliases"].items())),
    )


def load_registry(data: Optional[Dict[str, Any]] = None) -> ProviderRegistry:
    """Load and validate the shipped provider registry (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed registry.
    """
    raw = data if data is not None else load_resource(REGISTRY_RESOURCE)
    problems = validate_registry(raw)
    if problems:
        raise ValidationError(
            "provider registry failed validation: " + "; ".join(problems)
        )
    return _to_registry(raw)  # type: ignore[arg-type]


def render_markdown(registry: ProviderRegistry) -> str:
    """Render the registry as markdown: doors by dialect, then aliases."""
    local = registry.by_locality("local")
    remote = registry.by_locality("remote")
    lines = [
        "# The Provider Registry — providers as data",
        "",
        f"*Slice {REGISTRY_SLICE} of the All-Features road (Part II — "
        "The Provider Ocean).*",
        "",
        registry.source_note,
        "",
        f"**{len(registry.providers)} providers** "
        f"({len(local)} local, {len(remote)} remote), "
        f"{len(registry.aliases)} aliases.",
        "",
        f"*{registry.extension_rule}*",
        "",
    ]
    for dialect in DIALECTS:
        members = registry.by_dialect(dialect)
        if not members:
            continue
        lines.append(f"## Dialect: {dialect}")
        lines.append("")
        for provider in members:
            endpoint = provider.endpoint or "SDK-managed"
            auth = provider.api_key_env or "no key"
            flags = ", ".join(
                f"{flag}={'yes' if provider.capability(flag) else 'no'}"
                for flag in CAPABILITY_FLAGS
            )
            lines.append(
                f"- **{provider.name}** — {provider.title}: "
                f"`{endpoint}`, auth {auth}, default model "
                f"`{provider.default_model}`, models "
                f"{', '.join(provider.models)}; {flags}."
            )
        lines.append("")
    lines.append("## Aliases")
    lines.append("")
    for alias, canonical in registry.aliases:
        lines.append(
            f"- `{alias}` → **{canonical}** "
            f"({registry.provider(canonical).title})"
        )
    lines.append("")
    lines.append("## Canonical names")
    lines.append("")
    lines.append(", ".join(registry.names()))
    lines.append("")
    return "\n".join(lines)
