"""M-104 The keeper pattern - pure-layer tests.

TIER: integration

The pure layer is the keeper judgement as data: a
watch target (what is watched, how long it may
stay quiet, when it was last active, how many
restarts it has left) validated as data, a
mechanical verdict (active, quiet, or stalled,
from the age of the quiet alone), the keeper-law
action a stall owes (restart while restarts
remain, report when they run out), an
intervention record shaped as session news, and
a registry with deterministic ids. Nothing here
starts a timer or restarts anything.
"""

import pytest

from mythic_agent.core.keeper import (
    ACTIONS,
    KEEPER_SLICE,
    PLAIN_EXPLANATION,
    USAGE,
    WATCH_KINDS,
    WATCH_STATUSES,
    KeeperRegistry,
    WatchTarget,
    WatchVerdict,
    build_watch_target,
    format_intervention,
    format_keeper,
    format_verdict,
    format_watch_target,
    format_watch_targets,
    intervention_record,
    judge_watch,
    normalize_action,
    normalize_watch_kind,
    normalize_watch_status,
    parse_keeper_args,
    record_activity,
    record_restart,
    validate_watch_target,
)


def _target(**kwargs):
    kwargs.setdefault("kind", "background_job")
    kwargs.setdefault("label", "nightly build")
    return WatchTarget(**kwargs)


# -- constants and word readings --------------------------------------------


def test_constants_and_usage():
    assert KEEPER_SLICE == "M-104"
    assert WATCH_KINDS == ("background_job", "crew_member", "task")
    assert WATCH_STATUSES == ("active", "quiet", "stalled")
    assert ACTIONS == ("none", "restart", "report")
    assert USAGE.startswith("Usage: /keeper")
    assert "heartbeat" in USAGE and "check" in USAGE
    assert "timer that works" in PLAIN_EXPLANATION
    assert "restarts" in PLAIN_EXPLANATION


def test_kind_words_read_case_and_dashes():
    assert normalize_watch_kind("Crew-Member") == "crew_member"
    assert normalize_watch_kind(" TASK ") == "task"
    assert normalize_watch_status("Stalled") == "stalled"
    assert normalize_action("REPORT") == "report"
    for bad in ("job", "worker", "", None, 4):
        with pytest.raises(ValueError):
            normalize_watch_kind(bad)


# -- construction validation --------------------------------------------------


def test_target_defaults_are_the_keeper_cadence():
    target = _target()
    assert target.target_id is None
    assert target.stall_after_seconds == 600
    assert target.last_activity_at == 0.0
    assert target.restarts == 0 and target.max_restarts == 3
    assert target.restarts_remaining == 3
    assert target.restarts_exhausted is False
    assert target.to_record()["kind"] == "background_job"


def test_target_bad_kind_and_empty_label_refuse():
    with pytest.raises(ValueError):
        _target(kind="worker")
    with pytest.raises(ValueError):
        _target(label="   ")
    with pytest.raises(ValueError):
        _target(label=None)


def test_target_empty_id_refuses_but_absent_id_is_fine():
    with pytest.raises(ValueError):
        _target(target_id="  ")
    with pytest.raises(ValueError):
        _target(target_id="has space")
    assert _target(target_id="watch-9").target_id == "watch-9"


def test_target_stall_bound_bool_and_range_refuse():
    for bad in (True, 59, 86401, "600", 600.5, None):
        with pytest.raises(ValueError):
            _target(stall_after_seconds=bad)
    assert _target(stall_after_seconds=60).stall_after_seconds == 60
    assert _target(stall_after_seconds=86400).stall_after_seconds == 86400


def test_target_activity_and_restart_counts_validate():
    with pytest.raises(ValueError):
        _target(last_activity_at=-1.0)
    with pytest.raises(ValueError):
        _target(last_activity_at=True)
    with pytest.raises(ValueError):
        _target(restarts=-1)
    with pytest.raises(ValueError):
        _target(restarts=True)
    with pytest.raises(ValueError):
        _target(max_restarts=-1)
    with pytest.raises(ValueError):
        _target(max_restarts=101)
    with pytest.raises(ValueError):
        _target(max_restarts=False)
    assert _target(last_activity_at=12).last_activity_at == 12.0


# -- build / validate mapping ---------------------------------------------------


