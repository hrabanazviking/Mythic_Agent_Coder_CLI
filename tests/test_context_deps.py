"""
TIER: unit
Tests for dependency-aware file selection via stdlib ast import graphs
(Slice 059).
"""

import pytest

from mythic_agent.context import (
    ContextCompiler,
    build_import_graph,
    extract_imports,
    module_key,
    related_modules,
    select_related,
)
from mythic_agent.context.deps import DependencyFilesSource
from pathlib import Path


def _ws(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("")
    (tmp_path / "pkg" / "core.py").write_text("VALUE = 1\n")
    (tmp_path / "pkg" / "api.py").write_text("from pkg.core import VALUE\nimport os\n")
    (tmp_path / "main.py").write_text("from pkg.api import VALUE\n")
    (tmp_path / "client.py").write_text("import pkg\n")
    (tmp_path / "broken.py").write_text("import (\n")
    return tmp_path


# ---------------------------------------------------------------------------
# import extraction / module keys
# ---------------------------------------------------------------------------

def test_extract_imports():
    names = extract_imports("import os\nimport a.b\nfrom x import y\nfrom . import z\n")
    assert names == ["os", "a.b", "x"]


def test_extract_imports_raises_on_syntax_error():
    with pytest.raises(SyntaxError):
        extract_imports("import (\n")


def test_module_key():
    root = Path("/ws")
    assert module_key(Path("/ws/pkg/mod.py"), root) == "pkg.mod"
    assert module_key(Path("/ws/pkg/__init__.py"), root) == "pkg"
    assert module_key(Path("/ws/top.py"), root) == "top"


# ---------------------------------------------------------------------------
# graph
# ---------------------------------------------------------------------------

def test_build_import_graph_local_edges_only(tmp_path):
    ws = _ws(tmp_path)
    graph = build_import_graph(ws)
    assert graph.edges["pkg.api"] == {"pkg.core"}
    assert graph.edges["main"] == {"pkg.api"}
    assert graph.edges["client"] == {"pkg"}
    # stdlib import 'os' does not resolve locally
    assert "os" not in graph.edges["pkg.api"]
    assert any("broken.py" in w for w in graph.warnings)


def test_related_modules_importees_and_importers(tmp_path):
    ws = _ws(tmp_path)
    graph = build_import_graph(ws)
    related = related_modules(graph, "pkg.api", depth=1)
    assert "pkg.core" in related      # importee
    assert "main" in related          # importer
    assert "os" not in related        # stdlib never enters the graph
    related_pkg = related_modules(graph, "pkg", depth=1)
    assert "client" in related_pkg     # importer of the package


def test_related_modules_depth_and_validation(tmp_path):
    ws = _ws(tmp_path)
    graph = build_import_graph(ws)
    deep = related_modules(graph, "main", depth=2)
    assert deep == {"pkg.api", "pkg.core"}  # main -> pkg.api -> pkg.core
    with pytest.raises(ValueError):
        related_modules(graph, "main", depth=0)


# ---------------------------------------------------------------------------
# selection
# ---------------------------------------------------------------------------

def test_select_related_includes_seed_first(tmp_path):
    ws = _ws(tmp_path)
    selected, _warnings = select_related(ws / "pkg" / "api.py", ws,
                                         budget_tokens=10_000)
    assert selected[0] == ("pkg/api.py", "seed")
    relations = dict(selected)
    assert relations["pkg/core.py"] == "imports"


def test_select_related_finds_importers(tmp_path):
    ws = _ws(tmp_path)
    selected, _ = select_related(ws / "pkg" / "__init__.py", ws,
                                 budget_tokens=10_000)
    relations = dict(selected)
    assert relations.get("client.py") == "imported-by"


def test_select_related_seed_api_finds_main(tmp_path):
    ws = _ws(tmp_path)
    selected, _ = select_related(ws / "pkg" / "api.py", ws,
                                 budget_tokens=10_000)
    relations = dict(selected)
    assert relations.get("main.py") == "imported-by"


def test_select_related_budget_trims(tmp_path):
    ws = _ws(tmp_path)
    selected, _ = select_related(ws / "pkg" / "api.py", ws, budget_tokens=1)
    assert selected == []


def test_select_related_seed_outside_workspace_rejected(tmp_path):
    ws = _ws(tmp_path)
    with pytest.raises(Exception):
        select_related(tmp_path.parent / "elsewhere.py", ws)


def test_dependency_source_needs_seed(tmp_path):
    ws = _ws(tmp_path)
    compiler = ContextCompiler(ws)
    compiler.add_source(DependencyFilesSource())
    assert compiler.compile("query").blocks == []


def test_dependency_source_with_seed_via_config(tmp_path):
    ws = _ws(tmp_path)
    compiler = ContextCompiler(ws, config={"context_seed_file": str(ws / "pkg" / "api.py")})
    compiler.add_source(DependencyFilesSource(budget_tokens=10_000))
    compiled = compiler.compile()
    names = [b.name for b in compiled.blocks]
    assert "deps:pkg/api.py" in names
    assert "deps:pkg/core.py" in names
