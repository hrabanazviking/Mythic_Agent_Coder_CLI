"""Tests for M-089: patch export/import (pure layer).

TIER: integration
"""

import pytest

from mythic_agent.core import patch_exchange as pe
from mythic_agent.core.change_sets import (
    attach_evidence,
    decide,
    make_edit,
    make_evidence,
    start_change_set,
)


def _set(name="hand-off fix", evidence=True, reject_second=False):
    edits = [make_edit("src/app.py", "whole-file", "x = 2\n"),
             make_edit("src/new.py", "whole-file", "y = 3\n")]
    result = start_change_set(name, edits)
    result = decide(result, 0, "accept")
    result = decide(result, 1, "reject" if reject_second else "accept")
    if evidence:
        result = attach_evidence(result, make_evidence(
            "pytest -q", 12, 0, 1, "logs/run.log"))
    return result


def test_export_starts_with_magic_and_header():
    text = pe.export_patch(_set())
    lines = text.splitlines()
    assert lines[0] == pe.MAGIC
    assert '"patch_header"' in lines[1]
    assert '"slice":"M-089"' in lines[1]


def test_round_trip_recovers_name_files_and_evidence():
    patch = pe.parse_patch(pe.export_patch(_set()))
    assert patch.name == "hand-off fix"
    assert [e.path for e in patch.edits] == ["src/app.py", "src/new.py"]
    assert patch.edits[0].payload == "x = 2\n"
    assert patch.evidence["verdict"] == "passed"
    assert patch.evidence["passed"] == 12
    assert patch.record()["slice"] == "M-089"


def test_round_trip_change_set_is_fully_accepted():
    patch = pe.parse_patch(pe.export_patch(_set()))
    rebuilt = patch.change_set()
    assert rebuilt.undecided() == []
    assert rebuilt.counts() == {"accepted": 2, "rejected": 0,
                                 "pending": 0}
    assert rebuilt.evidence.command == "pytest -q"


def test_pending_file_refuses_export_and_is_named():
    result = start_change_set("half", [make_edit(
        "src/app.py", "whole-file", "x = 2\n")])
    with pytest.raises(ValueError, match="not decided"):
        pe.export_patch(result)


def test_all_rejected_refuses_export():
    result = start_change_set("no", [make_edit(
        "src/app.py", "whole-file", "x = 2\n")])
    result = decide(result, 0, "reject")
    with pytest.raises(ValueError, match="every"):
        pe.export_patch(result)


def test_rejected_file_is_named_but_carries_no_payload():
    text = pe.export_patch(_set(reject_second=True))
    patch = pe.parse_patch(text)
    assert patch.rejected == ("src/new.py",)
    assert [e.path for e in patch.edits] == ["src/app.py"]
    assert "y = 3" not in text


def test_no_evidence_is_recorded_as_none():
    patch = pe.parse_patch(pe.export_patch(_set(evidence=False)))
    assert patch.evidence is None
    assert "none attached" in pe.format_patch(patch)


def test_failed_evidence_verdict_travels():
    result = _set(evidence=False)
    result = attach_evidence(result, make_evidence("pytest -q", 3, 2))
    patch = pe.parse_patch(pe.export_patch(result))
    assert patch.evidence["verdict"] == "failed"


def test_tampered_header_refuses():
    text = pe.export_patch(_set())
    bad = text.replace("hand-off fix", "hand-off fox", 1)
    with pytest.raises(ValueError, match="checksum"):
        pe.parse_patch(bad)


def test_tampered_payload_refuses_on_anchor():
    text = pe.export_patch(_set())
    bad = text.replace("x = 2", "x = 9", 1)
    with pytest.raises(ValueError, match="anchor"):
        pe.parse_patch(bad)


def test_wrong_magic_refuses():
    with pytest.raises(ValueError, match="not a patch file"):
        pe.parse_patch("SOMETHING ELSE\n{}")


def test_trailing_bytes_refuse():
    text = pe.export_patch(_set()) + "smuggled\n"
    with pytest.raises(ValueError, match="after its last section"):
        pe.parse_patch(text)


def test_truncated_payload_refuses():
    text = pe.export_patch(_set())
    with pytest.raises(ValueError):
        pe.parse_patch(text[:len(text) - 8])


