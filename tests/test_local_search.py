"""M-058 — Beyond-grep local search.

TIER: integration

One search surface, three modes, all in-process: text
mode is a ripgrep-class regex search over every text
file in a tiny throwaway project, fuzzy mode matches
subsequences with an auditable score, structural mode
delegates to the M-047 engine, and every result is
ranked by the M-046 symbol graph — a definition site
outranks a plain mention, and each match carries the
reasons its score rests on. Refused patterns stay
refused, skipped files say why, and a graph that
cannot be built leaves results honestly unranked.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mythic_agent.tools import local_search as ls
from mythic_agent.tools.local_search import (
    LOCAL_SEARCH_SLICE, MODES, enabled_from_config,
    format_local_search, fuzzy_score, parse_local_search_args,
    render_markdown, search,
)

CALC = (
    "def add(a, b):\n"
    "    return a + b\n"
    "\n"
    "def mul(a, b):\n"
    "    return a * b\n"
    "\n"
    "def add_twice(a, b):\n"
    "    return add(add(a, b), add(a, b))\n"
)
MAIN = "from calc import add\n\nprint(add(1, 2))\n"
NOTES = "remember to add tests later\n"


@pytest.fixture()
def project(tmp_path):
    (tmp_path / "calc.py").write_text(CALC, encoding="utf-8")
    (tmp_path / "main.py").write_text(MAIN, encoding="utf-8")
    (tmp_path / "notes.txt").write_text(NOTES, encoding="utf-8")
    (tmp_path / "blob.bin").write_bytes(b"\x00\x01add\x00")
    return tmp_path


# ---------------------------------------------------------------- basics

def test_slice_modes_and_config_switch():
    assert LOCAL_SEARCH_SLICE == "M-058"
    assert MODES == ("text", "fuzzy", "structural")
    assert enabled_from_config(None) is True
    assert enabled_from_config({}) is True
    assert enabled_from_config({"local_search": True}) is True
    assert enabled_from_config({"local_search": False}) is False


def test_disabled_search_reads_nothing(project):
    report = search(project, "add", enabled=False)
    assert report.status == "disabled"
    assert report.matches == []
    assert "off" in report.note


def test_empty_query_and_unknown_mode_refused(project):
    with pytest.raises(ValueError):
        search(project, "   ")
    with pytest.raises(ValueError):
        search(project, "add", mode="semantic")


# ---------------------------------------------------------------- text mode

def test_text_search_finds_matches_across_file_kinds(project):
    report = search(project, "add")
    found = {(m.path, m.line) for m in report.matches}
    assert ("calc.py", 1) in found
    assert ("main.py", 3) in found
    assert ("notes.txt", 1) in found
    assert report.files_searched == 3
    skipped = {s.path: s.reason for s in report.skipped}
    assert skipped["blob.bin"] == "binary file"


def test_text_search_is_a_regex(project):
    report = search(project, r"def (add|mul)\(")
    assert {(m.path, m.line) for m in report.matches} == {
        ("calc.py", 1), ("calc.py", 4)}


def test_invalid_regex_is_refused_not_literal_searched(project):
    with pytest.raises(ValueError) as excinfo:
        search(project, "([")
    assert "not a valid regular expression" in str(excinfo.value)
    assert "not searched as literal" in str(excinfo.value)


def test_no_matches_is_an_answer_not_an_error(project):
    report = search(project, "zzzqqq")
    assert report.matches == []
    assert "no matches" in report.note


def test_oversized_files_are_skipped_with_their_reason(project):
    report = search(project, "add", max_file_bytes=10)
    assert report.matches == []
    reasons = {s.path: s.reason for s in report.skipped}
    assert "too large" in reasons["calc.py"]
    assert "too large" in reasons["main.py"]
    assert "too large" in reasons["notes.txt"]
    assert reasons["blob.bin"] == "binary file"


def test_result_cap_truncates_and_says_so(project):
    report = search(project, "a", max_results=2)
    assert len(report.matches) == 2
    assert report.truncated is True
    assert any("result cap reached" in w for w in report.warnings)


# ---------------------------------------------------------------- ranking

def test_definition_site_outranks_a_plain_mention(project):
    report = search(project, "add")
    assert report.ranking == "symbol-graph"
    first = report.matches[0]
    assert (first.path, first.line) == ("calc.py", 1)
    assert any("defines add" in r for r in first.reasons)
    plain = [m for m in report.matches if m.path == "notes.txt"][0]
    assert first.score > plain.score


def test_naming_a_referenced_symbol_earns_its_reason(project):
    report = search(project, "add")
    call = [m for m in report.matches
            if (m.path, m.line) == ("calc.py", 8)][0]
    assert any(r.startswith("names add, referenced")
               for r in call.reasons)


def test_unbuildable_graph_leaves_results_unranked(project, monkeypatch):
    import mythic_agent.context.symbol_graph as graph_module

    def boom(*args, **kwargs):
        raise RuntimeError("no graph today")

    monkeypatch.setattr(graph_module, "build_symbol_graph", boom)
    report = search(project, "add")
    assert report.ranking == "unranked"
    assert report.matches  # the matches survive, honestly unranked
    assert any("could not be built" in w for w in report.warnings)
    assert all(m.score == 0 for m in report.matches)


# ---------------------------------------------------------------- fuzzy mode

def test_fuzzy_score_orders_strength():
    assert fuzzy_score("add", "add(a, b)") > fuzzy_score("add", "a d d")
    assert fuzzy_score("ab", "ab") > fuzzy_score("ab", "xab")
    assert fuzzy_score("xyz", "abc") is None
    assert fuzzy_score("", "abc") is None


def test_fuzzy_search_matches_subsequences(project):
    report = search(project, "adtw", mode="fuzzy")
    assert any((m.path, m.line) == ("calc.py", 7)
               for m in report.matches)
    assert all(any(r.startswith("fuzzy score")
                   for r in m.reasons) for m in report.matches)


def test_fuzzy_search_without_the_subsequence_finds_nothing(project):
    report = search(project, "qqq", mode="fuzzy")
    assert report.matches == []


# ---------------------------------------------------------------- structural

def test_structural_mode_delegates_to_the_m047_engine(project):
    report = search(project, "add($A, $B)", mode="structural",
                    language="python")
    assert report.mode == "structural"
    assert any(m.path == "main.py" for m in report.matches)
    call = [m for m in report.matches if m.path == "main.py"][0]
    assert {c["name"] for c in call.captures} == {"A", "B"}


def test_structural_mode_needs_a_language(project):
    with pytest.raises(ValueError):
        search(project, "add($A, $B)", mode="structural")


def test_structural_pattern_error_stays_refused(project):
    with pytest.raises(ValueError):
        search(project, "add($", mode="structural", language="python")


# ---------------------------------------------------------------- surfaces

def test_parse_args_all_modes():
    assert parse_local_search_args("hello world") == {
        "action": "search", "mode": "text", "query": "hello world",
        "language": None}
    assert parse_local_search_args("text a+b")["mode"] == "text"
    assert parse_local_search_args("fuzzy adtw") == {
        "action": "search", "mode": "fuzzy", "query": "adtw",
        "language": None}
    parsed = parse_local_search_args("structural python add($A, $B)")
    assert parsed["mode"] == "structural"
    assert parsed["language"] == "python"
    assert parsed["query"] == "add($A, $B)"


def test_parse_args_usage_errors():
    for bad in ("", "text", "fuzzy", "structural",
                "structural python"):
        with pytest.raises(ValueError):
            parse_local_search_args(bad)


def test_format_and_render_carry_scores_and_reasons(project):
    report = search(project, "add")
    status = {"report": report.record(),
              "plain_explanation": ls.PLAIN_EXPLANATION}
    text = format_local_search(status)
    assert "Local search (M-058, text)" in text
    assert "defines add" in text
    markdown = render_markdown(report)
    assert "# Local Search" in markdown
    assert "calc.py:1" in markdown


def test_agent_and_terminal_roads(project):
    from mythic_agent.agents.llm import Agent
    from mythic_agent.terminal import _slash

    agent = Agent.__new__(Agent)
    agent.project_root = project
    agent.config = {}
    status = agent.local_search("add")
    assert status["report"]["matches"]
    handled, _, text = _slash(agent, "/search add")
    assert handled and "Local search (M-058, text)" in text
    handled, _, text = _slash(agent, "/search fuzzy adtw")
    assert handled and "fuzzy" in text
    handled, _, text = _slash(agent, "/search structural python add($A, $B)")
    assert handled and "structural" in text
    handled, _, text = _slash(agent, "/search ([")
    assert handled and "not a valid regular expression" in text
    handled, _, text = _slash(agent, "/search")
    assert handled and "Usage" in text


def test_agent_respects_the_config_switch(project):
    from mythic_agent.agents.llm import Agent

    agent = Agent.__new__(Agent)
    agent.project_root = project
    agent.config = {"local_search": False}
    status = agent.local_search("add")
    assert status["report"]["status"] == "disabled"
    assert status["report"]["matches"] == []
