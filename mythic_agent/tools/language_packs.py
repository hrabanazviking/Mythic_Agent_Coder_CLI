"""Language packs — the surface (M-068).

Part III — Code Intelligence. The roadmap's words for this
slice: "per-language toolchains (server commands, formatters,
test runners) declared in data; a new language is a pack, not
a patch."

The packs themselves are data, loaded and validated by
:mod:`mythic_agent.core.language_packs` from
``mythic_agent/data/language_packs.yaml`` — one pack per
language in the M-043 tree-sitter catalogue. What ships here,
in ``mythic_agent/tools/language_packs.py``, is the surface:

* **The account.** ``/langpacks show`` reports every pack's
  toolchain — its language server, formatters, and test
  runners, each with its declared command — and
  ``/langpacks <language>`` reports just that pack. An
  unknown language is refused plainly, naming the languages
  that do have packs.
* **Installed means on PATH.** Every declared binary carries
  a live ``installed`` check: :func:`shutil.which` on the
  command's first word, at report time. Installed is true or
  false from PATH, never claimed otherwise — a declared
  toolchain is data, and this machine either has the binary
  or it does not.
* **Nothing is executed.** Commands are only described and
  PATH-checked on this road; no server, formatter, or test
  runner is ever run by a language-packs report.
* **The surfaces.** ``Agent.language_packs(...)`` and
  ``/langpacks [show | <language>]`` on the terminal and TUI
  system-command roads, sharing this module's parser and
  formatter. The setting ``language_packs`` (on by default)
  closes the road plainly — a switched-off road does not
  even load the pack data.

Honesty rules, pinned by the slice's tests:

* **Declared is not installed.** A pack declares what a
  language's toolchain *is*; the ``installed`` flags say
  what this machine *has*, from PATH alone.
* **Server-less is named.** A pack whose data declares no
  server (Mojo) is reported with no server — never an
  invented one.
* **Unknown is refused, not guessed.** A language with no
  pack gets a plain refusal naming the packed languages.
"""

from __future__ import annotations

__all__ = [
    "PLAIN_EXPLANATION",
    "LANGUAGE_PACKS_SLICE",
    "USAGE",
    "LanguagePacksReport",
    "PackAccount",
    "ToolchainEntry",
    "enabled_from_config",
    "format_language_pack_report",
    "language_packs_report",
    "parse_langpacks_args",
    "render_markdown",
]

import shutil
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..core import language_packs as core_packs

LANGUAGE_PACKS_SLICE = "M-068"

PLAIN_EXPLANATION = (
    "Language packs declare each language's toolchain as "
    "data — its language server, its formatters, and its "
    "test runners — one pack per language, so a new "
    "language is a pack, not a patch. /langpacks show "
    "reports every pack's toolchain with a live check of "
    "which declared binaries this machine actually has on "
    "PATH, and /langpacks <language> reports just that "
    "pack. Nothing is executed on this road: commands are "
    "described and PATH-checked, never run."
)

USAGE = "Usage: /langpacks [show | <language>]"


def enabled_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """Language packs are on unless config says so."""
    if not config:
        return True
    return config.get("language_packs", True) is not False


# ---------------------------------------------------------------------------
# The account
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ToolchainEntry:
    """One declared tool, with its live PATH check."""

    name: str = ""
    command: Tuple[str, ...] = ()
    installed: bool = False

    def binary(self) -> str:
        """The binary this entry's command runs, or ''."""
        return self.command[0] if self.command else ""

    def command_text(self) -> str:
        """The declared command as one line of text."""
        return " ".join(self.command)

    def record(self) -> Dict[str, Any]:
        return {"name": self.name, "command": list(self.command),
                "installed": self.installed}


