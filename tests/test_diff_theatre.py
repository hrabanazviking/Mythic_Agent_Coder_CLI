"""Tests for M-091: diff theatre in the TUI (pure layer).

TIER: integration
"""

import pytest

from mythic_agent.core import diff_theatre as dt


# --- staging: one change, counted honestly --------------------

def test_identical_texts_stage_as_no_change():
    theatre = dt.build_theatre("a\nb\n", "a\nb\n")
    assert theatre.changed is False
    assert theatre.added == 0 and theatre.removed == 0
    assert theatre.unchanged == 2
    assert "no changes" in dt.render_unified(theatre)


def test_added_and_removed_lines_carry_written_signs():
    theatre = dt.build_theatre("keep\nold\n", "keep\nnew\n")
    signs = {x.kind: x.sign for x in theatre.lines}
    assert signs["add"] == "+"
    assert signs["remove"] == "-"
    assert signs["context"] == " "
    assert theatre.added == 1 and theatre.removed == 1


def test_empty_before_is_all_additions():
    theatre = dt.build_theatre("", "one\ntwo\n")
    assert theatre.added == 2 and theatre.removed == 0
    assert all(x.kind == "add" for x in theatre.lines)


def test_empty_after_is_all_removals():
    theatre = dt.build_theatre("one\ntwo\n", "")
    assert theatre.removed == 2 and theatre.added == 0


def test_both_empty_stage_as_no_change():
    theatre = dt.build_theatre("", "")
    assert theatre.changed is False and theatre.lines == ()


def test_line_numbers_track_both_sides():
    theatre = dt.build_theatre("a\nb\n", "a\nx\nb\n")
    added = [x for x in theatre.lines if x.kind == "add"][0]
    assert added.new_no == 2 and added.old_no is None
    last = theatre.lines[-1]
    assert last.old_no == 2 and last.new_no == 3


def test_unknown_view_raises_instead_of_guessing():
    with pytest.raises(ValueError, match="unknown diff view"):
        dt.build_theatre("a\n", "b\n", view="spiral")


def test_theatre_record_counts_close():
    theatre = dt.build_theatre("a\nold\n", "a\nnew\nextra\n")
    record = theatre.record()
    assert record["added"] == 2 and record["removed"] == 1
    assert record["unchanged"] == 1
    assert len(record["lines"]) == 4


# --- whitespace toggle: judged, flagged, never hidden ---------

def test_whitespace_only_change_detected():
    assert dt.whitespace_only_change("  x = 1", "x = 1") is True
    assert dt.whitespace_only_change("x = 1", "x = 2") is False
    assert dt.whitespace_only_change("x = 1", "x = 1") is False


def test_whitespace_toggle_stages_ws_change_as_context_flagged():
    theatre = dt.build_theatre("  x = 1\ny\n", "x = 1\ny\n",
                               ignore_whitespace=True)
    assert theatre.changed is False
    flagged = [x for x in theatre.lines if x.whitespace_only]
    assert len(flagged) == 1 and flagged[0].kind == "context"
    assert "[whitespace only]" in dt.render_unified(theatre)


def test_whitespace_off_stages_ws_change_as_real_change():
    theatre = dt.build_theatre("  x = 1\n", "x = 1\n",
                               ignore_whitespace=False)
    assert theatre.added == 1 and theatre.removed == 1


def test_real_change_still_changes_with_whitespace_toggle_on():
    theatre = dt.build_theatre("x = 1\n", "x = 2\n",
                               ignore_whitespace=True)
    assert theatre.changed is True
    assert not any(x.whitespace_only for x in theatre.lines)


# --- word level: the words that actually changed ---------------

def test_word_segments_join_back_to_the_exact_lines():
    old, new = "the quick brown fox", "the quick red fox jumps"
    old_segments, new_segments = dt.word_segments(old, new)
    assert "".join(text for _, text in old_segments) == old
    assert "".join(text for _, text in new_segments) == new


