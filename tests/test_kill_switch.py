"""M-108 The kill switch everywhere - pure-layer tests.

TIER: integration

The pure layer is the kill switch as data: a halt
(its targets - the coder, the crew, background
jobs and pending approvals, all four by default -
who or what asked, and a reason), a holdings
reading in the M-103 job-state words and the M-106
crew-status words, a mechanical judge returning
per-target verdicts (halted only when live work
was held, already stopped when the work had
finished, nothing held otherwise), a halt record
shaped as session news, and a registry with
deterministic ids. Nothing here starts a process,
kills anything or signals anything.
"""

import pytest

from mythic_agent.core.kill_switch import (
    BACKGROUND_ACTIVE_STATES,
    BACKGROUND_STATES,
    BACKGROUND_TERMINAL_STATES,
    CREW_FINISHED_STATUSES,
    CREW_STATUSES,
    HALT_OUTCOMES,
    HALT_STATUSES,
    HALT_TARGETS,
    KILL_SWITCH_SLICE,
    PLAIN_EXPLANATION,
    USAGE,
    Halt,
    HaltHoldings,
    HaltRegistry,
    HaltVerdict,
    Holdings,
    build_halt,
    build_holdings,
    format_halt,
    format_halt_record,
    format_halts,
    format_halts_screen,
    format_record,
    format_verdict,
    halt_record,
    judge_halt,
    normalize_halt_id,
    normalize_halt_target,
    parse_halt_args,
    validate_halt,
    validate_holdings,
)


def _holdings(**kwargs):
    return build_holdings(kwargs)


def _registry(*halts):
    registry = HaltRegistry()
    for halt in halts:
        registry.register(halt)
    return registry


# -- constants and word readings ---------------------------------------


def test_constants_and_usage():
    assert KILL_SWITCH_SLICE == "M-108"
    assert HALT_TARGETS == ("coder", "crew", "background_jobs", "approvals")
    assert HALT_OUTCOMES == ("halted", "already_stopped", "nothing_held")
    assert HALT_STATUSES == HALT_OUTCOMES
    assert BACKGROUND_STATES == (
        "queued", "running", "completed", "failed", "cancelled")
    assert BACKGROUND_ACTIVE_STATES == ("queued", "running")
    assert BACKGROUND_TERMINAL_STATES == ("completed", "failed", "cancelled")
    assert CREW_STATUSES == (
        "queued", "running", "passed", "failed", "error", "skipped")
    assert CREW_FINISHED_STATUSES == ("passed", "failed", "error", "skipped")
    assert USAGE.startswith("Usage: /halt")
    assert "halts the coder, the crew" in PLAIN_EXPLANATION
    assert "already" in PLAIN_EXPLANATION
    assert "nothing held" in PLAIN_EXPLANATION


def test_target_word_readings():
    assert normalize_halt_target("coder") == "coder"
    assert normalize_halt_target("Agent") == "coder"
    assert normalize_halt_target("crew") == "crew"
    assert normalize_halt_target("FLEET") == "crew"
    assert normalize_halt_target("background-jobs") == "background_jobs"
    assert normalize_halt_target("jobs") == "background_jobs"
    assert normalize_halt_target("background") == "background_jobs"
    assert normalize_halt_target("approval") == "approvals"
    assert normalize_halt_target("APPROVALS") == "approvals"
    assert normalize_halt_id("halt-1") == "halt-1"
    with pytest.raises(ValueError):
        normalize_halt_target("everything")
    with pytest.raises(ValueError):
        normalize_halt_target(None)
    with pytest.raises(ValueError):
        normalize_halt_id("two words")
    with pytest.raises(ValueError):
        normalize_halt_id("")


# -- the halt itself -----------------------------------------------------


def test_halt_defaults_halt_everything():
    halt = Halt()
    assert halt.targets == HALT_TARGETS
    assert halt.actor == "" and halt.reason == "" and halt.halt_id is None
    record = halt.to_record()
    assert record["type"] == "halt"
    assert record["slice"] == "M-108"
    assert record["targets"] == list(HALT_TARGETS)