@dataclass
class PackAccount:
    """One pack's whole surface account."""

    id: str = ""
    language: str = ""
    title: str = ""
    extensions: Tuple[str, ...] = ()
    server: Optional[ToolchainEntry] = None
    formatters: List[ToolchainEntry] = field(default_factory=list)
    test_runners: List[ToolchainEntry] = field(default_factory=list)
    notes: str = ""

    def toolchain_entries(self) -> Tuple[ToolchainEntry, ...]:
        """Every declared tool in this pack: server, then tools."""
        entries: List[ToolchainEntry] = []
        if self.server is not None:
            entries.append(self.server)
        entries.extend(self.formatters)
        entries.extend(self.test_runners)
        return tuple(entries)

    def record(self) -> Dict[str, Any]:
        return {"id": self.id, "language": self.language,
                "title": self.title,
                "extensions": list(self.extensions),
                "server": self.server.record() if self.server else None,
                "formatters": [f.record() for f in self.formatters],
                "test_runners": [r.record() for r in self.test_runners],
                "notes": self.notes}


@dataclass
class LanguagePacksReport:
    """One language-packs call's whole account."""

    kind: str = "show"  # show | language
    status: str = "ok"  # ok | disabled | error
    packs: List[PackAccount] = field(default_factory=list)
    note: str = ""

    def totals(self) -> Tuple[int, int, int]:
        """(packs, declared tools, tools installed on PATH)."""
        tools = [entry for pack in self.packs
                 for entry in pack.toolchain_entries()]
        return (len(self.packs), len(tools),
                sum(1 for entry in tools if entry.installed))

    def pack_languages(self) -> Tuple[str, ...]:
        return tuple(p.language for p in self.packs)

    def record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "status": self.status,
                "packs": [p.record() for p in self.packs],
                "note": self.note}


def _entry(name: str, command: Tuple[str, ...]) -> ToolchainEntry:
    """One declared tool with its honest PATH check."""
    return ToolchainEntry(
        name=name, command=tuple(command),
        installed=bool(command) and shutil.which(command[0]) is not None)


def _account(language: str) -> Optional[PackAccount]:
    """One pack's surface account, built through the core accessors."""
    pack = core_packs.pack_for_language(language)
    if pack is None:
        return None
    server = None
    if pack.server is not None:
        server = _entry(pack.server.name,
                        core_packs.server_command(language) or ())
    by_name = {f.name: f.command for f in pack.formatters}
    formatters = [_entry(name, by_name[name])
                  for name in core_packs.formatter_names(language)]
    runner_by_name = {r.name: r.command for r in pack.test_runners}
    runners = [_entry(name, runner_by_name[name])
               for name in core_packs.test_runner_names(language)]
    return PackAccount(
        id=pack.id, language=pack.language, title=pack.title,
        extensions=pack.extensions, server=server,
        formatters=formatters, test_runners=runners, notes=pack.notes)


def _closed(kind: str) -> LanguagePacksReport:
    return LanguagePacksReport(
        kind=kind, status="disabled",
        note=("language packs are off (the language_packs "
              "setting), so the pack data was not even loaded"))


def language_packs_report(
        workspace: Any = None, mode: str = "show", *,
        language: Optional[str] = None,
        enabled: bool = True,
) -> LanguagePacksReport:
    """One language-packs account — every pack, or one language's.

    The pack data is package data, so *workspace* is accepted
    for surface symmetry with the neighbouring sight tools
    and is not read. Nothing is executed: declared commands
    are described and their binaries PATH-checked only. An
    unknown language is an honest ``error`` report naming
    the packed languages. Raises :class:`ValueError` for an
    unknown mode.
    """
    kind = (mode or "show").strip().lower()
    if kind not in ("show", "language"):
        raise ValueError(f"{USAGE} — unknown mode {mode!r}")
    if not enabled:
        return _closed(kind)
    if kind == "language":
        if not language:
            raise ValueError(f"{USAGE} — this road needs its language")
        account = _account(language)
        if account is None:
            known = ", ".join(core_packs.languages())
            return LanguagePacksReport(
                kind=kind, status="error",
                note=(f"no language pack for {language!r} — the "
                      f"packs are: {known}; a new language is a "
                      "pack (a data entry), not a guess"))
        return LanguagePacksReport(
            kind=kind, packs=[account],
            note=("one pack's toolchain, described and "
                  "PATH-checked — nothing was executed"))
    accounts = [account for account in
                (_account(pack.language) for pack in core_packs.packs())
                if account is not None]
    return LanguagePacksReport(
        kind=kind, packs=accounts,
        note=("every pack's toolchain, described and "
              "PATH-checked — nothing was executed"))


