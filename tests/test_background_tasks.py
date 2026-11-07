"""M-103 Background tasks - pure-layer tests.

TIER: integration

The pure layer is managed background jobs as data:
a job spec whose command is an argv list (never a
shell string), a lifecycle in the tasks layer's own
state words with legal transitions only, a bounded
live tail that counts the lines it drops, a kill
held first as a request, a completion record shaped
as session news, and a registry with deterministic
ids. Nothing here runs a process.
"""

import pytest

from mythic_agent.core.background_tasks import (
    BACKGROUND_TASKS_SLICE,
    DEFAULT_TAIL_MAX_BYTES,
    DEFAULT_TAIL_MAX_LINES,
    JOB_STATES,
    PLAIN_EXPLANATION,
    TERMINAL_STATES,
    USAGE,
    BackgroundJobRegistry,
    Job,
    JobSpec,
    KillRequest,
    append_output,
    append_output_text,
    apply_kill,
    build_job,
    build_job_spec,
    completion_record,
    display_label,
    finish_job,
    format_background,
    format_command,
    format_completion,
    format_job,
    format_jobs,
    format_kill_request,
    format_tail,
    job_tail,
    kill_job,
    normalize_job_id,
    normalize_state,
    parse_background_args,
    request_kill,
    start_job,
    transition_job,
    validate_job_spec,
)


def _job(job_id="job-1", **kwargs):
    return build_job(job_id, ["pytest", "-q"], **kwargs)


def _running(job_id="job-1", **kwargs):
    return start_job(_job(job_id, **kwargs))


# -- constants, ids and states ----------------------------------------------


def test_constants_and_usage():
    assert BACKGROUND_TASKS_SLICE == "M-103"
    assert JOB_STATES == (
        "queued", "running", "completed", "failed", "cancelled")
    assert TERMINAL_STATES == ("completed", "failed", "cancelled")
    assert USAGE.startswith("Usage: /background")
    assert "kill" in USAGE and "tail" in USAGE
    assert "never a shell string" in PLAIN_EXPLANATION
    assert DEFAULT_TAIL_MAX_LINES >= 1 and DEFAULT_TAIL_MAX_BYTES >= 1


def test_state_words_match_the_tasks_lifecycle():
    from mythic_agent.agents.tasks import TaskState
    assert {state.value for state in TaskState} == set(JOB_STATES)


def test_normalize_job_id_keeps_case_and_pinned_shape():
    assert normalize_job_id("job-1") == "job-1"
    assert normalize_job_id(" Build_2.x ") == "Build_2.x"
    for bad in ("", "   ", "has space", "no/slash", "semi;colon", None, 7):
        with pytest.raises(ValueError):
            normalize_job_id(bad)


def test_normalize_state_reads_case_and_dashes():
    assert normalize_state("Running") == "running"
    assert normalize_state(" QUEUED ") == "queued"
    for bad in ("done", "killed", "", None, 3):
        with pytest.raises(ValueError):
            normalize_state(bad)


# -- the job spec ------------------------------------------------------------


def test_spec_argv_label_and_record():
    spec = build_job_spec(["python", "-m", "pytest", "-q"], label="suite")
    assert spec.argv == ("python", "-m", "pytest", "-q")
    assert spec.cwd is None and spec.label == "suite"
    assert spec.command_text == "python -m pytest -q"
    assert spec.display_label == "suite"
    assert spec.to_record() == {
        "argv": ["python", "-m", "pytest", "-q"],
        "cwd": None, "label": "suite"}
    assert display_label(spec) == "suite"
    assert format_command(spec) == "python -m pytest -q"


def test_spec_label_defaults_to_the_command():
    spec = JobSpec(argv=["make", "build"], cwd="/tmp/work")
    assert spec.label == "" and spec.display_label == "make build"
    assert spec.cwd == "/tmp/work"


def test_spec_refuses_a_shell_string():
    with pytest.raises(ValueError):
        build_job_spec("pytest -q && make build")
    with pytest.raises(ValueError):
        validate_job_spec({"argv": "pytest -q"})


def test_spec_refuses_empty_and_nontext_parts():
    for bad in ([], (), ["pytest", ""], ["pytest", "  "],
                ["pytest", 3], [None], "x", 7, None):
        with pytest.raises(ValueError):
            build_job_spec(bad)


def test_spec_mapping_aliases_conflicts_and_unknown_keys():
    spec = validate_job_spec(
        {"command": ["make"], "name": "build", "cwd": "/w"})
    assert spec.argv == ("make",) and spec.label == "build"
    assert spec.cwd == "/w"
    same = validate_job_spec(
        {"argv": ["make"], "command": ["make"],
         "label": "b", "name": "b"})
    assert same.label == "b"
    with pytest.raises(ValueError):
        validate_job_spec({"argv": ["make"], "command": ["other"]})
    with pytest.raises(ValueError):
        validate_job_spec({"argv": ["make"], "label": "a", "name": "b"})
    with pytest.raises(ValueError):
        validate_job_spec({"argv": ["make"], "shell": True})
    with pytest.raises(ValueError):
        validate_job_spec({"label": "no command"})
    with pytest.raises(ValueError):
        validate_job_spec(["make"])


