"""M-073 — Apply-failure repair loop.

TIER: integration

Covers the M-073 surface:

* the pure layer (``mythic_agent.core.apply_repair``): a
  refused apply becomes a repair packet — the road, the
  refusal's own reason, and the true current text of the
  refused target as a bounded window (the target's lines
  plus 5 lines of context, capped at 40 lines, truncation
  named with the file's true line count); exactly one
  honest retry rides on a packet, judged by the unchanged
  M-071/M-072 appliers (no fuzz, ever); a second refusal
  raises the exhaustion error naming the spent budget, and
  a spent packet refuses any further retry outright;
  target location for refused format payloads (a diff's
  first hunk, a search block's first hit, honestly unknown
  when the block is nowhere in the file),
* ``Agent``: the gate status, ``set_apply_repair`` journaled
  as ``apply_repair_setting_changed`` (a failed save
  restoring the previous value and journaling the revert),
  the three with-repair apply roads — a refusal journaled
  as ``apply_repair_offered`` and returned as a packet with
  nothing written when no retry is supplied, a repaired
  apply riding the EditJournal road and journaled as
  ``apply_repair_applied``, an exhausted loop journaled as
  ``apply_repair_exhausted`` and raised, and the gate off
  keeping the plain M-071/M-072 refusal with no packet,
* the tool road: a stale anchored write/replace and a
  replace whose target does not match exactly once return
  the packet's true current text in the tool result,
* the surfaces: the terminal ``/repairloop`` and the TUI
  ``/repairloop`` (system-command road through the
  CommandHandler + chat-screen routing), which share the
  parser and formatters,
* the config contract: ``apply_repair_loop`` ships in the
  defaults (True) and is catalogued (M-009, S-62).
"""

from __future__ import annotations

import pytest

from mythic_agent.core.apply_repair import (
    APPLY_REPAIR_SLICE,
    CONTEXT_LINES,
    MAX_RETRIES,
    MAX_WINDOW_LINES,
    PLAIN_EXPLANATION,
    ROADS,
    SETTING_KEY,
    build_packet,
    enabled_from_config,
    format_apply_repair,
    format_packet,
    format_setting_change,
    parse_repairloop_args,
    retry_anchored_range,
    retry_anchored_search,
    retry_edit_format,
    set_enabled,
    target_range_for_format,
    true_text_window,
)
from mythic_agent.core.hash_anchored import range_anchor, range_hash
from mythic_agent.core.sessions import SessionStore

SOURCE = "alpha = 1\nbeta = 2\ngamma = 3\n"
STALE_DIFF = "@@ -2,1 +2,1 @@\n-beta = 99\n+beta = 20"
GOOD_DIFF = "@@ -2,1 +2,1 @@\n-beta = 2\n+beta = 20"
SEARCH_PAYLOAD = ("<<<<<<< SEARCH\nbeta = 99\n=======\n"
                  "beta = 20\n>>>>>>> REPLACE")


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


def stale_diff_packet(current=SOURCE):
    from mythic_agent.core.edit_formats import apply_edit

    with pytest.raises(ValueError) as caught:
        apply_edit("unified-diff", current, STALE_DIFF)
    target = target_range_for_format("unified-diff", current, STALE_DIFF)
    return build_packet("edit_format", str(caught.value), current,
                        *target)


