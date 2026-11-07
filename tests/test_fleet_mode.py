"""M-106 Headless fleet mode - pure-layer tests.

TIER: integration

The pure layer is a headless fleet as data: a task
(what to run as an argv list, never a shell string;
in which repo; with the prompt the ``mythic run``
road itself names) validated as data, a per-task
verdict as data, a fleet verdict aggregated
mechanically with honest exit codes in the run
road's own mapping (0 only when every task passed,
1 for a failure, 2 for an error or an unfinished
fleet), an artefact bundle naming names only, a
resume plan in which a passed task is never re-run,
and a registry with deterministic ids. Nothing here
starts a process or runs anything.
"""

import pytest

from mythic_agent.core.fleet_mode import (
    EXIT_ERROR,
    EXIT_FAILED,
    EXIT_OK,
    FLEET_MODE_SLICE,
    FLEET_STATUSES,
    PLAIN_EXPLANATION,
    TASK_STATUSES,
    USAGE,
    ArtefactBundle,
    FleetRegistry,
    FleetVerdict,
    TaskVerdict,
    build_artefact_bundle,
    build_fleet_run,
    build_fleet_task,
    build_task_verdict,
    fleet_exit_code,
    format_artefact_bundle,
    format_fleet_mode,
    format_fleet_run,
    format_fleet_task,
    format_fleet_tasks,
    format_fleet_verdict,
    format_resume_plan,
    format_resume_record,
    judge_fleet,
    normalize_artefact_name,
    normalize_task_id,
    normalize_verdict_status,
    parse_fleet_args,
    plan_resume,
    resume_record,
    validate_fleet_task,
    validate_task_verdict,
)


def _task(**kwargs):
    kwargs.setdefault("label", "run the suite")
    kwargs.setdefault("argv", ["python", "-m", "pytest", "-q"])
    return build_fleet_task(kwargs)


def _registry(*tasks):
    registry = FleetRegistry()
    for task in tasks:
        registry.register(task)
    return registry


# -- constants and word readings ---------------------------------------


def test_constants_and_usage():
    assert FLEET_MODE_SLICE == "M-106"
    assert TASK_STATUSES == (
        "queued", "running", "passed", "failed", "error", "skipped")
    assert FLEET_STATUSES == ("passed", "failed", "error", "incomplete")
    assert (EXIT_OK, EXIT_FAILED, EXIT_ERROR) == (0, 1, 2)
    assert USAGE.startswith("Usage: /fleet")
    assert "never a shell string" in PLAIN_EXPLANATION
    assert "never run again" in PLAIN_EXPLANATION


def test_word_readings():
    assert normalize_task_id("fleet-1") == "fleet-1"
    assert normalize_task_id("Repo_A.2") == "Repo_A.2"
    assert normalize_verdict_status("Passed") == "passed"
    assert normalize_verdict_status("ERROR") == "error"
    for bad in ("", "has space", "a/b", None, 7):
        with pytest.raises(ValueError):
            normalize_task_id(bad)
    for bad in ("completed", "done", "", None):
        with pytest.raises(ValueError):
            normalize_verdict_status(bad)


# -- task validation -----------------------------------------------------


def test_task_defaults_and_record():
    task = _task(cwd="/repos/one", prompt="fix the tests")
    assert task.task_id is None and task.cwd == "/repos/one"
    assert task.display_label == "run the suite"
    record = task.to_record()
    assert record["type"] == "fleet_task" and record["slice"] == "M-106"
    assert record["argv"] == ["python", "-m", "pytest", "-q"]
    assert record["prompt"] == "fix the tests"
    plain = _task(label="")
    assert plain.display_label == "python -m pytest -q"


