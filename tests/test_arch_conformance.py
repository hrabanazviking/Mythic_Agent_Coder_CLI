"""Tests for the architecture conformance audit (R-002).

* Fixture-tree tests prove ``check()`` returns structured violations and
  catches a rule-violating file pair, using a synthetic package so the tests
  never depend on (or invent) violations in the real tree.
* The gate test audits the live ``mythic_agent/`` tree and requires ZERO
  violations.
"""

from pathlib import Path

import pytest

from mythic_agent.core.arch_conformance import (
    ACKNOWLEDGED_EXCEPTIONS,
    ENTRY_MODULES,
    RULES,
    Rule,
    Violation,
    check,
    collect_imports,
)

PACKAGE_DIR = Path(__file__).resolve().parent.parent / "mythic_agent"


def _write_tree(root: Path) -> Path:
    """Build a synthetic violating package tree; return its package dir."""
    pkg = root / "fake_pkg"
    (pkg / "core").mkdir(parents=True)
    (pkg / "ui").mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "core" / "__init__.py").write_text("")
    (pkg / "ui" / "__init__.py").write_text("")
    (pkg / "ui" / "widgets.py").write_text("VALUE = 1\n_secret = 2\n")
    # Module-level forbidden import (core -> ui).
    (pkg / "core" / "engine.py").write_text(
        "from fake_pkg.ui import widgets\n\n\ndef run():\n    return widgets.VALUE\n"
    )
    # Deferred (function-local) forbidden import.
    (pkg / "core" / "lazy.py").write_text(
        "def run():\n    from fake_pkg.ui import widgets\n    return widgets.VALUE\n"
    )
    # TYPE_CHECKING-only import: type-only, must NOT be flagged.
    (pkg / "core" / "typing_only.py").write_text(
        "from typing import TYPE_CHECKING\n\n"
        "if TYPE_CHECKING:\n"
        "    from fake_pkg.ui import widgets\n"
    )
    # Entry module touching a private name: must be flagged by the
    # public-interface rule.
    (pkg / "cli.py").write_text("from fake_pkg.ui.widgets import _secret\n")
    return pkg


@pytest.fixture()
def fixture_pkg(tmp_path: Path) -> Path:
    return _write_tree(tmp_path)


def _fixture_rules() -> list[Rule]:
    return [
        Rule("fake_pkg.core.*", "fake_pkg.ui.*", "core must not import ui"),
    ]


# ---------------------------------------------------------------------------
# check() behavior on the fixture tree
# ---------------------------------------------------------------------------
def test_check_returns_structured_violations(fixture_pkg: Path):
    violations = check(
        fixture_pkg,
        rules=_fixture_rules(),
        exceptions=[],
        entry_modules=(),
        package_prefix="fake_pkg",
    )
    assert violations, "expected violations in the fixture tree"
    for v in violations:
        assert isinstance(v, Violation)
        assert v.source_module and v.imported_module and v.lineno > 0
        assert v.scope in ("module", "deferred")
        assert isinstance(v.rule, Rule) and v.rule.reason


def test_violating_file_pair_is_caught(fixture_pkg: Path):
    violations = check(
        fixture_pkg,
        rules=_fixture_rules(),
        exceptions=[],
        entry_modules=(),
        package_prefix="fake_pkg",
    )
    by_source = {v.source_module: v for v in violations}
    hit = by_source.get("fake_pkg.core.engine")
    assert hit is not None, "core->ui module-level import was not caught"
    assert hit.imported_module == "fake_pkg.ui"
    assert hit.scope == "module"
    assert "core must not import ui" in hit.rule.reason


def test_deferred_import_is_flagged_with_scope(fixture_pkg: Path):
    violations = check(
        fixture_pkg,
        rules=_fixture_rules(),
        exceptions=[],
        entry_modules=(),
        package_prefix="fake_pkg",
    )
    hit = next(
        (v for v in violations if v.source_module == "fake_pkg.core.lazy"), None
    )
    assert hit is not None, "deferred core->ui import was not caught"
    assert hit.scope == "deferred"


def test_module_scoped_rule_ignores_deferred_import(fixture_pkg: Path):
    rules = [
        Rule(
            "fake_pkg.core.*",
            "fake_pkg.ui.*",
            "module-level only",
            scope="module",
        )
    ]
    violations = check(
        fixture_pkg,
        rules=rules,
        exceptions=[],
        entry_modules=(),
        package_prefix="fake_pkg",
    )
    sources = {v.source_module for v in violations}
    assert "fake_pkg.core.engine" in sources
    assert "fake_pkg.core.lazy" not in sources


def test_type_checking_imports_are_ignored(fixture_pkg: Path):
    violations = check(
        fixture_pkg,
        rules=_fixture_rules(),
        exceptions=[],
        entry_modules=(),
        package_prefix="fake_pkg",
    )
    sources = {v.source_module for v in violations}
    assert "fake_pkg.core.typing_only" not in sources


def test_entry_module_private_name_import_is_flagged(fixture_pkg: Path):
    violations = check(
        fixture_pkg,
        rules=[],
        exceptions=[],
        entry_modules=("fake_pkg.cli",),
        package_prefix="fake_pkg",
    )
    assert len(violations) == 1
    v = violations[0]
    assert v.source_module == "fake_pkg.cli"
    assert v.imported_module == "fake_pkg.ui.widgets._secret"
    assert "public interfaces" in v.rule.reason


def test_acknowledged_exception_subtracts_violation(fixture_pkg: Path):
    exceptions = [("fake_pkg.core.engine", "fake_pkg.ui.*", "reviewed")]
    violations = check(
        fixture_pkg,
        rules=_fixture_rules(),
        exceptions=exceptions,
        entry_modules=(),
        package_prefix="fake_pkg",
    )
    sources = {v.source_module for v in violations}
    assert "fake_pkg.core.engine" not in sources
    # Other sources still flagged.
    assert "fake_pkg.core.lazy" in sources


# ---------------------------------------------------------------------------
# Rule data integrity
# ---------------------------------------------------------------------------
def test_rules_are_well_formed():
    assert RULES, "RULES must not be empty"
    for rule in RULES:
        assert rule.source_pattern and rule.forbidden_pattern and rule.reason
        assert rule.scope in ("any", "module"), f"bad scope: {rule.scope}"
        assert "mythic_agent" in rule.source_pattern


def test_entry_modules_are_known():
    assert set(ENTRY_MODULES) >= {
        "mythic_agent.cli",
        "mythic_agent.terminal",
        "mythic_agent.mcp_server",
    }


def test_acknowledged_exceptions_still_match_live_imports():
    """Exceptions must document LIVE coupling; stale ones fail so the list
    cannot rot into a blanket waiver."""
    imports = collect_imports(PACKAGE_DIR)
    for source_pat, forbidden_pat, reason in ACKNOWLEDGED_EXCEPTIONS:
        assert reason.strip(), "every exception needs a documented reason"
        import fnmatch

        live = any(
            fnmatch.fnmatchcase(src, source_pat)
            and any(
                fnmatch.fnmatchcase(rec.module, forbidden_pat)
                for rec in recs
                if rec.module.startswith("mythic_agent")
            )
            for src, recs in imports.items()
        )
        assert live, f"stale exception (no live import matches): {source_pat} -> {forbidden_pat}"


# ---------------------------------------------------------------------------
# The gate: the live tree must be clean
# ---------------------------------------------------------------------------
def test_gate_live_tree_has_zero_violations():
    violations = check(PACKAGE_DIR)
    assert violations == [], (
        "architecture conformance gate failed:\n"
        + "\n".join(str(v) for v in violations)
    )
