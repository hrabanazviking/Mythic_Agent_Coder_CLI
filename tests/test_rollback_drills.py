"""M-112 Rollback drills - pure-layer tests.

TIER: integration

The pure layer is the drill book as data: a
catalogue of exactly three scripted disasters
(bad mass edit / wrong branch push attempt /
corrupted session - the roadmap's own three),
each a frozen validated definition carrying its
setup and the recovery road it exercises over
machinery the tree already ships, a drill result
whose outcome is derived from its step counts
(so a result never disagrees with itself, and a
partial walk is never rounded up to a recovery),
a mechanical judge reading counts alone, a drill
record shaped as session news, and a registry
with deterministic ids. Nothing here scripts a
disaster or restores anything.
"""

import pytest

from mythic_agent.core.rollback_drills import (
    DRILL_CATALOGUE,
    DRILL_DISASTERS,
    DRILL_OUTCOMES,
    OUTCOME_PHRASES,
    PLAIN_EXPLANATION,
    ROLLBACK_DRILLS_SLICE,
    USAGE,
    Definition,
    DrillDefinition,
    DrillRegistry,
    DrillResult,
    Result,
    build_definition,
    build_result,
    drill_for,
    drill_for_disaster,
    drill_record,
    format_drill,
    format_drills,
    format_record,
    format_result,
    format_results,
    format_rollback_record,
    format_rollback_screen,
    judge_result,
    normalize_disaster,
    normalize_drill_id,
    normalize_outcome,
    normalize_run_id,
    outcome_for_counts,
    parse_rollback_args,
    plain_words,
    validate_definition,
    validate_result,
)


def _registry(*runs):
    registry = DrillRegistry()
    for drill_id, passed in runs:
        registry.judge(drill_id, passed)
    return registry


# -- constants and word readings ---------------------------------------


def test_constants_and_usage():
    assert ROLLBACK_DRILLS_SLICE == "M-112"
    assert DRILL_DISASTERS == (
        "bad_mass_edit", "wrong_branch_push", "corrupted_session")
    assert DRILL_OUTCOMES == (
        "recovered", "partially_recovered", "not_recovered")
    assert set(OUTCOME_PHRASES) == set(DRILL_OUTCOMES)
    assert USAGE.startswith("Usage: /rollback")
    assert "exactly three drills" in PLAIN_EXPLANATION
    assert "never rounded up" in PLAIN_EXPLANATION
    assert Definition is DrillDefinition
    assert Result is DrillResult


def test_disaster_word_readings():
    assert normalize_disaster("bad_mass_edit") == "bad_mass_edit"
    assert normalize_disaster("Mass Edit") == "bad_mass_edit"
    assert normalize_disaster("wrong-branch") == "wrong_branch_push"
    assert normalize_disaster("WRONG_BRANCH_PUSH") == "wrong_branch_push"
    assert normalize_disaster("corrupted") == "corrupted_session"
    with pytest.raises(ValueError):
        normalize_disaster("disk_wipe")
    with pytest.raises(ValueError):
        normalize_disaster(None)
    with pytest.raises(ValueError):
        normalize_disaster("")


def test_outcome_word_readings():
    assert normalize_outcome("recovered") == "recovered"
    assert normalize_outcome("Full") == "recovered"
    assert normalize_outcome("partial") == "partially_recovered"
    assert normalize_outcome("Partly") == "partially_recovered"
    assert normalize_outcome("failed") == "not_recovered"
    with pytest.raises(ValueError):
        normalize_outcome("safe")
    with pytest.raises(ValueError):
        normalize_outcome("passed")


def test_id_readings():
    assert normalize_drill_id("Bad-Mass Edit Drill") == "bad_mass_edit_drill"
    assert normalize_run_id("run-1") == "run-1"
    assert normalize_run_id("Run.2_x") == "Run.2_x"
    with pytest.raises(ValueError):
        normalize_drill_id("bad drill!")
    with pytest.raises(ValueError):
        normalize_drill_id("")
    with pytest.raises(ValueError):
        normalize_run_id("two words")
    with pytest.raises(ValueError):
        normalize_run_id(None)


