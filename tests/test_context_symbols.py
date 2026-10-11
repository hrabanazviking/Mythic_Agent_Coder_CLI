"""
TIER: unit
Tests for symbol-aware file selection via stdlib ast (Slice 058).
"""

import pytest

from mythic_agent.context import (
    ContextCompiler,
    SymbolFilesSource,
    extract_symbols,
    index_workspace,
    rank_by_symbol_mentions,
    select_by_symbols,
)


def _ws(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "engine.py").write_text(
        "class Engine:\n"
        "    def start(self):\n"
        "        pass\n"
        "    async def stop(self):\n"
        "        pass\n"
        "def helper():\n"
        "    def nested():\n"
        "        pass\n")
    (tmp_path / "util.py").write_text("CONSTANT = 1\n")
    (tmp_path / "broken.py").write_text("def oops(:\n")
    return tmp_path


# ---------------------------------------------------------------------------
# extraction
# ---------------------------------------------------------------------------

def test_extract_symbols_finds_defs_and_classes():
    symbols = extract_symbols("class A:\n    def m(self):\n        pass\nasync def f():\n    pass\n")
    by_name = {s.name: s for s in symbols}
    assert by_name["A"].kind == "class"
    assert by_name["m"].kind == "function"
    assert by_name["m"].qualified == "A.m"
    assert by_name["f"].kind == "async function"


def test_extract_symbols_nested_qualified_names():
    symbols = extract_symbols("def outer():\n    def inner():\n        pass\n")
    qualified = {s.qualified for s in symbols}
    assert {"outer", "outer.inner"} == qualified


def test_extract_symbols_raises_on_syntax_error():
    with pytest.raises(SyntaxError):
        extract_symbols("def oops(:\n")


def test_extract_symbols_empty_source():
    assert extract_symbols("") == []


# ---------------------------------------------------------------------------
# indexing
# ---------------------------------------------------------------------------

def test_index_workspace_extracts_and_warns_on_unparseable(tmp_path):
    ws = _ws(tmp_path)
    index = index_workspace(ws)
    assert "engine.py" in index.files
    names = {s.name for s in index.files["engine.py"]}
    assert {"Engine", "start", "stop", "helper", "nested"} <= names
    assert "broken.py" not in index.files
    assert any("broken.py" in w for w in index.warnings)


def test_index_workspace_cross_workspace_isolation(tmp_path):
    ws_a = _ws(tmp_path / "a")
    _ws(tmp_path / "b")
    index = index_workspace(ws_a)
    assert all("b" not in doc_id for doc_id in index.files)


def test_index_missing_workspace_raises():
    with pytest.raises(ValueError):
        index_workspace("/nonexistent-workspace-xyz")


# ---------------------------------------------------------------------------
# ranking / selection
# ---------------------------------------------------------------------------

def test_rank_by_symbol_mentions(tmp_path):
    ws = _ws(tmp_path)
    index = index_workspace(ws)
    ranked = rank_by_symbol_mentions("How does Engine.start work?", index)
    assert ranked[0][0] == "engine.py"
    assert ranked[0][1] >= 2  # Engine + start


def test_rank_is_case_insensitive_and_deterministic(tmp_path):
    ws = _ws(tmp_path)
    index = index_workspace(ws)
    first = rank_by_symbol_mentions("ENGINE STOP helper", index)
    second = rank_by_symbol_mentions("engine stop HELPER", index)
    assert first == second
    assert first[0][0] == "engine.py"


def test_rank_empty_query_yields_nothing(tmp_path):
    ws = _ws(tmp_path)
    index = index_workspace(ws)
    assert rank_by_symbol_mentions("", index) == []


def test_select_by_symbols_top_n_and_budget(tmp_path):
    ws = _ws(tmp_path)
    selected, warnings = select_by_symbols("Engine start stop", ws,
                                           top_n=5, budget_tokens=10_000)
    assert selected[0][0] == "engine.py"
    assert any("broken.py" in w for w in warnings)
    tiny, _ = select_by_symbols("Engine start", ws, top_n=5, budget_tokens=1)
    assert tiny == []


def test_select_by_symbols_rejects_bad_args(tmp_path):
    ws = _ws(tmp_path)
    with pytest.raises(ValueError):
        select_by_symbols("q", ws, top_n=0)
    with pytest.raises(ValueError):
        select_by_symbols("q", ws, budget_tokens=-1)


def test_symbol_source_via_compiler(tmp_path):
    ws = _ws(tmp_path)
    compiler = ContextCompiler(ws)
    compiler.add_source(SymbolFilesSource(top_n=2, budget_tokens=10_000))
    compiled = compiler.compile("where is Engine.start defined")
    assert compiled.blocks
    assert compiled.blocks[0].name == "symbols:engine.py"
    assert "symbols:" in compiled.blocks[0].content


def test_symbol_source_empty_query_yields_nothing(tmp_path):
    ws = _ws(tmp_path)
    compiler = ContextCompiler(ws)
    compiler.add_source(SymbolFilesSource())
    assert compiler.compile("").blocks == []
