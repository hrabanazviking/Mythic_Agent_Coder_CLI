"""M-105 Scheduled work - pure-layer tests.

TIER: integration

The pure layer is scheduled work as data: a job
(what to run as an argv list, never a shell
string; when to run it, as a schedule of data;
whether it is enabled; and its approval posture,
the same approval lines as live work) validated
as data, the next due moment computed
deterministically, a mechanical due judgement
(not due, due exactly at its moment, overdue,
waiting for approval, disabled), a due record
shaped as session news, and a registry with
deterministic ids. Nothing here starts a timer
or runs anything.
"""

from datetime import datetime, timedelta, timezone

import pytest

from mythic_agent.core.scheduled_work import (
    APPROVAL_POSTURES,
    DUE_ACTIONS,
    DUE_STATUSES,
    PLAIN_EXPLANATION,
    SCHEDULED_WORK_SLICE,
    SCHEDULE_KINDS,
    USAGE,
    WEEKDAYS,
    DueVerdict,
    Schedule,
    ScheduledJob,
    ScheduledWorkRegistry,
    build_schedule,
    build_scheduled_job,
    due_at_or_before,
    due_record,
    format_due_record,
    format_schedule,
    format_scheduled_job,
    format_scheduled_jobs,
    format_scheduled_work,
    format_verdict,
    judge_job,
    next_due,
    normalize_approval,
    normalize_schedule_kind,
    normalize_time_of_day,
    normalize_weekday,
    parse_schedule_args,
    validate_schedule,
    validate_scheduled_job,
)


def _job(**kwargs):
    kwargs.setdefault("label", "run the suite")
    kwargs.setdefault("argv", ["python", "-m", "pytest", "-q"])
    kwargs.setdefault("schedule", {"kind": "daily", "time": "06:30"})
    return build_scheduled_job(kwargs)


# -- constants and word readings ---------------------------------------


def test_constants_and_usage():
    assert SCHEDULED_WORK_SLICE == "M-105"
    assert SCHEDULE_KINDS == ("daily", "weekly", "interval")
    assert WEEKDAYS[0] == "monday" and WEEKDAYS[6] == "sunday"
    assert APPROVAL_POSTURES == ("unattended", "needs_approval")
    assert "waiting_for_approval" in DUE_STATUSES
    assert DUE_ACTIONS == ("none", "run", "await_approval")
    assert USAGE.startswith("Usage: /schedule")
    assert "approval" in PLAIN_EXPLANATION
    assert "never a shell string" in PLAIN_EXPLANATION


def test_word_readings():
    assert normalize_schedule_kind("Weekly") == "weekly"
    assert normalize_time_of_day("6:05") == "06:05"
    assert normalize_time_of_day("23:59") == "23:59"
    assert normalize_weekday("Tue") == "tuesday"
    assert normalize_weekday("FRIDAY") == "friday"
    assert normalize_weekday(0) == "monday"
    assert normalize_approval("needs-approval") == "needs_approval"
    assert normalize_approval(True) == "needs_approval"
    assert normalize_approval(False) == "unattended"
    for bad in ("dawn", "24:00", "12:60", "12:00:00", "", None):
        with pytest.raises(ValueError):
            normalize_time_of_day(bad)
    for bad in ("funday", "", None, 7, True):
        with pytest.raises(ValueError):
            normalize_weekday(bad)


# -- schedule validation -------------------------------------------------


def test_schedule_daily_weekly_interval_build():
    daily = build_schedule({"kind": "daily", "at": "6:30"})
    assert daily.time_of_day == "06:30" and daily.weekday is None
    weekly = build_schedule(
        {"type": "weekly", "day": "mon", "time_of_day": "09:00"})
    assert weekly.weekday == "monday" and weekly.time_of_day == "09:00"
    interval = build_schedule({"kind": "interval", "every_hours": 2})
    assert interval.interval_minutes == 120
    interval = build_schedule({"kind": "interval", "every_minutes": 45})
    assert interval.interval_minutes == 45
    assert validate_schedule(daily) is daily