def test_build_mapping_canonical_spellings():
    target = build_watch_target({
        "kind": "crew_member", "label": "scout",
        "target_id": "watch-7", "stall_after_seconds": 900,
        "last_activity_at": 100, "restarts": 1, "max_restarts": 2})
    assert target == WatchTarget(
        target_id="watch-7", kind="crew_member", label="scout",
        stall_after_seconds=900, last_activity_at=100.0,
        restarts=1, max_restarts=2)
    assert validate_watch_target(target) is target


def test_build_mapping_alternate_spellings():
    target = build_watch_target({
        "type": "Background-Job", "name": "suite",
        "id": "job-watch", "stall_after": 300,
        "last_seen_at": 42})
    assert target.kind == "background_job"
    assert target.label == "suite" and target.target_id == "job-watch"
    assert target.stall_after_seconds == 300
    assert target.last_activity_at == 42.0


def test_build_mapping_same_value_both_spellings_is_fine():
    target = build_watch_target({
        "kind": "task", "type": "task", "label": "x", "name": "x"})
    assert target.kind == "task" and target.label == "x"


def test_build_mapping_conflicting_spellings_refuse():
    with pytest.raises(ValueError):
        build_watch_target({"kind": "task", "type": "crew_member",
                            "label": "x"})
    with pytest.raises(ValueError):
        build_watch_target({"kind": "task", "label": "x", "name": "y"})
    with pytest.raises(ValueError):
        build_watch_target({"kind": "task", "label": "x",
                            "stall_after_seconds": 600,
                            "stall_after": 300})
    with pytest.raises(ValueError):
        build_watch_target({"kind": "task", "label": "x",
                            "target_id": "a", "id": "b"})


def test_build_mapping_unknown_keys_and_missing_fields_refuse():
    with pytest.raises(ValueError):
        build_watch_target({"kind": "task", "label": "x", "bogus": 1})
    with pytest.raises(ValueError):
        build_watch_target({"label": "x"})
    with pytest.raises(ValueError):
        build_watch_target({"kind": "task"})
    with pytest.raises(ValueError):
        build_watch_target("not a mapping")
    with pytest.raises(ValueError):
        build_watch_target({"kind": "task", "label": "x",
                            "stall_after_seconds": True})


def test_build_watch_target_from_kwargs():
    target = build_watch_target(kind="task", label="ledger")
    assert target.kind == "task" and target.label == "ledger"


# -- activity and restarts -------------------------------------------------------


def test_record_activity_advances_and_allows_same_moment():
    target = _target(last_activity_at=100.0)
    moved = record_activity(target, 250)
    assert moved.last_activity_at == 250.0
    assert target.last_activity_at == 100.0
    assert record_activity(target, 100).last_activity_at == 100.0


def test_record_activity_backwards_time_refuses():
    target = _target(last_activity_at=100.0)
    with pytest.raises(ValueError):
        record_activity(target, 99.9)


def test_record_restart_increments_and_resets_clock():
    target = _target(last_activity_at=100.0, restarts=1)
    restarted = record_restart(target, 700)
    assert restarted.restarts == 2
    assert restarted.last_activity_at == 700.0
    assert target.restarts == 1


def test_record_restart_refuses_past_max_and_backwards():
    target = _target(restarts=3, max_restarts=3, last_activity_at=10.0)
    with pytest.raises(ValueError):
        record_restart(target, 20)
    fresh = _target(restarts=0, max_restarts=0)
    with pytest.raises(ValueError):
        record_restart(fresh, 20)
    with pytest.raises(ValueError):
        record_restart(_target(last_activity_at=100.0), 50)


# -- the verdict -------------------------------------------------------------------


def test_judge_active_and_quiet_bands():
    target = _target(stall_after_seconds=600, last_activity_at=1000.0)
    verdict = judge_watch(target, 1100)
    assert verdict.status == "active" and verdict.action == "none"
    assert verdict.age_seconds == 100.0
    verdict = judge_watch(target, 1599)
    assert verdict.status == "quiet" and verdict.action == "none"


def test_judge_boundaries_are_exact():
    target = _target(stall_after_seconds=600, last_activity_at=0.0)
    # Exactly half the bound is quiet, not active.
    assert judge_watch(target, 300).status == "quiet"
    # Exactly the bound is stalled, not quiet.
    assert judge_watch(target, 600).status == "stalled"
    assert judge_watch(target, 299).status == "active"