# -- the catalogue ------------------------------------------------------


def test_catalogue_is_exactly_the_roadmaps_three():
    assert len(DRILL_CATALOGUE) == 3
    assert tuple(d.disaster for d in DRILL_CATALOGUE) == DRILL_DISASTERS
    assert tuple(d.drill_id for d in DRILL_CATALOGUE) == (
        "bad_mass_edit_drill", "wrong_branch_push_drill",
        "corrupted_session_drill")
    for drill in DRILL_CATALOGUE:
        assert drill.step_count >= 3
        assert drill.setup
        assert all(drill.recovery_steps)


def test_catalogue_roads_walk_shipped_machinery():
    mass = drill_for("bad_mass_edit_drill")
    assert any("checkpoint" in s for s in mass.recovery_steps)
    assert any("mass-edit guard" in s for s in mass.recovery_steps)
    push = drill_for("wrong_branch_push_drill")
    assert any("doctrine" in s for s in push.recovery_steps)
    assert any("remote" in s for s in push.recovery_steps)
    session = drill_for("corrupted_session_drill")
    assert any("journal" in s for s in session.recovery_steps)
    assert any("recovery" in s for s in session.recovery_steps)


def test_drill_lookup_by_id_and_disaster():
    assert drill_for("BAD_MASS_EDIT_DRILL").disaster == "bad_mass_edit"
    assert drill_for_disaster("wrong branch").drill_id == (
        "wrong_branch_push_drill")
    assert drill_for_disaster("corrupted_session") is (
        drill_for("corrupted_session_drill"))
    with pytest.raises(ValueError):
        drill_for("no_such_drill")
    with pytest.raises(ValueError):
        drill_for_disaster("disk_wipe")


def test_definition_validation_refuses_bad_data():
    with pytest.raises(ValueError):
        DrillDefinition(
            drill_id="x_drill", disaster="disk_wipe",
            label="x", setup="y", recovery_steps=("step",))
    with pytest.raises(ValueError):
        DrillDefinition(
            drill_id="x_drill", disaster="bad_mass_edit",
            label="x", setup="y", recovery_steps=())
    with pytest.raises(ValueError):
        DrillDefinition(
            drill_id="x_drill", disaster="bad_mass_edit",
            label=" ", setup="y", recovery_steps=("step",))
    with pytest.raises(ValueError):
        DrillDefinition(
            drill_id="x_drill", disaster="bad_mass_edit",
            label="x", setup="y", recovery_steps=("ok", " "))


def test_definition_validate_and_build():
    built = build_definition({
        "id": "extra_drill", "kind": "corrupted",
        "label": "extra", "setup": "staged",
        "steps": ["one", "two"]})
    assert built.disaster == "corrupted_session"
    assert built.recovery_steps == ("one", "two")
    assert validate_definition(built) is built
    assert build_definition(built) is built
    record = built.to_record()
    assert record["type"] == "rollback_drill"
    assert record["slice"] == "M-112"
    assert record["step_count"] == 2
    with pytest.raises(ValueError):
        validate_definition({"drill_id": "x", "bogus": 1})
    with pytest.raises(ValueError):
        validate_definition({
            "drill_id": "x_drill", "id": "y_drill",
            "disaster": "bad_mass_edit", "label": "x",
            "setup": "y", "steps": ["s"]})
    with pytest.raises(ValueError):
        validate_definition("not a mapping")


# -- counts, the judge, and results that cannot disagree ----------------


def test_outcome_for_counts_derivation():
    assert outcome_for_counts(4, 4) == "recovered"
    assert outcome_for_counts(1, 4) == "partially_recovered"
    assert outcome_for_counts(3, 4) == "partially_recovered"
    assert outcome_for_counts(0, 4) == "not_recovered"
    with pytest.raises(ValueError):
        outcome_for_counts(5, 4)
    with pytest.raises(ValueError):
        outcome_for_counts(0, 0)
    with pytest.raises(ValueError):
        outcome_for_counts(-1, 4)
    with pytest.raises(ValueError):
        outcome_for_counts(True, 4)