def test_halt_targets_canonical_order_and_dedup():
    halt = Halt(targets=("approvals", "coder", "coder", "fleet"))
    assert halt.targets == ("coder", "crew", "approvals")
    assert Halt(targets="crew").targets == ("crew",)
    assert Halt(actor="  user  ").actor == "user"
    assert Halt(halt_id="halt-9").display_label == "halt-9"
    assert Halt(actor="user").display_label == "halt (pulled by user)"


def test_halt_refusals():
    with pytest.raises(ValueError):
        Halt(targets=())
    with pytest.raises(ValueError):
        Halt(targets=("bogus",))
    with pytest.raises(ValueError):
        Halt(targets=42)
    with pytest.raises(ValueError):
        Halt(actor=42)
    with pytest.raises(ValueError):
        Halt(halt_id="two words")


def test_halt_build_spellings():
    halt = build_halt({
        "id": "halt-7", "requested_by": "keeper", "why": "stalled",
        "target": "jobs"})
    assert halt.halt_id == "halt-7"
    assert halt.actor == "keeper"
    assert halt.reason == "stalled"
    assert halt.targets == ("background_jobs",)
    halt = build_halt(scope=["crew", "coder"], by="user")
    assert halt.targets == ("coder", "crew")
    assert build_halt(halt) is halt
    assert validate_halt(halt) is halt


def test_halt_build_refusals():
    with pytest.raises(ValueError):
        build_halt({"actor": "a", "by": "b"})
    with pytest.raises(ValueError):
        build_halt({"surprise": 1})
    with pytest.raises(ValueError):
        build_halt("crew")
    with pytest.raises(ValueError):
        build_halt({"targets": []})


# -- the holdings reading --------------------------------------------------


def test_holdings_defaults_are_a_quiet_session():
    holdings = HaltHoldings()
    assert holdings.coder_active is False
    assert holdings.background_jobs == ()
    assert holdings.crew_tasks == ()
    assert holdings.pending_approvals == 0
    assert holdings.background_active_ids == ()
    assert holdings.crew_running_ids == ()
    record = holdings.to_record()
    assert record["type"] == "halt_holdings"
    assert record["slice"] == "M-108"
    assert Holdings is HaltHoldings


def test_holdings_derived_ids():
    holdings = _holdings(
        coder_active=True,
        background_jobs=[("job-1", "running"), ("job-2", "queued"),
                         ("job-3", "completed"), ("job-4", "cancelled")],
        crew_tasks=[("task-1", "running"), ("task-2", "queued"),
                    ("task-3", "passed"), ("task-4", "error")],
        pending_approvals=2)
    assert holdings.background_active_ids == ("job-1", "job-2")
    assert holdings.background_finished_ids == ("job-3", "job-4")
    assert holdings.crew_running_ids == ("task-1",)
    assert holdings.crew_queued_ids == ("task-2",)
    assert holdings.crew_finished_ids == ("task-3", "task-4")
    assert holdings.pending_approvals == 2


def test_holdings_entry_spellings():
    holdings = build_holdings({
        "coder": True,
        "jobs": [{"id": "job-1", "status": "Running"},
                  {"job_id": "job-2", "state": "FAILED"}],
        "fleet_tasks": [{"task_id": "task-1", "state": "passed"}],
        "approvals": ["one", "two"]})
    assert holdings.coder_active is True
    assert holdings.background_jobs == (("job-1", "running"),
                                        ("job-2", "failed"))
    assert holdings.crew_tasks == (("task-1", "passed"),)
    assert holdings.pending_approvals == 2
    counted = build_holdings({"approvals_pending": 3})
    assert counted.pending_approvals == 3
    assert validate_holdings(holdings) is holdings


