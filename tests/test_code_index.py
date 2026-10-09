"""Tests for mythic_agent.tools.code_index (Slice 19)."""

from pathlib import Path

import pytest

from mythic_agent.tools.code_index import SymbolIndex, refresh_mtime


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    (tmp_path / "app.py").write_text(
        '"""Demo module."""\n'
        "import os\n"
        "from pathlib import Path as P\n"
        "\n"
        "class Engine:\n"
        '    """The engine."""\n'
        "    def start(self):\n"
        '        """Start it."""\n'
        "        return True\n"
        "\n"
        "def run(engine):\n"
        "    engine.start()\n"
    )
    (tmp_path / "lib").mkdir()
    (tmp_path / "lib" / "util.py").write_text(
        "def run():\n"
        "    pass\n"
    )
    (tmp_path / "broken.py").write_text("def broken(:\n")
    return tmp_path


def test_index_file_extracts_symbols(project: Path):
    idx = SymbolIndex(project)
    symbols = idx.index_file(project / "app.py")
    by_name = {s.name: s for s in symbols}
    assert by_name["Engine"].kind == "class"
    assert by_name["run"].kind == "function"
    assert by_name["start"].kind == "method"
    assert by_name["os"].kind == "import"
    assert by_name["P"].kind == "import"
    assert by_name["Engine"].qualified == "Engine"
    assert by_name["start"].qualified == "Engine.start"


def test_index_file_handles_syntax_errors(project: Path):
    idx = SymbolIndex(project)
    assert idx.index_file(project / "broken.py") == []
    assert idx.index_file(project / "nope.py") == []


def test_find_definition_prefers_definitions_over_imports(project: Path):
    idx = SymbolIndex(project)
    loc = idx.find_definition("Engine")
    assert loc is not None
    assert loc.startswith(str(project / "app.py") + ":")
    assert idx.find_definition("missing_symbol") is None


def test_find_definition_prefers_definition_to_duplicate(project: Path):
    # "run" is defined in both app.py and lib/util.py; either definition is fine,
    # but it must be a real definition, not an import.
    idx = SymbolIndex(project)
    loc = idx.find_definition("run")
    assert loc is not None
    assert loc.endswith(":11") or loc.endswith(":1")


def test_find_references(project: Path):
    idx = SymbolIndex(project)
    refs = idx.find_references("start")
    line_nos = {int(r.rsplit(":", 1)[1]) for r in refs}
    assert line_nos == {7, 12}  # def start / engine.start()
    # Word-boundary: "starter" must not match "start".
    (project / "app.py").write_text(
        (project / "app.py").read_text() + "\nstarter = 1\n"
    )
    refs = idx.find_references("start")
    line_nos = {int(r.rsplit(":", 1)[1]) for r in refs}
    assert line_nos == {7, 12}


def test_cache_invalidates_on_mtime_change(project: Path):
    idx = SymbolIndex(project)
    before = idx.index_file("app.py")
    assert len(before) > 0
    (project / "app.py").write_text("def brand_new_thing():\n    pass\n")
    refresh_mtime(project / "app.py")
    after = idx.index_file("app.py")
    assert [s.name for s in after] == ["brand_new_thing"]
    assert idx.find_definition("Engine") is None


def test_index_workspace_counts_symbols(project: Path):
    idx = SymbolIndex(project)
    total = idx.index_workspace()
    assert total >= 6  # Engine, start, run, os, P imports, lib.util run


def test_invalidate_clears_cache(project: Path):
    idx = SymbolIndex(project)
    idx.index_file("app.py")
    assert len(idx._files) == 1
    idx.invalidate("app.py")
    assert len(idx._files) == 0
    idx.index_file("app.py")
    idx.invalidate()
    assert len(idx._files) == 0
