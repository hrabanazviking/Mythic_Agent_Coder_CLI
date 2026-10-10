"""Schema validation and path sandboxing for agent tool arguments.

Every tool call is validated against the JSON schema declared in its tool
definition (see ``mythic_agent.core.tool_schemas.get_agent_tools``) *before* it
executes. File-tool paths are additionally resolved against the workspace so
traversal and symlink escapes are rejected at the validation layer, not just
at execution time.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "Path",
    "SecurityError",
    "ValidationError",
    "get_agent_tools",
    "resolve_file",
    "sandbox_path",
    "validate_tool_args",
]

from pathlib import Path
from typing import Any

from .workspace import resolve_file
from .tool_schemas import get_agent_tools
from .exceptions import MythicSecurityError, MythicValidationError


class ValidationError(MythicValidationError, ValueError):
    """A tool argument failed schema or security validation."""


class SecurityError(MythicSecurityError, ValidationError):
    """A tool argument violated the workspace sandbox or a security rule."""


# Tools whose ``path`` argument must resolve inside the workspace.
_FILE_TOOLS = {
    "read_file",
    "write_file",
    "list_dir",
    "replace_file_content",
    "grep_search",
}

# Tools that create or modify files; get the stricter write-mode sandbox.
_WRITE_TOOLS = {"write_file", "replace_file_content"}


def _tool_schemas() -> dict[str, dict[str, Any]]:
    """JSON parameter schemas keyed by tool name, from the tool definitions."""
    return {tool["function"]["name"]: tool["function"]["parameters"] for tool in get_agent_tools()}


def _type_name(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if value is None:
        return "null"
    return type(value).__name__


def _check_value(value: Any, schema: dict[str, Any], label: str) -> None:
    kind = schema.get("type")
    if kind is not None:
        ok = {
            "string": isinstance(value, str),
            "object": isinstance(value, dict),
            "array": isinstance(value, list),
            "integer": isinstance(value, int) and not isinstance(value, bool),
            "number": isinstance(value, (int, float)) and not isinstance(value, bool),
            "boolean": isinstance(value, bool),
            "null": value is None,
        }.get(kind, True)
        if not ok:
            raise ValidationError(f"{label}: expected {kind}, got {_type_name(value)}")

    if "enum" in schema and value not in schema["enum"]:
        allowed = ", ".join(repr(option) for option in schema["enum"])
        raise ValidationError(f"{label}: {value!r} is not one of [{allowed}]")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise ValidationError(
                f"{label}: shorter than minimum length {schema['minLength']}"
            )
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise ValidationError(
                f"{label}: longer than maximum length {schema['maxLength']}"
            )

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValidationError(f"{label}: below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise ValidationError(f"{label}: above maximum {schema['maximum']}")

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        missing = [key for key in schema.get("required", []) if key not in value]
        if missing:
            raise ValidationError(
                f"{label}: missing required argument(s): {', '.join(sorted(missing))}"
            )
        if schema.get("additionalProperties") is False:
            unknown = sorted(set(value) - set(properties))
            if unknown:
                raise ValidationError(
                    f"{label}: unknown argument(s): {', '.join(unknown)}"
                )
        for key, item in value.items():
            if key in properties:
                _check_value(item, properties[key], f"{label}.{key}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise ValidationError(
                f"{label}: fewer than {schema['minItems']} item(s)"
            )
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ValidationError(
                f"{label}: more than {schema['maxItems']} item(s)"
            )
        items_schema = schema.get("items")
        if isinstance(items_schema, dict):
            for index, item in enumerate(value):
                _check_value(item, items_schema, f"{label}[{index}]")


def sandbox_path(root: Path, value: Any, *, write: bool = False) -> Path:
    """Resolve *value* against the workspace *root*, rejecting escapes.

    Resolves symlinks and ``..`` segments; raises :class:`SecurityError`
    when the result would land outside the workspace, when the value is not
    a usable path string, or (``write=True``) when it targets the workspace
    root or Git metadata.
    """
    try:
        return resolve_file(root, value, write=write)
    except ValueError as exc:
        raise SecurityError(f"path {value!r}: {exc}") from exc


def validate_tool_args(
    tool_name: str,
    args: dict[str, Any],
    *,
    workspace: Path | str | None = None,
) -> dict[str, Any]:
    """Validate *args* against *tool_name*'s declared JSON schema.

    Raises :class:`ValidationError` with a clear, dotted-path message on any
    failure (unknown tool, wrong type, missing/unknown argument, enum
    violation, bad nesting). When *workspace* is given, file-tool ``path``
    arguments are additionally sandbox-checked, raising :class:`SecurityError`
    on traversal or symlink escapes.

    Returns *args* unchanged on success so calls can be chained.
    """
    if not isinstance(args, dict):
        raise ValidationError(f"{tool_name}: arguments must be an object, got {_type_name(args)}")
    schemas = _tool_schemas()
    if tool_name not in schemas:
        raise ValidationError(f"Unknown tool: {tool_name}")
    _check_value(args, schemas[tool_name], tool_name)

    if workspace is not None and tool_name in _FILE_TOOLS:
        root = Path(workspace)
        sandbox_path(root, args["path"], write=tool_name in _WRITE_TOOLS)

    return args