def test_judge_derives_outcome_from_counts_alone():
    full = judge_result("bad_mass_edit_drill", 4)
    assert full.outcome == "recovered" and full.recovered
    assert full.steps_total == drill_for("bad_mass_edit_drill").step_count
    part = judge_result("wrong_branch_push_drill", 2)
    assert part.outcome == "partially_recovered" and not part.recovered
    none = judge_result("corrupted_session_drill", 0)
    assert none.outcome == "not_recovered"
    with pytest.raises(ValueError):
        judge_result("no_such_drill", 1)
    with pytest.raises(ValueError):
        judge_result("bad_mass_edit_drill", 99)


def test_result_never_disagrees_with_itself():
    ok = DrillResult(drill_id="bad_mass_edit_drill", steps_passed=4,
                     outcome="recovered")
    assert ok.disaster == "bad_mass_edit"
    with pytest.raises(ValueError):
        DrillResult(drill_id="bad_mass_edit_drill", steps_passed=2,
                    outcome="recovered")
    with pytest.raises(ValueError):
        DrillResult(drill_id="bad_mass_edit_drill", steps_passed=4,
                    outcome="not_recovered")
    with pytest.raises(ValueError):
        DrillResult(drill_id="bad_mass_edit_drill", steps_passed=0,
                    steps_total=3)
    with pytest.raises(ValueError):
        DrillResult(drill_id="bad_mass_edit_drill", steps_passed=-1)


def test_result_validate_and_build_spellings():
    built = build_result({
        "drill": "corrupted_session_drill", "passed": 4,
        "verdict": "full"})
    assert built.outcome == "recovered"
    assert validate_result(built) is built
    record = built.to_record()
    assert record["type"] == "drill_result"
    assert record["disaster"] == "corrupted_session"
    with pytest.raises(ValueError):
        validate_result({"passed": 1})
    with pytest.raises(ValueError):
        validate_result({
            "drill_id": "bad_mass_edit_drill", "passed": 1,
            "steps_passed": 2})
    with pytest.raises(ValueError):
        validate_result({"drill_id": "bad_mass_edit_drill", "bogus": 1})


# -- plain words, the news record, and the registry ----------------------


def test_plain_words_states_the_outcome_whole():
    full = plain_words(judge_result("bad_mass_edit_drill", 4))
    assert full.startswith("Recovered in full")
    part = plain_words(judge_result("bad_mass_edit_drill", 1))
    assert part.startswith("Only partially recovered")
    assert "1 of 4" in part
    none = plain_words(judge_result("bad_mass_edit_drill", 0))
    assert none.startswith("Not recovered")


def test_drill_record_is_session_news():
    registry = _registry(("wrong_branch_push_drill", 4))
    held = registry.list_results()[0]
    record = drill_record(held)
    assert record["type"] == "rollback_drill_run"
    assert record["news"] is True
    assert record["slice"] == "M-112"
    assert record["run_id"] == "run-1"
    assert record["disaster"] == "wrong_branch_push"
    assert record["headline"].startswith("Recovered in full")
    assert format_rollback_record(record) == record["headline"]
    assert format_record(record) == record["headline"]
    with pytest.raises(ValueError):
        format_rollback_record({"type": "other"})


def test_registry_deterministic_ids_and_order():
    registry = _registry(
        ("bad_mass_edit_drill", 4), ("corrupted_session_drill", 0))
    results = registry.list_results()
    assert [r.run_id for r in results] == ["run-1", "run-2"]
    assert len(registry) == 2
    assert registry.get("run-2").outcome == "not_recovered"
    assert registry.record("run-1")["type"] == "rollback_drill_run"
    with pytest.raises(KeyError):
        registry.get("run-99")


