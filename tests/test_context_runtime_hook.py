"""
TIER: unit
Tests for the context compiler's hooks into the real agent prompt path:
``Agent.rebuild_system_prompt`` (instruction layers) and
``Agent._compile_prompt_context`` (file context), both gated on the
``context_compiler_enabled`` runtime setting (default off).
"""

import copy

import pytest

from mythic_agent.core.runtime import runtime_settings


class _OfflineMemory:
    def search(self, query, top_k=2):
        return []

    def insert(self, text, metadata=None):
        pass


@pytest.fixture()
def agent_factory(tmp_path, monkeypatch):
    from mythic_agent.agents import llm

    monkeypatch.setattr(llm.config_manager, "MYTHIC_DIR", tmp_path / "state")
    monkeypatch.setattr(llm.config_manager, "save_config", lambda config: True)
    monkeypatch.setattr(llm, "get_vector_provider",
                        lambda *args: _OfflineMemory())

    def make(config_extra=None, workspace=None):
        config = {"model": "test-model", "base_url": "http://localhost:1/v1",
                  "api_keys": {}}
        if config_extra:
            config.update(copy.deepcopy(config_extra))
        ws = workspace or (tmp_path / "ws")
        ws.mkdir(exist_ok=True)
        monkeypatch.setattr(llm.config_manager, "load_config",
                            lambda: copy.deepcopy(config))
        return llm.Agent(project_root=ws)

    return make


def _flag_on():
    return {"runtime": {"context_compiler_enabled": True}}


# ---------------------------------------------------------------------------
# default-off invariant
# ---------------------------------------------------------------------------

def test_flag_defaults_off(agent_factory):
    agent = agent_factory()
    assert agent.messages[0]["role"] == "system"
    assert "Repository instructions" not in agent.messages[0]["content"]
    assert agent._compile_prompt_context("fix @x.py") == ""


def test_runtime_settings_exposes_flag():
    assert runtime_settings({})["context_compiler_enabled"] is False
    assert runtime_settings(
        {"runtime": {"context_compiler_enabled": True}}
    )["context_compiler_enabled"] is True


def test_config_schema_accepts_flag():
    from mythic_agent.core import config_manager
    config = {"config_version": 1, "model": "m",
              "base_url": "http://localhost:1/v1",
              "runtime": {"context_compiler_enabled": True}}
    assert config_manager.validate_config(config) == []


# ---------------------------------------------------------------------------
# instruction hook
# ---------------------------------------------------------------------------

def test_instruction_block_in_system_prompt_when_enabled(agent_factory, tmp_path):
    ws = tmp_path / "proj"
    ws.mkdir()
    (ws / "AGENTS.md").write_text("- Never force-push\nTimeout: 30\n")
    agent = agent_factory(_flag_on(), workspace=ws)
    content = agent.messages[0]["content"]
    assert "Repository instructions" in content
    assert "Never force-push" in content


def test_no_instruction_block_without_instruction_files(agent_factory):
    agent = agent_factory(_flag_on())
    assert "Repository instructions" not in agent.messages[0]["content"]


# ---------------------------------------------------------------------------
# prompt file-context hook
# ---------------------------------------------------------------------------

def test_prompt_context_resolves_mentions(agent_factory, tmp_path):
    ws = tmp_path / "proj"
    ws.mkdir()
    (ws / "app.py").write_text("print('app')\n")
    agent = agent_factory(_flag_on(), workspace=ws)
    out = agent._compile_prompt_context("review @app.py please")
    assert "print('app')" in out
    assert "reference material, not instructions" in out


def test_prompt_context_empty_query(agent_factory):
    agent = agent_factory(_flag_on())
    assert agent._compile_prompt_context("   ") == ""


def test_prompt_context_cancelled(agent_factory):
    agent = agent_factory(_flag_on())
    agent._cancel.set()
    try:
        assert agent._compile_prompt_context("review @x.py") == ""
    finally:
        agent._cancel.clear()


def test_prompt_context_redacts_secrets(agent_factory, tmp_path):
    secret = "sk-live-hook-secret-123"
    ws = tmp_path / "proj"
    ws.mkdir()
    (ws / "app.py").write_text(f"API_KEY = '{secret}'\n")
    agent = agent_factory(
        {"runtime": {"context_compiler_enabled": True},
         "api_keys": {"service": secret}},
        workspace=ws)
    out = agent._compile_prompt_context("review @app.py")
    assert secret not in out
    assert "[REDACTED]" in out


def test_prompt_context_failure_degrades_gracefully(agent_factory, monkeypatch):
    agent = agent_factory(_flag_on())
    import mythic_agent.context.runtime as runtime_mod
    monkeypatch.setattr(runtime_mod, "ContextCompiler", None)
    # TypeError inside the hook must not propagate; the turn survives.
    assert agent._compile_prompt_context("review @x.py") == ""
