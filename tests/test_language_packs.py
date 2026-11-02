"""Tests for M-068 — Language packs as data.

TIER: unit

Per-language toolchains (server commands, formatters, test
runners) are declared in data
(``mythic_agent/data/language_packs.yaml``) — a new language
is a pack, not a patch. One pack per language in the M-043
tree-sitter catalogue, cross-checked against the live
consumers: the LSP server catalogue (names and commands,
with the typescript server serving both TypeScript and
JavaScript), the format covenant's live candidate names
(the Python pack's formatters), and test intelligence's
pytest detection (the Python pack's runner). The surface
(``/langpacks``) describes the declared toolchains and
PATH-checks their binaries; nothing is ever executed.
"""

from __future__ import annotations

import copy
import shutil
from pathlib import Path

import pytest

from mythic_agent.core import language_packs as core
from mythic_agent.core.language_packs import (
    PACKS_SLICE,
    LanguagePacks,
    formatter_names,
    languages,
    load_language_packs,
    pack_for_extension,
    pack_for_language,
    packs,
    render_markdown,
    server_command,
    validate_language_packs,
)

from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource
from mythic_agent.tools import language_packs as surface
from mythic_agent.tools.language_packs import (
    PLAIN_EXPLANATION,
    USAGE,
    format_language_pack_report,
    language_packs_report,
    parse_langpacks_args,
)


@pytest.fixture(scope="module")
def catalog() -> LanguagePacks:
    return load_language_packs()


def _mutated(mutator):
    data = copy.deepcopy(load_resource("language_packs.yaml"))
    mutator(data)
    return data


# -- the shipped packs ---------------------------------------------------

def test_packs_load_six_sequential_in_catalogue_order(catalog):
    from mythic_agent.core.tree_sitter_foundation import load_catalog

    ts_catalog = load_catalog()
    assert isinstance(catalog, LanguagePacks)
    assert validate_language_packs(
        load_resource("language_packs.yaml")) == []
    assert [p.id for p in catalog.entries] == [
        "LP-01", "LP-02", "LP-03", "LP-04", "LP-05", "LP-06"]
    assert list(catalog.languages()) == [
        entry.language for entry in ts_catalog.languages]
    assert list(languages()) == list(catalog.languages())
    assert [p.language for p in packs()] == list(catalog.languages())
    assert PACKS_SLICE == "M-068"
    assert catalog.source_note and catalog.extension_rule
    assert "pack, not a patch" in catalog.extension_rule
    assert "M-043" in catalog.extension_rule


def test_extensions_match_the_tree_sitter_catalogue(catalog):
    from mythic_agent.core.tree_sitter_foundation import load_catalog

    ts_catalog = load_catalog()
    for entry in ts_catalog.languages:
        pack = pack_for_language(entry.language)
        assert pack is not None
        assert list(pack.extensions) == list(entry.extensions)


def test_servers_match_the_live_lsp_catalogue(catalog):
    from mythic_agent.integrations.lsp import server_for_language

    for pack in catalog.entries:
        server = server_for_language(pack.language)
        if pack.language == "mojo":
            assert server is None
            assert pack.server is None
            assert server_command("mojo") is None
            continue
        assert server is not None
        assert pack.server is not None
        assert pack.server.name == server.name
        assert list(pack.server.command) == list(server.command)
        assert server_command(pack.language) == tuple(server.command)
    # The typescript ServerDef serves both languages, in data too.
    ts_server = server_for_language("typescript")
    js_server = server_for_language("javascript")
    assert ts_server is js_server
    assert pack_for_language("javascript").server.name == "typescript"
    assert pack_for_language("typescript").server.command == \
        ("typescript-language-server", "--stdio")
    assert pack_for_language("python").server.command == \
        ("pyright-langserver", "--stdio")
    assert pack_for_language("rust").server.command == ("rust-analyzer",)
    assert pack_for_language("go").server.command == ("gopls",)