def test_schedule_bad_values_refuse_plainly():
    for bad in ({"kind": "daily"},
                {"kind": "daily", "time": "dawn"},
                {"kind": "weekly", "time": "09:00"},
                {"kind": "weekly", "weekday": "funday", "time": "09:00"},
                {"kind": "interval"},
                {"kind": "interval", "every_minutes": 0},
                {"kind": "interval", "every_minutes": -5},
                {"kind": "interval", "every_minutes": True},
                {"kind": "monthly", "time": "09:00"},
                {"kind": "daily", "time": "09:00", "bogus": 1},
                {"kind": "daily", "time": "09:00", "weekday": "monday"},
                {"kind": "interval", "every_minutes": 5, "time": "09:00"}):
        with pytest.raises(ValueError):
            build_schedule(bad)
    with pytest.raises(ValueError):
        build_schedule({"kind": "daily", "time": "09:00", "at": "10:00"})
    with pytest.raises(ValueError):
        Schedule(kind="interval", interval_minutes=30,
                 anchor=datetime(2026, 1, 1, tzinfo=timezone.utc))


# -- job validation --------------------------------------------------------


def test_job_defaults_and_record():
    job = _job()
    assert job.enabled is True and job.approval == "unattended"
    assert job.requires_approval is False
    assert job.job_id is None and job.display_label == "run the suite"
    record = job.to_record()
    assert record["type"] == "scheduled_job"
    assert record["schedule"] == {
        "kind": "daily", "time_of_day": "06:30", "weekday": None,
        "interval_minutes": None, "anchor": None}


def test_job_shell_string_refuses_like_m103():
    with pytest.raises(ValueError):
        _job(argv="python -m pytest -q")
    with pytest.raises(ValueError):
        _job(argv=b"python -m pytest")
    with pytest.raises(ValueError):
        _job(argv=[])
    with pytest.raises(ValueError):
        _job(argv=["python", "  "])
    with pytest.raises(ValueError):
        _job(argv=["python", 7])


def test_job_mapping_spellings_and_conflicts():
    job = build_scheduled_job({
        "name": "upstream check", "command": ["git", "fetch"],
        "id": "schedule-9",
        "schedule": {"kind": "weekly", "weekday": "sunday",
                     "time": "08:00"},
        "requires_approval": True, "enabled": False})
    assert job.job_id == "schedule-9" and job.label == "upstream check"
    assert job.approval == "needs_approval" and job.enabled is False
    assert validate_scheduled_job(job) is job
    with pytest.raises(ValueError):
        build_scheduled_job({
            "argv": ["git"], "command": ["make"],
            "schedule": {"kind": "daily", "time": "08:00"}})
    with pytest.raises(ValueError):
        build_scheduled_job({
            "argv": ["git"], "schedule": {"kind": "daily",
                                          "time": "08:00"},
            "bogus": 1})
    with pytest.raises(ValueError):
        build_scheduled_job({"argv": ["git"]})
    with pytest.raises(ValueError):
        build_scheduled_job({
            "argv": ["git"], "schedule": {"kind": "daily",
                                          "time": "08:00"},
            "approval": "unattended", "requires_approval": True})
    with pytest.raises(ValueError):
        _job(enabled="yes")


# -- next_due -----------------------------------------------------------------


def test_next_due_daily():
    job = _job()
    assert next_due(job, datetime(2026, 1, 5, 5, 0)) == \
        datetime(2026, 1, 5, 6, 30)
    assert next_due(job, datetime(2026, 1, 5, 7, 0)) == \
        datetime(2026, 1, 6, 6, 30)
    # Exactly at the moment is due then, not a day later.
    assert next_due(job, datetime(2026, 1, 5, 6, 30)) == \
        datetime(2026, 1, 5, 6, 30)


def test_next_due_weekly():
    job = _job(schedule={"kind": "weekly", "weekday": "monday",
                         "time": "09:00"})
    monday = datetime(2026, 1, 5, 8, 0)  # 2026-01-05 is a Monday.
    assert monday.weekday() == 0
    assert next_due(job, monday) == datetime(2026, 1, 5, 9, 0)
    assert next_due(job, datetime(2026, 1, 5, 9, 0)) == \
        datetime(2026, 1, 5, 9, 0)
    assert next_due(job, datetime(2026, 1, 5, 10, 0)) == \
        datetime(2026, 1, 12, 9, 0)
    assert next_due(job, datetime(2026, 1, 7, 10, 0)) == \
        datetime(2026, 1, 12, 9, 0)