def test_judge_negative_age_refuses():
    target = _target(last_activity_at=100.0)
    with pytest.raises(ValueError):
        judge_watch(target, 50)


def test_judge_stalled_restart_while_restarts_remain():
    target = _target(stall_after_seconds=60, restarts=1, max_restarts=3)
    verdict = judge_watch(target, 60)
    assert verdict.status == "stalled" and verdict.action == "restart"
    assert verdict.target_id is None and verdict.kind == "background_job"
    assert verdict.label == "nightly build"


def test_judge_stalled_report_when_restarts_exhausted():
    target = _target(stall_after_seconds=60, restarts=3, max_restarts=3)
    assert judge_watch(target, 3600).action == "report"
    zero = _target(stall_after_seconds=60, restarts=0, max_restarts=0)
    assert judge_watch(zero, 60).action == "report"


def test_verdict_inconsistent_status_action_refuses():
    with pytest.raises(ValueError):
        WatchVerdict(label="x", status="active", action="restart")
    with pytest.raises(ValueError):
        WatchVerdict(label="x", status="stalled", action="none")


# -- intervention news -------------------------------------------------------------


def test_intervention_none_when_no_action_owed():
    target = _target(stall_after_seconds=600)
    assert intervention_record(judge_watch(target, 10), target) is None
    assert intervention_record(judge_watch(target, 400), target) is None


def test_intervention_record_shape_for_restart():
    target = _target(target_id="watch-1", stall_after_seconds=60,
                     restarts=0, max_restarts=3)
    record = intervention_record(judge_watch(target, 120), target)
    assert record["type"] == "keeper_intervention"
    assert record["news"] is True
    assert record["target_id"] == "watch-1"
    assert record["kind"] == "background_job"
    assert record["label"] == "nightly build"
    assert record["status"] == "stalled"
    assert record["action"] == "restart"
    assert record["age_seconds"] == 120.0
    assert record["restarts"] == 0
    assert "restart" in record["headline"]
    assert format_intervention(record) == record["headline"]


def test_intervention_record_shape_for_report():
    target = _target(stall_after_seconds=60, restarts=2, max_restarts=2)
    record = intervention_record(judge_watch(target, 600), target)
    assert record["action"] == "report" and record["restarts"] == 2
    assert "report" in record["headline"].lower()


# -- the registry ---------------------------------------------------------------------


def test_registry_deterministic_ids_skip_supplied_numbers():
    registry = KeeperRegistry()
    first = registry.register(_target(label="a"))
    second = registry.register(_target(label="b"))
    assert (first.target_id, second.target_id) == ("watch-1", "watch-2")
    registry2 = KeeperRegistry()
    registry2.register(_target(target_id="watch-1", label="pinned"))
    assert registry2.register(_target(label="next")).target_id == "watch-2"


def test_registry_supplied_id_used_as_given_and_duplicates_refuse():
    registry = KeeperRegistry()
    kept = registry.register(_target(target_id="crew-scout", label="s"))
    assert kept.target_id == "crew-scout"
    assert registry.get("crew-scout") is kept
    with pytest.raises(ValueError):
        registry.register(_target(target_id="crew-scout", label="again"))
    with pytest.raises(KeyError):
        registry.get("nope")


def test_registry_list_order_and_kind_filter():
    registry = KeeperRegistry()
    registry.register(_target(kind="task", label="one"))
    registry.register(_target(kind="crew_member", label="two"))
    registry.register(_target(kind="task", label="three"))
    assert [t.label for t in registry.list_targets()] == [
        "one", "two", "three"]
    assert [t.label for t in registry.list_targets("Task")] == [
        "one", "three"]
    assert [t.label for t in registry.list_targets("crew-member")] == [
        "two"]


def test_registry_heartbeat_moves_the_stored_target():
    registry = KeeperRegistry()
    kept = registry.register(_target(last_activity_at=10.0))
    moved = registry.heartbeat(kept.target_id, 90)
    assert moved.last_activity_at == 90.0
    assert registry.get(kept.target_id).last_activity_at == 90.0
    with pytest.raises(ValueError):
        registry.heartbeat(kept.target_id, 5)


