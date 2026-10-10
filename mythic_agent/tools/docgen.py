"""Documentation generation (Slice 43).

``generate_docstring`` synthesizes a NumPy-style docstring for a Python
function via AST analysis. ``generate_readme`` scaffolds a project
README from the on-disk structure. No model calls are involved, so both
are deterministic and offline.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "Optional",
    "Path",
    "date",
    "describe_signature",
    "generate_docstring",
    "generate_readme",
]

import ast
import textwrap
from datetime import date
from pathlib import Path
from typing import Any, Optional

__all__ = ["generate_docstring", "generate_readme", "describe_signature"]


def _unparse(node: Optional[ast.AST]) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return "..."


def _type_hint(annotation: Optional[ast.AST]) -> str:
    text = _unparse(annotation)
    return text or "Any"


def describe_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Render a readable ``name(arg: type, ...) -> ret`` signature."""
    args = node.args
    parts: list[str] = []
    positional = list(args.posonlyargs) + list(args.args)
    defaults = list(args.defaults)
    default_start = len(positional) - len(defaults)
    for i, arg in enumerate(positional):
        name = arg.arg
        if name in ("self", "cls") and i == 0:
            parts.append(name)
            continue
        text = f"{name}: {_type_hint(arg.annotation)}"
        if i >= default_start:
            text += f" = {_unparse(defaults[i - default_start])}"
        parts.append(text)
    for i, (arg, default) in enumerate(zip(args.kwonlyargs, args.kw_defaults)):
        if i == 0 and not args.vararg:
            parts.append("*")  # bare separator before keyword-only args
        text = f"{arg.arg}: {_type_hint(arg.annotation)}"
        if default is not None:
            text += f" = {_unparse(default)}"
        parts.append(text)
    if args.vararg:
        parts.append(f"*{args.vararg.arg}: {_type_hint(args.vararg.annotation)}")
    if args.kwarg:
        parts.append(f"**{args.kwarg.arg}: {_type_hint(args.kwarg.annotation)}")
    returns = _type_hint(node.returns) if node.returns else "None"
    kind = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return f"{kind}def {node.name}({', '.join(p for p in parts if p)}) -> {returns}"