def test_next_due_interval_anchored():
    anchor = datetime(2026, 1, 5, 0, 0)
    job = _job(schedule={"kind": "interval", "every_minutes": 90,
                         "anchor": anchor})
    assert next_due(job, datetime(2026, 1, 5, 0, 0)) == anchor
    assert next_due(job, datetime(2026, 1, 5, 1, 0)) == \
        datetime(2026, 1, 5, 1, 30)
    assert next_due(job, datetime(2026, 1, 5, 1, 30)) == \
        datetime(2026, 1, 5, 1, 30)
    assert next_due(job, datetime(2026, 1, 4, 23, 0)) == anchor
    assert due_at_or_before(job, datetime(2026, 1, 4, 23, 0)) is None


def test_next_due_interval_unanchored_counts_from_day_start():
    job = _job(schedule={"kind": "interval", "every_hours": 2})
    assert next_due(job, datetime(2026, 1, 5, 5, 15)) == \
        datetime(2026, 1, 5, 6, 0)
    with pytest.raises(ValueError):
        next_due(job, datetime(2026, 1, 5, tzinfo=timezone.utc))


# -- the verdict -----------------------------------------------------------------


def test_judge_not_due_before_the_moment():
    job = _job()
    # At 05:00 the pending slot is yesterday's 06:30, and a run
    # recorded at 04:00 today covers it - the job is not due,
    # and today's 06:30 is next.
    verdict = judge_job(job, datetime(2026, 1, 5, 5, 0),
                        last_run_at=datetime(2026, 1, 5, 4, 0))
    assert verdict.status == "not_due" and verdict.action == "none"
    assert verdict.next_due_at == datetime(2026, 1, 5, 6, 30)


def test_judge_exactly_at_due_time_is_due():
    job = _job()
    verdict = judge_job(job, datetime(2026, 1, 5, 6, 30))
    assert verdict.status == "due" and verdict.action == "run"
    assert verdict.due_at == datetime(2026, 1, 5, 6, 30)
    assert verdict.next_due_at == datetime(2026, 1, 6, 6, 30)


def test_judge_past_due_time_is_overdue():
    job = _job()
    verdict = judge_job(job, datetime(2026, 1, 5, 9, 15))
    assert verdict.status == "overdue" and verdict.action == "run"
    assert verdict.due_at == datetime(2026, 1, 5, 6, 30)


def test_judge_already_run_slot_is_not_due():
    job = _job()
    verdict = judge_job(job, datetime(2026, 1, 5, 9, 15),
                        last_run_at=datetime(2026, 1, 5, 6, 30))
    assert verdict.status == "not_due" and verdict.action == "none"
    assert verdict.due_at is None
    assert verdict.next_due_at == datetime(2026, 1, 6, 6, 30)
    verdict = judge_job(job, datetime(2026, 1, 5, 6, 45),
                        last_run_at=datetime(2026, 1, 5, 6, 45))
    assert verdict.status == "not_due"


def test_judge_backwards_last_run_refuses():
    job = _job()
    with pytest.raises(ValueError):
        judge_job(job, datetime(2026, 1, 5, 6, 30),
                  last_run_at=datetime(2026, 1, 5, 7, 0))


def test_judge_disabled_job_never_runs():
    job = _job(enabled=False)
    verdict = judge_job(job, datetime(2026, 1, 5, 9, 15))
    assert verdict.status == "disabled" and verdict.action == "none"
    assert due_record(verdict, job) is None


def test_judge_needs_approval_waits_and_never_runs():
    job = _job(approval="needs_approval")
    verdict = judge_job(job, datetime(2026, 1, 5, 6, 30))
    assert verdict.status == "waiting_for_approval"
    assert verdict.action == "await_approval"
    verdict = judge_job(job, datetime(2026, 1, 5, 23, 59))
    assert verdict.status == "waiting_for_approval"
    assert verdict.action == "await_approval"
    with pytest.raises(ValueError):
        DueVerdict(label="x", status="waiting_for_approval",
                   action="run", due_at=datetime(2026, 1, 5, 6, 30))
    with pytest.raises(ValueError):
        DueVerdict(label="x", status="due", action="none",
                   due_at=datetime(2026, 1, 5, 6, 30))


