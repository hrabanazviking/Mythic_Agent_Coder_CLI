"""Language packs as data (All-Features roadmap slice M-068).

Part III — Code Intelligence. The roadmap's words for this
slice: "per-language toolchains (server commands, formatters,
test runners) declared in data; a new language is a pack, not
a patch."

Every language in the M-043 tree-sitter catalogue carries one
pack in ``mythic_agent/data/language_packs.yaml``: its file
extensions, its language server (name and stdio command), its
formatters, and its test runners. This module loads, validates,
and renders those packs, in the provider-registry pattern
(M-019).

The honesty rules are enforced by
:func:`validate_language_packs`:

* A pack's language must exist in the live M-043 catalogue
  (:mod:`mythic_agent.core.tree_sitter_foundation`), and its
  extensions must be exactly that catalogue entry's
  extensions — a pack can neither invent a language nor
  redraw its file map.
* Pack ids are sequential (``LP-01``, ``LP-02``, ...) and no
  language carries two packs.
* A server is either ``null`` — Mojo today, matching the LSP
  catalogue's honest absence of a Mojo server — or a name
  with a non-empty command. No server is ever invented here;
  the slice's tests pin every non-null server against the
  live :data:`mythic_agent.integrations.lsp.SERVERS` entry
  for its language.
* Formatter and test-runner names never repeat within a
  pack, and every declared command is non-empty. The tests
  pin the Python pack's formatter names against the format
  covenant's live candidates and its pytest runner against
  test intelligence's pytest detection, so the live-wired
  parts of the packs cannot drift from their consumers; the
  remaining formatters and runners are declared pack data,
  and each pack's ``notes`` say exactly which parts are
  live-wired and which are declared only.
"""

from __future__ import annotations

__all__ = [
    "PACKS_RESOURCE",
    "PACKS_SCHEMA",
    "PACKS_SLICE",
    "Any",
    "Dict",
    "LanguagePack",
    "LanguagePacks",
    "List",
    "Optional",
    "ToolCommand",
    "Tuple",
    "formatter_names",
    "languages",
    "load_language_packs",
    "pack_for_extension",
    "pack_for_language",
    "packs",
    "render_markdown",
    "server_command",
    "test_runner_names",
    "validate_language_packs",
]

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .tree_sitter_foundation import load_catalog as _load_ts_catalog
from .validation import ValidationError

#: Resource name of the packs data file inside ``mythic_agent/data``.
PACKS_RESOURCE = "language_packs.yaml"

#: The only schema this loader accepts.
PACKS_SCHEMA = "mythic.language_packs/1"

#: The slice that owns these packs.
PACKS_SLICE = "M-068"


@dataclass(frozen=True)
class ToolCommand:
    """One declared tool: a name and its command, as data."""

    name: str
    command: Tuple[str, ...]

    def record(self) -> Dict[str, Any]:
        return {"name": self.name, "command": list(self.command)}


@dataclass(frozen=True)
class LanguagePack:
    """One language's toolchain, as declared in the pack data."""

    id: str
    language: str
    title: str
    extensions: Tuple[str, ...]
    server: Optional[ToolCommand]
    formatters: Tuple[ToolCommand, ...]
    test_runners: Tuple[ToolCommand, ...]
    notes: str

    def record(self) -> Dict[str, Any]:
        return {
            "id": self.id, "language": self.language,
            "title": self.title,
            "extensions": list(self.extensions),
            "server": self.server.record() if self.server else None,
            "formatters": [f.record() for f in self.formatters],
            "test_runners": [r.record() for r in self.test_runners],
            "notes": self.notes,
        }


@dataclass(frozen=True)
class LanguagePacks:
    """The validated language packs: one pack per language."""

    source_note: str
    extension_rule: str
    entries: Tuple[LanguagePack, ...]

    def languages(self) -> Tuple[str, ...]:
        """Every packed language, in pack (catalogue) order."""
        return tuple(p.language for p in self.entries)

    def pack_for_language(self, name: str) -> Optional[LanguagePack]:
        """The pack for *name*, or None — unknown is never guessed."""
        key = (name or "").strip().lower()
        for pack in self.entries:
            if pack.language == key:
                return pack
        return None

    def pack_for_extension(self, extension: str) -> Optional[LanguagePack]:
        """The pack claiming *extension* (e.g. ``.py``), or None."""
        key = (extension or "").strip().lower()
        if not key.startswith("."):
            key = "." + key
        for pack in self.entries:
            if key in pack.extensions:
                return pack
        return None

    def server_command(self, language: str) -> Optional[Tuple[str, ...]]:
        """The server command for *language*.

        None when the language is unknown or its pack honestly
        declares no server (Mojo).
        """
        pack = self.pack_for_language(language)
        if pack is None or pack.server is None:
            return None
        return pack.server.command

    def formatter_names(self, language: str) -> Tuple[str, ...]:
        """The formatter names declared for *language*."""
        pack = self.pack_for_language(language)
        if pack is None:
            return ()
        return tuple(f.name for f in pack.formatters)

    def test_runner_names(self, language: str) -> Tuple[str, ...]:
        """The test-runner names declared for *language*."""
        pack = self.pack_for_language(language)
        if pack is None:
            return ()
        return tuple(r.name for r in pack.test_runners)


