"""R-024 / roadmap 024 — Coverage Gap Assault.

TIER: integration

Covers the lowest-covered stable lines in mythic_agent/providers and installs
a coverage ratchet: the providers package must not drop below the measured
baseline recorded in docs/COVERAGE_BASELINE.md.
"""

import pytest

from mythic_agent.providers.ollama import OllamaProvider

# Measured 2026-10-10 dusk forge (R-024 commit) with coverage 7.16.2 over
# tests/test_providers.py, test_provider_protocol.py,
# test_provider_adapters.py, test_anthropic_hardening.py,
# test_redaction_audit.py. In-flight worker code (base.py, google.py,
# openai_compat.py) is mid-edit; the ratchet below covers the package as a
# whole so worker landings can only raise it.
BASELINE_TOTAL_PCT = 63.0


def test_ollama_options_passthrough_covered():
    """ollama.py:51 — options kwarg reaches the /api/chat payload."""
    seen = {}

    def fake_post(path, payload):
        seen["path"] = path
        seen["payload"] = payload
        return {"message": {"content": "hello"}}

    provider = OllamaProvider(model="llama3.1")
    provider._post = fake_post
    assert provider.chat([{"role": "user", "content": "hi"}], options={"temperature": 0.1}) == "hello"
    assert seen["path"] == "/api/chat"
    assert seen["payload"]["options"] == {"temperature": 0.1}
    assert seen["payload"]["stream"] is False


def test_ollama_empty_message_content_normalized():
    provider = OllamaProvider(model="llama3.1")
    seen = {}

    def fake_post(path, payload):
        seen["payload"] = payload
        return {"message": {"content": "ok"}}

    provider._post = fake_post
    provider.chat([{"role": "user"}])  # missing content -> ""
    assert seen["payload"]["messages"] == [{"role": "user", "content": ""}]


def test_providers_coverage_ratchet():
    """The providers package must not drop below the recorded baseline.

    Runs coverage in a SUBPROCESS (in-process measurement undercounts
    import-time lines) with exactly the methodology from
    docs/COVERAGE_BASELINE.md.
    """
    import os
    import re
    import subprocess
    import sys

    test_files = [
        "tests/test_providers.py",
        "tests/test_provider_protocol.py",
        "tests/test_provider_adapters.py",
        "tests/test_anthropic_hardening.py",
        "tests/test_redaction_audit.py",
        "tests/test_local_provider_adapters.py",
        # Forge 041-050 (dusk 2026-10-11): negotiation/normalization modules.
        "tests/test_structured_output.py",
        "tests/test_vision_negotiation.py",
        "tests/test_reasoning_negotiation.py",
        "tests/test_streaming_normalization.py",
        "tests/test_usage_normalization.py",
        "tests/test_cost_ledger.py",
        "tests/test_provider_health.py",
        "tests/test_provider_failover.py",
        "tests/test_provider_conformance.py",
        "tests/test_coverage_assault.py::test_ollama_options_passthrough_covered",
        "tests/test_coverage_assault.py::test_ollama_empty_message_content_normalized",
    ]
    env = dict(os.environ)
    env["COVERAGE_FILE"] = os.path.join(os.getcwd(), ".coverage.ratchet")
    run = subprocess.run(
        [sys.executable, "-m", "coverage", "run", "--source=mythic_agent/providers",
         "-m", "pytest", "-q", "-p", "no:cacheprovider", *test_files],
        capture_output=True, text=True, cwd=os.getcwd(), env=env, timeout=300,
    )
    report = subprocess.run(
        [sys.executable, "-m", "coverage", "report",
         "--include=mythic_agent/providers/*", "--data-file=./.coverage.ratchet"],
        capture_output=True, text=True, cwd=os.getcwd(), env=env, timeout=120,
    )
    try:
        os.unlink(os.path.join(os.getcwd(), ".coverage.ratchet"))
    except OSError:
        pass
    match = re.search(r"^TOTAL\s+\d+\s+\d+\s+([\d.]+)%", report.stdout, re.M)
    assert match, f"could not parse coverage report:\n{report.stdout}\n{report.stderr}"
    total = float(match.group(1))
    assert total >= BASELINE_TOTAL_PCT, (
        f"providers coverage {total:.1f}% below baseline {BASELINE_TOTAL_PCT}%\n"
        + report.stdout
    )


def test_baseline_doc_matches_code():
    import pathlib

    doc = pathlib.Path("docs/COVERAGE_BASELINE.md").read_text()
    assert f"{BASELINE_TOTAL_PCT:.0f}%" in doc
