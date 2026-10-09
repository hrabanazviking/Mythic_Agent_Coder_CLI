"""Tests for workspace-scoped core memory isolation (S11)."""

import json

import pytest

from mythic_agent.core import config_manager as cm_module
from mythic_agent.memory.core_memory import CoreMemoryManager
from mythic_agent.memory.scopes import (
    WorkspaceScope,
    sanitize_segment,
    scope_for_root,
    scoped_agent_key,
)


@pytest.fixture
def mythic_dir(tmp_path, monkeypatch):
    """Isolate MYTHIC_DIR so tests never touch the real ~/.mythic."""
    state = tmp_path / "mythic-state"
    monkeypatch.setattr(cm_module.config_manager, "MYTHIC_DIR", state)
    return state


def test_namespace_format():
    scope = WorkspaceScope("workspace-123")
    assert scope.namespace("persona") == "workspace-123:persona"
    assert scoped_agent_key("workspace-123", "Primary", "persona") == (
        "workspace-123:Primary:persona"
    )


def test_safe_namespace_is_filename_safe():
    scope = WorkspaceScope("ws/with:weird chars!")
    token = scope.safe_namespace("Pri/mary")
    assert "/" not in token and ":" not in token and " " not in token
    assert token != ""


def test_sanitize_segment():
    assert sanitize_segment("  a/b:c  ") == "a_b_c"
    assert sanitize_segment("!!!") == "default"
    assert sanitize_segment("ws-1_2") == "ws-1_2"


def test_isolation_two_workspaces_same_agent(mythic_dir):
    """Two workspaces, same agent name: no cross-workspace leakage."""
    mem_a = CoreMemoryManager("Primary", workspace_id="workspace-a")
    mem_b = CoreMemoryManager("Primary", workspace_id="workspace-b")

    assert mem_a.memory_file != mem_b.memory_file
    assert mem_a.replace("project", "secret project A")
    assert mem_b.load()["project"] == "No active project specified."
    # The other workspace must not read it either.
    mem_b2 = CoreMemoryManager("Primary", workspace_id="workspace-b")
    assert mem_b2.load()["project"] == "No active project specified."
    # And it must have landed in workspace A's file.
    mem_a2 = CoreMemoryManager("Primary", workspace_id="workspace-a")
    assert mem_a2.load()["project"] == "secret project A"


def test_same_workspace_shares_memory(mythic_dir):
    mem_a = CoreMemoryManager("Primary", workspace_id="shared-ws")
    mem_b = CoreMemoryManager("Primary", workspace_id="shared-ws")
    assert mem_a.memory_file == mem_b.memory_file
    assert mem_a.replace("human", "Volmarr")
    assert mem_b.load()["human"] == "Volmarr"


def test_legacy_default_keeps_backward_compatible_filename(mythic_dir):
    """workspace_id=None preserves the historical file layout."""
    mem = CoreMemoryManager("Primary")
    assert mem.scope.is_default
    assert mem.memory_file.name == "Primary_core.json"
    assert mem.memory_file.parent == mythic_dir / "memory" / "core"


def test_namespaced_filename_uses_scope(mythic_dir):
    mem = CoreMemoryManager("Primary", workspace_id="ws-9")
    assert "ws-9" in mem.memory_file.name
    assert mem.memory_file.name != "Primary_core.json"


def test_scope_for_root_gives_distinct_ids(tmp_path):
    root_a = tmp_path / "project-a"
    root_b = tmp_path / "project-b"
    root_a.mkdir()
    root_b.mkdir()
    scope_a = scope_for_root(root_a)
    scope_b = scope_for_root(root_b)
    assert scope_a.workspace_id != scope_b.workspace_id
    assert scope_for_root(None).is_default


def test_namespaced_memory_roundtrip_on_disk(mythic_dir):
    mem = CoreMemoryManager("Runa", workspace_id="ws-disk")
    mem.append("long_term_notes", "remember the runes")
    data = json.loads(mem.memory_file.read_text(encoding="utf-8"))
    assert "remember the runes" in data["long_term_notes"]
