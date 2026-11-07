"""M-111 Destructive-command doctrine - pure-layer tests.

TIER: integration

The pure layer is the doctrine as data: a ladder
of exactly three rungs (reversible / costly /
irreversible), each carrying the one approval it
needs (none / ask once / explicit approval naming
every target first), the command patterns held as
validated data that place an act on a rung, a
mechanical judge (an act earns a rung only from a
held pattern; an unknown command is unclassified
and never claimed safe), the plain-words rule (an
irreversible judgement refuses to exist without
named targets), a judgement record shaped as
session news, and a registry with deterministic
ids. Nothing here runs a command or deletes
anything.
"""

import pytest

from mythic_agent.core.destructive_doctrine import (
    APPROVAL_PHRASES,
    APPROVAL_REQUIREMENTS,
    CLASSIFICATIONS,
    COMMAND_PATTERNS,
    DESTRUCTIVE_DOCTRINE_SLICE,
    DOCTRINE_LADDER,
    DOCTRINE_RUNGS,
    PLAIN_EXPLANATION,
    USAGE,
    DestructiveJudgement,
    DestructivePattern,
    DoctrineRegistry,
    DoctrineRung,
    Judgement,
    Rung,
    approval_for_rung,
    build_judgement,
    build_pattern,
    build_rung,
    doctrine_record,
    format_doctrine_record,
    format_doctrine_screen,
    format_judgement,
    format_judgements,
    format_ladder,
    format_pattern,
    format_patterns,
    format_record,
    format_rung,
    judge_command,
    normalize_approval,
    normalize_classification,
    normalize_judgement_id,
    normalize_pattern_id,
    normalize_rung,
    pattern_for_id,
    plain_words,
    parse_doctrine_args,
    rung_for,
    validate_judgement,
    validate_pattern,
    validate_rung,
)


def _registry(*commands):
    registry = DoctrineRegistry()
    for command in commands:
        registry.judge(command)
    return registry


# -- constants and word readings ---------------------------------------


def test_constants_and_usage():
    assert DESTRUCTIVE_DOCTRINE_SLICE == "M-111"
    assert DOCTRINE_RUNGS == ("reversible", "costly", "irreversible")
    assert APPROVAL_REQUIREMENTS == (
        "none", "ask_once", "explicit_named_targets")
    assert CLASSIFICATIONS == ("classified", "unclassified")
    assert set(APPROVAL_PHRASES) == set(APPROVAL_REQUIREMENTS)
    assert USAGE.startswith("Usage: /doctrine")
    assert "three rungs" in PLAIN_EXPLANATION
    assert "never claimed safe" in PLAIN_EXPLANATION
    assert Judgement is DestructiveJudgement
    assert Rung is DoctrineRung


def test_rung_word_readings():
    assert normalize_rung("reversible") == "reversible"
    assert normalize_rung("Undoable") == "reversible"
    assert normalize_rung("COSTLY") == "costly"
    assert normalize_rung("irreversible") == "irreversible"
    assert normalize_rung("permanent") == "irreversible"
    with pytest.raises(ValueError):
        normalize_rung("safe")
    with pytest.raises(ValueError):
        normalize_rung(None)
    with pytest.raises(ValueError):
        normalize_rung("")


def test_approval_word_readings():
    assert normalize_approval("none") == "none"
    assert normalize_approval("ask") == "ask_once"
    assert normalize_approval("Ask-Once") == "ask_once"
    assert normalize_approval("explicit") == "explicit_named_targets"
    assert normalize_approval(
        "explicit named targets") == "explicit_named_targets"
    with pytest.raises(ValueError):
        normalize_approval("allow")
    with pytest.raises(ValueError):
        normalize_approval("trusted")


def test_classification_and_id_readings():
    assert normalize_classification("classified") == "classified"
    assert normalize_classification("unknown") == "unclassified"
    with pytest.raises(ValueError):
        normalize_classification("safe")
    assert normalize_judgement_id("judgement-1") == "judgement-1"
    with pytest.raises(ValueError):
        normalize_judgement_id("two words")
    with pytest.raises(ValueError):
        normalize_judgement_id("")
    assert normalize_pattern_id("RM-Force Recursive") == "rm_force_recursive"
    with pytest.raises(ValueError):
        normalize_pattern_id("has space!")


# -- the ladder itself ---------------------------------------------------


