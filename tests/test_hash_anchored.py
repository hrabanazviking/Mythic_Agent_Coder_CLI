"""M-072 — Hash-anchored edits.

TIER: integration

Covers the M-072 surface:

* the pure layer (``mythic_agent.core.hash_anchored``):
  per-line SHA-256 anchors and per-range anchors over the
  exact lines joined by newlines (the M-069 content-hash
  road, per-line); the anchored presentation (``annotate``:
  number:short-hash per line — the same lines hash the same
  anywhere, line numbers never ride in a hash); range
  verification in full and short form, with malformed
  anchors refused instead of guessed; anchored range edits
  (replace / grow / shrink / delete lines, only when the
  range's current anchor matches the anchor the edit
  carries — a moved target refuses, names expected vs
  current anchors, and changes nothing); anchored search
  edits (the search text must match exactly once AND its
  lines' anchor must match — zero / several matches and a
  wrong anchor all refuse),
* ``EditJournal`` (the gap audit's owning module, the edits
  core): ``write_anchored_range`` / ``write_anchored_search``
  judging through the pure layer and writing through the
  journal road (undoable like any edit; a refusal writes
  nothing),
* ``Agent``: the gate status, ``set_hash_anchored``
  journaled as ``hash_anchored_setting_changed`` (a failed
  save restoring the previous value and journaling the
  revert), anchored applies riding EditJournal and recorded
  as ``hash_anchored_applied``, refusals writing nothing,
  and the gate off refusing applies plainly,
* the surfaces: the terminal ``/hashanchor`` and the TUI
  ``/hashanchor`` (system-command road through the
  CommandHandler + chat-screen routing), which share the
  parser and formatters,
* the config contract: ``hash_anchored_edits`` ships in the
  defaults (True) and is catalogued (M-009, S-61); the gap
  audit row for hash-anchored-edits is owned by M-072 and
  names the existing edits core.
"""

from __future__ import annotations

import hashlib

import pytest

from mythic_agent.core.hash_anchored import (
    HASH_ANCHORED_SLICE,
    PLAIN_EXPLANATION,
    SETTING_KEY,
    SHORT_HASH_LEN,
    anchor_lines,
    annotate,
    apply_anchored_range,
    apply_anchored_search,
    enabled_from_config,
    format_hash_anchored,
    format_refusal,
    format_setting_change,
    line_hash,
    parse_hashanchor_args,
    range_anchor,
    range_hash,
    set_enabled,
    verify_range,
)
from mythic_agent.core.sessions import SessionStore

SOURCE = "alpha = 1\nbeta = 2\ngamma = 3\n"


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class TestAnchors:
    def test_slice_and_constants(self):
        assert HASH_ANCHORED_SLICE == "M-072"
        assert SETTING_KEY == "hash_anchored_edits"
        assert SHORT_HASH_LEN == 12
        assert PLAIN_EXPLANATION

    def test_line_hash_is_plain_sha256_of_the_exact_line(self):
        assert line_hash("beta = 2") == sha("beta = 2")
        assert line_hash("") == sha("")
        with pytest.raises(ValueError, match="text"):
            line_hash(None)

    def test_range_hash_joins_with_single_newlines(self):
        assert range_hash(["a", "b"]) == sha("a\nb")
        assert range_hash(["a"]) == sha("a")
        with pytest.raises(ValueError, match="empty range"):
            range_hash([])

    def test_anchor_lines_numbers_and_refs(self):
        anchors = anchor_lines(SOURCE)
        assert [a.number for a in anchors] == [1, 2, 3]
        assert anchors[1].hash == line_hash("beta = 2")
        assert anchors[1].short == anchors[1].hash[:12]
        assert anchors[1].ref() == f"2:{anchors[1].short}"
        assert anchors[1].text == "beta = 2"

    def test_anchor_lines_subrange_and_bounds(self):
        anchors = anchor_lines(SOURCE, 2, 3)
        assert [a.number for a in anchors] == [2, 3]
        with pytest.raises(ValueError, match="outside the file"):
            anchor_lines(SOURCE, 0, 2)
        with pytest.raises(ValueError, match="outside the file"):
            anchor_lines(SOURCE, 2, 9)
        assert anchor_lines("") == ()

    def test_range_anchor_and_ref(self):
        anchor = range_anchor(SOURCE, 1, 2)
        assert anchor.hash == range_hash(["alpha = 1", "beta = 2"])
        assert anchor.line_count == 2
        assert anchor.ref() == f"1-2:{anchor.short}"
        with pytest.raises(ValueError, match="outside the file"):
            range_anchor(SOURCE, 3, 2)

    def test_same_lines_same_anchor_anywhere(self):
        other = "zzz\nalpha = 1\nbeta = 2\n"
        assert range_anchor(other, 2, 3).hash == \
            range_anchor(SOURCE, 1, 2).hash
        assert anchor_lines(other, 2, 2)[0].hash == \
            anchor_lines(SOURCE, 1, 1)[0].hash

    def test_annotate_is_the_coders_presentation(self):
        text = annotate(SOURCE)
        lines = text.split("\n")
        assert lines[0] == f"1:{line_hash('alpha = 1')[:12]}| alpha = 1"
        assert lines[2].endswith("| gamma = 3")
        assert annotate(SOURCE, 2, 2).count("\n") == 0

    def test_verify_range_full_short_and_moved(self):
        full = range_anchor(SOURCE, 1, 2).hash
        assert verify_range(SOURCE, 1, 2, full) is True
        assert verify_range(SOURCE, 1, 2, full[:12]) is True
        moved = SOURCE.replace("beta = 2", "beta = 99")
        assert verify_range(moved, 1, 2, full) is False

    def test_verify_refuses_malformed_anchors(self):
        with pytest.raises(ValueError, match="hex"):
            verify_range(SOURCE, 1, 2, "not-an-anchor!")
        with pytest.raises(ValueError, match="12 to 64"):
            verify_range(SOURCE, 1, 2, "abc123")


