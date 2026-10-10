"""R-030: Gemini adapter hardening tests.

TIER: unit

The real ``google.generativeai`` SDK is never imported and never
installed here: every test either hides it from ``sys.modules``
(SDK-absent path) or installs stub ``google`` / ``google.generativeai``
modules. No network traffic, no real keys.
"""

import sys
import types

import pytest

from mythic_agent.providers.google import (
    GoogleAuthError,
    GoogleProvider,
    GoogleRateLimitError,
    ProviderError,
    ProviderNotConfigured,
    _gemini_contents,
    _map_genai_error,
    _safety_diagnosis,
)

FAKE_KEY = "AIza-test-key-000"


def _boom(exc):
    """Build a _send replacement that raises ``exc``."""
    def raiser(*args, **kwargs):
        raise exc
    return raiser


class _SafetyBlockedResponse:
    """Mimics the real SDK: .text raises ValueError when blocked."""

    finish_reason = "SAFETY"

    @property
    def text(self):
        raise ValueError(
            "The `response.text` quick accessor only works for simple "
            "text responses")


def _install_genai_stub(monkeypatch, captured, response=None, error=None):
    """Install stub ``google`` + ``google.generativeai`` modules with spies."""
    child = types.ModuleType("google.generativeai")
    parent = types.ModuleType("google")
    parent.__path__ = []  # mark as a package
    parent.generativeai = child

    class RateLimitError(Exception):
        status_code = 429

    class AuthenticationError(Exception):
        status_code = 401

    def configure(**kwargs):
        captured.setdefault("configure_calls", []).append(dict(kwargs))

    class GenerativeModel:
        def __init__(self, model_name, **kwargs):
            captured["model_name"] = model_name
            captured["model_kwargs"] = dict(kwargs)

        def generate_content(self, contents, **kwargs):
            captured["contents"] = contents
            captured["gen_kwargs"] = dict(kwargs)
            if error is not None:
                raise error
            assert response is not None, "stub needs a response or an error"
            return response() if callable(response) else response

    child.configure = configure
    child.GenerativeModel = GenerativeModel
    child.RateLimitError = RateLimitError
    child.AuthenticationError = AuthenticationError
    monkeypatch.setitem(sys.modules, "google", parent)
    monkeypatch.setitem(sys.modules, "google.generativeai", child)
    return child


def _hide_sdk(monkeypatch):
    monkeypatch.setitem(sys.modules, "google", None)
    monkeypatch.setitem(sys.modules, "google.generativeai", None)


def _text_response(text="hello from gemini"):
    return types.SimpleNamespace(text=text)


# ----------------------------------------------------------------------
# (a) SDK stubbed in sys.modules; absent SDK / missing key paths
# ----------------------------------------------------------------------

def test_sdk_absent_raises_provider_not_configured(monkeypatch):
    _hide_sdk(monkeypatch)
    provider = GoogleProvider(api_key=FAKE_KEY)
    with pytest.raises(ProviderNotConfigured):
        provider._client()


def test_chat_with_absent_sdk_raises_before_network(monkeypatch):
    _hide_sdk(monkeypatch)
    provider = GoogleProvider(api_key=FAKE_KEY)
    with pytest.raises(ProviderNotConfigured):
        provider.chat([{"role": "user", "content": "Hi"}])


def test_key_missing_raises_provider_not_configured(monkeypatch):
    captured = {}
    _install_genai_stub(monkeypatch, captured, response=_text_response())
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    provider = GoogleProvider(api_key=None)
    with pytest.raises(ProviderNotConfigured) as exc:
        provider._client()
    assert "GOOGLE_API_KEY" in str(exc.value)


def test_stub_sdk_is_used_not_real_sdk(monkeypatch):
    captured = {}
    child = _install_genai_stub(monkeypatch, captured,
                               response=_text_response("hi"))
    assert sys.modules["google.generativeai"] is child
    provider = GoogleProvider(api_key=FAKE_KEY)
    assert provider.chat([{"role": "user", "content": "Hi"}]) == "hi"


# ----------------------------------------------------------------------
# (b) safety-blocked responses -> ProviderError with a clear message
# ----------------------------------------------------------------------

def test_safety_blocked_property_raise_maps_to_provider_error():
    with pytest.raises(ProviderError) as exc:
        GoogleProvider._extract_text(_SafetyBlockedResponse())
    assert "safety" in str(exc.value).lower()


