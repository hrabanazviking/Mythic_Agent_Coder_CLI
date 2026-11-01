"""M-046 — Symbol graph.

TIER: integration

Part III (Code Intelligence): definitions, references,
imports, call edges extracted per language; the graph feeds
the map, the search, and Part VI's task splitting.

These tests do not take the graph's word for any of it:

* definitions are the M-043 parses' own (per language, with
  the backend named), references are identifier occurrences
  resolved by name to every definition carrying that name —
  ambiguity recorded with all sites, never silently picked,
* call edges run from the enclosing definition (or
  ``<module>``) to the callee, resolved the same way, with
  unresolved callees kept and queryable,
* imports carry the module as written; Python dotted and
  JS/TS relative imports resolve to real workspace files,
  Go package paths and Rust use paths honestly do not,
* Python's ast fallback backend extracts the same four edge
  kinds with the backend labelled, and every other language
  without its grammar refuses,
* honesty: definition names and parameter names are
  bindings, not references; a Go package clause is not a
  reference; Mojo is skipped with its grammar-less reason;
  oversized and binary files are skipped with theirs; the
  derived file edges agree with the repo map on the shared
  fixture's proven edge.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import mythic_agent.core.tree_sitter_foundation as foundation
from mythic_agent.context.repo_map import build_repo_map
from mythic_agent.context.symbol_graph import (
    EDGE_KINDS,
    MODULE_CALLER,
    SYMBOL_GRAPH_SLICE,
    build_symbol_graph,
    extract_file_graph,
    language_capabilities,
)
from mythic_agent.core.tree_sitter_foundation import (
    ParseUnavailableError,
    availability_for,
    load_catalog,
)

PY_SOURCE = (
    "import os\n"
    "from pkg.mod import thing\n"
    "\n"
    "def bar(y):\n"
    "    return y\n"
    "\n"
    "class Thing:\n"
    "    def m(self):\n"
    "        return self.m2()\n"
    "\n"
    "def foo(x):\n"
    "    return bar(x) + Thing()\n"
    "\n"
    "foo(1)\n"
)


def _grammar_available(language):
    return availability_for(language, load_catalog()).available


# ---------------------------------------------------------------------------
# identity + capabilities
# ---------------------------------------------------------------------------

def test_slice_identity_and_edge_kinds():
    assert SYMBOL_GRAPH_SLICE == "M-046"
    assert EDGE_KINDS == ("definitions", "references", "imports", "calls")
    assert MODULE_CALLER == "<module>"


def test_capabilities_cover_the_catalogue_honestly():
    caps = {c.language: c for c in language_capabilities()}
    assert tuple(caps) == load_catalog().names()
    for language in ("python", "javascript", "typescript", "rust", "go"):
        assert caps[language].kinds == EDGE_KINDS, language
    assert caps["mojo"].kinds == ()
    assert "no grammar" in caps["mojo"].note


# ---------------------------------------------------------------------------
# per-file extraction: Python (tree-sitter backend)
# ---------------------------------------------------------------------------

def test_python_definitions_come_from_the_parse():
    graph = extract_file_graph("a.py", "python", PY_SOURCE)
    assert graph.language == "python"
    assert graph.backend in ("tree_sitter", "python_ast")
    by_name = {d.name: d for d in graph.definitions}
    assert by_name["Thing"].kind == "class"
    assert by_name["Thing"].line == 7
    assert by_name["bar"].kind == "function"
    assert by_name["m"].line == 8
    for definition in graph.definitions:
        assert definition.path == "a.py"
        assert definition.backend == graph.backend
        assert definition.id == (
            f"a.py:{definition.line}:{definition.name}")


def test_python_references_resolve_by_name_with_enclosing():
    graph = extract_file_graph("a.py", "python", PY_SOURCE)
    refs = {(r.name, r.enclosing) for r in graph.references}
    assert ("bar", "foo") in refs
    assert ("Thing", "foo") in refs
    bar_ref = next(r for r in graph.references if r.name == "bar")
    assert bar_ref.resolved_to == ("a.py:4:bar",)
    # a definition's own name site is a binding, not a reference,
    # and an undefined name (m2, thing) is no reference at all
    assert all(r.line != 4 or r.name != "bar" for r in graph.references)
    assert "m2" not in {r.name for r in graph.references}


def test_python_imports_carry_the_module_as_written():
    graph = extract_file_graph("a.py", "python", PY_SOURCE)
    assert [(i.module, i.line) for i in graph.imports] == [
        ("os", 1), ("pkg.mod", 2)]
    # standalone extraction has no workspace to resolve against
    assert all(i.resolved_path is None for i in graph.imports)


def test_python_calls_run_from_the_enclosing_definition():
    graph = extract_file_graph("a.py", "python", PY_SOURCE)
    by_callee = {c.callee: c for c in graph.calls}
    assert by_callee["bar"].caller == "foo"
    assert by_callee["bar"].resolved_to == ("a.py:4:bar",)
    assert by_callee["Thing"].caller == "foo"
    assert by_callee["m2"].caller == "m"
    assert by_callee["m2"].resolved_to == ()  # unresolved, recorded
    assert by_callee["foo"].caller == MODULE_CALLER  # the top-level call


def test_parameter_names_are_bindings_not_references():
    source = (
        "def bar():\n    return 1\n\n"
        "def foo(bar):\n    return None\n")
    graph = extract_file_graph("a.py", "python", source)
    assert graph.references == ()


def test_unknown_language_and_mojo_refuse():
    with pytest.raises(KeyError):
        extract_file_graph("a.cobol", "cobol", "x")
    with pytest.raises(ParseUnavailableError):
        extract_file_graph("s.mojo", "mojo", "fn main():\n    pass\n")


# ---------------------------------------------------------------------------
# per-file extraction: the other grammar languages
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _grammar_available("javascript"),
                    reason="javascript grammar not installed")
def test_javascript_edges():
    source = (
        "import {thing} from './mod.js';\n"
        "class A { b() { return c(); } }\n"
        "function c() { return 1; }\n"
        "function main() { return new A(); }\n")
    graph = extract_file_graph("web.js", "javascript", source)
    assert {d.name for d in graph.definitions} >= {"A", "b", "c", "main"}
    assert [i.module for i in graph.imports] == ["./mod.js"]
    by_callee = {c.callee: c for c in graph.calls}
    assert by_callee["c"].caller == "b"
    assert by_callee["c"].resolved_to == ("web.js:3:c",)
    assert by_callee["A"].caller == "main"  # a new_expression call
    refs = {(r.name, r.enclosing) for r in graph.references}
    assert ("c", "b") in refs and ("A", "main") in refs


@pytest.mark.skipif(not _grammar_available("typescript"),
                    reason="typescript grammar not installed")
def test_typescript_edges():
    source = (
        "import {foo} from './mod';\n"
        "interface Shape { area(): number; }\n"
        "function make(): Shape { return null; }\n"
        "function main(): number { return foo(1); }\n")
    graph = extract_file_graph("app.ts", "typescript", source)
    assert {d.name for d in graph.definitions} >= {"Shape", "make", "main"}
    assert [i.module for i in graph.imports] == ["./mod"]
    refs = {(r.name, r.enclosing) for r in graph.references}
    assert ("Shape", "make") in refs  # the return-type annotation
    by_callee = {c.callee: c for c in graph.calls}
    assert by_callee["foo"].caller == "main"
    assert by_callee["foo"].resolved_to == ()


@pytest.mark.skipif(not _grammar_available("rust"),
                    reason="rust grammar not installed")
def test_rust_edges():
    source = (
        "use std::collections::HashMap;\n"
        "fn foo() {}\n"
        "struct P {}\n"
        "fn main() { let x = foo(); obj.method(); }\n")
    graph = extract_file_graph("main.rs", "rust", source)
    assert {d.name for d in graph.definitions} >= {"foo", "P", "main"}
    assert [i.module for i in graph.imports] == [
        "std::collections::HashMap"]
    by_callee = {c.callee: c for c in graph.calls}
    assert by_callee["foo"].caller == "main"
    assert by_callee["foo"].resolved_to == ("main.rs:2:foo",)
    assert by_callee["method"].resolved_to == ()
    refs = {(r.name, r.enclosing) for r in graph.references}
    assert ("foo", "main") in refs


@pytest.mark.skipif(not _grammar_available("go"),
                    reason="go grammar not installed")
def test_go_edges():
    source = (
        "package main\n"
        "import (\"fmt\"; m \"example.com/mod\")\n"
        "func foo() {}\n"
        "func main() { fmt.Println(foo()) }\n")
    graph = extract_file_graph("main.go", "go", source)
    assert {d.name for d in graph.definitions} >= {"foo", "main"}
    assert {i.module for i in graph.imports} == {
        "fmt", "example.com/mod"}
    by_callee = {c.callee: c for c in graph.calls}
    assert by_callee["foo"].caller == "main"
    assert by_callee["foo"].resolved_to == ("main.go:3:foo",)
    assert by_callee["Println"].resolved_to == ()
    # the package clause is not a reference to the main function
    assert all(r.enclosing != MODULE_CALLER or r.name != "main"
               for r in graph.references)
    refs = {(r.name, r.enclosing) for r in graph.references}
    assert ("foo", "main") in refs


# ---------------------------------------------------------------------------
# Python's ast fallback backend: the same four kinds, labelled
# ---------------------------------------------------------------------------

def test_python_ast_fallback_extracts_the_same_edges(monkeypatch):
    monkeypatch.setattr(foundation, "_tree_sitter", None)
    graph = extract_file_graph("a.py", "python", PY_SOURCE)
    assert graph.backend == "python_ast"
    assert {d.name for d in graph.definitions} == {
        "bar", "Thing", "m", "foo"}
    assert {(r.name, r.enclosing) for r in graph.references} >= {
        ("bar", "foo"), ("Thing", "foo")}
    assert [i.module for i in graph.imports] == ["os", "pkg.mod"]
    by_callee = {c.callee: c for c in graph.calls}
    assert by_callee["bar"].caller == "foo"
    assert by_callee["m2"].resolved_to == ()
    assert by_callee["foo"].caller == MODULE_CALLER
    with pytest.raises(SyntaxError):
        extract_file_graph("b.py", "python", "def broken(:\n")
    with pytest.raises(ParseUnavailableError):
        extract_file_graph("w.js", "javascript", "function f() {}\n")


# ---------------------------------------------------------------------------
# the workspace build: resolution, queries, file edges
# ---------------------------------------------------------------------------

def _ws(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("")
    (tmp_path / "pkg" / "mod.py").write_text(
        "def thing():\n    return 1\n")
    (tmp_path / "pkg" / "sibling.py").write_text(
        "def sib():\n    return 2\n")
    (tmp_path / "app.py").write_text(
        "from pkg.mod import thing\n"
        "from pkg.sibling import sib\n"
        "\n"
        "def main():\n"
        "    return thing()\n")
    return tmp_path


def test_workspace_python_imports_resolve_to_files(tmp_path):
    graph = build_symbol_graph(_ws(tmp_path))
    imports = {(i.module, i.resolved_path) for i in graph.imports_of("app.py")}
    assert ("pkg.mod", "pkg/mod.py") in imports
    assert graph.files_seen == 4
    assert graph.skipped == ()


def test_workspace_queries(tmp_path):
    graph = build_symbol_graph(_ws(tmp_path))
    assert [d.path for d in graph.definitions_named("THING")] == [
        "pkg/mod.py"]
    assert [d.name for d in graph.definitions_in("pkg/mod.py")] == ["thing"]
    refs = graph.references_to("thing")
    assert len(refs) == 1 and refs[0].path == "app.py"
    assert refs[0].resolved_to == ("pkg/mod.py:1:thing",)
    callers = graph.callers_of("thing")
    assert len(callers) == 1 and callers[0].caller == "main"
    callees = graph.callees_of("main")
    assert [c.callee for c in callees] == ["thing"]
    assert graph.unresolved_calls() == ()


def test_relative_import_resolves_within_the_package(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("")
    (tmp_path / "pkg" / "sibling.py").write_text("def sib():\n    pass\n")
    (tmp_path / "pkg" / "a.py").write_text(
        "from .sibling import sib\n\ndef use():\n    return sib()\n")
    graph = build_symbol_graph(tmp_path)
    imports = graph.imports_of("pkg/a.py")
    assert imports[0].module == ".sibling"
    assert imports[0].resolved_path == "pkg/sibling.py"
    assert graph.file_edges()["pkg/a.py"] == ("pkg/sibling.py",)


def test_javascript_relative_import_resolves(tmp_path):
    if not _grammar_available("javascript"):
        pytest.skip("javascript grammar not installed")
    (tmp_path / "mod.js").write_text(
        "export function thing() { return 1; }\n")
    (tmp_path / "web.js").write_text(
        "import {thing} from './mod.js';\n"
        "function main() { return thing(); }\n")
    graph = build_symbol_graph(tmp_path)
    imports = graph.imports_of("web.js")
    assert imports[0].resolved_path == "mod.js"
    assert graph.file_edges()["web.js"] == ("mod.js",)


def test_go_and_rust_imports_are_honestly_unresolved(tmp_path):
    if not (_grammar_available("go") and _grammar_available("rust")):
        pytest.skip("go/rust grammar not installed")
    (tmp_path / "main.go").write_text(
        "package main\nimport \"fmt\"\nfunc main() { fmt.Println(1) }\n")
    (tmp_path / "main.rs").write_text(
        "use std::vec::Vec;\nfn main() {}\n")
    graph = build_symbol_graph(tmp_path)
    assert {i.module for i in graph.imports} == {"fmt", "std::vec::Vec"}
    assert all(i.resolved_path is None for i in graph.imports)


def test_ambiguous_names_resolve_to_every_site(tmp_path):
    (tmp_path / "dup1.py").write_text("def helper():\n    return 1\n")
    (tmp_path / "dup2.py").write_text(
        "def helper():\n    return 2\n\ndef use():\n    return helper()\n")
    graph = build_symbol_graph(tmp_path)
    refs = graph.references_to("helper")
    assert len(refs) == 1
    assert refs[0].resolved_to == (
        "dup1.py:1:helper", "dup2.py:1:helper")
    callers = graph.callers_of("helper")
    assert callers[0].resolved_to == refs[0].resolved_to


def test_file_edges_agree_with_the_repo_map_on_a_shared_edge(tmp_path):
    (tmp_path / "core.py").write_text(
        "class Engine:\n"
        "    def start(self):\n"
        "        return 'on'\n"
        "\n"
        "def build_engine():\n"
        "    return Engine()\n")
    (tmp_path / "app.py").write_text(
        "def main():\n"
        "    engine = build_engine()\n"
        "    return engine.start()\n")
    graph = build_symbol_graph(tmp_path)
    assert graph.file_edges()["app.py"] == ("core.py",)
    repo_map = build_repo_map(tmp_path, budget_tokens=10_000)
    app_entry = next(e for e in repo_map.entries if e.path == "app.py")
    assert "core.py" in app_entry.references_out


def test_build_is_deterministic(tmp_path):
    ws = _ws(tmp_path)
    one = build_symbol_graph(ws)
    two = build_symbol_graph(ws)
    assert one.record() == two.record()


def test_record_is_plain_data_with_the_whole_story(tmp_path):
    graph = build_symbol_graph(_ws(tmp_path))
    record = graph.record()
    assert record["files_seen"] == 4
    assert record["file_edges"]["app.py"] == [
        "pkg/mod.py", "pkg/sibling.py"]
    thing = next(d for d in record["definitions"] if d["name"] == "thing")
    assert thing["id"] == "pkg/mod.py:1:thing"
    caps = {c["language"]: c for c in record["capabilities"]}
    assert caps["mojo"]["kinds"] == []
    assert caps["python"]["kinds"] == list(EDGE_KINDS)


# ---------------------------------------------------------------------------
# honesty: skipped files and their reasons
# ---------------------------------------------------------------------------

def test_mojo_is_skipped_with_its_grammarless_reason(tmp_path):
    (tmp_path / "spell.mojo").write_text("fn main():\n    pass\n")
    (tmp_path / "real.py").write_text("def real():\n    pass\n")
    graph = build_symbol_graph(tmp_path)
    assert [d.path for d in graph.definitions] == ["real.py"]
    assert len(graph.skipped) == 1
    assert graph.skipped[0].path == "spell.mojo"
    assert "no tree-sitter grammar package is published" in \
        graph.skipped[0].reason


def test_oversized_and_binary_files_are_skipped_with_reasons(tmp_path):
    (tmp_path / "big.py").write_text("def big():\n    pass\n" * 10)
    (tmp_path / "blob.py").write_bytes(b"def x():\n    pass\n\x00")
    graph = build_symbol_graph(tmp_path, max_file_bytes=64)
    reasons = {s.path: s.reason for s in graph.skipped}
    assert "too large for the graph" in reasons["big.py"]
    assert reasons["blob.py"] == "binary file"


def test_unparseable_python_is_skipped_not_invented(tmp_path, monkeypatch):
    monkeypatch.setattr(foundation, "_tree_sitter", None)
    (tmp_path / "broken.py").write_text("def broken(:\n")
    (tmp_path / "real.py").write_text("def real():\n    pass\n")
    graph = build_symbol_graph(tmp_path)
    assert [s.path for s in graph.skipped] == ["broken.py"]
    assert "unparseable" in graph.skipped[0].reason
    assert [d.name for d in graph.definitions] == ["real"]


def test_file_cap_is_a_warning_never_silence(tmp_path):
    for i in range(4):
        (tmp_path / f"f{i}.py").write_text(f"def f{i}():\n    pass\n")
    graph = build_symbol_graph(tmp_path, max_files=2)
    assert graph.files_seen == 2
    assert any("file cap reached (2)" in w for w in graph.warnings)


def test_empty_workspace_graphs_to_an_empty_graph(tmp_path):
    graph = build_symbol_graph(tmp_path)
    assert graph.definitions == () and graph.references == ()
    assert graph.calls == () and graph.imports == ()
    assert graph.files_seen == 0
    assert graph.file_edges() == {}
    assert len(graph.capabilities) == 6


def test_invalid_bounds_are_refused(tmp_path):
    with pytest.raises(ValueError):
        build_symbol_graph(tmp_path, max_files=0)
    with pytest.raises(ValueError):
        build_symbol_graph(tmp_path, max_file_bytes=0)


def test_non_code_files_are_not_candidates(tmp_path):
    (tmp_path / "notes.txt").write_text("def not_code():\n")
    (tmp_path / "real.py").write_text("def real():\n    pass\n")
    graph = build_symbol_graph(tmp_path)
    assert graph.files_seen == 1
    assert [d.path for d in graph.definitions] == ["real.py"]