# -- due news -----------------------------------------------------------------------


def test_due_record_none_when_nothing_owed():
    job = _job()
    verdict = judge_job(job, datetime(2026, 1, 5, 9, 15),
                        last_run_at=datetime(2026, 1, 5, 6, 30))
    assert due_record(verdict, job) is None


def test_due_record_shape_for_a_run():
    job = _job(job_id="schedule-1")
    verdict = judge_job(job, datetime(2026, 1, 5, 9, 15))
    record = due_record(verdict, job)
    assert record["type"] == "scheduled_job_due"
    assert record["news"] is True
    assert record["job_id"] == "schedule-1"
    assert record["status"] == "overdue" and record["action"] == "run"
    assert record["due_at"] == "2026-01-05T06:30:00"
    assert "overdue" in record["headline"]
    assert format_due_record(record) == record["headline"]


def test_due_record_shape_for_waiting_approval():
    job = _job(approval="needs_approval")
    verdict = judge_job(job, datetime(2026, 1, 5, 6, 30))
    record = due_record(verdict, job)
    assert record["action"] == "await_approval"
    assert record["approval"] == "needs_approval"
    assert "waiting for approval" in record["headline"]
    assert "does not run unattended" in record["headline"]


# -- the registry ---------------------------------------------------------------------


def test_registry_deterministic_ids_skip_supplied_numbers():
    registry = ScheduledWorkRegistry()
    first = registry.register(_job(label="a"))
    second = registry.register(_job(label="b"))
    assert (first.job_id, second.job_id) == ("schedule-1", "schedule-2")
    registry2 = ScheduledWorkRegistry()
    registry2.register(_job(job_id="schedule-1", label="pinned"))
    assert registry2.register(_job(label="next")).job_id == "schedule-2"


def test_registry_supplied_id_duplicates_and_unknown():
    registry = ScheduledWorkRegistry()
    kept = registry.register(_job(job_id="dawn-suite", label="s"))
    assert registry.get("dawn-suite") is kept
    with pytest.raises(ValueError):
        registry.register(_job(job_id="dawn-suite", label="again"))
    with pytest.raises(KeyError):
        registry.get("nope")


def test_registry_list_order_and_enabled_filter():
    registry = ScheduledWorkRegistry()
    registry.register(_job(label="one"))
    registry.register(_job(label="two", enabled=False))
    registry.register(_job(label="three"))
    assert [j.label for j in registry.list_jobs()] == [
        "one", "two", "three"]
    assert [j.label for j in registry.list_jobs(True)] == ["one", "three"]
    assert [j.label for j in registry.list_jobs(False)] == ["two"]


def test_registry_record_run_moves_the_verdict():
    registry = ScheduledWorkRegistry()
    kept = registry.register(_job())
    now = datetime(2026, 1, 5, 9, 15)
    assert registry.check(now)[0].status == "overdue"
    registry.record_run(kept.job_id, datetime(2026, 1, 5, 6, 30))
    assert registry.last_run(kept.job_id) == datetime(2026, 1, 5, 6, 30)
    assert registry.check(now)[0].status == "not_due"
    assert registry.due_records(now) == ()
    with pytest.raises(ValueError):
        registry.record_run(kept.job_id, datetime(2026, 1, 5, 6, 0))


def test_registry_due_records_only_owed():
    registry = ScheduledWorkRegistry()
    registry.register(_job(label="waiting", approval="needs_approval"))
    registry.register(_job(label="plain"))
    registry.register(_job(label="off", enabled=False))
    records = registry.due_records(datetime(2026, 1, 5, 6, 30))
    assert [r["label"] for r in records] == ["waiting", "plain"]
    assert [r["action"] for r in records] == ["await_approval", "run"]


# -- the /schedule surface ---------------------------------------------------------------


def test_parse_show_and_check_shapes():
    assert parse_schedule_args("") == ("show", None)
    assert parse_schedule_args(None) == ("show", None)
    assert parse_schedule_args("show") == ("show", None)
    assert parse_schedule_args("show schedule-1") == (
        "show", "schedule-1")
    assert parse_schedule_args("schedule-1") == ("show", "schedule-1")
    assert parse_schedule_args("check") == ("check", None)


