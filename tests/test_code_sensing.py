"""Tests for M-062 — Dead-code and duplication sensing.

TIER: integration

Dead code from the shipped scanner over a fixture
package, duplication as exact structural AST
fingerprints (renamed and re-literal'd copies cluster;
textual coincidence and trivial shapes do not), and a
report that is sensing only — it deletes and edits
nothing. Every test runs on a throwaway workspace.
"""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path

import pytest

from mythic_agent.tools import code_sensing as cs
from mythic_agent.tools.code_sensing import (
    MIN_CLUSTER_NODES,
    PLAIN_EXPLANATION,
    SENSING_SLICE,
    USAGE,
    code_sensing,
    find_duplications,
    format_sensing_report,
    parse_sensing_args,
    render_markdown,
    scan_dead_code,
    structural_fingerprint,
)

ALPHA = '''
def alpha_report(entries):
    total = 0
    count = 0
    for entry in entries:
        if entry > 10:
            total = total + entry * 2
            count = count + 1
        else:
            total = total - 1
    average = total / count if count else 0
    return {"total": total, "count": count, "average": average}
'''

BETA = '''
def beta_summary(rows):
    acc = 0
    seen = 0
    for row in rows:
        if row > 99:
            acc = acc + row * 7
            seen = seen + 1
        else:
            acc = acc - 5
    mean = acc / seen if seen else 0
    return {"sum": acc, "n": seen, "mean": mean}
'''


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "mod_a.py").write_text(
        "def used_helper():\n"
        "    return 1\n"
        "\n"
        "def dead_helper():\n"
        "    return 2\n"
        "\n"
        "def tiny_one():\n"
        "    return 1\n"
        + ALPHA
        + "\nprint(used_helper())\n",
        encoding="utf-8")
    (pkg / "mod_b.py").write_text(
        "def tiny_two():\n"
        "    return 2\n"
        + BETA
        + '''
def gamma_scan(rows):
    acc = 0
    seen = 0
    while rows:
        row = rows.pop()
        acc = acc + row
        seen = seen + 1
    return {"sum": acc, "n": seen}
''',
        encoding="utf-8")
    return tmp_path


def _func(source: str) -> ast.FunctionDef:
    return ast.parse(textwrap.dedent(source)).body[0]


def test_slice_identity_and_config():
    assert SENSING_SLICE == "M-062"
    assert MIN_CLUSTER_NODES >= 10
    assert cs.enabled_from_config(None) is True
    assert cs.enabled_from_config({}) is True
    assert cs.enabled_from_config({"code_sensing": False}) is False
    assert "never deletes" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /sensing")


def test_fingerprint_ignores_names_and_literals():
    fp_a, count_a = structural_fingerprint(_func(ALPHA))
    fp_b, count_b = structural_fingerprint(_func(BETA))
    assert fp_a == fp_b
    assert count_a == count_b >= MIN_CLUSTER_NODES


def test_fingerprint_keeps_structure_and_input():
    node = _func(ALPHA)
    before = ast.dump(node)
    fp_a, _ = structural_fingerprint(node)
    assert ast.dump(node) == before  # the input is never mutated
    other = _func('''
def other(rows):
    acc = 0
    seen = 0
    while rows:
        row = rows.pop()
        acc = acc + row
        seen = seen + 1
    return {"sum": acc, "n": seen}
''')
    fp_other, _ = structural_fingerprint(other)
    assert fp_other != fp_a


def test_duplication_cluster_finds_renamed_copy(project):
    clusters, scanned, warnings = find_duplications(project)
    assert scanned == 3
    assert len(clusters) == 1
    cluster = clusters[0]
    names = {m.name for m in cluster.members}
    assert names == {"alpha_report", "beta_summary"}
    assert cluster.nodes >= MIN_CLUSTER_NODES
    assert cluster.total_nodes == cluster.nodes * 2
    paths = {m.path for m in cluster.members}
    assert paths == {"pkg/mod_a.py", "pkg/mod_b.py"}


def test_trivial_shapes_and_textual_coincidence_never_cluster(project):
    clusters, _, _ = find_duplications(project)
    member_names = {m.name for c in clusters for m in c.members}
    # identical one-line shapes are below the size floor
    assert "tiny_one" not in member_names
    assert "tiny_two" not in member_names
    # gamma_scan shares vocabulary with the cluster but
    # its structure differs — no cluster claims it
    assert "gamma_scan" not in member_names


def test_dead_code_from_the_shipped_scanner(project):
    items, packages, warnings, recorded, unrecorded = \
        scan_dead_code(project)
    assert packages == ["pkg"]
    names = {i.name for i in items}
    assert "dead_helper" in names
    assert "used_helper" not in names
    dead = [i for i in items if i.name == "dead_helper"][0]
    assert dead.path == "pkg/mod_a.py"
    assert dead.kind == "function"
    assert dead.line >= 1