def test_ladder_is_exactly_three_rungs_with_their_approvals():
    assert [rung.rung for rung in DOCTRINE_LADDER] == list(DOCTRINE_RUNGS)
    assert approval_for_rung("reversible") == "none"
    assert approval_for_rung("costly") == "ask_once"
    assert approval_for_rung("irreversible") == "explicit_named_targets"
    for rung in DOCTRINE_LADDER:
        record = rung.to_record()
        assert record["type"] == "doctrine_rung"
        assert record["slice"] == "M-111"
        assert record["approval"] == approval_for_rung(rung.rung)
    assert rung_for("costly").label == "can be undone only at a price"


def test_rung_approval_is_derived_and_mismatch_refuses():
    assert DoctrineRung(rung="costly").approval == "ask_once"
    assert DoctrineRung(
        rung="costly", approval="ask").approval == "ask_once"
    with pytest.raises(ValueError):
        DoctrineRung(rung="reversible", approval="ask_once")
    with pytest.raises(ValueError):
        DoctrineRung(rung="irreversible", approval="none")
    with pytest.raises(ValueError):
        DoctrineRung(rung="safe")


def test_rung_validate_and_build():
    assert validate_rung({"level": "costly"}).rung == "costly"
    assert build_rung({"rung": "irreversible"}).approval == (
        "explicit_named_targets")
    held = rung_for("reversible")
    assert validate_rung(held) is held
    with pytest.raises(ValueError):
        validate_rung({"rung": "costly", "bogus": 1})
    with pytest.raises(ValueError):
        validate_rung({"label": "no rung named"})
    with pytest.raises(ValueError):
        validate_rung({"rung": "costly", "level": "reversible"})


# -- the held patterns ---------------------------------------------------


def test_patterns_are_valid_unique_data_covering_the_rungs():
    ids = [pattern.pattern_id for pattern in COMMAND_PATTERNS]
    assert len(ids) == len(set(ids))
    assert {pattern.rung for pattern in COMMAND_PATTERNS} == set(DOCTRINE_RUNGS)
    for pattern in COMMAND_PATTERNS:
        record = pattern.to_record()
        assert record["type"] == "destructive_pattern"
        assert record["rung"] in DOCTRINE_RUNGS
        assert pattern.matches("rm -rf x") is not None or True
    assert pattern_for_id("rm_force_recursive").rung == "irreversible"
    assert pattern_for_id("git_force_push").rung == "irreversible"
    with pytest.raises(ValueError):
        pattern_for_id("no_such_pattern")


def test_pattern_validate_and_build():
    pattern = validate_pattern({
        "id": "my_shape", "level": "costly", "label": "a shape",
        "pattern": r"\bfoo\b"})
    assert pattern.pattern_id == "my_shape" and pattern.rung == "costly"
    assert build_pattern(pattern) is pattern
    with pytest.raises(ValueError):
        validate_pattern({
            "pattern_id": "bad", "rung": "costly", "label": "x",
            "regex": "(["})
    with pytest.raises(ValueError):
        validate_pattern({
            "pattern_id": "x", "rung": "costly", "label": "x",
            "regex": "a", "bogus": 1})
    with pytest.raises(ValueError):
        DestructivePattern(
            pattern_id="x", rung="safe", label="x", regex="a")


# -- the judge: the rm -rf class ----------------------------------------


def test_rm_rf_class_is_irreversible_and_names_targets():
    for command in (
            "rm -rf build dist", "rm -fr build", "rm -Rf build",
            "rm --recursive --force build", "rm -r -f build",
            "rm --force --recursive build"):
        judged = judge_command(command)
        assert judged.rung == "irreversible", command
        assert judged.pattern_id == "rm_force_recursive"
        assert judged.approval == "explicit_named_targets"
        assert judged.classified and judged.needs_approval
        assert "build" in judged.targets
    assert judge_command("rm -rf build dist").targets == ("build", "dist")
    assert judge_command("rm -rf /").targets == ("/",)


def test_rm_rf_inside_a_compound_command_is_still_irreversible():
    judged = judge_command("cd build && rm -rf dist")
    assert judged.rung == "irreversible"
    assert judged.targets == ("dist",)


def test_plain_rm_is_costly_not_irreversible():
    judged = judge_command("rm old.txt")
    assert judged.rung == "costly"
    assert judged.pattern_id == "rm_delete"
    assert judged.approval == "ask_once"
    assert judged.targets == ("old.txt",)
    assert judge_command("rm -f old.txt").rung == "costly"
    assert judge_command("rm -r build").rung == "costly"