def test_safety_blocked_none_text_maps_to_provider_error():
    response = types.SimpleNamespace(text=None, finish_reason="SAFETY")
    with pytest.raises(ProviderError) as exc:
        GoogleProvider._extract_text(response)
    assert "safety" in str(exc.value).lower()


def test_safety_diagnosis_reads_candidate_finish_reason():
    response = types.SimpleNamespace(
        text=None,
        candidates=[types.SimpleNamespace(finish_reason="SAFETY")])
    assert "safety" in _safety_diagnosis(response).lower()


def test_plain_empty_text_is_not_a_safety_message():
    response = types.SimpleNamespace(text=None)
    with pytest.raises(ProviderError) as exc:
        GoogleProvider._extract_text(response)
    assert "safety" not in str(exc.value).lower()
    assert "no text content" in str(exc.value).lower()


def test_safety_blocked_end_to_end(monkeypatch):
    captured = {}
    _install_genai_stub(monkeypatch, captured,
                        response=_SafetyBlockedResponse())
    provider = GoogleProvider(api_key=FAKE_KEY)
    with pytest.raises(ProviderError) as exc:
        provider.chat([{"role": "user", "content": "Hi"}])
    assert "safety" in str(exc.value).lower()
    assert FAKE_KEY not in str(exc.value)


# ----------------------------------------------------------------------
# (c) empty candidates -> ProviderError
# ----------------------------------------------------------------------

def test_empty_candidates_raise_provider_error():
    response = types.SimpleNamespace(candidates=[], text=None)
    with pytest.raises(ProviderError) as exc:
        GoogleProvider._extract_text(response)
    assert "candidate" in str(exc.value).lower()


def test_empty_candidates_end_to_end(monkeypatch):
    captured = {}
    _install_genai_stub(monkeypatch, captured,
                        response=types.SimpleNamespace(candidates=[]))
    provider = GoogleProvider(api_key=FAKE_KEY)
    with pytest.raises(ProviderError):
        provider.chat([{"role": "user", "content": "Hi"}])


# ----------------------------------------------------------------------
# (d) role mapping: assistant->model; tool transcripts degrade (documented)
# ----------------------------------------------------------------------

def test_assistant_maps_to_model_role():
    _, contents = _gemini_contents([
        {"role": "assistant", "content": "prev"},
        {"role": "user", "content": "hi"},
    ])
    assert [c["role"] for c in contents] == ["model", "user"]


def test_tool_transcript_degrades_to_user_text():
    _, contents = _gemini_contents([
        {"role": "user", "content": "run it"},
        {"role": "tool", "content": "tool output here"},
    ])
    assert contents[1] == {"role": "user", "parts": ["tool output here"]}


def test_tool_degradation_reaches_sdk_call(monkeypatch):
    captured = {}
    _install_genai_stub(monkeypatch, captured,
                        response=_text_response("ok"))
    provider = GoogleProvider(api_key=FAKE_KEY)
    provider.chat([
        {"role": "user", "content": "run it"},
        {"role": "tool", "content": "tool output here"},
    ])
    contents = captured["contents"]
    assert contents[1]["role"] == "user"
    assert contents[1]["parts"] == ["tool output here"]


def test_unknown_roles_also_degrade_to_user():
    _, contents = _gemini_contents([{"role": "developer", "content": "x"}])
    assert contents == [{"role": "user", "parts": ["x"]}]


# ----------------------------------------------------------------------
# (e) system_instruction present when given, absent when not
# ----------------------------------------------------------------------

def test_system_instruction_passed_through_when_present(monkeypatch):
    captured = {}
    _install_genai_stub(monkeypatch, captured,
                        response=_text_response("ok"))
    provider = GoogleProvider(api_key=FAKE_KEY)
    provider.chat([
        {"role": "system", "content": "be terse"},
        {"role": "system", "content": "be kind"},
        {"role": "user", "content": "hi"},
    ])
    assert captured["model_kwargs"]["system_instruction"] == "be terse\n\nbe kind"


def test_system_instruction_absent_when_no_system_block(monkeypatch):
    captured = {}
    _install_genai_stub(monkeypatch, captured,
                        response=_text_response("ok"))
    provider = GoogleProvider(api_key=FAKE_KEY)
    provider.chat([{"role": "user", "content": "hi"}])
    assert "system_instruction" not in captured["model_kwargs"]


# ----------------------------------------------------------------------
# (f) genai.configure called with the key exactly once per chat
# ----------------------------------------------------------------------