class TestConstantsAndWindow:
    def test_slice_and_bounds(self):
        assert APPLY_REPAIR_SLICE == "M-073"
        assert SETTING_KEY == "apply_repair_loop"
        assert MAX_RETRIES == 1
        assert CONTEXT_LINES == 5
        assert MAX_WINDOW_LINES == 40
        assert ROADS == ("edit_format", "anchored_range",
                         "anchored_search")

    def test_small_file_window_is_the_whole_file(self):
        window = true_text_window(SOURCE, 2, 2)
        assert (window.start, window.end) == (1, 3)
        assert window.total_lines == 3
        assert window.truncated is False
        assert window.text() == SOURCE.rstrip("\n")

    def test_window_carries_context_around_the_target(self):
        big = "\n".join(f"line {n}" for n in range(1, 101))
        window = true_text_window(big, 50, 52)
        assert (window.start, window.end) == (45, 57)
        assert window.truncated is True
        assert window.lines[5] == "line 50"

    def test_window_is_capped_and_says_so(self):
        big = "\n".join(f"line {n}" for n in range(1, 101))
        window = true_text_window(big, 1, 100)
        assert len(window.lines) == MAX_WINDOW_LINES
        assert window.truncated is True
        assert window.total_lines == 100

    def test_no_target_window_starts_at_the_head(self):
        window = true_text_window(SOURCE)
        assert window.start == 1
        assert "alpha = 1" in window.text()

    def test_empty_file_window_is_empty(self):
        window = true_text_window("")
        assert window.lines == ()
        assert window.total_lines == 0
        assert window.truncated is False

    def test_window_refuses_non_text_and_bad_numbers(self):
        with pytest.raises(ValueError, match="made from"):
            true_text_window(None)
        with pytest.raises(ValueError, match="whole numbers"):
            true_text_window(SOURCE, "2", 2)


class TestTargetLocation:
    def test_diff_target_is_its_first_hunk(self):
        assert target_range_for_format(
            "unified-diff", SOURCE, STALE_DIFF) == (2, 2)

    def test_search_target_is_its_first_hit(self):
        payload = ("<<<<<<< SEARCH\nbeta = 2\n=======\n"
                   "beta = 20\n>>>>>>> REPLACE")
        assert target_range_for_format(
            "search-replace", SOURCE, payload) == (2, 2)

    def test_search_target_nowhere_is_honestly_unknown(self):
        assert target_range_for_format(
            "search-replace", SOURCE, SEARCH_PAYLOAD) is None

    def test_whole_file_has_no_locatable_target(self):
        assert target_range_for_format(
            "whole-file", SOURCE, "anything") is None


class TestPacket:
    def test_packet_carries_road_reason_and_true_text(self):
        packet = stale_diff_packet()
        assert packet.road == "edit_format"
        assert "context does not match" in packet.reason
        assert "beta = 2" in packet.window.text()
        assert packet.attempts_used == 0
        assert packet.attempts_left == 1

    def test_packet_record_and_event_carry_the_window(self):
        packet = stale_diff_packet()
        event = packet.event()
        assert event["type"] == "apply_repair_offered"
        assert event["start"] == 1 and event["end"] == 3
        record = packet.record("s1", True)
        assert record["true_text"] == packet.window.text()
        assert record["journaled"] is True

    def test_build_packet_validates(self):
        with pytest.raises(ValueError, match="road is one of"):
            build_packet("telepathy", "reason", SOURCE)
        with pytest.raises(ValueError, match="refusal's reason"):
            build_packet("edit_format", "  ", SOURCE)

    def test_spend_is_bounded_by_construction(self):
        packet = stale_diff_packet()
        spent = packet.spend()
        assert spent.attempts_used == 1
        assert spent.attempts_left == 0
        with pytest.raises(ValueError, match="already"):
            spent.spend()
        assert packet.attempts_used == 0  # the original is untouched


class TestRetryEditFormat:
    def test_one_honest_retry_applies_on_the_true_text(self):
        packet = stale_diff_packet()
        new_text, units, spent = retry_edit_format(
            SOURCE, packet, "unified-diff", GOOD_DIFF)
        assert units == 1
        assert "beta = 20" in new_text
        assert spent.attempts_used == 1

    def test_a_second_refusal_exhausts_and_names_the_budget(self):
        packet = stale_diff_packet()
        with pytest.raises(ValueError, match="budget is spent"):
            retry_edit_format(SOURCE, packet, "unified-diff", STALE_DIFF)

    def test_a_spent_packet_refuses_any_further_retry(self):
        packet = stale_diff_packet().spend()
        with pytest.raises(ValueError, match="already"):
            retry_edit_format(SOURCE, packet, "unified-diff", GOOD_DIFF)

    def test_a_packet_cannot_cross_roads(self):
        packet = build_packet("anchored_range", "moved", SOURCE, 2, 2)
        with pytest.raises(ValueError, match="cannot be retried"):
            retry_edit_format(SOURCE, packet, "unified-diff", GOOD_DIFF)

    def test_search_replace_retry_on_a_corrected_block(self):
        packet = build_packet("edit_format", "matched nothing", SOURCE)
        good = ("<<<<<<< SEARCH\nbeta = 2\n=======\n"
                "beta = 20\n>>>>>>> REPLACE")
        new_text, units, _spent = retry_edit_format(
            SOURCE, packet, "search-replace", good)
        assert units == 1
        assert "beta = 20" in new_text