def test_holdings_refusals():
    with pytest.raises(ValueError):
        HaltHoldings(coder_active="yes")
    with pytest.raises(ValueError):
        HaltHoldings(pending_approvals=-1)
    with pytest.raises(ValueError):
        HaltHoldings(pending_approvals=True)
    with pytest.raises(ValueError):
        HaltHoldings(background_jobs=[("job-1", "bogus")])
    with pytest.raises(ValueError):
        HaltHoldings(crew_tasks=[("task-1", "running-ish")])
    with pytest.raises(ValueError):
        HaltHoldings(background_jobs=[("job-1",)])
    with pytest.raises(ValueError):
        build_holdings({"pending_approvals": 1, "approvals": ["a", "b"]})
    with pytest.raises(ValueError):
        build_holdings({"surprise": 1})
    with pytest.raises(ValueError):
        build_holdings("quiet")


# -- the judge ---------------------------------------------------------------


def test_judge_quiet_session_halts_nothing():
    verdict = judge_halt(Halt())
    assert verdict.status == "already_stopped"
    assert verdict.outcome_map == {
        "coder": "already_stopped", "crew": "nothing_held",
        "background_jobs": "nothing_held", "approvals": "nothing_held"}
    scoped = judge_halt(Halt(targets=("crew", "approvals")))
    assert scoped.status == "nothing_held"


def test_judge_busy_session_halts_everything_held():
    verdict = judge_halt(
        {"actor": "user", "reason": "enough"},
        {"coder_active": True,
         "background_jobs": [("job-1", "running")],
         "crew_tasks": [("task-1", "running")],
         "pending_approvals": 1})
    assert verdict.status == "halted"
    assert verdict.outcome_map == {
        "coder": "halted", "crew": "halted",
        "background_jobs": "halted", "approvals": "halted"}
    assert verdict.actor == "user" and verdict.reason == "enough"
    record = verdict.to_record()
    assert record["type"] == "halt_verdict"
    assert record["background_active"] == ["job-1"]
    assert record["crew_running"] == ["task-1"]
    assert record["pending_approvals"] == 1


def test_judge_finished_work_is_already_stopped_never_halted():
    verdict = judge_halt(
        Halt(),
        _holdings(background_jobs=[("job-1", "completed"),
                                   ("job-2", "cancelled")],
                  crew_tasks=[("task-1", "passed"),
                              ("task-2", "failed")]))
    assert verdict.outcome_map["background_jobs"] == "already_stopped"
    assert verdict.outcome_map["crew"] == "already_stopped"
    assert verdict.status == "already_stopped"


def test_judge_queued_crew_is_a_plan_not_held_work():
    verdict = judge_halt(
        Halt(targets=("crew",)),
        _holdings(crew_tasks=[("task-1", "queued"),
                              ("task-2", "queued")]))
    assert verdict.outcome_map == {"crew": "nothing_held"}
    assert verdict.status == "nothing_held"
    assert verdict.crew_queued_ids == ("task-1", "task-2")
    # A queued background job, by contrast, is a live managed job.
    jobs = judge_halt(
        Halt(targets=("background_jobs",)),
        _holdings(background_jobs=[("job-1", "queued")]))
    assert jobs.outcome_map == {"background_jobs": "halted"}


def test_judge_scoped_halt_touches_only_its_targets():
    verdict = judge_halt(
        Halt(targets=("background_jobs",)),
        _holdings(coder_active=True,
                  background_jobs=[("job-1", "running")],
                  pending_approvals=3))
    assert verdict.targets == ("background_jobs",)
    assert list(verdict.outcome_map) == ["background_jobs"]
    assert verdict.status == "halted"
    # The other holdings are still carried honestly on the verdict.
    assert verdict.coder_active is True
    assert verdict.pending_approvals == 3


def test_verdict_cannot_disagree_with_itself():
    holdings = _holdings(background_jobs=[("job-1", "running")])
    judged = judge_halt(Halt(targets=("background_jobs",)), holdings)
    forged = dict(judged.to_record())
    with pytest.raises(ValueError):
        HaltVerdict(
            halt_id=judged.halt_id, targets=judged.targets,
            outcomes=(("background_jobs", "nothing_held"),),
            status="nothing_held",
            background_active_ids=judged.background_active_ids)
    with pytest.raises(ValueError):
        HaltVerdict(
            targets=("background_jobs",),
            outcomes=(("background_jobs", "halted"),),
            status="already_stopped",
            background_active_ids=("job-1",))
    with pytest.raises(ValueError):
        HaltVerdict(status="paused")


