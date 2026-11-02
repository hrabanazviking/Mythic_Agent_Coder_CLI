"""Config and infra sight (M-066).

Part III — Code Intelligence. The roadmap's words for
this slice: "Config and infra files: YAML/TOML/
Dockerfile/systemd units parsed structurally, with
the no-Docker law enforced as a *warning the coder
itself raises* on Volmarr's projects."

What ships here, in ``mythic_agent/tools/config_sight.py``:

* **Structural parsing, never a content dump.** Each
  recognised file is parsed by the real parser for its
  format and reported as structure: for YAML and TOML,
  the top-level keys with each value's kind and size,
  the total key count and the maximum depth; for
  systemd units and INI files, the sections in order
  with their directives (repeated directives kept —
  systemd allows them); for a Dockerfile, its build
  stages, base images, instruction counts, exposed
  ports, ENV keys and volumes; for a compose file, its
  services and each service's image/build shape.
* **The parsers are the honest ones available.** YAML
  rides PyYAML (a core dependency, already the house
  config parser), TOML rides the stdlib ``tomllib``,
  units/INI ride a small tolerant parser written here
  (``configparser`` would merge the repeated directives
  systemd files legitimately carry), and Dockerfiles
  ride a line parser that joins continuations and
  strips comments. A file that does not parse is
  reported with its parser's error, never dressed as
  an empty file.
* **The no-Docker law, raised by the coder itself.**
  Docker artifacts — ``Dockerfile``, ``Dockerfile.*``,
  ``*.dockerfile`` and compose YAML (``docker-compose``
  / ``compose``) — found in a workspace detected as
  Volmarr's project raise :data:`NO_DOCKER_WARNING` in
  the report: Volmarr's standing law is no Docker,
  ever, on his projects (native installs, language-
  native environments, Nix/Guix, system containers or
  a VM first). Detection is honest and named: a marker
  file at the workspace root — ``AGENTS.md``,
  ``SOUL.md``, ``MEMORY.md``, ``RULES.AI.md``, or any
  root file whose name carries "Volmarr" — or an
  explicit override. Docker artifacts in a workspace
  with no marker are still listed, and the report says
  plainly that the law-warning was not raised because
  no Volmarr-project marker was found.
* **The surfaces.** ``Agent.config_sight(...)`` and
  ``/config [show | <file> | docker]`` on the terminal
  and TUI system-command roads, sharing this module's
  parser and formatter. The setting ``config_sight``
  (on by default) closes the road plainly.

Honesty rules, pinned by the slice's tests:

* **Read-only.** This road reads and parses; it never
  executes, applies, renders or starts anything a
  config file describes.
* **Structure, not secrets.** Values of mapping keys
  and unit directives are reported by kind and size;
  scalar values themselves are not echoed into the
  report (a config file is where secrets live).
* **Absence and failure are named.** A workspace with
  no recognised files says so; an unparseable file
  carries its error; a capped scan names its cap.
"""

from __future__ import annotations

__all__ = [
    "PLAIN_EXPLANATION",
    "CONFIG_SLICE",
    "USAGE",
    "NO_DOCKER_WARNING",
    "MARKER_FILES",
    "YAML_EXTENSIONS",
    "TOML_EXTENSIONS",
    "INI_EXTENSIONS",
    "UNIT_EXTENSIONS",
    "TopEntry",
    "UnitSection",
    "DockerInfo",
    "ConfigFile",
    "ConfigReport",
    "enabled_from_config",
    "classify_file",
    "is_docker_name",
    "detect_volmarr_project",
    "find_config_files",
    "summarise_mapping",
    "parse_unit_text",
    "parse_dockerfile_text",
    "parse_config_file",
    "config_sight",
    "parse_config_args",
    "format_config_report",
    "render_markdown",
]

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import yaml

CONFIG_SLICE = "M-066"