def test_registry_supplied_ids_skip_and_duplicates_refuse():
    registry = DrillRegistry()
    registry.register(DrillResult(
        drill_id="bad_mass_edit_drill", steps_passed=4,
        run_id="run-2"))
    fresh = registry.judge("bad_mass_edit_drill", 4)
    assert fresh.run_id == "run-1"
    fresh2 = registry.judge("bad_mass_edit_drill", 4)
    assert fresh2.run_id == "run-3"
    with pytest.raises(ValueError):
        registry.register(DrillResult(
            drill_id="bad_mass_edit_drill", steps_passed=4,
            run_id="run-2"))
    with pytest.raises(ValueError):
        registry.register()


# -- formatters and the shared parser ------------------------------------


def test_format_drills_states_each_disaster_in_words():
    text = format_drills()
    assert text.startswith("Rollback drills: 3 scripted.")
    for drill in DRILL_CATALOGUE:
        assert drill.drill_id in text
    single = format_drill("corrupted_session_drill")
    assert "corrupted session" in single
    assert "recovery steps" in single


def test_format_results_and_empty_statement():
    assert format_results().startswith(
        "Rollback drills: no drill runs reported.")
    assert format_results(None).startswith(
        "Rollback drills: no drill runs reported.")
    registry = _registry(("bad_mass_edit_drill", 3))
    text = format_results(registry)
    assert "1 runs reported" in text
    assert "only partially recovered" in text
    one = format_result(registry.list_results()[0])
    assert "3 of 4 steps passed" in one
    with pytest.raises(ValueError):
        format_results(42)


def test_format_rollback_screen_is_whole_and_plain():
    registry = _registry(("corrupted_session_drill", 4))
    screen = format_rollback_screen(registry)
    assert screen.startswith("Rollback drills (M-112)")
    assert "exactly three drills" in screen
    assert "3 scripted" in screen
    assert "recovered in full" in screen
    assert screen.rstrip().endswith(USAGE)


def test_parse_rollback_args_grammar():
    assert parse_rollback_args("") == ("show", None)
    assert parse_rollback_args(None) == ("show", None)
    assert parse_rollback_args("show") == ("show", None)
    assert parse_rollback_args("drills") == ("drills", None)
    assert parse_rollback_args("show run-1") == ("show", "run-1")
    assert parse_rollback_args("run-7") == ("show", "run-7")
    assert parse_rollback_args(
        "run bad_mass_edit_drill") == ("run", "bad_mass_edit_drill")
    assert parse_rollback_args(
        "run WRONG-BRANCH-PUSH-DRILL") == (
            "run", "wrong_branch_push_drill")


def test_parse_rollback_args_refuses_bad_grammar():
    for bad in ("run", "run no_such_drill", "run run-1",
                "show run", "show a b", "bad_mass_edit",
                "bad_mass_edit_drill", "corrupted_session",
                "drills now", "two words here"):
        with pytest.raises(ValueError):
            parse_rollback_args(bad)
    with pytest.raises(ValueError):
        parse_rollback_args(42)


def test_module_is_pure_data_only():
    import mythic_agent.core.rollback_drills as module
    import inspect
    source = inspect.getsource(module)
    for banned in ("import subprocess", "import os", "open(",
                   "import sys"):
        assert banned not in source


def test_definition_display_and_record_round_trip():
    drill = drill_for("wrong_branch_push_drill")
    assert "wrong_branch_push_drill" in drill.display_label
    record = drill.to_record()
    rebuilt = validate_definition({
        "drill_id": record["drill_id"],
        "disaster": record["disaster"],
        "label": record["label"], "setup": record["setup"],
        "recovery_steps": record["recovery_steps"]})
    assert rebuilt == drill


def test_result_display_label_and_defaults():
    result = DrillResult(drill_id="corrupted_session_drill")
    assert result.steps_passed == 0
    assert result.outcome == "not_recovered"
    assert "corrupted_session_drill" in result.display_label
    held = _registry(("corrupted_session_drill", 4)).list_results()[0]
    assert held.display_label.startswith("run-1")