def test_word_changes_name_only_the_changed_words():
    removed, added = dt.word_changes("beta old gamma",
                                     "beta new gamma")
    assert removed == ["old"]
    assert added == ["new"]


def test_word_changes_empty_for_identical_lines():
    assert dt.word_changes("same line", "same line") == ([], [])


def test_format_word_change_uses_written_signs():
    text = dt.format_word_change("beta old gamma", "beta new gamma")
    assert "-old" in text and "+new" in text


# --- rendering: colour never the only signal -------------------

def test_render_unified_opens_with_a_counted_header():
    theatre = dt.build_theatre("a\nold\n", "a\nnew\n")
    rendered = dt.render_unified(theatre)
    assert rendered.splitlines()[0].endswith(
        "1 added, 1 removed, 1 unchanged")
    assert "- old" in rendered and "+ new" in rendered


def test_render_unified_shows_the_word_change_for_a_replace():
    theatre = dt.build_theatre("beta old gamma\n",
                               "beta new gamma\n")
    rendered = dt.render_unified(theatre)
    assert "words removed: -old" in rendered
    assert "words added: +new" in rendered


def test_side_by_side_pairs_a_replacement_on_one_row():
    theatre = dt.build_theatre("a\nold\nb\n", "a\nnew\nb\n",
                               view="side_by_side")
    rows = theatre.pairs()
    assert [r.kind for r in rows] == ["equal", "replace", "equal"]
    assert rows[1].left.text == "old"
    assert rows[1].right.text == "new"


def test_side_by_side_unpaired_add_has_no_left_side():
    theatre = dt.build_theatre("a\n", "a\nextra\n",
                               view="side_by_side")
    rows = theatre.pairs()
    assert rows[-1].kind == "add"
    assert rows[-1].left is None and rows[-1].right is not None


def test_render_side_by_side_carries_signs_and_both_texts():
    theatre = dt.build_theatre("old\n", "new\n",
                               view="side_by_side")
    rendered = dt.render_side_by_side(theatre)
    assert "- old" in rendered and "+ new" in rendered
    assert "|" in rendered


def test_render_dispatches_on_the_staged_view():
    unified = dt.build_theatre("a\n", "b\n")
    side = dt.build_theatre("a\n", "b\n", view="side_by_side")
    assert "|" not in dt.render(unified)
    assert "|" in dt.render(side)


# --- gate + grammar ---------------------------------------------

def test_gate_absent_means_on_and_malformed_raises():
    assert dt.enabled_from_config({}) is True
    assert dt.enabled_from_config({"diff_theatre": False}) is False
    with pytest.raises(ValueError, match="must be true or false"):
        dt.enabled_from_config({"diff_theatre": "yes"})


def test_set_enabled_validates_and_records_the_change():
    enabled, change = dt.set_enabled({}, False)
    assert enabled is False
    assert change.event() == {"type": "diff_theatre_setting_changed",
                              "from": True, "to": False}
    with pytest.raises(ValueError, match="already on"):
        dt.set_enabled({}, True)
    with pytest.raises(ValueError, match="turned on or off"):
        dt.set_enabled({}, "off")


def test_parse_diff_args_grammar():
    assert dt.parse_diff_args("") == {"action": "show"}
    assert dt.parse_diff_args("on") == {"action": "on"}
    assert dt.parse_diff_args("off") == {"action": "off"}
    assert dt.parse_diff_args("unified") == {
        "action": "view", "view": "unified"}
    assert dt.parse_diff_args("side-by-side") == {
        "action": "view", "view": "side_by_side"}
    assert dt.parse_diff_args("whitespace") == {
        "action": "whitespace", "ignore_whitespace": True}
    assert dt.parse_diff_args("whitespace off") == {
        "action": "whitespace", "ignore_whitespace": False}
    with pytest.raises(ValueError, match="Usage: /diff"):
        dt.parse_diff_args("explode")


def test_format_diff_theatre_exercises_both_views():
    text = dt.format_diff_theatre({})
    assert "Diff theatre in the TUI (M-091)" in text
    assert "Setting: on (diff_theatre)." in text
    assert "words removed: -old" in text
    assert "|" in text