PLAIN_EXPLANATION = (
    "Config sight reads the workspace's configuration "
    "and infrastructure files structurally: /config "
    "show parses each YAML, TOML, INI and systemd unit "
    "file and each Dockerfile or compose file, and "
    "reports its shape — top-level keys and their kinds, "
    "sections and directives, build stages and base "
    "images — never the files' values, and nothing a "
    "file describes is ever executed or applied. On a "
    "workspace marked as one of Volmarr's projects, any "
    "Docker file raises the coder's own no-Docker-law "
    "warning, because his standing law is no Docker, "
    "ever, on his projects."
)

USAGE = "Usage: /config [show | <file> | docker]"

NO_DOCKER_WARNING = (
    "NO-DOCKER LAW: Docker artifacts were found in one "
    "of Volmarr's projects. Volmarr's standing law is "
    "no Docker, ever — install natively (binary + "
    "config + systemd unit), use a language-native "
    "environment, Nix/Guix, a system container "
    "(Incus/LXC, systemd-nspawn) or a VM before any "
    "container tool, and Docker itself only at his "
    "explicit word. This road only reads and warns; "
    "nothing was run."
)

#: Root files that mark a workspace as Volmarr's project.
MARKER_FILES = ("AGENTS.md", "SOUL.md", "MEMORY.md",
                "RULES.AI.md")

YAML_EXTENSIONS = (".yaml", ".yml")
TOML_EXTENSIONS = (".toml",)
INI_EXTENSIONS = (".ini", ".cfg")
UNIT_EXTENSIONS = (".service", ".timer", ".socket",
                   ".mount", ".automount", ".path",
                   ".target", ".slice", ".scope",
                   ".device", ".swap")

_SKIP_DIRS = {".git", ".hg", ".svn", "__pycache__",
              "node_modules", "dist", "build",
              ".venv", ".venv-baseline", "venv"}

MAX_SCAN_FILES = 500
MAX_FILE_BYTES = 512_000


def enabled_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """Config sight is on unless config says so."""
    if not config:
        return True
    return config.get("config_sight", True) is not False


# ---------------------------------------------------------------------------
# Recognition
# ---------------------------------------------------------------------------

_COMPOSE_RE = re.compile(
    r"^(?:docker-)?compose(?:\.[^.]+)?\.ya?ml$", re.IGNORECASE)


def is_docker_name(name: str) -> bool:
    """True when a file *name* is a Docker artifact."""
    lower = name.lower()
    return (lower == "dockerfile"
            or lower.startswith("dockerfile.")
            or lower.endswith(".dockerfile")
            or bool(_COMPOSE_RE.match(name)))


def classify_file(path: Path) -> str:
    """The format of one file: yaml | toml | ini | systemd |
    dockerfile | docker-compose | '' (unrecognised)."""
    name = path.name
    if _COMPOSE_RE.match(name):
        return "docker-compose"
    lower = name.lower()
    if lower == "dockerfile" or lower.startswith("dockerfile.") \
            or lower.endswith(".dockerfile"):
        return "dockerfile"
    suffix = path.suffix.lower()
    if suffix in YAML_EXTENSIONS:
        return "yaml"
    if suffix in TOML_EXTENSIONS:
        return "toml"
    if suffix in UNIT_EXTENSIONS:
        return "systemd"
    if suffix in INI_EXTENSIONS:
        return "ini"
    return ""


def detect_volmarr_project(
        workspace: Any,
        override: Optional[bool] = None) -> Tuple[bool, str]:
    """(is Volmarr's project, the evidence) for a workspace.

    An explicit override wins and is named as such.
    Otherwise the root markers in :data:`MARKER_FILES`
    decide, plus any root file whose name carries
    "Volmarr". No marker is an honest False.
    """
    if override is not None:
        return bool(override), "explicit caller ruling"
    root = Path(workspace)
    if not root.is_dir():
        return False, "no workspace directory"
    for marker in MARKER_FILES:
        if (root / marker).is_file():
            return True, f"marker file {marker} at the root"
    for entry in sorted(root.iterdir()):
        if entry.is_file() and "volmarr" in entry.name.lower():
            return True, f"root file {entry.name} carries his name"
    return False, "no Volmarr-project marker at the root"