def test_payload_with_header_like_lines_round_trips():
    tricky = 'MYTHIC-PATCH/1\n{"path": "fake"}\nreal = 1\n'
    result = start_change_set("tricky", [make_edit(
        "src/t.py", "whole-file", tricky)])
    result = decide(result, 0, "accept")
    patch = pe.parse_patch(pe.export_patch(result))
    assert patch.edits[0].payload == tricky


def test_payload_without_trailing_newline_round_trips():
    result = start_change_set("nonl", [make_edit(
        "src/t.py", "whole-file", "no newline at end")])
    result = decide(result, 0, "accept")
    patch = pe.parse_patch(pe.export_patch(result))
    assert patch.edits[0].payload == "no newline at end"


def test_unicode_payload_round_trips():
    result = start_change_set("uni", [make_edit(
        "src/t.py", "whole-file", "rune = 'ᚱ'\n")])
    result = decide(result, 0, "accept")
    patch = pe.parse_patch(pe.export_patch(result))
    assert patch.edits[0].payload == "rune = 'ᚱ'\n"


def test_import_plans_against_receiving_tree():
    text = pe.export_patch(_set())
    planned, outcome = pe.import_patch(
        text, {"src/app.py": "x = 1\n", "src/new.py": None})
    assert planned == {"src/app.py": "x = 2\n", "src/new.py": "y = 3\n"}
    assert outcome.applied == 2


def test_import_refuses_whole_set_on_one_stale_file():
    edits = [make_edit("src/a.py", "search-replace",
                       "<<<<<<< SEARCH\nold = 1\n=======\n"
                       "old = 2\n>>>>>>> REPLACE"),
             make_edit("src/b.py", "whole-file", "b = 2\n")]
    result = start_change_set("strict", edits)
    result = decide(decide(result, 0, "accept"), 1, "accept")
    text = pe.export_patch(result)
    with pytest.raises(ValueError, match="whole"):
        pe.import_patch(text, {"src/a.py": "changed = 9\n",
                               "src/b.py": "b = 1\n"})


def test_setting_gate_reads_config():
    assert pe.enabled_from_config({}) is True
    assert pe.enabled_from_config({"patch_exchange": False}) is False
    with pytest.raises(ValueError, match="true or false"):
        pe.enabled_from_config({"patch_exchange": "yes"})


def test_set_enabled_validates_and_records():
    enabled, change = pe.set_enabled({}, False)
    assert enabled is False
    assert change.event() == {"type": "patch_exchange_setting_changed",
                              "from": True, "to": False}
    with pytest.raises(ValueError, match="already on"):
        pe.set_enabled({}, True)
    with pytest.raises(ValueError, match="on or off"):
        pe.set_enabled({}, "off")


def test_parse_args_grammar():
    assert pe.parse_patch_args("") == {"action": "show"}
    assert pe.parse_patch_args("on") == {"action": "on"}
    assert pe.parse_patch_args("off") == {"action": "off"}
    assert pe.parse_patch_args("export my set name") == {
        "action": "export", "name": "my set name"}
    assert pe.parse_patch_args("import /tmp/a.patch") == {
        "action": "import", "ref": "/tmp/a.patch"}
    with pytest.raises(ValueError, match="usage"):
        pe.parse_patch_args("frobnicate")


def test_format_patch_names_rejected_and_evidence():
    patch = pe.parse_patch(pe.export_patch(
        _set(reject_second=True)))
    shown = pe.format_patch(patch)
    assert "src/new.py" in shown
    assert "rejected in review" in shown
    assert "passed" in shown


def test_format_patch_exchange_show_surface():
    shown = pe.format_patch_exchange({})
    assert "M-089" in shown
    assert "Setting: on (patch_exchange)" in shown
    assert "Plans whole on the receiving tree" in shown
    assert pe.format_patch_exchange(
        {"patch_exchange": False}).splitlines()[2] == \
        "Setting: off (patch_exchange)."


def test_format_setting_change():
    assert pe.format_setting_change({"to": True}) == \
        "Patch exchange is now on."
    assert pe.format_setting_change({"to": False}) == \
        "Patch exchange is now off."


# ---------------------------------------------------------------------
# Agent layer + surfaces (keeper restart tick, 2026-11-06).
#
# Design note: the Agent holds no persistent named change sets -
# M-084 sets are transient values built by preview/apply_change_set -
# so export takes the ChangeSet object itself plus a destination
# path, and /patch export <set name> refuses plainly on both roads.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