def test_parse_bad_grammar_is_usage():
    for bad in ("show a b", "check schedule-1", "frobnicate x",
                "show has space"):
        with pytest.raises(ValueError) as caught:
            parse_schedule_args(bad)
        assert str(caught.value) == USAGE
    with pytest.raises(ValueError):
        parse_schedule_args(7)


def test_format_schedule_words():
    assert format_schedule({"kind": "daily", "time": "06:30"}) == \
        "daily at 06:30"
    assert format_schedule(
        {"kind": "weekly", "weekday": "monday", "time": "09:00"}) == \
        "weekly on monday at 09:00"
    assert format_schedule({"kind": "interval", "every_hours": 2}) == \
        "every 2 hours"
    assert format_schedule({"kind": "interval", "every_minutes": 45}) == \
        "every 45 minutes"


def test_format_job_and_verdict_state_in_words():
    job = _job(job_id="schedule-1")
    line = format_scheduled_job(job)
    assert "enabled" in line and "daily at 06:30" in line
    line = format_scheduled_job(job, datetime(2026, 1, 5, 6, 30))
    assert "due" in line and "run it" in line
    waiting = _job(approval="needs_approval")
    verdict = judge_job(waiting, datetime(2026, 1, 5, 6, 30))
    line = format_verdict(verdict)
    assert "waiting for approval" in line
    assert "never run unattended" in line


def test_format_jobs_empty_and_held():
    assert format_scheduled_jobs(None).startswith("Scheduled jobs: none.")
    assert format_scheduled_jobs([]).startswith("Scheduled jobs: none.")
    registry = ScheduledWorkRegistry()
    registry.register(_job(label="one"))
    text = format_scheduled_jobs(registry, datetime(2026, 1, 5, 5, 0))
    assert "Scheduled jobs: 1 held." in text and "one" in text


def test_format_scheduled_work_is_the_whole_screen():
    registry = ScheduledWorkRegistry()
    registry.register(_job(label="dawn suite"))
    screen = format_scheduled_work(registry)
    assert screen.startswith("Scheduled work (M-105) - " + PLAIN_EXPLANATION)
    assert "Scheduled jobs: 1 held." in screen
    assert screen.rstrip().endswith(USAGE)
    assert "none." in format_scheduled_work(None)


def test_format_registry_screen_respects_recorded_runs():
    registry = ScheduledWorkRegistry()
    kept = registry.register(_job())
    now = datetime(2026, 1, 5, 9, 15)
    assert "overdue" in format_scheduled_jobs(registry, now)
    registry.record_run(kept.job_id, datetime(2026, 1, 5, 6, 30))
    text = format_scheduled_jobs(registry, now)
    assert "not due" in text and "overdue" not in text
    screen = format_scheduled_work(registry, now)
    assert "not due" in screen


# -- agent layer: jobs held for a session (M-105) -----------------------

import copy as _copy
import sys as _sys
import time as _time

from mythic_agent.core.sessions import SessionStore


class _OfflineMemorySched:
    def __init__(self):
        self.archived = []

    def search(self, query, top_k=2):
        return []

    def insert(self, text, metadata=None):
        self.archived.append(text)


@pytest.fixture()
def sched_agent(tmp_path, monkeypatch):
    from mythic_agent.agents import llm
    from mythic_agent.core.secure_api import unsubscribe

    config = {"model": "test-model", "base_url": "http://localhost:1/v1", "api_keys": {}}
    monkeypatch.setattr(llm.config_manager, "MYTHIC_DIR", tmp_path / "state")
    monkeypatch.setattr(llm.config_manager, "load_config", lambda: _copy.deepcopy(config))
    monkeypatch.setattr(llm.config_manager, "save_config", lambda config: True)
    monkeypatch.setattr(llm, "get_vector_provider", lambda *args: _OfflineMemorySched())
    instance = llm.Agent(project_root=tmp_path)
    from mythic_agent.core.policy import ToolPolicy
    instance.tool_policy = ToolPolicy("trusted")
    yield instance
    unsubscribe("agent_clear_history", instance._handle_clear_history)
    unsubscribe("agent_compact_history", instance._handle_compact_history)


def _sched_events(store, session_id, type_name):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == type_name]