def test_registry_check_order_and_interventions_filtering():
    registry = KeeperRegistry()
    registry.register(_target(label="fresh", stall_after_seconds=600,
                              last_activity_at=1000.0))
    registry.register(_target(label="dead", stall_after_seconds=60,
                              last_activity_at=0.0))
    registry.register(_target(label="spent", stall_after_seconds=60,
                              last_activity_at=0.0, restarts=3,
                              max_restarts=3))
    verdicts = registry.check(1000)
    assert [v.label for v in verdicts] == ["fresh", "dead", "spent"]
    assert [v.status for v in verdicts] == [
        "active", "stalled", "stalled"]
    records = registry.interventions(1000)
    assert [r["label"] for r in records] == ["dead", "spent"]
    assert [r["action"] for r in records] == ["restart", "report"]


# -- the /keeper surface -----------------------------------------------------------------


def test_parse_show_check_heartbeat_shapes():
    assert parse_keeper_args("") == ("show", None)
    assert parse_keeper_args(None) == ("show", None)
    assert parse_keeper_args("show") == ("show", None)
    assert parse_keeper_args("show watch-1") == ("show", "watch-1")
    assert parse_keeper_args("watch-1") == ("show", "watch-1")
    assert parse_keeper_args("check") == ("check", None)
    assert parse_keeper_args("heartbeat watch-2") == (
        "heartbeat", "watch-2")


def test_parse_grammar_words_in_wrong_shape_are_usage_errors():
    for bad in ("show a b", "check watch-1", "heartbeat",
                "heartbeat a b", "show has space", "frobnicate x",
                "check check"):
        with pytest.raises(ValueError) as caught:
            parse_keeper_args(bad)
        assert str(caught.value) == USAGE
    with pytest.raises(ValueError):
        parse_keeper_args(7)


def test_format_watch_target_states_status_in_words():
    target = _target(target_id="watch-1", stall_after_seconds=600,
                     last_activity_at=0.0)
    line = format_watch_target(target, 100)
    assert "active" in line and "100 seconds" in line
    line = format_watch_target(target, 700)
    assert "stalled" in line and "700 seconds" in line
    assert "restart" in line


def test_format_stalled_line_states_age_and_report_action():
    target = _target(stall_after_seconds=60, restarts=3, max_restarts=3)
    line = format_watch_target(target, 3600)
    assert "stalled" in line and "3600 seconds" in line
    assert "report" in line
    verdict = judge_watch(target, 3600)
    assert format_verdict(verdict) == line


def test_format_watch_targets_empty_and_held():
    assert format_watch_targets(None, 0).startswith("Keeper watches: none.")
    assert format_watch_targets([], 0).startswith("Keeper watches: none.")
    registry = KeeperRegistry()
    registry.register(_target(label="one"))
    text = format_watch_targets(registry, 10)
    assert "Keeper watches: 1 held." in text and "one" in text


def test_format_keeper_is_the_whole_screen():
    registry = KeeperRegistry()
    registry.register(_target(label="watched thing"))
    screen = format_keeper(registry, 10)
    assert screen.startswith("Keeper (M-104) - " + PLAIN_EXPLANATION)
    assert "Keeper watches: 1 held." in screen
    assert screen.rstrip().endswith(USAGE)
    assert "none." in format_keeper(None, 0)


# -- agent layer: watches held for a session (M-104) -----------------------

import copy as _copy
import sys as _sys
import time as _time

from mythic_agent.core.sessions import SessionStore


class _OfflineMemoryKeeper:
    def __init__(self):
        self.archived = []

    def search(self, query, top_k=2):
        return []

    def insert(self, text, metadata=None):
        self.archived.append(text)


@pytest.fixture()
def keeper_agent(tmp_path, monkeypatch):
    from mythic_agent.agents import llm
    from mythic_agent.core.secure_api import unsubscribe

    config = {"model": "test-model", "base_url": "http://localhost:1/v1", "api_keys": {}}
    monkeypatch.setattr(llm.config_manager, "MYTHIC_DIR", tmp_path / "state")
    monkeypatch.setattr(llm.config_manager, "load_config", lambda: _copy.deepcopy(config))
    monkeypatch.setattr(llm.config_manager, "save_config", lambda config: True)
    monkeypatch.setattr(llm, "get_vector_provider", lambda *args: _OfflineMemoryKeeper())
    instance = llm.Agent(project_root=tmp_path)
    from mythic_agent.core.policy import ToolPolicy
    instance.tool_policy = ToolPolicy("trusted")
    yield instance
    unsubscribe("agent_clear_history", instance._handle_clear_history)
    unsubscribe("agent_compact_history", instance._handle_compact_history)


