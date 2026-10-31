"""The Rivals' Config Import Study (All-Features roadmap slice M-014).

What the config and instruction files of Claude Code, Codex CLI,
OpenCode and Aider look like, behaviourally: names, locations,
scopes, formats, precedence, merge behaviour, key settings and the
disguises secrets wear in each. The study was made clean-room, from
the rivals' public documentation — no rival source was read and no
rival file was copied; formats and observable behaviour are all an
importer needs, and all that is recorded here.

This study is the specification for Part X's rival importers
(M-241). Every rival entry carries its precedence ladder and the
directives its importer must obey; every key mapping names the
Mythic setting it lands on — a real setting from the M-009 config
catalogue — or ``none``, with the reason recorded, where Mythic has
no counterpart. The validator enforces the study's shape: the four
roadmap-named rivals in roadmap order, every rival holding at
least one settings file and one instruction source, every mapping
naming its landing spot, and every rival carrying importer
directives that route secrets to Kista rather than copying them.

One honest gap is recorded in the data itself: M-241 also names
Gemini/Antigravity layouts, which M-014's roadmap text does not —
they are not studied here, and M-241 must commission that study
rather than guess from this one.

Data lives in ``mythic_agent/data/rival_config_study.yaml``.
"""

from __future__ import annotations

__all__ = [
    "CATALOG_RESOURCE",
    "CATALOG_SCHEMA",
    "FORMATS",
    "Any",
    "Dict",
    "FileEntry",
    "Finding",
    "KeyMapping",
    "List",
    "Optional",
    "RIVAL_IDS",
    "ROLES",
    "Rival",
    "RivalConfigStudy",
    "SCOPES",
    "load_study",
    "render_markdown",
    "validate_study",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the study data file inside ``mythic_agent/data``.
CATALOG_RESOURCE = "rival_config_study.yaml"

#: The only schema this loader accepts.
CATALOG_SCHEMA = "mythic.rival_config_study/1"

#: The rivals the roadmap names for this study, in roadmap order.
RIVAL_IDS = ("claude-code", "codex-cli", "opencode", "aider")

SCOPES = ("user", "project", "local", "managed")

FORMATS = (
    "json",
    "jsonc",
    "toml",
    "yaml",
    "markdown",
    "markdown-frontmatter",
    "plaintext",
    "dotenv",
)

ROLES = ("settings", "instructions", "mcp", "commands", "agents", "state", "ignore")

_RIVAL_ID_RE = re.compile(r"^R-\d{2}$")
_FILE_ID_RE = re.compile(r"^F-\d{2}$")
_KEY_ID_RE = re.compile(r"^K-\d{2}$")
_FINDING_ID_RE = re.compile(r"^G-\d{2}$")


@dataclass(frozen=True)
class Rival:
    """One studied rival: its ladder, its merge rule, its importer law."""

    id: str
    rival: str
    name: str
    vendor: str
    precedence: Tuple[str, ...]
    merge_behaviour: str
    importer_directives: Tuple[str, ...]


@dataclass(frozen=True)
class FileEntry:
    """One config or instruction file in one rival's layout."""

    id: str
    rival: str
    name: str
    scope: str
    format: str
    role: str
    behaviour: str


@dataclass(frozen=True)
class KeyMapping:
    """One rival config key and the Mythic setting it lands on."""

    id: str
    rival: str
    key: str
    mythic_setting: str
    behaviour: str


@dataclass(frozen=True)
class Finding:
    """One cross-rival behavioural finding and what it means for M-241."""

    id: str
    finding: str
    importer_implication: str


@dataclass(frozen=True)
class RivalConfigStudy:
    """The validated study: rivals, their files, key mappings, findings."""

    recorded: str
    scope_note: str
    rivals: Tuple[Rival, ...]
    files: Tuple[FileEntry, ...]
    key_mappings: Tuple[KeyMapping, ...]
    findings: Tuple[Finding, ...]

    def counts(self) -> Tuple[int, int, int, int]:
        """(rivals, files, key mappings, findings) as recorded."""
        return (
            len(self.rivals),
            len(self.files),
            len(self.key_mappings),
            len(self.findings),
        )

    def rival_ids(self) -> Tuple[str, ...]:
        """The studied rivals' ids, in study order."""
        return tuple(r.rival for r in self.rivals)

    def files_for(self, rival: str) -> Tuple[FileEntry, ...]:
        """Every studied file belonging to *rival*, in study order."""
        return tuple(f for f in self.files if f.rival == rival)

    def mappings_for(self, rival: str) -> Tuple[KeyMapping, ...]:
        """Every key mapping belonging to *rival*, in study order."""
        return tuple(m for m in self.key_mappings if m.rival == rival)

    def mapped_settings(self) -> Tuple[str, ...]:
        """The distinct real Mythic settings any rival key lands on."""
        seen: List[str] = []
        for mapping in self.key_mappings:
            if mapping.mythic_setting != "none" and mapping.mythic_setting not in seen:
                seen.append(mapping.mythic_setting)
        return tuple(seen)

    def unmapped_keys(self) -> Tuple[str, ...]:
        """Ids of key mappings that land on no Mythic setting."""
        return tuple(m.id for m in self.key_mappings if m.mythic_setting == "none")


def _check_rivals(entries: Any, problems: List[str]) -> None:
    if not isinstance(entries, list) or not entries:
        problems.append("rivals must be a non-empty list")
        return
    slugs: List[str] = []
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"rival entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"R-{position:02d}"
        if not isinstance(eid, str) or not _RIVAL_ID_RE.match(eid):
            problems.append(f"rival entry {eid!r}: id must look like 'R-01'")
        elif eid != expected:
            problems.append(
                f"rival entry {eid}: ids must be sequential, expected {expected}"
            )
        slug = entry.get("rival")
        if slug not in RIVAL_IDS:
            problems.append(f"rival entry {eid}: rival {slug!r} not in {RIVAL_IDS}")
        elif isinstance(slug, str):
            slugs.append(slug)
        for key in ("name", "vendor", "merge_behaviour"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"rival entry {eid}: {key} must be non-empty")
        precedence = entry.get("precedence")
        if (
            not isinstance(precedence, list)
            or len(precedence) < 2
            or not all(isinstance(p, str) and p for p in precedence)
        ):
            problems.append(
                f"rival entry {eid}: precedence must list at least two "
                "non-empty layers, highest first"
            )
        directives = entry.get("importer_directives")
        if (
            not isinstance(directives, list)
            or len(directives) < 3
            or not all(isinstance(d, str) and d for d in directives)
        ):
            problems.append(
                f"rival entry {eid}: importer_directives must list at "
                "least three non-empty directives for M-241"
            )
        elif not any("Kista" in d for d in directives):
            problems.append(
                f"rival entry {eid}: importer_directives must route "
                "secrets to Kista in at least one directive"
            )
    if slugs != list(RIVAL_IDS):
        problems.append(
            f"rivals must be exactly the roadmap-named four in order "
            f"{list(RIVAL_IDS)}, got {slugs}"
        )


def _check_files(entries: Any, problems: List[str]) -> None:
    if not isinstance(entries, list) or not entries:
        problems.append("files must be a non-empty list")
        return
    roles_by_rival: Dict[str, set] = {slug: set() for slug in RIVAL_IDS}
    scopes_by_rival: Dict[str, set] = {slug: set() for slug in RIVAL_IDS}
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"file entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"F-{position:02d}"
        if not isinstance(eid, str) or not _FILE_ID_RE.match(eid):
            problems.append(f"file entry {eid!r}: id must look like 'F-01'")
        elif eid != expected:
            problems.append(
                f"file entry {eid}: ids must be sequential, expected {expected}"
            )
        rival = entry.get("rival")
        if rival not in RIVAL_IDS:
            problems.append(f"file entry {eid}: rival {rival!r} not in {RIVAL_IDS}")
        scope = entry.get("scope")
        fmt = entry.get("format")
        role = entry.get("role")
        if scope not in SCOPES:
            problems.append(f"file entry {eid}: scope {scope!r} not in {SCOPES}")
        if fmt not in FORMATS:
            problems.append(f"file entry {eid}: format {fmt!r} not in {FORMATS}")
        if role not in ROLES:
            problems.append(f"file entry {eid}: role {role!r} not in {ROLES}")
        for key in ("name", "behaviour"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"file entry {eid}: {key} must be non-empty")
        if rival in RIVAL_IDS:
            if isinstance(role, str):
                roles_by_rival[rival].add(role)
            if isinstance(scope, str):
                scopes_by_rival[rival].add(scope)
    for slug in RIVAL_IDS:
        if "settings" not in roles_by_rival[slug]:
            problems.append(f"rival {slug}: no settings file studied")
        if "instructions" not in roles_by_rival[slug]:
            problems.append(f"rival {slug}: no instruction source studied")
        if "user" not in scopes_by_rival[slug]:
            problems.append(f"rival {slug}: no user-scope file studied")
        if "project" not in scopes_by_rival[slug]:
            problems.append(f"rival {slug}: no project-scope file studied")


def _check_mappings(entries: Any, problems: List[str]) -> None:
    if not isinstance(entries, list) or not entries:
        problems.append("key_mappings must be a non-empty list")
        return
    mapped_by_rival: Dict[str, int] = {slug: 0 for slug in RIVAL_IDS}
    total_by_rival: Dict[str, int] = {slug: 0 for slug in RIVAL_IDS}
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"key mapping entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"K-{position:02d}"
        if not isinstance(eid, str) or not _KEY_ID_RE.match(eid):
            problems.append(f"key mapping entry {eid!r}: id must look like 'K-01'")
        elif eid != expected:
            problems.append(
                f"key mapping entry {eid}: ids must be sequential, "
                f"expected {expected}"
            )
        rival = entry.get("rival")
        if rival not in RIVAL_IDS:
            problems.append(
                f"key mapping entry {eid}: rival {rival!r} not in {RIVAL_IDS}"
            )
        for key in ("key", "mythic_setting", "behaviour"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"key mapping entry {eid}: {key} must be non-empty")
        if rival in RIVAL_IDS:
            total_by_rival[rival] += 1
            if entry.get("mythic_setting") not in (None, "none"):
                mapped_by_rival[rival] += 1
    for slug in RIVAL_IDS:
        if total_by_rival[slug] < 3:
            problems.append(
                f"rival {slug}: at least three key mappings required, "
                f"got {total_by_rival[slug]}"
            )
        if mapped_by_rival[slug] < 1:
            problems.append(
                f"rival {slug}: at least one key must land on a real "
                "Mythic setting"
            )


def _check_findings(entries: Any, problems: List[str]) -> None:
    if not isinstance(entries, list) or len(entries) < 4:
        problems.append("findings must list at least four findings")
        return
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"finding entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"G-{position:02d}"
        if not isinstance(eid, str) or not _FINDING_ID_RE.match(eid):
            problems.append(f"finding entry {eid!r}: id must look like 'G-01'")
        elif eid != expected:
            problems.append(
                f"finding entry {eid}: ids must be sequential, expected {expected}"
            )
        for key in ("finding", "importer_implication"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"finding entry {eid}: {key} must be non-empty")


def validate_study(data: Any) -> List[str]:
    """Return a list of human-readable problems with study *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"study root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != CATALOG_SCHEMA:
        problems.append(f"schema must be {CATALOG_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != "M-014":
        problems.append(f"slice must be 'M-014', got {data.get('slice')!r}")
    for key in ("recorded", "scope_note"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")
    _check_rivals(data.get("rivals"), problems)
    _check_files(data.get("files"), problems)
    _check_mappings(data.get("key_mappings"), problems)
    _check_findings(data.get("findings"), problems)
    return problems


def _to_study(data: Dict[str, Any]) -> RivalConfigStudy:
    return RivalConfigStudy(
        recorded=data["recorded"],
        scope_note=data["scope_note"],
        rivals=tuple(
            Rival(
                id=r["id"], rival=r["rival"], name=r["name"], vendor=r["vendor"],
                precedence=tuple(r["precedence"]),
                merge_behaviour=r["merge_behaviour"],
                importer_directives=tuple(r["importer_directives"]),
            )
            for r in data["rivals"]
        ),
        files=tuple(
            FileEntry(
                id=f["id"], rival=f["rival"], name=f["name"], scope=f["scope"],
                format=f["format"], role=f["role"], behaviour=f["behaviour"],
            )
            for f in data["files"]
        ),
        key_mappings=tuple(
            KeyMapping(
                id=m["id"], rival=m["rival"], key=m["key"],
                mythic_setting=m["mythic_setting"], behaviour=m["behaviour"],
            )
            for m in data["key_mappings"]
        ),
        findings=tuple(
            Finding(
                id=g["id"], finding=g["finding"],
                importer_implication=g["importer_implication"],
            )
            for g in data["findings"]
        ),
    )


def load_study(data: Optional[Dict[str, Any]] = None) -> RivalConfigStudy:
    """Load and validate the shipped rivals' config import study (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed study.
    """
    raw = data if data is not None else load_resource(CATALOG_RESOURCE)
    problems = validate_study(raw)
    if problems:
        raise ValidationError(
            "rival config study failed validation: " + "; ".join(problems)
        )
    return _to_study(raw)  # type: ignore[arg-type]


def render_markdown(study: RivalConfigStudy) -> str:
    """Render the study as markdown, rival by rival, findings last.

    Built from :meth:`RivalConfigStudy.counts`,
    :meth:`RivalConfigStudy.rival_ids`,
    :meth:`RivalConfigStudy.files_for`,
    :meth:`RivalConfigStudy.mappings_for`,
    :meth:`RivalConfigStudy.mapped_settings`, and
    :meth:`RivalConfigStudy.unmapped_keys`, so the rendered page is
    computed from the same accessors the tests pin.
    """
    n_rivals, n_files, n_mappings, n_findings = study.counts()
    lines = [
        "# The Rivals' Config Import Study (M-014)",
        "",
        f"*Recorded {study.recorded}: {n_rivals} rivals, {n_files} files, "
        f"{n_mappings} key mappings, {n_findings} findings — the spec for "
        "Part X's rival importers (M-241).*",
        "",
        study.scope_note,
        "",
    ]
    by_slug = {r.rival: r for r in study.rivals}
    for slug in study.rival_ids():
        rival = by_slug[slug]
        lines += [f"## {rival.id} {rival.name} ({rival.vendor})", ""]
        lines.append("Precedence, highest first:")
        for layer in rival.precedence:
            lines.append(f"- {layer}")
        lines += ["", f"Merge: {rival.merge_behaviour}", "", "Files:"]
        for entry in study.files_for(slug):
            lines.append(
                f"- {entry.id} `{entry.name}` — {entry.scope} scope, "
                f"{entry.format}, {entry.role}: {entry.behaviour}"
            )
        lines += ["", "Key mappings:"]
        for mapping in study.mappings_for(slug):
            lines.append(
                f"- {mapping.id} `{mapping.key}` -> "
                f"`{mapping.mythic_setting}`: {mapping.behaviour}"
            )
        lines += ["", "Importer directives for M-241:"]
        for directive in rival.importer_directives:
            lines.append(f"- {directive}")
        lines.append("")
    lines += ["## Findings", ""]
    for finding in study.findings:
        lines.append(
            f"- {finding.id} {finding.finding} "
            f"Importer: {finding.importer_implication}"
        )
    lines += [
        "",
        "## The count, plainly",
        "",
        f"Mythic settings landed on: {', '.join(study.mapped_settings())}.",
        f"Keys with no Mythic counterpart: {', '.join(study.unmapped_keys())}.",
        "",
    ]
    return "\n".join(lines)