def _wait_bg_state(agent, job_id, states, timeout=15.0):
    deadline = _time.monotonic() + timeout
    while _time.monotonic() < deadline:
        job = agent.get_background_job(job_id)
        if job.state in states:
            return job
        _time.sleep(0.05)
    return agent.get_background_job(job_id)


_DUE = datetime(2026, 1, 5, 6, 30)


def _due_job(agent, **overrides):
    spec = {"label": "dawn suite",
            "argv": [_sys.executable, "-c", "print('sched-one')"],
            "schedule": {"kind": "daily", "time": "06:30"}}
    spec.update(overrides)
    return agent.register_scheduled_job(spec)


class TestScheduledAgentJobs:
    def test_status_starts_empty(self, sched_agent):
        status = sched_agent.scheduled_work_status(now=_DUE)
        assert status["jobs"] == []
        assert status["verdicts"] == []
        assert "Scheduled jobs: none." in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["screen"] == format_scheduled_work(
            sched_agent._scheduled_registry(), _DUE)

    def test_register_holds_the_job_as_data(self, sched_agent):
        record = _due_job(sched_agent)
        assert record["type"] == "scheduled_job"
        assert record["job_id"] == "schedule-1"
        assert record["approval"] == "unattended"
        status = sched_agent.scheduled_work_status(now=_DUE)
        assert [j["job_id"] for j in status["jobs"]] == ["schedule-1"]
        assert status["last_runs"] == {"schedule-1": None}
        assert status["verdicts"][0]["status"] == "due"
        assert status["verdicts"][0]["action"] == "run"
        assert "Scheduled jobs: 1 held." in status["screen"]

    def test_unknown_job_raises_keyerror(self, sched_agent):
        with pytest.raises(KeyError):
            sched_agent.get_scheduled_job("schedule-99")
        with pytest.raises(KeyError):
            sched_agent.get_scheduled_verdict("schedule-99", now=_DUE)
        with pytest.raises(KeyError):
            sched_agent.record_scheduled_run("schedule-99", at=_DUE)

    def test_record_run_moves_the_verdict(self, sched_agent):
        record = _due_job(sched_agent)
        later = datetime(2026, 1, 5, 9, 15)
        status = sched_agent.scheduled_work_status(now=later)
        assert status["verdicts"][0]["status"] == "overdue"
        sched_agent.record_scheduled_run(record["job_id"], at=_DUE)
        status = sched_agent.scheduled_work_status(now=later)
        assert status["verdicts"][0]["status"] == "not_due"
        assert status["last_runs"]["schedule-1"] == "2026-01-05T06:30:00"
        assert "not due" in status["screen"]
        with pytest.raises(ValueError):
            sched_agent.record_scheduled_run(
                record["job_id"], at=datetime(2026, 1, 5, 6, 0))

    def test_check_not_due_owes_nothing_and_runs_nothing(self, sched_agent):
        record = _due_job(sched_agent)
        sched_agent.record_scheduled_run(
            record["job_id"], at=datetime(2026, 1, 5, 4, 0))
        result = sched_agent.scheduled_check(
            now=datetime(2026, 1, 5, 5, 0))
        assert result["due_records"] == []
        assert result["started"] == []
        assert result["verdicts"][0]["status"] == "not_due"
        assert sched_agent.background_jobs_status()["jobs"] == []

    def test_check_runs_a_due_unattended_job_for_real(
            self, sched_agent, tmp_path):
        store = SessionStore(tmp_path, tmp_path / "state")
        session_id = sched_agent.attach_session(store)
        _due_job(sched_agent)
        result = sched_agent.scheduled_check(now=_DUE)
        assert len(result["due_records"]) == 1
        due = result["due_records"][0]
        assert due["type"] == "scheduled_job_due"
        assert due["job_id"] == "schedule-1"
        assert due["status"] == "due" and due["action"] == "run"
        assert len(result["started"]) == 1
        bg_id = result["started"][0]["job_id"]
        job = _wait_bg_state(sched_agent, bg_id, ("completed",))
        assert job.state == "completed"
        assert job.tail_lines == ("sched-one",)
        registry = sched_agent._scheduled_registry()
        assert registry.last_run("schedule-1") == _DUE
        events = _sched_events(store, session_id, "scheduled_job_due")
        assert len(events) == 1
        assert events[0]["job_id"] == "schedule-1"
        again = sched_agent.scheduled_check(now=_DUE)
        assert again["due_records"] == [] and again["started"] == []
        assert "not due" in again["screen"]

    def test_check_needs_approval_waits_and_never_runs(
            self, sched_agent, tmp_path):
        store = SessionStore(tmp_path, tmp_path / "state")
        session_id = sched_agent.attach_session(store)
        _due_job(sched_agent, approval="needs_approval")
        result = sched_agent.scheduled_check(now=_DUE)
        assert len(result["due_records"]) == 1
        due = result["due_records"][0]
        assert due["status"] == "waiting_for_approval"
        assert due["action"] == "await_approval"
        assert result["started"] == []
        assert sched_agent.background_jobs_status()["jobs"] == []
        registry = sched_agent._scheduled_registry()
        assert registry.last_run("schedule-1") is None
        events = _sched_events(store, session_id, "scheduled_job_due")
        assert len(events) == 1
        later = sched_agent.scheduled_check(
            now=datetime(2026, 1, 5, 9, 15))
        assert len(later["due_records"]) == 1
        assert later["started"] == []
        events = _sched_events(store, session_id, "scheduled_job_due")
        assert len(events) == 1

    def test_check_disabled_job_owes_nothing(self, sched_agent):
        _due_job(sched_agent, enabled=False)
        result = sched_agent.scheduled_check(now=_DUE)
        assert result["verdicts"][0]["status"] == "disabled"
        assert result["due_records"] == [] and result["started"] == []