def _keeper_events(store, session_id, type_name):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == type_name]


def _wait_job_state(agent, job_id, states, timeout=15.0):
    deadline = _time.monotonic() + timeout
    while _time.monotonic() < deadline:
        job = agent.get_background_job(job_id)
        if job.state in states:
            return job
        _time.sleep(0.05)
    return agent.get_background_job(job_id)


def _stalled_task(agent, **overrides):
    spec = {"target_id": "watch-task", "kind": "task",
            "label": "quiet task", "stall_after_seconds": 60,
            "last_activity_at": 1000.0, "max_restarts": 3}
    spec.update(overrides)
    return agent.register_keeper_watch(spec)


class TestKeeperAgentWatches:
    def test_status_starts_empty(self, keeper_agent):
        status = keeper_agent.keeper_status(now=10.0)
        assert status["targets"] == []
        assert status["verdicts"] == []
        assert "Keeper watches: none." in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["screen"] == format_keeper(
            keeper_agent._keeper_registry(), 10.0)

    def test_register_stamps_a_fresh_watch_with_now(self, keeper_agent):
        before = _time.time()
        record = keeper_agent.register_keeper_watch(
            {"kind": "task", "label": "fresh work"})
        assert record["target_id"] == "watch-1"
        assert record["last_activity_at"] >= before
        assert record["type"] == "keeper_watch"

    def test_register_and_heartbeat(self, keeper_agent):
        _stalled_task(keeper_agent)
        record = keeper_agent.keeper_heartbeat("watch-task", at=1500.0)
        assert record["last_activity_at"] == 1500.0
        target = keeper_agent.get_keeper_target("watch-task")
        assert target.last_activity_at == 1500.0
        with pytest.raises(ValueError):
            keeper_agent.keeper_heartbeat("watch-task", at=1400.0)
        with pytest.raises(KeyError):
            keeper_agent.keeper_heartbeat("watch-99", at=1500.0)
        with pytest.raises(KeyError):
            keeper_agent.get_keeper_target("watch-99")

    def test_check_active_watch_owes_nothing(self, keeper_agent):
        _stalled_task(keeper_agent)
        result = keeper_agent.keeper_check(now=1010.0)
        assert result["interventions"] == []
        assert result["verdicts"][0]["status"] == "active"
        assert result["verdicts"][0]["action"] == "none"

    def test_check_stalled_task_publishes_intervention_once(
            self, keeper_agent, tmp_path):
        store = SessionStore(tmp_path, tmp_path / "state")
        session_id = keeper_agent.attach_session(store)
        _stalled_task(keeper_agent)
        result = keeper_agent.keeper_check(now=2000.0)
        assert len(result["interventions"]) == 1
        record = result["interventions"][0]
        assert record["type"] == "keeper_intervention"
        assert record["action"] == "restart"
        assert record["target_id"] == "watch-task"
        events = _keeper_events(store, session_id, "keeper_intervention")
        assert len(events) == 1
        assert events[0]["target_id"] == "watch-task"
        keeper_agent.keeper_check(now=2000.0)
        events = _keeper_events(store, session_id, "keeper_intervention")
        assert len(events) == 1

    def test_check_exhausted_watch_reports(self, keeper_agent):
        _stalled_task(keeper_agent, restarts=3)
        result = keeper_agent.keeper_check(now=2000.0)
        assert result["verdicts"][0]["action"] == "report"
        assert result["interventions"][0]["action"] == "report"
        assert "reporting the stall" in result["interventions"][0]["headline"]

    def test_background_job_activity_feeds_its_watch(self, keeper_agent):
        keeper_agent.register_keeper_watch(
            {"target_id": "job-1", "kind": "background_job",
             "label": "watched job", "stall_after_seconds": 60,
             "last_activity_at": 1.0})
        record = keeper_agent.start_background_job(
            [_sys.executable, "-c", "print('kept-alive')"])
        assert record["job_id"] == "job-1"
        _wait_job_state(keeper_agent, "job-1", ("completed",))
        deadline = _time.monotonic() + 5.0
        target = keeper_agent.get_keeper_target("job-1")
        while target.last_activity_at <= 1.0 and _time.monotonic() < deadline:
            _time.sleep(0.05)
            target = keeper_agent.get_keeper_target("job-1")
        assert target.last_activity_at > 1.0
        status = keeper_agent.keeper_status(
            now=target.last_activity_at + 10.0)
        assert status["verdicts"][0]["status"] == "active"

    def test_check_restarts_a_stalled_background_job(self, keeper_agent):
        record = keeper_agent.start_background_job(
            [_sys.executable, "-c", "import time; time.sleep(30)"])
        _wait_job_state(keeper_agent, record["job_id"], ("running",))
        keeper_agent.register_keeper_watch(
            {"target_id": record["job_id"], "kind": "background_job",
             "label": "sleeping job", "stall_after_seconds": 60,
             "last_activity_at": _time.time() - 120.0})
        result = keeper_agent.keeper_check()
        assert len(result["interventions"]) == 1
        assert result["interventions"][0]["action"] == "restart"
        old = keeper_agent.get_background_job(record["job_id"])
        assert old.state == "cancelled"
        jobs = keeper_agent.background_jobs_status()["jobs"]
        assert len(jobs) == 2
        assert jobs[1]["job_id"] != record["job_id"]
        target = keeper_agent.get_keeper_target(record["job_id"])
        assert target.restarts == 1
        again = keeper_agent.keeper_check()
        assert again["interventions"] == []
        keeper_agent.kill_background_job(jobs[1]["job_id"], "test over")


