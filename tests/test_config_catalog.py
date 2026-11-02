"""
TIER: unit
Config Catalogue gate (All-Features roadmap slice M-009).

The shipped catalogue (``mythic_agent/data/config_catalog.yaml``) is
the compatibility contract for Part VIII's settings redesign. It is
not a hand-waved list: these tests cross-check it against the live
tree — every key of ``config_defaults.yaml`` and
``runtime_defaults.yaml``, every key of ``CONFIG_SCHEMA``, every
environment variable named in the package's env-reading modules, the
packaged data files, and the workspace instruction filenames — so a
new setting, key, or variable cannot land uncatalogued.
"""

import copy
import re
from pathlib import Path

import pytest
import yaml

from mythic_agent.core.config_catalog import (
    ConfigCatalog,
    load_catalog,
    render_markdown,
    validate_catalog,
)
from mythic_agent.core.config_manager import CONFIG_SCHEMA
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource, resource_root

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE = REPO_ROOT / "mythic_agent"

_ENV_TOKEN = re.compile(r'"([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)"')
_ENV_PREFIXES = ("MYTHIC_", "OPENAI_", "ANTHROPIC_", "GOOGLE_", "DEEPSEEK_",
                 "OPENROUTER_", "PG_")


def _live_env_names() -> set:
    """Env vars named in modules that read the environment or name a key env."""
    names = set()
    for path in PACKAGE.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "environ" not in text and "api_key_env" not in text:
            continue
        for token in _ENV_TOKEN.findall(text):
            if token.startswith(_ENV_PREFIXES) or token == "TMPDIR":
                names.add(token)
    return names


@pytest.fixture(scope="module")
def catalog() -> ConfigCatalog:
    return load_catalog()


def test_shipped_catalogue_loads_and_validates(catalog):
    assert isinstance(catalog, ConfigCatalog)
    assert validate_catalog(load_resource("config_catalog.yaml")) == []
    n_settings, n_env, n_files = catalog.counts()
    assert n_settings >= 35 and n_env >= 16 and n_files >= 10


def test_every_defaults_key_is_catalogued(catalog):
    names = set(catalog.setting_names())
    defaults = yaml.safe_load((resource_root() / "config_defaults.yaml").read_text())
    for key in defaults:
        assert key in names, f"config_defaults key {key!r} uncatalogued"
    for key in defaults["github"]:
        assert f"github.{key}" in names, f"github key {key!r} uncatalogued"
    runtime = yaml.safe_load((resource_root() / "runtime_defaults.yaml").read_text())
    for key in runtime:
        assert key in names, f"runtime key {key!r} uncatalogued"


def test_every_schema_key_is_catalogued(catalog):
    names = set(catalog.setting_names())
    for key in CONFIG_SCHEMA:
        assert key in names, f"CONFIG_SCHEMA key {key!r} uncatalogued"


def test_setting_types_and_defaults_match_the_defaults_files(catalog):
    by_name = {s.name: s for s in catalog.settings}
    defaults = yaml.safe_load((resource_root() / "config_defaults.yaml").read_text())
    for key, value in defaults.items():
        if key in ("runtime", "github"):
            continue
        assert by_name[key].type == type(value).__name__, key
    runtime = yaml.safe_load((resource_root() / "runtime_defaults.yaml").read_text())
    for key, value in runtime.items():
        assert by_name[key].scope == "runtime"
        assert by_name[key].type == type(value).__name__, key


def test_every_live_env_var_is_catalogued(catalog):
    catalogued = set(catalog.env_names())
    live = _live_env_names()
    assert live, "the live scan must find the env vars it guards"
    missing = live - catalogued
    assert not missing, f"env vars named in the package but uncatalogued: {sorted(missing)}"


def test_secret_env_vars_are_exactly_the_key_and_password_ones(catalog):
    for name in catalog.secret_env_names():
        assert name.endswith(("_API_KEY", "_PASSWORD")), name
    assert "MYTHIC_HOME" not in catalog.secret_env_names()


def test_package_data_files_exist_and_instruction_names_match(catalog):
    for entry in catalog.files:
        if entry.kind == "package-data":
            assert (REPO_ROOT / entry.path).exists(), entry.path
    from mythic_agent.context.instructions import INSTRUCTION_FILENAMES
    instruction = [f for f in catalog.files if f.kind == "workspace-instruction"]
    assert len(instruction) == 1
    assert set(instruction[0].names) == set(INSTRUCTION_FILENAMES)


def test_setting_sources_exist(catalog):
    for entry in list(catalog.settings) + list(catalog.env_vars):
        source = entry.source.split(" ")[0]
        assert (REPO_ROOT / source).exists(), f"{entry.name}: {source}"


def test_ids_are_sequential(catalog):
    assert [s.id for s in catalog.settings] == [
        f"S-{n:02d}" for n in range(1, len(catalog.settings) + 1)]
    assert [v.id for v in catalog.env_vars] == [
        f"V-{n:02d}" for n in range(1, len(catalog.env_vars) + 1)]
    assert [f.id for f in catalog.files] == [
        f"F-{n:02d}" for n in range(1, len(catalog.files) + 1)]


def test_render_covers_every_entry(catalog):
    text = render_markdown(catalog)
    for name in catalog.setting_names():
        assert f"`{name}`" in text
    for name in catalog.env_names():
        assert f"`{name}`" in text
    for entry in catalog.files:
        assert entry.id in text and entry.path in text
    for name in catalog.secret_env_names():
        assert name in text


def _tampered(mutator):
    data = copy.deepcopy(load_resource("config_catalog.yaml"))
    mutator(data)
    return data


def test_validation_rejects_a_dropped_setting():
    data = _tampered(lambda d: d["settings"].pop(0))
    problems = validate_catalog(data)
    assert any("sequential" in p or "non-empty" in p for p in problems)
    with pytest.raises(ValidationError):
        load_catalog(data)


def test_validation_rejects_an_unknown_scope():
    data = _tampered(lambda d: d["settings"][0].update(scope="somewhere"))
    problems = validate_catalog(data)
    assert any("scope" in p for p in problems)


def test_validation_rejects_a_non_bool_secret_flag():
    data = _tampered(lambda d: d["env_vars"][0].update(secret="yes"))
    problems = validate_catalog(data)
    assert any("secret must be a boolean" in p for p in problems)


def test_validation_rejects_a_contract_without_part_viii():
    data = _tampered(lambda d: d.update(scope_note="A list of settings."))
    problems = validate_catalog(data)
    assert any("Part VIII" in p for p in problems)
