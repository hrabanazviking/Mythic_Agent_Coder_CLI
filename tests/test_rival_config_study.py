"""
TIER: unit
Rivals' Config Import Study gate (All-Features roadmap slice M-014).

The shipped study (``mythic_agent/data/rival_config_study.yaml``)
records, clean-room from public documentation, what the config and
instruction files of Claude Code, Codex CLI, OpenCode and Aider look
like behaviourally — the spec for Part X's rival importers (M-241).
These tests cross-check the study against the live tree it must
serve: the four rivals must be the roadmap-named four and appear in
the M-001 feature census; every Mythic setting a rival key claims
to land on must exist in the M-009 config catalogue; and the magic
instruction filenames the study credits to Claude Code and Codex /
OpenCode (CLAUDE.md, AGENTS.md) must be names Mythic's own
instruction resolver already discovers.
"""

import copy

import pytest

from mythic_agent.context.instructions import INSTRUCTION_FILENAMES
from mythic_agent.core.config_catalog import load_catalog
from mythic_agent.core.feature_census import load_census
from mythic_agent.core.rival_config_study import (
    RIVAL_IDS,
    RivalConfigStudy,
    load_study,
    render_markdown,
    validate_study,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource


@pytest.fixture(scope="module")
def study() -> RivalConfigStudy:
    return load_study()


def test_shipped_study_loads_and_validates(study):
    assert isinstance(study, RivalConfigStudy)
    assert validate_study(load_resource("rival_config_study.yaml")) == []
    assert study.counts() == (4, 23, 24, 6)


def test_rivals_are_the_roadmap_four_in_order(study):
    assert study.rival_ids() == RIVAL_IDS
    assert [r.name for r in study.rivals] == [
        "Claude Code", "Codex CLI", "OpenCode", "Aider",
    ]


def test_rivals_appear_in_the_feature_census(study):
    census_rivals = {r.id for r in load_census().rivals}
    for slug in study.rival_ids():
        assert slug in census_rivals


def test_mapped_settings_exist_in_config_catalog(study):
    setting_names = set(load_catalog().setting_names())
    assert study.mapped_settings() == (
        "model", "permission_mode", "base_url", "sub_agents", "api_keys",
    )
    for name in study.mapped_settings():
        assert name in setting_names


def test_every_rival_has_settings_and_instruction_sources(study):
    for slug in study.rival_ids():
        files = study.files_for(slug)
        roles = {f.role for f in files}
        scopes = {f.scope for f in files}
        assert "settings" in roles
        assert "instructions" in roles
        assert "user" in scopes
        assert "project" in scopes
        assert len(study.mappings_for(slug)) >= 3


def test_magic_instruction_filenames_are_already_discovered(study):
    instruction_names = {
        f.rival: f.name
        for f in study.files
        if f.role == "instructions" and f.rival != "aider"
    }
    assert instruction_names["claude-code"] == "CLAUDE.md"
    assert instruction_names["codex-cli"] == "AGENTS.md"
    assert instruction_names["opencode"] == "AGENTS.md"
    for name in ("CLAUDE.md", "AGENTS.md"):
        assert name in INSTRUCTION_FILENAMES


def test_aider_instructions_come_from_a_read_list_not_a_magic_name(study):
    aider_instructions = [
        f for f in study.files_for("aider") if f.role == "instructions"
    ]
    assert len(aider_instructions) == 1
    entry = aider_instructions[0]
    assert "read" in entry.behaviour
    assert entry.name not in INSTRUCTION_FILENAMES


def test_formats_match_each_rivals_real_dialect(study):
    formats = {}
    for slug in study.rival_ids():
        formats[slug] = {
            f.format for f in study.files_for(slug) if f.role == "settings"
        }
    assert formats["claude-code"] == {"json"}
    assert formats["codex-cli"] == {"toml"}
    assert formats["opencode"] == {"jsonc"}
    assert formats["aider"] == {"yaml", "dotenv"}


def test_mcp_dialects_present_and_aider_honestly_has_none(study):
    assert any(f.role == "mcp" for f in study.files_for("claude-code"))
    for slug in ("codex-cli", "opencode"):
        mcp_mappings = [
            m for m in study.mappings_for(slug) if "mcp" in m.key
        ]
        assert len(mcp_mappings) == 1
    assert not any(f.role == "mcp" for f in study.files_for("aider"))


def test_every_rival_routes_secrets_to_kista(study):
    for rival in study.rivals:
        assert any("Kista" in d for d in rival.importer_directives), rival.rival
    secrets_findings = [f for f in study.findings if "Kista" in f.importer_implication]
    assert len(secrets_findings) >= 1


def test_precedence_ladders_name_the_trust_and_policy_edges(study):
    by_slug = {r.rival: r for r in study.rivals}
    assert "managed" in by_slug["claude-code"].precedence[0]
    codex_files = " ".join(
        f.behaviour for f in study.files_for("codex-cli")
    )
    assert "trusted" in codex_files
    aider_top = by_slug["aider"].precedence[0]
    assert "command-line" in aider_top


def test_scope_note_records_the_gemini_gap(study):
    assert "Gemini/Antigravity" in study.scope_note
    assert "NOT studied here" in study.scope_note


def test_render_markdown_uses_the_accessors(study):
    page = render_markdown(study)
    for rival in study.rivals:
        assert rival.name in page
    assert "4 rivals, 23 files, 24 key mappings, 6 findings" in page
    for setting in study.mapped_settings():
        assert setting in page
    for key_id in study.unmapped_keys():
        assert key_id in page


def test_validation_rejects_a_dropped_rival():
    raw = load_resource("rival_config_study.yaml")
    broken = copy.deepcopy(raw)
    broken["rivals"] = broken["rivals"][:3]
    problems = validate_study(broken)
    assert any("roadmap-named four" in p for p in problems)
    with pytest.raises(ValidationError):
        load_study(broken)


def test_validation_rejects_a_mapping_with_no_landing_spot():
    raw = load_resource("rival_config_study.yaml")
    broken = copy.deepcopy(raw)
    broken["key_mappings"][0]["mythic_setting"] = ""
    problems = validate_study(broken)
    assert any("mythic_setting" in p for p in problems)


def test_validation_rejects_directives_without_kista():
    raw = load_resource("rival_config_study.yaml")
    broken = copy.deepcopy(raw)
    broken["rivals"][0]["importer_directives"] = [
        d.replace("Kista", "a drawer") for d in broken["rivals"][0]["importer_directives"]
    ]
    problems = validate_study(broken)
    assert any("Kista" in p for p in problems)


def test_validation_rejects_rival_without_instructions():
    raw = load_resource("rival_config_study.yaml")
    broken = copy.deepcopy(raw)
    broken["files"] = [
        f for f in broken["files"]
        if not (f["rival"] == "aider" and f["role"] == "instructions")
    ]
    # Renumbering would mask the loss; the study must fail as-is.
    problems = validate_study(broken)
    assert problems
