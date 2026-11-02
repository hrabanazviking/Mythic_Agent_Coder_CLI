"""M-044 — The Repo Map.

TIER: integration

Part III (Code Intelligence): a token-budgeted map of the
whole repo — files, classes, functions, signatures — ranked
by relevance to the current task (PageRank over the
reference graph), refreshed incrementally.

These tests do not take the map's word for any of it:

* definitions come from the M-043 parses (Python plus a
  grammar-backed second language), each entry naming its
  parse backend and carrying signature lines as written,
* the reference graph is name-mention truth: a file that
  mentions another file's symbol references it, and
  PageRank rewards the referenced file — computed ranks
  sum to 1 and are deterministic across rebuilds,
* task relevance is explainable arithmetic: a query naming
  a symbol multiplies that file's score by (1 + matches),
  the matched symbols ride the entry, and every entry
  carries plain reasons,
* the token budget is enforced by the shipped estimator:
  the rendered map never exceeds it, entries beyond the
  budget are named as omitted (never silently dropped),
  and inclusion follows rank order,
* refresh is incremental by content hash: an unchanged
  file's parse is reused, a changed file's is not, a new
  file is parsed, a vanished file drops out,
* honesty: a Mojo file is skipped with its grammar-less
  reason in every environment, an oversized file is
  skipped with its size reason, and the RepoMapSource
  serves the map through the real context compiler.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mythic_agent.context.budget import TokenEstimator
from mythic_agent.context.compiler import CompileContext, ContextCompiler
from mythic_agent.context.repo_map import (
    DEFAULT_MAP_BUDGET_TOKENS,
    PAGERANK_DAMPING,
    REPO_MAP_SLICE,
    RepoMapSource,
    build_repo_map,
    compute_pagerank,
    render_repo_map,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _ws(tmp_path):
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
    (tmp_path / "lonely.py").write_text(
        "def unused_helper():\n"
        "    return 42\n")
    return tmp_path


def _entry(repo_map, path):
    for entry in repo_map.entries:
        if entry.path == path:
            return entry
    raise AssertionError(f"no entry for {path}: "
                         f"{[e.path for e in repo_map.entries]}")


# ---------------------------------------------------------------------------
# the build: definitions from the M-043 parses
# ---------------------------------------------------------------------------

def test_slice_identity_and_defaults():
    assert REPO_MAP_SLICE == "M-044"
    assert DEFAULT_MAP_BUDGET_TOKENS == 1000
    assert PAGERANK_DAMPING == 0.85


def test_build_maps_files_definitions_and_signatures(tmp_path):
    repo_map = build_repo_map(_ws(tmp_path), budget_tokens=10_000)
    assert repo_map.files_seen == 3
    assert repo_map.reparsed_files == 3
    assert repo_map.reused_files == 0
    assert repo_map.skipped == ()
    core = _entry(repo_map, "core.py")
    assert core.language == "python"
    assert core.backend in ("tree_sitter", "python_ast")
    by_name = {d.name: d for d in core.definitions}
    assert by_name["Engine"].kind == "class"
    assert by_name["Engine"].signature == "class Engine:"
    assert by_name["Engine"].line == 1
    assert by_name["build_engine"].kind == "function"
    assert by_name["build_engine"].signature == "def build_engine():"
    assert by_name["build_engine"].line == 5


def test_build_maps_a_second_grammar_language(tmp_path):
    (tmp_path / "main.go").write_text(
        "package main\n\nfunc main() {}\n")
    repo_map = build_repo_map(tmp_path, budget_tokens=10_000)
    entry = _entry(repo_map, "main.go")
    assert entry.language == "go"
    assert entry.backend == "tree_sitter"
    assert {d.name for d in entry.definitions} >= {"main"}


def test_non_code_files_are_not_candidates(tmp_path):
    (tmp_path / "notes.txt").write_text("def not_code():\n")
    (tmp_path / "real.py").write_text("def real():\n    pass\n")
    repo_map = build_repo_map(tmp_path, budget_tokens=10_000)
    assert repo_map.files_seen == 1
    assert [e.path for e in repo_map.entries] == ["real.py"]


def test_hidden_and_vendor_dirs_are_skipped(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "hooked.py").write_text("def hooked():\n    pass\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "dep.py").write_text("def dep():\n    pass\n")
    (tmp_path / "mine.py").write_text("def mine():\n    pass\n")
    repo_map = build_repo_map(tmp_path, budget_tokens=10_000)
    assert [e.path for e in repo_map.entries] == ["mine.py"]


# ---------------------------------------------------------------------------
# the reference graph and PageRank
# ---------------------------------------------------------------------------

def test_reference_graph_and_pagerank_reward_the_referenced(tmp_path):
    repo_map = build_repo_map(_ws(tmp_path), budget_tokens=10_000)
    core = _entry(repo_map, "core.py")
    app = _entry(repo_map, "app.py")
    lonely = _entry(repo_map, "lonely.py")
    assert app.references_out == ("core.py",)
    assert core.references_in == ("app.py",)
    assert lonely.references_in == ()
    assert core.pagerank > lonely.pagerank
    total = sum(e.pagerank for e in repo_map.entries)
    assert total == pytest.approx(1.0, abs=1e-6)


def test_pagerank_is_deterministic_and_sums_to_one():
    edges = {"a.py": ("b.py",), "b.py": (), "c.py": ("b.py",)}
    first = compute_pagerank(("c.py", "a.py", "b.py"), edges)
    second = compute_pagerank(("b.py", "c.py", "a.py"), edges)
    assert first == second
    assert sum(first.values()) == pytest.approx(1.0, abs=1e-6)
    assert first["b.py"] > first["a.py"]  # referenced by both others
    assert first["a.py"] == pytest.approx(first["c.py"])
    assert compute_pagerank((), {}) == {}


def test_ranking_is_deterministic_across_rebuilds(tmp_path):
    ws = _ws(tmp_path)
    one = build_repo_map(ws, budget_tokens=10_000)
    two = build_repo_map(ws, budget_tokens=10_000)
    assert [e.path for e in one.entries] == [e.path for e in two.entries]
    assert [e.score for e in one.entries] == [e.score for e in two.entries]


# ---------------------------------------------------------------------------
# task relevance, explained
# ---------------------------------------------------------------------------

def test_query_relevance_multiplies_and_is_named(tmp_path):
    repo_map = build_repo_map(
        _ws(tmp_path), query="fix build_engine please",
        budget_tokens=10_000)
    core = _entry(repo_map, "core.py")
    assert core.matched_symbols == ("build_engine",)
    assert core.score == pytest.approx(core.pagerank * 2)
    assert repo_map.entries[0].path == "core.py"
    assert any("matches the task: defines build_engine" in r
               for r in core.reasons)


def test_path_match_counts_and_is_named(tmp_path):
    repo_map = build_repo_map(
        _ws(tmp_path), query="the lonely module", budget_tokens=10_000)
    lonely = _entry(repo_map, "lonely.py")
    assert lonely.path_matched is True
    assert lonely.score == pytest.approx(lonely.pagerank * 2)
    assert any("file name matches the task" in r for r in lonely.reasons)


def test_no_query_score_is_the_pagerank_itself(tmp_path):
    repo_map = build_repo_map(_ws(tmp_path), budget_tokens=10_000)
    for entry in repo_map.entries:
        assert entry.score == pytest.approx(entry.pagerank)
        assert entry.matched_symbols == ()
        assert entry.reasons  # every entry explains itself
        assert any(r.startswith("PageRank ") for r in entry.reasons)


# ---------------------------------------------------------------------------
# the token budget
# ---------------------------------------------------------------------------

def test_rendered_map_never_exceeds_the_budget(tmp_path):
    estimator = TokenEstimator()
    repo_map = build_repo_map(
        _ws(tmp_path), budget_tokens=40, estimator=estimator)
    rendered = render_repo_map(repo_map)
    assert estimator.count(rendered) <= 40
    assert repo_map.omitted  # the three files cannot all fit in 40 tokens
    included = [e.path for e in repo_map.entries]
    assert included  # but the header and the top entry do
    # omitted files are exactly the ranked remainder, named not dropped
    assert set(included) | set(repo_map.omitted) == {
        "app.py", "core.py", "lonely.py"}
    for path in repo_map.omitted:
        assert path not in rendered


def test_zero_budget_maps_nothing_but_names_everything(tmp_path):
    repo_map = build_repo_map(_ws(tmp_path), budget_tokens=0)
    assert repo_map.entries == ()
    assert set(repo_map.omitted) == {"app.py", "core.py", "lonely.py"}


def test_inclusion_follows_rank_order(tmp_path):
    estimator = TokenEstimator()
    full = build_repo_map(_ws(tmp_path), budget_tokens=10_000)
    ranked_paths = [e.path for e in full.entries]
    tight = build_repo_map(_ws(tmp_path), budget_tokens=40)
    assert [e.path for e in tight.entries] == ranked_paths[:len(tight.entries)]
    assert list(tight.omitted) == ranked_paths[len(tight.entries):]


def test_negative_budget_is_refused(tmp_path):
    with pytest.raises(ValueError):
        build_repo_map(_ws(tmp_path), budget_tokens=-1)


# ---------------------------------------------------------------------------
# incremental refresh
# ---------------------------------------------------------------------------

def test_refresh_reuses_unchanged_parses(tmp_path):
    ws = _ws(tmp_path)
    first = build_repo_map(ws, budget_tokens=10_000)
    second = build_repo_map(ws, budget_tokens=10_000, previous=first)
    assert second.reused_files == 3
    assert second.reparsed_files == 0
    assert [e.path for e in second.entries] == [e.path for e in first.entries]
    assert [e.score for e in second.entries] == [e.score for e in first.entries]


def test_refresh_reparses_changed_and_new_and_drops_vanished(tmp_path):
    ws = _ws(tmp_path)
    first = build_repo_map(ws, budget_tokens=10_000)
    (ws / "core.py").write_text(
        "class Engine:\n"
        "    def start(self):\n"
        "        return 'on'\n"
        "\n"
        "def build_engine():\n"
        "    return Engine()\n"
        "\n"
        "def shutdown():\n"
        "    return None\n")
    (ws / "extra.py").write_text("def extra():\n    return build_engine()\n")
    (ws / "lonely.py").unlink()
    second = build_repo_map(ws, budget_tokens=10_000, previous=first)
    assert second.reused_files == 1  # app.py only
    assert second.reparsed_files == 2  # core.py changed, extra.py new
    paths = [e.path for e in second.entries]
    assert "lonely.py" not in paths
    assert "extra.py" in paths
    core = _entry(second, "core.py")
    assert "shutdown" in {d.name for d in core.definitions}
    assert _entry(second, "extra.py").references_out == ("core.py",)


def test_refresh_ranking_is_recomputed_not_reused(tmp_path):
    ws = _ws(tmp_path)
    first = build_repo_map(ws, budget_tokens=10_000)
    second = build_repo_map(
        ws, query="unused_helper", budget_tokens=10_000, previous=first)
    assert second.reused_files == 3  # parses reused...
    lonely = _entry(second, "lonely.py")
    assert lonely.matched_symbols == ("unused_helper",)
    assert second.entries[0].path == "lonely.py"  # ...ranking is fresh


# ---------------------------------------------------------------------------
# honesty: skipped files and their reasons
# ---------------------------------------------------------------------------

def test_mojo_is_skipped_with_its_grammarless_reason(tmp_path):
    (tmp_path / "spell.mojo").write_text("fn main():\n    pass\n")
    (tmp_path / "real.py").write_text("def real():\n    pass\n")
    repo_map = build_repo_map(tmp_path, budget_tokens=10_000)
    assert [e.path for e in repo_map.entries] == ["real.py"]
    assert len(repo_map.skipped) == 1
    skip = repo_map.skipped[0]
    assert skip.path == "spell.mojo"
    assert "no tree-sitter grammar package is published" in skip.reason


def test_oversized_file_is_skipped_with_its_size_reason(tmp_path):
    (tmp_path / "big.py").write_text("def big():\n    pass\n")
    repo_map = build_repo_map(tmp_path, budget_tokens=10_000, max_file_bytes=8)
    assert repo_map.entries == ()
    assert len(repo_map.skipped) == 1
    assert "too large for the map" in repo_map.skipped[0].reason


def test_file_cap_is_a_warning_never_silence(tmp_path):
    for i in range(4):
        (tmp_path / f"f{i}.py").write_text(f"def f{i}():\n    pass\n")
    repo_map = build_repo_map(tmp_path, budget_tokens=10_000, max_files=2)
    assert repo_map.files_seen == 2
    assert any("file cap reached (2)" in w for w in repo_map.warnings)


def test_empty_workspace_maps_to_an_empty_map(tmp_path):
    repo_map = build_repo_map(tmp_path, budget_tokens=10_000)
    assert repo_map.entries == ()
    assert repo_map.files_seen == 0
    assert render_repo_map(repo_map).startswith("# Repo Map")


# ---------------------------------------------------------------------------
# rendering + records
# ---------------------------------------------------------------------------

def test_render_shows_files_and_signatures(tmp_path):
    repo_map = build_repo_map(_ws(tmp_path), budget_tokens=10_000)
    rendered = render_repo_map(repo_map)
    assert "core.py:" in rendered
    assert "class Engine:" in rendered
    assert "def build_engine():" in rendered
    assert estimator_fits(repo_map, rendered)


def estimator_fits(repo_map, rendered):
    return TokenEstimator().count(rendered) <= repo_map.budget_tokens


def test_record_is_plain_data_with_the_whole_story(tmp_path):
    repo_map = build_repo_map(_ws(tmp_path), budget_tokens=10_000)
    record = repo_map.record()
    assert record["files_seen"] == 3
    assert record["budget_tokens"] == 10_000
    core = next(e for e in record["entries"] if e["path"] == "core.py")
    assert core["references_in"] == ["app.py"]
    assert core["definitions"][0]["name"] == "Engine"
    assert len(core["content_hash"]) == 64


# ---------------------------------------------------------------------------
# the compiler source
# ---------------------------------------------------------------------------

def test_repo_map_source_serves_the_map_through_the_compiler(tmp_path):
    ws = _ws(tmp_path)
    ctx = CompileContext(workspace=Path(ws), query="build_engine")
    source = RepoMapSource()
    produced = source.collect(ctx)
    assert len(produced) == 1
    block = produced[0]
    assert block.name == "repo-map"
    assert "core.py:" in block.content
    assert block.provenance["files_mapped"] == 3
    assert block.provenance["files_seen"] == 3


def test_repo_map_source_yields_nothing_for_an_empty_workspace(tmp_path):
    source = RepoMapSource()
    ctx = CompileContext(workspace=Path(tmp_path), query="anything")
    assert source.collect(ctx) == []


def test_repo_map_source_compiles_inside_the_real_compiler(tmp_path):
    ws = _ws(tmp_path)
    compiler = ContextCompiler(ws, budget_tokens=10_000)
    compiler.add_source(RepoMapSource())
    compiled = compiler.compile("build_engine")
    names = [b.name for b in compiled.blocks]
    assert "repo-map" in names