def test_quarantine_state_is_named(project):
    docs = project / "docs"
    docs.mkdir()
    (docs / "DEAD_CODE_QUARANTINE.txt").write_text(
        "# Dead-code quarantine inventory\n"
        "# format: path:lineno:name:kind\n"
        "pkg/mod_a.py:4:dead_helper:function\n",
        encoding="utf-8")
    items, _, _, recorded, unrecorded = scan_dead_code(project)
    assert recorded >= 1
    assert recorded + unrecorded == len(items)


def test_no_package_workspace_is_honest(tmp_path):
    (tmp_path / "loose.py").write_text(
        "print('hello')\n", encoding="utf-8")
    report = code_sensing(tmp_path, "dead")
    assert report.status == "ok"
    assert report.dead_items == []
    assert report.packages_scanned == []
    assert any("no Python package" in w for w in report.warnings)
    assert any("not a claim" in w for w in report.warnings)


def test_show_report_combines_both_halves(project):
    report = code_sensing(project)
    assert report.status == "ok"
    assert report.kind == "show"
    n_dead, n_clusters, n_files = report.counts()
    assert n_dead == len(report.dead_items) > 0
    assert n_clusters == 1
    assert n_files == 3
    assert "dead_helper" in report.dead_names()
    assert "sensing only" in report.note
    assert "nothing was deleted" in report.note


def test_dead_and_dup_modes_are_separate(project):
    dead = code_sensing(project, "dead")
    assert dead.dead_items and dead.clusters == []
    dup = code_sensing(project, "dup")
    assert dup.clusters and dup.dead_items == []
    with pytest.raises(ValueError):
        code_sensing(project, "bogus")


def test_sensing_never_writes_or_deletes(project):
    before = {p.relative_to(project).as_posix(): p.read_bytes()
              for p in project.rglob("*") if p.is_file()}
    report = code_sensing(project)
    assert report.status == "ok"
    after = {p.relative_to(project).as_posix(): p.read_bytes()
             for p in project.rglob("*") if p.is_file()}
    assert before == after
    # the module has no delete/edit/apply road at all
    for forbidden in ("delete_dead_code", "remove_duplicates",
                      "apply_sensing", "delete_item"):
        assert not hasattr(cs, forbidden)


def test_disabled_road_reads_nothing(project):
    report = code_sensing(project, enabled=False)
    assert report.status == "disabled"
    assert report.dead_items == [] and report.clusters == []


def test_missing_workspace_is_an_honest_error(tmp_path):
    report = code_sensing(tmp_path / "nope")
    assert report.status == "error"
    assert "no workspace" in report.note


def test_parse_args_roads_and_usage_errors():
    assert parse_sensing_args("") == {"action": "show"}
    assert parse_sensing_args("show") == {"action": "show"}
    assert parse_sensing_args("dead") == {"action": "dead"}
    assert parse_sensing_args("dup") == {"action": "dup"}
    assert parse_sensing_args("duplicates") == {"action": "dup"}
    for bad in ("bogus", "dead dup"):
        with pytest.raises(ValueError) as excinfo:
            parse_sensing_args(bad)
        assert "Usage" in str(excinfo.value)


def test_format_and_render(project):
    report = code_sensing(project)
    text = format_sensing_report(
        {"report": report.record(),
         "plain_explanation": PLAIN_EXPLANATION})
    assert "Code sensing (M-062)" in text
    assert "dead_helper" in text
    assert "alpha_report" in text
    md = render_markdown(report)
    assert "Code Sensing" in md and "dead_helper" in md
    assert "beta_summary" in md


def _bare_agent(root: Path, config=None):
    from mythic_agent.agents.llm import Agent

    agent = Agent.__new__(Agent)
    agent.project_root = root
    agent.config = config or {}
    agent._session_store = None
    agent.session_id = None
    return agent


def test_agent_surfaces(project):
    agent = _bare_agent(project)
    status = agent.code_sensing()
    assert status["report"]["status"] == "ok"
    assert status["report"]["clusters"]
    status = agent.code_sensing("dead")
    assert status["report"]["clusters"] == []


def test_agent_respects_the_config_switch(project):
    agent = _bare_agent(project, {"code_sensing": False})
    status = agent.code_sensing()
    assert status["report"]["status"] == "disabled"
    assert status["report"]["dead_items"] == []


def test_terminal_road(project):
    from mythic_agent.terminal import _slash

    agent = _bare_agent(project)
    handled, _, text = _slash(agent, "/sensing")
    assert handled and "Code sensing (M-062)" in text
    handled, _, text = _slash(agent, "/sensing dead")
    assert handled and "dead_helper" in text
    handled, _, text = _slash(agent, "/sensing dup")
    assert handled and "Duplication" in text
    handled, _, text = _slash(agent, "/sensing bogus")
    assert handled and "Usage" in text


def test_config_catalogue_carries_the_setting():
    from mythic_agent.core.config_catalog import load_catalog

    catalog = load_catalog()
    names = {s.name for s in catalog.settings}
    assert "code_sensing" in names
    entry = [s for s in catalog.settings
             if s.name == "code_sensing"][0]
    assert entry.id == "S-52"
