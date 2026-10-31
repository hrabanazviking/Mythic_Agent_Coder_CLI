"""
TIER: unit
Provider-registry-as-data gate (All-Features roadmap slice M-019).

The shipped registry data (``mythic_agent/data/provider_registry.yaml``)
must define every provider the app ships — endpoint, auth style, model
list, capabilities — and it must agree with the live adapter classes:
each entry is cross-checked against the class it names (canonical
name, default model, key env, endpoint default, live capabilities())
and against the runtime registry in ``mythic_agent.providers.registry``,
so the data and the code cannot drift apart. Model honesty: every
non-default model in a list must be a model the static model registry
already knows; a provider's own default is always allowed (local
placeholder names and the gateway's auto-router are defaults, not
claims about a vendor catalogue).
"""

import copy
import importlib

import pytest

from mythic_agent.core.provider_registry import (
    CAPABILITY_FLAGS,
    DIALECTS,
    ProviderRegistry,
    load_registry,
    render_markdown,
    validate_registry,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.providers.model_registry import known
from mythic_agent.providers.registry import get_provider, list_providers
from mythic_agent.resources import load_resource


@pytest.fixture(scope="module")
def registry() -> ProviderRegistry:
    return load_registry()


def _adapter_class(provider):
    module_name, class_name = provider.adapter.split(":")
    return getattr(importlib.import_module(module_name), class_name)


def test_shipped_registry_loads_and_validates(registry):
    assert isinstance(registry, ProviderRegistry)
    assert validate_registry(load_resource("provider_registry.yaml")) == []
    assert registry.source_note and registry.extension_rule


def test_registry_names_match_the_runtime_registry(registry):
    assert list(registry.names()) == list_providers()
    assert len(registry.providers) == 10


def test_every_entry_matches_its_live_adapter_class(registry):
    for provider in registry.providers:
        cls = _adapter_class(provider)
        assert cls.name == provider.name
        assert cls.default_model == provider.default_model
        assert cls.api_key_env == provider.api_key_env
        instance = cls()
        live_caps = instance.capabilities()
        assert set(live_caps) == set(CAPABILITY_FLAGS)
        for flag in CAPABILITY_FLAGS:
            assert provider.capability(flag) is live_caps[flag], (
                provider.name,
                flag,
            )


def test_endpoints_match_live_adapter_defaults(registry):
    for provider in registry.providers:
        cls = _adapter_class(provider)
        if provider.dialect == "native_sdk":
            # The SDK owns the address; the class defines no default
            # endpoint and the data must not invent one.
            assert provider.endpoint is None
            assert not hasattr(cls, "base_url_default")
        elif provider.dialect == "ollama_native":
            assert provider.endpoint == cls().host
        else:
            assert provider.endpoint == cls.base_url_default


def test_auth_styles_agree_with_live_key_envs(registry):
    for provider in registry.providers:
        if provider.auth_style == "api_key_env":
            assert provider.api_key_env
            assert provider.locality == "remote"
        else:
            assert provider.api_key_env is None


def test_home_fires_are_first_citizens(registry):
    # Part II's promise: Ollama and the local doors are registry
    # citizens, not afterthoughts.
    local_names = [p.name for p in registry.by_locality("local")]
    assert "ollama" in local_names
    assert len(local_names) == 5
    assert len(registry.by_locality("remote")) == 5
    ollama = registry.provider("ollama")
    assert ollama.dialect == "ollama_native"
    assert ollama.endpoint == "http://localhost:11434"


def test_aliases_resolve_like_the_runtime_registry(registry):
    for alias, canonical in registry.aliases:
        assert registry.provider(alias).name == canonical
        assert get_provider(alias).name == canonical
    assert registry.provider("claude").name == "anthropic"
    with pytest.raises(KeyError):
        registry.provider("no-such-door")


def test_model_lists_are_honest(registry):
    for provider in registry.providers:
        assert provider.default_model in provider.models
        for model in provider.models:
            # A listed model is either the provider's own default
            # (placeholders, the gateway auto-router) or a model the
            # static model registry already knows — never invented.
            assert model == provider.default_model or known(model), (
                provider.name,
                model,
            )


def test_dialects_cover_the_ocean(registry):
    assert {p.dialect for p in registry.providers} == set(DIALECTS)
    assert len(registry.by_dialect("openai_compatible")) == 7
    assert len(registry.by_dialect("native_sdk")) == 2
    assert len(registry.by_dialect("ollama_native")) == 1


def test_render_markdown_reports_every_door(registry):
    text = render_markdown(registry)
    assert "10 providers" in text
    for provider in registry.providers:
        assert f"**{provider.name}**" in text
        assert provider.default_model in text
    for alias, _canonical in registry.aliases:
        assert f"`{alias}`" in text
    # The one honestly-false capability in the ocean is rendered.
    assert "tool_calling=no" in text


def _mutated(mutator):
    data = copy.deepcopy(load_resource("provider_registry.yaml"))
    mutator(data)
    return data


def test_validator_rejects_a_duplicate_provider():
    data = _mutated(lambda d: d["providers"].append(dict(d["providers"][0])))
    assert any("duplicate" in p for p in validate_registry(data))


def test_validator_rejects_an_invented_native_endpoint():
    def spoil(d):
        d["providers"][0]["endpoint"] = "https://example.invalid/v1"

    problems = validate_registry(_mutated(spoil))
    assert any("native_sdk" in p for p in problems)


def test_validator_rejects_auth_inconsistency():
    def spoil(d):
        d["providers"][0]["api_key_env"] = None

    assert validate_registry(_mutated(spoil))


def test_validator_rejects_default_outside_model_list():
    def spoil(d):
        d["providers"][1]["default_model"] = "not-listed"

    assert any("models list" in p for p in validate_registry(_mutated(spoil)))


def test_validator_rejects_a_missing_capability_flag():
    def spoil(d):
        del d["providers"][1]["capabilities"]["vision"]

    assert any("capabilities" in p for p in validate_registry(_mutated(spoil)))


def test_validator_rejects_alias_to_an_unknown_provider():
    def spoil(d):
        d["aliases"]["claude"] = "no-such-door"

    assert any("alias" in p for p in validate_registry(_mutated(spoil)))


def test_load_raises_on_invalid_data():
    with pytest.raises(ValidationError):
        load_registry({"schema": "nope", "providers": [], "aliases": {}})