def test_task_shell_string_refuses_like_m103_m105():
    with pytest.raises(ValueError):
        _task(argv="python -m pytest -q")
    with pytest.raises(ValueError):
        _task(argv=b"python -m pytest")
    with pytest.raises(ValueError):
        _task(argv=[])
    with pytest.raises(ValueError):
        _task(argv=["python", "  "])
    with pytest.raises(ValueError):
        _task(argv=["python", 7])


def test_task_mapping_spellings_and_conflicts():
    task = build_fleet_task({
        "name": "upstream", "command": ["git", "fetch"],
        "id": "fleet-9", "workspace": "/repos/upstream",
        "prompt": "check upstream"})
    assert task.task_id == "fleet-9" and task.label == "upstream"
    assert task.cwd == "/repos/upstream"
    assert validate_fleet_task(task) is task
    with pytest.raises(ValueError):
        build_fleet_task({
            "argv": ["git"], "command": ["make"]})
    with pytest.raises(ValueError):
        build_fleet_task({"argv": ["git"], "bogus": 1})
    with pytest.raises(ValueError):
        build_fleet_task({"label": "no command"})
    with pytest.raises(ValueError):
        build_fleet_task({
            "argv": ["git"], "cwd": "/a", "repo": "/b"})
    with pytest.raises(ValueError):
        _task(prompt="   ")
    with pytest.raises(ValueError):
        _task(cwd="")


# -- per-task verdicts -----------------------------------------------------


def test_verdict_defaults_and_record():
    verdict = build_task_verdict(
        {"task_id": "fleet-1", "status": "passed", "exit_code": 0})
    assert verdict.status == "passed" and verdict.exit_code == 0
    record = verdict.to_record()
    assert record["type"] == "fleet_task_verdict"
    assert record["task_id"] == "fleet-1"
    assert validate_task_verdict(verdict) is verdict


def test_verdict_self_contradictions_refuse():
    with pytest.raises(ValueError):
        TaskVerdict(task_id="fleet-1", status="passed", exit_code=3)
    with pytest.raises(ValueError):
        TaskVerdict(task_id="fleet-1", status="failed", exit_code=0)
    with pytest.raises(ValueError):
        TaskVerdict(task_id="fleet-1", status="queued", exit_code=0)
    with pytest.raises(ValueError):
        TaskVerdict(task_id="fleet-1", status="running", exit_code=1)
    with pytest.raises(ValueError):
        TaskVerdict(task_id="fleet-1", status="skipped", exit_code=0)
    with pytest.raises(ValueError):
        TaskVerdict(task_id="fleet-1", status="failed", exit_code=True)
    with pytest.raises(ValueError):
        TaskVerdict(task_id="fleet-1", status="failed", exit_code="1")
    with pytest.raises(ValueError):
        build_task_verdict({"status": "passed"})
    with pytest.raises(ValueError):
        build_task_verdict({
            "task_id": "fleet-1", "status": "passed", "bogus": 1})


# -- fleet verdict and exit codes -------------------------------------------


def _verdict(task_id, status, **kwargs):
    return build_task_verdict(
        {"task_id": task_id, "status": status, **kwargs})


def test_fleet_all_passed_is_zero():
    verdicts = [_verdict("fleet-1", "passed", exit_code=0),
                _verdict("fleet-2", "passed")]
    judged = judge_fleet(verdicts)
    assert judged.status == "passed" and judged.exit_code == 0
    assert judged.total == 2 and judged.passed_count == 2
    assert fleet_exit_code(verdicts) == EXIT_OK
    assert fleet_exit_code(judged) == 0


def test_fleet_failed_task_can_never_yield_zero():
    verdicts = [_verdict("fleet-1", "passed", exit_code=0),
                _verdict("fleet-2", "failed", exit_code=3)]
    judged = judge_fleet(verdicts)
    assert judged.status == "failed" and judged.exit_code == 1
    assert fleet_exit_code(verdicts) == EXIT_FAILED


