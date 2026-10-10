"""Architecture conformance audit for the ``mythic_agent`` package.

Static import-graph audit (stdlib ``ast`` only -- no third-party tools) that
enforces the documented layering rules of this codebase.

Layers (bottom-up; a layer may only depend on layers below it):

* ``providers/``  -- provider LLM clients (anthropic/google/ollama) behind
  ``providers/base.py`` and ``providers/registry.py``.  UI-agnostic and
  agent-agnostic.
* ``core/``       -- headless infrastructure: config, sessions, execution,
  policy, redaction, workspace, validation, runtime, secure API (event bus).
  Knows nothing about presentation (``ui/``), CLI entry points
  (``terminal.py``), or agent orchestration internals (``agents/``).
* ``agents/``     -- agent orchestration (``llm.py``), tool implementations
  (``tools.py``), commands, planning, recovery.  Headless: never touches
  ``ui/`` or ``terminal.py``.
* ``memory/`` ``tools/`` ``knowledge/`` ``data/`` ``integrations/``
  ``workflow/`` -- service layers.  Headless like ``agents/``.
* ``ui/``         -- Textual presentation.  Obtains provider clients through
  the shared runtime/services layer, never constructs them directly.
* entry modules (``cli.py``, ``terminal.py``, ``mcp_server.py``,
  ``doctor.py``, ``onboarding.py``, ``bench.py``) -- composition roots that
  wire everything together.  They may only touch *public* interfaces.

"Public" for entry modules means: module-level names that do not start with
an underscore.  Anything underscore-prefixed is an implementation detail of
its owning module and must not be imported across module boundaries.

Rule records are data::

    Rule(source_pattern, forbidden_pattern, reason, scope)

``source_pattern`` / ``forbidden_pattern`` are fnmatch-style dotted-module
patterns (``*`` spans dots).  ``scope`` is ``"module"`` (only module-level
imports are flagged -- used where a deferred, function-local import is the
deliberate pattern, e.g. a screen lazily launching the TUI app to avoid a
load-time cycle) or ``"any"`` (any static import, including function-local
ones, is flagged).

``check(package_dir)`` returns a list of :class:`Violation` namedtuples.
Imports inside ``if TYPE_CHECKING:`` blocks are ignored -- they are type-only
and never execute at runtime.
"""

from __future__ import annotations

import ast
import fnmatch
from collections import namedtuple
from pathlib import Path
from typing import Iterable, NamedTuple


class Rule(NamedTuple):
    source_pattern: str
    forbidden_pattern: str
    reason: str
    scope: str = "any"  # "any" | "module"


class Violation(NamedTuple):
    source_module: str
    imported_module: str
    lineno: int
    scope: str  # "module" | "deferred" (function-local / nested import)
    rule: Rule

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return (
            f"{self.source_module}:{self.lineno} imports {self.imported_module} "
            f"({self.scope} import) -- {self.rule.reason}"
        )