def test_configure_called_exactly_once_with_key(monkeypatch):
    captured = {}
    _install_genai_stub(monkeypatch, captured,
                        response=_text_response("ok"))
    provider = GoogleProvider(api_key=FAKE_KEY)
    provider.chat([{"role": "user", "content": "Hi"}])
    assert captured["configure_calls"] == [{"api_key": FAKE_KEY}]


def test_configure_not_called_when_sdk_absent(monkeypatch):
    _hide_sdk(monkeypatch)
    provider = GoogleProvider(api_key=FAKE_KEY)
    with pytest.raises(ProviderNotConfigured):
        provider.chat([{"role": "user", "content": "Hi"}])


# ----------------------------------------------------------------------
# exception mapping + (g) redaction: no key material in any error text
# ----------------------------------------------------------------------

def test_auth_error_maps_without_key_material(monkeypatch):
    captured = {}
    child = _install_genai_stub(monkeypatch, captured,
                               response=_text_response("ok"))
    provider = GoogleProvider(api_key=FAKE_KEY)
    sdk_error = child.AuthenticationError(f"API key not valid: {FAKE_KEY}")
    monkeypatch.setattr(provider, "_send", _boom(sdk_error))
    with pytest.raises(GoogleAuthError) as exc:
        provider.chat([{"role": "user", "content": "Hi"}])
    assert isinstance(exc.value, ProviderError)
    assert FAKE_KEY not in str(exc.value)


def test_rate_limit_maps_without_key_material(monkeypatch):
    captured = {}
    child = _install_genai_stub(monkeypatch, captured,
                               response=_text_response("ok"))
    provider = GoogleProvider(api_key=FAKE_KEY)
    monkeypatch.setattr(provider, "_send", _boom(child.RateLimitError("429")))
    with pytest.raises(GoogleRateLimitError) as exc:
        provider.chat([{"role": "user", "content": "Hi"}])
    assert isinstance(exc.value, ProviderError)
    assert FAKE_KEY not in str(exc.value)


def test_generic_error_maps_without_key_material(monkeypatch):
    captured = {}
    _install_genai_stub(monkeypatch, captured,
                        response=_text_response("ok"))
    provider = GoogleProvider(api_key=FAKE_KEY)
    monkeypatch.setattr(
        provider, "_send", _boom(Exception(f"weird failure {FAKE_KEY}")))
    with pytest.raises(ProviderError) as exc:
        provider.chat([{"role": "user", "content": "Hi"}])
    assert FAKE_KEY not in str(exc.value)


def test_name_based_mapping_without_status_code():
    class OddApiKeyBlast(Exception):
        pass

    assert isinstance(_map_genai_error(OddApiKeyBlast("x")), GoogleAuthError)

    class StrangeHiccup(Exception):
        pass

    assert type(_map_genai_error(StrangeHiccup("x"))) is ProviderError


def test_no_key_material_in_any_failure_path(monkeypatch):
    """Every failure path with a keyed provider must stay redacted."""
    captured = {}
    _install_genai_stub(monkeypatch, captured,
                        response=_SafetyBlockedResponse())
    provider = GoogleProvider(api_key=FAKE_KEY)
    messages = []
    try:
        provider.chat([{"role": "user", "content": "Hi"}])
    except ProviderError as exc:
        messages.append(str(exc))
    provider.model = ""
    try:
        provider.chat([{"role": "user", "content": "Hi"}])
    except ProviderError as exc:
        messages.append(str(exc))
    try:
        provider.chat([])
    except ProviderError as exc:
        messages.append(str(exc))
    assert messages, "expected failures to exercise"
    assert all(FAKE_KEY not in message for message in messages)


# ----------------------------------------------------------------------
# model override via kwargs; empty model raises
# ----------------------------------------------------------------------

def test_model_override_via_kwargs(monkeypatch):
    captured = {}
    _install_genai_stub(monkeypatch, captured,
                        response=_text_response("ok"))
    provider = GoogleProvider(api_key=FAKE_KEY)
    provider.chat([{"role": "user", "content": "hi"}], model="gemini-custom-1")
    assert captured["model_name"] == "gemini-custom-1"


def test_empty_model_raises_provider_error(monkeypatch):
    captured = {}
    _install_genai_stub(monkeypatch, captured,
                        response=_text_response("ok"))
    provider = GoogleProvider(api_key=FAKE_KEY)
    provider.model = ""
    with pytest.raises(ProviderError):
        provider.chat([{"role": "user", "content": "hi"}])