def _check_tool_list(entry: Dict[str, Any], key: str, label: str,
                     problems: List[str]) -> None:
    """Validate one pack's formatter/runner list into *problems*."""
    tools = entry.get(key)
    if not isinstance(tools, list):
        problems.append(f"pack {label}: {key} must be a list")
        return
    seen: List[str] = []
    for tool in tools:
        if not isinstance(tool, dict):
            problems.append(f"pack {label}: {key} entry is not a "
                            f"mapping: {tool!r}")
            continue
        name = tool.get("name")
        if not isinstance(name, str) or not name:
            problems.append(f"pack {label}: {key} entry needs a "
                            "non-empty name")
        elif name in seen:
            problems.append(f"pack {label}: duplicate {key} name "
                            f"{name!r} within the pack")
        else:
            seen.append(name)
        command = tool.get("command")
        if (not isinstance(command, list) or not command
                or not all(isinstance(c, str) and c for c in command)):
            problems.append(f"pack {label}: {key} entry {name!r} "
                            "must carry a non-empty command")


def validate_language_packs(data: Any) -> List[str]:
    """Return a list of human-readable problems with packs *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"language packs root must be a mapping, got "
                f"{type(data).__name__}"]
    if data.get("schema") != PACKS_SCHEMA:
        problems.append(
            f"schema must be {PACKS_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("packs_slice") != PACKS_SLICE:
        problems.append(
            f"packs_slice must be {PACKS_SLICE!r}, "
            f"got {data.get('packs_slice')!r}")
    for key in ("source_note", "extension_rule"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")

    catalogue = _load_ts_catalog()
    by_language = {entry.language: entry for entry in catalogue.languages}

    entries = data.get("packs")
    if not isinstance(entries, list) or not entries:
        problems.append("packs must be a non-empty list")
        return problems
    seen_languages: List[str] = []
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"pack entry is not a mapping: {entry!r}")
            continue
        pid = entry.get("id")
        expected = f"LP-{position:02d}"
        if pid != expected:
            problems.append(
                f"pack entry {pid!r}: ids must be sequential, "
                f"expected {expected}")
        language = entry.get("language")
        label = language if isinstance(language, str) and language \
            else repr(entry)[:60]
        if not isinstance(language, str) or not language \
                or language != language.strip().lower():
            problems.append(
                f"pack {label}: language must be a lowercase string")
        elif language in seen_languages:
            problems.append(f"pack {label}: duplicate language")
        else:
            seen_languages.append(language)
        if not isinstance(entry.get("title"), str) or not entry["title"]:
            problems.append(f"pack {label}: title must be non-empty")
        extensions = entry.get("extensions")
        if not isinstance(extensions, list) or not extensions:
            problems.append(
                f"pack {label}: extensions must be a non-empty list")
        elif language in by_language:
            expected_exts = list(by_language[language].extensions)
            if extensions != expected_exts:
                problems.append(
                    f"pack {label}: extensions {extensions} must be "
                    f"exactly the M-043 catalogue's extensions for "
                    f"{language}, {expected_exts}")
        if isinstance(language, str) and language \
                and language not in by_language:
            problems.append(
                f"pack {label}: language {language!r} is absent from "
                "the live M-043 tree-sitter catalogue — a pack's "
                "language must exist in that catalogue")
        server = entry.get("server")
        if server is not None:
            if not isinstance(server, dict):
                problems.append(
                    f"pack {label}: server must be a mapping or null")
            else:
                if not isinstance(server.get("name"), str) \
                        or not server["name"]:
                    problems.append(
                        f"pack {label}: server needs a non-empty name")
                command = server.get("command")
                if (not isinstance(command, list) or not command
                        or not all(isinstance(c, str) and c
                                   for c in command)):
                    problems.append(
                        f"pack {label}: a non-null server must carry "
                        "a non-empty command")
        _check_tool_list(entry, "formatters", str(label), problems)
        _check_tool_list(entry, "test_runners", str(label), problems)
        if not isinstance(entry.get("notes"), str) or not entry["notes"]:
            problems.append(f"pack {label}: notes must be non-empty")
    return problems


def _to_tool(raw: Dict[str, Any]) -> ToolCommand:
    return ToolCommand(name=raw["name"], command=tuple(raw["command"]))


def _to_packs(data: Dict[str, Any]) -> LanguagePacks:
    return LanguagePacks(
        source_note=data["source_note"],
        extension_rule=data["extension_rule"],
        entries=tuple(
            LanguagePack(
                id=p["id"], language=p["language"], title=p["title"],
                extensions=tuple(p["extensions"]),
                server=_to_tool(p["server"]) if p["server"] else None,
                formatters=tuple(_to_tool(f) for f in p["formatters"]),
                test_runners=tuple(_to_tool(r) for r in p["test_runners"]),
                notes=p["notes"],
            )
            for p in data["packs"]
        ),
    )


_CACHE: Optional[LanguagePacks] = None


def load_language_packs(
        data: Optional[Dict[str, Any]] = None) -> LanguagePacks:
    """Load and validate the shipped language packs (or *data*).

    The shipped packs are loaded once and cached; passing *data*
    validates and builds that data fresh (the mutation road the
    tests use). Raises
    :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not well-formed.
    """
    global _CACHE
    if data is not None:
        problems = validate_language_packs(data)
        if problems:
            raise ValidationError(
                "language packs failed validation: "
                + "; ".join(problems))
        return _to_packs(data)
    if _CACHE is None:
        raw = load_resource(PACKS_RESOURCE)
        problems = validate_language_packs(raw)
        if problems:
            raise ValidationError(
                "language packs failed validation: "
                + "; ".join(problems))
        _CACHE = _to_packs(raw)  # type: ignore[arg-type]
    return _CACHE


def packs() -> Tuple[LanguagePack, ...]:
    """Every shipped pack, in pack (catalogue) order."""
    return load_language_packs().entries


def pack_for_language(name: str) -> Optional[LanguagePack]:
    """The shipped pack for *name*, or None."""
    return load_language_packs().pack_for_language(name)


def pack_for_extension(extension: str) -> Optional[LanguagePack]:
    """The shipped pack claiming *extension*, or None."""
    return load_language_packs().pack_for_extension(extension)


def languages() -> Tuple[str, ...]:
    """Every packed language, in pack (catalogue) order."""
    return load_language_packs().languages()


def server_command(language: str) -> Optional[Tuple[str, ...]]:
    """The shipped server command for *language*, or None."""
    return load_language_packs().server_command(language)


def formatter_names(language: str) -> Tuple[str, ...]:
    """The formatter names the shipped pack declares for *language*."""
    return load_language_packs().formatter_names(language)


def test_runner_names(language: str) -> Tuple[str, ...]:
    """The test-runner names the shipped pack declares for *language*."""
    return load_language_packs().test_runner_names(language)


def render_markdown(catalog: Optional[LanguagePacks] = None) -> str:
    """Render the packs as markdown, through the accessors.

    Built from :func:`packs`, :func:`languages`,
    :func:`server_command`, :func:`formatter_names`,
    :func:`test_runner_names`, and :func:`pack_for_extension`
    (the extension index), so the rendered page is computed
    from the same values the tests pin. A *catalog* argument
    renders that catalogue's own entries instead of the
    shipped packs.
    """
    if catalog is not None:
        entries = catalog.entries
        rule = catalog.extension_rule
        note = catalog.source_note
    else:
        entries = packs()
        loaded = load_language_packs()
        rule = loaded.extension_rule
        note = loaded.source_note
    lines = [
        "# Language Packs — per-language toolchains as data",
        "",
        f"*Slice {PACKS_SLICE} of the All-Features road "
        "(Part III — Code Intelligence).*",
        "",
        note,
        "",
        f"**{len(entries)} pack(s)** for: "
        + ", ".join(p.language for p in entries) + ".",
        "",
        f"*{rule}*",
        "",
    ]
    for pack in entries:
        if catalog is not None:
            command = catalog.server_command(pack.language)
            formatters = catalog.formatter_names(pack.language)
            runners = catalog.test_runner_names(pack.language)
        else:
            command = server_command(pack.language)
            formatters = formatter_names(pack.language)
            runners = test_runner_names(pack.language)
        server_text = "`" + " ".join(command) + "`" if command \
            else "no server (declared null, honestly)"
        lines.append(
            f"- **{pack.language}** ({pack.id}, {pack.title}): "
            f"extensions {', '.join(pack.extensions)}; server "
            f"{server_text}; formatters "
            f"{', '.join(formatters) or 'none'}; test runners "
            f"{', '.join(runners) or 'none'}. {pack.notes}")
    lines.append("")
    lines.append("## Extension index")
    lines.append("")
    for pack in entries:
        for extension in pack.extensions:
            if catalog is not None:
                owner = catalog.pack_for_extension(extension)
            else:
                owner = pack_for_extension(extension)
            lines.append(
                f"- `{extension}` → "
                f"**{owner.language if owner else 'none'}**")
    lines.append("")
    lines.append("Languages: " + ", ".join(
        catalog.languages() if catalog is not None else languages()))
    lines.append("")
    return "\n".join(lines)