def test_python_formatters_are_the_format_covenants_live_names():
    from mythic_agent.tools.format_covenant import (
        formatter_names as covenant_names,
    )

    assert formatter_names("python") == covenant_names()
    assert set(formatter_names("python")) == {
        "black", "ruff", "isort", "yapf"}


def test_python_pytest_runner_is_recognised_live():
    from mythic_agent.tools.debug_loop import is_pytest_command

    pack = pack_for_language("python")
    runners = {r.name: r.command for r in pack.test_runners}
    assert "pytest" in runners
    assert core.test_runner_names("python") == ("pytest",)
    assert is_pytest_command(" ".join(runners["pytest"]))


def test_the_other_toolchains_are_the_declared_ones():
    assert formatter_names("javascript") == ("prettier",)
    assert formatter_names("typescript") == ("prettier",)
    assert formatter_names("rust") == ("rustfmt",)
    assert formatter_names("go") == ("gofmt",)
    assert formatter_names("mojo") == ("mojo",)
    assert pack_for_language("mojo").formatters[0].command == \
        ("mojo", "format")
    assert core.test_runner_names("javascript") == ("npm",)
    assert core.test_runner_names("typescript") == ("npm",)
    assert core.test_runner_names("rust") == ("cargo",)
    assert core.test_runner_names("go") == ("go",)
    assert core.test_runner_names("mojo") == ("mojo",)
    assert pack_for_language("go").test_runners[0].command == \
        ("go", "test", "./...")


def test_accessors_resolve_extensions_and_unknowns():
    assert pack_for_extension(".py").language == "python"
    assert pack_for_extension("pyi").language == "python"
    assert pack_for_extension(".tsx").language == "typescript"
    assert pack_for_extension(".mojo").language == "mojo"
    assert pack_for_extension(".cobol") is None
    assert pack_for_language("Python").language == "python"
    assert pack_for_language("cobol") is None
    assert formatter_names("cobol") == ()
    assert core.test_runner_names("cobol") == ()
    assert server_command("cobol") is None


def test_notes_are_honest_about_live_wiring(catalog):
    python = pack_for_language("python")
    assert "live" in python.notes.lower()
    mojo = pack_for_language("mojo")
    assert "no Mojo server" in mojo.notes or "server null" in mojo.notes
    for language in ("javascript", "rust", "go"):
        notes = pack_for_language(language).notes
        assert "declared pack data only" in notes


def test_core_render_markdown_reports_every_pack(catalog):
    text = render_markdown()
    assert "6 pack(s)" in text
    for pack in catalog.entries:
        assert f"**{pack.language}**" in text
        assert pack.id in text
    for pack in catalog.entries:
        for extension in pack.extensions:
            assert f"`{extension}`" in text
    assert "no server (declared null, honestly)" in text
    assert "Languages: " + ", ".join(catalog.languages()) in text


# -- the validator --------------------------------------------------------

def test_validator_rejects_non_sequential_ids():
    data = _mutated(lambda d: d["packs"][2].update(id="LP-09"))
    assert any("sequential" in p for p in validate_language_packs(data))


def test_validator_rejects_a_duplicate_language():
    def spoil(d):
        d["packs"][1]["language"] = "python"
        d["packs"][1]["extensions"] = [".py", ".pyi"]

    problems = validate_language_packs(_mutated(spoil))
    assert any("duplicate language" in p for p in problems)


def test_validator_rejects_a_language_absent_from_the_catalogue():
    def spoil(d):
        d["packs"][0]["language"] = "cobol"

    problems = validate_language_packs(_mutated(spoil))
    assert any("absent from" in p and "M-043" in p for p in problems)


def test_validator_rejects_extensions_mismatching_the_catalogue():
    def spoil(d):
        d["packs"][3]["extensions"] = [".rs", ".rust"]

    problems = validate_language_packs(_mutated(spoil))
    assert any("extensions" in p and "catalogue" in p for p in problems)


def test_validator_rejects_empty_extensions():
    data = _mutated(lambda d: d["packs"][0].update(extensions=[]))
    assert any("extensions" in p for p in validate_language_packs(data))


