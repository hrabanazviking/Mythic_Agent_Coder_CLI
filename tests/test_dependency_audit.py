"""Dependency/extras audit (R-004 / roadmap slice 004).

Every third-party module imported anywhere in ``mythic_agent/`` must be
declared in ``pyproject.toml`` — either in the core ``dependencies`` or in
one of the ``[project.optional-dependencies]`` extras.  This test scans the
live tree with ``ast`` (no imports are executed) and fails on:

* an import with no declared requirement (the ``httpx2`` phantom-import bug
  and the missing ``anthropic``/``google`` extras were found this way);
* an extra referenced by install hints in code (``mythic-agent[<name>]``)
  that does not exist in ``pyproject.toml``.
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
    "torch": "torchaudio",
    "anthropic": "anthropic",
    "google": "google-generativeai",
}


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def declared_requirements(pyproject: Path = PYPROJECT) -> set[str]:
    """All requirement names declared in core deps + every extra, normalized."""
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = data["project"]
    declared: set[str] = set()
    for req in project.get("dependencies", []):
        declared.add(_normalize(req.split(";")[0].split("[")[0].split(">")[0].split("<")[0].split("=")[0].strip()))
    for extra_reqs in project.get("optional-dependencies", {}).values():
        for req in extra_reqs:
            declared.add(_normalize(req.split(";")[0].split("[")[0].split(">")[0].split("<")[0].split("=")[0].strip()))
    return declared


def declared_extras(pyproject: Path = PYPROJECT) -> set[str]:
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return set(data["project"].get("optional-dependencies", {}))


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


def test_no_phantom_httpx2_import():
    """Regression: the bogus ``import httpx2`` fallback is gone."""
    hits = [str(p) for p in PACKAGE_DIR.rglob("*.py")
            if "__pycache__" not in p.parts and "httpx2" in p.read_text(encoding="utf-8")]
    assert hits == [], f"phantom httpx2 references remain in: {hits}"


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