class TestApplyAnchoredRange:
    def test_applies_under_the_true_anchor(self):
        anchor = range_anchor(SOURCE, 2, 2).hash
        new, applied = apply_anchored_range(
            SOURCE, 2, 2, anchor, "beta = 20")
        assert new == "alpha = 1\nbeta = 20\ngamma = 3\n"
        assert applied.before.hash == anchor
        assert applied.units == 1
        assert applied.start == 2 and applied.end == 2

    def test_short_anchor_applies_too(self):
        short = range_anchor(SOURCE, 1, 1).short
        new, _ = apply_anchored_range(SOURCE, 1, 1, short, "alpha = 9")
        assert new.startswith("alpha = 9\n")

    def test_grow_shrink_and_delete(self):
        a12 = range_anchor(SOURCE, 1, 2).hash
        new, _ = apply_anchored_range(SOURCE, 1, 2, a12, "x\ny\nz")
        assert new == "x\ny\nz\ngamma = 3\n"
        a2 = range_anchor(SOURCE, 2, 2).hash
        new, _ = apply_anchored_range(SOURCE, 2, 2, a2, "")
        assert new == "alpha = 1\ngamma = 3\n"

    def test_moved_target_refuses_and_names_both_anchors(self):
        stale = range_anchor(SOURCE, 2, 2).hash
        moved = SOURCE.replace("beta = 2", "beta = 99")
        with pytest.raises(ValueError) as excinfo:
            apply_anchored_range(moved, 2, 2, stale, "beta = 20")
        message = str(excinfo.value)
        assert "refused" in message
        assert stale[:12] in message
        assert line_hash("beta = 99")[:12] in message
        assert moved == SOURCE.replace("beta = 2", "beta = 99")

    def test_out_of_range_refuses(self):
        with pytest.raises(ValueError, match="outside the file"):
            apply_anchored_range(SOURCE, 4, 4, "a" * 64, "x")


class TestApplyAnchoredSearch:
    def test_applies_the_one_match_under_its_anchor(self):
        anchor = range_hash(["beta = 2"])
        new, applied = apply_anchored_search(
            SOURCE, "beta = 2", anchor, "beta = 20")
        assert "beta = 20" in new
        assert (applied.start, applied.end) == (2, 2)

    def test_wrong_anchor_refuses_even_when_text_matches(self):
        wrong = range_hash(["some other line"])
        with pytest.raises(ValueError, match="refused"):
            apply_anchored_search(SOURCE, "beta = 2", wrong, "x")

    def test_zero_and_several_matches_refuse(self):
        with pytest.raises(ValueError, match="matched nothing"):
            apply_anchored_search(SOURCE, "delta = 4", "a" * 64, "x")
        doubled = "same\nsame\n"
        with pytest.raises(ValueError, match="exactly once"):
            apply_anchored_search(
                doubled, "same", range_hash(["same"]), "other")

    def test_empty_search_refuses(self):
        with pytest.raises(ValueError, match="needs the text"):
            apply_anchored_search(SOURCE, "", "a" * 64, "x")


class TestSetting:
    def test_absent_means_on_and_bool_round_trips(self):
        assert enabled_from_config({}) is True
        assert enabled_from_config({SETTING_KEY: False}) is False
        with pytest.raises(ValueError, match="true or false"):
            enabled_from_config({SETTING_KEY: "yes"})

    def test_set_enabled_validates(self):
        value, change = set_enabled({}, False)
        assert value is False
        assert change.event() == {
            "type": "hash_anchored_setting_changed",
            "from": True, "to": False}
        with pytest.raises(ValueError, match="already on"):
            set_enabled({}, True)
        with pytest.raises(ValueError, match="on or off"):
            set_enabled({}, "off")


