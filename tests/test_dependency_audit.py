"""Dependency/extras audit (R-004 / roadmap slice 004).

Every third-party module imported anywhere in ``mythic_agent/`` must be
declared in ``pyproject.toml`` — either in the core ``dependencies`` or in
one of the ``[project.optional-dependencies]`` extras.  This test scans the
live tree with ``ast`` (no imports are executed) and fails on:

* an import with no declared requirement (this is how the missing
  ``anthropic``/``google`` extras and the undeclared ``torch`` import in
  ``core/tts.py`` were found);
* an ``httpx``/``httpx2`` import outside the declared
  ``try: import httpx2 / except ImportError: import httpx`` fallback shape;
* an extra referenced by install hints in code (``mythic-agent[<name>]``)
  that does not exist in ``pyproject.toml``;
* a ``try/except ImportError`` optional import whose feature is not
  recorded in :data:`OPTIONAL_IMPORT_FEATURES`.

Warn-only (print, do not fail): extras declared in ``pyproject.toml`` that
no module in ``mythic_agent/`` imports.  The ``dev`` extra is intentionally
unused by the package (pytest/build tooling only).  Any *other* unused
extra fails the test so genuinely dead extras get proposed for removal.

Packaging hygiene: license metadata must be present in ``pyproject.toml``,
and any ``requirements*.txt``/lockfile at the repo root must be referenced
in docs or it is reported as drift.
"""

from __future__ import annotations

import ast
import re
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = REPO_ROOT / "mythic_agent"
PYPROJECT = REPO_ROOT / "pyproject.toml"

# Third-party top-level import -> PEP 503 normalized requirement name.
# Derived from real usage in this tree (not invented).
IMPORT_TO_REQUIREMENT = {
    "openai": "openai",
    "prompt_toolkit": "prompt-toolkit",
    "rich": "rich",
    "filelock": "filelock",
    "yaml": "pyyaml",
    "httpx": "httpx",
    "httpx2": "httpx2",
    "textual": "textual",
    "textual_image": "textual-image",
    "PIL": "pillow",
    "pyperclip": "pyperclip",
    "mcp": "mcp",
    "psycopg": "psycopg",
    "requests": "requests",
    "sounddevice": "sounddevice",
    "numpy": "numpy",
    "scipy": "scipy",
    "piper": "piper-tts",
    "pydub": "pydub",
    "chatterbox": "chatterbox-tts",
    "torch": "torch",
    "anthropic": "anthropic",
    "google": "google-generativeai",
}

# Every third-party import that lives inside a ``try/except ImportError``
# guard, mapped to the feature it enables.  Derived from the real import
# sites in this tree (see tests: R-004 survey).  A new optional import of a
# package not listed here fails the feature-registry test until its feature
# is recorded.  (In-code one-line feature comments at these sites are the
# recommended follow-up; this registry is the enforced record for now.)
OPTIONAL_IMPORT_FEATURES = {
    "sounddevice": "audio recording/playback (voice extra)",
    "numpy": "audio array math + fast cosine similarity in the vector DB (voice extra)",
    "scipy": "WAV file writing for audio capture (voice extra)",
    "requests": "HTTP for TTS cloud backends (NovelAI/MOSS) and knowledge tools (voice/knowledge extras)",
    "piper": "Piper on-device TTS voices (voice extra)",
    "chatterbox": "Chatterbox voice-cloning TTS (voice-cloning extra)",
    "mcp": "MCP server via FastMCP (mcp extra)",
    "anthropic": "Anthropic provider SDK (anthropic extra)",
    "google": "Google Gemini provider SDK (google extra)",
    "yaml": "optional YAML data loading with graceful fallback (core dependency)",
    "httpx": "async HTTP client fallback for provider calls (core dependency)",
    "httpx2": "async HTTP client preferred for provider calls; openai 3.x's httpx fork (core dependency)",
}

# Extras that are intentionally never imported by ``mythic_agent/`` itself
# (build/test tooling).  Any other unused extra is reported and fails.
EXPECTED_UNUSED_EXTRAS = {"dev"}


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _req_name(req: str) -> str:
    return _normalize(req.split(";")[0].split("[")[0].split(">")[0]
                      .split("<")[0].split("=")[0].split("!")[0].strip())


def declared_requirements(pyproject: Path = PYPROJECT) -> set[str]:
    """All requirement names declared in core deps + every extra, normalized."""
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = data["project"]
    declared: set[str] = set()
    for req in project.get("dependencies", []):
        declared.add(_req_name(req))
    for extra_reqs in project.get("optional-dependencies", {}).values():
        for req in extra_reqs:
            declared.add(_req_name(req))
    return declared


def declared_extras(pyproject: Path = PYPROJECT) -> set[str]:
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return set(data["project"].get("optional-dependencies", {}))


def extra_requirements(pyproject: Path = PYPROJECT) -> dict[str, set[str]]:
    """extra name -> normalized requirement names it declares."""
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return {name: {_req_name(r) for r in reqs}
            for name, reqs in data["project"].get("optional-dependencies", {}).items()}