def test_validator_rejects_a_server_with_an_empty_command():
    def spoil(d):
        d["packs"][0]["server"]["command"] = []

    problems = validate_language_packs(_mutated(spoil))
    assert any("server" in p and "command" in p for p in problems)


def test_validator_rejects_duplicate_formatter_names():
    def spoil(d):
        d["packs"][0]["formatters"].append(
            {"name": "black", "command": ["black"]})

    problems = validate_language_packs(_mutated(spoil))
    assert any("duplicate" in p and "formatters" in p for p in problems)


def test_validator_rejects_duplicate_runner_names():
    def spoil(d):
        d["packs"][3]["test_runners"].append(
            {"name": "cargo", "command": ["cargo", "test"]})

    problems = validate_language_packs(_mutated(spoil))
    assert any("duplicate" in p and "test_runners" in p
               for p in problems)


def test_validator_rejects_an_empty_formatter_command():
    def spoil(d):
        d["packs"][1]["formatters"][0]["command"] = []

    problems = validate_language_packs(_mutated(spoil))
    assert any("formatters" in p and "command" in p for p in problems)


def test_validator_rejects_an_empty_runner_command():
    def spoil(d):
        d["packs"][4]["test_runners"][0]["command"] = []

    problems = validate_language_packs(_mutated(spoil))
    assert any("test_runners" in p and "command" in p for p in problems)


def test_load_raises_on_invalid_data():
    with pytest.raises(ValidationError):
        load_language_packs({"schema": "nope", "packs": []})


# -- the surface -----------------------------------------------------------

def test_show_report_covers_all_packs():
    report = language_packs_report()
    assert report.status == "ok"
    assert report.kind == "show"
    assert report.pack_languages() == languages()
    n_packs, n_tools, _ = report.totals()
    assert n_packs == 6
    assert n_tools == sum(
        len(p.toolchain_entries()) for p in report.packs)


def test_single_language_report_is_just_that_pack():
    report = language_packs_report(mode="language", language="rust")
    assert report.status == "ok"
    assert report.pack_languages() == ("rust",)
    pack = report.packs[0]
    assert pack.server is not None and pack.server.name == "rust-analyzer"
    assert [f.name for f in pack.formatters] == ["rustfmt"]


def test_unknown_language_is_a_plain_refusal():
    report = language_packs_report(mode="language", language="cobol")
    assert report.status == "error"
    assert report.packs == []
    for language in languages():
        assert language in report.note


def test_installed_flags_are_bool_and_match_which():
    report = language_packs_report()
    for pack in report.packs:
        for entry in pack.toolchain_entries():
            assert isinstance(entry.installed, bool)
            assert entry.installed == (
                shutil.which(entry.binary()) is not None)
            assert entry.binary() == entry.command[0]
            assert entry.command_text() == " ".join(entry.command)


