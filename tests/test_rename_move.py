"""Tests for M-085: rename/move files as first-class edits."""

import pytest

from mythic_agent.core import rename_move as rm


EXISTING = ["pkg/mod.py", "pkg/__init__.py", "app.py", "docs/guide.md"]


def test_module_name_for_plain_module():
    assert rm.module_name_for("pkg/mod.py") == "pkg.mod"


def test_module_name_for_init_is_package():
    assert rm.module_name_for("pkg/__init__.py") == "pkg"


def test_module_name_for_non_python_is_none():
    assert rm.module_name_for("docs/guide.md") is None


def test_plan_move_happy_path_uses_git_mv():
    plan = rm.plan_move("pkg/mod.py", "pkg/renamed.py", existing=EXISTING)
    assert plan.git_argv == ("git", "mv", "pkg/mod.py", "pkg/renamed.py")
    assert plan.updates == ()
    assert plan.warnings == ()


def test_plan_move_refuses_missing_source():
    with pytest.raises(ValueError, match="does not exist"):
        rm.plan_move("pkg/nope.py", "pkg/x.py", existing=EXISTING)


def test_plan_move_refuses_existing_destination():
    with pytest.raises(ValueError, match="already exists"):
        rm.plan_move("pkg/mod.py", "app.py", existing=EXISTING)


def test_plan_move_refuses_same_path():
    with pytest.raises(ValueError, match="same"):
        rm.plan_move("app.py", "app.py", existing=EXISTING)


@pytest.mark.parametrize("bad", ["/abs/path.py", "../up.py", "a//b.py",
                                 "a/./b.py", "", "  "])
def test_plan_move_refuses_dirty_paths(bad):
    with pytest.raises(ValueError):
        rm.plan_move(bad, "pkg/x.py", existing=EXISTING)


def test_plan_move_refuses_directory_into_itself():
    with pytest.raises(ValueError, match="into itself"):
        rm.plan_move("pkg", "pkg/inner", existing=["pkg"],
                     is_directory=True)


def test_reference_update_rewrites_module_and_path_tokens():
    text = "import pkg.mod\nPATH = 'pkg/mod.py'\n"
    plan = rm.plan_move("pkg/mod.py", "pkg/renamed.py", existing=EXISTING,
                        referencing=["app.py"], texts={"app.py": text})
    assert len(plan.updates) == 1
    update = plan.updates[0]
    assert update.replacements == 2
    assert "import pkg.renamed" in update.new_text
    assert "pkg/renamed.py" in update.new_text


def test_reference_update_leaves_longer_names_alone():
    text = "import pkg.modular\nimport pkg.mod\n"
    plan = rm.plan_move("pkg/mod.py", "pkg/renamed.py", existing=EXISTING,
                        referencing=["app.py"], texts={"app.py": text})
    update = plan.updates[0]
    assert update.replacements == 1
    assert "pkg.modular" in update.new_text


def test_reference_update_for_init_move_rewrites_package():
    text = "from pkg import thing\n"
    plan = rm.plan_move("pkg/__init__.py", "pack/__init__.py",
                        existing=EXISTING, referencing=["app.py"],
                        texts={"app.py": text})
    assert plan.updates[0].new_text == "from pack import thing\n"


def test_referencing_file_without_text_warns():
    plan = rm.plan_move("pkg/mod.py", "pkg/renamed.py", existing=EXISTING,
                        referencing=["app.py"], texts={})
    assert plan.updates == ()
    assert len(plan.warnings) == 1
    assert "not supplied" in plan.warnings[0]


def test_referencing_file_without_token_warns():
    plan = rm.plan_move("pkg/mod.py", "pkg/renamed.py", existing=EXISTING,
                        referencing=["app.py"],
                        texts={"app.py": "nothing here\n"})
    assert plan.updates == ()
    assert "no exact" in plan.warnings[0]


def test_source_itself_is_not_a_reference_target():
    plan = rm.plan_move("pkg/mod.py", "pkg/renamed.py", existing=EXISTING,
                        referencing=["pkg/mod.py"],
                        texts={"pkg/mod.py": "import pkg.mod\n"})
    assert plan.updates == ()
    assert plan.warnings == ()


def test_record_carries_slice_and_command():
    plan = rm.plan_move("app.py", "main.py", existing=EXISTING)
    record = plan.record()
    assert record["slice"] == "M-085"
    assert record["command"] == ["git", "mv", "app.py", "main.py"]
    assert record["type"] == "file_moved"


def test_format_move_plan_names_history_and_updates():
    plan = rm.plan_move("pkg/mod.py", "pkg/renamed.py", existing=EXISTING,
                        referencing=["app.py"],
                        texts={"app.py": "import pkg.mod\n"})
    rendered = rm.format_move_plan(plan)
    assert "git mv pkg/mod.py pkg/renamed.py" in rendered
    assert "app.py: 1 replacement(s)" in rendered


def test_enabled_defaults_on_and_reads_stored_bool():
    assert rm.enabled_from_config({}) is True
    assert rm.enabled_from_config({"rename_move": False}) is False


def test_enabled_malformed_raises():
    with pytest.raises(ValueError, match="true or false"):
        rm.enabled_from_config({"rename_move": "yes"})


def test_set_enabled_roundtrip_and_noop_refusal():
    enabled, change = rm.set_enabled({}, False)
    assert enabled is False
    assert change.event()["type"] == "rename_move_setting_changed"
    with pytest.raises(ValueError, match="already"):
        rm.set_enabled({}, True)


def test_parse_move_and_gate_words():
    assert rm.parse_rename_args("") == {"action": "show"}
    assert rm.parse_rename_args("off") == {"action": "off"}
    parsed = rm.parse_rename_args("a/b.py c/d.py")
    assert parsed == {"action": "move", "source": "a/b.py",
                      "destination": "c/d.py"}


def test_parse_refuses_bad_grammar():
    with pytest.raises(ValueError, match="usage"):
        rm.parse_rename_args("only-one")
    with pytest.raises(ValueError, match="usage"):
        rm.parse_rename_args("a b c")