def third_party_imports(package_dir: Path = PACKAGE_DIR) -> dict[str, set[str]]:
    """Map top-level third-party import name -> set of importing files (relative)."""
    stdlib = set(sys.stdlib_module_names)
    found: dict[str, set[str]] = {}
    for path in sorted(package_dir.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            name: str | None = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.split(".")[0]
                    if name not in stdlib and name != package_dir.name:
                        found.setdefault(name, set()).add(str(path.relative_to(package_dir.parent)))
            elif isinstance(node, ast.ImportFrom):
                if node.level:  # relative import: within the package
                    continue
                if node.module:
                    name = node.module.split(".")[0]
                    if name not in stdlib and name != package_dir.name:
                        found.setdefault(name, set()).add(str(path.relative_to(package_dir.parent)))
    return found


def _catches_import_error(try_node: ast.Try) -> bool:
    for handler in try_node.handlers:
        t = handler.type
        if isinstance(t, ast.Name) and t.id == "ImportError":
            return True
        if isinstance(t, ast.Tuple) and any(
                isinstance(e, ast.Name) and e.id == "ImportError" for e in t.elts):
            return True
    return False


def optional_third_party_imports(
        package_dir: Path = PACKAGE_DIR) -> dict[str, set[str]]:
    """Third-party imports guarded by ``try/except ImportError``.

    Returns import name -> set of ``"file:line"`` sites.  Nested ``try``
    blocks are attributed to their own innermost guard.
    """
    stdlib = set(sys.stdlib_module_names)
    found: dict[str, set[str]] = {}

    def record(node: ast.Import | ast.ImportFrom, path: Path) -> None:
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            names = [node.module.split(".")[0]]
        rel = str(path.relative_to(package_dir.parent))
        for name in names:
            if name and name not in stdlib and name != package_dir.name:
                found.setdefault(name, set()).add(f"{rel}:{node.lineno}")

    for path in sorted(package_dir.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        # innermost ImportError-guard for each import, via explicit recursion
        def visit(node: ast.AST, guard: ast.Try | None) -> None:
            if isinstance(node, ast.Try):
                inner_guard = node if _catches_import_error(node) else guard
                for child in ast.iter_child_nodes(node):
                    visit(child, inner_guard)
                return
            if isinstance(node, (ast.Import, ast.ImportFrom)) and guard is not None:
                record(node, path)
                return
            for child in ast.iter_child_nodes(node):
                visit(child, guard)
        visit(tree, None)
    return found


def audit(package_dir: Path = PACKAGE_DIR,
          pyproject: Path = PYPROJECT) -> dict[str, object]:
    """Return {'undeclared': {import: files}, 'missing_extras': [...], 'unknown_mapping': [...]}."""
    declared = declared_requirements(pyproject)
    extras = declared_extras(pyproject)
    imports = third_party_imports(package_dir)
    undeclared: dict[str, set[str]] = {}
    unknown_mapping: list[str] = []
    for name, files in imports.items():
        req = IMPORT_TO_REQUIREMENT.get(name)
        if req is None:
            unknown_mapping.append(name)
        elif _normalize(req) not in declared:
            undeclared[name] = files
    # extras referenced by install hints in the code must exist
    hinted = set()
    for path in package_dir.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        hinted.update(re.findall(r"mythic-agent\[([a-z0-9_-]+)\]", path.read_text(encoding="utf-8")))
    missing_extras = sorted(h for h in hinted if h not in extras)
    return {
        "undeclared": undeclared,
        "unknown_mapping": sorted(unknown_mapping),
        "missing_extras": missing_extras,
        "hinted_extras": sorted(hinted),
    }


# ------------------------------------------------------------------ tests


def test_every_third_party_import_is_declared():
    result = audit()
    assert result["unknown_mapping"] == [], (
        f"imports with no requirement mapping: {result['unknown_mapping']}")
    assert result["undeclared"] == {}, (
        "third-party imports missing from pyproject.toml: "
        + ", ".join(f"{name} (used in {sorted(files)[0]})"
                    for name, files in result["undeclared"].items()))


def test_hinted_extras_exist():
    result = audit()
    assert result["missing_extras"] == [], (
        f"code references mythic-agent[extra] that is not declared: {result['missing_extras']}")


def test_httpx_fallback_pattern():
    """The httpx/httpx2 import must be a declared try/except fallback.

    ``httpx2`` is real: it is openai 3.x's renamed httpx fork, installed in
    the venv as openai's hard dependency.  Plain ``httpx`` is the declared
    fallback for environments where only it exists.  Both are declared in
    ``pyproject.toml`` core dependencies, and every import site must use the
    ``try: import httpx2 / except ImportError: import httpx`` shape -- a bare
    ``import httpx`` breaks where only httpx2 is installed and vice versa.
    """
    hits = []
    for path in PACKAGE_DIR.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Import):
                continue
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top not in ("httpx", "httpx2"):
                    continue
                parent = _enclosing_try(tree, node)
                ok = (
                    parent is not None
                    and _catches_import_error(parent)
                    and _try_imports_httpx2_first(parent)
                )
                if not ok:
                    hits.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}")
    assert hits == [], f"httpx/httpx2 imported outside the declared fallback pattern: {hits}"