def test_format_setting_change_plain_words():
    assert dt.format_setting_change({"to": False}) == (
        "Diff theatre is now off.")


# --- agent layer: gate, staging road, surfaces ----------------

from mythic_agent.core.sessions import SessionStore


def _store_for(tmp_path):
    return SessionStore(tmp_path, tmp_path / "state")


class TestAgentGate:
    def test_status(self, agent):
        status = agent.diff_theatre_status()
        assert status["enabled"] is True
        assert status["explanation"] == dt.PLAIN_EXPLANATION

    def test_set_without_session(self, agent):
        record = agent.set_diff_theatre(False)
        assert record["journaled"] is False
        assert agent.config["diff_theatre"] is False
        with pytest.raises(ValueError, match="already"):
            agent.set_diff_theatre(False)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_diff_theatre(False)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "diff_theatre_setting_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_diff_theatre(False)
        assert agent.config.get("diff_theatre") is not False
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["diff_theatre_setting_changed",
                              "diff_theatre_setting_reverted"]
        agent.close()


class TestShowRoad:
    def test_show_stages_and_renders(self, agent):
        record = agent.show_diff_theatre("a\nold\n", "a\nnew\n")
        assert record["type"] == "diff_theatre"
        assert record["added"] == 1 and record["removed"] == 1
        assert "1 added, 1 removed" in record["rendered"]
        assert record["journaled"] is False

    def test_show_side_by_side(self, agent):
        record = agent.show_diff_theatre(
            "a\nold\n", "a\nnew\n", view="side_by_side")
        assert "side_by_side" in record["rendered"]
        assert " | " in record["rendered"]

    def test_show_whitespace_toggle_judges(self, agent):
        record = agent.show_diff_theatre(
            "a  b\n", "a b\n", ignore_whitespace=True)
        assert record["added"] == 0 and record["removed"] == 0
        assert "[whitespace only]" in record["rendered"]

    def test_show_journals_the_staging(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.show_diff_theatre("x\n", "y\n")
        assert record["journaled"] is True
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "diff_theatre" in types
        agent.close()

    def test_gate_off_refuses_and_stages_nothing(self, agent):
        agent.set_diff_theatre(False)
        with pytest.raises(ValueError, match="diff theatre is off"):
            agent.show_diff_theatre("x\n", "y\n")


class TestTerminalSurface:
    def test_show_and_set(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/diff")
        assert "Diff theatre in the TUI (M-091)" in text
        assert "Setting: on (diff_theatre)" in text
        _, _, text = _slash(agent, "/diff off")
        assert "Diff theatre is now off." in text
        assert agent.config["diff_theatre"] is False
        _, _, text = _slash(agent, "/diff on")
        assert "Diff theatre is now on." in text

    def test_view_via_the_terminal(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/diff side-by-side")
        assert "side_by_side" in text
        _, _, text = _slash(agent, "/diff whitespace")
        assert "Diff theatre (unified)" in text

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/diff frobnicate")
        assert "Usage: /diff" in text


@pytest.fixture()
def diff_handler(agent, monkeypatch):
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


def _diff_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestDiffCommand:
    def test_show_is_default(self, diff_handler, agent):
        diff_handler._handle_diff("")
        assert "Diff theatre in the TUI (M-091)" in _diff_published_text(diff_handler)

    def test_set_via_the_handler(self, diff_handler, agent):
        diff_handler._handle_diff("off")
        assert "Diff theatre is now off." in _diff_published_text(diff_handler)
        assert agent.config["diff_theatre"] is False

    def test_view_via_the_handler(self, diff_handler, agent):
        diff_handler._handle_diff("side-by-side")
        assert "side_by_side" in _diff_published_text(diff_handler)

    def test_usage_error_is_published(self, diff_handler, agent):
        diff_handler._handle_diff("frobnicate")
        assert "Usage: /diff" in _diff_published_text(diff_handler)
