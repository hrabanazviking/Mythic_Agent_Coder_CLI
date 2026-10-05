"""Durable checkpoints, process leases, protocol recovery and redacted exports."""

import json
import logging
import os
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from mythic_agent.core.redaction import SecretRedactor, protect_logging
from mythic_agent.core.sessions import SessionBusy, SessionStore, validate_messages
from mythic_agent.core.runtime import TurnCancelled


def store_for(tmp_path, workspace=None, redactor=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state", redactor)


def messages():
    return [{"role": "system", "content": "Fixture system"}, {"role": "user", "content": "hello"}]


def pending_context():
    return messages() + [{"role": "assistant", "content": "Editing", "tool_calls": [
        {"id": "call-1", "type": "function", "function": {"name": "write_file", "arguments": "{}"}},
        {"id": "call-2", "type": "function", "function": {"name": "run_command", "arguments": "{}"}},
    ]}, {"role": "tool", "tool_call_id": "call-1", "content": "Edit already recorded"}]


def reply(text):
    return SimpleNamespace(choices=[SimpleNamespace(message={"role": "assistant", "content": text})],
                           usage=SimpleNamespace(total_tokens=7))


def test_restart_recovers_only_unmatched_calls_and_never_reexecutes(tmp_path):
    store = store_for(tmp_path)
    session_id = store.create(messages(), {})
    store.checkpoint(session_id, pending_context(), "running", 14)
    store.release(session_id)
    restarted = store_for(tmp_path)
    recovered = restarted.resume(session_id)
    assert recovered["status"] == "interrupted"
    assert recovered["context"][:-1] == pending_context()
    assert recovered["context"][-1]["tool_call_id"] == "call-2"
    assert "No tool was re-executed" in recovered["context"][-1]["content"]
    assert validate_messages(recovered["context"]) == {}
    restarted.release(session_id)
    assert len(restarted.resume(session_id)["context"]) == len(recovered["context"])
    restarted.release(session_id)


def test_session_lease_refuses_other_process_and_releases_after_close(tmp_path):
    store = store_for(tmp_path)
    session_id = store.create(messages(), {})
    with pytest.raises(SessionBusy):
        store_for(tmp_path).resume(session_id)
    script = "from mythic_agent.core.sessions import SessionStore,SessionBusy; from pathlib import Path; import sys; s=SessionStore(Path(sys.argv[1]),Path(sys.argv[1])/'state'); s.resume(sys.argv[2])"
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path), session_id],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode != 0 and "SessionBusy" in result.stderr
    store.release(session_id)
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path), session_id],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("session_id", ["../config", "a" * 33, "A" * 32, "..\\file", "bad", ""])
def test_session_ids_cannot_escape_state(tmp_path, session_id):
    store = store_for(tmp_path)
    for operation in (store.resume, store.load, store.export):
        with pytest.raises(ValueError, match="Session ID"):
            operation(session_id)


def test_workspace_isolation_and_checkpoint_requires_lease(tmp_path):
    store = store_for(tmp_path)
    session_id = store.create(messages(), {})
    other_workspace = tmp_path / "other"
    other_workspace.mkdir()
    other = store_for(tmp_path, other_workspace)
    with pytest.raises(ValueError, match="not found"):
        other.resume(session_id)
    assert not other.list_sessions()
    store.release(session_id)
    with pytest.raises(SessionBusy):
        store.checkpoint(session_id, messages(), "completed", 7)


@pytest.mark.parametrize("context", [None, [], ["bad"], [{"role": "user", "content": "missing system"}],
    [{"role": "system", "content": []}], messages() + [{"role": "tool", "tool_call_id": "no-call", "content": "bad"}],
    pending_context() + [{"role": "user", "content": "missing result"}]])
def test_malformed_context_rejected_before_storage(tmp_path, context):
    store = store_for(tmp_path)
    with pytest.raises(ValueError):
        store.create(context, {})
    assert not store.list_sessions()


