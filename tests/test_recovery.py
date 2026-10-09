"""Tests for mythic_agent.agents.recovery (Slice 20)."""

from pathlib import Path

import pytest

from mythic_agent.agents.recovery import (
    RecoveryStrategy,
    analyze_failure,
    suggest_fix,
)


def test_missing_file_triggers_fix_path():
    err = FileNotFoundError("[Errno 2] No such file or directory: 'x.py'")
    assert analyze_failure("read_file", {"path": "x.py"}, err) is RecoveryStrategy.FIX_PATH


def test_missing_file_message_text_triggers_fix_path():
    assert analyze_failure("read_file", {"path": "mian.py"},
                           "ENOENT: no such file 'mian.py'") is RecoveryStrategy.FIX_PATH


def test_permission_error_triggers_abort():
    assert analyze_failure("write_file", {"path": "/root/x"},
                           PermissionError("Permission denied")) is RecoveryStrategy.ABORT


def test_permission_text_triggers_abort():
    assert analyze_failure("run_command", {"command": "rm /"},
                           "operation not permitted") is RecoveryStrategy.ABORT


def test_timeout_triggers_retry():
    assert analyze_failure("run_command", {"command": "sleep 99"},
                           TimeoutError("timed out")) is RecoveryStrategy.RETRY
    assert analyze_failure("run_command", {"command": "x"},
                           "resource temporarily unavailable") is RecoveryStrategy.RETRY


def test_bad_arguments_trigger_try_alternative():
    assert analyze_failure("grep_search", {"path": "x", "query": "("},
                           ValueError("unterminated group")) is RecoveryStrategy.TRY_ALTERNATIVE
    assert analyze_failure("frobnicate", {}, "unknown tool") is RecoveryStrategy.TRY_ALTERNATIVE


def test_nonexistent_path_heuristic(tmp_path: Path):
    # A path-like arg that does not exist is treated as fixable.
    strategy = analyze_failure("read_file", {"path": str(tmp_path / "typo.py")}, "boom")
    assert strategy is RecoveryStrategy.FIX_PATH


def test_suggest_fix_repairs_mistyped_path(tmp_path: Path):
    target = tmp_path / "mythic_report.md"
    target.write_text("report\n")
    fixed = suggest_fix("read_file", {"path": "mythic_repot.md"},
                        FileNotFoundError("no such file"), root=tmp_path)
    assert fixed is not None
    assert fixed["path"] == str(target)
    assert "_recovery_note" in fixed


def test_suggest_fix_returns_none_for_non_path_failures():
    fixed = suggest_fix("write_file", {"path": "x"},
                        PermissionError("denied"), root=".")
    assert fixed is None


def test_suggest_fix_returns_none_without_matches(tmp_path: Path):
    fixed = suggest_fix("read_file", {"path": "zzz_nope_qqq.txt"},
                        FileNotFoundError("no such file"), root=tmp_path)
    assert fixed is None


def test_suggest_fix_lists_alternatives(tmp_path: Path):
    (tmp_path / "database_alpha.yaml").write_text("a")
    (tmp_path / "database_beta.yaml").write_text("b")
    fixed = suggest_fix("read_file", {"path": "datbase.yaml"},
                        FileNotFoundError("no such file"), root=tmp_path)
    assert fixed is not None
    assert fixed["path"] in (
        str(tmp_path / "database_alpha.yaml"),
        str(tmp_path / "database_beta.yaml"),
    )
    assert "_alternatives" in fixed


def test_recovery_strategy_enum_values():
    assert RecoveryStrategy.RETRY.value == "retry"
    assert RecoveryStrategy.FIX_PATH.value == "fix_path"
    assert RecoveryStrategy.TRY_ALTERNATIVE.value == "try_alternative"
    assert RecoveryStrategy.ABORT.value == "abort"
