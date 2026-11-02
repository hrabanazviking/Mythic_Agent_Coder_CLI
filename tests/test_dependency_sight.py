"""Tests for M-061 — Dependency sight.

TIER: integration

The declared graph from pyproject.toml with honest
installed truth, local-only changelog and vulnerability
data, and upgrade proposals that are data only — never
applied. Every test runs on a throwaway workspace; the
installed-version lookup is injected where a test needs
a known installed/uninstalled split, and the real
lookup's honesty is proven against a package name that
cannot be installed anywhere.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mythic_agent.tools import dependency_sight as ds
from mythic_agent.tools.dependency_sight import (
    DEPS_SLICE,
    PLAIN_EXPLANATION,
    USAGE,
    declared_dependencies,
    dependency_proposal,
    dependency_sight,
    find_changelog,
    find_vulnerabilities,
    format_deps_report,
    parse_deps_args,
    render_markdown,
    scan_imports,
)


def _lookup(table):
    return lambda name: table.get(name)


FAKE_VERSIONS = {"pyyaml": "6.0.3", "rich": "13.9.0",
                 "pytest": "8.3.0"}


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text(
        "[build-system]\n"
        'requires = ["hatchling"]\n'
        'build-backend = "hatchling.build"\n\n'
        "[project]\n"
        'name = "fixture"\n'
        'version = "0.1"\n'
        'dependencies = ["pyyaml>=6.0", "rich>=13.0"]\n\n'
        "[project.optional-dependencies]\n"
        'dev = ["pytest>=8"]\n'
        'pinned = ["rich<14"]\n',
        encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "import yaml\n\nimport rich\n\nprint(yaml, rich)\n",
        encoding="utf-8")
    (tmp_path / "other.py").write_text(
        "import os\n\nprint(os.name)\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## 1.0\n\n- rich: upgraded the "
        "terminal rendering.\n- pyyaml: nothing changed.\n",
        encoding="utf-8")
    return tmp_path


def test_slice_identity_and_config():
    assert DEPS_SLICE == "M-061"
    assert ds.enabled_from_config(None) is True
    assert ds.enabled_from_config({}) is True
    assert ds.enabled_from_config(
        {"dependency_sight": False}) is False
    assert "never" in PLAIN_EXPLANATION
    assert ds.normalize_name("PyYAML") == "pyyaml"
    assert ds.normalize_name("some_pkg.name") == "some-pkg-name"


def test_graph_building_from_fixture_pyproject(project):
    nodes, warnings = declared_dependencies(
        project, version_lookup=_lookup(FAKE_VERSIONS))
    assert warnings == []
    by_name = {n.name: n for n in nodes}
    assert set(by_name) == {"hatchling", "pyyaml", "rich", "pytest"}
    assert by_name["rich"].groups == ("core", "pinned")
    assert set(by_name["rich"].specs) == {">=13.0", "<14"}
    assert by_name["pyyaml"].groups == ("core",)
    assert by_name["pyyaml"].specs == (">=6.0",)
    assert by_name["hatchling"].groups == ("build-system",)
    # census enrichment rides along, never duplicated data
    assert by_name["pyyaml"].import_names == ("yaml",)
    assert by_name["pyyaml"].licence


def test_installed_vs_uninstalled_honesty(project):
    nodes, _ = declared_dependencies(
        project, version_lookup=_lookup(FAKE_VERSIONS))
    by_name = {n.name: n for n in nodes}
    assert by_name["pyyaml"].installed_version == "6.0.3"
    assert by_name["hatchling"].installed_version is None
    # the real lookup never guesses a version for a
    # package that cannot be installed anywhere
    assert ds.installed_version_for(
        "definitely-not-a-real-package-zzqxv") is None
    report = dependency_sight(
        project, version_lookup=_lookup(FAKE_VERSIONS))
    text = format_deps_report(
        {"report": report.record(),
         "plain_explanation": PLAIN_EXPLANATION})
    assert "not installed (version unknown)" in text


def test_missing_pyproject_is_an_honest_error(tmp_path):
    report = dependency_sight(tmp_path)
    assert report.status == "error"
    assert report.nodes == []
    assert "pyproject.toml" in report.note \
        or any("pyproject.toml" in w for w in report.warnings)


def test_changelog_local_hit_and_honest_absence(project):
    found = find_changelog(project, "rich")
    assert found["status"] == "found"
    assert found["files"] == ["CHANGELOG.md"]
    assert any("rich" in hit.text for hit in found["hits"])
    missing = find_changelog(project, "pytest")
    assert missing["status"] == "no-local-data"
    assert "none mentions pytest" in missing["note"]


def test_changelog_no_files_at_all(tmp_path):
    result = find_changelog(tmp_path, "rich")
    assert result["status"] == "no-local-data"
    assert "no local changelog data" in result["note"]
    assert "nothing was fetched" in result["note"]


def test_vulnerability_no_local_data_honesty(project):
    result = find_vulnerabilities(project, "rich")
    assert result["status"] == "no-local-data"
    assert result["sources"] == []
    assert "NOT PROVEN" in result["note"]
    assert "not a claim" in result["note"]
    report = dependency_sight(
        project, "rich", version_lookup=_lookup(FAKE_VERSIONS))
    assert report.vuln_status == "no-local-data"
    assert "NOT PROVEN" in report.note


def test_vulnerability_local_source_mentions(project):
    (project / "security-advisories.md").write_text(
        "# Advisories\n\n- rich <13.5 had a colour "
        "parsing flaw.\n", encoding="utf-8")
    result = find_vulnerabilities(project, "rich")
    assert result["status"] == "local-data"
    assert result["sources"] == ["security-advisories.md"]
    assert result["hits"]
    silent = find_vulnerabilities(project, "pytest")
    assert silent["status"] == "local-data"
    assert silent["hits"] == []
    assert "not a clean bill" in silent["note"]


def test_scan_imports_shape(project):
    imports, warnings = scan_imports(project)
    assert imports["app.py"] == {"yaml", "rich"}
    assert imports["other.py"] == {"os"}


def test_package_view_counts_blast_radius(project):
    report = dependency_sight(
        project, "pyyaml", version_lookup=_lookup(FAKE_VERSIONS))
    assert report.status == "ok"
    assert report.node.name == "pyyaml"
    assert report.blast_radius.files == ("app.py",)
    assert report.blast_radius.file_count == 1
    assert report.changelog_status == "found"


def test_undeclared_package_is_refused_plainly(project):
    report = dependency_sight(
        project, "requests",
        version_lookup=_lookup(FAKE_VERSIONS))
    assert report.status == "error"
    assert "not declared" in report.note
    proposal = dependency_proposal(
        project, "requests", "9.9",
        version_lookup=_lookup(FAKE_VERSIONS))
    assert proposal.status == "error"
    assert proposal.proposal is None
    assert "no proposal is drafted" in proposal.note


def test_proposal_blast_radius_and_pins(project):
    report = dependency_proposal(
        project, "rich", "14.0",
        version_lookup=_lookup(FAKE_VERSIONS))
    assert report.status == "ok"
    proposal = report.proposal
    assert proposal.package == "rich"
    assert proposal.target_version == "14.0"
    assert proposal.installed_version == "13.9.0"
    assert set(proposal.current_specs) == {">=13.0", "<14"}
    assert proposal.groups == ("core", "pinned")
    assert proposal.blast_radius.files == ("app.py",)
    assert proposal.pinned_elsewhere is True
    assert "every" in proposal.pin_note
    assert proposal.applied is False


def test_proposal_never_applies_and_changes_nothing(project):
    before = {p.name: p.read_bytes()
              for p in project.iterdir() if p.is_file()}
    report = dependency_proposal(
        project, "pyyaml", "7.0",
        version_lookup=_lookup(FAKE_VERSIONS))
    assert report.proposal.applied is False
    assert "nothing was applied" in report.note
    after = {p.name: p.read_bytes()
             for p in project.iterdir() if p.is_file()}
    assert before == after
    # the module has no apply/write road at all
    assert not hasattr(ds, "apply_proposal")
    assert not hasattr(ds, "apply_upgrade")


def test_proposal_usage_errors_raise(project):
    with pytest.raises(ValueError):
        dependency_proposal(project, "", "1.0")
    with pytest.raises(ValueError):
        dependency_proposal(project, "rich", "  ")


def test_disabled_road_reads_nothing(project):
    report = dependency_sight(project, enabled=False)
    assert report.status == "disabled"
    assert report.nodes == []
    proposal = dependency_proposal(
        project, "rich", "14.0", enabled=False)
    assert proposal.status == "disabled"
    assert proposal.proposal is None


def test_parse_args_roads_and_usage_errors():
    assert parse_deps_args("") == {"action": "show"}
    assert parse_deps_args("show") == {"action": "show"}
    assert parse_deps_args("rich") == {
        "action": "package", "package": "rich"}
    assert parse_deps_args("propose rich 14.0") == {
        "action": "propose", "package": "rich",
        "version": "14.0"}
    for bad in ("show extra", "propose rich",
                "propose rich 1.0 extra", "two words"):
        with pytest.raises(ValueError) as excinfo:
            parse_deps_args(bad)
        assert "Usage" in str(excinfo.value)
    assert USAGE.startswith("Usage: /deps")


def test_format_and_render(project):
    report = dependency_sight(
        project, version_lookup=_lookup(FAKE_VERSIONS))
    text = format_deps_report(
        {"report": report.record(),
         "plain_explanation": PLAIN_EXPLANATION})
    assert "Dependency sight (M-061)" in text
    assert "pyyaml" in text
    md = render_markdown(report)
    assert "Dependency Sight" in md and "pyyaml" in md
    proposal = dependency_proposal(
        project, "rich", "14.0",
        version_lookup=_lookup(FAKE_VERSIONS))
    text = format_deps_report(
        {"report": proposal.record(),
         "plain_explanation": PLAIN_EXPLANATION})
    assert "Upgrade proposal (M-061)" in text
    assert "NOT applied" in text
    md = render_markdown(proposal)
    assert "never applied" in md


def _bare_agent(root: Path, config=None):
    from mythic_agent.agents.llm import Agent

    agent = Agent.__new__(Agent)
    agent.project_root = root
    agent.config = config or {}
    agent._session_store = None
    agent.session_id = None
    return agent


def test_agent_surfaces(project, monkeypatch):
    import mythic_agent.tools.dependency_sight as module

    monkeypatch.setattr(
        module, "installed_version_for",
        _lookup(FAKE_VERSIONS))
    agent = _bare_agent(project)
    status = agent.dependency_sight()
    names = [n["name"] for n in status["report"]["nodes"]]
    assert "pyyaml" in names and "rich" in names
    status = agent.dependency_sight("pyyaml")
    assert status["report"]["blast_radius"]["file_count"] == 1
    status = agent.dependency_proposal("rich", "14.0")
    assert status["report"]["proposal"]["applied"] is False


def test_agent_respects_the_config_switch(project):
    agent = _bare_agent(project, {"dependency_sight": False})
    status = agent.dependency_sight()
    assert status["report"]["status"] == "disabled"
    assert status["report"]["nodes"] == []


def test_terminal_road(project, monkeypatch):
    from mythic_agent.terminal import _slash
    import mythic_agent.tools.dependency_sight as module

    monkeypatch.setattr(
        module, "installed_version_for",
        _lookup(FAKE_VERSIONS))
    agent = _bare_agent(project)
    handled, _, text = _slash(agent, "/deps")
    assert handled and "Dependency sight (M-061)" in text
    handled, _, text = _slash(agent, "/deps show")
    assert handled and "pyyaml" in text
    handled, _, text = _slash(agent, "/deps pyyaml")
    assert handled and "Blast radius" in text
    handled, _, text = _slash(agent, "/deps propose rich 14.0")
    assert handled and "Upgrade proposal (M-061)" in text
    assert "NOT applied" in text
    handled, _, text = _slash(agent, "/deps propose rich")
    assert handled and "Usage" in text


def test_config_catalogue_carries_the_setting():
    from mythic_agent.core.config_catalog import load_catalog

    catalog = load_catalog()
    names = {s.name for s in catalog.settings}
    assert "dependency_sight" in names
    entry = [s for s in catalog.settings
             if s.name == "dependency_sight"][0]
    assert entry.id == "S-51"
