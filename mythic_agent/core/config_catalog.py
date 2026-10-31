"""The Config Catalogue (All-Features roadmap slice M-009).

Config archaeology, frozen as validated data: every current setting
(top-level, ``github.*``, ``runtime.*``, and the config-managed keys),
every environment variable the package names, and every file the
configuration system reads or writes — each with its source in the
tree and what it does.

This catalogue is the compatibility contract for Part VIII's settings
redesign: a redesign may move or rename an entry only with a
migration, never silently. The tests cross-check the catalogue
against the live tree (the defaults files, ``CONFIG_SCHEMA``, and a
literal scan for environment variables), so a new setting, key, or
variable cannot land uncatalogued.

Data lives in ``mythic_agent/data/config_catalog.yaml``.
"""

from __future__ import annotations

__all__ = [
    "CATALOG_RESOURCE",
    "CATALOG_SCHEMA",
    "Any",
    "CatalogFile",
    "ConfigCatalog",
    "Dict",
    "EnvVar",
    "List",
    "Optional",
    "Setting",
    "load_catalog",
    "render_markdown",
    "validate_catalog",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the catalogue data file inside ``mythic_agent/data``.
CATALOG_RESOURCE = "config_catalog.yaml"

#: The only schema this loader accepts.
CATALOG_SCHEMA = "mythic.config_catalog/1"

SETTING_SCOPES = ("top-level", "github", "runtime", "managed")
ENV_KINDS = ("override", "secret", "state-dir", "mode", "marker", "system")
FILE_KINDS = (
    "package-data",
    "user-config",
    "legacy-user-config",
    "lock",
    "recovery",
    "state-dir",
    "log",
    "workspace-instruction",
)

_SETTING_ID_RE = re.compile(r"^S-\d{2}$")
_ENV_ID_RE = re.compile(r"^V-\d{2}$")
_FILE_ID_RE = re.compile(r"^F-\d{2}$")


@dataclass(frozen=True)
class Setting:
    """One catalogued configuration setting."""

    id: str
    name: str
    scope: str
    type: str
    default: str
    source: str
    effect: str


@dataclass(frozen=True)
class EnvVar:
    """One catalogued environment variable."""

    id: str
    name: str
    kind: str
    effect: str
    secret: bool
    source: str


@dataclass(frozen=True)
class CatalogFile:
    """One catalogued file the configuration system touches."""

    id: str
    name: str
    kind: str
    path: str
    role: str
    names: Tuple[str, ...]


@dataclass(frozen=True)
class ConfigCatalog:
    """The validated config catalogue: settings + env vars + files."""

    catalogued: str
    scope_note: str
    settings: Tuple[Setting, ...]
    env_vars: Tuple[EnvVar, ...]
    files: Tuple[CatalogFile, ...]

    def setting_names(self) -> Tuple[str, ...]:
        """Every catalogued setting name, in catalogue order."""
        return tuple(s.name for s in self.settings)

    def env_names(self) -> Tuple[str, ...]:
        """Every catalogued environment variable name, in order."""
        return tuple(v.name for v in self.env_vars)

    def secret_env_names(self) -> Tuple[str, ...]:
        """The environment variables that carry secrets."""
        return tuple(v.name for v in self.env_vars if v.secret)

    def counts(self) -> Tuple[int, int, int]:
        """(settings, env vars, files) as catalogued."""
        return (len(self.settings), len(self.env_vars), len(self.files))


def _check_entries(entries: Any, label: str, id_re: Any, prefix: str,
                   fields: Tuple[str, ...], problems: List[str]) -> List[Dict[str, Any]]:
    if not isinstance(entries, list) or not entries:
        problems.append(f"{label} must be a non-empty list")
        return []
    seen: set = set()
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"{label} entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"{prefix}-{position:02d}"
        if not isinstance(eid, str) or not id_re.match(eid):
            problems.append(f"{label} entry {eid!r}: id must look like '{prefix}-01'")
        elif eid != expected:
            problems.append(
                f"{label} entry {eid}: ids must be sequential, expected {expected}"
            )
        for key in fields:
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"{label} entry {eid}: {key} must be non-empty")
        name = entry.get("name")
        if isinstance(name, str):
            if name in seen:
                problems.append(f"{label} entry {name!r} is named twice")
            seen.add(name)
    return entries


