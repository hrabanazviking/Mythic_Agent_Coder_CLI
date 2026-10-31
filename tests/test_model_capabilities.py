"""
TIER: unit
Capability-truth-per-model gate (All-Features roadmap slice M-027).

The shipped data (``mythic_agent/data/model_capabilities.yaml``) must
carry exactly one record for every distinct model in the M-019
provider registry, and every value must agree with the live static
model registry (``mythic_agent.providers.model_registry``): a model
that registry knows gets its context and flags from ``lookup()`` —
never from its provider's door-level capabilities — and a model it
does not know (or a local placeholder name) is all-unknown (null),
never guessed. Reasoning is true only for deepseek-reasoner, the one
model with explicit in-tree evidence; max output is unknown for
every model, because no per-model max-output value is documented
anywhere in the tree.
"""

import copy

import pytest

from mythic_agent.core.model_capabilities import (
    CAPABILITY_FIELDS,
    ModelCapabilities,
    load_capabilities,
    render_markdown,
    validate_capabilities,
)
from mythic_agent.core.provider_registry import load_registry
from mythic_agent.core.validation import ValidationError
from mythic_agent.providers.model_registry import known, lookup
from mythic_agent.resources import load_resource

#: Names that stand for whatever model a local server was launched
#: with — all-unknown by design, even when a name pattern happens to
#: match the static registry (llama.cpp-local matches ^llama).
PLACEHOLDERS = {
    "aesir-local",
    "llama.cpp-local",
    "lmstudio-local",
    "local-model",
    "vllm-local",
    "openrouter/auto",
}


@pytest.fixture(scope="module")
def capabilities() -> ModelCapabilities:
    return load_capabilities()


def test_shipped_capabilities_load_and_validate(capabilities):
    assert isinstance(capabilities, ModelCapabilities)
    assert validate_capabilities(load_resource("model_capabilities.yaml")) == []
    assert len(capabilities.records) == 28
    # The honesty rule is stated in the data itself: provider-level
    # capabilities are NOT inherited per model.
    assert "NOT inherited" in capabilities.source_note


def test_model_set_matches_the_provider_registry_exactly(capabilities):
    registry = load_registry()
    expected = {m for p in registry.providers for m in p.models}
    assert len(expected) == 28
    assert set(capabilities.models()) == expected
    assert len(capabilities.models()) == len(set(capabilities.models()))


def test_providers_lists_match_the_provider_registry(capabilities):
    registry = load_registry()
    expected = {}
    for provider in registry.providers:
        for model in provider.models:
            expected.setdefault(model, []).append(provider.name)
    for record in capabilities.records:
        assert list(record.providers) == expected[record.model]


def test_known_models_take_context_and_flags_from_model_registry(capabilities):
    checked = 0
    for record in capabilities.records:
        if record.model in PLACEHOLDERS or not known(record.model):
            continue
        flags, window = lookup(record.model)
        assert record.context_tokens == window, record.model
        assert record.tool_calling is flags["tool_calling"], record.model
        assert record.vision is flags["vision"], record.model
        assert record.streaming is flags["streaming"], record.model
        assert record.json_mode is flags["json_mode"], record.model
        checked += 1
    assert checked == 19


def test_unknown_and_placeholder_models_are_all_unknown(capabilities):
    checked = 0
    for record in capabilities.records:
        if record.model not in PLACEHOLDERS and known(record.model):
            continue
        for field in CAPABILITY_FIELDS:
            assert record.capability(field) is None, (record.model, field)
        checked += 1
    assert checked == 9


def test_reasoning_is_true_only_for_deepseek_reasoner(capabilities):
    # The only in-tree per-model reasoning evidence names the
    # reasoner model (mythic_agent.providers.reasoning: reasoning is
    # inherent to *reasoner* models). Any other true would need its
    # own cited evidence in that record's source — none exists.
    trues = [r.model for r in capabilities.records if r.reasoning is True]
    assert trues == ["deepseek-reasoner"]
    reasoner = capabilities.for_model("deepseek-reasoner")
    assert "providers.reasoning" in reasoner.source
    for record in capabilities.records:
        if record.model != "deepseek-reasoner":
            assert record.reasoning is None, record.model


def test_max_output_is_unknown_for_every_model(capabilities):
    # No documented per-model max-output value exists in the tree;
    # a number here would be invented, so every record is null.
    assert all(r.max_output_tokens is None for r in capabilities.records)
    assert all(r.source and r.notes for r in capabilities.records)


def test_lookup_surfaces(capabilities):
    anthropic = capabilities.by_provider("anthropic")
    assert [r.model for r in anthropic] == [
        "claude-3-5-haiku",
        "claude-3-5-sonnet",
        "claude-opus-4-1",
        "claude-sonnet-4-5",
    ]
    assert capabilities.by_provider("no-such-provider") == ()
    assert capabilities.known_context("gpt-5") == 400_000
    assert capabilities.known_context("grok-4") is None
    assert capabilities.known_context("no-such-model") is None
    record = capabilities.for_model("gpt-5")
    assert record.capability("vision") is True
    with pytest.raises(KeyError):
        record.capability("telepathy")


def test_unlisted_model_is_all_unknown_never_a_crash(capabilities):
    record = capabilities.for_model("no-such-model")
    assert record.model == "no-such-model"
    assert record.providers == ()
    for field in CAPABILITY_FIELDS:
        assert record.capability(field) is None, field


def test_render_markdown_shows_every_field_of_every_record(capabilities):
    text = render_markdown(capabilities)
    assert "28 models" in text
    for record in capabilities.records:
        assert f"### {record.model}" in text
        assert record.source in text
        assert record.notes in text
    for field in CAPABILITY_FIELDS:
        assert f"- {field}:" in text
    # Null fields render as the word "unknown" — grok-4 is all-null,
    # and the unlisted-model example is rendered too.
    assert "unknown" in text
    assert "### no-such-model" in text
    assert "context_tokens: 400000" in text  # a known value, rendered


def _mutated(mutator):
    data = copy.deepcopy(load_resource("model_capabilities.yaml"))
    mutator(data)
    return data


def test_validator_rejects_a_duplicate_model():
    data = _mutated(lambda d: d["models"].append(dict(d["models"][0])))
    assert any("duplicate" in p for p in validate_capabilities(data))


def test_validator_rejects_a_bad_tri_state_value():
    def spoil(d):
        d["models"][0]["vision"] = "yes"

    assert any("vision" in p for p in validate_capabilities(_mutated(spoil)))


def test_validator_rejects_zero_and_negative_tokens():
    def zero(d):
        d["models"][2]["context_tokens"] = 0

    def negative(d):
        d["models"][2]["max_output_tokens"] = -5

    assert any(
        "context_tokens" in p for p in validate_capabilities(_mutated(zero))
    )
    assert any(
        "max_output_tokens" in p
        for p in validate_capabilities(_mutated(negative))
    )


def test_validator_rejects_a_missing_source():
    def spoil(d):
        d["models"][0]["source"] = ""

    assert any("source" in p for p in validate_capabilities(_mutated(spoil)))


def test_validator_rejects_an_extra_field_and_a_wrong_schema():
    def extra(d):
        d["models"][0]["telepathy"] = True

    def schema(d):
        d["schema"] = "mythic.model_capabilities/2"

    assert validate_capabilities(_mutated(extra))
    assert any("schema" in p for p in validate_capabilities(_mutated(schema)))


def test_load_raises_on_invalid_data():
    with pytest.raises(ValidationError):
        load_capabilities({"schema": "nope", "models": []})