# -- lifecycle ---------------------------------------------------------------


def test_new_job_is_queued_with_defaults():
    job = _job()
    assert job.state == "queued" and job.exit_code is None
    assert job.is_terminal is False and job.kill_requested is False
    assert job.tail_lines == () and job.dropped_lines == 0
    record = job.to_record()
    assert record["type"] == "background_job"
    assert record["job_id"] == "job-1" and record["state"] == "queued"
    assert record["argv"] == ["pytest", "-q"]


def test_start_and_finish_completed():
    job = finish_job(_running(), 0)
    assert job.state == "completed" and job.exit_code == 0
    assert job.is_terminal is True


def test_finish_nonzero_fails():
    job = finish_job(_running(), 3)
    assert job.state == "failed" and job.exit_code == 3


def test_illegal_transitions_refuse():
    queued = _job()
    with pytest.raises(ValueError):
        finish_job(queued, 0)
    with pytest.raises(ValueError):
        transition_job(queued, "completed", exit_code=0)
    running = _running()
    with pytest.raises(ValueError):
        start_job(running)
    done = finish_job(running, 0)
    for move in ("running", "failed", "cancelled"):
        with pytest.raises(ValueError):
            transition_job(done, move)
    with pytest.raises(ValueError):
        transition_job(queued, "bogus")


def test_finish_requires_a_real_exit_code():
    running = _running()
    for bad in (None, "0", 0.0, True):
        with pytest.raises(ValueError):
            finish_job(running, bad)
    with pytest.raises(ValueError):
        transition_job(running, "completed", exit_code=2)
    with pytest.raises(ValueError):
        transition_job(running, "failed", exit_code=0)
    with pytest.raises(ValueError):
        transition_job(running, "cancelled", exit_code=1)


def test_job_record_validation_refuses_impossible_states():
    spec = build_job_spec(["make"])
    with pytest.raises(ValueError):
        Job(job_id="j", spec=spec, state="running", exit_code=0)
    with pytest.raises(ValueError):
        Job(job_id="j", spec=spec, state="completed", exit_code=1)
    with pytest.raises(ValueError):
        Job(job_id="j", spec=spec, state="cancelled", exit_code=137)
    with pytest.raises(ValueError):
        Job(job_id="j", spec=spec, tail_max_lines=0)
    with pytest.raises(ValueError):
        Job(job_id="j", spec=spec, dropped_lines=-1)


# -- the live tail -----------------------------------------------------------


def test_tail_appends_and_reads_newest():
    job = _running()
    job = append_output(job, "first\n")
    job = append_output_text(job, "second\nthird\n")
    assert job.tail_lines == ("first", "second", "third")
    assert job_tail(job) == ("first", "second", "third")
    assert job_tail(job, 2) == ("second", "third")
    assert job_tail(job, 99) == ("first", "second", "third")
    with pytest.raises(ValueError):
        job_tail(job, 0)


def test_tail_only_grows_while_running():
    with pytest.raises(ValueError):
        append_output(_job(), "too early")
    done = finish_job(_running(), 0)
    with pytest.raises(ValueError):
        append_output(done, "too late")
    with pytest.raises(ValueError):
        append_output(_running(), 42)


def test_tail_line_bound_drops_oldest_and_counts():
    job = _running(tail_max_lines=3)
    for line in ("a", "b", "c", "d", "e"):
        job = append_output(job, line)
    assert job.tail_lines == ("c", "d", "e")
    assert job.dropped_lines == 2


def test_tail_byte_bound_drops_oldest_and_counts():
    job = _running(tail_max_bytes=12)
    for line in ("aaaa", "bbbb", "cccc"):
        job = append_output(job, line)
    # Each kept line costs 5 bytes with its newline; two fit.
    assert job.tail_lines == ("bbbb", "cccc")
    assert job.dropped_lines == 1


def test_tail_never_cuts_a_single_long_line():
    job = _running(tail_max_bytes=4)
    job = append_output(job, "a very long line indeed")
    assert job.tail_lines == ("a very long line indeed",)
    assert job.dropped_lines == 0


# -- kill --------------------------------------------------------------------


def test_kill_request_is_data_and_changes_no_state():
    job = request_kill(_running(), "too slow")
    assert job.state == "running"
    assert job.kill_requested is True
    assert job.kill == KillRequest(requested=True, reason="too slow")
    assert "too slow" in format_kill_request(job)
    assert "No kill" in format_kill_request(_running())


def test_kill_request_refusals():
    done = finish_job(_running(), 0)
    with pytest.raises(ValueError):
        request_kill(done)
    asked = request_kill(_running())
    with pytest.raises(ValueError):
        request_kill(asked, "again")
    with pytest.raises(ValueError):
        KillRequest(requested=False, reason="orphan reason")
    with pytest.raises(ValueError):
        KillRequest(requested="yes")


def test_apply_kill_needs_a_request_and_cancels():
    with pytest.raises(ValueError):
        apply_kill(_running())
    job = apply_kill(request_kill(_running(), "stop"))
    assert job.state == "cancelled" and job.exit_code is None
    queued = kill_job(_job(), "never mind")
    assert queued.state == "cancelled" and queued.kill_requested is True