def _seed_tree(tmp_path):
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")


class TestAgentGate:
    def test_status(self, agent):
        status = agent.patch_exchange_status()
        assert status["enabled"] is True
        assert status["explanation"] == pe.PLAIN_EXPLANATION

    def test_set_without_session(self, agent):
        record = agent.set_patch_exchange(False)
        assert record["journaled"] is False
        assert agent.config["patch_exchange"] is False
        with pytest.raises(ValueError, match="already"):
            agent.set_patch_exchange(False)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_patch_exchange(False)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "patch_exchange_setting_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_patch_exchange(False)
        assert agent.config.get("patch_exchange") is not False
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["patch_exchange_setting_changed",
                              "patch_exchange_setting_reverted"]
        agent.close()


class TestExportImportFiles:
    def test_export_writes_a_real_patch_file(self, agent, tmp_path):
        dest = tmp_path / "hand-off.patch"
        record = agent.export_patch_to_file(_set(), dest)
        assert record["name"] == "hand-off fix"
        assert record["files"] == ["src/app.py", "src/new.py"]
        assert record["journaled"] is False
        text = dest.read_text(encoding="utf-8")
        assert text.startswith(pe.MAGIC + "\n")
        patch = pe.parse_patch(text)
        assert patch.name == "hand-off fix"

    def test_export_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.export_patch_to_file(_set(), tmp_path / "a.patch")
        assert record["journaled"] is True
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "patch_exported" in types
        agent.close()

    def test_export_gate_off_refuses_and_writes_nothing(
            self, agent, tmp_path):
        agent.set_patch_exchange(False)
        dest = tmp_path / "a.patch"
        with pytest.raises(ValueError, match="patch exchange is off"):
            agent.export_patch_to_file(_set(), dest)
        assert not dest.exists()

    def test_export_undecided_set_refuses_and_writes_nothing(
            self, agent, tmp_path):
        pending = start_change_set("half", [make_edit(
            "src/app.py", "whole-file", "x = 2\n")])
        dest = tmp_path / "a.patch"
        with pytest.raises(ValueError, match="not decided"):
            agent.export_patch_to_file(pending, dest)
        assert not dest.exists()

    def test_import_round_trip_lands_on_the_tree(self, agent, tmp_path):
        _seed_tree(tmp_path)
        dest = tmp_path / "hand-off.patch"
        agent.export_patch_to_file(_set(), dest)
        record = agent.import_patch_from_file(dest)
        assert record["applied"] == 2
        assert record["changed_files"] == 2
        assert (tmp_path / "src" / "app.py").read_text(
            encoding="utf-8") == "x = 2\n"
        assert (tmp_path / "src" / "new.py").read_text(
            encoding="utf-8") == "y = 3\n"

    def test_import_journals_on_the_session(self, agent, tmp_path):
        _seed_tree(tmp_path)
        dest = tmp_path / "a.patch"
        agent.export_patch_to_file(_set(), dest)
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.import_patch_from_file(dest)
        assert record["journaled"] is True
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "patch_imported" in types
        agent.close()

    def test_import_across_instances(self, agent, tmp_path):
        from mythic_agent.agents import llm

        _seed_tree(tmp_path)
        dest = tmp_path / "a.patch"
        agent.export_patch_to_file(_set(), dest)
        other = llm.Agent(project_root=tmp_path)
        record = other.import_patch_from_file(dest)
        assert record["name"] == "hand-off fix"
        assert (tmp_path / "src" / "app.py").read_text(
            encoding="utf-8") == "x = 2\n"

    def test_import_gate_off_refuses_and_writes_nothing(
            self, agent, tmp_path):
        _seed_tree(tmp_path)
        dest = tmp_path / "a.patch"
        agent.export_patch_to_file(_set(), dest)
        agent.set_patch_exchange(False)
        with pytest.raises(ValueError, match="patch exchange is off"):
            agent.import_patch_from_file(dest)
        assert (tmp_path / "src" / "app.py").read_text(
            encoding="utf-8") == "x = 1\n"
        assert not (tmp_path / "src" / "new.py").exists()

    def test_import_missing_file_refuses_plainly(self, agent, tmp_path):
        with pytest.raises(ValueError, match="no patch file"):
            agent.import_patch_from_file(tmp_path / "nope.patch")

    def test_import_tampered_file_refuses_and_writes_nothing(
            self, agent, tmp_path):
        _seed_tree(tmp_path)
        dest = tmp_path / "a.patch"
        agent.export_patch_to_file(_set(), dest)
        dest.write_text(dest.read_text(encoding="utf-8").replace(
            "x = 2", "x = 9", 1), encoding="utf-8")
        with pytest.raises(ValueError, match="anchor"):
            agent.import_patch_from_file(dest)
        assert (tmp_path / "src" / "app.py").read_text(
            encoding="utf-8") == "x = 1\n"

    def test_import_one_stale_file_refuses_the_whole_import(
            self, agent, tmp_path):
        (tmp_path / "src").mkdir(exist_ok=True)
        (tmp_path / "src" / "a.py").write_text("changed = 9\n",
                                              encoding="utf-8")
        (tmp_path / "src" / "b.py").write_text("b = 1\n",
                                              encoding="utf-8")
        edits = [make_edit("src/a.py", "search-replace",
                           "<<<<<<< SEARCH\nold = 1\n=======\n"
                           "old = 2\n>>>>>>> REPLACE"),
                 make_edit("src/b.py", "whole-file", "b = 2\n")]
        strict = start_change_set("strict", edits)
        strict = decide(decide(strict, 0, "accept"), 1, "accept")
        dest = tmp_path / "strict.patch"
        agent.export_patch_to_file(strict, dest)
        with pytest.raises(ValueError, match="whole"):
            agent.import_patch_from_file(dest)
        assert (tmp_path / "src" / "b.py").read_text(
            encoding="utf-8") == "b = 1\n"