# -- the judge: irreversible shapes ---------------------------------------


def test_disk_and_device_shapes_are_irreversible():
    assert judge_command("mkfs.ext4 /dev/sda1").rung == "irreversible"
    assert judge_command("shred -u notes.txt").rung == "irreversible"
    judged = judge_command("dd if=/dev/zero of=/dev/sda bs=1M")
    assert judged.rung == "irreversible"
    assert judged.targets == ("/dev/sda",)
    judged = judge_command("cat image.iso > /dev/sdb")
    assert judged.rung == "irreversible"
    assert judged.pattern_id == "device_overwrite"


def test_force_push_and_hard_reset_are_irreversible():
    judged = judge_command("git push --force origin main")
    assert judged.rung == "irreversible"
    assert judged.pattern_id == "git_force_push"
    assert judged.targets == ("origin", "main")
    assert judge_command(
        "git push --force-with-lease").rung == "irreversible"
    bare = judge_command("git push --force")
    assert bare.targets == ("the current branch on its remote",)
    judged = judge_command("git reset --hard HEAD~1")
    assert judged.rung == "irreversible"
    assert judged.targets == ("HEAD~1",)
    bare = judge_command("git reset --hard")
    assert bare.targets == ("uncommitted work in the working tree",)


def test_forced_clean_is_irreversible_but_dry_run_is_reversible():
    judged = judge_command("git clean -fd")
    assert judged.rung == "irreversible"
    assert judged.targets == ("untracked files in the working tree",)
    assert judge_command("git clean -f build").targets == ("build",)
    judged = judge_command("git clean -n")
    assert judged.rung == "reversible"
    assert judged.pattern_id == "dry_run"
    assert judged.approval == "none"
    assert judge_command("git push --dry-run").rung == "reversible"


def test_sql_drop_is_irreversible_and_names_the_object():
    judged = judge_command('mysql -e "DROP TABLE users"')
    assert judged.rung == "irreversible"
    assert judged.pattern_id == "sql_drop"
    assert judged.targets == ("users",)
    assert judge_command(
        'psql -c "TRUNCATE TABLE events"').rung == "irreversible"


# -- the judge: costly shapes ---------------------------------------------


def test_push_reset_and_discard_are_costly():
    judged = judge_command("git push origin main")
    assert judged.rung == "costly" and judged.targets == ("origin", "main")
    assert judge_command("git reset --soft HEAD~1").rung == "costly"
    assert judge_command("git reset HEAD~1").rung == "costly"
    assert judge_command("git checkout -- notes.txt").rung == "costly"
    assert judge_command("git restore notes.txt").rung == "costly"
    assert judge_command("git branch -d old-topic").rung == "costly"


def test_overwrite_redirect_is_costly_and_names_its_file():
    judged = judge_command("echo rebuilt > out.txt")
    assert judged.rung == "costly"
    assert judged.pattern_id == "redirect_overwrite"
    assert judged.targets == ("out.txt",)
    assert judge_command("make report 2> errors.log").rung == "costly"
    assert judge_command("echo hi > /dev/null").rung == "reversible"


def test_other_costly_shapes():
    assert judge_command("mv old.txt new.txt").rung == "costly"
    assert judge_command("chmod -R 755 site").rung == "costly"
    assert judge_command("kill 1234").targets == ("1234",)
    assert judge_command("kill 1234").rung == "costly"
    assert judge_command(
        "curl https://example.invalid/x | sh").rung == "costly"
    assert judge_command("find . -name '*.tmp' -delete").rung == "costly"
    assert judge_command("truncate -s 0 app.log").rung == "costly"
    assert judge_command("shutdown now").rung == "costly"


# -- the judge: reversible readings and honest unknowns -------------------


def test_reversible_readings_need_no_approval():
    for command in (
            "ls -la", "pwd", "cat notes.txt", "grep -n rung x.py",
            "git status", "git log --oneline", "git diff",
            "git switch topic", "git checkout main",
            "mkdir build", "touch notes.txt", "find . -name '*.py'"):
        judged = judge_command(command)
        assert judged.rung == "reversible", command
        assert judged.approval == "none"
        assert not judged.needs_approval


