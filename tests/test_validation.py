"""SLICE 14: schema validation, path sandboxing, secrets audit."""

import pytest

from mythic_agent.core.secrets_audit import (
    audit_report,
    count_by_kind,
    has_secrets,
    mask_text,
    scan_mapping,
    scan_secrets,
)
from mythic_agent.core.validation import (
    SecurityError,
    ValidationError,
    sandbox_path,
    validate_tool_args,
)


# --- schema validation -----------------------------------------------------


def test_valid_read_file_args_pass():
    result = validate_tool_args("read_file", {"path": "notes/todo.md"})
    assert result == {"path": "notes/todo.md"}


def test_valid_write_file_args_pass():
    result = validate_tool_args(
        "write_file", {"path": "out.txt", "content": "hello"}
    )
    assert result["content"] == "hello"


def test_valid_nested_delegation_args_pass():
    args = {
        "delegations": [
            {"sub_agent_name": "scribe", "task_description": "summarize"},
            {"sub_agent_name": "skald", "task_description": "read"},
        ]
    }
    assert validate_tool_args("delegate_parallel_tasks", args) == args


def test_unknown_tool_rejected():
    with pytest.raises(ValidationError, match="Unknown tool"):
        validate_tool_args("delete_everything", {})


def test_missing_required_argument_rejected_with_clear_message():
    with pytest.raises(ValidationError) as excinfo:
        validate_tool_args("write_file", {"path": "out.txt"})
    message = str(excinfo.value)
    assert "content" in message and "missing required" in message


def test_wrong_type_rejected_with_clear_message():
    with pytest.raises(ValidationError) as excinfo:
        validate_tool_args("read_file", {"path": 42})
    message = str(excinfo.value)
    assert "path" in message and "string" in message and "integer" in message


def test_unknown_argument_rejected():
    with pytest.raises(ValidationError, match="unknown argument"):
        validate_tool_args("read_file", {"path": "a.txt", "bogus": 1})


def test_enum_violation_lists_allowed_values():
    with pytest.raises(ValidationError) as excinfo:
        validate_tool_args("core_memory_append", {"block": "nope", "content": "x"})
    message = str(excinfo.value)
    assert "persona" in message and "long_term_notes" in message


def test_nested_array_item_validated():
    with pytest.raises(ValidationError) as excinfo:
        validate_tool_args(
            "delegate_parallel_tasks",
            {"delegations": [{"sub_agent_name": "scribe"}]},
        )
    message = str(excinfo.value)
    assert "delegations[0]" in message and "task_description" in message


def test_non_object_arguments_rejected():
    with pytest.raises(ValidationError, match="must be an object"):
        validate_tool_args("read_file", ["path"])


def test_bool_is_not_an_integer():
    # knowledge_db_semantic_search.limit is integer; True must not pass.
    with pytest.raises(ValidationError, match="integer"):
        validate_tool_args("knowledge_db_semantic_search", {"query": "x", "limit": True})


# --- path sandboxing -------------------------------------------------------


def test_path_traversal_blocked(tmp_path):
    with pytest.raises(SecurityError, match="outside the workspace"):
        validate_tool_args("read_file", {"path": "../secret.txt"}, workspace=tmp_path)


def test_absolute_path_outside_workspace_blocked(tmp_path):
    with pytest.raises(SecurityError):
        validate_tool_args(
            "write_file",
            {"path": "/etc/passwd", "content": "x"},
            workspace=tmp_path,
        )


def test_symlink_escape_blocked(tmp_path):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("top secret")
    link = workspace / "link.txt"
    link.symlink_to(outside)
    with pytest.raises(SecurityError, match="outside the workspace"):
        validate_tool_args("read_file", {"path": "link.txt"}, workspace=workspace)


def test_write_to_git_metadata_blocked(tmp_path):
    with pytest.raises(SecurityError):
        validate_tool_args(
            "write_file",
            {"path": ".git/hooks/evil", "content": "x"},
            workspace=tmp_path,
        )