def validate_catalog(data: Any) -> List[str]:
    """Return a list of human-readable problems with catalogue *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"catalogue root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != CATALOG_SCHEMA:
        problems.append(
            f"schema must be {CATALOG_SCHEMA!r}, got {data.get('schema')!r}"
        )
    if data.get("slice") != "M-009":
        problems.append(f"slice must be 'M-009', got {data.get('slice')!r}")
    for key in ("catalogued", "scope_note"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")
    if isinstance(data.get("scope_note"), str) and "Part VIII" not in data["scope_note"]:
        problems.append("scope_note must name Part VIII (the contract's consumer)")

    settings = _check_entries(
        data.get("settings"), "settings", _SETTING_ID_RE, "S",
        ("name", "scope", "type", "default", "source", "effect"), problems,
    )
    for entry in settings:
        if isinstance(entry, dict) and entry.get("scope") not in SETTING_SCOPES:
            problems.append(
                f"setting {entry.get('name')!r}: scope {entry.get('scope')!r} "
                f"not in {SETTING_SCOPES}"
            )
    envs = _check_entries(
        data.get("env_vars"), "env_vars", _ENV_ID_RE, "V",
        ("name", "kind", "effect", "source"), problems,
    )
    for entry in envs:
        if not isinstance(entry, dict):
            continue
        if entry.get("kind") not in ENV_KINDS:
            problems.append(
                f"env var {entry.get('name')!r}: kind {entry.get('kind')!r} "
                f"not in {ENV_KINDS}"
            )
        if not isinstance(entry.get("secret"), bool):
            problems.append(f"env var {entry.get('name')!r}: secret must be a boolean")
    files = _check_entries(
        data.get("files"), "files", _FILE_ID_RE, "F",
        ("name", "kind", "path", "role"), problems,
    )
    for entry in files:
        if not isinstance(entry, dict):
            continue
        if entry.get("kind") not in FILE_KINDS:
            problems.append(
                f"file {entry.get('name')!r}: kind {entry.get('kind')!r} "
                f"not in {FILE_KINDS}"
            )
        names = entry.get("names")
        if not isinstance(names, list) or any(not isinstance(n, str) or not n for n in names):
            problems.append(f"file {entry.get('name')!r}: names must be a list of strings")
    return problems


def _to_catalog(data: Dict[str, Any]) -> ConfigCatalog:
    return ConfigCatalog(
        catalogued=data["catalogued"],
        scope_note=data["scope_note"],
        settings=tuple(
            Setting(id=s["id"], name=s["name"], scope=s["scope"], type=s["type"],
                    default=s["default"], source=s["source"], effect=s["effect"])
            for s in data["settings"]
        ),
        env_vars=tuple(
            EnvVar(id=v["id"], name=v["name"], kind=v["kind"], effect=v["effect"],
                   secret=v["secret"], source=v["source"])
            for v in data["env_vars"]
        ),
        files=tuple(
            CatalogFile(id=f["id"], name=f["name"], kind=f["kind"], path=f["path"],
                        role=f["role"], names=tuple(f["names"]))
            for f in data["files"]
        ),
    )


def load_catalog(data: Optional[Dict[str, Any]] = None) -> ConfigCatalog:
    """Load and validate the shipped config catalogue (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed catalogue.
    """
    raw = data if data is not None else load_resource(CATALOG_RESOURCE)
    problems = validate_catalog(raw)
    if problems:
        raise ValidationError(
            "config catalogue failed validation: " + "; ".join(problems)
        )
    return _to_catalog(raw)  # type: ignore[arg-type]


def render_markdown(catalog: ConfigCatalog) -> str:
    """Render the catalogue as markdown: settings, env vars, files.

    Built from :meth:`ConfigCatalog.counts`,
    :meth:`ConfigCatalog.setting_names`, and
    :meth:`ConfigCatalog.secret_env_names`, so the rendered page is
    computed from the same accessors the tests pin.
    """
    n_settings, n_env, n_files = catalog.counts()
    lines = [
        "# Config Catalogue — the compatibility contract (M-009)",
        "",
        f"*Catalogued {catalog.catalogued}: {n_settings} settings, "
        f"{n_env} environment variables, {n_files} files.*",
        "",
        catalog.scope_note,
        "",
        "## Settings",
        "",
    ]
    by_name = {s.name: s for s in catalog.settings}
    for name in catalog.setting_names():
        s = by_name[name]
        lines.append(
            f"- {s.id} `{s.name}` ({s.scope}, {s.type}, default {s.default}) — "
            f"{s.effect} [{s.source}]"
        )
    lines += ["", "## Environment variables", ""]
    secrets = set(catalog.secret_env_names())
    vars_by_name = {v.name: v for v in catalog.env_vars}
    for name in catalog.env_names():
        v = vars_by_name[name]
        mark = " (secret)" if v.name in secrets else ""
        lines.append(f"- {v.id} `{v.name}` ({v.kind}){mark} — {v.effect} [{v.source}]")
    lines += ["", "## Files", ""]
    for f in catalog.files:
        extra = f" Names: {', '.join(f.names)}." if f.names else ""
        lines.append(f"- {f.id} `{f.path}` ({f.kind}) — {f.role}{extra}")
    lines.append("")
    return "\n".join(lines)
