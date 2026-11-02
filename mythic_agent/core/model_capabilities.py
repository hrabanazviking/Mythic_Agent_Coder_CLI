"""Capability truth per model (All-Features roadmap slice M-027).

Part II — The Provider Ocean — continues here. What a *model* can do
(context size, tool use, vision, reasoning, max output) is stored per
model in ``mythic_agent/data/model_capabilities.yaml`` and shown
before selection — never guessed: a capability with no in-tree
evidence is recorded as ``null`` and rendered as the word "unknown".

The honesty rules are enforced by :func:`validate_capabilities` and
pinned by the slice's tests:

* Exactly one record exists for every distinct model listed in the
  M-019 provider registry; a model listed by several providers
  carries all of them in its ``providers`` list.
* Context size and the tool_calling / vision / streaming / json_mode
  flags come only from the static model registry
  (``mythic_agent.providers.model_registry``) for models that
  registry knows. Provider-level capabilities from the provider
  registry are deliberately NOT inherited here: a provider door's
  flags describe the door, not each model behind it — per-model
  truth is the whole point of this slice. (This core loader imports
  no provider module; the cross-check against the live registries
  lives in the slice's tests.)
* ``reasoning`` is true only where in-tree evidence names the model
  (deepseek-reasoner); every other model's reasoning is unknown.
* ``max_output_tokens`` is unknown for every model in this file: no
  documented per-model max-output value exists in the tree, and no
  vendor number is invented from memory.
* Local placeholder names (a name standing for whatever model a
  local server was launched with) are all-unknown, by design.
* An unlisted model resolves through
  :meth:`ModelCapabilities.for_model` to an all-unknown record —
  never a guessed record, and never a crash.
"""

from __future__ import annotations

__all__ = [
    "CAPABILITIES_RESOURCE",
    "CAPABILITIES_SCHEMA",
    "CAPABILITIES_SLICE",
    "CAPABILITY_FIELDS",
    "FLAG_FIELDS",
    "TOKEN_FIELDS",
    "Any",
    "Dict",
    "List",
    "ModelCapabilities",
    "ModelCapability",
    "Optional",
    "Tuple",
    "load_capabilities",
    "render_markdown",
    "validate_capabilities",
]

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the capabilities data file inside ``mythic_agent/data``.
CAPABILITIES_RESOURCE = "model_capabilities.yaml"

#: The only schema this loader accepts.
CAPABILITIES_SCHEMA = "mythic.model_capabilities/1"

#: The slice that owns this data.
CAPABILITIES_SLICE = "M-027"

#: Every capability field a record carries, in record order.
CAPABILITY_FIELDS = (
    "context_tokens",
    "max_output_tokens",
    "tool_calling",
    "vision",
    "reasoning",
    "streaming",
    "json_mode",
)

#: The capability fields whose values are tri-state (bool or null).
FLAG_FIELDS = ("tool_calling", "vision", "reasoning", "streaming", "json_mode")

#: The capability fields whose values are token counts (positive int or null).
TOKEN_FIELDS = ("context_tokens", "max_output_tokens")

#: The exact field set every record must carry — no more, no fewer.
_RECORD_FIELDS = (
    ("model", "providers") + CAPABILITY_FIELDS + ("source", "notes")
)


@dataclass(frozen=True)
class ModelCapability:
    """One model's capability truth: known values, or None (unknown)."""

    model: str
    providers: Tuple[str, ...]
    context_tokens: Optional[int]
    max_output_tokens: Optional[int]
    tool_calling: Optional[bool]
    vision: Optional[bool]
    reasoning: Optional[bool]
    streaming: Optional[bool]
    json_mode: Optional[bool]
    source: str
    notes: str

    def capability(self, field: str) -> Any:
        """The recorded value of capability *field* (KeyError if absent)."""
        if field not in CAPABILITY_FIELDS:
            raise KeyError(f"no capability {field!r}")
        return getattr(self, field)


def _unknown_record(name: str) -> ModelCapability:
    """The all-unknown record for a model this data does not list."""
    return ModelCapability(
        model=name,
        providers=(),
        context_tokens=None,
        max_output_tokens=None,
        tool_calling=None,
        vision=None,
        reasoning=None,
        streaming=None,
        json_mode=None,
        source=(
            "No in-tree source: this model is not listed in "
            "mythic_agent/data/model_capabilities.yaml, so every "
            "capability is unknown (null), never guessed"
        ),
        notes=(
            "Unlisted model — shown as all-unknown before selection; "
            "a model becomes known here only by being listed with "
            "in-tree evidence."
        ),
    )


@dataclass(frozen=True)
class ModelCapabilities:
    """The validated per-model capability truth."""

    source_note: str
    records: Tuple[ModelCapability, ...]

    def models(self) -> Tuple[str, ...]:
        """Every listed model name, in data order."""
        return tuple(r.model for r in self.records)

    def for_model(self, name: str) -> ModelCapability:
        """Return the record for *name*.

        An unlisted model returns an all-unknown record — unknown is
        unknown, never guessed, and never a KeyError crash.
        """
        key = (name or "").strip()
        for record in self.records:
            if record.model == key:
                return record
        return _unknown_record(key)

    def by_provider(self, name: str) -> Tuple[ModelCapability, ...]:
        """Every record listed by provider *name*, in data order."""
        key = (name or "").strip()
        return tuple(r for r in self.records if key in r.providers)

    def known_context(self, model: str) -> Optional[int]:
        """The known context size for *model*, or None when unknown."""
        return self.for_model(model).context_tokens