# -- the news record -----------------------------------------------------------


def test_halt_record_is_always_news():
    record = halt_record(
        {"actor": "user", "reason": "bedtime"},
        {"coder_active": True,
         "background_jobs": [("job-1", "running"),
                             ("job-2", "completed")]})
    assert record["type"] == "kill_switch_pulled"
    assert record["news"] is True
    assert record["slice"] == "M-108"
    assert record["status"] == "halted"
    assert record["outcomes"]["background_jobs"] == "halted"
    headline = record["headline"]
    assert headline.startswith("Kill switch pulled")
    assert "the coder halted" in headline
    assert "background jobs halted (job-1)" in headline
    assert "Pulled by user." in headline
    assert "Reason: bedtime." in headline
    quiet = halt_record(Halt())
    assert quiet["status"] == "already_stopped"
    assert "the coder already stopped" in quiet["headline"]
    assert "nothing held" in quiet["headline"]
    assert format_halt_record(record) == headline
    assert format_record(record) == headline
    with pytest.raises(ValueError):
        format_halt_record({"type": "budget_paused", "headline": "x"})


def test_halt_record_headline_names_finished_and_queued_honestly():
    record = halt_record(
        Halt(),
        _holdings(crew_tasks=[("task-1", "passed"),
                              ("task-2", "queued")],
                  pending_approvals=2))
    assert "the crew already stopped (task-1)" in record["headline"]
    assert "pending approvals halted (2 approvals refused)" in (
        record["headline"])
    queued_only = halt_record(
        Halt(targets=("crew",)),
        _holdings(crew_tasks=[("task-9", "queued")]))
    assert "queued tasks are plans, not running work: task-9" in (
        queued_only["headline"])


# -- the registry ----------------------------------------------------------------


def test_registry_deterministic_ids():
    registry = HaltRegistry()
    first = registry.register({"actor": "user"})
    second = registry.register(Halt(targets=("crew",)))
    assert (first.halt_id, second.halt_id) == ("halt-1", "halt-2")
    assert [h.halt_id for h in registry.list_halts()] == ["halt-1", "halt-2"]
    assert registry.get("halt-2").targets == ("crew",)
    with pytest.raises(KeyError):
        registry.get("halt-99")


def test_registry_supplied_ids_and_duplicates():
    registry = HaltRegistry()
    registry.register({"halt_id": "halt-2"})
    fresh = registry.register({})
    assert fresh.halt_id == "halt-1"
    nxt = registry.register({})
    assert nxt.halt_id == "halt-3"
    with pytest.raises(ValueError):
        registry.register({"halt_id": "halt-2"})
    with pytest.raises(ValueError):
        registry.register(Halt(), actor="named twice over")


def test_registry_judges_at_the_pull_and_holds_the_verdict():
    registry = _registry({"actor": "user"}, {})
    assert registry.get_verdict("halt-1") is None
    verdict = registry.judge(
        "halt-1", _holdings(background_jobs=[("job-1", "running")]))
    assert verdict.status == "halted"
    assert registry.get_verdict("halt-1") is verdict
    assert registry.list_verdicts() == (verdict,)
    # Later holdings never re-judge the held verdict.
    record = registry.record("halt-1")
    assert record["outcomes"]["background_jobs"] == "halted"
    # An unjudged halt is judged by its record, against named holdings.
    fresh = registry.record("halt-2", _holdings(coder_active=True))
    assert fresh["outcomes"]["coder"] == "halted"
    assert registry.get_verdict("halt-2") is not None
    with pytest.raises(KeyError):
        registry.judge("halt-99")
    with pytest.raises(KeyError):
        registry.record("halt-99")


# -- formatters and the shared parser ---------------------------------------------


