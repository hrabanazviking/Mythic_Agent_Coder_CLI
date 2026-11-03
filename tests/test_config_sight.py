"""Tests for M-066 — Config and infra sight.

TIER: integration

YAML, TOML, INI and systemd unit files, Dockerfiles
and compose files are parsed structurally — real
parsers per format (PyYAML, stdlib tomllib, a tolerant
unit parser that keeps repeated directives, a
Dockerfile line parser) — and reported as structure
only: kinds and sizes, never scalar values, nothing
executed. Docker artifacts in a workspace detected as
Volmarr's project (root marker files, or an explicit
ruling) raise the coder's own no-Docker-law warning;
without a marker the artifacts are listed and the
warning is honestly withheld. Every test builds a real
fixture tree on disk.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mythic_agent.tools import config_sight as cs
from mythic_agent.tools.config_sight import (
    CONFIG_SLICE,
    NO_DOCKER_WARNING,
    PLAIN_EXPLANATION,
    USAGE,
    classify_file,
    config_sight,
    detect_volmarr_project,
    find_config_files,
    format_config_report,
    is_docker_name,
    parse_config_args,
    parse_config_file,
    parse_dockerfile_text,
    parse_unit_text,
    render_markdown,
    summarise_mapping,
)


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    (tmp_path / "settings.yaml").write_text(
        "model: deepseek-chat\n"
        "limits:\n"
        "  retries: 3\n"
        "  tags: [a, b]\n"
        "names:\n"
        "  - one\n"
        "  - two\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        "name = \"demo\"\n"
        "version = \"1.0\"\n\n"
        "[tool.pytest]\n"
        "addopts = \"-q\"\n", encoding="utf-8")
    (tmp_path / "app.ini").write_text(
        "[server]\nhost = localhost\nport = 8080\n",
        encoding="utf-8")
    svc = tmp_path / "units"
    svc.mkdir()
    (svc / "demo.service").write_text(
        "[Unit]\nDescription=Demo\nAfter=network.target\n\n"
        "[Service]\nExecStart=/usr/bin/demo\nRestart=always\n"
        "Environment=A=1\nEnvironment=B=2\n\n"
        "[Install]\nWantedBy=multi-user.target\n",
        encoding="utf-8")
    (tmp_path / "notes.txt").write_text(
        "not config", encoding="utf-8")
    return tmp_path


@pytest.fixture()
def docker_project(tmp_path: Path) -> Path:
    (tmp_path / "Dockerfile").write_text(
        "FROM python:3.12 AS base\n"
        "WORKDIR /app\n"
        "COPY . /app\n"
        "RUN pip install \\\n"
        "    -r requirements.txt\n"
        "ENV MODE=prod DEBUG=0\n"
        "EXPOSE 8000 9000\n"
        "VOLUME [\"/data\"]\n\n"
        "FROM base AS final\n"
        "ENTRYPOINT [\"python\"]\n"
        "CMD [\"app.py\"]\n", encoding="utf-8")
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n"
        "  web:\n"
        "    image: demo-web\n"
        "    ports: [\"8000:8000\"]\n"
        "  db:\n"
        "    build: .\n", encoding="utf-8")
    return tmp_path


# -- recognition ---------------------------------------------------------------

def test_classify_by_format(tmp_path: Path):
    cases = {
        "a.yaml": "yaml", "a.yml": "yaml", "a.toml": "toml",
        "a.ini": "ini", "a.cfg": "ini",
        "a.service": "systemd", "a.timer": "systemd",
        "Dockerfile": "dockerfile", "Dockerfile.dev": "dockerfile",
        "app.dockerfile": "dockerfile",
        "docker-compose.yml": "docker-compose",
        "compose.yaml": "docker-compose",
        "a.txt": "", "a.py": "",
    }
    for name, expected in cases.items():
        assert classify_file(tmp_path / name) == expected, name
        assert is_docker_name(name) is (
            expected in ("dockerfile", "docker-compose")), name


def test_find_config_files_skips_vcs_and_venvs(project: Path):
    (project / ".git").mkdir()
    (project / ".git" / "config.toml").write_text(
        "x = 1\n", encoding="utf-8")
    found, warnings = find_config_files(project)
    names = {p.name for p, _ in found}
    assert names == {"settings.yaml", "pyproject.toml",
                     "app.ini", "demo.service"}
    assert warnings == []


# -- mapping structure -----------------------------------------------------------

def test_yaml_structure_kinds_sizes_depth(project: Path):
    info = parse_config_file(project / "settings.yaml",
                             "settings.yaml")
    assert info.note == "" and info.format == "yaml"
    by_name = {e.name: e for e in info.top_level}
    assert by_name["model"].kind == "scalar"
    assert by_name["limits"].kind == "mapping"
    assert by_name["limits"].size == 2
    assert by_name["names"].kind == "sequence"
    assert by_name["names"].size == 2
    assert info.total_keys == 5  # model, limits, retries, tags, names
    assert info.max_depth == 4  # root -> limits -> tags -> item


def test_toml_structure(project: Path):
    info = parse_config_file(project / "pyproject.toml")
    assert info.note == ""
    assert {e.name for e in info.top_level} == {"project", "tool"}
    assert info.top_names() == ("project", "tool")


def test_scalar_values_are_never_echoed(project: Path):
    report = config_sight(project)
    page = render_markdown(report)
    text = format_config_report(
        {"report": report.record(),
         "plain_explanation": PLAIN_EXPLANATION})
    for secretish in ("deepseek-chat", "localhost", "8080"):
        assert secretish not in page
        assert secretish not in text


def test_summarise_non_mapping_top_level():
    entries, total, depth = summarise_mapping([1, {"a": 1}])
    assert entries[0].name == "(top level)"
    assert entries[0].kind == "sequence"
    assert total == 1


def test_unparseable_yaml_is_named_not_dressed_empty(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("a: [unclosed\n", encoding="utf-8")
    info = parse_config_file(bad)
    assert "did not parse" in info.note
    assert info.top_level == []


def test_empty_yaml_is_named(tmp_path: Path):
    empty = tmp_path / "empty.yml"
    empty.write_text("", encoding="utf-8")
    assert parse_config_file(empty).note == "the file is empty"


# -- units -----------------------------------------------------------------------

def test_unit_parser_keeps_sections_and_repeats(project: Path):
    info = parse_config_file(project / "units" / "demo.service")
    assert info.format == "systemd"
    assert info.section_names() == ("Unit", "Service", "Install")
    service = info.sections[1]
    assert service.directive_names().count("Environment") == 2
    assert info.total_keys == 7  # 2 Unit + 4 Service + 1 Install


def test_unit_parser_comments_continuations_and_flags():
    sections = parse_unit_text(
        "# comment\n; another\n[Unit]\nDescription=one \\\n"
        "  two\nFlagLine\n")
    assert len(sections) == 1
    directives = dict()
    for name, value in sections[0].directives:
        directives.setdefault(name, value)
    assert directives["Description"] == "one two"
    assert directives["FlagLine"] == ""


# -- Dockerfile --------------------------------------------------------------------

def test_dockerfile_parser_stages_instructions_ports_env(docker_project: Path):
    info = parse_config_file(docker_project / "Dockerfile")
    assert info.docker is True
    docker = info.docker_info
    assert docker is not None
    assert docker.stages == ["base", "final"]
    assert docker.base_images == ["python:3.12", "base"]
    assert docker.instructions["RUN"] == 1  # continuation joined
    assert docker.instructions["COPY"] == 1
    assert docker.exposed_ports == ["8000", "9000"]
    assert docker.env_keys == ["MODE", "DEBUG"]
    assert docker.volumes == ["/data"]
    assert docker.has_entrypoint and docker.has_cmd
    assert docker.instruction_total() == sum(
        docker.instructions.values())


def test_dockerfile_parser_skips_comments_and_flags():
    info = parse_dockerfile_text(
        "# syntax=docker/dockerfile:1\n"
        "FROM --platform=linux/amd64 alpine:3\n")
    assert info.base_images == ["alpine:3"]
    assert info.stages == ["alpine:3"]


# -- compose -----------------------------------------------------------------------

def test_compose_services_are_docker_artifacts(docker_project: Path):
    info = parse_config_file(docker_project / "docker-compose.yml")
    assert info.format == "docker-compose" and info.docker is True
    assert info.services == ["web", "db"]


# -- the no-Docker law ----------------------------------------------------------------

def test_marker_detection_by_root_files(tmp_path: Path):
    assert detect_volmarr_project(tmp_path)[0] is False
    (tmp_path / "AGENTS.md").write_text("x", encoding="utf-8")
    found, evidence = detect_volmarr_project(tmp_path)
    assert found is True and "AGENTS.md" in evidence


def test_marker_detection_by_his_name(tmp_path: Path):
    (tmp_path / "Volmarr_Notes.md").write_text("x", encoding="utf-8")
    assert detect_volmarr_project(tmp_path)[0] is True


def test_override_wins_and_is_named(tmp_path: Path):
    found, evidence = detect_volmarr_project(tmp_path, True)
    assert found is True and "explicit" in evidence


def test_docker_warning_raised_on_volmarr_project(docker_project: Path):
    (docker_project / "AGENTS.md").write_text("x", encoding="utf-8")
    report = config_sight(docker_project)
    assert report.volmarr_project is True
    assert report.docker_warning is True
    assert any(NO_DOCKER_WARNING in w for w in report.warnings)
    assert set(report.docker_names()) == {
        "Dockerfile", "docker-compose.yml"}


def test_docker_warning_honestly_withheld_without_marker(
        docker_project: Path):
    report = config_sight(docker_project)
    assert report.docker_warning is False
    assert report.warnings == []
    assert "not raised" in report.note
    assert set(report.docker_names()) == {
        "Dockerfile", "docker-compose.yml"}


def test_docker_mode_lists_only_artifacts(docker_project: Path):
    (docker_project / "other.yaml").write_text(
        "a: 1\n", encoding="utf-8")
    report = config_sight(docker_project, "docker")
    assert {f.format for f in report.files} == {
        "dockerfile", "docker-compose"}


# -- the report roads ------------------------------------------------------------------

def test_show_report_counts_and_files(project: Path):
    report = config_sight(project)
    assert report.status == "ok"
    n_files, n_docker, n_clean = report.totals()
    assert n_files == 4 and n_docker == 0 and n_clean == 4
    assert "settings.yaml" in report.file_names()


def test_file_mode_and_errors(project: Path):
    report = config_sight(project, "file", target="pyproject.toml")
    assert [f.path for f in report.files] == ["pyproject.toml"]
    missing = config_sight(project, "file", target="nope.yaml")
    assert missing.status == "error" and "no file" in missing.note
    unknown = config_sight(project, "file", target="notes.txt")
    assert unknown.status == "error"
    assert "not a recognised" in unknown.note
    with pytest.raises(ValueError):
        config_sight(project, "file")
    with pytest.raises(ValueError):
        config_sight(project, "bogus-mode")


def test_disabled_reads_nothing(project: Path):
    report = config_sight(project, enabled=False)
    assert report.status == "disabled" and report.files == []


def test_missing_workspace_is_an_error(tmp_path: Path):
    report = config_sight(tmp_path / "nowhere")
    assert report.status == "error"


def test_parse_config_args():
    assert parse_config_args("") == {"action": "show"}
    assert parse_config_args("show") == {"action": "show"}
    assert parse_config_args("docker") == {"action": "docker"}
    assert parse_config_args("a.toml") == {
        "action": "file", "target": "a.toml"}
    with pytest.raises(ValueError):
        parse_config_args("a.toml b.toml")


def test_format_and_render_use_the_reports_own_values(docker_project: Path):
    (docker_project / "AGENTS.md").write_text("x", encoding="utf-8")
    report = config_sight(docker_project)
    text = format_config_report(
        {"report": report.record(),
         "plain_explanation": PLAIN_EXPLANATION})
    assert "Config sight (M-066)" in text
    assert "DOCKER ARTIFACT" in text
    assert "Warning:" in text and "NO-DOCKER LAW" in text
    page = render_markdown(report)
    n_files, n_docker, _ = report.totals()
    assert f"**{n_files} file(s)**" in page
    assert f"**{n_docker} Docker artifact(s)**" in page
    assert "warning raised: yes" in page
    assert CONFIG_SLICE == "M-066"
    assert USAGE.startswith("Usage")


# -- surfaces ---------------------------------------------------------------------------

def _bare_agent(root: Path, config=None):
    from mythic_agent.agents.llm import Agent

    agent = Agent.__new__(Agent)
    agent.project_root = root
    agent.config = config or {}
    agent._session_store = None
    agent.session_id = None
    return agent


def test_agent_surfaces(project: Path):
    agent = _bare_agent(project)
    status = agent.config_sight()
    assert status["report"]["status"] == "ok"
    assert len(status["report"]["files"]) == 4
    one = agent.config_sight("file", target="app.ini")
    assert one["report"]["files"][0]["format"] == "ini"


def test_agent_respects_the_config_switch(project: Path):
    agent = _bare_agent(project, {"config_sight": False})
    status = agent.config_sight()
    assert status["report"]["status"] == "disabled"
    assert status["report"]["files"] == []


def test_terminal_road(project: Path, docker_project: Path):
    from mythic_agent.terminal import _slash

    agent = _bare_agent(project)
    handled, _, text = _slash(agent, "/config")
    assert handled and "Config sight (M-066)" in text
    handled, _, text = _slash(agent, "/config pyproject.toml")
    assert handled and "project" in text
    handled, _, text = _slash(agent, "/config a.toml b.toml")
    assert handled and "Usage" in text
    docker_agent = _bare_agent(docker_project)
    handled, _, text = _slash(docker_agent, "/config docker")
    assert handled and "Dockerfile" in text


def test_setting_lives_in_defaults_and_catalogue():
    import yaml

    root = Path(__file__).resolve().parents[1]
    defaults = yaml.safe_load(
        (root / "mythic_agent/data/config_defaults.yaml").read_text(
            encoding="utf-8"))
    assert defaults["config_sight"] is True
    catalogue = yaml.safe_load(
        (root / "mythic_agent/data/config_catalog.yaml").read_text(
            encoding="utf-8"))
    entries = [s for s in catalogue["settings"]
               if s["name"] == "config_sight"]
    assert len(entries) == 1
    assert entries[0]["id"] == "S-56"
    assert cs.enabled_from_config({}) is True
    assert cs.enabled_from_config({"config_sight": False}) is False
    assert cs.enabled_from_config(None) is True


def test_config_catalogue_carries_the_setting():
    from mythic_agent.core.config_catalog import load_catalog

    catalog = load_catalog()
    entry = [s for s in catalog.settings
             if s.name == "config_sight"]
    assert len(entry) == 1
    assert entry[0].id == "S-56"


def test_gap_audit_has_no_m066_row_recorded():
    # Checked at build time (M-065's pattern): no census
    # gap row is owned by M-066, so no module_kind flip
    # exists to make for this slice.
    import yaml

    root = Path(__file__).resolve().parents[1]
    audit = yaml.safe_load(
        (root / "mythic_agent/data/gap_audit.yaml").read_text(
            encoding="utf-8"))
    assert [r for r in audit["rows"] if r["slice"] == "M-066"] == []
