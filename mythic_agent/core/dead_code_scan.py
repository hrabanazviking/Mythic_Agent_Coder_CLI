"""Dead-code detection for the mythic_agent package.

A stdlib-only, AST-based scanner: vulture is not installed in the forge
venv and offline installs are not permitted, so this module provides an
equivalent capability without third-party dependencies.

Pipeline:
    items = scan(root)            -> list[DeadItem]
    write_quarantine(items, path) -> records the current dead-code inventory
    load_quarantine(path)         -> rereads it

A symbol is considered dead when it is *defined* in the package but never
*referenced* anywhere else in the package.  Whitelisted (never reported):

  * dunder names (``__init__``, ``__main__``, ...).
  * names listed in a module's ``__all__`` (public exports).
  * everything exported from ``__init__.py`` files.
  * console-script entry points declared in ``pyproject.toml``
    (``mythic_agent.cli:main``, ``mythic_agent.mcp_server:main``).
  * the convention hooks ``main``, ``main_cli`` and ``run_main``.
  * ``pytest``-style test helpers are irrelevant here because the scan only
    covers the ``mythic_agent/`` package, not ``tests/``.

References counted include: Name loads, attribute accesses
(``obj.method`` marks ``method`` referenced), decorators, base classes,
keyword argument names, ``getattr(obj, "name")`` string arguments, and
type-annotation strings.

``DeadItem`` is a plain 4-tuple ``(path, lineno, name, kind)`` with
``kind`` in ``{"function", "method", "class", "variable", "import"}``.
"""

from __future__ import annotations

import ast
import os
from typing import List, Optional, Tuple

DeadItem = Tuple[str, int, str, str]

# Console-script entry points from pyproject.toml [project.scripts].
_ENTRY_POINTS = {
    ("mythic_agent/cli.py", "main"),
    ("mythic_agent/mcp_server.py", "main"),
}

# Convention hooks that are called externally (shell, MCP hosts, docs).
_ENTRY_HOOK_NAMES = {"main", "main_cli", "run_main"}

# Names imported for a language/framework feature but never referenced as
# identifiers (``from __future__ import annotations``).
_FEATURE_IMPORTS = {"annotations"}

# Function-name hooks that are external plugin entry points
# (e.g. register_cli called by the CLI framework, registered via docstring).
_PLUGIN_HOOK_PREFIXES = ("register_",)

# Method-name hooks called by frameworks rather than by package code.
# - Textual TUI: on_*, action_*, watch_*, validate_*, render_*, compose
# - ast.NodeVisitor: visit_*
_METHOD_HOOK_PREFIXES = ("on_", "action_", "watch_", "validate_",
                         "render_", "visit_")
_METHOD_HOOK_NAMES = {"compose"}

# Class-level variables consumed by frameworks, not by package code.
_FRAMEWORK_VARS = {"CSS", "DEFAULT_CSS", "BINDINGS", "DEFAULT_THEME",
                   "_fields_"}  # ctypes.Structure field layout

_QUARANTINE_HEADER = "# Dead-code quarantine inventory"


def _iter_py_files(root: str) -> List[str]:
    files: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fn in filenames:
            if fn.endswith(".py"):
                files.append(os.path.join(dirpath, fn))
    return sorted(files)


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


