"""Tests for M-088: the stash shelf.

TIER: integration
"""

import pytest

from mythic_agent.core import stash_shelf as ss


BASE = {"src/app.py": "x = 1\n", "src/old.py": "gone = True\n"}
WORKING = {"src/app.py": "x = 2\n", "src/new.py": "y = 3\n"}


def _entry(name="half-done fix", base=None, working=None, **kw):
    return ss.build_entry(name, BASE if base is None else base,
                          WORKING if working is None else working, **kw)


def test_build_entry_captures_added_modified_deleted():
    entry = _entry()
    kinds = {c.path: c.kind for c in entry.changes}
    assert kinds == {"src/app.py": "modified",
                     "src/new.py": "added",
                     "src/old.py": "deleted"}
    assert entry.file_count == 3
    assert entry.record()["slice"] == "M-088"
    assert entry.record()["type"] == "stash_shelf_entry"


def test_build_entry_changes_are_sorted_by_path():
    entry = _entry()
    assert [c.path for c in entry.changes] == sorted(
        c.path for c in entry.changes)


def test_build_entry_anchors_match_content():
    entry = _entry()
    for change in entry.changes:
        if change.shelf_content is not None:
            assert change.shelf_anchor == ss.content_anchor(
                change.shelf_content)
        if change.base_content is not None:
            assert change.base_anchor == ss.content_anchor(
                change.base_content)


def test_shelving_nothing_refuses():
    with pytest.raises(ValueError, match="nothing to shelve"):
        ss.build_entry("empty", BASE, dict(BASE))


def test_name_is_stripped_and_kept_as_words():
    entry = _entry(name="  before the auth rework  ")
    assert entry.name == "before the auth rework"


@pytest.mark.parametrize("bad", ["", "   ", "x" * (ss.MAX_NAME_CHARS + 1),
                                 "bad\nname", None, 7])
def test_validate_name_refuses_bad_names(bad):
    with pytest.raises(ValueError):
        ss.validate_name(bad)


@pytest.mark.parametrize("bad", ["/abs/x.py", "../x.py", "a//b.py", ""])
def test_build_entry_refuses_dirty_paths(bad):
    with pytest.raises(ValueError):
        ss.build_entry("n", {bad: "x"}, {bad: "y"})


def test_build_entry_refuses_non_string_text():
    with pytest.raises(ValueError):
        ss.build_entry("n", {"a.py": 1}, {"a.py": 2})


def test_session_id_is_recorded():
    entry = _entry(session_id="session-9")
    assert entry.session_id == "session-9"
    assert entry.record()["session_id"] == "session-9"


def test_clean_tree_returns_the_base_exactly():
    entry = _entry()
    assert ss.clean_tree(BASE, entry) == BASE


def test_clean_tree_refuses_an_entry_from_another_base():
    entry = _entry()
    other = {"src/app.py": "different\n", "src/old.py": "gone = True\n"}
    with pytest.raises(ValueError, match="not shelved against this base"):
        ss.clean_tree(other, entry)


def test_restore_round_trip_brings_the_work_back():
    entry = _entry()
    cleaned = ss.clean_tree(BASE, entry)
    assert ss.restore_tree(entry, BASE, cleaned) == WORKING


def test_restore_deleted_file_removes_it_again():
    entry = _entry()
    restored = ss.restore_tree(entry, BASE, ss.clean_tree(BASE, entry))
    assert "src/old.py" not in restored


def test_restore_conflict_refuses_and_names_the_path():
    entry = _entry()
    moved = dict(BASE)
    moved["src/app.py"] = "someone else's work\n"
    with pytest.raises(ValueError, match="src/app.py"):
        ss.restore_tree(entry, BASE, moved)


def test_restore_conflict_on_an_added_path_refuses():
    entry = _entry()
    moved = dict(BASE)
    moved["src/new.py"] = "clash\n"
    assert ss.restore_conflicts(entry, BASE, moved) == ["src/new.py"]
    with pytest.raises(ValueError):
        ss.restore_tree(entry, BASE, moved)


def test_restore_with_discard_overwrites_on_purpose():
    entry = _entry()
    moved = dict(BASE)
    moved["src/app.py"] = "someone else's work\n"
    restored = ss.restore_tree(entry, BASE, moved, discard=True)
    assert restored == WORKING


def test_restore_refuses_non_bool_discard():
    entry = _entry()
    with pytest.raises(ValueError):
        ss.restore_tree(entry, BASE, dict(BASE), discard="yes")


def test_shelf_refuses_a_duplicate_name():
    shelf = ss.Shelf()
    shelf.shelve(_entry())
    with pytest.raises(ValueError, match="already holds"):
        shelf.shelve(_entry())


def test_shelf_get_and_drop():
    shelf = ss.Shelf([_entry()])
    assert shelf.names() == ["half-done fix"]
    dropped = shelf.drop("half-done fix")
    assert dropped.name == "half-done fix"
    assert len(shelf) == 0
    with pytest.raises(ValueError, match="no shelf entry"):
        shelf.get("half-done fix")