# ---------------------------------------------------------------------------
# Layering rules.  Chosen after inspecting the live import graph on
# 2026-10-10; each rule below currently passes on the live tree except where
# noted in ACKNOWLEDGED_EXCEPTIONS.
# ---------------------------------------------------------------------------
RULES: list[Rule] = [
    # -- core/ stays UI/provider/entry/agent-agnostic -------------------------
    Rule(
        "mythic_agent.core.*",
        "mythic_agent.ui.*",
        "core is UI-agnostic infrastructure; presentation lives in ui/",
    ),
    Rule(
        "mythic_agent.core.*",
        "mythic_agent.terminal",
        "core must not reach up into the terminal entry module; "
        "entry modules import core, never the reverse (shared helpers live "
        "in core, e.g. core/recovery.py)",
    ),
    Rule(
        "mythic_agent.core.*",
        "mythic_agent.agents.*",
        "core is agent-agnostic infrastructure; agents orchestrate core, "
        "never the reverse -- except the composition root, see "
        "ACKNOWLEDGED_EXCEPTIONS",
    ),
    Rule(
        "mythic_agent.core.*",
        "mythic_agent.cli",
        "core must not depend on the CLI entry module",
    ),
    Rule(
        "mythic_agent.core.*",
        "mythic_agent.mcp_server",
        "core must not depend on the MCP entry module",
    ),
    # -- ui/ is presentation only ---------------------------------------------
    Rule(
        "mythic_agent.ui.*",
        "mythic_agent.providers.*",
        "ui must obtain provider LLM clients through the shared "
        "runtime/services layer (core.secure_api / core.runtime / "
        "providers.registry), never construct them directly",
    ),
    Rule(
        "mythic_agent.ui.*",
        "mythic_agent.terminal",
        "ui is headless-testable presentation; terminal entry logic stays out",
    ),
    Rule(
        "mythic_agent.ui.screens.*",
        "mythic_agent.ui.main_app",
        "main_app is the TUI composition root; a module-level screen->main_app "
        "import creates a load-time cycle (deferred function-local launch "
        "imports are the permitted pattern)",
        scope="module",
    ),
    # -- providers/ are leaf clients -------------------------------------------
    Rule(
        "mythic_agent.providers.*",
        "mythic_agent.ui.*",
        "providers are UI-agnostic leaf clients",
    ),
    Rule(
        "mythic_agent.providers.*",
        "mythic_agent.agents.*",
        "providers are agent-agnostic; agents consume providers via "
        "providers.registry",
    ),
    # -- agents/ and service layers stay headless ------------------------------
    Rule(
        "mythic_agent.agents.*",
        "mythic_agent.ui.*",
        "agents stay headless; the UI subscribes to agent events instead",
    ),
    Rule(
        "mythic_agent.agents.*",
        "mythic_agent.terminal",
        "agents must not reach up into CLI entry points",
    ),
    Rule(
        "mythic_agent.memory.*",
        "mythic_agent.ui.*",
        "memory is a headless service layer",
    ),
    Rule(
        "mythic_agent.memory.*",
        "mythic_agent.terminal",
        "memory is a headless service layer",
    ),
    Rule(
        "mythic_agent.tools.*",
        "mythic_agent.ui.*",
        "tools are a headless service layer",
    ),
    Rule(
        "mythic_agent.tools.*",
        "mythic_agent.terminal",
        "tools are a headless service layer",
    ),
    Rule(
        "mythic_agent.knowledge.*",
        "mythic_agent.ui.*",
        "knowledge is a headless service layer",
    ),
    Rule(
        "mythic_agent.data.*",
        "mythic_agent.ui.*",
        "data is a headless service layer",
    ),
    Rule(
        "mythic_agent.integrations.*",
        "mythic_agent.ui.*",
        "integrations are a headless service layer",
    ),
    Rule(
        "mythic_agent.workflow.*",
        "mythic_agent.ui.*",
        "workflow is a headless service layer",
    ),
]

# ---------------------------------------------------------------------------
# Entry modules: composition roots that may wire anything together, but may
# only touch *public* interfaces (no underscore-prefixed names imported from
# another mythic_agent module).
# ---------------------------------------------------------------------------
ENTRY_MODULES = (
    "mythic_agent.cli",
    "mythic_agent.terminal",
    "mythic_agent.mcp_server",
    "mythic_agent.doctor",
    "mythic_agent.onboarding",
    "mythic_agent.bench",
)

# ---------------------------------------------------------------------------
# Acknowledged exceptions: genuine rule hits that cannot be removed safely.
# Each entry documents WHY.  Adding an entry here requires a reason; the
# gate test asserts every exception still matches a live import (stale
# exceptions fail the suite so the list cannot rot).
# ---------------------------------------------------------------------------
# (source_pattern, forbidden_pattern, reason)
ACKNOWLEDGED_EXCEPTIONS: list[tuple[str, str, str]] = [
    (
        "mythic_agent.core.engine",
        "mythic_agent.agents.*",
        "engine.py is the application composition root: initialize() "
        "constructs the Primary Agent, registers it in AGENT_REGISTRY, and "
        "starts the agent loop thread.  Removing the agents import would "
        "require a dependency-injection container this codebase does not "
        "have; the coupling is deliberate and reviewed (2026-10-10).",
    ),
]


# ---------------------------------------------------------------------------
# Import-graph collection (stdlib ast)
# ---------------------------------------------------------------------------
class _ImportRecord(NamedTuple):
    module: str      # fully resolved dotted name that was imported
    lineno: int
    scope: str       # "module" | "deferred"
    names: tuple[str, ...]  # names bound by `from X import ...` (empty for plain `import X`)