class _DefCollector(ast.NodeVisitor):
    """First pass: collect every definition in a module."""

    def __init__(self) -> None:
        self.functions: List[Tuple[str, int]] = []
        self.methods: List[Tuple[str, int]] = []
        self.classes: List[Tuple[str, int]] = []
        self.variables: List[Tuple[str, int]] = []
        self.imports: List[Tuple[str, int]] = []  # (bound name, lineno)
        self.all_names: List[str] = []  # names listed in __all__
        self.from_source_names: List[str] = []  # names imported FROM a module
        self.registered_tools: List[str] = []  # functions registered as tools
        self._class_depth = 0
        self._func_depth = 0

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.append((node.name, node.lineno))
        self._class_depth += 1
        self.generic_visit(node)
        self._class_depth -= 1

    def _record_func(self, node) -> None:
        for deco in node.decorator_list:
            # @mcp.tool() / @<anything>.tool(...) registers an external
            # entry point (MCP tool, plugin) invoked by name over the wire
            func = deco.func if isinstance(deco, ast.Call) else deco
            if isinstance(func, ast.Attribute) and func.attr == "tool":
                self.registered_tools.append(node.name)
        if node.decorator_list:
            # any decorator receives the function object at definition time,
            # so it is a reference: rule registries (@_rule, @health_check),
            # @property, @lru_cache, etc. count as external hooks
            self.registered_tools.append(node.name)
        if self._class_depth:
            self.methods.append((node.name, node.lineno))
        else:
            self.functions.append((node.name, node.lineno))
        self._func_depth += 1
        self.generic_visit(node)
        self._func_depth -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._record_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._record_func(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        if self._func_depth == 0:  # module/class level only; locals excluded
            for target in node.targets:
                self._record_target(target, node.lineno)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if self._func_depth == 0:  # module/class level only; locals excluded
            self._record_target(node.target, node.lineno)
        self.generic_visit(node)

    def _record_target(self, target, lineno: int) -> None:
        if isinstance(target, ast.Name):
            self.variables.append((target.id, lineno))
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                self._record_target(elt, lineno)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            self.imports.append((name, node.lineno))
        # do not generic_visit: the names are definitions, not references

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            if alias.name == "*":
                continue
            name = alias.asname or alias.name
            self.imports.append((name, node.lineno))
            # the source name is *referenced* by this import, even though the
            # bound local name is a fresh definition
            self.from_source_names.append(alias.name)


class _RefCollector(ast.NodeVisitor):
    """Second pass: collect every referenced name across the whole package."""

    def __init__(self) -> None:
        self.names: set = set()      # plain Name ids and attribute names
        self.strings: set = set()    # string arguments that may be names

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self.names.add(node.attr)
        self.generic_visit(node)

    def visit_keyword(self, node: ast.keyword) -> None:
        if node.arg:
            self.names.add(node.arg)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # getattr(obj, "name") / setattr(obj, "name", v) -> string is a ref
        func = node.func
        is_getset = isinstance(func, ast.Name) and func.id in (
            "getattr", "setattr", "hasattr")
        if is_getset and len(node.args) >= 2:
            arg = node.args[1]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                self.strings.add(arg.value)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            # short identifier-like strings (e.g. tool names, hook names)
            value = node.value.strip()
            if value.isidentifier() and not value.startswith("_"):
                self.strings.add(value)
        self.generic_visit(node)


def _module_all_names(source_files: List[str]) -> dict:
    """Map relpath -> names listed in that module's ``__all__``."""
    result = {}
    for path in source_files:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=path)
        except (OSError, SyntaxError):
            continue
        names: List[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                targets = [t.id for t in node.targets
                           if isinstance(t, ast.Name)]
                if "__all__" in targets:
                    try:
                        value = ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        value = []
                    if isinstance(value, (list, tuple)):
                        names.extend(str(n) for n in value)
        result[path] = names
    return result


def scan(root: str) -> List[DeadItem]:
    """Scan the package at ``root`` and return dead-code items.

    ``root`` is the package directory (e.g. ``mythic_agent``).  Each item is
    ``(path, lineno, name, kind)`` sorted by (path, lineno).  Paths are
    repo-relative (``mythic_agent/...``) when ``root`` is given repo-relative,
    absolute otherwise.
    """
    root = os.path.normpath(root)
    files = _iter_py_files(root)
    all_names_map = _module_all_names(files)

    refs = _RefCollector()
    defs: List[Tuple[str, int, str, str]] = []  # (file, lineno, name, kind)
    import_from_source_names: set = set()
    registered_tools: set = set()  # (path, name) pairs

    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=path)
        except (OSError, SyntaxError):
            continue
        collector = _DefCollector()
        collector.visit(tree)
        refs.visit(tree)
        import_from_source_names.update(collector.from_source_names)
        for name in collector.registered_tools:
            registered_tools.add((path, name))
        is_init = os.path.basename(path) == "__init__.py"
        rel = os.path.relpath(path, root) if not os.path.isabs(root) \
            else path
        for name, lineno in collector.classes:            defs.append((path, lineno, name, "class"))
        for name, lineno in collector.functions:
            defs.append((path, lineno, name, "function"))
        for name, lineno in collector.methods:
            defs.append((path, lineno, name, "method"))
        for name, lineno in collector.variables:
            defs.append((path, lineno, name, "variable"))
        for name, lineno in collector.imports:
            # imports from __init__ files are re-exports; skip them
            if is_init:
                continue
            defs.append((path, lineno, name, "import"))

    ref_names = refs.names | refs.strings | import_from_source_names
    # collect whitelisted names per module
    whitelist: set = set()
    for path, names in all_names_map.items():
        for name in names:
            whitelist.add((path, name))
    init_names: set = set()
    for path in files:
        if os.path.basename(path) != "__init__.py":
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=path)
        except (OSError, SyntaxError):
            continue
        c = _DefCollector()
        c.visit(tree)
        for name, _ in (c.functions + c.classes + c.imports):
            init_names.add((path, name))

    dead: List[DeadItem] = []
    for path, lineno, name, kind in defs:
        if _is_dunder(name):
            continue
        if kind == "import" and name in _FEATURE_IMPORTS:
            continue  # from __future__ import annotations etc.
        if kind == "method" and (
                name in _METHOD_HOOK_NAMES
                or name.startswith(_METHOD_HOOK_PREFIXES)):
            continue  # framework-dispatched hook
        if kind == "variable" and name in _FRAMEWORK_VARS:
            continue  # framework-consumed class variable
        if kind == "variable" and (
                name.startswith(_METHOD_HOOK_PREFIXES)
                or name in _METHOD_HOOK_NAMES):
            continue  # e.g. visit_AsyncFunctionDef = visit_FunctionDef alias
        if kind == "function" and name.startswith(_PLUGIN_HOOK_PREFIXES):
            continue  # plugin entry point
        if (path, name) in registered_tools:
            continue  # registered external tool/plugin entry point
        if (path, name) in whitelist:
            continue  # listed in __all__
        if (path, name) in init_names:
            continue  # __init__ export surface
        rel = os.path.relpath(path, root)
        # repo-relative display path, e.g. "mythic_agent/cli.py"
        if os.path.isabs(root):
            out_path = path
        else:
            out_path = os.path.join(os.path.basename(root), rel)
        if (out_path, name) in _ENTRY_POINTS:
            continue  # console-script entry point
        if name in _ENTRY_HOOK_NAMES:
            continue  # external hook convention
        if name in ref_names:
            continue
        # a module-level name shadowed by a same-named import in another
        # module would have been caught by the ref pass; here it is dead.
        dead.append((out_path, lineno, name, kind))

    dead.sort(key=lambda item: (item[0], item[1]))
    return dead


