"""R-021 / roadmap 021 — Secret Redaction Audit: adversarial gate tests.

Proves that credential material cannot escape through the paths this slice
owns: the pattern scanner, the redactor, config/session/journal exports, the
logging factory, and provider __repr__. Raw SDK exception passthrough in the
anthropic/google adapters is a documented audit finding owned by R-029/R-030;
here we prove the defense-in-depth layer (redact_text) neutralizes it.
"""

import logging

import pytest

from mythic_agent.core.redaction import SecretRedactor, protect_logging, redact_text
from mythic_agent.core.secrets_audit import (
    audit_report,
    has_secrets,
    mask_text,
    scan_secrets,
)
from mythic_agent.providers.registry import get_provider, list_providers

FAKE_ANTHROPIC_KEY = "sk-ant-" + "F" * 40
FAKE_GOOGLE_KEY = "AIza" + "G" * 35
FAKE_OPENAI_KEY = "sk-" + "H" * 48
FAKE_XAI_KEY = "xai-" + "J" * 24


# --- pattern scanner: every known kind is detected and masked -------------

@pytest.mark.parametrize(
    "kind,secret",
    [
        ("openai_key", FAKE_OPENAI_KEY),
        ("anthropic_key", FAKE_ANTHROPIC_KEY),
        ("google_api_key", FAKE_GOOGLE_KEY),
        ("xai_key", FAKE_XAI_KEY),
        ("github_token", "ghp_" + "K" * 36),
        ("stripe_key", "sk_live_" + "L" * 24),
        ("slack_token", "xoxb-123456789012-" + "M" * 24),
        ("bearer_token", "Bearer " + "N" * 32),
        ("private_key", "-----BEGIN RSA PRIVATE KEY-----"),
    ],
)
def test_scanner_detects_and_masks_every_kind(kind, secret):
    text = f"prefix {secret} suffix"
    assert has_secrets(text)
    findings = scan_secrets(text)
    assert findings, f"no finding for {kind}"
    assert findings[0].kind == kind
    masked = mask_text(text)
    assert secret not in masked
    assert "[REDACTED]" in masked


def test_scanner_preview_never_carries_raw_secret():
    report = audit_report(f"leaked={FAKE_ANTHROPIC_KEY} and {FAKE_GOOGLE_KEY}")
    assert report["findings"] == 2
    for preview in report["previews"]:
        assert FAKE_ANTHROPIC_KEY not in preview["preview"]
        assert FAKE_GOOGLE_KEY not in preview["preview"]


def test_scanner_ignores_benign_text():
    assert not has_secrets("the api key is stored in the vault, see docs")
    assert mask_text("no secrets here") == "no secrets here"


# --- redactor: key-name variants are collected ------------------------------

def test_redactor_collects_credential_key_variants():
    redactor = SecretRedactor(
        {
            "client_secret": "cs-1",
            "nested": {"access_token": "tok-2", "auth_token": "tok-3"},
            "deep": {"refresh_token": "tok-4", "private_key": "pk-5"},
            "plain": "visible",
        }
    )
    cleaned = redactor.sanitize(
        {
            "client_secret": "cs-1",
            "nested": {"access_token": "tok-2"},
            "plain": "visible",
        }
    )
    assert cleaned["client_secret"] == "[REDACTED]"
    assert cleaned["nested"]["access_token"] == "[REDACTED]"
    assert cleaned["plain"] == "visible"
    assert "cs-1" not in redactor.text("value cs-1 here")


def test_redact_text_masks_url_credentials_and_env_style_keys(monkeypatch):
    monkeypatch.setenv("MYTHIC_AUDIT_API_KEY", FAKE_OPENAI_KEY)
    redactor = SecretRedactor({})
    assert FAKE_OPENAI_KEY in redactor.secrets  # env-sourced
    out = redactor.text(f"db https://user:{FAKE_OPENAI_KEY}@host/x q={FAKE_OPENAI_KEY}")
    assert FAKE_OPENAI_KEY not in out
    assert "user:" not in out


# --- defense in depth: a leaked SDK-style error is neutralized --------------

def test_redact_text_neutralizes_raw_sdk_error_text():
    # Audit finding (R-029/R-030 own the adapter fix): raw SDK exceptions can
    # propagate with key material in their text. The redaction layer must
    # neutralize such text wherever the doctor/CLI applies it.
    raw = f"RuntimeError: auth failed for key={FAKE_ANTHROPIC_KEY}"
    cleaned = redact_text(raw)
    assert FAKE_ANTHROPIC_KEY not in cleaned
    assert "[REDACTED]" in cleaned


def test_protect_logging_factory_redacts_records(caplog):
    redactor = SecretRedactor({"api_key": FAKE_XAI_KEY})
    protect_logging(redactor)
    logger = logging.getLogger("mythic.redaction.audit")
    with caplog.at_level(logging.ERROR, logger="mythic.redaction.audit"):
        logger.error("provider blew up: %s", FAKE_XAI_KEY)
    assert FAKE_XAI_KEY not in caplog.text
    assert "[REDACTED]" in caplog.text


# --- provider surface: repr and exports never carry keys --------------------

@pytest.mark.parametrize("name", list_providers())
def test_provider_repr_never_contains_api_key(name):
    provider = get_provider(name, api_key=FAKE_OPENAI_KEY)
    assert FAKE_OPENAI_KEY not in repr(provider)


def test_session_export_redacts_pasted_secrets(tmp_path):
    from mythic_agent.core.sessions import SessionStore

    redactor = SecretRedactor({"api_key": FAKE_GOOGLE_KEY})
    store = SessionStore(tmp_path, tmp_path / "state", redactor)
    session_id = store.create(
        [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": f"pasted {FAKE_GOOGLE_KEY} here"},
        ],
        {"note": "plain"},
    )
    exported = store.export(session_id)
    assert FAKE_GOOGLE_KEY not in str(exported)


def test_crash_report_redacts_with_redactor(tmp_path):
    from mythic_agent.core.journal import write_crash_report

    redactor = SecretRedactor({"token": FAKE_XAI_KEY})
    try:
        raise RuntimeError(f"provider failed with token {FAKE_XAI_KEY} inline")
    except RuntimeError as exc:
        path = write_crash_report(exc, mythic_dir=tmp_path, redactor=redactor)
    assert FAKE_XAI_KEY not in path.read_text()