def test_registry_register_from_mapping_and_kwargs():
    registry = DrillRegistry()
    from_map = registry.register(
        {"drill_id": "bad_mass_edit_drill", "passed": 4})
    assert from_map.run_id == "run-1" and from_map.recovered
    from_kwargs = registry.register(
        drill_id="bad_mass_edit_drill", steps_passed=1)
    assert from_kwargs.run_id == "run-2"
    assert from_kwargs.outcome == "partially_recovered"
    merged = registry.register(
        {"drill_id": "bad_mass_edit_drill"}, steps_passed=2)
    assert merged.outcome == "partially_recovered"
    with pytest.raises(ValueError):
        registry.register(
            {"drill_id": "bad_mass_edit_drill", "passed": 4},
            steps_passed=1)


def test_format_results_from_list_and_single_sources():
    result = judge_result("bad_mass_edit_drill", 4)
    assert "recovered in full" in format_results([result])
    assert "recovered in full" in format_results(result)
    assert "recovered in full" in format_results(
        [{"drill_id": "bad_mass_edit_drill", "passed": 4}])


def test_parse_is_case_insensitive_for_grammar_words():
    assert parse_rollback_args("SHOW") == ("show", None)
    assert parse_rollback_args("Drills") == ("drills", None)
    assert parse_rollback_args("Show Run-3") == ("show", "Run-3")

# -- agent layer: drills held for a session (M-112) -----------------------

import json as _json

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _rollback_events(store, session_id):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == "rollback_drill_run"]


def _held_results(agent):
    return agent._drill_registry().list_results()


