"""M-047 — Structural search.

TIER: integration

Part III (Code Intelligence): ast-grep-style pattern search
— "find every call like `foo($A, $$$)`" — as a tool and a
TUI panel, over the M-043 parse foundation.

These tests do not take the search's word for any of it:

* the roadmap's own example matches, with captures: $NAME
  takes exactly one node, $$$ takes the rest (including
  zero), a named $$$ captures the joined text,
* matching is structural, never textual: the same text in
  a comment or a string does not match, a different callee
  does not match, `$A + $B` never matches a subtraction,
  and a metavariable used twice must capture the same
  text twice,
* a match is found wherever the shape sits — inside a
  return, an assignment, another call — and nested matches
  are each reported,
* the other grammar languages match through their own
  grammars (JavaScript live; Go and Rust through the
  declared context wraps), and Python's ast fallback
  backend extracts the same matches, labelled,
* honesty: an unparseable pattern is refused (never
  text-searched), a stray $ is a pattern error, Mojo is
  refused with the foundation's own reason, an unknown
  language is a KeyError, unparseable files are skipped
  with reasons, and other languages' files are not this
  search's population,
* the gap audit's structural row now names an existing
  module (this one) while its state stays MISSING — the
  rewrite half is M-048 and is not claimed here,
* the surfaces share one parser + formatter: the Agent
  tool, the terminal ``/ssearch`` road, the TUI
  system-command road, and the chat screen's routing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mythic_agent.core import tree_sitter_foundation as foundation
from mythic_agent.core.gap_audit import load_audit
from mythic_agent.core.tree_sitter_foundation import (
    ParseUnavailableError,
    availability_for,
)
from mythic_agent.tools.structural_search import (
    PLAIN_EXPLANATION,
    STRUCTURAL_SEARCH_SLICE,
    PatternError,
    compile_pattern,
    format_search_status,
    parse_search_args,
    render_markdown,
    search_source,
    search_workspace,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

PY_SOURCE = (
    "def main():\n"
    "    foo(1, 2, 3)\n"
    "    foo(bar, baz)\n"
    "    other(1)\n"
    "    return foo(x)\n"
)


def _grammar_available(language):
    return availability_for(language).available


pytestmark = pytest.mark.skipif(
    not _grammar_available("python"),
    reason="python grammar not installed in this environment")


# ---------------------------------------------------------------------------
# The pattern language
# ---------------------------------------------------------------------------

class TestCompilePattern:
    def test_slice_and_explanation(self):
        assert STRUCTURAL_SEARCH_SLICE == "M-047"
        assert "Search only" in PLAIN_EXPLANATION
        assert "M-048" in PLAIN_EXPLANATION

    def test_metavariables_are_named_in_order(self):
        pattern = compile_pattern("foo($B, $$$REST)", "python")
        assert pattern.language == "python"
        assert pattern.backend == "tree_sitter"
        assert pattern.metavariables == ("B", "REST")
        assert pattern.text == "foo($B, $$$REST)"

    def test_exact_pattern_has_no_metavariables(self):
        pattern = compile_pattern("foo(1)", "python")
        assert pattern.metavariables == ()

    @pytest.mark.parametrize("bad", [
        "", "   ", "foo(", "foo($a)", "foo($$)", "foo($)",
        "foo($A, $$$A)",
    ])
    def test_malformed_patterns_are_refused(self, bad):
        with pytest.raises(PatternError):
            compile_pattern(bad, "python")

    def test_grammarless_language_is_refused_by_the_foundation(self):
        with pytest.raises(ParseUnavailableError):
            compile_pattern("foo($A)", "mojo")

    def test_unknown_language_is_key_error(self):
        with pytest.raises(KeyError):
            compile_pattern("foo($A)", "cobol")


# ---------------------------------------------------------------------------
# Matching — the roadmap's example, proven structurally
# ---------------------------------------------------------------------------

class TestMatching:
    def test_roadmap_example_with_captures(self):
        pattern = compile_pattern("foo($A, $$$)", "python")
        matches = search_source("a.py", PY_SOURCE, pattern)
        assert [(m.line, m.text) for m in matches] == [
            (2, "foo(1, 2, 3)"), (3, "foo(bar, baz)"),
            (5, "foo(x)")]
        first = {c.name: c.text for c in matches[0].captures}
        assert first == {"A": "1"}
        last = {c.name: c.text for c in matches[-1].captures}
        assert last == {"A": "x"}

    def test_named_many_captures_the_rest(self):
        pattern = compile_pattern("foo($A, $$$REST)", "python")
        matches = search_source("a.py", PY_SOURCE, pattern)
        rest = [{c.name: c.text for c in m.captures}
                for m in matches]
        assert rest[0]["REST"] == "2, 3"
        assert rest[1]["REST"] == "baz"
        assert rest[2]["REST"] == ""

    def test_single_meta_is_exactly_one_node(self):
        pattern = compile_pattern("foo($A)", "python")
        matches = search_source("a.py", PY_SOURCE, pattern)
        assert [(m.line, m.text) for m in matches] == [
            (5, "foo(x)")]

    def test_meta_function_name(self):
        pattern = compile_pattern("$F($A)", "python")
        matches = search_source("a.py", PY_SOURCE, pattern)
        got = {(m.text, tuple((c.name, c.text)
                               for c in m.captures))
               for m in matches}
        assert ("other(1)", (("F", "other"), ("A", "1"))) in got
        assert ("foo(x)", (("F", "foo"), ("A", "x"))) in got
        assert len(matches) == 2

    def test_repeated_meta_must_capture_the_same_text(self):
        pattern = compile_pattern("foo($A, $A)", "python")
        source = "foo(x, x)\nfoo(x, y)\n"
        matches = search_source("a.py", source, pattern)
        assert [(m.line, m.text) for m in matches] == [
            (1, "foo(x, x)")]

    def test_exact_text_must_agree(self):
        pattern = compile_pattern("foo(1, $$$)", "python")
        matches = search_source("a.py", PY_SOURCE, pattern)
        assert [m.text for m in matches] == ["foo(1, 2, 3)"]

    def test_matching_is_structural_never_textual(self):
        pattern = compile_pattern("foo($A)", "python")
        source = (
            "# foo(9) in a comment\n"
            "s = 'foo(9) in a string'\n"
            "bar(9)\n")
        assert search_source("a.py", source, pattern) == ()

    def test_operator_is_part_of_the_shape(self):
        pattern = compile_pattern("$A + $B", "python")
        source = "x = a + b\ny = a - b\nz = c + d\n"
        matches = search_source("a.py", source, pattern)
        assert [m.text for m in matches] == ["a + b", "c + d"]

    def test_nested_matches_are_each_reported(self):
        pattern = compile_pattern("foo($A)", "python")
        matches = search_source("a.py", "foo(foo(1))\n", pattern)
        assert [m.text for m in matches] == [
            "foo(foo(1))", "foo(1)"]

    def test_statement_pattern_with_named_many(self):
        pattern = compile_pattern(
            "def main():\n    $$$BODY", "python")
        matches = search_source("a.py", PY_SOURCE, pattern)
        assert len(matches) == 1
        body = {c.name: c.text for c in matches[0].captures}
        assert "foo(1, 2, 3)" in body["BODY"]
        assert "return foo(x)" in body["BODY"]

    def test_capture_spans_point_at_the_source(self):
        pattern = compile_pattern("foo($A, $$$)", "python")
        match = search_source("a.py", PY_SOURCE, pattern)[0]
        capture = match.captures[0]
        assert (capture.line, capture.column) == (2, 8)
        assert PY_SOURCE.splitlines()[1][8] == "1"
        assert (match.line, match.end_line) == (2, 2)

    def test_broken_target_source_raises_never_invents(self):
        # with the grammar installed a broken file parses with
        # errors and simply yields no clean match; on the ast
        # fallback it raises — either way nothing is invented
        pattern = compile_pattern("foo($A)", "python")
        matches = search_source("a.py", "def broken(:\n", pattern)
        assert matches == ()


class TestOtherLanguages:
    @pytest.mark.skipif(not _grammar_available("javascript"),
                        reason="javascript grammar not installed")
    def test_javascript_live(self):
        pattern = compile_pattern("foo($A, $$$REST)", "javascript")
        source = "foo(1, 2);\nbar(foo(3));\n"
        matches = search_source("a.js", source, pattern)
        assert [(m.line, m.text) for m in matches] == [
            (1, "foo(1, 2)"), (2, "foo(3)")]
        rest = {c.name: c.text for c in matches[0].captures}
        assert rest == {"A": "1", "REST": "2"}

    @pytest.mark.skipif(not _grammar_available("go"),
                        reason="go grammar not installed")
    def test_go_through_the_context_wrap(self):
        pattern = compile_pattern("foo($A)", "go")
        source = "package main\nfunc main() { foo(1); bar(2) }\n"
        matches = search_source("a.go", source, pattern)
        assert [(m.line, m.text) for m in matches] == [
            (2, "foo(1)")]

    @pytest.mark.skipif(not _grammar_available("rust"),
                        reason="rust grammar not installed")
    def test_rust_through_the_context_wrap(self):
        pattern = compile_pattern("foo($A)", "rust")
        source = "fn main() { foo(1); }\n"
        matches = search_source("a.rs", source, pattern)
        assert [(m.line, m.text) for m in matches] == [
            (1, "foo(1)")]

    def test_python_ast_fallback_matches_the_same(self, monkeypatch):
        monkeypatch.setattr(foundation, "_tree_sitter", None)
        pattern = compile_pattern("foo($A, $$$)", "python")
        assert pattern.backend == "python_ast"
        matches = search_source("a.py", PY_SOURCE, pattern)
        assert [(m.line, m.text) for m in matches] == [
            (2, "foo(1, 2, 3)"), (3, "foo(bar, baz)"),
            (5, "foo(x)")]
        with pytest.raises(PatternError):
            compile_pattern("foo(", "python")
        with pytest.raises(SyntaxError):
            search_source("a.py", "def broken(:\n", pattern)
        binop = compile_pattern("$A + $B", "python")
        matches = search_source(
            "a.py", "x = a + b\ny = a - b\n", binop)
        assert [m.text for m in matches] == ["a + b"]


# ---------------------------------------------------------------------------
# The workspace search
# ---------------------------------------------------------------------------

def _ws(tmp_path):
    root = tmp_path / "ws"
    root.mkdir()
    (root / "a.py").write_text(PY_SOURCE)
    (root / "b.py").write_text("foo(9)\n")
    (root / "c.js").write_text("foo(9);\n")
    (root / "broken.py").write_text("def broken(:\n")
    return root


class TestWorkspaceSearch:
    def test_workspace_counts_and_population(self, tmp_path):
        root = _ws(tmp_path)
        pattern = compile_pattern("foo($A, $$$)", "python")
        result = search_workspace(root, pattern)
        assert result.language == "python"
        assert result.files_seen == 3  # a.py, b.py, broken.py
        assert result.files_searched == 3
        assert result.skipped == ()
        assert {(m.path, m.text) for m in result.matches} >= {
            ("a.py", "foo(1, 2, 3)"), ("b.py", "foo(9)")}
        assert all(m.path != "c.js" for m in result.matches)
        assert any("broken.py" in w and "parsed with errors" in w
                   for w in result.warnings)

    def test_oversized_and_binary_files_are_skipped(self, tmp_path):
        root = tmp_path / "ws"
        root.mkdir()
        (root / "big.py").write_text("foo(1)\n" * 100)
        (root / "bin.py").write_bytes(b"foo(1)\x00\n")
        pattern = compile_pattern("foo($A)", "python")
        result = search_workspace(root, pattern, max_file_bytes=64)
        assert result.files_searched == 0
        reasons = {s.path: s.reason for s in result.skipped}
        assert "too large" in reasons["big.py"]
        assert reasons["bin.py"] == "binary file"

    def test_result_record_and_render(self, tmp_path):
        root = _ws(tmp_path)
        pattern = compile_pattern("foo($A, $$$)", "python")
        result = search_workspace(root, pattern)
        record = result.record()
        assert record["slice"] == "M-047"
        assert record["pattern"] == "foo($A, $$$)"
        assert record["matches"][0]["captures"][0]["name"] == "A"
        text = render_markdown(result)
        assert "Structural Search" in text
        assert "foo(1, 2, 3)" in text

    def test_bounds_are_validated(self, tmp_path):
        pattern = compile_pattern("foo($A)", "python")
        with pytest.raises(ValueError):
            search_workspace(tmp_path, pattern, max_files=0)
        with pytest.raises(ValueError):
            search_workspace(tmp_path, pattern, max_file_bytes=0)


# ---------------------------------------------------------------------------
# The gap audit truth flip
# ---------------------------------------------------------------------------

class TestGapAuditRow:
    def test_structural_row_names_an_existing_module(self):
        audit = load_audit()
        row = {r.feature: r for r in audit.rows}[
            "structural-search-rewrite"]
        assert row.owning_module == \
            "mythic_agent/tools/structural_search.py"
        assert row.module_kind == "existing"
        # the rewrite half (M-048) is still owed, not claimed
        assert row.state == "MISSING"
        assert (REPO_ROOT / row.owning_module).is_file()


# ---------------------------------------------------------------------------
# Surfaces — Agent tool + terminal + TUI command road
# ---------------------------------------------------------------------------

def _seed_agent_workspace(agent):
    root = Path(agent.project_root)
    (root / "core.py").write_text(PY_SOURCE)
    return root


class TestAgentTool:
    def test_agent_search_matches_the_pure_layer(self, agent):
        _seed_agent_workspace(agent)
        status = agent.structural_search("foo($A, $$$)", "python")
        result = search_workspace(
            agent.project_root,
            compile_pattern("foo($A, $$$)", "python"))
        assert status["result"] == result.record()
        assert status["plain_explanation"] == PLAIN_EXPLANATION

    def test_agent_refusals_are_plain(self, agent):
        _seed_agent_workspace(agent)
        with pytest.raises(PatternError):
            agent.structural_search("foo(", "python")
        with pytest.raises(ParseUnavailableError):
            agent.structural_search("foo($A)", "mojo")


class TestParseArgs:
    def test_grammar(self):
        request = parse_search_args("python foo($A, $$$)")
        assert request == {"action": "search",
                           "language": "python",
                           "pattern": "foo($A, $$$)"}

    def test_pattern_keeps_its_spaces(self):
        request = parse_search_args("Python def f($A): $$$BODY")
        assert request["language"] == "python"
        assert request["pattern"] == "def f($A): $$$BODY"

    @pytest.mark.parametrize("bad", ["", "python", None])
    def test_usage_errors(self, bad):
        with pytest.raises(ValueError, match="Usage: /ssearch"):
            parse_search_args(bad)

    def test_non_text_arguments_raise(self):
        with pytest.raises(ValueError, match="must be text"):
            parse_search_args(42)


class TestTerminalSurface:
    def test_search_flow(self, agent):
        from mythic_agent.terminal import _slash

        _seed_agent_workspace(agent)
        _, _, text = _slash(agent, "/ssearch python foo($A, $$$)")
        assert "Structural search (M-047)" in text
        assert "foo(1, 2, 3)" in text
        assert "$A = 1" in text

    def test_refusal_is_plain(self, agent):
        from mythic_agent.terminal import _slash

        _seed_agent_workspace(agent)
        _, _, text = _slash(agent, "/ssearch python foo(")
        assert "does not parse" in text
        _, _, text = _slash(agent, "/ssearch")
        assert text.startswith("Usage: /ssearch")


@pytest.fixture()
def handler(agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY

    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestSsearchCommand:
    def test_search(self, handler, agent):
        _seed_agent_workspace(agent)
        handler._handle_ssearch("python foo($A, $$$)")
        text = _published_text(handler)
        assert "Structural search (M-047)" in text
        assert "foo(bar, baz)" in text

    def test_usage_error_is_plain(self, handler, agent):
        _seed_agent_workspace(agent)
        handler._handle_ssearch("")
        assert "Usage: /ssearch" in _published_text(handler)


class TestChatScreenRouting:
    def test_ssearch_routes_as_system_command(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import MainChatScreen

        class _FakeLog:
            def __init__(self):
                self.lines = []

            def write(self, *args, **kwargs):
                self.lines.append(" ".join(str(a) for a in args))

        calls = []
        monkeypatch.setattr(
            chat_screen.SecureAPI, "publish_system_command",
            staticmethod(lambda cmd, args: calls.append((cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        screen.handle_command("/ssearch python foo($A)", _FakeLog())
        assert calls == [("/ssearch", "python foo($A)")]

    def test_format_status_from_agent_record(self, agent):
        _seed_agent_workspace(agent)
        status = agent.structural_search("foo($A)", "python")
        text = format_search_status(status)
        assert "1 match(es)" in text
        assert "core.py:5" in text
