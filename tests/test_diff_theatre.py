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