def write_quarantine(items: List[DeadItem], path: str) -> None:
    """Write the dead-code inventory to ``path`` (one record per line).

    Format: ``file:lineno:name:kind`` under a ``#`` header line.
    """
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(_QUARANTINE_HEADER + "\n")
        fh.write("# format: path:lineno:name:kind\n")
        for item_path, lineno, name, kind in items:
            fh.write(f"{item_path}:{lineno}:{name}:{kind}\n")


def load_quarantine(path: str) -> List[DeadItem]:
    """Read a quarantine file written by :func:`write_quarantine`."""
    items: List[DeadItem] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.rsplit(":", 3)
            if len(parts) != 4:
                continue
            item_path, lineno_s, name, kind = parts
            try:
                lineno = int(lineno_s)
            except ValueError:
                continue
            items.append((item_path, lineno, name, kind))
    return items


def main(argv: Optional[List[str]] = None) -> int:
    """CLI: ``python -m mythic_agent.core.dead_code_scan [root]``."""
    import sys
    args = sys.argv[1:] if argv is None else argv
    root = args[0] if args else "mythic_agent"
    items = scan(root)
    for item_path, lineno, name, kind in items:
        print(f"{item_path}:{lineno}: {name} ({kind})")
    print(f"{len(items)} dead-code item(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