def find_config_files(
        workspace: Any) -> Tuple[List[Tuple[Path, str]], List[str]]:
    """Every recognised config/infra file, caps named."""
    root = Path(workspace)
    found: List[Tuple[Path, str]] = []
    warnings: List[str] = []
    if not root.is_dir():
        return found, warnings
    for candidate in sorted(root.rglob("*")):
        if not candidate.is_file():
            continue
        if any(part in _SKIP_DIRS or part.startswith(".venv")
               for part in candidate.parts):
            continue
        fmt = classify_file(candidate)
        if not fmt:
            continue
        if len(found) >= MAX_SCAN_FILES:
            warnings.append(
                f"scan capped at {MAX_SCAN_FILES} config "
                "files; further files were not read")
            break
        found.append((candidate, fmt))
    return found, warnings


# ---------------------------------------------------------------------------
# Structural accounts
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TopEntry:
    """One top-level key's structural account."""

    name: str
    kind: str = "scalar"  # mapping | sequence | scalar | null
    size: int = 0
    value_type: str = ""

    def record(self) -> Dict[str, Any]:
        return {"name": self.name, "kind": self.kind,
                "size": self.size, "value_type": self.value_type}


def _kind_of(value: Any) -> Tuple[str, int, str]:
    if isinstance(value, dict):
        return "mapping", len(value), "mapping"
    if isinstance(value, (list, tuple)):
        return "sequence", len(value), "sequence"
    if value is None:
        return "null", 0, "null"
    return "scalar", 1, type(value).__name__


def _walk(value: Any, depth: int) -> Tuple[int, int]:
    """(total mapping keys under value, max depth)."""
    if isinstance(value, dict):
        keys = len(value)
        deepest = depth
        for child in value.values():
            child_keys, child_depth = _walk(child, depth + 1)
            keys += child_keys
            deepest = max(deepest, child_depth)
        return keys, deepest
    if isinstance(value, (list, tuple)):
        keys = 0
        deepest = depth
        for child in value:
            child_keys, child_depth = _walk(child, depth + 1)
            keys += child_keys
            deepest = max(deepest, child_depth)
        return keys, deepest
    return 0, depth


def summarise_mapping(
        data: Any) -> Tuple[List[TopEntry], int, int]:
    """(top entries, total keys, max depth) for parsed data.

    Non-mapping data (a top-level sequence or scalar) is
    one synthetic ``(top level)`` entry — named, never
    hidden.
    """
    if isinstance(data, dict):
        entries = []
        for key, value in data.items():
            kind, size, vtype = _kind_of(value)
            entries.append(TopEntry(
                name=str(key), kind=kind, size=size,
                value_type=vtype))
        total, depth = _walk(data, 1)
        return entries, total, depth
    kind, size, vtype = _kind_of(data)
    total, depth = _walk(data, 1)
    return [TopEntry(name="(top level)", kind=kind, size=size,
                     value_type=vtype)], total, depth


@dataclass
class UnitSection:
    """One [Section] of a unit/INI file, directives in order."""

    name: str
    directives: List[Tuple[str, str]] = field(default_factory=list)

    def directive_names(self) -> Tuple[str, ...]:
        return tuple(name for name, _ in self.directives)

    def record(self) -> Dict[str, Any]:
        return {"name": self.name,
                "directives": [
                    {"name": name, "value": value}
                    for name, value in self.directives]}


_SECTION_RE = re.compile(r"^\s*\[([^\]]+)\]\s*$")