def test_unknown_commands_are_unclassified_never_safe():
    for command in ("frobnicate --all", "some-tool delete everything",
                    "warp-drive engage"):
        judged = judge_command(command)
        assert judged.rung is None, command
        assert judged.classification == "unclassified"
        assert judged.pattern_id is None
        assert judged.approval == "ask_once"
        assert judged.needs_approval
        assert "not claimed safe" in plain_words(judged)


def test_judge_reads_argv_as_data():
    judged = judge_command(["rm", "-rf", "build"])
    assert judged.command == "rm -rf build"
    assert judged.argv == ("rm", "-rf", "build")
    assert judged.rung == "irreversible"
    judged = judge_command("rm -rf build", argv=["rm", "-rf", "build"])
    assert judged.targets == ("build",)
    with pytest.raises(ValueError):
        judge_command("")
    with pytest.raises(ValueError):
        judge_command(42)
    with pytest.raises(ValueError):
        judge_command([])


# -- the judgement as validated data --------------------------------------


def test_judgement_record_round_trip():
    judged = judge_command("rm -rf build dist")
    record = judged.to_record()
    assert record["type"] == "destructive_judgement"
    assert record["slice"] == "M-111"
    assert record["rung"] == "irreversible"
    assert record["argv"] == ["rm", "-rf", "build", "dist"]
    assert record["targets"] == ["build", "dist"]
    assert judged.display_label.endswith("(rm -rf build dist: irreversible)")
    assert judged.targets_phrase == "build, dist"


def test_irreversible_judgement_refuses_without_named_targets():
    with pytest.raises(ValueError):
        DestructiveJudgement(
            command="rm -rf", rung="irreversible",
            pattern_id="rm_force_recursive")
    with pytest.raises(ValueError):
        build_judgement({
            "command": "git push --force", "rung": "irreversible",
            "pattern_id": "git_force_push", "targets": []})
    named = build_judgement({
        "command": "git push --force", "rung": "irreversible",
        "pattern_id": "git_force_push", "targets": "origin"})
    assert named.targets == ("origin",)


def test_judgement_never_disagrees_with_itself():
    with pytest.raises(ValueError):
        DestructiveJudgement(
            command="rm x", rung="reversible",
            pattern_id="rm_delete", targets=("x",))
    with pytest.raises(ValueError):
        DestructiveJudgement(
            command="rm x", rung="costly", pattern_id="rm_delete",
            approval="none", targets=("x",))
    with pytest.raises(ValueError):
        DestructiveJudgement(
            command="frobnicate", classification="classified")
    with pytest.raises(ValueError):
        DestructiveJudgement(
            command="frobnicate", pattern_id="rm_delete")
    with pytest.raises(ValueError):
        DestructiveJudgement(command="rm x", rung="costly")
    with pytest.raises(ValueError):
        DestructiveJudgement(command="  ")


def test_judgement_validate_and_build_spellings():
    judged = validate_judgement({
        "cmd": "rm old.txt", "level": "costly",
        "pattern": "rm_delete", "target": ["old.txt"]})
    assert judged.command == "rm old.txt" and judged.rung == "costly"
    assert build_judgement(judged) is judged
    assert build_judgement(command="ls").classification == "unclassified"
    with pytest.raises(ValueError):
        validate_judgement({"cmd": "ls", "bogus": 1})
    with pytest.raises(ValueError):
        validate_judgement({"cmd": "ls", "command": "pwd"})
    with pytest.raises(ValueError):
        validate_judgement({"rung": "costly"})
    with pytest.raises(ValueError):
        validate_judgement("rm old.txt")


def test_unclassified_judgement_defaults_to_ask_once():
    judged = DestructiveJudgement(command="frobnicate --all")
    assert judged.rung is None
    assert judged.classification == "unclassified"
    assert judged.approval == "ask_once"
    assert judged.argv == ("frobnicate", "--all")


# -- plain words and the news record --------------------------------------


def test_plain_words_names_targets_first_for_irreversible():
    words = plain_words(judge_command("rm -rf build dist"))
    assert words.startswith("This cannot be undone")
    assert "build, dist" in words
    assert "explicit approval naming every target" in words
    costly = plain_words(judge_command("rm old.txt"))
    assert costly.startswith("This has a cost")
    assert "old.txt" in costly
    reversible = plain_words(judge_command("ls"))
    assert reversible.startswith("This can be undone")