def test_shelf_restore_removes_the_entry_by_default():
    shelf = ss.Shelf([_entry()])
    restored = shelf.restore("half-done fix", BASE, dict(BASE))
    assert restored == WORKING
    assert len(shelf) == 0


def test_shelf_restore_with_keep_leaves_the_entry():
    shelf = ss.Shelf([_entry()])
    shelf.restore("half-done fix", BASE, dict(BASE), keep=True)
    assert shelf.names() == ["half-done fix"]


def test_failed_restore_keeps_the_entry_on_the_shelf():
    shelf = ss.Shelf([_entry()])
    moved = dict(BASE)
    moved["src/app.py"] = "moved\n"
    with pytest.raises(ValueError):
        shelf.restore("half-done fix", BASE, moved)
    assert shelf.names() == ["half-done fix"]


def test_journal_round_trip_restores_across_sessions():
    shelf = ss.Shelf([_entry(session_id="session-1"),
                      _entry(name="second", session_id="session-2")])
    rebuilt, corrupt = ss.Shelf.from_journal_text(shelf.to_journal_text())
    assert corrupt == 0
    assert rebuilt.names() == ["half-done fix", "second"]
    restored = rebuilt.restore("half-done fix", BASE, dict(BASE))
    assert restored == WORKING


def test_journal_torn_last_line_is_counted_not_loaded():
    shelf = ss.Shelf([_entry()])
    text = shelf.to_journal_text() + '{"record": {"type": "stash_shelf_e'
    rebuilt, corrupt = ss.Shelf.from_journal_text(text)
    assert corrupt == 1
    assert rebuilt.names() == ["half-done fix"]


def test_journal_tampered_checksum_is_counted_not_loaded():
    shelf = ss.Shelf([_entry()])
    lines = shelf.to_journal_text().splitlines()
    tampered = lines[0].replace("half-done", "half-doneX")
    rebuilt, corrupt = ss.Shelf.from_journal_text(tampered + "\n")
    assert corrupt == 1
    assert len(rebuilt) == 0


def test_journal_empty_text_is_an_empty_shelf():
    rebuilt, corrupt = ss.Shelf.from_journal_text("")
    assert corrupt == 0
    assert len(rebuilt) == 0


def test_entry_from_record_rejects_a_wrong_anchor():
    record = _entry().record()
    record["changes"][0]["shelf_anchor"] = "0" * 64
    with pytest.raises(ValueError, match="anchor mismatch"):
        ss.entry_from_record(record)


def test_gate_absent_means_on_and_malformed_raises():
    assert ss.enabled_from_config({}) is True
    assert ss.enabled_from_config({ss.SETTING_KEY: False}) is False
    with pytest.raises(ValueError):
        ss.enabled_from_config({ss.SETTING_KEY: "yes"})


def test_set_enabled_validates_the_change():
    after, change = ss.set_enabled({}, False)
    assert after is False
    assert change.event()["type"] == "stash_shelf_setting_changed"
    with pytest.raises(ValueError, match="already on"):
        ss.set_enabled({}, True)
    with pytest.raises(ValueError):
        ss.set_enabled({}, "off")


def test_parse_stash_args_grammar():
    assert ss.parse_stash_args("") == {"action": "show"}
    assert ss.parse_stash_args("list") == {"action": "show"}
    assert ss.parse_stash_args("on") == {"action": "on"}
    assert ss.parse_stash_args("off") == {"action": "off"}
    assert ss.parse_stash_args("shelve before the rework") == {
        "action": "shelve", "name": "before the rework"}
    assert ss.parse_stash_args("restore before the rework") == {
        "action": "restore", "name": "before the rework"}
    assert ss.parse_stash_args("drop before the rework") == {
        "action": "drop", "name": "before the rework"}
    with pytest.raises(ValueError, match="usage"):
        ss.parse_stash_args("shelve")
    with pytest.raises(ValueError, match="usage"):
        ss.parse_stash_args("frobnicate x")


def test_format_shelf_entry_names_files_and_kinds():
    text = ss.format_shelf_entry(_entry())
    assert "half-done fix" in text
    assert "modified: src/app.py" in text
    assert "added: src/new.py" in text
    assert "deleted: src/old.py" in text


def test_format_shelf_list_empty_and_full():
    assert "empty" in ss.format_shelf_list(ss.Shelf())
    text = ss.format_shelf_list(ss.Shelf([_entry()]))
    assert "half-done fix" in text


def test_format_stash_shelf_show_surface_exercises_the_road():
    text = ss.format_stash_shelf({})
    assert "M-088" in text
    assert "half-done fix" in text or "3 file" in text or "file(s)" in text
    assert "on" in text
    off = ss.format_stash_shelf({ss.SETTING_KEY: False})
    assert "off" in off


def test_format_setting_change_words():
    assert ss.format_setting_change({"to": True}) == (
        "The stash shelf is now on.")
    assert ss.format_setting_change({"to": False}) == (
        "The stash shelf is now off.")