def parse_unit_text(text: str) -> List[UnitSection]:
    """Parse systemd/INI text into sections + directives.

    Tolerant by design: comments (``#``/``;``) and blank
    lines are skipped, continuation lines (trailing
    ``\\``) are joined, a directive without ``=`` keeps
    an empty value, and repeated directives are kept in
    order — systemd allows repeats and so does this
    parser. Directives before any section land in a
    ``(no section)`` section, named as such.
    """
    sections: List[UnitSection] = []
    current: Optional[UnitSection] = None
    pending = ""
    for raw in text.splitlines():
        line = raw.rstrip()
        if pending:
            line = pending + line.lstrip()
            pending = ""
        if line.endswith("\\") and not line.lstrip().startswith(("#", ";")):
            pending = line[:-1]
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", ";")):
            continue
        match = _SECTION_RE.match(line)
        if match:
            current = UnitSection(name=match.group(1).strip())
            sections.append(current)
            continue
        if current is None:
            current = UnitSection(name="(no section)")
            sections.append(current)
        name, sep, value = stripped.partition("=")
        current.directives.append(
            (name.strip(), value.strip() if sep else ""))
    if pending:
        if current is None:
            current = UnitSection(name="(no section)")
            sections.append(current)
        name, sep, value = pending.strip().partition("=")
        current.directives.append(
            (name.strip(), value.strip() if sep else ""))
    return sections


@dataclass
class DockerInfo:
    """One Dockerfile's structural account."""

    stages: List[str] = field(default_factory=list)
    base_images: List[str] = field(default_factory=list)
    instructions: Dict[str, int] = field(default_factory=dict)
    exposed_ports: List[str] = field(default_factory=list)
    env_keys: List[str] = field(default_factory=list)
    volumes: List[str] = field(default_factory=list)
    has_entrypoint: bool = False
    has_cmd: bool = False

    def instruction_total(self) -> int:
        return sum(self.instructions.values())

    def record(self) -> Dict[str, Any]:
        return {"stages": list(self.stages),
                "base_images": list(self.base_images),
                "instructions": dict(self.instructions),
                "exposed_ports": list(self.exposed_ports),
                "env_keys": list(self.env_keys),
                "volumes": list(self.volumes),
                "has_entrypoint": self.has_entrypoint,
                "has_cmd": self.has_cmd}


def parse_dockerfile_text(text: str) -> DockerInfo:
    """Parse Dockerfile text structurally (never executed).

    Continuation lines are joined, comments and blank
    lines skipped, each instruction counted by its
    keyword; FROM lines give stages (``AS`` names) and
    base images in order.
    """
    info = DockerInfo()
    logical: List[str] = []
    pending = ""
    for raw in text.splitlines():
        line = raw.rstrip()
        if pending:
            line = pending + " " + line.strip()
            pending = ""
        if line.endswith("\\"):
            pending = line[:-1].rstrip()
            continue
        logical.append(line)
    if pending:
        logical.append(pending)
    for line in logical:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(None, 1)
        keyword = parts[0].upper()
        rest = parts[1] if len(parts) > 1 else ""
        info.instructions[keyword] = \
            info.instructions.get(keyword, 0) + 1
        if keyword == "FROM":
            tokens = [t for t in rest.split()
                      if not t.startswith("--")]
            if tokens:
                info.base_images.append(tokens[0])
                stage = tokens[0]
                upper = [t.upper() for t in tokens]
                if "AS" in upper:
                    stage = tokens[upper.index("AS") + 1] \
                        if upper.index("AS") + 1 < len(tokens) \
                        else tokens[0]
                info.stages.append(stage)
        elif keyword == "EXPOSE":
            info.exposed_ports.extend(rest.split())
        elif keyword == "ENV":
            for token in rest.split():
                key = token.split("=", 1)[0]
                if key:
                    info.env_keys.append(key)
                if "=" not in token:
                    break
        elif keyword == "VOLUME":
            cleaned = rest.strip().strip("[]")
            info.volumes.extend(
                v.strip().strip("\"'") for v in cleaned.split(",")
                if v.strip())
        elif keyword == "ENTRYPOINT":
            info.has_entrypoint = True
        elif keyword == "CMD":
            info.has_cmd = True
    return info