def test_disabled_reads_nothing(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("the pack data must not be loaded")

    monkeypatch.setattr(core, "load_language_packs", _boom)
    report = language_packs_report(enabled=False)
    assert report.status == "disabled"
    assert report.packs == []
    assert surface.enabled_from_config({}) is True
    assert surface.enabled_from_config({"language_packs": False}) is False
    assert surface.enabled_from_config(None) is True


def test_parse_langpacks_args():
    assert parse_langpacks_args("") == {"action": "show"}
    assert parse_langpacks_args("show") == {"action": "show"}
    assert parse_langpacks_args("Python") == {
        "action": "language", "language": "python"}
    with pytest.raises(ValueError):
        parse_langpacks_args("python rust")


def test_format_and_render_use_the_reports_own_values():
    report = language_packs_report()
    text = format_language_pack_report(
        {"report": report.record(),
         "plain_explanation": PLAIN_EXPLANATION})
    assert "Language packs (M-068)" in text
    assert "pyright-langserver" in text
    assert "server: none declared" in text  # Mojo, honestly
    page = surface.render_markdown(report)
    n_packs, n_tools, n_installed = report.totals()
    assert f"**{n_packs} pack(s)**" in page
    assert f"**{n_tools} declared" in page
    assert f"**{n_installed} installed**" in page
    assert USAGE.startswith("Usage")


def test_report_never_writes(tmp_path: Path):
    before = sorted(p.name for p in tmp_path.iterdir())
    language_packs_report(tmp_path)
    language_packs_report(tmp_path, mode="language", language="go")
    assert sorted(p.name for p in tmp_path.iterdir()) == before


# -- surfaces ---------------------------------------------------------------

def _bare_agent(root: Path, config=None):
    from mythic_agent.agents.llm import Agent

    agent = Agent.__new__(Agent)
    agent.project_root = root
    agent.config = config or {}
    agent._session_store = None
    agent.session_id = None
    return agent


def test_agent_surfaces(tmp_path: Path):
    agent = _bare_agent(tmp_path)
    status = agent.language_packs()
    assert status["report"]["status"] == "ok"
    assert len(status["report"]["packs"]) == 6
    one = agent.language_packs("language", language="go")
    assert [p["language"] for p in one["report"]["packs"]] == ["go"]
    assert one["plain_explanation"] == PLAIN_EXPLANATION


def test_agent_respects_the_config_switch(tmp_path: Path):
    agent = _bare_agent(tmp_path, {"language_packs": False})
    status = agent.language_packs()
    assert status["report"]["status"] == "disabled"
    assert status["report"]["packs"] == []


def test_terminal_road(tmp_path: Path):
    from mythic_agent.terminal import _slash

    agent = _bare_agent(tmp_path)
    handled, _, text = _slash(agent, "/langpacks")
    assert handled and "Language packs (M-068)" in text
    handled, _, text = _slash(agent, "/langpacks python")
    assert handled and "pyright" in text
    handled, _, text = _slash(agent, "/langpacks python rust")
    assert handled and "Usage" in text


def test_tui_road(tmp_path: Path, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY

    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    agent = _bare_agent(tmp_path)
    AGENT_REGISTRY["Primary"] = agent
    try:
        handler = CommandHandler.__new__(CommandHandler)
        handler._handle_langpacks("")
        handler._handle_langpacks("rust")
        handler._handle_langpacks("python rust")
    finally:
        AGENT_REGISTRY.pop("Primary", None)
    text = "\n".join(kwargs.get("text", "")
                     for _event, kwargs in published)
    assert "Language packs (M-068)" in text
    assert "rust-analyzer" in text
    assert "Usage" in text


def test_setting_lives_in_defaults_and_catalogue():
    import yaml

    root = Path(__file__).resolve().parents[1]
    defaults = yaml.safe_load(
        (root / "mythic_agent/data/config_defaults.yaml").read_text(
            encoding="utf-8"))
    assert defaults["language_packs"] is True
    catalogue = yaml.safe_load(
        (root / "mythic_agent/data/config_catalog.yaml").read_text(
            encoding="utf-8"))
    entries = [s for s in catalogue["settings"]
               if s["name"] == "language_packs"]
    assert len(entries) == 1
    assert entries[0]["id"] == "S-58"


def test_config_catalogue_carries_the_setting():
    from mythic_agent.core.config_catalog import load_catalog

    catalog = load_catalog()
    entry = [s for s in catalog.settings if s.name == "language_packs"]
    assert len(entry) == 1
    assert entry[0].id == "S-58"


def test_gap_audit_has_no_m068_row_recorded():
    # Checked at build time (M-067's pattern): no census
    # gap row is owned by M-068, so no module_kind flip
    # exists to make for this slice.
    import yaml

    root = Path(__file__).resolve().parents[1]
    audit = yaml.safe_load(
        (root / "mythic_agent/data/gap_audit.yaml").read_text(
            encoding="utf-8"))
    assert [r for r in audit["rows"] if r["slice"] == "M-068"] == []
