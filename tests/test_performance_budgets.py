"""M-258 Performance budgets - pure-layer tests.

TIER: unit

Cold start, repo-map build on a 100k-file repo, TUI
frame health, memory ceiling - measured on the VM,
Mimir-class ARM, and the laptop; budgets from
measurement: a measure whose run rests on no held
measurement evidence, or whose measurement stands
over its budget on any machine, holds the whole
book open.
"""
import pytest

from mythic_agent.core.performance_budgets import (
    BARE_CLAIMS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    MACHINES,
    MEASURES,
    STAGES,
    BudgetEntry,
    BudgetRecord,
    BudgetRegistry,
    default_registry,
    derive_standing,
    derive_verdict,
    format_measure,
    format_measures,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(measure="cold_start", machine="vm",
                run="bench-2026-11-a",
                date="2026-11-13", measured=800, limit=1000,
                stages=STAGES,
                claims=("measurement_log_ref", "benchmark_ref"))
    base.update(kw)
    return BudgetRecord(**base)


def full_book(**overrides):
    records = []
    for measure, machine in default_registry().combinations():
        kw = dict(measure=measure, machine=machine,
                  run="bench-2026-11-a",
                  date="2026-11-13", measured=800, limit=1000,
                  stages=STAGES,
                  claims=("measurement_log_ref", "benchmark_ref"))
        kw.update(overrides.get(f"{measure}/{machine}", {}))
        records.append(BudgetRecord(**kw))
    return records


def test_registry_holds_four_measures_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 4
    assert reg.ids()[0] == "cold_start"
    assert reg.ids()[-1] == "memory_ceiling"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_measure_units_and_machines():
    reg = default_registry()
    assert reg.get("cold_start").unit == "milliseconds"
    assert reg.get("memory_ceiling").unit == "megabytes"
    assert reg.get("repo_map_100k").label == "Repo-map build on a 100k-file repo"
    assert tuple(m.id for m in MACHINES) == ("vm", "mimir_arm", "laptop")


def test_registry_unknown_measure_refused_by_name():
    with pytest.raises(ValidationError, match="unknown measure: warp_drive"):
        default_registry().get("warp_drive")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate measure"):
        BudgetRegistry(MEASURES + MEASURES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        BudgetRegistry([BudgetEntry(
            "cold_start", "", "milliseconds", "listed", "why")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        BudgetRegistry([BudgetEntry(
            "cold_start", "X", "milliseconds", "published", "why")])


def test_record_complete_within_budget_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held
    assert standing.grade == "held"
    assert standing.gaps == ()


def test_record_incomplete_walk_stands_open():
    standing = derive_standing(fresh_record(stages=STAGES[:3]))
    assert not standing.held
    assert any("not held" in g for g in standing.gaps)


def test_record_bad_stage_step_stands_open():
    bad = ("named", "compared", "judged", "held")
    standing = derive_standing(fresh_record(stages=bad))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_record_over_budget_stops_the_claim():
    standing = derive_standing(fresh_record(measured=1200))
    assert not standing.held
    assert any("over its budget" in g for g in standing.gaps)


def test_record_without_measurement_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("benchmark_ref",)))
    assert not standing.held
    assert any("no held measurement evidence" in g for g in standing.gaps)


def test_record_bare_claims_only_stand_open():
    standing = derive_standing(fresh_record(claims=("feeling",)))
    assert not standing.held
    assert any("bare claims only" in g for g in standing.gaps)


def test_record_unknown_evidence_kind_refused():
    with pytest.raises(ValidationError, match="unknown record evidence kind"):
        derive_standing(fresh_record(claims=("rumour",)))


def test_record_bad_date_refused():
    with pytest.raises(ValidationError, match="unknown measurement date"):
        derive_standing(fresh_record(date="13/11/2026"))


def test_record_negative_measurement_refused():
    with pytest.raises(ValidationError, match="negative"):
        derive_standing(fresh_record(measured=-1))


def test_record_unknown_machine_refused():
    with pytest.raises(ValidationError, match="unknown machine: toaster"):
        derive_standing(fresh_record(machine="toaster"))


def test_verdict_ready_when_every_combination_held():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.over_combinations == ()
    assert verdict.missing_combinations == ()


def test_verdict_one_over_budget_stops_the_whole_book():
    verdict = derive_verdict(full_book(
        **{"tui_frame/laptop": dict(measured=1200)}))
    assert not verdict.ready
    assert verdict.over_combinations == ("tui_frame/laptop",)


def test_verdict_missing_combination_stops_the_book():
    verdict = derive_verdict(full_book()[:11])
    assert not verdict.ready
    assert verdict.missing_combinations == ("memory_ceiling/laptop",)


def test_verdict_open_record_stops_the_book():
    verdict = derive_verdict(full_book(
        **{"cold_start/vm": dict(claims=("summary",))}))
    assert not verdict.ready
    assert any("cold_start/vm stands open" in g for g in verdict.gaps)


def test_prepare_report_all_within_may_certify():
    draft = prepare_report(
        "bench-2026-11", "release-1", "every combination within budget",
        "2026-11-13", 12, 12, claims=("measurement_log_ref",),
        certified=True)
    assert draft.state == "ready"
    assert draft.certified


def test_prepare_report_certify_short_of_within_refused():
    with pytest.raises(ValidationError, match="stops the certification"):
        prepare_report(
            "bench-2026-11", "release-1", "mostly within",
            "2026-11-13", 11, 12, claims=("measurement_log_ref",),
            certified=True)


def test_prepare_report_sealed_state_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report(
            "bench-2026-11", "release-1", "every combination within budget",
            "2026-11-13", 12, 12, claims=("measurement_log_ref",),
            state="sealed")


def test_prepare_report_bare_claim_refused():
    with pytest.raises(ValidationError, match="held measurements only"):
        prepare_report(
            "bench-2026-11", "release-1", "every combination within budget",
            "2026-11-13", 12, 12, claims=("feeling",))


def test_format_roads_name_the_measure_and_machine():
    line = format_record(fresh_record())
    assert "cold_start/vm" in line
    assert "800 of budget 1000 milliseconds" in line
    assert "held as measured" in line
    measure_line = format_measure(default_registry().get("memory_ceiling"))
    assert "Memory ceiling" in measure_line
    assert "megabytes" in measure_line
    assert len(format_measures().splitlines()) == 4
    assert len(format_records(full_book()).splitlines()) == 12
    assert HELD_EVIDENCE[0] == "measurement_log_ref"
    assert BARE_CLAIMS[-1] == "summary"
    assert "measurement_log_ref" in EVIDENCE_KINDS
    assert MEASURES[0].id == "cold_start"


# ---------------------------------------------------------------------
# M-258 Performance budgets - agent layer. The pure book is held by a
# session registry in the agent layer alone: measures are read from
# the shipped registry, measurement records are held one by one for
# the session, records, viewed standings and held reports are
# published as session news through the checkpoint road
# (journal-first, deduped per record, standing and verdict),
# standings, the index and the verdict are derived at call time from
# the held records - a measurement stands held only when it rests on
# held measurement evidence and stands within its budget - budget
# reports are held only as reports, state ready by default, may be
# marked shared by a human, a certification claimed only when every
# combination stands within budget, and never inflated, and the
# registry is session state, never a stored setting. This layer
# measures nothing, times no start and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    PERFORMANCEBUDGETS_USAGE,
    parse_performancebudgets_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.performance_budgets import (
    PLAIN_EXPLANATION,
    PERFORMANCE_BUDGETS_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_PB_EVENT_TYPES = (
    "performancebudgets_record", "performancebudgets_standing",
    "performancebudgets_verdict")

ALL_MEASURES = ["cold_start", "repo_map_100k", "tui_frame",
                "memory_ceiling"]


def _pb_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _pb_record(**overrides):
    raw = {
        "measure": "cold_start",
        "machine": "vm",
        "run": "bench-2026-11-a",
        "date": "2026-11-13",
        "measured": 800,
        "limit": 1000,
        "stages": list(STAGES),
        "claims": ["measurement_log_ref", "benchmark_ref"],
    }
    raw.update(overrides)
    return raw


def _pb_fresh_for(measure, machine, run="bench-2026-11-a"):
    return _pb_record(measure=measure, machine=machine, run=run)


class TestPerformanceBudgetsAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_measures(
            self, agent):
        status = agent.performancebudgets_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["performancebudgets_book"]["schema"] == (
            PERFORMANCE_BUDGETS_SCHEMA)
        assert [m["id"] for m in status[
            "performancebudgets_book"]["measures"]] == ALL_MEASURES
        assert status["performancebudgets_book"]["records"] == []
        assert status["performancebudgets_book"]["reports"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "Cold start" in status["measures_text"]
        assert "standing listed" in status["measures_text"]
        assert "none recorded this session" in status["screen"]
        assert "Performance budgets" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == PERFORMANCEBUDGETS_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._performancebudgets_registry()
        assert agent._performancebudgets_registry() is first
        assert agent._performancebudgets_store is first
        for name in ("performancebudgets_measures",
                     "performancebudgets_book",
                     "performancebudgets_status",
                     "get_performancebudgets_measure",
                     "get_performancebudgets_record",
                     "performancebudgets_standing",
                     "records_for_machine",
                     "performancebudgets_held",
                     "performancebudgets_index",
                     "performancebudgets_verdict",
                     "prepare_performancebudgets_report",
                     "get_performancebudgets_report",
                     "performancebudgets_reports",
                     "report_performancebudgets"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_performancebudgets_registry",
            "performancebudgets_measures",
            "performancebudgets_book",
            "performancebudgets_status",
            "get_performancebudgets_measure",
            "get_performancebudgets_record",
            "performancebudgets_standing", "records_for_machine",
            "performancebudgets_held", "performancebudgets_index",
            "performancebudgets_verdict",
            "register_performancebudgets_record",
            "register_performancebudgets_records",
            "record_performancebudgets_records",
            "view_performancebudgets",
            "prepare_performancebudgets_report",
            "report_performancebudgets",
            "_publish_performancebudgets_record",
            "_performancebudgets_screen",
            "_performancebudgets_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.performancebudgets_status()
        entry = agent.get_performancebudgets_measure("cold_start")
        assert entry.unit == "milliseconds"
        assert entry.label == "Cold start"
        standing = agent.performancebudgets_standing(
            "cold_start", "vm")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.grade == "open"
        assert agent.performancebudgets_held() == []
        assert agent.records_for_machine("vm") == []
        agent.performancebudgets_index()
        agent.performancebudgets_verdict()
        agent.report_performancebudgets()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _PB_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown measure"):
            agent.get_performancebudgets_measure("guess")
        with pytest.raises(ValueError, match="unknown measure"):
            agent.performancebudgets_standing("guess", "vm")
        with pytest.raises(ValueError, match="holds no"):
            agent.get_performancebudgets_record("cold_start", "vm")
        with pytest.raises(ValueError):
            agent.records_for_machine("")
        agent.close()


class TestPerformanceBudgetsAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_performancebudgets_record(
            _pb_record())
        assert result["record"]["measure"] == "cold_start"
        assert result["record"]["machine"] == "vm"
        assert result["record_news"]["type"] == (
            "performancebudgets_record")
        assert "held as measured" in result["screen"]
        status = agent.performancebudgets_status()
        assert [r["measure"] for r in status["records"]] == [
            "cold_start"]
        assert status["book"]["records"][0]["run"] == (
            "bench-2026-11-a")
        assert status["held"] == ["cold_start/vm"]
        assert status["open"] == []
        assert "held as measured" in status["records_text"]
        assert len(_pb_records(
            store, session_id, "performancebudgets_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_performancebudgets_record(_pb_record())
        with pytest.raises(ValueError, match="cold_start"):
            agent.register_performancebudgets_record(
                _pb_record(measured=900))
        assert len(_pb_records(
            store, session_id, "performancebudgets_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_performancebudgets_record(
                _pb_record(claims=["vibes"]))
        assert agent.performancebudgets_status()["records"] == []
        assert _pb_records(
            store, session_id, "performancebudgets_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_performancebudgets_records([
            _pb_fresh_for("tui_frame", "laptop"), _pb_record()])
        assert result["count"] == 2
        assert [r["measure"] for r in result["records_news"]] == [
            "tui_frame", "cold_start"]
        assert len(_pb_records(
            store, session_id, "performancebudgets_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_performancebudgets_records(
            [_pb_fresh_for("tui_frame", "laptop")])
        assert result["count"] == 1
        assert result["book"]["schema"] == PERFORMANCE_BUDGETS_SCHEMA
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_performancebudgets_records(
                [_pb_fresh_for("tui_frame", "laptop")])
        assert len(_pb_records(
            store, session_id, "performancebudgets_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_performancebudgets_record(_pb_record())
        result = agent.view_performancebudgets("cold_start", "vm")
        assert result["measure"]["id"] == "cold_start"
        assert result["standing"]["held"] is True
        assert result["record"]["run"] == "bench-2026-11-a"
        assert result["record_news"]["type"] == (
            "performancebudgets_standing")
        assert result["held_record_news"]["type"] == (
            "performancebudgets_record")
        assert len(_pb_records(
            store, session_id, "performancebudgets_record")) == 1
        assert len(_pb_records(
            store, session_id, "performancebudgets_standing")) == 1
        result = agent.view_performancebudgets(
            "repo_map_100k", "vm")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_pb_records(
            store, session_id, "performancebudgets_standing")) == 2
        agent.close()


class TestPerformanceBudgetsReports:
    def test_prepare_report_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_performancebudgets_report(
            "bench-2026-11", "release-1",
            "every combination within budget",
            "2026-11-13", 12, 12,
            claims=("measurement_log_ref", "report_ref"))
        assert result["report"]["state"] == "ready"
        assert result["report"]["certified"] is False
        assert result["report"]["inflated"] is False
        assert result["report_news"]["type"] == (
            "performancebudgets_verdict")
        assert "every combination within budget" in result["screen"]
        report = agent.get_performancebudgets_report("bench-2026-11")
        assert report.entry == "release-1"
        assert [r.book for r in
                agent.performancebudgets_reports()] == [
            "bench-2026-11"]
        assert len(_pb_records(
            store, session_id, "performancebudgets_verdict")) == 1
        agent.close()

    def test_report_unshared_state_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared"):
            agent.prepare_performancebudgets_report(
                "bench-2026-11", "release-1", "x",
                "2026-11-13", 12, 12,
                claims=("measurement_log_ref",), state="executed")
        assert agent.performancebudgets_reports() == []
        assert _pb_records(
            store, session_id, "performancebudgets_verdict") == []
        agent.close()

    def test_duplicate_report_refuses(self, agent):
        agent.prepare_performancebudgets_report(
            "bench-2026-11", "release-1",
            "every combination within budget", "2026-11-13", 12, 12,
            claims=("measurement_log_ref",))
        with pytest.raises(ValueError, match="bench-2026-11"):
            agent.prepare_performancebudgets_report(
                "bench-2026-11", "release-2",
                "a second telling", "2026-11-13", 12, 12,
                claims=("measurement_log_ref",))
        with pytest.raises(ValueError,
                           match="holds no budget report"):
            agent.get_performancebudgets_report("bench-2026-12")


class TestPerformanceBudgetsParseArgs:
    def test_parse_args_well(self):
        assert parse_performancebudgets_args("") == (
            "show", None, (), None)
        assert parse_performancebudgets_args(None) == (
            "show", None, (), None)
        assert parse_performancebudgets_args("measures") == (
            "measures", None, (), None)
        assert parse_performancebudgets_args(
            "measure cold_start") == (
            "measure", "cold_start", (), None)
        assert parse_performancebudgets_args(
            "record cold_start vm") == (
            "record", ("cold_start", "vm"), (), None)
        assert parse_performancebudgets_args(
            "standing tui_frame laptop") == (
            "standing", ("tui_frame", "laptop"), (), None)
        assert parse_performancebudgets_args("report") == (
            "reports", None, (), None)
        assert parse_performancebudgets_args(
            "report bench-2026-11") == (
            "report", "bench-2026-11", (), None)
        assert parse_performancebudgets_args("verdict") == (
            "verdict", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "measure", "record",
                    "record cold_start",
                    "measures now", "standing cold_start",
                    "report bench extra"):
            with pytest.raises(ValueError) as caught:
                parse_performancebudgets_args(bad)
            assert str(caught.value) == PERFORMANCEBUDGETS_USAGE


class TestPerformanceBudgetsTerminalRoad:
    def test_show_measures_measure_record_standing_report_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/performancebudgets")
        assert "Cold start (cold_start)" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/performancebudgets measures")
        assert "Memory ceiling" in text
        _, _, text = _slash(
            agent, "/performancebudgets measure memory_ceiling")
        assert "Memory ceiling" in text
        assert "megabytes" in text
        _, _, text = _slash(
            agent, "/performancebudgets record cold_start vm")
        assert "holds no" in text
        _, _, text = _slash(
            agent, "/performancebudgets standing cold_start vm")
        assert "cold_start/vm:" in text
        assert "open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/performancebudgets report")
        assert "none held" in text
        _, _, text = _slash(agent, "/performancebudgets verdict")
        assert "Performance budgets stand open" in text
        agent.register_performancebudgets_record(_pb_record())
        _, _, text = _slash(
            agent, "/performancebudgets record cold_start vm")
        assert "held as measured" in text
        _, _, text = _slash(
            agent, "/performancebudgets standing cold_start vm")
        assert "held as measured" in text
        _, _, text = _slash(agent, "/performancebudgets index")
        assert "held as measured" in text
        agent.prepare_performancebudgets_report(
            "bench-2026-11", "release-1",
            "every combination within budget", "2026-11-13", 12, 12,
            claims=("measurement_log_ref",))
        _, _, text = _slash(
            agent, "/performancebudgets report bench-2026-11")
        assert "every combination within budget" in text
        assert "never inflated" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/performancebudgets [show|measures|"
                "measure <measure>|"
                "record <measure> <machine>|"
                "standing <measure> <machine>|"
                "report [<book>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/performancebudgets dance party")
        assert text == PERFORMANCEBUDGETS_USAGE
        _, _, text = _slash(
            agent, "/performancebudgets measure guess")
        assert "unknown measure" in text


@pytest.fixture()
def pb_handler(agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY
    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda record, **kwargs: published.append((record, kwargs)))
    AGENT_REGISTRY["Primary"] = agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _pb_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestPerformanceBudgetsHandler:
    def test_show_is_default(self, pb_handler, agent):
        pb_handler._handle_performancebudgets("")
        assert "Cold start (cold_start)" in (
            _pb_published_text(pb_handler))

    def test_measure_record_and_verdict(
            self, pb_handler, agent):
        pb_handler._handle_performancebudgets(
            "measure repo_map_100k")
        assert "Repo-map build on a 100k-file repo" in (
            _pb_published_text(pb_handler))
        agent.register_performancebudgets_record(_pb_record())
        pb_handler._handle_performancebudgets(
            "record cold_start vm")
        assert "held as measured" in (
            _pb_published_text(pb_handler))
        pb_handler._handle_performancebudgets("verdict")
        assert "Performance budgets stand held" in (
            _pb_published_text(pb_handler))

    def test_bad_grammar_is_published(
            self, pb_handler, agent):
        pb_handler._handle_performancebudgets("dance party")
        assert PERFORMANCEBUDGETS_USAGE in (
            _pb_published_text(pb_handler))
        pb_handler._handle_performancebudgets("measure guess")
        assert "unknown measure" in (
            _pb_published_text(pb_handler))


class TestChatScreenRoutingPerformanceBudgets:
    def test_routes_as_system_command(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import (
            MainChatScreen)

        class _FakeLog:
            def __init__(self):
                self.lines = []

            def write(self, *args, **kwargs):
                self.lines.append(" ".join(str(a) for a in args))

        calls = []
        monkeypatch.setattr(
            chat_screen.SecureAPI, "publish_system_command",
            staticmethod(lambda cmd, args: calls.append(
                (cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        screen.handle_command("/performancebudgets verdict",
                              _FakeLog())
        assert calls == [("/performancebudgets", "verdict")]

    def test_chat_screen_help_and_usage_name_the_budgets(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/performancebudgets[/green] - show the "
                "Performance budgets (M-258)") in text
        assert ('"/performancebudgets": "Usage: '
                "/performancebudgets | "
                "/performancebudgets measures") in text


class TestPerformanceBudgetsDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.performancebudgets_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _PB_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        verdict = agent.performancebudgets_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_performancebudgets_record(_pb_record())
        agent.register_performancebudgets_record(
            _pb_fresh_for("tui_frame", "laptop"))
        verdict = agent.performancebudgets_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "cold_start/vm", "tui_frame/laptop"]
        assert "Performance budgets stand held" in (
            verdict["verdict_text"])

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_performancebudgets()
        assert report["book"]["schema"] == PERFORMANCE_BUDGETS_SCHEMA
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_performancebudgets_record(_pb_record())
        report = agent.report_performancebudgets()
        assert "held as measured" in report["records_text"]
        assert [s["measure"] for s in report["standings"]] == [
            "cold_start"]

    def test_records_for_machine_and_held_keys(self, agent):
        agent.register_performancebudgets_record(_pb_record())
        agent.register_performancebudgets_record(_pb_record(
            machine="laptop", run="bench-2026-11-b",
            measured=1200,
            stages=["named"], claims=["assertion"]))
        assert [r.run for r in
                agent.records_for_machine("vm")] == [
            "bench-2026-11-a"]
        assert [r.run for r in
                agent.records_for_machine("laptop")] == [
            "bench-2026-11-b"]
        assert agent.performancebudgets_held() == ["cold_start/vm"]
        standing = agent.performancebudgets_standing(
            "cold_start", "laptop")
        assert standing.held is False
        assert any("bare claims" in gap
                   for gap in standing.gaps)