class TestRetryAnchored:
    def test_range_retry_with_the_true_anchor_applies(self):
        packet = build_packet("anchored_range", "moved", SOURCE, 2, 2)
        new_text, applied, _spent = retry_anchored_range(
            SOURCE, packet, 2, 2, range_anchor(SOURCE, 2, 2).hash,
            "beta = 20")
        assert "beta = 20" in new_text
        assert (applied.start, applied.end) == (2, 2)

    def test_range_retry_with_a_wrong_anchor_exhausts(self):
        packet = build_packet("anchored_range", "moved", SOURCE, 2, 2)
        with pytest.raises(ValueError, match="budget is spent"):
            retry_anchored_range(
                SOURCE, packet, 2, 2, "f" * 64, "beta = 20")

    def test_search_retry_with_the_true_anchor_applies(self):
        packet = build_packet("anchored_search", "moved", SOURCE, 2, 2)
        new_text, _applied, _spent = retry_anchored_search(
            SOURCE, packet, "beta = 2", range_hash(["beta = 2"]),
            "beta = 20")
        assert "beta = 20" in new_text

    def test_search_retry_exhausts_on_a_second_refusal(self):
        packet = build_packet("anchored_search", "moved", SOURCE, 2, 2)
        with pytest.raises(ValueError, match="budget is spent"):
            retry_anchored_search(
                SOURCE, packet, "beta = 2", "f" * 64, "beta = 20")


class TestSetting:
    def test_absent_means_on_and_bool_round_trips(self):
        assert enabled_from_config({}) is True
        assert enabled_from_config({SETTING_KEY: False}) is False
        with pytest.raises(ValueError, match="true or false"):
            enabled_from_config({SETTING_KEY: "yes"})

    def test_set_enabled_validates(self):
        value, change = set_enabled({}, False)
        assert value is False
        assert (change.before, change.after) == (True, False)
        assert change.event()["type"] == "apply_repair_setting_changed"
        with pytest.raises(ValueError, match="already off"):
            set_enabled({SETTING_KEY: False}, False)
        with pytest.raises(ValueError, match="on or off"):
            set_enabled({}, "off")


class TestSurface:
    def test_parse(self):
        assert parse_repairloop_args("") == {"action": "show"}
        assert parse_repairloop_args("on") == {
            "action": "setting", "enabled": True}
        assert parse_repairloop_args("off") == {
            "action": "setting", "enabled": False}
        with pytest.raises(ValueError, match="Usage"):
            parse_repairloop_args("sideways")

    def test_format_setting_change(self):
        text = format_setting_change({"from": True, "to": False})
        assert "on -> off" in text

    def test_format_packet_shows_the_true_text(self):
        text = format_packet(stale_diff_packet())
        assert "beta = 2" in text
        assert "One honest retry" in text
        assert "no second retry" in text

    def test_show_surface_names_everything(self):
        text = format_apply_repair({})
        assert "Apply-failure repair loop (M-073)" in text
        assert PLAIN_EXPLANATION in text
        assert "Setting: on (apply_repair_loop)" in text
        assert "The one honest retry" in text
        assert "A second retry refuses" in text
        assert "Usage: /repairloop" in text


class TestAgentRepairLoop:
    def test_status(self, agent):
        status = agent.repair_loop_status()
        assert status["enabled"] is True
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_set_without_session(self, agent):
        record = agent.set_apply_repair(False)
        assert record["journaled"] is False
        assert agent.config["apply_repair_loop"] is False
        with pytest.raises(ValueError, match="already off"):
            agent.set_apply_repair(False)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_apply_repair(False)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "apply_repair_setting_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_apply_repair(False)
        assert agent.config.get("apply_repair_loop") is not False
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["apply_repair_setting_changed",
                              "apply_repair_setting_reverted"]
        agent.close()


