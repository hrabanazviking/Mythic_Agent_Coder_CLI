"""Credential-free launch and resource contracts, safe in core-only installs."""

import subprocess
import sys

from mythic_agent.resources import character_directory, engineering_protocol


def test_cli_import_has_no_bootstrap_side_effects():
    code = (
        "import sys; import mythic_agent.cli; "
        "assert 'mythic_agent.agents.llm' not in sys.modules; "
        "assert 'mythic_agent.core.config_manager' not in sys.modules; "
        "assert 'textual' not in sys.modules; assert 'torch' not in sys.modules"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True)
    assert result.returncode == 0, result.stderr.decode()


def test_help_and_version_do_not_require_tui_or_credentials():
    for flag, expected in [("--help", "coding harness"), ("--version", "0.1.0")]:
        result = subprocess.run(
            [sys.executable, "-m", "mythic_agent.cli", flag],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, result.stderr
        assert expected in result.stdout
        assert not result.stderr


def test_resources_are_present():
    assert len(list(character_directory().glob("*.md"))) == 9
    assert "Mythic Engineering" in engineering_protocol()
