"""M-048 — Structural rewrite.

TIER: integration

Part III (Code Intelligence): the M-047 patterns as safe
codemods — "change every call like `foo($A, $$$)` into
`bar($A, $$$)`" — with per-site diff previews and
application only through the edit journal, only for files
still exactly as the plan saw them.

These tests do not take the rewrite's word for any of it:

* the replacement compiles through M-047's own machinery,
  and a replacement that cannot be filled is refused
  before anything is planned: unparseable, an unnamed
  $$$, a metavariable the pattern never captures, and a
  single/multi kind mismatch,
* rendering fills each placeholder span with the match's
  own captured text — single captures, joined multi
  captures, a repeated metavariable rendering the same
  text everywhere, nested matches rendered site by site,
* a plan over a real workspace carries per-site unified
  diffs with the true -/+ lines, the file's plan-time
  sha256, and the file's full new content; overlapping
  (nested) sites are refused on the plan, with the reason;
  planning alone changes no file bytes,
* application writes exactly the previewed content
  through the EditJournal (its journal proves the edit by
  undoing it), refuses a file changed since the plan
  whole and untouched while other files still apply, and
  the apply record carries the previews,
* the surfaces share one parser + formatter: the Agent
  tool (preview by default), the terminal ``/srewrite``
  road, the TUI system-command road, and the chat
  screen's routing,
* the gap audit's structural row stays exactly as its
  cross-checks allow (see TestGapAuditRow), and Mojo /
  uncatalogued-language refusals ride M-047's errors.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from mythic_agent.core import tree_sitter_foundation as foundation
from mythic_agent.core.gap_audit import load_audit
from mythic_agent.core.tree_sitter_foundation import (
    ParseUnavailableError,
    availability_for,
)
from mythic_agent.tools.structural_rewrite import (
    PLAIN_EXPLANATION,
    STRUCTURAL_REWRITE_SLICE,
    apply_rewrite,
    compile_replacement,
    format_rewrite_status,
    parse_rewrite_args,
    plan_rewrite,
    render_markdown,
    render_replacement,
)
from mythic_agent.tools.structural_search import (
    PatternError,
    compile_pattern,
    search_source,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

PY_SOURCE = (
    "def main():\n"
    "    foo(1, 2, 3)\n"
    "    foo(bar, baz)\n"
    "    other(1)\n"
    "    return foo(x)\n"
)

REWRITTEN = (
    "def main():\n"
    "    bar(1)\n"
    "    bar(bar)\n"
    "    other(1)\n"
    "    return bar(x)\n"
)


def _grammar_available(language):
    return availability_for(language).available


pytestmark = pytest.mark.skipif(
    not _grammar_available("python"),
    reason="python grammar not installed in this environment")


def _ws(tmp_path, files=None):
    root = tmp_path / "ws"
    root.mkdir()
    for name, text in (files or {"a.py": PY_SOURCE}).items():
        (root / name).write_text(text)
    return root


# ---------------------------------------------------------------------------
# Compiling a replacement — the refusals come first
# ---------------------------------------------------------------------------

class TestCompileReplacement:
    def test_slice_and_explanation(self):
        assert STRUCTURAL_REWRITE_SLICE == "M-048"
        assert "preview writes nothing" in PLAIN_EXPLANATION
        assert "edit journal" in PLAIN_EXPLANATION

    def test_compiles_through_the_search_machinery(self):
        pattern = compile_pattern("foo($A, $$$REST)", "python")
        replacement = compile_replacement(
            "bar($A, $$$REST)", "python", pattern)
        assert replacement.language == "python"
        assert replacement.compiled.backend == pattern.backend

    def test_unparseable_replacement_is_refused(self):
        pattern = compile_pattern("foo($A)", "python")
        with pytest.raises(PatternError):
            compile_replacement("bar(", "python", pattern)

    def test_unnamed_many_in_replacement_is_refused(self):
        pattern = compile_pattern("foo($A, $$$)", "python")
        with pytest.raises(PatternError, match="unnamed"):
            compile_replacement("bar($A, $$$)", "python", pattern)

    def test_uncaptured_single_is_refused(self):
        pattern = compile_pattern("foo($A)", "python")
        with pytest.raises(PatternError, match="never captures"):
            compile_replacement("bar($B)", "python", pattern)

    def test_uncaptured_many_is_refused(self):
        pattern = compile_pattern("foo($A)", "python")
        with pytest.raises(PatternError, match="never captures"):
            compile_replacement("bar($A, $$$REST)", "python", pattern)

    def test_single_used_as_many_is_a_kind_mismatch(self):
        pattern = compile_pattern("foo($A)", "python")
        with pytest.raises(PatternError, match="one thing"):
            compile_replacement("bar($$$A)", "python", pattern)

    def test_many_used_as_single_is_a_kind_mismatch(self):
        pattern = compile_pattern("foo($$$REST)", "python")
        with pytest.raises(PatternError, match="one thing"):
            compile_replacement("bar($REST)", "python", pattern)

    def test_constant_replacement_needs_no_captures(self):
        pattern = compile_pattern("foo($A)", "python")
        replacement = compile_replacement("bar(0)", "python", pattern)
        assert replacement.text == "bar(0)"

    def test_grammarless_language_is_refused_by_the_foundation(self):
        pattern = compile_pattern("foo($A)", "python")
        with pytest.raises(ParseUnavailableError):
            compile_replacement("bar($A)", "mojo", pattern)

    def test_unknown_language_is_key_error(self):
        pattern = compile_pattern("foo($A)", "python")
        with pytest.raises(KeyError):
            compile_replacement("bar($A)", "cobol", pattern)


# ---------------------------------------------------------------------------
# Rendering — placeholders filled from the match's captures
# ---------------------------------------------------------------------------

class TestRendering:
    def _render(self, pattern_text, replacement_text, source,
                language="python"):
        pattern = compile_pattern(pattern_text, language)
        replacement = compile_replacement(
            replacement_text, language, pattern)
        return [render_replacement(replacement, match)
                for match in search_source("a.py", source, pattern)]

    def test_single_capture_is_substituted(self):
        rendered = self._render(
            "foo($A, $$$)", "bar($A)", PY_SOURCE)
        assert rendered == ["bar(1)", "bar(bar)", "bar(x)"]

    def test_named_many_is_the_joined_capture(self):
        rendered = self._render(
            "foo($A, $$$REST)", "bar($A, $$$REST)", PY_SOURCE)
        assert rendered == [
            "bar(1, 2, 3)", "bar(bar, baz)", "bar(x, )"]

    def test_repeated_metavariable_renders_the_same_text(self):
        rendered = self._render(
            "foo($A)", "pair($A, $A)", "foo(7)\n")
        assert rendered == ["pair(7, 7)"]

    def test_nested_matches_render_site_by_site(self):
        rendered = self._render(
            "foo($A)", "bar($A)", "foo(foo(1))\n")
        assert rendered == ["bar(foo(1))", "bar(1)"]

    def test_callee_metavariable_renders(self):
        rendered = self._render("$F($A)", "$F($A, 0)", "foo(1)\n")
        assert rendered == ["foo(1, 0)"]

    def test_python_ast_fallback_renders_the_same(self, monkeypatch):
        monkeypatch.setattr(foundation, "_tree_sitter", None)
        rendered = self._render(
            "foo($A, $$$REST)", "bar($A, $$$REST)", PY_SOURCE)
        assert rendered == [
            "bar(1, 2, 3)", "bar(bar, baz)", "bar(x, )"]


# ---------------------------------------------------------------------------
# The plan — previews as data, nothing written
# ---------------------------------------------------------------------------

class TestPlan:
    def test_plan_sites_previews_and_new_content(self, tmp_path):
        root = _ws(tmp_path)
        plan = plan_rewrite(
            root, "foo($A, $$$)", "bar($A)", "python")
        record = plan.record()
        assert record["slice"] == "M-048"
        assert record["counts"] == {
            "matches": 3, "planned": 3, "refused": 0, "files": 1}
        assert plan.files[0].new_content == REWRITTEN
        site = plan.sites[0]
        assert (site.line, site.text) == (2, "foo(1, 2, 3)")
        assert site.replacement == "bar(1)"
        assert site.status == "planned"
        # the per-site diff carries the true -/+ lines
        assert "-    foo(1, 2, 3)" in site.diff
        assert "+    bar(1)" in site.diff
        # every site's own preview is independently readable:
        # its changed lines are only its own (other sites may
        # appear as unchanged context, never as -/+ lines)
        last = plan.sites[-1]
        assert "-    return foo(x)" in last.diff
        assert "+    return bar(x)" in last.diff
        assert "-    foo(1, 2, 3)" not in last.diff
        assert "+    bar(1)" not in last.diff

    def test_plan_hash_is_the_files_sha256(self, tmp_path):
        root = _ws(tmp_path)
        plan = plan_rewrite(root, "foo($A)", "bar($A)", "python")
        digest = hashlib.sha256(
            (root / "a.py").read_bytes()).hexdigest()
        assert plan.files[0].sha256 == digest

    def test_match_byte_spans_slice_the_source(self, tmp_path):
        root = _ws(tmp_path)
        plan = plan_rewrite(root, "foo($A, $$$)", "bar($A)", "python")
        raw = (root / "a.py").read_bytes()
        for site in plan.sites:
            assert raw[site.start_byte:site.end_byte].decode() \
                == site.text

    def test_byte_spans_survive_non_ascii_text(self, tmp_path):
        source = "# café — naïve\nfoo(1)\nx = 'é'; foo(2)\n"
        root = _ws(tmp_path, {"a.py": source})
        plan = plan_rewrite(root, "foo($A)", "bar($A)", "python")
        raw = (root / "a.py").read_bytes()
        assert [site.text for site in plan.sites] == [
            "foo(1)", "foo(2)"]
        for site in plan.sites:
            assert raw[site.start_byte:site.end_byte].decode() \
                == site.text
        assert "bar(2)" in plan.files[0].new_content

    def test_planning_never_writes(self, tmp_path):
        root = _ws(tmp_path)
        before = (root / "a.py").read_bytes()
        plan_rewrite(root, "foo($A, $$$)", "bar($A)", "python")
        assert (root / "a.py").read_bytes() == before

    def test_overlapping_sites_are_refused_with_reason(self, tmp_path):
        root = _ws(tmp_path, {"a.py": "foo(foo(1))\n"})
        plan = plan_rewrite(root, "foo($A)", "bar($A)", "python")
        assert len(plan.sites) == 2
        assert all(site.status == "refused" for site in plan.sites)
        assert all("overlaps another match" in site.refusal_reason
                   for site in plan.sites)
        # a refused site is not applied to the planned content
        assert plan.files[0].new_content == "foo(foo(1))\n"
        assert plan.record()["counts"]["refused"] == 2

    def test_search_skips_ride_the_plan(self, tmp_path):
        root = _ws(tmp_path)
        (root / "bin.py").write_bytes(b"foo(1)\x00\n")
        plan = plan_rewrite(root, "foo($A)", "bar($A)", "python")
        reasons = {skip.path: skip.reason for skip in plan.skipped}
        assert reasons["bin.py"] == "binary file"

    def test_multi_file_plan(self, tmp_path):
        root = _ws(tmp_path, {
            "a.py": "foo(1)\n", "b.py": "foo(2)\nfoo(3)\n"})
        plan = plan_rewrite(root, "foo($A)", "bar($A)", "python")
        by_path = {f.path: f for f in plan.files}
        assert by_path["a.py"].new_content == "bar(1)\n"
        assert by_path["b.py"].new_content == "bar(2)\nbar(3)\n"

    def test_no_matches_is_a_plan_not_an_error(self, tmp_path):
        root = _ws(tmp_path, {"a.py": "other(1)\n"})
        plan = plan_rewrite(root, "foo($A)", "bar($A)", "python")
        assert plan.sites == ()
        assert plan.files == ()

    def test_render_markdown_is_built_from_the_plan(self, tmp_path):
        root = _ws(tmp_path)
        plan = plan_rewrite(
            root, "foo($A, $$$)", "bar($A)", "python")
        text = render_markdown(plan)
        assert "Structural Rewrite" in text
        assert "foo(1, 2, 3)" in text
        assert "bar(1)" in text


# ---------------------------------------------------------------------------
# The application — journal-first, hash-guarded
# ---------------------------------------------------------------------------

def _seed_agent_workspace(agent):
    root = Path(agent.project_root)
    (root / "core.py").write_text(PY_SOURCE)
    return root


class TestApply:
    def test_apply_writes_exactly_the_previewed_content(self, agent):
        root = _seed_agent_workspace(agent)
        plan = plan_rewrite(
            root, "foo($A, $$$)", "bar($A)", "python")
        result = apply_rewrite(root, plan)
        assert (root / "core.py").read_text() == REWRITTEN
        outcome = result.outcomes[0]
        assert (outcome.status, outcome.sites_applied) == ("applied", 3)

    def test_the_journal_records_the_edit(self, agent):
        from mythic_agent.core.edits import EditJournal

        root = _seed_agent_workspace(agent)
        plan = plan_rewrite(
            root, "foo($A, $$$)", "bar($A)", "python")
        apply_rewrite(root, plan)
        assert (root / "core.py").read_text() == REWRITTEN
        # the repo's own journal road proves the edit: undo
        # restores the file the plan started from
        assert "Restored" in EditJournal(root).undo()
        assert (root / "core.py").read_text() == PY_SOURCE

    def test_stale_file_is_refused_whole_and_untouched(self, agent):
        root = _seed_agent_workspace(agent)
        (root / "other.py").write_text("foo(9)\n")
        plan = plan_rewrite(root, "foo($A)", "bar($A)", "python")
        (root / "core.py").write_text("foo(1)  # changed since\n")
        result = apply_rewrite(root, plan)
        outcomes = {o.path: o for o in result.outcomes}
        assert outcomes["core.py"].status == "refused-stale"
        assert "changed since the plan" in outcomes["core.py"].reason
        assert (root / "core.py").read_text() == \
            "foo(1)  # changed since\n"
        # one file's refusal never blocks the others
        assert outcomes["other.py"].status == "applied"
        assert (root / "other.py").read_text() == "bar(9)\n"

    def test_all_refused_file_reports_refused_overlap(self, agent):
        root = Path(agent.project_root)
        (root / "nested.py").write_text("foo(foo(1))\n")
        plan = plan_rewrite(root, "foo($A)", "bar($A)", "python")
        result = apply_rewrite(root, plan)
        assert result.outcomes[0].status == "refused-overlap"
        assert (root / "nested.py").read_text() == "foo(foo(1))\n"

    def test_apply_record_carries_the_previews(self, agent):
        root = _seed_agent_workspace(agent)
        plan = plan_rewrite(
            root, "foo($A, $$$)", "bar($A)", "python")
        record = apply_rewrite(root, plan).record()
        assert record["slice"] == "M-048"
        assert record["counts"] == {"applied": 1}
        assert "-    foo(1, 2, 3)" in record["plan"]["sites"][0]["diff"]
        assert record["plan"]["counts"]["planned"] == 3


# ---------------------------------------------------------------------------
# The gap audit truth
# ---------------------------------------------------------------------------

class TestGapAuditRow:
    def test_structural_row_stays_validator_consistent(self):
        # The audit's cross-check pins a row's state to the
        # census row's Mythic state, and the census counts a
        # feature as a gap only while it is PARTIAL/MISSING —
        # so neither file can honestly flip to HAVE alone,
        # exactly as M-044's shipped repo-map row still reads
        # MISSING in both. What M-048 can truthfully assert
        # is that the row loads against the real tree with
        # its module standing.
        audit = load_audit(repo_root=REPO_ROOT)
        row = audit.row("structural-search-rewrite")
        assert row.owning_module == \
            "mythic_agent/tools/structural_search.py"
        assert row.module_kind == "existing"
        assert row.state == "MISSING"
        assert (REPO_ROOT / row.owning_module).is_file()
        assert (REPO_ROOT /
                "mythic_agent/tools/structural_rewrite.py").is_file()


# ---------------------------------------------------------------------------
# Surfaces — Agent tool + terminal + TUI command road
# ---------------------------------------------------------------------------

class TestAgentTool:
    def test_agent_preview_matches_the_pure_layer(self, agent):
        root = _seed_agent_workspace(agent)
        status = agent.structural_rewrite(
            "foo($A, $$$)", "bar($A)", "python")
        plan = plan_rewrite(
            root, "foo($A, $$$)", "bar($A)", "python")
        assert status["result"] == plan.record()
        assert status["plain_explanation"] == PLAIN_EXPLANATION
        # a preview writes nothing
        assert (root / "core.py").read_text() == PY_SOURCE

    def test_agent_apply_only_when_asked(self, agent):
        root = _seed_agent_workspace(agent)
        status = agent.structural_rewrite(
            "foo($A, $$$)", "bar($A)", "python", apply=True)
        assert status["result"]["counts"] == {"applied": 1}
        assert status["result"]["plan"]["counts"]["planned"] == 3
        assert (root / "core.py").read_text() == REWRITTEN

    def test_agent_refusals_are_plain(self, agent):
        _seed_agent_workspace(agent)
        with pytest.raises(PatternError):
            agent.structural_rewrite("foo($A)", "bar($B)", "python")
        with pytest.raises(ParseUnavailableError):
            agent.structural_rewrite("foo($A)", "bar($A)", "mojo")


class TestParseArgs:
    def test_preview_grammar(self):
        request = parse_rewrite_args("python foo($A) => bar($A)")
        assert request == {"action": "preview", "language": "python",
                           "pattern": "foo($A)",
                           "replacement": "bar($A)"}

    def test_apply_grammar(self):
        request = parse_rewrite_args(
            "apply Python foo($A, $$$) => bar($A)")
        assert request["action"] == "apply"
        assert request["language"] == "python"
        assert request["pattern"] == "foo($A, $$$)"
        assert request["replacement"] == "bar($A)"

    def test_replacement_keeps_its_spaces(self):
        request = parse_rewrite_args(
            "python foo($A) => bar($A, 0)")
        assert request["replacement"] == "bar($A, 0)"

    @pytest.mark.parametrize("bad", [
        "", "python", "python foo($A)", "python => bar($A)",
        "python foo($A) =>", "apply", None])
    def test_usage_errors(self, bad):
        with pytest.raises(ValueError, match="Usage: /srewrite"):
            parse_rewrite_args(bad)

    def test_non_text_arguments_raise(self):
        with pytest.raises(ValueError, match="must be text"):
            parse_rewrite_args(42)


class TestTerminalSurface:
    def test_preview_flow_shows_diffs_and_writes_nothing(self, agent):
        from mythic_agent.terminal import _slash

        root = _seed_agent_workspace(agent)
        _, _, text = _slash(
            agent, "/srewrite python foo($A, $$$) => bar($A)")
        assert "Structural rewrite (M-048)" in text
        assert "preview only" in text
        assert "-    foo(1, 2, 3)" in text
        assert "+    bar(1)" in text
        assert (root / "core.py").read_text() == PY_SOURCE

    def test_apply_flow(self, agent):
        from mythic_agent.terminal import _slash

        root = _seed_agent_workspace(agent)
        _, _, text = _slash(
            agent, "/srewrite apply python foo($A, $$$) => bar($A)")
        assert "applied: core.py" in text
        assert (root / "core.py").read_text() == REWRITTEN

    def test_refusal_is_plain(self, agent):
        from mythic_agent.terminal import _slash

        _seed_agent_workspace(agent)
        _, _, text = _slash(
            agent, "/srewrite python foo($A) => bar($B)")
        assert "never captures" in text
        _, _, text = _slash(agent, "/srewrite")
        assert text.startswith("Usage: /srewrite")


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


class TestSrewriteCommand:
    def test_preview(self, handler, agent):
        root = _seed_agent_workspace(agent)
        handler._handle_srewrite("python foo($A, $$$) => bar($A)")
        text = _published_text(handler)
        assert "Structural rewrite (M-048)" in text
        assert "bar(bar)" in text
        assert (root / "core.py").read_text() == PY_SOURCE

    def test_apply(self, handler, agent):
        root = _seed_agent_workspace(agent)
        handler._handle_srewrite(
            "apply python foo($A, $$$) => bar($A)")
        text = _published_text(handler)
        assert "applied: core.py" in text
        assert (root / "core.py").read_text() == REWRITTEN

    def test_usage_error_is_plain(self, handler, agent):
        _seed_agent_workspace(agent)
        handler._handle_srewrite("")
        assert "Usage: /srewrite" in _published_text(handler)


class TestChatScreenRouting:
    def test_srewrite_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command(
            "/srewrite python foo($A) => bar($A)", _FakeLog())
        assert calls == [("/srewrite", "python foo($A) => bar($A)")]

    def test_format_status_from_agent_record(self, agent):
        _seed_agent_workspace(agent)
        status = agent.structural_rewrite(
            "foo($A, $$$)", "bar($A)", "python")
        text = format_rewrite_status(status)
        assert "3 site(s)" in text
        assert "core.py:2" in text
        assert "+    bar(1)" in text