def test_format_halt_and_halts():
    assert format_halts() == "Kill switch: none pulled. No halt is held."
    assert format_halts([]) == "Kill switch: none pulled. No halt is held."
    halt = Halt(halt_id="halt-1", actor="user", reason="enough")
    line = format_halt(halt)
    assert line.startswith("halt-1: kill switch - targets:")
    assert "the coder" in line and "pending approvals" in line
    assert "Pulled by user." in line and "Reason: enough." in line
    verdict = judge_halt(halt, _holdings(coder_active=True))
    assert format_halt(halt, verdict).endswith("Verdict: halted.")
    other = judge_halt(Halt(halt_id="halt-2"))
    with pytest.raises(ValueError):
        format_halt(halt, other)
    registry = _registry(halt)
    registry.judge("halt-1", _holdings(coder_active=True))
    text = format_halts(registry)
    assert text.startswith("Kill switch: 1 pulled.")
    assert "Verdict: halted." in text


def test_format_verdict_and_screen():
    verdict = judge_halt(
        Halt(), _holdings(background_jobs=[("job-1", "running")]))
    text = format_verdict(verdict)
    assert text.startswith("Halt verdict: halted - ")
    assert "background jobs halted (job-1)" in text
    via_halt = format_verdict(
        Halt(targets=("approvals",)), _holdings(pending_approvals=1))
    assert "1 approval refused" in via_halt
    with pytest.raises(ValueError):
        format_verdict()
    screen = format_halts_screen(_registry({"actor": "user"}))
    assert screen.startswith("Kill switch (M-108) - ")
    assert "Kill switch: 1 pulled." in screen
    assert USAGE in screen
    assert format_halts_screen().splitlines()[2] == (
        "Kill switch: none pulled. No halt is held.")


def test_parse_halt_args_grammar():
    assert parse_halt_args("") == ("show", None)
    assert parse_halt_args(None) == ("show", None)
    assert parse_halt_args("show") == ("show", None)
    assert parse_halt_args("show halt-3") == ("show", "halt-3")
    assert parse_halt_args("halt-3") == ("show", "halt-3")
    assert parse_halt_args("frobnicate") == ("show", "frobnicate")
    assert parse_halt_args("pull") == ("pull", None)
    assert parse_halt_args("pull all") == ("pull", None)
    assert parse_halt_args("pull everything") == ("pull", None)
    assert parse_halt_args("pull crew") == ("pull", "crew")
    assert parse_halt_args("pull fleet") == ("pull", "crew")
    assert parse_halt_args("pull jobs") == ("pull", "background_jobs")
    assert parse_halt_args("PULL CODER") == ("pull", "coder")


def test_parse_halt_args_refusals_are_the_usage():
    for bad in ("crew", "all", "pull bogus", "pull crew extra",
                "show a b", "show two words here"):
        with pytest.raises(ValueError) as excinfo:
            parse_halt_args(bad)
        assert str(excinfo.value) == USAGE
    with pytest.raises(ValueError):
        parse_halt_args(42)


# -- more pure-layer readings ------------------------------------------------------


def test_holdings_entries_may_be_objects():
    class _Job:
        job_id = "job-1"
        state = "running"

    class _Task:
        task_id = "task-1"
        status = "passed"

    holdings = HaltHoldings(
        background_jobs=[_Job()], crew_tasks=[_Task()])
    assert holdings.background_active_ids == ("job-1",)
    assert holdings.crew_finished_ids == ("task-1",)
    with pytest.raises(ValueError):
        HaltHoldings(background_jobs=[object()])
    with pytest.raises(ValueError):
        HaltHoldings(background_jobs="job-1")


def test_holdings_approvals_spellings_agree_or_refuse():
    assert build_holdings({"approvals": 2}).pending_approvals == 2
    assert build_holdings(
        {"pending_approvals": 2, "approvals": ["a", "b"]}
    ).pending_approvals == 2
    with pytest.raises(ValueError):
        build_holdings({"coder_active": True, "coder": False})
    with pytest.raises(ValueError):
        build_holdings({"jobs": [], "background_jobs": [("j", "running")]})