def test_fleet_error_outranks_failure_and_is_two():
    verdicts = [_verdict("fleet-1", "failed", exit_code=3),
                _verdict("fleet-2", "error")]
    judged = judge_fleet(verdicts)
    assert judged.status == "error" and judged.exit_code == 2
    assert fleet_exit_code(verdicts) == EXIT_ERROR


def test_fleet_unfinished_and_empty_are_never_zero():
    for verdicts in ([_verdict("fleet-1", "passed"),
                      _verdict("fleet-2", "running")],
                     [_verdict("fleet-1", "skipped")],
                     [_verdict("fleet-1", "queued")],
                     []):
        judged = judge_fleet(verdicts)
        assert judged.status == "incomplete" and judged.exit_code == 2


def test_fleet_judged_by_tasks_counts_missing_as_queued():
    registry = _registry(_task(label="a"), _task(label="b"))
    registry.record_verdict("fleet-1", status="passed", exit_code=0)
    judged = registry.fleet_verdict()
    assert judged.status == "incomplete" and judged.queued_count == 1
    assert registry.exit_code() == 2
    with pytest.raises(ValueError):
        judge_fleet([_verdict("fleet-99", "passed")],
                    registry.list_tasks())
    with pytest.raises(ValueError):
        judge_fleet([_verdict("fleet-1", "passed"),
                     _verdict("fleet-1", "failed", exit_code=1)])


def test_fleet_verdict_record_cannot_disagree_with_itself():
    with pytest.raises(ValueError):
        FleetVerdict(status="passed", exit_code=1, total=0)
    with pytest.raises(ValueError):
        FleetVerdict(status="passed", exit_code=0, total=2,
                     passed_count=1)
    with pytest.raises(ValueError):
        FleetVerdict(status="incomplete", exit_code=2, total=-1)
    with pytest.raises(ValueError):
        FleetVerdict(status="incomplete", exit_code=2, total=True)


# -- artefact bundles ---------------------------------------------------------


def test_bundle_names_and_record():
    bundle = build_artefact_bundle({
        "task_id": "fleet-1",
        "artefacts": ["report.html", "logs/run.txt"]})
    assert bundle.artefacts == ("report.html", "logs/run.txt")
    assert bundle.to_record()["type"] == "fleet_artefact_bundle"
    empty = build_artefact_bundle({"id": "fleet-2", "names": []})
    assert empty.artefacts == ()
    assert normalize_artefact_name("a/b.txt") == "a/b.txt"


def test_bundle_traversal_and_absolute_names_refuse():
    for bad in ("../secret.txt", "logs/../../secret.txt", "..",
                "/etc/passwd", "logs//run.txt", "", "C:\\secret.txt"):
        with pytest.raises(ValueError):
            normalize_artefact_name(bad)
    with pytest.raises(ValueError):
        build_artefact_bundle({
            "task_id": "fleet-1", "artefacts": ["ok.txt", "../no.txt"]})
    with pytest.raises(ValueError):
        build_artefact_bundle({
            "task_id": "fleet-1", "artefacts": ["a.txt", "a.txt"]})
    with pytest.raises(ValueError):
        ArtefactBundle(task_id="fleet-1", artefacts="report.html")


# -- the fleet run --------------------------------------------------------------


def test_fleet_run_holds_tasks_and_refuses_duplicate_ids():
    run = build_fleet_run({
        "label": "nightly", "tasks": [
            {"argv": ["make"], "task_id": "fleet-1"},
            {"argv": ["make", "test"], "task_id": "fleet-2"}]})
    assert run.label == "nightly" and len(run.tasks) == 2
    record = run.to_record()
    assert record["type"] == "fleet_run" and record["task_count"] == 2
    with pytest.raises(ValueError):
        build_fleet_run({"tasks": [
            {"argv": ["make"], "task_id": "fleet-1"},
            {"argv": ["make"], "task_id": "fleet-1"}]})
    with pytest.raises(ValueError):
        build_fleet_run({"label": "x"})