class TestScheduledTerminalSurface:
    def test_show_is_the_whole_slice(self, sched_agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(sched_agent, "/schedule")
        assert text.startswith("Scheduled work (M-105) - ")
        assert "Scheduled jobs: none." in text
        assert USAGE in text

    def test_show_one_and_check_via_the_terminal(self, sched_agent):
        from mythic_agent.terminal import _slash
        _due_job(sched_agent)
        _, _, text = _slash(sched_agent, "/schedule show schedule-1")
        assert text.startswith("schedule-1: ")
        assert "due" in text
        _, _, text = _slash(sched_agent, "/schedule check")
        assert "Scheduled jobs: 1 held." in text
        assert "not due" in text
        jobs = sched_agent.background_jobs_status()["jobs"]
        assert len(jobs) == 1
        _wait_bg_state(sched_agent, jobs[0]["job_id"], ("completed",))

    def test_bad_grammar_is_the_usage(self, sched_agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(sched_agent, "/schedule frobnicate x")
        assert text == USAGE
        _, _, text = _slash(sched_agent, "/schedule check extra")
        assert text == USAGE
        _, _, text = _slash(sched_agent, "/schedule show schedule-99")
        assert "unknown scheduled job" in text


@pytest.fixture()
def sched_handler(sched_agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY

    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = sched_agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _sched_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestScheduledCommand:
    def test_show_is_default(self, sched_handler, sched_agent):
        sched_handler._handle_schedule("")
        assert "Scheduled jobs: none." in _sched_published_text(
            sched_handler)

    def test_show_one_via_the_handler(self, sched_handler, sched_agent):
        _due_job(sched_agent)
        sched_handler._handle_schedule("show schedule-1")
        assert "schedule-1: " in _sched_published_text(sched_handler)

    def test_check_is_published_and_runs_the_job(
            self, sched_handler, sched_agent):
        _due_job(sched_agent)
        sched_handler._handle_schedule("check")
        text = _sched_published_text(sched_handler)
        assert "Scheduled jobs: 1 held." in text
        assert "not due" in text
        jobs = sched_agent.background_jobs_status()["jobs"]
        assert len(jobs) == 1
        _wait_bg_state(sched_agent, jobs[0]["job_id"], ("completed",))

    def test_bad_grammar_is_published(self, sched_handler, sched_agent):
        sched_handler._handle_schedule("check extra")
        assert "Usage: /schedule" in _sched_published_text(sched_handler)
        sched_handler._handle_schedule("show schedule-99")
        assert "unknown scheduled job" in _sched_published_text(
            sched_handler)


class TestChatScreenRoutingSchedule:
    def test_schedule_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/schedule check", _FakeLog())
        assert calls == [("/schedule", "check")]