def _enclosing_try(tree: ast.AST, node: ast.AST) -> ast.Try | None:
    found = None
    for parent in ast.walk(tree):
        if isinstance(parent, ast.Try) and any(n is node for n in ast.walk(parent)):
            # keep the innermost Try containing the node
            if found is None or any(n is parent for n in ast.walk(found)):
                inner = [t for t in ast.walk(parent)
                         if isinstance(t, ast.Try) and t is not parent
                         and any(n is node for n in ast.walk(t))]
                found = inner[0] if inner else parent
    return found


def _try_imports_httpx2_first(try_node: ast.Try) -> bool:
    """The try body must import httpx2 and some handler must import httpx."""
    def _names(stmts):
        out = set()
        for s in stmts:
            for n in ast.walk(s):
                if isinstance(n, ast.Import):
                    out.update(a.name.split(".")[0] for a in n.names)
        return out
    handler_names = set()
    for h in try_node.handlers:
        handler_names |= _names(h.body)
    return "httpx2" in _names(try_node.body) and "httpx" in handler_names


def test_audit_catches_undeclared_import(tmp_path):
    pkg = tmp_path / "fakepkg"
    pkg.mkdir()
    (pkg / "mod.py").write_text("import some_obscure_undeclared_lib\n", encoding="utf-8")
    found = third_party_imports(pkg)
    assert "some_obscure_undeclared_lib" in found
    assert IMPORT_TO_REQUIREMENT.get("some_obscure_undeclared_lib") is None


def test_import_mapping_covers_live_tree():
    imports = third_party_imports()
    unmapped = [name for name in imports if name not in IMPORT_TO_REQUIREMENT]
    assert unmapped == [], f"live imports missing from the mapping table: {unmapped}"


def test_mapping_table_has_no_typos():
    declared = declared_requirements()
    for import_name, req in IMPORT_TO_REQUIREMENT.items():
        assert _normalize(req) in declared, (
            f"mapping claims {import_name} -> {req}, but {req} is not declared in pyproject.toml")


def test_optional_imports_name_their_feature():
    """Every ``try/except ImportError`` third-party import must have its
    enabled feature recorded in :data:`OPTIONAL_IMPORT_FEATURES`."""
    optional = optional_third_party_imports()
    undocumented = sorted(name for name in optional if name not in OPTIONAL_IMPORT_FEATURES)
    assert undocumented == [], (
        "try/except ImportError imports with no recorded feature: "
        + ", ".join(f"{name} (at {sorted(optional[name])[0]})" for name in undocumented))
    # the registry itself must stay honest: every entry must be a real
    # optional import site in the live tree (no invented entries)
    stale = sorted(name for name in OPTIONAL_IMPORT_FEATURES if name not in optional)
    assert stale == [], (
        f"feature registry entries with no live optional import site: {stale}")


def test_unused_extras_are_reported(capsys):
    """Warn-only report of declared extras no module imports.

    Prints the report; fails only if an *unexpected* extra is unused (the
    ``dev`` extra is intentionally package-import-free).  A genuinely dead
    extra should be proposed for removal, not silently kept.
    """
    imports = third_party_imports()
    used_reqs = {_normalize(IMPORT_TO_REQUIREMENT[name])
                 for name in imports if name in IMPORT_TO_REQUIREMENT}
    extras = extra_requirements()
    unused = sorted(name for name, reqs in extras.items() if reqs.isdisjoint(used_reqs))
    print("\n[dependency-audit] extras usage report:")
    for name in sorted(extras):
        reqs = sorted(extras[name])
        status = "UNUSED by mythic_agent/" if name in unused else "used"
        print(f"  extra {name!r}: {status} (declares: {', '.join(reqs)})")
    if unused:
        print(f"[dependency-audit] unused extras (warn-only): {', '.join(unused)}")
    unexpected = [name for name in unused if name not in EXPECTED_UNUSED_EXTRAS]
    assert unexpected == [], (
        f"extras declared but imported by no module (propose removal): {unexpected}")


def test_packaging_hygiene(capsys):
    """License metadata present; no drifting requirements/lockfiles."""
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    project = data["project"]
    license_meta = project.get("license")
    print(f"\n[dependency-audit] license metadata in pyproject: {license_meta!r}")
    assert license_meta, "no license metadata in [project] (pyproject.toml)"

    lockfile_names = ("requirements.txt", "requirements-dev.txt", "requirements_test.txt",
                      "Pipfile", "Pipfile.lock", "poetry.lock", "uv.lock",
                      "setup.py", "setup.cfg")
    found = [name for name in lockfile_names if (REPO_ROOT / name).exists()]
    print(f"[dependency-audit] requirements/lockfiles at repo root: {found or 'none'}")
    for name in found:
        blob = "\n".join(p.read_text(encoding="utf-8", errors="replace")
                         for p in REPO_ROOT.rglob("*.md"))
        referenced = name in blob or name in PYPROJECT.read_text(encoding="utf-8")
        assert referenced, (
            f"{name} exists at repo root but is referenced nowhere (drift)")