class TestSurface:
    def test_parse(self):
        assert parse_hashanchor_args("") == {"action": "show"}
        assert parse_hashanchor_args("on") == {
            "action": "setting", "enabled": True}
        assert parse_hashanchor_args("off") == {
            "action": "setting", "enabled": False}
        with pytest.raises(ValueError, match="Usage"):
            parse_hashanchor_args("sideways")

    def test_format_setting_change(self):
        assert format_setting_change({"from": True, "to": False}) == \
            "Hash-anchored edits: on -> off."

    def test_format_refusal_names_the_move(self):
        from mythic_agent.core.hash_anchored import RefusalReport
        report = RefusalReport(
            start=2, end=2, expected="a" * 64, current="b" * 64,
            reason="lines 2-2 moved")
        assert "refused" in format_refusal(report)
        assert "lines 2-2 moved" in format_refusal(report)

    def test_show_surface_names_everything(self):
        text = format_hash_anchored({})
        assert PLAIN_EXPLANATION in text
        assert "Hash-anchored edits (M-072)" in text
        assert "Setting: on" in text
        assert "1:" in text and "| alpha = 1" in text
        assert format_hash_anchored(
            {SETTING_KEY: False}).split("\n")[2] == \
            "Setting: off (hash_anchored_edits)."


class TestEditJournalAnchored:
    def test_write_anchored_range_rides_the_journal(self, agent, tmp_path):
        from mythic_agent.core.edits import EditJournal
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        anchor = range_anchor(SOURCE, 2, 2).hash
        EditJournal(tmp_path).write_anchored_range(
            "app.py", 2, 2, anchor, "beta = 20")
        assert "beta = 20" in target.read_text(encoding="utf-8")
        message = EditJournal(tmp_path).undo()
        assert "app.py" in message
        assert target.read_text(encoding="utf-8") == SOURCE

    def test_write_anchored_search_and_refusal_writes_nothing(
            self, agent, tmp_path):
        from mythic_agent.core.edits import EditJournal
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        EditJournal(tmp_path).write_anchored_search(
            "app.py", "gamma = 3", range_hash(["gamma = 3"]),
            "gamma = 30")
        assert "gamma = 30" in target.read_text(encoding="utf-8")
        with pytest.raises(ValueError, match="refused"):
            EditJournal(tmp_path).write_anchored_range(
                "app.py", 1, 1, "f" * 64, "nope")
        assert "alpha = 1" in target.read_text(encoding="utf-8")


