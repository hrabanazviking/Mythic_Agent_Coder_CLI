"""Tests for M-060 — Docs-at-hand.

The offline shelf: the project's own docs plus doc
packs under ``.mythic/docpacks/``, discovered,
searched in-process with ranked, reasoned hits, and
read whole by name. Every test runs on a throwaway
workspace; no network exists in the module to mock.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mythic_agent.tools import docs_at_hand as dh
from mythic_agent.tools.docs_at_hand import (
    DOCS_SLICE,
    PLAIN_EXPLANATION,
    USAGE,
    discover_docs,
    docs_list,
    docs_read,
    docs_search,
    format_docs_report,
    parse_docs_args,
    render_markdown,
)


@pytest.fixture()
def shelf(tmp_path: Path) -> Path:
    (tmp_path / "GUIDE.md").write_text(
        "# The Forge Guide\n\nHow to temper a blade.\n"
        "Tempering takes patience.\n", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "tempering.md").write_text(
        "# Tempering Steel\n\n## Heat\n\nHeat the steel, "
        "then quench it.\nTempering again.\n", encoding="utf-8")
    (docs / "gardening.txt").write_text(
        "Gardening Notes\n\nPlant the tempering herbs "
        "in spring.\n", encoding="utf-8")
    (docs / "code.py").write_text(
        "# not a doc\n", encoding="utf-8")
    pack = tmp_path / ".mythic" / "docpacks" / "mojo"
    pack.mkdir(parents=True)
    (pack / "gpu.md").write_text(
        "# Mojo GPU Guide\n\nKernels and tempering "
        "on the GPU.\n", encoding="utf-8")
    return tmp_path


def test_slice_identity_and_config():
    assert DOCS_SLICE == "M-060"
    assert dh.enabled_from_config(None) is True
    assert dh.enabled_from_config({}) is True
    assert dh.enabled_from_config({"docs_at_hand": False}) is False
    assert "offline" in PLAIN_EXPLANATION


def test_discovery_catalogues_project_and_pack_docs(shelf):
    entries = discover_docs(shelf)
    by_path = {e.path: e for e in entries}
    assert set(by_path) == {
        "GUIDE.md", "docs/tempering.md", "docs/gardening.txt",
        ".mythic/docpacks/mojo/gpu.md"}
    assert by_path["docs/tempering.md"].title == "Tempering Steel"
    assert by_path["docs/tempering.md"].source == "project"
    assert by_path[".mythic/docpacks/mojo/gpu.md"].source == "mojo"
    assert by_path["docs/gardening.txt"].title == "Gardening Notes"


def test_list_report_and_empty_shelf(tmp_path):
    report = docs_list(tmp_path)
    assert report.status == "ok"
    assert report.docs == []
    assert "empty" in report.note
    report = docs_list(tmp_path, enabled=False)
    assert report.status == "disabled"
    assert report.docs == []


def test_search_ranks_title_above_body(shelf):
    report = docs_search(shelf, "tempering steel")
    assert report.status == "ok"
    assert report.hits
    top = report.hits[0]
    assert top.entry.path == "docs/tempering.md"
    assert any("title" in reason for reason in top.reasons)
    assert top.line >= 1 and top.snippet


def test_search_finds_pack_docs(shelf):
    report = docs_search(shelf, "gpu kernels")
    paths = [h.entry.path for h in report.hits]
    assert ".mythic/docpacks/mojo/gpu.md" in paths
    hit = report.hits[paths.index(".mythic/docpacks/mojo/gpu.md")]
    assert hit.entry.source == "mojo"


def test_search_no_match_is_an_answer_not_an_error(shelf):
    report = docs_search(shelf, "zzqxv nothing")
    assert report.status == "ok"
    assert report.hits == []
    assert "no doc on the shelf" in report.note


def test_search_cap_names_itself(shelf):
    report = docs_search(shelf, "tempering", max_hits=1)
    assert len(report.hits) == 1
    assert report.truncated is True
    assert any("hit cap" in w for w in report.warnings)


def test_usage_errors_raise(shelf):
    with pytest.raises(ValueError):
        docs_search(shelf, "   ")
    with pytest.raises(ValueError):
        docs_read(shelf, "")
    with pytest.raises(ValueError):
        docs_search(shelf, "x", max_hits=0)


def test_disabled_road_reads_nothing(shelf):
    for report in (docs_search(shelf, "tempering", enabled=False),
                   docs_read(shelf, "GUIDE.md", enabled=False)):
        assert report.status == "disabled"
        assert report.hits == [] and report.text == ""


def test_read_by_path_name_and_title(shelf):
    by_path = docs_read(shelf, "docs/tempering.md")
    assert by_path.status == "ok"
    assert "quench" in by_path.text
    by_name = docs_read(shelf, "tempering.md")
    assert by_name.doc.path == "docs/tempering.md"
    by_title = docs_read(shelf, "The Forge Guide")
    assert by_title.doc.path == "GUIDE.md"


def test_read_missing_doc_is_an_honest_error(shelf):
    report = docs_read(shelf, "nonexistent.md")
    assert report.status == "error"
    assert report.text == ""
    assert "no doc on the shelf" in report.note


def test_read_ambiguous_name_is_refused_with_candidates(shelf):
    (shelf / "docs" / "guide-copy.md").write_text(
        "# The Forge Guide\n\nA second copy.\n", encoding="utf-8")
    report = docs_read(shelf, "The Forge Guide")
    assert report.status == "error"
    assert "names 2 docs" in report.note
    assert "guide-copy.md" in report.note


def test_read_char_cap_names_itself(shelf):
    report = docs_read(shelf, "GUIDE.md", max_chars=10)
    assert len(report.text) == 10
    assert report.truncated is True
    assert any("text cap" in w for w in report.warnings)


def test_oversized_doc_is_catalogued_not_indexed(shelf, monkeypatch):
    monkeypatch.setattr(dh, "MAX_DOC_BYTES", 10)
    entries = discover_docs(shelf)
    assert entries and all(not e.indexed for e in entries)
    report = docs_read(shelf, "GUIDE.md")
    assert report.status == "error"
    assert "catalogued, not read" in report.note
    report = docs_search(shelf, "tempering")
    assert report.hits == []


def test_parse_args_roads_and_usage_errors():
    assert parse_docs_args("list") == {"action": "list"}
    assert parse_docs_args("search heat treat") == {
        "action": "search", "query": "heat treat"}
    assert parse_docs_args("read The Forge Guide") == {
        "action": "read", "name": "The Forge Guide"}
    for bad in ("", "search", "read", "list extra", "bogus x"):
        with pytest.raises(ValueError) as excinfo:
            parse_docs_args(bad)
        assert "Usage" in str(excinfo.value)
    assert USAGE.startswith("Usage: /docs")


def test_format_and_render(shelf):
    listing = docs_list(shelf)
    text = format_docs_report(
        {"report": listing.record(),
         "plain_explanation": PLAIN_EXPLANATION})
    assert "Docs-at-hand (M-060)" in text
    assert "tempering.md" in text
    md = render_markdown(listing)
    assert "Docs-at-Hand" in md and "Tempering Steel" in md
    found = docs_search(shelf, "tempering steel")
    text = format_docs_report(
        {"report": found.record(),
         "plain_explanation": PLAIN_EXPLANATION})
    assert "Docs search (M-060)" in text
    read = docs_read(shelf, "GUIDE.md")
    md = render_markdown(read)
    assert "temper a blade" in md


def _bare_agent(root: Path, config=None):
    from mythic_agent.agents.llm import Agent

    agent = Agent.__new__(Agent)
    agent.project_root = root
    agent.config = config or {}
    agent._session_store = None
    agent.session_id = None
    return agent


def test_agent_surfaces(shelf):
    agent = _bare_agent(shelf)
    status = agent.docs_list()
    assert len(status["report"]["docs"]) == 4
    status = agent.docs_search("gpu")
    assert status["report"]["hits"]
    status = agent.docs_read("gpu.md")
    assert "Kernels" in status["report"]["text"]


def test_agent_respects_the_config_switch(shelf):
    agent = _bare_agent(shelf, {"docs_at_hand": False})
    status = agent.docs_list()
    assert status["report"]["status"] == "disabled"
    assert status["report"]["docs"] == []


def test_terminal_road(shelf):
    from mythic_agent.terminal import _slash

    agent = _bare_agent(shelf)
    handled, _, text = _slash(agent, "/docs list")
    assert handled and "Docs-at-hand (M-060)" in text
    handled, _, text = _slash(agent, "/docs search tempering")
    assert handled and "Docs search (M-060)" in text
    handled, _, text = _slash(agent, "/docs read GUIDE.md")
    assert handled and "temper a blade" in text
    handled, _, text = _slash(agent, "/docs")
    assert handled and "Usage" in text


def test_config_catalogue_carries_the_setting():
    from mythic_agent.core.config_catalog import load_catalog

    catalog = load_catalog()
    names = {s.name for s in catalog.settings}
    assert "docs_at_hand" in names