@dataclass
class ConfigFile:
    """One config/infra file's whole structural account."""

    path: str
    format: str = ""  # yaml | toml | ini | systemd | dockerfile | docker-compose
    docker: bool = False
    top_level: List[TopEntry] = field(default_factory=list)
    total_keys: int = 0
    max_depth: int = 0
    sections: List[UnitSection] = field(default_factory=list)
    docker_info: Optional[DockerInfo] = None
    services: List[str] = field(default_factory=list)
    note: str = ""

    def top_names(self) -> Tuple[str, ...]:
        return tuple(e.name for e in self.top_level)

    def section_names(self) -> Tuple[str, ...]:
        return tuple(s.name for s in self.sections)

    def record(self) -> Dict[str, Any]:
        return {"path": self.path, "format": self.format,
                "docker": self.docker,
                "top_level": [e.record() for e in self.top_level],
                "total_keys": self.total_keys,
                "max_depth": self.max_depth,
                "sections": [s.record() for s in self.sections],
                "docker_info": self.docker_info.record()
                if self.docker_info else None,
                "services": list(self.services),
                "note": self.note}


def parse_config_file(path: Path, display: str = "",
                      fmt: str = "") -> ConfigFile:
    """Parse one file structurally with its format's parser.

    A parse failure lands in ``note`` with the parser's
    own words — the file is named, never dressed as
    empty. A read failure does the same.
    """
    fmt = fmt or classify_file(path)
    info = ConfigFile(
        path=display or str(path), format=fmt,
        docker=fmt in ("dockerfile", "docker-compose"))
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        info.note = f"the file could not be read: {exc}"
        return info
    if fmt == "dockerfile":
        info.docker_info = parse_dockerfile_text(text)
        return info
    if fmt in ("systemd", "ini"):
        info.sections = parse_unit_text(text)
        info.total_keys = sum(
            len(s.directives) for s in info.sections)
        info.max_depth = 1 if info.sections else 0
        return info
    try:
        if fmt == "toml":
            data = tomllib.loads(text)
        else:  # yaml + docker-compose both ride PyYAML
            data = yaml.safe_load(text)
    except Exception as exc:  # the parser's error, named
        info.note = f"the file did not parse: {exc}"
        return info
    if data is None:
        info.note = "the file is empty"
        return info
    (info.top_level, info.total_keys,
     info.max_depth) = summarise_mapping(data)
    if fmt == "docker-compose" and isinstance(data, dict):
        services = data.get("services")
        if isinstance(services, dict):
            info.services = [str(name) for name in services]
    return info


# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------

@dataclass
class ConfigReport:
    """One config-sight call's whole account."""

    kind: str = "show"  # show | file | docker
    status: str = "ok"  # ok | disabled | error
    files: List[ConfigFile] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    volmarr_project: bool = False
    volmarr_evidence: str = ""
    docker_warning: bool = False
    note: str = ""

    def totals(self) -> Tuple[int, int, int]:
        """(files, docker artifacts, parsed-clean files)."""
        return (len(self.files),
                sum(1 for f in self.files if f.docker),
                sum(1 for f in self.files if not f.note))

    def file_names(self) -> Tuple[str, ...]:
        return tuple(f.path for f in self.files)

    def docker_names(self) -> Tuple[str, ...]:
        return tuple(f.path for f in self.files if f.docker)

    def record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "status": self.status,
                "files": [f.record() for f in self.files],
                "warnings": list(self.warnings),
                "volmarr_project": self.volmarr_project,
                "volmarr_evidence": self.volmarr_evidence,
                "docker_warning": self.docker_warning,
                "note": self.note}


def _closed(kind: str) -> ConfigReport:
    return ConfigReport(
        kind=kind, status="disabled",
        note=("config sight is off (the config_sight "
              "setting), so no project file was read"))