class TestAgentHashAnchored:
    def test_status(self, agent):
        status = agent.hash_anchor_status()
        assert status["enabled"] is True
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_set_without_session(self, agent):
        record = agent.set_hash_anchored(False)
        assert record["journaled"] is False
        assert agent.config["hash_anchored_edits"] is False
        with pytest.raises(ValueError, match="already off"):
            agent.set_hash_anchored(False)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_hash_anchored(False)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "hash_anchored_setting_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_hash_anchored(False)
        assert agent.config.get("hash_anchored_edits") is not False
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["hash_anchored_setting_changed",
                              "hash_anchored_setting_reverted"]
        agent.close()

    def test_apply_range_rides_edit_journal_and_journals(
            self, agent, tmp_path):
        (tmp_path / "app.py").write_text(SOURCE, encoding="utf-8")
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.apply_hash_anchored_range(
            "app.py", 2, 2, range_anchor(SOURCE, 2, 2).hash,
            "beta = 20")
        assert record["journaled"] is True
        assert record["units"] == 1
        assert "beta = 20" in (tmp_path / "app.py").read_text(
            encoding="utf-8")
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "hash_anchored_applied" in types
        from mythic_agent.core.edits import EditJournal
        assert "app.py" in EditJournal(tmp_path).undo()
        agent.close()

    def test_apply_search(self, agent, tmp_path):
        (tmp_path / "app.py").write_text(SOURCE, encoding="utf-8")
        record = agent.apply_hash_anchored_search(
            "app.py", "gamma = 3", range_hash(["gamma = 3"]),
            "gamma = 30")
        assert record["changed"] is True
        assert "gamma = 30" in (tmp_path / "app.py").read_text(
            encoding="utf-8")

    def test_moved_target_writes_nothing(self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        with pytest.raises(ValueError, match="refused"):
            agent.apply_hash_anchored_range(
                "app.py", 2, 2, "f" * 64, "beta = 20")
        assert target.read_text(encoding="utf-8") == SOURCE

    def test_gate_off_refuses_applies_plainly(self, agent, tmp_path):
        (tmp_path / "app.py").write_text(SOURCE, encoding="utf-8")
        agent.set_hash_anchored(False)
        with pytest.raises(ValueError, match="are off"):
            agent.apply_hash_anchored_range(
                "app.py", 2, 2, range_anchor(SOURCE, 2, 2).hash,
                "beta = 20")
        assert (tmp_path / "app.py").read_text(
            encoding="utf-8") == SOURCE

    def test_missing_file_refuses(self, agent):
        with pytest.raises(ValueError, match="does not exist"):
            agent.apply_hash_anchored_range(
                "nope.py", 1, 1, "a" * 64, "x")


class TestToolRoad:
    """The agent tool road: anchored writes via the tools."""

    def _run(self, agent, name, arguments):
        from mythic_agent.agents.tools import execute_tool
        from mythic_agent.core.policy import ToolPolicy
        return execute_tool(name, arguments, agent.project_root,
                            agent=agent, policy=ToolPolicy("trusted"))

    def test_write_file_with_a_true_anchor(self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        anchor = range_anchor(SOURCE, 1, 3).hash
        result = self._run(agent, "write_file", {
            "path": "app.py", "content": "fresh = 1\n",
            "anchor": anchor})
        assert result.startswith("Successfully wrote")
        assert target.read_text(encoding="utf-8") == "fresh = 1\n"

    def test_write_file_with_a_stale_anchor_refuses(self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        result = self._run(agent, "write_file", {
            "path": "app.py", "content": "fresh = 1\n",
            "anchor": "f" * 64})
        assert result.startswith("Failed to write file")
        assert "refused" in result
        assert target.read_text(encoding="utf-8") == SOURCE

    def test_replace_with_a_true_anchor(self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        result = self._run(agent, "replace_file_content", {
            "path": "app.py", "target_content": "beta = 2",
            "replacement_content": "beta = 20",
            "anchor": range_hash(["beta = 2"])})
        assert result.startswith("Successfully replaced")
        assert "beta = 20" in target.read_text(encoding="utf-8")

    def test_replace_with_a_stale_anchor_refuses(self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        result = self._run(agent, "replace_file_content", {
            "path": "app.py", "target_content": "beta = 2",
            "replacement_content": "beta = 20",
            "anchor": "f" * 64})
        assert result.startswith("Failed to replace content")
        assert target.read_text(encoding="utf-8") == SOURCE

    def test_replace_without_an_anchor_is_the_old_road(
            self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        result = self._run(agent, "replace_file_content", {
            "path": "app.py", "target_content": "beta = 2",
            "replacement_content": "beta = 20"})
        assert result.startswith("Successfully replaced")


class TestTerminalSurface:
    def test_show_and_set(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/hashanchor")
        assert "Hash-anchored edits (M-072)" in text
        _, _, text = _slash(agent, "/hashanchor off")
        assert "on -> off" in text
        assert agent.config["hash_anchored_edits"] is False
        _, _, text = _slash(agent, "/hashanchor on")
        assert "off -> on" in text

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/hashanchor sideways")
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


class TestHashAnchorCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_hashanchor("")
        assert "Hash-anchored edits (M-072)" in _published_text(handler)

    def test_set_via_the_handler(self, handler, agent):
        handler._handle_hashanchor("off")
        assert "on -> off" in _published_text(handler)
        assert agent.config["hash_anchored_edits"] is False

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_hashanchor("sideways")
        assert "Usage" in _published_text(handler)


class TestChatScreenRouting:
    def test_hashanchor_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/hashanchor off", _FakeLog())
        assert calls == [("/hashanchor", "off")]


class TestConfigContract:
    def test_defaults_ship_on(self):
        import yaml
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        defaults = yaml.safe_load(
            (root / "mythic_agent/data/config_defaults.yaml").read_text(
                encoding="utf-8"))
        assert defaults["hash_anchored_edits"] is True

    def test_catalogue_carries_the_setting(self):
        from mythic_agent.core.config_catalog import load_catalog

        by_name = {s.name: s for s in load_catalog().settings}
        assert by_name["hash_anchored_edits"].id == "S-61"
        assert by_name["hash_anchored_edits"].type == "bool"
        assert by_name["hash_anchored_edits"].default == "True"

    def test_gap_audit_row_is_owned_by_m072_in_the_edits_core(self):
        from pathlib import Path

        from mythic_agent.core.gap_audit import load_audit

        root = Path(__file__).resolve().parents[1]
        row = {r.feature: r for r in load_audit().rows}[
            "hash-anchored-edits"]
        assert row.slice == "M-072"
        assert row.owning_module == "mythic_agent/core/edits.py"
        assert row.module_kind == "existing"
        assert row.state == "MISSING"
        assert (root / row.owning_module).is_file()