# ---------------------------------------------------------------------------
# Surfaces: the shared parser + formatters
# ---------------------------------------------------------------------------

def parse_langpacks_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/langpacks`` arguments into a packs request.

    Grammar::

        /langpacks
        /langpacks show
        /langpacks <language>

    Raises :class:`ValueError` on a usage error.
    """
    text = (arguments or "").strip()
    if not text:
        return {"action": "show"}
    tokens = text.split()
    if len(tokens) != 1:
        raise ValueError(f"{USAGE} — name one language, or none")
    head = tokens[0].lower()
    if head == "show":
        return {"action": "show"}
    return {"action": "language", "language": head}


def _entry_text(entry: Dict[str, Any]) -> str:
    state = "installed" if entry["installed"] else "not installed"
    return (f"{entry['name']} (`{' '.join(entry['command'])}`, "
            f"{state} on PATH)")


def format_language_pack_report(status: Dict[str, Any]) -> str:
    """One language-packs call's account, from an Agent status mapping."""
    report = status["report"]
    lines = [f"Language packs ({LANGUAGE_PACKS_SLICE}): "
             f"{report['kind']} — per-language toolchains "
             "declared in data, described never executed."]
    for pack in report["packs"]:
        lines.append(
            f"  {pack['language']} [{pack['id']}] "
            f"({pack['title']}): extensions "
            f"{', '.join(pack['extensions'])}")
        if pack["server"]:
            lines.append(f"    server: {_entry_text(pack['server'])}")
        else:
            lines.append("    server: none declared (honestly "
                         "server-less in the pack data)")
        for entry in pack["formatters"]:
            lines.append(f"    formatter: {_entry_text(entry)}")
        for entry in pack["test_runners"]:
            lines.append(f"    test runner: {_entry_text(entry)}")
        lines.append(f"    {pack['notes']}")
    if report["note"]:
        lines.append(f"  {report['note']}")
    lines.append(status["plain_explanation"])
    return "\n".join(lines)


def render_markdown(report: LanguagePacksReport) -> str:
    """Render *report* as a human report, from its own record.

    Built from :meth:`LanguagePacksReport.totals`,
    :meth:`LanguagePacksReport.pack_languages`, and each
    pack's :meth:`PackAccount.toolchain_entries` with each
    entry's :meth:`ToolchainEntry.command_text` /
    :meth:`ToolchainEntry.binary`, so the rendered page is
    computed from the same values the tests pin.
    """
    n_packs, n_tools, n_installed = report.totals()
    lines = [
        "# Language Packs — per-language toolchains as data",
        "",
        f"*Slice {LANGUAGE_PACKS_SLICE} of the All-Features "
        "road (Part III — Code Intelligence). Read-only — "
        "nothing is executed by this report; declared "
        "binaries are PATH-checked only.*",
        "",
        f"**{n_packs} pack(s)**, **{n_tools} declared "
        f"tool(s)**, **{n_installed} installed** on PATH.",
        "",
    ]
    for pack in report.packs:
        bits = []
        for entry in pack.toolchain_entries():
            state = "installed" if entry.installed else "not installed"
            bits.append(f"{entry.name} `{entry.command_text()}` "
                        f"({state}; binary `{entry.binary()}`)")
        lines.append(
            f"- `{pack.language}` [{pack.id}]: "
            + "; ".join(bits))
    lines.append("")
    lines.append(
        "Packs: " + (", ".join(report.pack_languages()) or "none"))
    lines.append("")
    return "\n".join(lines)