# -- resumability -----------------------------------------------------------------


def _fleet_with_verdicts():
    registry = _registry(
        _task(label="a"), _task(label="b"), _task(label="c"),
        _task(label="d"), _task(label="e"))
    registry.record_verdict("fleet-1", status="passed", exit_code=0)
    registry.record_verdict("fleet-2", status="failed", exit_code=3)
    registry.record_verdict("fleet-3", status="error")
    registry.record_verdict("fleet-4", status="running")
    return registry


def test_resume_passed_tasks_are_never_rerun():
    registry = _fleet_with_verdicts()
    plan = registry.resume_plan()
    assert plan.passed_ids == ("fleet-1",)
    assert "fleet-1" not in plan.remaining_ids
    # fleet-4 running and fleet-5 verdictless remain; the failed
    # and error tasks are held back without an explicit retry.
    assert plan.remaining_ids == ("fleet-4", "fleet-5")
    assert plan.held_back_ids == ("fleet-2", "fleet-3")
    assert plan.retry_failures is False


def test_resume_retry_failures_is_an_explicit_choice():
    registry = _fleet_with_verdicts()
    plan = registry.resume_plan(retry_failures=True)
    assert plan.remaining_ids == (
        "fleet-2", "fleet-3", "fleet-4", "fleet-5")
    assert plan.held_back_ids == ()
    with pytest.raises(ValueError):
        registry.resume_plan(retry_failures="yes")
    with pytest.raises(ValueError):
        plan_resume(registry.list_tasks(), [], retry_failures=1)


def test_resume_record_is_news_only_when_something_remains():
    registry = _fleet_with_verdicts()
    record = registry.resume_record()
    assert record["type"] == "fleet_resume" and record["news"] is True
    assert record["remaining"] == ["fleet-4", "fleet-5"]
    assert "will not be run again" in record["headline"]
    assert format_resume_record(record) == record["headline"]
    done = _registry(_task(label="only"))
    done.record_verdict("fleet-1", status="passed", exit_code=0)
    assert done.resume_record() is None
    assert resume_record(done.list_tasks(), done.list_verdicts()) is None
    with pytest.raises(ValueError):
        format_resume_record({"type": "other"})


def test_resume_plan_refuses_unknown_and_unregistered():
    with pytest.raises(ValueError):
        plan_resume([_task()], [])
    with pytest.raises(ValueError):
        plan_resume(
            [_task(task_id="fleet-1")],
            [_verdict("fleet-9", "passed")])


# -- the registry ---------------------------------------------------------------------


def test_registry_deterministic_ids_skip_supplied_numbers():
    registry = FleetRegistry()
    first = registry.register(_task(label="a"))
    second = registry.register(_task(label="b"))
    assert (first.task_id, second.task_id) == ("fleet-1", "fleet-2")
    registry2 = FleetRegistry()
    registry2.register(_task(task_id="fleet-1", label="pinned"))
    assert registry2.register(_task(label="next")).task_id == "fleet-2"


def test_registry_supplied_id_duplicates_and_unknown():
    registry = FleetRegistry()
    kept = registry.register(_task(task_id="nightly", label="s"))
    assert registry.get("nightly") is kept
    with pytest.raises(ValueError):
        registry.register(_task(task_id="nightly", label="again"))
    with pytest.raises(KeyError):
        registry.get("nope")
    with pytest.raises(KeyError):
        registry.record_verdict("nope", status="passed")
    with pytest.raises(KeyError):
        registry.record_bundle("nope", artefacts=[])


def test_registry_list_order_and_verdict_replacement():
    registry = _registry(
        _task(label="one"), _task(label="two"), _task(label="three"))
    assert [t.label for t in registry.list_tasks()] == [
        "one", "two", "three"]
    registry.record_verdict("fleet-2", status="running")
    registry.record_verdict(
        {"task_id": "fleet-2", "status": "passed", "exit_code": 0})
    assert registry.get_verdict("fleet-2").status == "passed"
    assert [v.task_id for v in registry.list_verdicts()] == ["fleet-2"]
    assert registry.get_verdict("fleet-1") is None