# -- completion as news --------------------------------------------------------


def test_completion_record_only_for_terminal_jobs():
    assert completion_record(_job()) is None
    assert completion_record(_running()) is None
    with pytest.raises(ValueError):
        format_completion(_running())


def test_completion_record_completed_and_failed():
    done = finish_job(_running(), 0)
    record = completion_record(done)
    assert record["type"] == "background_job_completed"
    assert record["news"] is True
    assert record["surface"] == "session_event"
    assert record["job_id"] == "job-1"
    assert record["state"] == "completed" and record["exit_code"] == 0
    assert record["headline"] == format_completion(done)
    assert "completed (exit 0)" in record["headline"]
    failed = finish_job(_running(), 2)
    assert "failed (exit 2)" in format_completion(failed)
    assert completion_record(failed)["exit_code"] == 2


def test_completion_record_killed_names_the_kill():
    job = kill_job(_running(), "user asked")
    headline = format_completion(job)
    assert "was killed" in headline and "user asked" in headline
    record = completion_record(job)
    assert record["state"] == "cancelled" and record["exit_code"] is None
    plain = apply_kill(request_kill(_running()))
    assert "was killed" in format_completion(plain)


# -- the registry --------------------------------------------------------------


def test_registry_deterministic_sequential_ids():
    registry = BackgroundJobRegistry()
    first = registry.create(["make", "build"])
    second = registry.create({"argv": ["pytest"], "label": "suite"})
    assert (first.job_id, second.job_id) == ("job-1", "job-2")
    assert second.label == "suite"
    assert [j.job_id for j in registry.list_jobs()] == ["job-1", "job-2"]


def test_registry_caller_ids_duplicates_and_unknown():
    registry = BackgroundJobRegistry()
    registry.create(["make"], job_id="build-1")
    with pytest.raises(ValueError):
        registry.create(["make"], job_id="build-1")
    with pytest.raises(KeyError):
        registry.get("nope")
    assert registry.get("build-1").state == "queued"
    # A supplied id takes its sequence number out of the pool.
    registry.create(["make"], job_id="job-1")
    assert registry.create(["make"]).job_id == "job-2"


def test_registry_flow_replaces_jobs_and_filters():
    registry = BackgroundJobRegistry()
    registry.create(["make", "build"], job_id="b")
    registry.create(["pytest"], job_id="t")
    registry.start("b")
    registry.append_output("b", "compiling")
    registry.finish("b", 0)
    registry.kill("t", "not needed")
    assert registry.get("b").state == "completed"
    assert registry.get("b").tail_lines == ("compiling",)
    assert registry.get("t").state == "cancelled"
    assert [j.job_id for j in registry.list_jobs("completed")] == ["b"]
    assert [j.job_id for j in registry.list_jobs("Running")] == []
    record = registry.completion_record("b")
    assert record["state"] == "completed"
    with pytest.raises(KeyError):
        registry.start("ghost")


# -- the /background surface ---------------------------------------------------


def test_format_job_and_jobs():
    job = _running()
    text = format_job(job)
    assert text.startswith("job-1:")
    assert "[running]" in text and "pytest -q" in text
    empty = format_jobs()
    assert empty.startswith("Background jobs: none.")
    listed = format_jobs([job])
    assert listed.startswith("Background jobs: 1 held.")
    assert "job-1" in listed
    registry = BackgroundJobRegistry()
    registry.create(["make"])
    assert "job-1" in format_jobs(registry)
    with pytest.raises(ValueError):
        format_jobs("job-1")


def test_format_tail_states_dropped_lines():
    job = _running(tail_max_lines=2)
    for line in ("old", "mid", "new"):
        job = append_output(job, line)
    text = format_tail(job)
    assert "Tail of job job-1" in text
    assert "1 earlier line(s) dropped" in text
    assert "mid" in text and "new" in text and "old" not in text
    quiet = format_tail(_running())
    assert "(no output yet)" in quiet


def test_format_background_is_the_whole_slice():
    text = format_background()
    assert text.startswith("Background tasks (M-103) - ")
    assert PLAIN_EXPLANATION in text
    assert "Background jobs: none." in text
    assert USAGE in text


def test_parse_background_args_grammar():
    assert parse_background_args("") == ("show", None)
    assert parse_background_args(None) == ("show", None)
    assert parse_background_args("list") == ("show", None)
    assert parse_background_args("show") == ("show", None)
    assert parse_background_args("show job-1") == ("show", "job-1")
    assert parse_background_args("job-1") == ("show", "job-1")
    assert parse_background_args("tail") == ("tail", None)
    assert parse_background_args("tail job-2") == ("tail", "job-2")
    assert parse_background_args("kill job-3") == ("kill", "job-3")
    assert parse_background_args("start pytest -q") == ("start", "pytest -q")


def test_parse_background_args_refusals():
    for bad in ("kill", "show job-1 extra", "tail a b", "frobnicate x",
                "show bad/id", "kill bad;id", 7):
        with pytest.raises(ValueError):
            parse_background_args(bad)