def test_context_clear_preserves_transcript_and_resume(agent, tmp_path):
    store = store_for(tmp_path)
    session_id = agent.attach_session(store)
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=Mock(side_effect=[reply("first answer"), reply("second answer")]))))
    agent.get_client = lambda: client
    agent.chat("first prompt")
    agent._handle_clear_history(agent.name)
    agent.chat("second prompt")
    exported = store.export(session_id)
    assert "first prompt" not in json.dumps(exported["context"])
    assert "first prompt" in json.dumps(exported["events"])
    assert exported["status"] == "completed" and exported["total_tokens"] == 14
    assert any(e["type"] == "context_cleared" for e in exported["events"])
    agent.close()
    assert store.resume(session_id)["context"] == exported["context"]
    store.release(session_id)


def test_failure_and_cancellation_are_durable_and_allow_continuation(agent, tmp_path):
    store = store_for(tmp_path)
    session_id = agent.attach_session(store)
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=Mock(side_effect=[
        RuntimeError("fixture provider failed"), KeyboardInterrupt(), reply("recovered")]))))
    agent.get_client = lambda: client
    with pytest.raises(RuntimeError):
        agent.chat("first")
    assert store.load(session_id)["status"] == "failed"
    with pytest.raises(TurnCancelled):
        agent.chat("second")
    assert store.load(session_id)["status"] == "cancelled"
    assert agent.chat("third") == "recovered"
    assert store.load(session_id)["status"] == "completed"
    agent.close()


def test_checkpoint_failure_does_not_report_success_or_execute_tools(agent, tmp_path, monkeypatch):
    store = store_for(tmp_path)
    agent.attach_session(store)
    provider = Mock()
    agent.get_client = provider
    def failure(*args, **kwargs):
        raise OSError("fixture unavailable storage")
    monkeypatch.setattr(store, "checkpoint", failure)
    with pytest.raises(OSError, match="storage"):
        agent.chat("run this")
    assert agent.last_result.status == "failed"
    provider.assert_not_called()
    agent.close()


def test_export_redacts_configured_environment_and_common_tokens(tmp_path, monkeypatch):
    configured = "fixture-configured-credential"
    environment = "fixture-environment-credential"
    monkeypatch.setenv("FIXTURE_API_KEY", environment)
    redactor = SecretRedactor({"api_keys": {"http://localhost": configured}})
    store = store_for(tmp_path, redactor=redactor)
    context = messages() + [{"role": "assistant", "content": f"{configured} {environment} sk-proj-0123456789abcdefgh"}]
    session_id = store.create(context, {"base_url": "http://name:password@localhost/v1?token=hidden"})
    exported = json.dumps(store.export(session_id))
    assert configured not in exported and environment not in exported
    assert "sk-proj-0123456789abcdefgh" not in exported
    assert "name:password" not in exported and "token=hidden" not in exported
    assert "[REDACTED]" in exported
    assert store.load(session_id)["context"] == context  # Private local transcript is complete.
    store.release(session_id)


def test_logging_redacts_formatted_arguments_and_exception_trace(caplog):
    secret = "fixture-logging-credential"
    protect_logging(SecretRedactor({"github": {"token": secret}}, include_environment=False))
    with caplog.at_level(logging.ERROR):
        try:
            raise RuntimeError(secret)
        except RuntimeError:
            logging.exception("Fixture diagnostic %s", secret)
    assert secret not in caplog.text
    assert "[REDACTED]" in caplog.text


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits are not Windows ACLs")
def test_session_database_and_directory_are_private(tmp_path):
    store = store_for(tmp_path)
    session_id = store.create(messages(), {})
    assert store.path.stat().st_mode & 0o777 == 0o600
    assert store.root.stat().st_mode & 0o777 == 0o700
    store.release(session_id)


def test_future_storage_version_and_corrupt_context_preserve_database(tmp_path):
    store = store_for(tmp_path)
    session_id = store.create(messages(), {})
    store.release(session_id)
    with store._connection() as connection:
        connection.execute("UPDATE sessions SET context=? WHERE id=?", ('["bad"]', session_id))
    with pytest.raises(ValueError):
        store.resume(session_id)
    with store._connection() as connection:
        assert connection.execute("SELECT context FROM sessions").fetchone()[0] == '["bad"]'
        connection.execute("PRAGMA user_version=999")
    with pytest.raises(ValueError, match="version"):
        store_for(tmp_path)