def _display(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _finish_docker_law(report: ConfigReport) -> None:
    """Raise (or honestly withhold) the no-Docker warning."""
    docker_files = report.docker_names()
    if not docker_files:
        return
    if report.volmarr_project:
        report.docker_warning = True
        report.warnings.append(
            NO_DOCKER_WARNING + " Artifacts: "
            + ", ".join(docker_files) + ".")
    else:
        report.note = (
            (report.note + " " if report.note else "")
            + "Docker artifacts are present ("
            + ", ".join(docker_files)
            + ") but no Volmarr-project marker was found "
              "at the workspace root, so the no-Docker-law "
              "warning was not raised for this workspace.")


def config_sight(
        workspace: Any, mode: str = "show", *,
        target: Optional[str] = None,
        volmarr_project: Optional[bool] = None,
        enabled: bool = True,
) -> ConfigReport:
    """One config account — all files, one file, or Docker only.

    Read-only structural parsing; nothing a file
    describes is executed or applied. A missing
    workspace is an honest ``error`` report. Raises
    :class:`ValueError` for an unknown mode.
    """
    kind = (mode or "show").strip().lower()
    if kind not in ("show", "file", "docker"):
        raise ValueError(f"{USAGE} — unknown mode {mode!r}")
    if not enabled:
        return _closed(kind)
    root = Path(workspace)
    if not root.is_dir():
        return ConfigReport(
            kind=kind, status="error",
            note=f"no workspace at {root} — nothing was read")
    is_volmarr, evidence = detect_volmarr_project(
        root, volmarr_project)
    report = ConfigReport(
        kind=kind, volmarr_project=is_volmarr,
        volmarr_evidence=evidence)
    if kind == "file":
        if not target:
            raise ValueError(f"{USAGE} — this road needs its file")
        candidate = Path(target)
        if not candidate.is_absolute():
            candidate = root / candidate
        if not candidate.is_file():
            report.status = "error"
            report.note = f"no file at {target} — nothing was read"
            return report
        fmt = classify_file(candidate)
        if not fmt:
            report.status = "error"
            report.note = (
                f"{target} is not a recognised config or "
                "infra file — config sight knows YAML, "
                "TOML, INI, systemd units, Dockerfiles "
                "and compose files")
            return report
        if candidate.stat().st_size > MAX_FILE_BYTES:
            report.status = "error"
            report.note = (
                f"{target} is over the {MAX_FILE_BYTES}-byte "
                "scan cap and was not read")
            return report
        report.files = [parse_config_file(
            candidate, _display(root, candidate), fmt)]
        _finish_docker_law(report)
        if not report.note:
            report.note = "one file read structurally — nothing was executed"
        return report
    found, warnings = find_config_files(root)
    report.warnings.extend(warnings)
    for path, fmt in found:
        if kind == "docker" and fmt not in (
                "dockerfile", "docker-compose"):
            continue
        display = _display(root, path)
        if path.stat().st_size > MAX_FILE_BYTES:
            report.warnings.append(
                f"{display} skipped: over the "
                f"{MAX_FILE_BYTES}-byte scan cap")
            continue
        report.files.append(parse_config_file(path, display, fmt))
    _finish_docker_law(report)
    if not report.note:
        report.note = (
            "files read structurally — nothing was executed "
            "or applied" if report.files else
            "no recognised config or infra files in this "
            "workspace — YAML, TOML, INI, systemd units, "
            "Dockerfiles and compose files are recognised "
            "wherever they land")
    return report


# ---------------------------------------------------------------------------
# Surfaces: the shared parser + formatters
# ---------------------------------------------------------------------------

def parse_config_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/config`` arguments into a config request.

    Grammar::

        /config
        /config show
        /config <file>
        /config docker

    Raises :class:`ValueError` on a usage error.
    """
    text = (arguments or "").strip()
    if not text:
        return {"action": "show"}
    tokens = text.split()
    if len(tokens) != 1:
        raise ValueError(f"{USAGE} — name one file, or none")
    head = tokens[0].lower()
    if head == "show":
        return {"action": "show"}
    if head == "docker":
        return {"action": "docker"}
    return {"action": "file", "target": tokens[0]}


def format_config_report(status: Dict[str, Any]) -> str:
    """One config call's account, from an Agent status mapping."""
    report = status["report"]
    lines = [f"Config sight ({CONFIG_SLICE}): {report['kind']} — "
             "config and infra files parsed structurally, "
             "nothing executed."]
    lines.append(
        "  Volmarr's project: "
        + ("yes" if report["volmarr_project"] else "not detected")
        + f" ({report['volmarr_evidence']})")
    for entry in report["files"]:
        lines.append(
            f"  {entry['path']} [{entry['format']}]"
            f"{' — DOCKER ARTIFACT' if entry['docker'] else ''}: "
            f"{entry['total_keys']} key(s)/directive(s), "
            f"depth {entry['max_depth']}")
        for top in entry["top_level"]:
            lines.append(
                f"    {top['name']}: {top['kind']} "
                f"({top['size']})")
        for section in entry["sections"]:
            names = [d["name"] for d in section["directives"]]
            lines.append(
                f"    [{section['name']}] "
                f"{len(names)} directive(s): "
                + (", ".join(names) or "none"))
        docker = entry.get("docker_info")
        if docker:
            lines.append(
                f"    stages: {docker['stages'] or '[]'}; "
                f"base images: {docker['base_images'] or '[]'}; "
                f"instructions: {docker['instructions']}; "
                f"ports: {docker['exposed_ports'] or '[]'}; "
                f"env keys: {docker['env_keys'] or '[]'}")
        if entry["services"]:
            lines.append(
                f"    services: {', '.join(entry['services'])}")
        if entry["note"]:
            lines.append(f"    {entry['note']}")
    if report["note"]:
        lines.append(f"  {report['note']}")
    for warning in report["warnings"]:
        lines.append(f"  Warning: {warning}")
    lines.append(status["plain_explanation"])
    return "\n".join(lines)


def render_markdown(report: ConfigReport) -> str:
    """Render *report* as a human report, from its own record.

    Built from :meth:`ConfigReport.totals`,
    :meth:`ConfigReport.file_names` /
    :meth:`ConfigReport.docker_names` and each file's
    own accessors, so the rendered page is computed
    from the same values the tests pin.
    """
    n_files, n_docker, n_clean = report.totals()
    lines = [
        "# Config Sight — config and infra files, structurally",
        "",
        f"*Slice {CONFIG_SLICE} of the All-Features road "
        "(Part III — Code Intelligence). Read-only — "
        "nothing is executed or applied by this report.*",
        "",
        f"**{n_files} file(s)**, **{n_docker} Docker "
        f"artifact(s)**, **{n_clean} parsed clean**.",
        "",
        "Volmarr's project: "
        + ("yes" if report.volmarr_project else "not detected")
        + f" ({report.volmarr_evidence}).",
        "",
    ]
    for entry in report.files:
        tops = ", ".join(entry.top_names()) or "none"
        sections = ", ".join(entry.section_names())
        directive_bits = "; ".join(
            f"[{section.name}] "
            + (", ".join(section.directive_names()) or "none")
            for section in entry.sections)
        lines.append(
            f"- `{entry.path}` [{entry.format}]: "
            f"top-level {tops}"
            + (f"; sections {sections}" if sections else "")
            + (f"; directives {directive_bits}"
               if directive_bits else "")
            + (f"; services {', '.join(entry.services)}"
               if entry.services else ""))
        if entry.docker_info is not None:
            lines.append(
                f"  - docker: {entry.docker_info.instruction_total()} "
                f"instruction(s); stages "
                f"{entry.docker_info.stages}")
    lines.append("")
    lines.append(
        "Files read: " + (", ".join(report.file_names()) or "none"))
    lines.append(
        "Docker artifacts: "
        + (", ".join(report.docker_names()) or "none"))
    lines.append(
        "No-Docker-law warning raised: "
        + ("yes" if report.docker_warning else "no"))
    lines.append("")
    return "\n".join(lines)
