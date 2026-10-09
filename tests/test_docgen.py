"""Tests for mythic_agent.tools.docgen (Slice 43)."""

import ast
from pathlib import Path

import pytest

from mythic_agent.tools.docgen import (
    describe_signature,
    generate_docstring,
    generate_readme,
)


def sample_func(a: int, b: str = "x", *args: float, flag: bool = True, **kw: int) -> str:
    if not a:
        raise ValueError("bad a")
    return b


def undocumented(x, y=2):
    return x + y


class TestGenerateDocstring:
    def test_from_function_object(self):
        doc = generate_docstring(sample_func)
        assert "Parameters" in doc
        assert "a : int" in doc
        assert 'b : str' in doc
        assert "flag : bool" in doc
        assert "Returns" in doc
        assert "Raises" in doc
        assert "ValueError" in doc

    def test_from_source_string(self):
        doc = generate_docstring("def add(a: int, b: int) -> int:\n    return a + b\n")
        assert "Add." in doc
        assert "a : int" in doc and "b : int" in doc

    def test_from_ast_node(self):
        node = ast.parse("def greet(name):\n    return 'hi'\n").body[0]
        doc = generate_docstring(node)
        assert "Greet." in doc
        assert "name : Any" in doc

    def test_existing_docstring_preserved(self):
        def documented():
            """Keep me."""
            pass
        assert generate_docstring(documented) == "Keep me."

    def test_no_params_no_returns(self):
        doc = generate_docstring("def noop():\n    pass\n")
        assert "Parameters" not in doc
        assert "Returns" not in doc

    def test_invalid_source_raises(self):
        with pytest.raises(ValueError):
            generate_docstring("x = 1\n")
        with pytest.raises(TypeError):
            generate_docstring(42)


class TestDescribeSignature:
    def test_signature_rendering(self):
        node = ast.parse("def f(a: int, b='x', *args, k: bool = True, **kw) -> str:\n    pass\n").body[0]
        sig = describe_signature(node)
        assert sig.startswith("def f(")
        assert "a: int" in sig
        assert "b: Any = 'x'" in sig
        assert "*args: Any" in sig
        assert "k: bool = True" in sig
        assert "**kw: Any" in sig
        assert sig.endswith("-> str")

    def test_async_and_self(self):
        node = ast.parse("async def m(self, x):\n    pass\n").body[0]
        sig = describe_signature(node)
        assert sig.startswith("async def m(self, x: Any)")


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo-proj"\ndescription = "A demo project."\n'
    )
    (tmp_path / "main.py").write_text('"""Entry point."""\n')
    pkg = tmp_path / "core"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "engine.py").write_text("def run():\n    pass\n")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_x.py").write_text("def test_x():\n    pass\n")
    return tmp_path


class TestGenerateReadme:
    def test_scaffold_contents(self, project: Path):
        readme = generate_readme(project)
        assert readme.startswith("# demo-proj")
        assert "A demo project." in readme
        assert "## Project structure" in readme
        assert "## Modules" in readme
        assert "`main` — Entry point." in readme
        assert "`core/` (package)" in readme
        assert "## Installation" in readme
        assert "pip install -e ." in readme
        assert "## Testing" in readme

    def test_missing_directory_raises(self, tmp_path: Path):
        with pytest.raises(ValueError):
            generate_readme(tmp_path / "nope")

    def test_no_packaging_metadata(self, tmp_path: Path):
        (tmp_path / "solo.py").write_text("x = 1\n")
        readme = generate_readme(tmp_path)
        assert "No packaging metadata found" in readme