def test_abrupt_process_exit_releases_lease_and_preserves_pending_checkpoint(tmp_path):
    script = """import json,os,sys
from pathlib import Path
from mythic_agent.core.sessions import SessionStore
s=SessionStore(Path(sys.argv[1]),Path(sys.argv[1])/'state')
context=json.loads(sys.argv[2])
session_id=s.create(context,{})
s.checkpoint(session_id,context,'running',7)
print(session_id,flush=True)
os._exit(9)
"""
    child = subprocess.run([sys.executable, "-c", script, str(tmp_path), json.dumps(pending_context())],
                           capture_output=True, text=True, timeout=15)
    assert child.returncode == 9, child.stderr
    store = store_for(tmp_path)
    session_id = child.stdout.strip()
    recovered = store.resume(session_id)
    assert recovered["status"] == "interrupted"
    assert validate_messages(recovered["context"]) == {}
    assert store.export(session_id)["events"][-1]["type"] == "recovered"
    store.release(session_id)


def test_manual_compaction_retains_every_original_message(agent, tmp_path):
    store = store_for(tmp_path)
    session_id = agent.attach_session(store)
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=Mock(side_effect=[reply("one"), reply("two")]))))
    agent.get_client = lambda: client
    agent.chat("first")
    agent.chat("second")
    agent._handle_compact_history(agent.name)
    exported = store.export(session_id)
    assert [m["role"] for m in exported["context"]] == ["system", "user", "assistant"]
    assert exported["context"][1]["content"] == "second"
    assert "first" in json.dumps(exported["events"])
    assert any(e["type"] == "context_compacted" for e in exported["events"])
    agent.close()


def test_workspace_switch_rotates_session_and_preserves_old_transcript(agent, tmp_path):
    store = store_for(tmp_path)
    original_id = agent.attach_session(store)
    agent.add_context("Old workspace context")
    other = tmp_path / "another"
    other.mkdir()
    agent.change_workspace(other)
    assert agent.project_root == other
    assert agent.session_id != original_id
    assert len(agent.messages) == 1
    assert "Old workspace context" in json.dumps(store.export(original_id))
    assert store.resume(original_id)
    store.release(original_id)
    agent.close()


def test_direct_workspace_mutation_refused_before_provider_execution(agent, tmp_path):
    store = store_for(tmp_path)
    agent.attach_session(store)
    other = tmp_path / "another"
    other.mkdir()
    agent.project_root = other
    provider = Mock()
    agent.get_client = provider
    with pytest.raises(ValueError, match="Workspace changed"):
        agent.chat("continue")
    provider.assert_not_called()
    agent.close()


def test_model_save_failure_restores_live_selection(agent, monkeypatch):
    from mythic_agent.agents import llm
    before = agent.config.copy()
    monkeypatch.setattr(llm.config_manager, "save_config", lambda config: False)
    with pytest.raises(RuntimeError, match="could not be saved"):
        agent.set_model("changed", "http://localhost:2/v1")
    assert agent.config == before


def test_failed_context_write_keeps_live_and_durable_context(agent, tmp_path, monkeypatch):
    store = store_for(tmp_path)
    session_id = agent.attach_session(store)
    agent.add_context("Retain this context")
    before = agent.history_snapshot()
    original_checkpoint = store.checkpoint
    def failure(*args, **kwargs):
        raise OSError("fixture disk failure")
    monkeypatch.setattr(store, "checkpoint", failure)
    with pytest.raises(OSError):
        agent._handle_clear_history(agent.name)
    assert agent.history_snapshot() == before
    assert store.load(session_id)["context"] == before
    with pytest.raises(OSError):
        agent.add_context("Failed addition")
    assert agent.history_snapshot() == before
    monkeypatch.setattr(store, "checkpoint", original_checkpoint)
    agent.close()
