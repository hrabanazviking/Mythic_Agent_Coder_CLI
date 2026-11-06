"""Tests for M-090: editor bridges lite (pure layer).

TIER: integration
"""

import pytest

from mythic_agent.core import editor_bridge as eb


# --- resolution: the terminal's own precedence ---------------

def test_visual_wins_over_editor():
    choice = eb.resolve_editor(
        {"VISUAL": "code --wait", "EDITOR": "nano"})
    assert choice.source == "VISUAL"
    assert choice.name == "code"
    assert choice.argv == ("code", "--wait")


def test_editor_used_when_visual_absent():
    choice = eb.resolve_editor({"EDITOR": "vim"})
    assert choice.source == "EDITOR"
    assert choice.argv == ("vim",)


def test_whitespace_visual_counts_as_unset():
    choice = eb.resolve_editor({"VISUAL": "  ", "EDITOR": "nano"})
    assert choice.source == "EDITOR"


def test_no_editor_refuses_and_names_the_remedy():
    with pytest.raises(ValueError, match="no editor is configured"):
        eb.resolve_editor({})
    with pytest.raises(ValueError, match="EDITOR"):
        eb.resolve_editor({"VISUAL": "", "EDITOR": " "})


def test_editor_value_split_like_a_shell():
    choice = eb.resolve_editor({"EDITOR": "emacs -nw"})
    assert choice.argv == ("emacs", "-nw")


def test_malformed_editor_value_raises():
    with pytest.raises(ValueError, match="cannot be split"):
        eb.resolve_editor({"EDITOR": "code 'unterminated"})


def test_editor_command_appends_the_scratch_path():
    argv = eb.editor_command({"EDITOR": "nano"}, "/tmp/x.py")
    assert argv == ["nano", "/tmp/x.py"]


def test_editor_command_refuses_without_an_editor():
    with pytest.raises(ValueError, match="no editor is configured"):
        eb.editor_command({}, "/tmp/x.py")


# --- preparation: anchors and scratch names -------------------

def test_file_round_trip_keeps_its_suffix():
    trip = eb.prepare_file_round_trip("src/app.py", "x = 1\n")
    assert trip.kind == "file"
    assert trip.scratch_name.endswith(".py")
    assert trip.record()["label"] == "src/app.py"


def test_file_without_suffix_gets_a_text_suffix():
    trip = eb.prepare_file_round_trip("Makefile", "all:\n")
    assert trip.scratch_name.endswith(".txt")


def test_prompt_round_trip_travels_as_prose():
    trip = eb.prepare_prompt_round_trip("approval draft", "do it\n")
    assert trip.kind == "prompt"
    assert trip.scratch_name.endswith(".md")


def test_scratch_names_differ_for_different_texts():
    one = eb.prepare_file_round_trip("a.py", "x = 1\n")
    two = eb.prepare_file_round_trip("a.py", "x = 2\n")
    assert one.scratch_name != two.scratch_name


def test_prepare_needs_a_path_and_a_label():
    with pytest.raises(ValueError, match="needs a path"):
        eb.prepare_file_round_trip(" ", "x\n")
    with pytest.raises(ValueError, match="needs a label"):
        eb.prepare_prompt_round_trip("", "x\n")


# --- judgement: changed / unchanged / emptied -----------------

def test_unchanged_text_judged_unchanged():
    trip = eb.prepare_file_round_trip("a.py", "x = 1\n")
    outcome = eb.judge_round_trip(trip, "x = 1\n")
    assert outcome.status == "unchanged"
    assert outcome.text == "x = 1\n"


def test_changed_text_judged_changed_with_new_text():
    trip = eb.prepare_prompt_round_trip("chat draft", "hi\n")
    outcome = eb.judge_round_trip(trip, "hi, edited\n")
    assert outcome.status == "changed"
    assert outcome.text == "hi, edited\n"
    record = outcome.record(trip)
    assert record["anchor_before"] != record["anchor_after"]


def test_emptied_file_refuses_and_original_stands():
    trip = eb.prepare_file_round_trip("a.py", "x = 1\n")
    outcome = eb.judge_round_trip(trip, "")
    assert outcome.status == "refused"
    assert outcome.text is None
    assert "never silently truncated" in outcome.reason


def test_emptied_prompt_is_a_cancellation():
    trip = eb.prepare_prompt_round_trip("chat draft", "hi\n")
    outcome = eb.judge_round_trip(trip, "  \n")
    assert outcome.status == "cancelled"
    assert outcome.text is None


# --- the gate ---------------------------------------------------

def test_gate_absent_means_on_and_malformed_raises():
    assert eb.enabled_from_config({}) is True
    assert eb.enabled_from_config({"editor_bridge": False}) is False
    with pytest.raises(ValueError, match="editor_bridge"):
        eb.enabled_from_config({"editor_bridge": "yes"})


def test_set_enabled_records_the_change():
    enabled, change = eb.set_enabled({}, False)
    assert enabled is False
    assert change.event() == {
        "type": "editor_bridge_setting_changed",
        "from": True, "to": False}
    record = change.record("s1", True)
    assert record["session_id"] == "s1"
    assert record["journaled"] is True


def test_set_enabled_refuses_same_value_and_non_bool():
    with pytest.raises(ValueError, match="already on"):
        eb.set_enabled({}, True)
    with pytest.raises(ValueError, match="on or off"):
        eb.set_enabled({}, "off")


# --- the shared /editor grammar ---------------------------------

def test_parse_editor_args():
    assert eb.parse_editor_args("") == {"action": "show"}
    assert eb.parse_editor_args("on") == {"action": "on"}
    assert eb.parse_editor_args("off") == {"action": "off"}
    assert eb.parse_editor_args("prompt") == {"action": "prompt"}
    assert eb.parse_editor_args("file src/my file.py") == {
        "action": "file", "path": "src/my file.py"}


def test_parse_editor_args_rejects_bad_grammar():
    with pytest.raises(ValueError, match="Usage: /editor"):
        eb.parse_editor_args("file")
    with pytest.raises(ValueError, match="Usage: /editor"):
        eb.parse_editor_args("launch")


# --- formatters ---------------------------------------------------

def test_format_editor_bridge_names_editor_and_setting():
    text = eb.format_editor_bridge({}, {"EDITOR": "nano"})
    assert "Editor bridges lite (M-090)" in text
    assert "Setting: on (editor_bridge)" in text
    assert "Editor: nano (from EDITOR: nano)" in text
    assert "changed" in text


def test_format_editor_bridge_states_absence_honestly():
    text = eb.format_editor_bridge({"editor_bridge": False}, {})
    assert "Setting: off (editor_bridge)" in text
    assert "Editor: none - no editor is configured" in text


def test_format_setting_change_and_round_trip():
    assert eb.format_setting_change({"to": False}) == \
        "Editor bridge is now off."
    trip = eb.prepare_file_round_trip("a.py", "x = 1\n")
    outcome = eb.judge_round_trip(trip, "x = 2\n")
    text = eb.format_round_trip(trip, outcome)
    assert "changed" in text
    assert "a.py" in text