class _Collector(ast.NodeVisitor):
    """Collect static imports, tracking scope and skipping TYPE_CHECKING."""

    def __init__(self, module_name: str) -> None:
        self.module_name = module_name
        self.records: list[_ImportRecord] = []
        self._depth = 0  # >0 inside a function/class/lambda body
        self._type_checking = 0

    # -- scope tracking ----------------------------------------------------
    def _scoped(self, node: ast.AST) -> None:
        self._depth += 1
        self.generic_visit(node)
        self._depth -= 1

    visit_FunctionDef = _scoped
    visit_AsyncFunctionDef = _scoped
    visit_ClassDef = _scoped
    visit_Lambda = _scoped

    def visit_If(self, node: ast.If) -> None:
        if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
            self._type_checking += 1
            self.generic_visit(node)
            self._type_checking -= 1
        else:
            self.generic_visit(node)

    # -- import resolution -------------------------------------------------
    def _package_of(self) -> list[str]:
        # Dotted package containing this module (the module itself if it is
        # a package __init__).
        parts = self.module_name.split(".")
        return parts if self._is_package_init else parts[:-1]

    @property
    def _is_package_init(self) -> bool:  # set per-file by collect()
        return getattr(self, "_package_init", False)

    def _resolve(self, level: int, name: str) -> str:
        if level == 0:
            return name
        base = self._package_of()
        if level - 1 > len(base):
            return name  # over-relative; leave as-is, never matches our rules
        prefix = base[: len(base) - (level - 1)]
        return ".".join(prefix + ([name] if name else []))

    def _emit(self, dotted: str, node: ast.AST, names: tuple[str, ...] = ()) -> None:
        if self._type_checking:
            return
        scope = "module" if self._depth == 0 else "deferred"
        self.records.append(_ImportRecord(dotted, node.lineno, scope, names))

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._emit(alias.name, node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module is None and node.level == 0:
            return
        dotted = self._resolve(node.level, node.module or "")
        names = tuple(a.name for a in node.names)
        self._emit(dotted, node, names)


def _iter_modules(package_dir: Path) -> Iterable[tuple[str, Path, bool]]:
    """Yield (dotted_name, path, is_package_init) for every .py under package_dir."""
    root_name = package_dir.name
    for path in sorted(package_dir.rglob("*.py")):
        rel = path.relative_to(package_dir).with_suffix("")
        parts = list(rel.parts)
        is_init = parts[-1] == "__init__"
        if is_init:
            parts = parts[:-1]
        dotted = ".".join([root_name] + parts)
        yield dotted, path, is_init


def collect_imports(package_dir: Path) -> dict[str, list[_ImportRecord]]:
    """Map each module to its static import records."""
    result: dict[str, list[_ImportRecord]] = {}
    for dotted, path, is_init in _iter_modules(package_dir):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue  # unparseable file: not our audit's job to report
        collector = _Collector(dotted)
        collector._package_init = is_init
        collector.visit(tree)
        result[dotted] = collector.records
    return result


def _matches(pattern: str, dotted: str) -> bool:
    # A pattern like "mythic_agent.ui.*" also covers the package itself
    # ("mythic_agent.ui"), e.g. `from mythic_agent.ui import widgets`.
    if fnmatch.fnmatchcase(dotted, pattern):
        return True
    if pattern.endswith(".*") and dotted == pattern[:-2]:
        return True
    return False


def check(
    package_dir: str | Path,
    rules: Iterable[Rule] = RULES,
    exceptions: Iterable[tuple[str, str, str]] = ACKNOWLEDGED_EXCEPTIONS,
    entry_modules: Iterable[str] = ENTRY_MODULES,
    package_prefix: str = "mythic_agent",
) -> list[Violation]:
    """Audit the import graph under *package_dir*; return structured violations.

    Acknowledged exceptions are subtracted so the gate stays green only for
    reviewed, documented coupling.  ``package_prefix`` / ``entry_modules``
    exist so tests can audit synthetic fixture trees.
    """
    package_dir = Path(package_dir)
    imports = collect_imports(package_dir)
    violations: list[Violation] = []
    for source, records in imports.items():
        for rec in records:
            if not rec.module.startswith(package_prefix):
                continue  # third-party / stdlib: out of scope
            if rec.module == source or rec.module.startswith(source + "."):
                continue  # self / submodule imports are internal structure
            for rule in rules:
                if rule.scope == "module" and rec.scope != "module":
                    continue
                if _matches(rule.source_pattern, source) and _matches(
                    rule.forbidden_pattern, rec.module
                ):
                    if any(
                        _matches(sp, source) and _matches(fp, rec.module)
                        for sp, fp, _ in exceptions
                    ):
                        continue
                    violations.append(
                        Violation(source, rec.module, rec.lineno, rec.scope, rule)
                    )
    # Entry-module public-interface rule: no underscore-private cross-module
    # imports (dunder names included -- they are private too).
    for source, records in imports.items():
        if source not in entry_modules:
            continue
        for rec in records:
            if not rec.module.startswith(package_prefix):
                continue
            if rec.module == source or rec.module.startswith(source + "."):
                continue
            for name in rec.names:
                if name == "*":
                    continue
                if name.startswith("_"):
                    violations.append(
                        Violation(
                            source,
                            f"{rec.module}.{name}",
                            rec.lineno,
                            rec.scope,
                            Rule(
                                source,
                                f"{package_prefix}.* (private name)",
                                "entry modules may only touch public interfaces: "
                                f"'{name}' is underscore-private in {rec.module}",
                            ),
                        )
                    )
    return sorted(violations, key=lambda v: (v.source_module, v.lineno))