def validate_capabilities(data: Any) -> List[str]:
    """Return a list of human-readable problems with capabilities *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"capabilities root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != CAPABILITIES_SCHEMA:
        problems.append(
            f"schema must be {CAPABILITIES_SCHEMA!r}, got {data.get('schema')!r}"
        )
    if data.get("capabilities_slice") != CAPABILITIES_SLICE:
        problems.append(
            f"capabilities_slice must be {CAPABILITIES_SLICE!r}, "
            f"got {data.get('capabilities_slice')!r}"
        )
    if not isinstance(data.get("source_note"), str) or not data["source_note"]:
        problems.append("source_note must be a non-empty string")

    models = data.get("models")
    if not isinstance(models, list) or not models:
        problems.append("models must be a non-empty list")
        return problems
    seen: List[str] = []
    for entry in models:
        if not isinstance(entry, dict):
            problems.append(f"model entry is not a mapping: {entry!r}")
            continue
        model = entry.get("model")
        label = model if isinstance(model, str) and model else repr(entry)[:60]
        if set(entry) != set(_RECORD_FIELDS):
            problems.append(
                f"model {label}: record must carry exactly the fields "
                f"{_RECORD_FIELDS}, got {sorted(entry)}"
            )
        if not isinstance(model, str) or not model:
            problems.append(f"model {label}: model must be a non-empty string")
        elif model in seen:
            problems.append(f"model {label}: duplicate model record")
        else:
            seen.append(model)
        providers = entry.get("providers")
        if (
            not isinstance(providers, list)
            or not providers
            or not all(isinstance(p, str) and p for p in providers)
        ):
            problems.append(
                f"model {label}: providers must be a non-empty list of "
                "non-empty strings"
            )
        elif len(set(providers)) != len(providers):
            problems.append(f"model {label}: providers must not repeat a provider")
        for field in TOKEN_FIELDS:
            value = entry.get(field)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value <= 0
            ):
                problems.append(
                    f"model {label}: {field} must be a positive int or "
                    f"null (unknown), got {value!r}"
                )
        for field in FLAG_FIELDS:
            value = entry.get(field)
            if value is not None and not isinstance(value, bool):
                problems.append(
                    f"model {label}: {field} must be true, false, or "
                    f"null (unknown), got {value!r}"
                )
        for key in ("source", "notes"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"model {label}: {key} must be non-empty")
    return problems


def _to_capabilities(data: Dict[str, Any]) -> ModelCapabilities:
    return ModelCapabilities(
        source_note=data["source_note"],
        records=tuple(
            ModelCapability(
                model=r["model"],
                providers=tuple(r["providers"]),
                context_tokens=r["context_tokens"],
                max_output_tokens=r["max_output_tokens"],
                tool_calling=r["tool_calling"],
                vision=r["vision"],
                reasoning=r["reasoning"],
                streaming=r["streaming"],
                json_mode=r["json_mode"],
                source=r["source"],
                notes=r["notes"],
            )
            for r in data["models"]
        ),
    )


def load_capabilities(
    data: Optional[Dict[str, Any]] = None,
) -> ModelCapabilities:
    """Load and validate the shipped model capabilities (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not well-formed.
    """
    raw = data if data is not None else load_resource(CAPABILITIES_RESOURCE)
    problems = validate_capabilities(raw)
    if problems:
        raise ValidationError(
            "model capabilities failed validation: " + "; ".join(problems)
        )
    return _to_capabilities(raw)  # type: ignore[arg-type]


def _render_value(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def _render_record(record: ModelCapability) -> List[str]:
    lines = [f"### {record.model}", ""]
    providers = ", ".join(record.providers) if record.providers else "unknown"
    lines.append(f"- providers: {providers}")
    for field in CAPABILITY_FIELDS:
        lines.append(f"- {field}: {_render_value(record.capability(field))}")
    lines.append(f"- source: {record.source}")
    lines.append(f"- notes: {record.notes}")
    lines.append("")
    return lines


def render_markdown(capabilities: ModelCapabilities) -> str:
    """Render the capability truth as markdown, shown before selection.

    Every field of every record is rendered; a null capability
    renders as the word "unknown". The provider index is built from
    :meth:`ModelCapabilities.by_provider`, the context summary from
    :meth:`ModelCapabilities.known_context` over
    :meth:`ModelCapabilities.models`, and the closing example shows
    an unlisted model through :meth:`ModelCapabilities.for_model` —
    all-unknown, never guessed.
    """
    lines = [
        "# Capability Truth Per Model — shown before selection",
        "",
        f"*Slice {CAPABILITIES_SLICE} of the All-Features road "
        "(Part II — The Provider Ocean).*",
        "",
        capabilities.source_note,
        "",
        f"**{len(capabilities.records)} models**: "
        + ", ".join(capabilities.models()),
        "",
        "## Every model, every field",
        "",
    ]
    for record in capabilities.records:
        lines.extend(_render_record(record))
    lines.append("## Models by provider")
    lines.append("")
    provider_names = sorted(
        {p for record in capabilities.records for p in record.providers}
    )
    for provider in provider_names:
        members = capabilities.by_provider(provider)
        lines.append(
            f"- **{provider}**: "
            + ", ".join(record.model for record in members)
        )
    lines.append("")
    lines.append("## Known context sizes")
    lines.append("")
    for model in capabilities.models():
        context = capabilities.known_context(model)
        lines.append(f"- {model}: {_render_value(context)}")
    lines.append("")
    lines.append("## An unlisted model is unknown, never guessed")
    lines.append("")
    lines.extend(_render_record(capabilities.for_model("no-such-model")))
    return "\n".join(lines)