def test_registry_bundles_in_task_order():
    registry = _registry(_task(label="one"), _task(label="two"))
    registry.record_bundle("fleet-2", artefacts=["b.html"])
    registry.record_bundle(
        {"task_id": "fleet-1", "artifacts": ["a.html"]})
    assert [b.task_id for b in registry.list_bundles()] == [
        "fleet-1", "fleet-2"]
    assert registry.get_bundle("fleet-1").artefacts == ("a.html",)
    assert registry.get_bundle("fleet-2").artefacts == ("b.html",)


# -- the /fleet surface ------------------------------------------------------------------


def test_parse_show_verdict_and_resume_shapes():
    assert parse_fleet_args("") == ("show", None)
    assert parse_fleet_args(None) == ("show", None)
    assert parse_fleet_args("show") == ("show", None)
    assert parse_fleet_args("show fleet-1") == ("show", "fleet-1")
    assert parse_fleet_args("fleet-1") == ("show", "fleet-1")
    assert parse_fleet_args("verdict") == ("verdict", None)
    assert parse_fleet_args("resume") == ("resume", None)


def test_parse_bad_grammar_is_usage():
    for bad in ("show a b", "verdict fleet-1", "resume now",
                "frobnicate x", "show has space"):
        with pytest.raises(ValueError) as caught:
            parse_fleet_args(bad)
        assert str(caught.value) == USAGE
    with pytest.raises(ValueError):
        parse_fleet_args(7)


def test_format_task_and_verdict_state_in_words():
    registry = _registry(_task(task_id=None, label="suite"))
    task = registry.list_tasks()[0]
    line = format_fleet_task(task)
    assert "queued" in line and "fleet-1" in line
    registry.record_verdict("fleet-1", status="failed", exit_code=3)
    line = format_fleet_task(task, registry.get_verdict("fleet-1"))
    assert "failed" in line and "exit 3" in line
    with pytest.raises(ValueError):
        format_fleet_task(task, _verdict("fleet-2", "passed"))


def test_format_fleet_verdict_states_its_exit_code():
    registry = _fleet_with_verdicts()
    line = format_fleet_verdict(registry)
    assert "exit code 2" in line and "error" in line
    line = format_fleet_verdict(
        [_verdict("a", "passed"), _verdict("b", "passed")])
    assert line.startswith("Fleet verdict: passed")
    assert "exit code 0" in line


def test_format_tasks_empty_and_held():
    assert format_fleet_tasks(None).startswith("Fleet tasks: none.")
    assert format_fleet_tasks([]).startswith("Fleet tasks: none.")
    registry = _registry(_task(label="one"))
    text = format_fleet_tasks(registry)
    assert "Fleet tasks: 1 held." in text and "one" in text


def test_format_run_bundle_resume_and_whole_screen():
    registry = _fleet_with_verdicts()
    text = format_fleet_run(registry)
    assert "Fleet tasks: 5 held." in text
    assert "Fleet verdict:" in text and "exit code 2" in text
    bundle = build_artefact_bundle(
        {"task_id": "fleet-1", "artefacts": ["report.html"]})
    assert "report.html" in format_artefact_bundle(bundle)
    assert "no artefacts" in format_artefact_bundle(
        build_artefact_bundle({"task_id": "fleet-9"}))
    plan_text = format_resume_plan(registry.resume_plan())
    assert "remain" in plan_text and "fleet-1" in plan_text
    assert "Held back" in plan_text
    screen = format_fleet_mode(registry)
    assert screen.startswith("Fleet mode (M-106) - " + PLAIN_EXPLANATION)
    assert screen.rstrip().endswith(USAGE)
    assert "none." in format_fleet_mode(None)