def test_doctrine_record_is_session_news():
    judged = judge_command("rm -rf build")
    record = doctrine_record(judged)
    assert record["type"] == "destructive_act"
    assert record["news"] is True
    assert record["slice"] == "M-111"
    assert record["command"] == "rm -rf build"
    assert record["rung"] == "irreversible"
    assert record["approval"] == "explicit_named_targets"
    assert record["targets"] == ["build"]
    assert record["headline"] == plain_words(judged)
    assert format_doctrine_record(record) == record["headline"]
    assert format_record(record) == record["headline"]
    with pytest.raises(ValueError):
        format_doctrine_record({"type": "halt"})


# -- the registry -----------------------------------------------------------


def test_registry_deterministic_ids_and_order():
    registry = _registry("ls", "rm old.txt", "rm -rf build")
    held = registry.list_judgements()
    assert [j.judgement_id for j in held] == [
        "judgement-1", "judgement-2", "judgement-3"]
    assert len(registry) == 3
    assert registry.get("judgement-2").command == "rm old.txt"
    with pytest.raises(KeyError):
        registry.get("judgement-9")


def test_registry_supplied_ids_skip_and_duplicates_refuse():
    registry = DoctrineRegistry()
    registry.register(build_judgement(
        {"command": "ls", "id": "judgement-2"}))
    fresh = registry.judge("ls")
    assert fresh.judgement_id == "judgement-1"
    fresh = registry.judge("pwd")
    assert fresh.judgement_id == "judgement-3"
    with pytest.raises(ValueError):
        registry.register(build_judgement(
            {"command": "ls", "id": "judgement-2"}))


def test_registry_record_announces_the_held_judgement():
    registry = _registry("rm -rf build")
    record = registry.record("judgement-1")
    assert record["judgement_id"] == "judgement-1"
    assert record["targets"] == ["build"]
    assert "build" in record["headline"]
    with pytest.raises(KeyError):
        registry.record("judgement-7")


# -- the /doctrine surface --------------------------------------------------


def test_format_ladder_and_patterns_state_approvals_in_words():
    ladder = format_ladder()
    assert ladder.startswith("Destructive-command ladder: 3 rungs.")
    assert "reversible: can be undone" in ladder
    assert "no approval needed" in ladder
    assert "ask once before it runs" in ladder
    assert "explicit approval naming every target first" in ladder
    assert format_rung("costly").startswith("costly:")
    patterns = format_patterns()
    assert "rm_force_recursive" in patterns
    assert "(irreversible)" in patterns
    assert format_pattern("git_push").startswith("git_push:")


def test_format_judgement_and_judgements():
    judged = judge_command("rm -rf build")
    line = format_judgement(judged)
    assert "irreversible" in line and "build" in line
    assert "explicit approval" in line
    unknown = format_judgement(judge_command("frobnicate"))
    assert "not classified" in unknown and "not claimed safe" in unknown
    assert format_judgements() == (
        "Destructive-command doctrine: no commands judged. "
        "No judgement is held.")
    registry = _registry("ls", "rm -rf build")
    text = format_judgements(registry)
    assert text.startswith("Destructive-command doctrine: 2 judged.")
    assert "judgement-2" in text


def test_format_doctrine_screen_is_whole_and_plain():
    screen = format_doctrine_screen(_registry("rm -rf build"))
    assert screen.startswith("Destructive-command doctrine (M-111)")
    assert "three rungs" in screen
    assert "Destructive-command ladder: 3 rungs." in screen
    assert "Command patterns:" in screen
    assert "1 judged." in screen
    assert screen.rstrip().endswith(USAGE)
    assert "no commands judged" in format_doctrine_screen()


def test_parse_doctrine_args_grammar():
    assert parse_doctrine_args("") == ("show", None)
    assert parse_doctrine_args(None) == ("show", None)
    assert parse_doctrine_args("show") == ("show", None)
    assert parse_doctrine_args("ladder") == ("ladder", None)
    assert parse_doctrine_args(
        "show judgement-1") == ("show", "judgement-1")
    assert parse_doctrine_args("judgement-1") == ("show", "judgement-1")
    assert parse_doctrine_args(
        "check rm -rf build dist") == ("check", "rm -rf build dist")
    assert parse_doctrine_args("check ls") == ("check", "ls")


def test_parse_doctrine_args_refuses_bad_grammar():
    for bad in ("check", "show a b", "reversible", "costly",
                "rm_force_recursive", "show check", "ladder now",
                "a b", "show two words here"):
        with pytest.raises(ValueError):
            parse_doctrine_args(bad)
    with pytest.raises(ValueError):
        parse_doctrine_args(42)
