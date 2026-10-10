"""Public API inventory gate (forge run 2026-10-10, R-003 / roadmap 003).

Every non-test module in ``mythic_agent/`` must define ``__all__`` (or be a
documented intentional exclusion), and every name listed must actually exist
on the module — so the public surface is inventoried, not implied.
"""

import ast
import importlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PKG_DIR = REPO_ROOT / "mythic_agent"

# Package-namespace modules: they re-export via plain imports; the API
# surface lives in the leaf modules.  Documented here, not forgotten.
INTENTIONALLY_PRIVATE = {
    "mythic_agent.__init__": "top-level package namespace",
    "mythic_agent.agents.__init__": "subpackage namespace",
    "mythic_agent.core.__init__": "subpackage namespace",
    "mythic_agent.data.__init__": "subpackage namespace",
    "mythic_agent.integrations.__init__": "subpackage namespace",
    "mythic_agent.memory.__init__": "subpackage namespace",
    "mythic_agent.providers.__init__": "subpackage namespace",
    "mythic_agent.ui.__init__": "subpackage namespace",
    "mythic_agent.ui.components.__init__": "subpackage namespace",
    "mythic_agent.ui.screens.__init__": "subpackage namespace",
}

# Modules that cannot be imported in this minimal environment (missing
# optional third-party deps).  They are still AST-scanned for ``__all__``
# presence; only the attribute-existence rot check is skipped.
UNIMPORTABLE_IN_THIS_ENV = {
    "mythic_agent.core.tts": "piper-tts missing (pre-existing NameError at import)",
    "mythic_agent.mcp_server": "mcp package not installed",
    "mythic_agent.ui.components.modals": "textual not installed",
    "mythic_agent.ui.components.subagent_editor": "textual not installed",
    "mythic_agent.ui.components.subagent_modal": "textual not installed",
    "mythic_agent.ui.main_app": "textual not installed",
    "mythic_agent.ui.screens.chat_screen": "textual not installed",
    "mythic_agent.ui.screens.setup_screen": "textual not installed",
    "mythic_agent.ui.screens.splash_screen": "textual not installed",
}


def _iter_modules():
    for path in sorted(PKG_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        dotted = str(path.relative_to(REPO_ROOT))[:-3].replace("/", ".")
        yield dotted, path


def read_all_names(path: Path) -> list[str] | None:
    """Return the module's ``__all__`` names via AST, or None if absent."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "__all__"
        ):
            return [
                elt.value
                for elt in node.value.elts
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            ]
    return None


def validate_module(dotted: str, path: Path) -> list[str]:
    """Return human-readable problems with a module's public API surface."""
    problems = []
    names = read_all_names(path)
    if names is None:
        reason = INTENTIONALLY_PRIVATE.get(dotted)
        if reason is None:
            problems.append(f"{dotted}: no __all__ and not in INTENTIONALLY_PRIVATE")
        return problems
    if dotted in INTENTIONALLY_PRIVATE:
        problems.append(f"{dotted}: has __all__ but is listed in INTENTIONALLY_PRIVATE")
    if len(names) != len(set(names)):
        problems.append(f"{dotted}: duplicate entries in __all__")
    for name in names:
        if name.startswith("_") and not (name.startswith("__") and name.endswith("__")):
            problems.append(f"{dotted}: private name {name!r} in __all__")
    if dotted in UNIMPORTABLE_IN_THIS_ENV:
        return problems  # presence checked; existence check needs an import
    try:
        module = importlib.import_module(dotted)
    except Exception as exc:  # noqa: BLE001 - environment-dependent, reported not raised
        problems.append(f"{dotted}: import failed unexpectedly: {type(exc).__name__}: {exc}")
        return problems
    for name in names:
        if not hasattr(module, name):
            problems.append(f"{dotted}: __all__ names {name!r} but module has no such attribute")
    return problems


def test_every_module_has_all_or_is_documented():
    failures = []
    for dotted, path in _iter_modules():
        names = read_all_names(path)
        if names is None and dotted not in INTENTIONALLY_PRIVATE:
            failures.append(f"{dotted}: no __all__ and not documented in INTENTIONALLY_PRIVATE")
        if names is not None and dotted in INTENTIONALLY_PRIVATE:
            failures.append(f"{dotted}: gained __all__; remove it from INTENTIONALLY_PRIVATE")
    # anti-rot: every documented exclusion must still exist and still lack __all__
    existing = {dotted for dotted, _ in _iter_modules()}
    for dotted in INTENTIONALLY_PRIVATE:
        assert dotted in existing, f"INTENTIONALLY_PRIVATE entry {dotted} no longer exists"
    assert not failures, "\n".join(failures)


def test_all_names_exist_and_are_public():
    failures = []
    for dotted, path in _iter_modules():
        failures.extend(validate_module(dotted, path))
    assert not failures, "\n".join(failures)


def test_validator_catches_missing_attribute(tmp_path, monkeypatch):
    """Negative control: the validator must flag __all__ entries that don't exist."""
    fixture = tmp_path / "fixture_mod.py"
    fixture.write_text('__all__ = ["real_thing", "ghost_thing"]\nreal_thing = 1\n')
    monkeypatch.syspath_prepend(str(tmp_path))
    problems = validate_module("fixture_mod", fixture)
    assert any("ghost_thing" in p and "no such attribute" in p for p in problems), (
        f"validator failed to flag the missing attribute; problems={problems}"
    )
    assert not any("real_thing" in p for p in problems)


def test_public_api_inventory_doc_is_synchronized():
    """docs/PUBLIC_API.md must reflect the live scan (regenerate when the API changes)."""
    doc = (REPO_ROOT / "docs" / "PUBLIC_API.md").read_text(encoding="utf-8")
    live_total = sum(
        len(names) for _, path in _iter_modules() if (names := read_all_names(path)) is not None
    )
    assert f"TOTAL: {live_total} public names" in doc, (
        f"docs/PUBLIC_API.md is out of sync: live scan finds {live_total} public names; "
        "regenerate the doc"
    )
