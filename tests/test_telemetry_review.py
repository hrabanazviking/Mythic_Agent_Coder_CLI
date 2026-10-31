"""
TIER: unit
Telemetry Honesty Review gate (All-Features roadmap slice M-015).

The shipped review (``mythic_agent/data/telemetry_review.yaml``)
records what the app records today (metrics, costs, audit, journal,
sessions, logs, cache, memory), every channel through which
information can leave the machine at all, the telemetry systems it
does not have, and the rule that it never phones home. These tests
cross-check the review against the live tree: every owner module it
names must exist and carry the destination/endpoint strings it
cites; the package source must contain no known telemetry library
or endpoint; the OpenRouter identification headers the review
discloses must be the provider's real defaults; and the webhook
channel must really be opt-in (empty by default).
"""

import copy
import re
from pathlib import Path

import pytest

from mythic_agent.core.telemetry_review import (
    NEVER_PHONES_HOME,
    TRIGGERS,
    TelemetryReview,
    load_review,
    render_markdown,
    validate_review,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.providers.openrouter import (
    DEFAULT_HTTP_REFERER,
    DEFAULT_X_TITLE,
)
from mythic_agent.resources import load_resource

REPO_ROOT = Path(__file__).resolve().parent.parent
PKG_DIR = REPO_ROOT / "mythic_agent"

# Known telemetry/analytics libraries and endpoints: none may appear
# in the package source (imports or endpoint strings).
FORBIDDEN_TELEMETRY = (
    "sentry_sdk",
    "sentry.io",
    "posthog",
    "segment.io",
    "segment.com",
    "mixpanel",
    "amplitude.com",
    "google-analytics",
    "googletagmanager",
    "fullstory",
    "hotjar",
)


@pytest.fixture(scope="module")
def review() -> TelemetryReview:
    return load_review()


def _package_source() -> str:
    parts = []
    for path in sorted(PKG_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        parts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts).lower()


def test_shipped_review_loads_and_validates(review):
    assert isinstance(review, TelemetryReview)
    assert validate_review(load_resource("telemetry_review.yaml")) == []
    assert review.counts() == (10, 6, 5, 6)


def test_every_recording_stays_local(review):
    assert review.recorded_ids() == tuple(
        f"R-{n:02d}" for n in range(1, 11))
    for item in review.recorded_items:
        assert item.leaves_machine is False, item.id
        assert item.destination_kind in ("local-file", "in-memory"), item.id
        dest = item.destination.lower()
        assert ".mythic" in dest or "memory" in dest or "stderr" in dest \
            or "spill" in dest, item.id


def test_every_channel_is_user_driven(review):
    assert review.channel_ids() == tuple(f"O-{n:02d}" for n in range(1, 7))
    for channel in review.outbound_channels:
        assert channel.trigger in TRIGGERS, channel.id
        assert channel.trigger not in ("background", "automatic"), channel.id


def test_never_phones_home_rule_is_verbatim(review):
    assert NEVER_PHONES_HOME in review.rule_texts()
    assert review.rules[0].rule == NEVER_PHONES_HOME


def test_owner_modules_exist_and_carry_the_cited_strings(review):
    cited = {
        "mythic_agent/core/costs.py": "costs.json",
        "mythic_agent/providers/cost_ledger.py": "cost_ledger.json",
        "mythic_agent/core/audit.py": "audit.jsonl",
        "mythic_agent/core/sessions.py": "sessions.sqlite",
        "mythic_agent/core/journal.py": "crashes",
        "mythic_agent/core/cache.py": "cache",
    }
    owners = {i.owner_module for i in review.recorded_items} | {
        c.owner_module for c in review.outbound_channels}
    for owner in owners:
        assert (REPO_ROOT / owner).is_file(), owner
    for rel, needle in cited.items():
        assert needle in (REPO_ROOT / rel).read_text(encoding="utf-8"), rel
    cli_text = (REPO_ROOT / "mythic_agent/cli.py").read_text(encoding="utf-8")
    assert "metrics.json" in cli_text


def test_no_telemetry_library_or_endpoint_in_package_source():
    source = _package_source()
    for needle in FORBIDDEN_TELEMETRY:
        assert needle not in source, needle
    # no update/version phone-home endpoint either
    assert "pypi.org/pypi" not in source
    assert not re.search(r"check_for_updates|check_update\(\)", source)


def test_openrouter_identification_is_disclosed_accurately(review):
    provider_channel = review.outbound_channels[0]
    assert provider_channel.id == "O-01"
    assert DEFAULT_HTTP_REFERER in provider_channel.sends
    assert DEFAULT_X_TITLE in provider_channel.sends
    assert DEFAULT_HTTP_REFERER == (
        "https://github.com/hrabanazviking/Mythic_Agent_Coder_CLI")


def test_webhook_channel_is_opt_in_by_default(review):
    webhook = [c for c in review.outbound_channels if c.id == "O-05"][0]
    assert webhook.trigger == "user-configured"
    module = (PKG_DIR / "core/notifications.py").read_text(encoding="utf-8")
    assert "No network traffic happens unless" in module
    assert "webhook_url" in module


def test_absent_systems_cover_the_honesty_core(review):
    names = " ".join(review.absent_names()).lower()
    for concept in ("analytics", "crash", "update", "beacon", "tracker"):
        assert concept in names, concept


def test_render_covers_every_entry(review):
    text = render_markdown(review)
    for item in review.recorded_items:
        assert item.id in text and item.destination in text
    for channel in review.outbound_channels:
        assert channel.id in text and channel.sends in text
    for name in review.absent_names():
        assert name in text
    for rule_text in review.rule_texts():
        assert rule_text in text


def _tampered(mutator):
    data = copy.deepcopy(load_resource("telemetry_review.yaml"))
    mutator(data)
    return data


def test_validation_rejects_a_recording_that_leaves():
    data = _tampered(lambda d: d["recorded_items"][0].update(
        leaves_machine=True))
    problems = validate_review(data)
    assert any("leaves_machine" in p for p in problems)
    with pytest.raises(ValidationError):
        load_review(data)


def test_validation_rejects_a_background_channel():
    data = _tampered(lambda d: d["outbound_channels"][0].update(
        trigger="background"))
    problems = validate_review(data)
    assert any("never phones home" in p or "trigger" in p for p in problems)
    with pytest.raises(ValidationError):
        load_review(data)


def test_validation_rejects_dropping_the_never_phones_home_rule():
    data = _tampered(lambda d: d["rules"][0].update(
        rule="phones home sometimes, politely"))
    problems = validate_review(data)
    assert any("never-phones-home" in p for p in problems)


def test_validation_rejects_a_remote_recording_destination():
    data = _tampered(lambda d: d["recorded_items"][1].update(
        destination_kind="remote-server"))
    problems = validate_review(data)
    assert any("destination_kind" in p for p in problems)