def _raised_exceptions(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    raised: list[str] = []

    class _RaiseVisitor(ast.NodeVisitor):
        def visit_Raise(self, n: ast.Raise) -> None:
            if n.exc is not None:
                name = _unparse(n.exc).split("(")[0]
                if name and name not in raised:
                    raised.append(name)

    _RaiseVisitor().visit(node)
    return raised


def _returns_value(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Return) and child.value is not None:
            return True
    return False


def generate_docstring(func: Any) -> str:
    """Generate a NumPy-style docstring for a Python function.

    Accepts a function object, a source string, or an AST node.
    The generated docstring includes a one-line summary inferred from
    the function name, a Parameters section derived from annotations
    and defaults, and Returns / Raises sections when detectable.
    Existing docstrings are left untouched (returned as-is).
    """
    node: Optional[ast.FunctionDef | ast.AsyncFunctionDef] = None
    source_name = "function"

    if isinstance(func, str):
        tree = ast.parse(textwrap.dedent(func))
        for child in ast.walk(tree):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                node = child
                break
        if node is None:
            raise ValueError("no function definition found in source string")
    elif isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
        node = func
    elif callable(func):
        try:
            import inspect
            src = textwrap.dedent(inspect.getsource(func))
        except (OSError, TypeError) as exc:
            raise ValueError(f"cannot retrieve source for {func!r}") from exc
        return generate_docstring(src)
    else:
        raise TypeError(f"expected function, source string, or AST node; got {type(func).__name__}")

    assert node is not None
    source_name = node.name
    if ast.get_docstring(node):
        return ast.get_docstring(node, clean=False) or ""

    # One-line summary from the name: split snake_case into words.
    words = source_name.replace("__", " ").strip("_").split("_")
    summary = " ".join(w for w in words if w).capitalize() + "."

    lines = [summary, ""]
    args = node.args
    params = [a for a in list(args.posonlyargs) + list(args.args)
              if not (a.arg in ("self", "cls"))]
    params += list(args.kwonlyargs)
    if args.vararg:
        params.append(args.vararg)
    if args.kwarg:
        params.append(args.kwarg)

    if params:
        lines.append("Parameters")
        lines.append("----------")
        for param in params:
            lines.append(f"{param.arg} : {_type_hint(param.annotation)}")
            lines.append(f"    {param.arg.replace('_', ' ').capitalize()}.")
        lines.append("")

    if _returns_value(node):
        ret = _type_hint(node.returns) if node.returns else "Any"
        lines.append("Returns")
        lines.append("-------")
        lines.append(f"{ret}")
        lines.append("    Result of the computation.")
        lines.append("")

    raised = _raised_exceptions(node)
    if raised:
        lines.append("Raises")
        lines.append("------")
        for exc in raised:
            lines.append(f"{exc}")
            lines.append(f"    When {exc} is raised.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _project_tree(root: Path, max_depth: int = 2) -> list[str]:
    lines: list[str] = []
    skip = {".git", ".hg", "__pycache__", ".venv", "venv", "node_modules",
            ".mythic", ".tox", ".eggs", "*.egg-info", "dist", "build"}

    def walk(dirpath: Path, prefix: str, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            entries = sorted(dirpath.iterdir(),
                             key=lambda p: (p.is_file(), p.name.lower()))
        except OSError:
            return
        entries = [e for e in entries
                   if e.name not in skip and not e.name.endswith(".egg-info")]
        for i, entry in enumerate(entries):
            last = i == len(entries) - 1
            connector = "└── " if last else "├── "
            lines.append(f"{prefix}{connector}{entry.name}")
            if entry.is_dir():
                walk(entry, prefix + ("    " if last else "│   "), depth + 1)

    walk(root, "", 0)
    return lines


def _detect_project_meta(root: Path) -> dict[str, str]:
    meta = {"name": root.name, "description": "", "license": ""}
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        try:
            import tomllib
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            project = data.get("project", {})
            meta["name"] = str(project.get("name", meta["name"]))
            meta["description"] = str(project.get("description", ""))
            meta["license"] = str(project.get("license", {}).get("text", "")
                                  if isinstance(project.get("license"), dict)
                                  else project.get("license", ""))
        except Exception:
            pass
    return meta


def generate_readme(project_root: str | Path) -> str:
    """Scaffold a Markdown README from a project's on-disk structure.

    Includes the project name/description (from ``pyproject.toml`` when
    present), a directory tree, top-level Python modules, install
    instructions, and a testing section.
    """
    root = Path(project_root)
    if not root.is_dir():
        raise ValueError(f"not a directory: {project_root}")
    meta = _detect_project_meta(root)

    py_files = sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)
    top_modules = sorted({p.relative_to(root).parts[0].removesuffix(".py")
                          for p in py_files if len(p.relative_to(root).parts) == 1})
    packages = sorted({p.relative_to(root).parts[0]
                       for p in py_files
                       if len(p.relative_to(root).parts) > 1
                       and (p.parent / "__init__.py").exists()})

    has_tests = (root / "tests").is_dir() or any("test" in p.name for p in py_files)
    has_pyproject = (root / "pyproject.toml").is_file()
    has_requirements = (root / "requirements.txt").is_file()

    lines = [
        f"# {meta['name']}",
        "",
    ]
    if meta["description"]:
        lines += [meta["description"], ""]
    lines += [
        f"*Generated by Mythic Agent on {date.today().isoformat()}.*",
        "",
        "## Project structure",
        "",
        "```",
        root.name + "/",
    ]
    lines += _project_tree(root)
    lines += ["```", ""]

    if top_modules or packages:
        lines += ["## Modules", ""]
        for mod in top_modules:
            doc = ""
            mod_file = root / f"{mod}.py"
            try:
                tree = ast.parse(mod_file.read_text(encoding="utf-8", errors="replace"))
                doc = (ast.get_docstring(tree) or "").strip().splitlines()[0] \
                    if ast.get_docstring(tree) else ""
            except (SyntaxError, OSError):
                pass
            lines.append(f"- `{mod}`" + (f" — {doc}" if doc else ""))
        for pkg in packages:
            lines.append(f"- `{pkg}/` (package)")
        lines.append("")

    lines += ["## Installation", ""]
    if has_pyproject:
        lines += ["```bash", "pip install -e .", "```", ""]
    elif has_requirements:
        lines += ["```bash", "pip install -r requirements.txt", "```", ""]
    else:
        lines += ["No packaging metadata found; add a `pyproject.toml` to make",
                  "the project installable.", ""]

    if has_tests:
        lines += ["## Testing", "", "```bash", "pytest", "```", ""]

    if meta["license"]:
        lines += ["## License", "", meta["license"], ""]

    return "\n".join(lines)
