"""Tests for M-064 — Mojo as a first-class language.

TIER: integration

Mojo files recognised through the tree-sitter
foundation's catalogue, parsed via its grammar where
one truly loads — none exists in this environment,
measured, so the honestly named mojo-scan structural
backend serves — removed syntax flagged with its
replacement from the house Mojo skills, and those
skills' distilled knowledge searchable. Every test
runs on a throwaway workspace or a source string.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mythic_agent.tools import mojo_sight as ms
from mythic_agent.tools.mojo_sight import (
    KNOWLEDGE,
    MOJO_SLICE,
    PLAIN_EXPLANATION,
    REMOVED_SYNTAX,
    USAGE,
    format_mojo_report,
    grammar_status,
    is_mojo_path,
    mojo_sight,
    parse_mojo_args,
    render_markdown,
    scan_source,
    search_knowledge,
)

MODERN = '''
from std.collections import List
from std.python import Python

comptime N = 1024

@fieldwise_init
struct Point(Copyable, Movable):
    var x: Int
    var y: Int

trait Shape:
    pass

def area(p: Point) -> Int:
    var total = p.x * p.y
    return total

def main():
    print(area(Point(2, 3)))
'''

LEGACY = '''
alias MAX = 10

fn old_kernel():
    let x = 1

@value
struct Old:
    pass

@parameter if True:
    pass

def conv(inout self, owned other: Stringable):
    from collections import Dict
'''


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    (tmp_path / "modern.mojo").write_text(MODERN, encoding="utf-8")
    sub = tmp_path / "kernels"
    sub.mkdir()
    (sub / "legacy.mojo").write_text(LEGACY, encoding="utf-8")
    (tmp_path / "notes.txt").write_text("not mojo", encoding="utf-8")
    return tmp_path


# -- grammar honesty ---------------------------------------------------------

def test_grammar_status_matches_the_foundation_catalogue():
    status = grammar_status()
    assert status.language == "mojo"
    assert status.catalog_status == "no-grammar-package"
    # Measured in this environment: no Mojo grammar package
    # exists, so availability is honestly False.
    assert status.available is False
    assert "no grammar package" in status.detail


def test_scan_backend_is_never_dressed_as_tree_sitter():
    scan = scan_source(MODERN, "modern.mojo")
    assert scan.backend == "mojo-scan"


def test_is_mojo_path_uses_the_catalogue():
    assert is_mojo_path("kernels/device.mojo") is True
    assert is_mojo_path("kernels/device.py") is False
    assert is_mojo_path("README") is False


# -- the structural scan -----------------------------------------------------

def test_scan_reads_definitions_with_kinds_and_lines():
    scan = scan_source(MODERN, "modern.mojo")
    by_name = {d.name: d for d in scan.definitions}
    assert by_name["N"].kind == "constant"
    assert by_name["Point"].kind == "struct"
    assert by_name["Shape"].kind == "trait"
    assert by_name["area"].kind == "function"
    assert by_name["main"].kind == "function"
    assert by_name["area"].line > by_name["Point"].line


def test_scan_reads_imports_and_decorators():
    scan = scan_source(MODERN, "modern.mojo")
    assert "std.collections" in scan.imports
    assert "std.python" in scan.imports
    assert "fieldwise_init" in scan.decorators


def test_modern_source_has_no_removed_findings():
    scan = scan_source(MODERN, "modern.mojo")
    assert scan.findings == []


def test_scan_flags_removed_syntax_with_replacements():
    scan = scan_source(LEGACY, "legacy.mojo")
    rules = {f.rule for f in scan.findings}
    assert "alias-definition" in rules
    assert "fn-definition" in rules
    assert "let-binding" in rules
    assert "value-decorator" in rules
    assert "parameter-decorator" in rules
    assert "argument-convention" in rules
    assert "stringable" in rules
    assert "non-std-import" in rules
    for finding in scan.findings:
        assert finding.replacement
        assert finding.line >= 1
        assert finding.text


def test_removed_rules_cover_the_house_skill_table():
    names = {rule.rule for rule in REMOVED_SYNTAX}
    assert names == {
        "alias-definition", "let-binding", "parameter-decorator",
        "value-decorator", "register-passable-decorator",
        "argument-convention", "stringable", "non-std-import",
        "fn-definition",
    }


def test_register_passable_is_flagged():
    scan = scan_source('@register_passable("trivial")\nstruct T:\n    pass\n')
    assert [f.rule for f in scan.findings] == [
        "register-passable-decorator"]


# -- knowledge ---------------------------------------------------------------

def test_knowledge_entries_are_sequential_and_sourced():
    ids = [entry.entry_id for entry in KNOWLEDGE]
    assert ids == [f"K-{i:02d}" for i in range(1, len(KNOWLEDGE) + 1)]
    for entry in KNOWLEDGE:
        assert entry.source
        assert entry.body


def test_knowledge_search_finds_gpu_and_python_entries():
    gpu = search_knowledge("gpu")
    assert any("not CUDA" in entry.topic for entry in gpu)
    interop = search_knowledge("py=")
    assert any("Python from Mojo" in entry.topic for entry in interop)
    assert search_knowledge("") == KNOWLEDGE
    assert search_knowledge("no-such-topic-zzz") == ()


def test_knowledge_names_its_external_references():
    external = [e for e in KNOWLEDGE if e.entry_id == "K-09"]
    assert external and "Mojo Docs MCP" in external[0].body
    assert "outside" in external[0].body


# -- the report roads ----------------------------------------------------------

def test_show_scans_the_whole_workspace(project: Path):
    report = mojo_sight(project)
    assert report.status == "ok"
    assert report.kind == "show"
    paths = {f.path for f in report.files}
    assert paths == {"modern.mojo", "kernels/legacy.mojo"}
    n_files, n_defs, n_findings = report.totals()
    assert n_files == 2
    assert n_defs >= 7
    assert n_findings >= 8
    assert report.grammar is not None
    assert report.grammar.available is False


def test_show_on_a_mojo_less_workspace_says_so(tmp_path: Path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    report = mojo_sight(tmp_path)
    assert report.files == []
    assert "no Mojo files" in report.note


def test_file_road_scans_one_file(project: Path):
    report = mojo_sight(project, "file", target="kernels/legacy.mojo")
    assert len(report.files) == 1
    assert report.files[0].path == "kernels/legacy.mojo"
    assert report.files[0].findings


def test_file_road_refuses_a_non_mojo_file(project: Path):
    report = mojo_sight(project, "file", target="notes.txt")
    assert report.status == "error"
    assert "not a Mojo file" in report.note


def test_file_road_names_a_missing_file(project: Path):
    report = mojo_sight(project, "file", target="gone.mojo")
    assert report.status == "error"
    assert "no file at" in report.note


def test_knowledge_road(project: Path):
    report = mojo_sight(project, "knowledge", term="comptime")
    assert report.knowledge
    assert all(
        "comptime" in (e.topic + e.body).lower()
        for e in report.knowledge)
    empty = mojo_sight(project, "knowledge", term="zzz-no-match")
    assert empty.knowledge == []
    assert "no house-skill knowledge" in empty.note


def test_disabled_road_reads_nothing(project: Path):
    report = mojo_sight(project, enabled=False)
    assert report.status == "disabled"
    assert report.files == []
    assert "no project file was read" in report.note


def test_missing_workspace_is_an_honest_error(tmp_path: Path):
    report = mojo_sight(tmp_path / "nope")
    assert report.status == "error"
    assert "no workspace" in report.note


def test_unknown_mode_raises(project: Path):
    with pytest.raises(ValueError):
        mojo_sight(project, "sideways")


def test_scan_never_writes(project: Path):
    before = {p: p.read_bytes() for p in project.rglob("*") if p.is_file()}
    mojo_sight(project)
    mojo_sight(project, "file", target="modern.mojo")
    after = {p: p.read_bytes() for p in project.rglob("*") if p.is_file()}
    assert before == after


# -- surfaces ------------------------------------------------------------------

def test_parse_mojo_args_grammar():
    assert parse_mojo_args("") == {"action": "show"}
    assert parse_mojo_args("show") == {"action": "show"}
    assert parse_mojo_args("kernels/legacy.mojo") == {
        "action": "file", "target": "kernels/legacy.mojo"}
    assert parse_mojo_args("knowledge") == {
        "action": "knowledge", "term": ""}
    assert parse_mojo_args("knowledge gpu threads") == {
        "action": "knowledge", "term": "gpu threads"}
    with pytest.raises(ValueError):
        parse_mojo_args("show extra")
    with pytest.raises(ValueError):
        parse_mojo_args("a.mojo b.mojo")


def test_format_report_names_backend_and_findings(project: Path):
    report = mojo_sight(project)
    text = format_mojo_report({
        "report": report.record(),
        "plain_explanation": PLAIN_EXPLANATION})
    assert MOJO_SLICE in text
    assert "mojo-scan" in text
    assert "NOT PROVEN" in text
    assert "alias-definition" in text
    assert PLAIN_EXPLANATION in text


def test_format_knowledge_report(project: Path):
    report = mojo_sight(project, "knowledge", term="gpu")
    text = format_mojo_report({
        "report": report.record(),
        "plain_explanation": PLAIN_EXPLANATION})
    assert "K-07" in text
    assert "mojo-gpu-fundamentals" in text


def test_render_markdown_uses_the_reports_own_totals(project: Path):
    report = mojo_sight(project)
    page = render_markdown(report)
    n_files, n_defs, n_findings = report.totals()
    assert f"**{n_files} Mojo file(s)**" in page
    assert f"**{n_findings} removed-syntax" in page
    assert "Point" in page
    assert USAGE.split(":")[0] == "Usage"


def test_setting_lives_in_defaults_and_catalogue():
    import yaml

    root = Path(__file__).resolve().parents[1]
    defaults = yaml.safe_load(
        (root / "mythic_agent/data/config_defaults.yaml").read_text(
            encoding="utf-8"))
    assert defaults["mojo_sight"] is True
    catalogue = yaml.safe_load(
        (root / "mythic_agent/data/config_catalog.yaml").read_text(
            encoding="utf-8"))
    entries = [s for s in catalogue["settings"]
               if s["name"] == "mojo_sight"]
    assert len(entries) == 1
    assert entries[0]["id"] == "S-54"
    assert ms.enabled_from_config({}) is True
    assert ms.enabled_from_config({"mojo_sight": False}) is False
    assert ms.enabled_from_config(None) is True