class TestTerminalSurface:
    def test_show_and_set(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/patch")
        assert "Patch export/import (M-089)" in text
        assert "Setting: on (patch_exchange)" in text
        _, _, text = _slash(agent, "/patch off")
        assert "Patch exchange is now off." in text
        assert agent.config["patch_exchange"] is False
        _, _, text = _slash(agent, "/patch on")
        assert "Patch exchange is now on." in text

    def test_import_via_the_terminal(self, agent, tmp_path):
        from mythic_agent.terminal import _slash

        _seed_tree(tmp_path)
        dest = tmp_path / "hand-off.patch"
        agent.export_patch_to_file(_set(), dest)
        _, _, text = _slash(agent, f"/patch import {dest}")
        assert "Imported patch 'hand-off fix'" in text
        assert (tmp_path / "src" / "app.py").read_text(
            encoding="utf-8") == "x = 2\n"
        assert (tmp_path / "src" / "new.py").read_text(
            encoding="utf-8") == "y = 3\n"

    def test_export_via_the_terminal_is_an_honest_refusal(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/patch export hand-off fix")
        assert "no change set named" in text
        assert "Nothing was exported." in text

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/patch frobnicate")
        assert "usage" in text


@pytest.fixture()
def handler(agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY

    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestPatchCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_patch("")
        assert "Patch export/import (M-089)" in _published_text(handler)

    def test_set_via_the_handler(self, handler, agent):
        handler._handle_patch("off")
        assert "Patch exchange is now off." in _published_text(handler)
        assert agent.config["patch_exchange"] is False

    def test_import_via_the_handler(self, handler, agent, tmp_path):
        _seed_tree(tmp_path)
        dest = tmp_path / "hand-off.patch"
        agent.export_patch_to_file(_set(), dest)
        handler._handle_patch(f"import {dest}")
        assert "Imported patch 'hand-off fix'" in _published_text(handler)
        assert (tmp_path / "src" / "app.py").read_text(
            encoding="utf-8") == "x = 2\n"

    def test_export_via_the_handler_is_an_honest_refusal(
            self, handler, agent):
        handler._handle_patch("export hand-off fix")
        assert "Nothing was exported." in _published_text(handler)

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_patch("frobnicate")
        assert "usage" in _published_text(handler)


class TestChatScreenRouting:
    def test_patch_routes_as_system_command(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import MainChatScreen

        class _FakeLog:
            def __init__(self):
                self.lines = []

            def write(self, *args, **kwargs):
                self.lines.append(" ".join(str(a) for a in args))

        calls = []
        monkeypatch.setattr(
            chat_screen.SecureAPI, "publish_system_command",
            staticmethod(lambda cmd, args: calls.append((cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        screen.handle_command("/patch off", _FakeLog())
        assert calls == [("/patch", "off")]
