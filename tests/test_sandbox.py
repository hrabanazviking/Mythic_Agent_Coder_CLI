"""Slice 45: execution sandboxing."""

import pytest

from mythic_agent.core.sandbox import Sandbox, SandboxError, SandboxResult


def test_run_safe_command():
    sb = Sandbox()
    result = sb.run("echo hello", cwd="/tmp")
    assert isinstance(result, SandboxResult)
    assert result.returncode == 0
    assert "hello" in result.stdout
    assert result.ok


def test_run_command_in_cwd():
    sb = Sandbox()
    result = sb.run("pwd", cwd="/tmp")
    assert result.ok
    assert "/tmp" in result.stdout.strip()


def test_run_failed_command_captured():
    sb = Sandbox()
    result = sb.run("false", cwd="/tmp")
    assert not result.ok
    assert result.returncode != 0


def test_denylist_refuses_rm_rf_root():
    sb = Sandbox()
    with pytest.raises(SandboxError):
        sb.run("rm -rf /", cwd="/tmp")


def test_denylist_refuses_mkfs():
    sb = Sandbox()
    with pytest.raises(SandboxError):
        sb.run("mkfs.ext4 /dev/sda1", cwd="/tmp")


def test_denylist_refuses_fork_bomb():
    sb = Sandbox()
    with pytest.raises(SandboxError):
        sb.run(":(){ :|:& };:", cwd="/tmp")


def test_check_denied_reason():
    sb = Sandbox()
    assert sb.check_denied("echo ok") is None
    reason = sb.check_denied("dd if=/dev/zero of=/dev/sda")
    assert reason is not None and "dd" in reason


def test_empty_command_rejected():
    sb = Sandbox()
    with pytest.raises(SandboxError):
        sb.run("   ", cwd="/tmp")


def test_timeout_kills_command():
    sb = Sandbox(timeout=0.5)
    result = sb.run("sleep 3", cwd="/tmp")
    assert result.timed_out
    assert not result.ok
    assert result.duration_s < 3


def test_memory_limit_applied_when_generous():
    sb = Sandbox(memory_limit_mb=2048)
    result = sb.run("echo capped", cwd="/tmp")
    assert result.ok
    assert "capped" in result.stdout


def test_dry_run_does_not_execute(tmp_path):
    sb = Sandbox()
    marker = tmp_path / "should-not-exist.txt"
    text = sb.dry_run(f"touch {marker}")
    assert "Would run" in text
    assert not marker.exists()


def test_dry_run_refuses_dangerous():
    sb = Sandbox()
    text = sb.dry_run("rm -rf /")
    assert text.startswith("REFUSED")


def test_dry_run_explains_stages():
    sb = Sandbox()
    text = sb.dry_run("ls -la | grep py")
    assert "list directory contents" in text
    assert "search text for a pattern" in text


def test_render_output():
    sb = Sandbox()
    result = sb.run("echo hi", cwd="/tmp")
    text = result.render()
    assert "$ echo hi" in text
    assert "hi" in text
    assert "exit 0" in text