class TestRollbackAgentStatus:
    def test_status_starts_empty(self, agent):
        status = agent.rollback_status()
        assert status["results"] == []
        assert "no drill runs reported" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["screen"] == format_rollback_screen(
            agent._drill_registry())

    def test_registry_is_one_per_agent(self, agent):
        assert agent._drill_registry() is agent._drill_registry()

    def test_unknown_run_raises_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.get_drill_run("run-99")

    def test_full_recovery_judged_and_published_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.judge_drill_run("bad_mass_edit_drill", 4)
        assert outcome["result"]["outcome"] == "recovered"
        assert outcome["result"]["run_id"] == "run-1"
        assert outcome["record"]["type"] == "rollback_drill_run"
        assert outcome["record"]["news"] is True
        assert outcome["record"]["headline"].startswith(
            "Recovered in full")
        events = _rollback_events(store, session_id)
        assert len(events) == 1
        assert events[0]["drill_id"] == "bad_mass_edit_drill"
        assert events[0]["steps_passed"] == 4
        agent._publish_drill_record(outcome["record"])
        agent.rollback_status()
        agent.get_drill_run("run-1")
        assert len(_rollback_events(store, session_id)) == 1
        assert agent.get_drill_run("run-1").outcome == "recovered"

    def test_partial_is_never_rounded_up_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.judge_drill_run("wrong_branch_push_drill", 2)
        assert outcome["result"]["outcome"] == "partially_recovered"
        assert outcome["record"]["headline"].startswith(
            "Only partially recovered")
        assert len(_rollback_events(store, session_id)) == 1

    def test_failed_recovery_publishes_too(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.judge_drill_run("corrupted_session_drill", 0)
        assert outcome["result"]["outcome"] == "not_recovered"
        assert outcome["record"]["headline"].startswith("Not recovered")
        assert len(_rollback_events(store, session_id)) == 1

    def test_register_result_holds_and_publishes(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_drill_result(
            {"drill_id": "corrupted_session_drill", "steps_passed": 4})
        assert outcome["result"]["run_id"] == "run-1"
        assert outcome["result"]["outcome"] == "recovered"
        named = agent.register_drill_result(
            drill_id="bad_mass_edit_drill", steps_passed=3,
            run_id="field-run")
        assert named["result"]["outcome"] == "partially_recovered"
        assert len(_rollback_events(store, session_id)) == 2
        with pytest.raises(ValueError):
            agent.register_drill_result(
                drill_id="bad_mass_edit_drill", steps_passed=3,
                run_id="field-run")
        assert len(_held_results(agent)) == 2

    def test_judge_refusals_hold_nothing(self, agent):
        with pytest.raises(ValueError):
            agent.judge_drill_run("disk_wipe_drill", 4)
        with pytest.raises(ValueError):
            agent.judge_drill_run("bad_mass_edit_drill", 5)
        with pytest.raises(ValueError):
            agent.judge_drill_run("bad_mass_edit_drill", -1)
        assert _held_results(agent) == ()

    def test_status_read_publishes_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.judge_drill_run("bad_mass_edit_drill", 4)
        assert len(_rollback_events(store, session_id)) == 1
        agent.rollback_status()
        agent.get_drill_run("run-1")
        agent.rollback_status()
        assert len(_rollback_events(store, session_id)) == 1

    def test_judge_without_session_holds_quietly(self, agent):
        outcome = agent.judge_drill_run("bad_mass_edit_drill", 4)
        assert outcome["result"]["outcome"] == "recovered"
        assert "1 runs reported" in outcome["screen"]
        assert len(_held_results(agent)) == 1

class TestRollbackRealRoads:
    """The drills run against the real recovery roads.

    Each test performs the catalogue drill's own
    recovery steps on the shipped machinery and
    counts a step passed only when that machinery
    actually did its step; the agent then judges
    the earned count - no count here is invented.
    """

    def test_bad_mass_edit_drill_on_checkpoint_road(
            self, agent, tmp_path):
        from mythic_agent.core.checkpoints import CheckpointStore
        from mythic_agent.core.mass_edit_guard import build_report

        tree = tmp_path / "tree"
        tree.mkdir()
        clean = {"a.txt": "alpha clean\n", "b.txt": "beta clean\n",
                 "c.txt": "gamma clean\n"}
        for name, text in clean.items():
            (tree / name).write_text(text)
        passed = 0
        store = CheckpointStore(tree)
        checkpoint = store.create("drill-clean")
        if checkpoint.file_count == 3:
            passed += 1  # step 1: checkpoint taken first (M-075)
        plan = [{"path": name, "before": text,
                 "after": text.replace("clean", "BAD")}
                for name, text in clean.items()]
        report = build_report(plan)
        if len(report.files) == 3 and all(
                f.changed for f in report.files):
            passed += 1  # step 2: guard report read (M-093)
        for entry in plan:
            (tree / entry["path"]).write_text(entry["after"])
        _, outcome = store.restore("drill-clean", discard=True)
        if outcome.discarded_changes == 3:
            passed += 1  # step 3: checkpoint restored whole
        if all((tree / name).read_text() == text
               for name, text in clean.items()):
            passed += 1  # step 4: tree verified against it
        assert passed == 4
        session_store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(session_store)
        judged = agent.judge_drill_run("bad_mass_edit_drill", passed)
        assert judged["result"]["outcome"] == "recovered"
        events = _rollback_events(session_store, session_id)
        assert len(events) == 1
        assert events[0]["disaster"] == "bad_mass_edit"

    def test_bad_mass_edit_partial_when_verify_step_not_walked(
            self, agent, tmp_path):
        from mythic_agent.core.checkpoints import CheckpointStore
        from mythic_agent.core.mass_edit_guard import build_report

        tree = tmp_path / "tree"
        tree.mkdir()
        (tree / "a.txt").write_text("alpha clean\n")
        store = CheckpointStore(tree)
        store.create("drill-clean")
        passed = 1  # checkpoint taken
        report = build_report([{
            "path": "a.txt", "before": "alpha clean\n",
            "after": "alpha BAD\n"}])
        if report.files[0].changed:
            passed += 1  # guard report read
        (tree / "a.txt").write_text("alpha BAD\n")
        store.restore("drill-clean", discard=True)
        passed += 1  # checkpoint restored whole
        # The verification step is not walked, so it
        # is not counted: 3 of 4 is partial, honestly.
        judged = agent.judge_drill_run("bad_mass_edit_drill", passed)
        assert judged["result"]["outcome"] == "partially_recovered"
        assert judged["record"]["headline"].startswith(
            "Only partially recovered")

    def test_wrong_branch_push_drill_on_doctrine_road(
            self, agent, tmp_path):
        import subprocess

        def git(*argv, cwd):
            return subprocess.run(
                ["git", "-C", str(cwd), *argv],
                check=True, capture_output=True, text=True).stdout

        repo = tmp_path / "repo"
        repo.mkdir()
        git("init", "-b", "main", cwd=repo)
        (repo / "note.txt").write_text("session work\n")
        git("add", "note.txt", cwd=repo)
        git("-c", "user.name=Drill", "-c",
            "user.email=drill@example.invalid",
            "commit", "-m", "session work", cwd=repo)
        remote = tmp_path / "remote.git"
        subprocess.run(["git", "clone", "--bare", str(repo),
                        str(remote)], check=True, capture_output=True)

        def remote_refs():
            out = subprocess.run(
                ["git", "ls-remote", str(remote)],
                check=True, capture_output=True, text=True).stdout
            return {line.split()[1]: line.split()[0]
                    for line in out.splitlines() if line.strip()}

        before = remote_refs()
        passed = 0
        wrong = agent.judge_command("git push origin wrong-branch")
        if wrong["judgement"]["rung"] == "costly":
            passed += 1  # step 1: push judged first (M-111)
        if wrong["judgement"]["approval"] == "ask_once":
            passed += 1  # step 2: attempt stopped at the gate -
            # the push is never executed, so the remote
            # is never written by this drill
        if remote_refs() == before:
            passed += 1  # step 3: remote verified unchanged
        retargeted = agent.judge_command("git push origin main")
        if retargeted["judgement"]["rung"] == "costly" and len(
                agent._doctrine_registry().list_judgements()) == 2:
            passed += 1  # step 4: retargeted and judged again
        assert passed == 4
        assert remote_refs() == before
        judged = agent.judge_drill_run(
            "wrong_branch_push_drill", passed)
        assert judged["result"]["outcome"] == "recovered"

    def test_corrupted_session_drill_on_journal_road(
            self, agent, tmp_path):
        from types import SimpleNamespace

        from mythic_agent.core.recovery import (
            recover_crashed_sessions)
        from mythic_agent.core.undo_timeline import (
            TimelineEntry, build_footprint, build_timeline,
            judge_walk, take_snapshot)

        ws = tmp_path / "ws"
        ws.mkdir()
        state = tmp_path / "drill-state"
        store = _SessionStore(ws, state)
        base_messages = [
            {"role": "system", "content": "Fixture system"},
            {"role": "user", "content": "hello"}]
        session_id = store.create(base_messages, {})
        full_messages = base_messages + [
            {"role": "user", "content": "second turn"}]
        # The dead process journaled its checkpoint
        # and died before the commit: the corruption.
        store.journal.append_checkpoint(
            session_id,
            {"messages": full_messages, "status": "running",
             "total_tokens": 42, "outcome": None}, None)
        passed = 0
        restarted = _SessionStore(ws, state)
        pending = restarted.check_recovery()
        if len(pending) == 1 and (
                pending[0]["session_id"] == session_id):
            passed += 1  # step 1: journal detects the dead
            # session's uncommitted checkpoint
        recovered = recover_crashed_sessions(
            SimpleNamespace(_session_store=restarted))
        if recovered == [session_id]:
            passed += 1  # step 2: startup crash recovery
            # replays it
        data = restarted.load(session_id)
        if data["context"] == full_messages and (
                data["total_tokens"] == 42):
            passed += 1  # step 3: recovered transcript whole
        tree = tmp_path / "undo-tree"
        tree.mkdir()
        (tree / "state.txt").write_text("whole\n")
        before_snap = take_snapshot(tree)
        (tree / "state.txt").write_text("corrupted\n")
        after_snap = take_snapshot(tree)
        footprint = build_footprint(
            "corrupt the session state", before_snap, after_snap)
        entry = TimelineEntry(
            kind="command", ref_id="cmd-corrupt",
            label="corrupting command",
            detail="state.txt rewritten", seq=1,
            certainty="certain")
        judge_walk(build_timeline([entry]), entry)
        if [c.path for c in footprint.changes] == ["state.txt"]:
            passed += 1  # step 4: undo timeline walks the
            # corrupting command's footprint (M-077)
        assert passed == 4
        judged = agent.judge_drill_run(
            "corrupted_session_drill", passed)
        assert judged["result"]["outcome"] == "recovered"

class TestRollbackTerminalSurface:
    def test_show_is_the_whole_slice(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/rollback")
        assert text.startswith("Rollback drills (M-112) - ")
        assert "no drill runs reported" in text
        assert USAGE in text

    def test_help_line_names_rollback(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert "/rollback [show|show <run>|drills|run <drill>]" in text

    def test_drills_and_run_via_the_terminal(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/rollback drills")
        assert text.startswith("Rollback drills: 3 scripted.")
        assert "bad_mass_edit_drill" in text
        _, _, text = _slash(agent, "/rollback run bad_mass_edit_drill")
        assert text.startswith("bad_mass_edit_drill:")
        assert "4 recovery steps" in text
        assert _held_results(agent) == ()

    def test_show_one_via_the_terminal(self, agent):
        from mythic_agent.terminal import _slash
        agent.judge_drill_run("bad_mass_edit_drill", 4)
        _, _, text = _slash(agent, "/rollback show run-1")
        assert text.startswith(
            "run-1: bad_mass_edit_drill - recovered in full")
        _, _, text = _slash(agent, "/rollback run-1")
        assert "4 of 4 steps passed" in text

    def test_unknown_and_bad_grammar_via_the_terminal(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/rollback show run-99")
        assert "unknown drill run" in text
        _, _, text = _slash(agent, "/rollback run")
        assert text == USAGE
        _, _, text = _slash(agent, "/rollback bad_mass_edit")
        assert text == USAGE
        _, _, text = _slash(agent, "/rollback run disk_wipe_drill")
        assert text == USAGE


@pytest.fixture()
def rollback_handler(agent, monkeypatch):
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


def _rollback_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestRollbackCommand:
    def test_show_is_default(self, rollback_handler, agent):
        rollback_handler._handle_rollback("")
        assert "no drill runs reported" in _rollback_published_text(
            rollback_handler)

    def test_drills_and_run_via_the_handler(
            self, rollback_handler, agent):
        rollback_handler._handle_rollback("drills")
        assert "Rollback drills: 3 scripted." in (
            _rollback_published_text(rollback_handler))
        rollback_handler._handle_rollback(
            "run corrupted_session_drill")
        assert "corrupted_session_drill:" in (
            _rollback_published_text(rollback_handler))
        assert _held_results(agent) == ()

    def test_show_one_via_the_handler(self, rollback_handler, agent):
        agent.judge_drill_run("wrong_branch_push_drill", 4)
        rollback_handler._handle_rollback("show run-1")
        assert "run-1: wrong_branch_push_drill - " in (
            _rollback_published_text(rollback_handler))
        assert "recovered in full" in _rollback_published_text(
            rollback_handler)

    def test_bad_grammar_and_unknown_are_published(
            self, rollback_handler, agent):
        rollback_handler._handle_rollback("run")
        assert "Usage: /rollback" in _rollback_published_text(
            rollback_handler)
        rollback_handler._handle_rollback("show run-99")
        assert "unknown drill run" in _rollback_published_text(
            rollback_handler)


class TestChatScreenRoutingRollback:
    def test_rollback_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/rollback drills", _FakeLog())
        assert calls == [("/rollback", "drills")]