def test_judge_accepts_validated_objects_unchanged():
    halt = Halt(targets=("coder",), actor="user")
    holdings = HaltHoldings(coder_active=True)
    verdict = judge_halt(halt, holdings)
    assert verdict.halt_id is None and verdict.actor == "user"
    assert verdict.outcomes == (("coder", "halted"),)
    assert validate_holdings(holdings) is holdings
    assert build_holdings(holdings) is holdings


def test_judge_status_is_the_strongest_outcome():
    mixed = judge_halt(
        Halt(),
        _holdings(background_jobs=[("job-1", "failed")]))
    assert mixed.status == "already_stopped"
    one_live = judge_halt(
        Halt(),
        _holdings(background_jobs=[("job-1", "failed")],
                  pending_approvals=1))
    assert one_live.status == "halted"
    approvals_only = judge_halt(
        Halt(targets=("approvals",)), _holdings(coder_active=True))
    assert approvals_only.status == "nothing_held"


def test_judge_crew_skipped_and_error_are_finished():
    verdict = judge_halt(
        Halt(targets=("crew",)),
        _holdings(crew_tasks=[("t-1", "skipped"), ("t-2", "error")]))
    assert verdict.outcome_map == {"crew": "already_stopped"}
    assert verdict.crew_finished_ids == ("t-1", "t-2")


def test_verdict_outcomes_follow_roadmap_target_order():
    verdict = judge_halt(
        Halt(targets=("approvals", "coder")), _holdings(coder_active=True))
    assert [target for target, _ in verdict.outcomes] == ["coder", "approvals"]
    assert verdict.outcome_map == {
        "coder": "halted", "approvals": "nothing_held"}


def test_halt_record_with_an_explicit_verdict():
    verdict = judge_halt(
        Halt(halt_id="halt-4"), _holdings(pending_approvals=1))
    record = halt_record(None, None, verdict)
    assert record["halt_id"] == "halt-4"
    assert record["outcomes"]["approvals"] == "halted"
    assert "1 approval refused" in record["headline"]


def test_dataclasses_are_frozen():
    import dataclasses

    halt = Halt()
    with pytest.raises(dataclasses.FrozenInstanceError):
        halt.actor = "someone"
    holdings = HaltHoldings()
    with pytest.raises(dataclasses.FrozenInstanceError):
        holdings.coder_active = True


def test_registry_get_verdict_unknown_id_raises():
    registry = HaltRegistry()
    with pytest.raises(KeyError):
        registry.get_verdict("halt-99")
    assert registry.list_verdicts() == ()


def test_format_halts_from_a_list_with_verdicts():
    halts = [Halt(halt_id="halt-1"), Halt(halt_id="halt-2")]
    verdicts = [judge_halt(halts[0], _holdings(coder_active=True))]
    text = format_halts(halts, verdicts)
    lines = text.splitlines()
    assert lines[0] == "Kill switch: 2 pulled."
    assert "Verdict: halted." in lines[1]
    assert "Verdict" not in lines[2]
    with pytest.raises(ValueError):
        format_halts(42)
    with pytest.raises(ValueError):
        format_halts(halts, verdicts="nope")


def test_format_halt_without_id_or_verdict():
    line = format_halt(Halt(targets=("crew",)))
    assert line == "halt: kill switch - targets: the crew."


def test_parse_pull_spelling_variants():
    assert parse_halt_args("pull background_jobs") == (
        "pull", "background_jobs")
    assert parse_halt_args("pull background-jobs") == (
        "pull", "background_jobs")
    assert parse_halt_args("pull approval") == ("pull", "approvals")
    assert parse_halt_args("  pull   crew  ") == ("pull", "crew")
    assert parse_halt_args("SHOW halt-1") == ("show", "halt-1")


def test_headline_for_a_scoped_quiet_pull():
    record = halt_record(Halt(targets=("background_jobs",), halt_id="halt-5"))
    assert record["headline"] == (
        "Kill switch pulled (halt-5): background jobs: nothing held.")
    assert record["targets"] == ["background_jobs"]