class TestKeeperTerminalSurface:
    def test_show_is_the_whole_slice(self, keeper_agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(keeper_agent, "/keeper")
        assert text.startswith("Keeper (M-104) - ")
        assert "Keeper watches: none." in text
        assert USAGE in text

    def test_show_one_heartbeat_and_check_via_the_terminal(
            self, keeper_agent):
        from mythic_agent.terminal import _slash
        _stalled_task(keeper_agent)
        _, _, text = _slash(keeper_agent, "/keeper show watch-task")
        assert text.startswith("watch-task: ")
        _, _, text = _slash(keeper_agent, "/keeper heartbeat watch-task")
        assert text.startswith("watch-task: ")
        assert "active" in text
        _stalled_task(keeper_agent, target_id="watch-old",
                      label="old task")
        _, _, text = _slash(keeper_agent, "/keeper check")
        assert "Keeper watches: 2 held." in text
        assert "stalled" in text

    def test_bad_grammar_is_the_usage(self, keeper_agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(keeper_agent, "/keeper frobnicate x")
        assert text == USAGE
        _, _, text = _slash(keeper_agent, "/keeper heartbeat")
        assert text == USAGE
        _, _, text = _slash(keeper_agent, "/keeper show watch-99")
        assert "unknown watch target" in text


@pytest.fixture()
def keeper_handler(keeper_agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY

    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = keeper_agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _keeper_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestKeeperCommand:
    def test_show_is_default(self, keeper_handler, keeper_agent):
        keeper_handler._handle_keeper("")
        assert "Keeper watches: none." in _keeper_published_text(
            keeper_handler)

    def test_check_and_heartbeat_are_published(
            self, keeper_handler, keeper_agent):
        _stalled_task(keeper_agent)
        keeper_handler._handle_keeper("check")
        assert "stalled" in _keeper_published_text(keeper_handler)
        keeper_handler._handle_keeper("heartbeat watch-task")
        assert "watch-task: " in _keeper_published_text(keeper_handler)

    def test_show_one_via_the_handler(self, keeper_handler, keeper_agent):
        _stalled_task(keeper_agent)
        keeper_handler._handle_keeper("show watch-task")
        assert "watch-task: " in _keeper_published_text(keeper_handler)

    def test_bad_grammar_is_published(self, keeper_handler, keeper_agent):
        keeper_handler._handle_keeper("heartbeat")
        assert "Usage: /keeper" in _keeper_published_text(keeper_handler)
        keeper_handler._handle_keeper("show watch-99")
        assert "unknown watch target" in _keeper_published_text(
            keeper_handler)


class TestChatScreenRoutingKeeper:
    def test_keeper_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/keeper check", _FakeLog())
        assert calls == [("/keeper", "check")]