def test_in_workspace_path_allowed(tmp_path):
    resolved = sandbox_path(tmp_path, "sub/dir/file.txt")
    assert str(resolved).startswith(str(tmp_path.resolve()))


# --- secrets audit ---------------------------------------------------------


def test_openai_key_detected():
    findings = scan_secrets("key=sk-proj-abcdefghij1234567890XYZ")
    assert any(f.kind == "openai_key" for f in findings)


def test_github_token_detected():
    findings = scan_secrets("token ghp_abcdefghij1234567890abcdefghij12 here")
    assert any(f.kind == "github_token" for f in findings)


def test_aws_keys_detected():
    findings = scan_secrets("AKIAIOSFODNN7EXAMPLE and aws_secret = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
    kinds = {f.kind for f in findings}
    assert "aws_access_key" in kinds and "aws_secret_key" in kinds


def test_private_key_header_detected():
    findings = scan_secrets("-----BEGIN RSA PRIVATE KEY-----\nMIIE...")
    assert any(f.kind == "private_key" for f in findings)


def test_bearer_token_detected():
    findings = scan_secrets("Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
    assert any(f.kind == "bearer_token" for f in findings)


def test_clean_text_has_no_findings():
    text = "The raven flies over the fjord at dawn, carrying no secrets at all."
    assert scan_secrets(text) == []
    assert not has_secrets(text)


def test_findings_never_carry_raw_secret():
    secret = "sk-proj-abcdefghij1234567890XYZ"
    findings = scan_secrets(f"leaked {secret} oops")
    assert findings and all(secret not in (f.preview, f.kind) for f in findings)
    assert "..." in findings[0].preview


def test_mask_text_redacts_without_leaking_positions():
    secret = "ghp_abcdefghij1234567890abcdefghij12"
    masked = mask_text(f"prefix {secret} suffix")
    assert secret not in masked
    assert masked == "prefix [REDACTED] suffix"


def test_audit_report_is_log_safe():
    secret = "sk-ant-abcdefghij1234567890wxyz"
    report = audit_report(f"oops {secret}")
    assert report["findings"] == 1
    assert report["kinds"] == {"anthropic_key": 1}
    assert secret not in str(report)


def test_scan_mapping_scans_string_values_only():
    result = scan_mapping({"a": "clean", "b": "xoxb-123456789012-abcdef", "c": 42})
    assert set(result) == {"b"}
    assert result["b"][0].kind == "slack_token"


def test_count_by_kind_tallies():
    findings = scan_secrets("sk-proj-abcdefghij1234567890XYZ and sk-proj-ZYX9876543210wvu-tsrq")
    assert count_by_kind(findings) == {"openai_key": 2}


# --- execute_tool integration ----------------------------------------------


def test_execute_tool_rejects_invalid_args_before_running(tmp_path):
    from mythic_agent.agents.tools import execute_tool

    result = execute_tool("write_file", {"path": "x.txt"}, project_root=tmp_path)
    assert result.startswith("Error:")
    assert "content" in result  # clear message names the missing argument


def test_execute_tool_blocks_traversal_before_policy(tmp_path):
    from mythic_agent.agents.tools import execute_tool

    result = execute_tool("read_file", {"path": "../outside.txt"}, project_root=tmp_path)
    assert result.startswith("Error:")
    assert "outside the workspace" in result


def test_execute_tool_unknown_tool_returns_error(tmp_path):
    from mythic_agent.agents.tools import execute_tool

    result = execute_tool("nope", {}, project_root=tmp_path)
    assert result.startswith("Error: Unknown tool")


def test_execute_tool_still_runs_valid_read(tmp_path):
    from mythic_agent.agents.tools import execute_tool

    target = tmp_path / "hello.txt"
    target.write_text("waves crash")
    result = execute_tool("read_file", {"path": "hello.txt"}, project_root=tmp_path)
    assert result == "waves crash"