class TestAgentFormatRepair:
    def test_refusal_returns_the_packet_and_writes_nothing(
            self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.apply_edit_format_with_repair(
            "app.py", "unified-diff", STALE_DIFF)
        assert record["applied"] is False
        assert record["repaired"] is False
        assert "beta = 2" in record["packet"].window.text()
        assert "True current text" in record["packet_text"]
        assert target.read_text(encoding="utf-8") == SOURCE
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "apply_repair_offered" in types
        agent.close()

    def test_one_retry_repairs_and_journals(self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.apply_edit_format_with_repair(
            "app.py", "unified-diff", STALE_DIFF,
            retry_payload=GOOD_DIFF)
        assert record["applied"] is True
        assert record["repaired"] is True
        assert "beta = 20" in target.read_text(encoding="utf-8")
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "apply_repair_offered" in types
        assert "apply_repair_retried" in types
        assert "apply_repair_applied" in types
        from mythic_agent.core.edits import EditJournal
        assert "app.py" in EditJournal(tmp_path).undo()
        agent.close()

    def test_a_bad_retry_exhausts_and_writes_nothing(
            self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        with pytest.raises(ValueError, match="budget is spent"):
            agent.apply_edit_format_with_repair(
                "app.py", "unified-diff", STALE_DIFF,
                retry_payload=STALE_DIFF)
        assert target.read_text(encoding="utf-8") == SOURCE
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "apply_repair_exhausted" in types
        agent.close()

    def test_first_try_success_is_not_a_repair(self, agent, tmp_path):
        (tmp_path / "app.py").write_text(SOURCE, encoding="utf-8")
        record = agent.apply_edit_format_with_repair(
            "app.py", "unified-diff", GOOD_DIFF)
        assert record["repaired"] is False
        assert "beta = 20" in (tmp_path / "app.py").read_text(
            encoding="utf-8")

    def test_gate_off_keeps_the_plain_refusal(self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        agent.set_apply_repair(False)
        with pytest.raises(ValueError, match="context does not match"):
            agent.apply_edit_format_with_repair(
                "app.py", "unified-diff", STALE_DIFF,
                retry_payload=GOOD_DIFF)
        assert target.read_text(encoding="utf-8") == SOURCE


class TestAgentAnchoredRepair:
    def test_range_refusal_returns_the_packet(self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        record = agent.apply_hash_anchored_range_with_repair(
            "app.py", 2, 2, "f" * 64, "beta = 20")
        assert record["applied"] is False
        assert record["packet"].road == "anchored_range"
        assert "beta = 2" in record["packet"].window.text()
        assert target.read_text(encoding="utf-8") == SOURCE

    def test_range_retry_with_the_true_anchor_repairs(
            self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        record = agent.apply_hash_anchored_range_with_repair(
            "app.py", 2, 2, "f" * 64, "beta = 20",
            retry_expected=range_anchor(SOURCE, 2, 2).hash)
        assert record["applied"] is True
        assert record["repaired"] is True
        assert "beta = 20" in target.read_text(encoding="utf-8")

    def test_range_retry_with_a_wrong_anchor_exhausts(
            self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        with pytest.raises(ValueError, match="budget is spent"):
            agent.apply_hash_anchored_range_with_repair(
                "app.py", 2, 2, "f" * 64, "beta = 20",
                retry_expected="e" * 64)
        assert target.read_text(encoding="utf-8") == SOURCE

    def test_search_retry_repairs_from_the_packet(self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        record = agent.apply_hash_anchored_search_with_repair(
            "app.py", "beta = 2", "f" * 64, "beta = 20",
            retry_expected=range_hash(["beta = 2"]))
        assert record["applied"] is True
        assert record["repaired"] is True
        assert "beta = 20" in target.read_text(encoding="utf-8")

    def test_search_nowhere_packet_falls_back_to_the_head(
            self, agent, tmp_path):
        (tmp_path / "app.py").write_text(SOURCE, encoding="utf-8")
        record = agent.apply_hash_anchored_search_with_repair(
            "app.py", "delta = 4", "f" * 64, "delta = 40")
        assert record["applied"] is False
        assert record["packet"].window.start == 1
        assert "alpha = 1" in record["packet"].window.text()

    def test_hash_gate_off_stays_a_plain_refusal(self, agent, tmp_path):
        (tmp_path / "app.py").write_text(SOURCE, encoding="utf-8")
        agent.set_hash_anchored(False)
        with pytest.raises(ValueError, match="are off"):
            agent.apply_hash_anchored_range_with_repair(
                "app.py", 2, 2, "f" * 64, "beta = 20",
                retry_expected=range_anchor(SOURCE, 2, 2).hash)


class TestToolRoad:
    """The agent tool road: refusals return the packet's truth."""

    def _run(self, agent, name, arguments):
        from mythic_agent.agents.tools import execute_tool
        from mythic_agent.core.policy import ToolPolicy
        return execute_tool(name, arguments, agent.project_root,
                            agent=agent, policy=ToolPolicy("trusted"))

    def test_stale_anchored_write_returns_the_true_text(
            self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        result = self._run(agent, "write_file", {
            "path": "app.py", "content": "fresh = 1\n",
            "anchor": "f" * 64})
        assert result.startswith("Failed to write file")
        assert "True current text" in result
        assert "beta = 2" in result
        assert target.read_text(encoding="utf-8") == SOURCE

    def test_true_anchored_write_still_succeeds(self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        result = self._run(agent, "write_file", {
            "path": "app.py", "content": "fresh = 1\n",
            "anchor": range_anchor(SOURCE, 1, 3).hash})
        assert result.startswith("Successfully wrote")

    def test_stale_anchored_replace_returns_the_true_text(
            self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        result = self._run(agent, "replace_file_content", {
            "path": "app.py", "target_content": "beta = 2",
            "replacement_content": "beta = 20", "anchor": "f" * 64})
        assert result.startswith("Failed to replace content")
        assert "True current text" in result
        assert target.read_text(encoding="utf-8") == SOURCE

    def test_ambiguous_replace_returns_the_true_text(
            self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text("x = 1\nx = 1\n", encoding="utf-8")
        result = self._run(agent, "replace_file_content", {
            "path": "app.py", "target_content": "x = 1",
            "replacement_content": "x = 2"})
        assert "must match exactly one" in result
        assert "True current text" in result
        assert target.read_text(encoding="utf-8") == "x = 1\nx = 1\n"

    def test_missing_replace_target_returns_the_head(
            self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        result = self._run(agent, "replace_file_content", {
            "path": "app.py", "target_content": "delta = 4",
            "replacement_content": "delta = 40"})
        assert "must match exactly one" in result
        assert "alpha = 1" in result
        assert target.read_text(encoding="utf-8") == SOURCE


class TestTerminalSurface:
    def test_show_and_set(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/repairloop")
        assert "Apply-failure repair loop (M-073)" in text
        _, _, text = _slash(agent, "/repairloop off")
        assert "on -> off" in text
        assert agent.config["apply_repair_loop"] is False
        _, _, text = _slash(agent, "/repairloop on")
        assert "off -> on" in text

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/repairloop sideways")
        assert "Usage" in text


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


class TestRepairLoopCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_repairloop("")
        assert "Apply-failure repair loop (M-073)" in _published_text(
            handler)

    def test_set_via_the_handler(self, handler, agent):
        handler._handle_repairloop("off")
        assert "on -> off" in _published_text(handler)
        assert agent.config["apply_repair_loop"] is False

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_repairloop("sideways")
        assert "Usage" in _published_text(handler)


class TestChatScreenRouting:
    def test_repairloop_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/repairloop off", _FakeLog())
        assert calls == [("/repairloop", "off")]


class TestConfigContract:
    def test_defaults_ship_on(self):
        import yaml
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        defaults = yaml.safe_load(
            (root / "mythic_agent/data/config_defaults.yaml").read_text(
                encoding="utf-8"))
        assert defaults["apply_repair_loop"] is True

    def test_catalogue_carries_the_setting(self):
        from mythic_agent.core.config_catalog import load_catalog

        by_name = {s.name: s for s in load_catalog().settings}
        assert by_name["apply_repair_loop"].id == "S-62"
        assert by_name["apply_repair_loop"].type == "bool"
        assert by_name["apply_repair_loop"].default == "True"
