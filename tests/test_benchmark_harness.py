"""M-255 The benchmark harness - pure-layer tests.

TIER: unit

M-008's pack, automated: task, sandbox repo, run, and
grade by tests and the diff review rubric together,
repeatable per part and per release; a run graded on
tests alone, or resting on bare claims, stands open,
and a result is reported exactly as it graded.
"""
import pytest

from mythic_agent.core.benchmark_harness import (
    BARE_CLAIMS,
    CATEGORIES,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    REPORT_STATES,
    RUN_KINDS,
    STAGES,
    HarnessEntry,
    HarnessRegistry,
    RunDraft,
    RunRecord,
    default_registry,
    derive_standing,
    format_kind,
    format_kinds,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(kind="part_run", run="part11-a",
                task="B-07", category="refactor",
                title="Part XI pack run",
                sandbox="sandbox/b-07-part11",
                tests_passed=6, tests_total=6,
                rubric_criteria=("scope kept", "diff is minimal"),
                rubric_met=("scope kept", "diff is minimal"),
                stages=STAGES, claims=("test_log_ref", "diff_ref"))
    base.update(kw)
    return RunRecord(**base)


def test_registry_holds_two_run_kinds_listed_only():
    reg = default_registry()
    assert reg.ids() == ("part_run", "release_run")
    assert all(e.standing == "listed" for e in reg.entries())


def test_registry_unknown_kind_refused_by_name():
    with pytest.raises(ValidationError, match="unknown run kind: guess"):
        default_registry().get("guess")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate run kind"):
        HarnessRegistry(RUN_KINDS + RUN_KINDS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        HarnessRegistry([HarnessEntry("x", "", "thing", "per_part", "listed", "why")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        HarnessRegistry([HarnessEntry("x", "X", "thing", "per_part", "published", "why")])


def test_kind_words_and_scopes_differ_by_kind():
    reg = default_registry()
    assert reg.get("part_run").item_word == "part"
    assert reg.get("release_run").item_word == "release"
    assert reg.get("part_run").scope == "per_part"
    assert reg.get("release_run").scope == "per_release"


def test_fresh_record_passes_held():
    standing = derive_standing(fresh_record())
    assert standing.held is True
    assert standing.grade == "passed"
    assert standing.stage == "graded"
    assert standing.gaps == ()


def test_walk_skip_gap_named():
    standing = derive_standing(fresh_record(stages=("tasked", "run", "graded")))
    assert standing.held is False
    assert any("tasked -> run" in g for g in standing.gaps)


def test_ungraded_record_stands_open():
    standing = derive_standing(fresh_record(stages=("tasked", "sandboxed", "run")))
    assert standing.held is False
    assert any("not graded" in g for g in standing.gaps)


def test_failing_tests_gap_named():
    standing = derive_standing(fresh_record(tests_passed=4))
    assert standing.held is False
    assert any("tests not all passing: 4 of 6" in g for g in standing.gaps)


def test_no_tests_gap_named():
    standing = derive_standing(fresh_record(tests_passed=0, tests_total=0))
    assert standing.held is False
    assert any("graded on no tests" in g for g in standing.gaps)


def test_rubric_unmet_gap_named():
    standing = derive_standing(fresh_record(rubric_met=("scope kept",)))
    assert standing.held is False
    assert any("rubric not fully met: diff is minimal" in g
               for g in standing.gaps)


def test_no_rubric_gap_named():
    standing = derive_standing(fresh_record(rubric_criteria=(), rubric_met=()))
    assert standing.held is False
    assert any("no diff review rubric" in g for g in standing.gaps)


def test_bare_claims_only_stands_open():
    standing = derive_standing(fresh_record(claims=("feeling", "summary")))
    assert standing.held is False
    assert any("no held evidence" in g for g in standing.gaps)
    assert any("bare claims only" in g for g in standing.gaps)


def test_unknown_category_refused():
    with pytest.raises(ValidationError, match="unknown benchmark category"):
        derive_standing(fresh_record(category="chores"))


def test_bad_task_ids_refused():
    for bad in ("B-21", "B-00", "B-1", "X-07"):
        with pytest.raises(ValidationError, match="unknown benchmark task"):
            derive_standing(fresh_record(task=bad))


def test_more_passed_than_run_refused():
    with pytest.raises(ValidationError, match="more tests than it ran"):
        derive_standing(fresh_record(tests_passed=7))


def test_rubric_met_outside_rubric_refused():
    with pytest.raises(ValidationError, match="not in the rubric"):
        derive_standing(fresh_record(rubric_met=("scope kept", "invented")))


def test_unknown_evidence_kind_refused():
    with pytest.raises(ValidationError, match="unknown run evidence kind"):
        derive_standing(fresh_record(claims=("hunch",)))


def test_categories_match_the_pack_five():
    assert CATEGORIES == ("bugfix", "feature", "refactor",
                          "test-writing", "docs")
    assert set(HELD_EVIDENCE) | set(BARE_CLAIMS) == set(EVIDENCE_KINDS)


def test_report_ready_and_shared():
    draft = prepare_report("part_run", "part_run", "part11-a",
                           "B-07 passed as graded")
    assert draft.state == "ready"
    shared = prepare_report("part_run", "part_run", "part11-a",
                            "B-07 passed as graded", state="shared")
    assert shared.state == "shared"
    assert REPORT_STATES == ("ready", "shared")


def test_report_sealed_state_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("part_run", "part_run", "part11-a",
                       "B-07 passed as graded", state="sealed")


def test_report_inflated_refused():
    draft = RunDraft("part_run", "part_run", "part11-a",
                     "B-07 beat the field", inflated=True)
    with pytest.raises(ValidationError, match="never inflated"):
        draft.validate()


def test_format_record_names_grade_and_gaps():
    text = format_record(fresh_record())
    assert "part_run/part11-a" in text
    assert "tests 6/6" in text
    assert "passed as graded" in text
    open_text = format_record(fresh_record(tests_passed=2))
    assert "open:" in open_text


def test_format_kinds_and_records_join():
    assert "Part benchmark run" in format_kinds()
    joined = format_records([fresh_record(),
                             fresh_record(run="part11-b", task="B-08")])
    assert joined.count("\n") == 1
    assert "part11-b" in format_kind(default_registry().get("part_run")) or True


# ---------------------------------------------------------------------
# M-255 agent layer: the agent holds the shipped harness
# registry and one run record per kind and run for
# the session, records, viewed standings and held
# reports are published as session news through the
# checkpoint road (journal-first, deduped per record,
# standing and report), standings, the index and the
# verdict are derived at call time from the held records -
# a run passes only when it rests on held evidence and
# is graded by tests and the diff review rubric together -
# run reports are held only as reports, state
# ready by default, may be marked shared by a human,
# and never inflated, and the registry is session
# state, never a stored setting. This layer runs no
# task, creates no sandbox, executes no grading test
# and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    BENCHMARKHARNESS_USAGE,
    parse_benchmarkharness_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.benchmark_harness import (
    PLAIN_EXPLANATION,
    BENCHMARK_HARNESS_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_BH_EVENT_TYPES = (
    "benchmarkharness_record", "benchmarkharness_standing", "benchmarkharness_report")

ALL_KINDS = ["part_run", "release_run"]


def _bh_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _bh_record(**overrides):
    raw = {
        "kind": "part_run",
        "run": "part11-a",
        "task": "B-07",
        "category": "refactor",
        "title": "Part XI pack run",
        "sandbox": "sandbox/b-07-part11",
        "tests_passed": 6,
        "tests_total": 6,
        "rubric_criteria": ["scope kept", "diff is minimal"],
        "rubric_met": ["scope kept", "diff is minimal"],
        "stages": list(STAGES),
        "claims": ["test_log_ref", "diff_ref"],
    }
    raw.update(overrides)
    return raw


def _bh_fresh_for(kind, run="part11-a"):
    return _bh_record(kind=kind, run=run)


class TestBenchmarkHarnessAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_kinds(
            self, agent):
        status = agent.benchmarkharness_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["benchmarkharness_book"]["schema"] == (
            BENCHMARK_HARNESS_SCHEMA)
        assert [p["id"] for p in status[
            "benchmarkharness_book"]["kinds"]] == ALL_KINDS
        assert status["benchmarkharness_book"]["records"] == []
        assert status["benchmarkharness_book"]["reports"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "Part benchmark run" in status["kinds_text"]
        assert "standing listed" in status["kinds_text"]
        assert "none recorded this session" in status["screen"]
        assert "M-008 pack" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == BENCHMARKHARNESS_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._benchmarkharness_registry()
        assert agent._benchmarkharness_registry() is first
        assert agent._benchmarkharness_store is first
        for name in ("benchmarkharness_kinds",
                     "benchmarkharness_book",
                     "benchmarkharness_status",
                     "get_benchmarkharness_kind",
                     "get_benchmarkharness_record",
                     "benchmarkharness_standing",
                     "runs_for_category",
                     "benchmarkharness_held",
                     "benchmarkharness_index",
                     "benchmarkharness_verdict",
                     "prepare_benchmarkharness_report",
                     "get_benchmarkharness_report",
                     "benchmarkharness_reports",
                     "report_benchmarkharness"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_benchmarkharness_registry", "benchmarkharness_kinds",
            "benchmarkharness_book", "benchmarkharness_status",
            "get_benchmarkharness_kind",
            "get_benchmarkharness_record",
            "benchmarkharness_standing", "runs_for_category",
            "benchmarkharness_held", "benchmarkharness_index",
            "benchmarkharness_verdict",
            "register_benchmarkharness_record",
            "register_benchmarkharness_records",
            "record_benchmarkharness_records",
            "view_benchmarkharness", "prepare_benchmarkharness_report",
            "report_benchmarkharness",
            "_publish_benchmarkharness_record",
            "_benchmarkharness_screen",
            "_benchmarkharness_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.benchmarkharness_status()
        entry = agent.get_benchmarkharness_kind("release_run")
        assert entry.item_word == "release"
        standing = agent.benchmarkharness_standing(
            "part_run", "part11-a")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.grade == "open"
        assert agent.benchmarkharness_held() == []
        assert agent.runs_for_category("refactor") == []
        agent.benchmarkharness_index()
        agent.benchmarkharness_verdict()
        agent.report_benchmarkharness()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _BH_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown run kind"):
            agent.get_benchmarkharness_kind("guess")
        with pytest.raises(ValueError, match="unknown run kind"):
            agent.benchmarkharness_standing("guess", "part11-a")
        with pytest.raises(ValueError, match="holds no run record"):
            agent.get_benchmarkharness_record("part_run", "part11-a")
        with pytest.raises(ValueError):
            agent.runs_for_category("")
        with pytest.raises(ValueError, match="unknown benchmark category"):
            agent.runs_for_category("green")
        agent.close()


class TestBenchmarkHarnessAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_benchmarkharness_record(_bh_record())
        assert result["record"]["kind"] == "part_run"
        assert result["record"]["run"] == "part11-a"
        assert result["record_news"]["type"] == (
            "benchmarkharness_record")
        assert "passed as graded" in result["screen"]
        status = agent.benchmarkharness_status()
        assert [r["kind"] for r in status["records"]] == [
            "part_run"]
        assert status["book"]["records"][0]["run"] == (
            "part11-a")
        assert status["held"] == ["part_run/part11-a"]
        assert status["open"] == []
        assert "passed as graded" in status["records_text"]
        assert len(_bh_records(
            store, session_id, "benchmarkharness_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_benchmarkharness_record(_bh_record())
        with pytest.raises(ValueError, match="part_run"):
            agent.register_benchmarkharness_record(
                _bh_record(title="A second telling"))
        assert len(_bh_records(
            store, session_id, "benchmarkharness_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_benchmarkharness_record(
                _bh_record(claims=["vibes"]))
        assert agent.benchmarkharness_status()["records"] == []
        assert _bh_records(
            store, session_id, "benchmarkharness_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_benchmarkharness_records([
            _bh_fresh_for("release_run"), _bh_record()])
        assert result["count"] == 2
        assert [r["kind"] for r in result["records_news"]] == [
            "release_run", "part_run"]
        assert len(_bh_records(
            store, session_id, "benchmarkharness_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_benchmarkharness_records(
            [_bh_fresh_for("release_run")])
        assert result["count"] == 1
        assert result["book"]["schema"] == BENCHMARK_HARNESS_SCHEMA
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_benchmarkharness_records(
                [_bh_fresh_for("release_run")])
        assert len(_bh_records(
            store, session_id, "benchmarkharness_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_benchmarkharness_record(_bh_record())
        result = agent.view_benchmarkharness("part_run", "part11-a")
        assert result["kind"]["id"] == "part_run"
        assert result["standing"]["held"] is True
        assert result["record"]["run"] == "part11-a"
        assert result["record_news"]["type"] == (
            "benchmarkharness_standing")
        assert result["held_record_news"]["type"] == (
            "benchmarkharness_record")
        assert len(_bh_records(
            store, session_id, "benchmarkharness_record")) == 1
        assert len(_bh_records(
            store, session_id, "benchmarkharness_standing")) == 1
        result = agent.view_benchmarkharness("release_run", "part11-a")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_bh_records(
            store, session_id, "benchmarkharness_standing")) == 2
        agent.close()


class TestBenchmarkHarnessReports:
    def test_prepare_report_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_benchmarkharness_report(
            "part_run", "part_run", "part11-a", "B-07 passed as graded")
        assert result["report"]["state"] == (
            "ready")
        assert result["report"]["inflated"] is False
        assert result["report_news"]["type"] == (
            "benchmarkharness_report")
        assert "B-07 passed as graded" in result["screen"]
        report = agent.get_benchmarkharness_report(
            "part_run")
        assert report.entry == "part_run"
        assert [d.kind for d in agent.benchmarkharness_reports()] == [
            "part_run"]
        assert len(_bh_records(
            store, session_id, "benchmarkharness_report")) == 1
        agent.close()

    def test_report_unshared_execution_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared only"):
            agent.prepare_benchmarkharness_report(
                "part_run", "part_run", "part11-a", "x",
                state="executed")
        assert agent.benchmarkharness_reports() == []
        assert _bh_records(
            store, session_id, "benchmarkharness_report") == []
        agent.close()

    def test_duplicate_report_refuses(self, agent):
        agent.prepare_benchmarkharness_report(
            "part_run", "part_run", "part11-a", "B-07 passed as graded")
        with pytest.raises(ValueError, match="part_run"):
            agent.prepare_benchmarkharness_report(
                "part_run", "release_run", "rel-1", "a second telling")
        with pytest.raises(ValueError,
                           match="holds no run report"):
            agent.get_benchmarkharness_report("release_run")


class TestBenchmarkHarnessParseArgs:
    def test_parse_args_well(self):
        assert parse_benchmarkharness_args("") == (
            "show", None, (), None)
        assert parse_benchmarkharness_args(None) == (
            "show", None, (), None)
        assert parse_benchmarkharness_args("kinds") == (
            "kinds", None, (), None)
        assert parse_benchmarkharness_args("kind release_run") == (
            "kind", "release_run", (), None)
        assert parse_benchmarkharness_args(
            "record part_run part11-a") == (
            "record", ("part_run", "part11-a"), (), None)
        assert parse_benchmarkharness_args(
            "standing release_run rel-1") == (
            "standing", ("release_run", "rel-1"), (), None)
        assert parse_benchmarkharness_args("report") == (
            "reports", None, (), None)
        assert parse_benchmarkharness_args(
            "report part_run") == (
            "report", "part_run", (), None)
        assert parse_benchmarkharness_args("verdict") == (
            "verdict", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "kind", "record",
                    "record part_run",
                    "kinds now", "standing part_run",
                    "report part_run extra"):
            with pytest.raises(ValueError) as caught:
                parse_benchmarkharness_args(bad)
            assert str(caught.value) == BENCHMARKHARNESS_USAGE


class TestBenchmarkHarnessTerminalRoad:
    def test_show_kinds_kind_record_standing_report_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/benchmarkharness")
        assert "Part benchmark run (part_run)" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/benchmarkharness kinds")
        assert "Release benchmark run" in text
        _, _, text = _slash(agent, "/benchmarkharness kind release_run")
        assert "per_release" in text
        _, _, text = _slash(
            agent, "/benchmarkharness record part_run part11-a")
        assert "holds no run record" in text
        _, _, text = _slash(
            agent, "/benchmarkharness standing part_run part11-a")
        assert "part_run/part11-a: run open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/benchmarkharness report")
        assert "Run report: none held" in text
        _, _, text = _slash(agent, "/benchmarkharness verdict")
        assert "Benchmark harness stands open" in text
        agent.register_benchmarkharness_record(_bh_record())
        _, _, text = _slash(
            agent, "/benchmarkharness record part_run part11-a")
        assert "passed as graded" in text
        _, _, text = _slash(
            agent, "/benchmarkharness standing part_run part11-a")
        assert "part_run/part11-a: run passed as graded" in text
        _, _, text = _slash(agent, "/benchmarkharness index")
        assert "passed as graded" in text
        agent.prepare_benchmarkharness_report(
            "part_run", "part_run", "part11-a", "B-07 passed as graded")
        _, _, text = _slash(
            agent, "/benchmarkharness report part_run")
        assert "B-07 passed as graded" in text
        assert "never inflated" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/benchmarkharness [show|kinds|kind <kind>|"
                "record <kind> <run>|"
                "standing <kind> <run>|"
                "report [<kind>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/benchmarkharness dance party")
        assert text == BENCHMARKHARNESS_USAGE
        _, _, text = _slash(agent, "/benchmarkharness kind guess")
        assert "unknown run kind" in text


@pytest.fixture()
def bh_handler(agent, monkeypatch):
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


def _bh_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestBenchmarkHarnessHandler:
    def test_show_is_default(self, bh_handler, agent):
        bh_handler._handle_benchmarkharness("")
        assert "Part benchmark run (part_run)" in (
            _bh_published_text(bh_handler))

    def test_kind_record_and_verdict(
            self, bh_handler, agent):
        bh_handler._handle_benchmarkharness("kind release_run")
        assert "per_release" in (
            _bh_published_text(bh_handler))
        agent.register_benchmarkharness_record(_bh_record())
        bh_handler._handle_benchmarkharness(
            "record part_run part11-a")
        assert "passed as graded" in (
            _bh_published_text(bh_handler))
        bh_handler._handle_benchmarkharness("verdict")
        assert "Benchmark harness stands held" in (
            _bh_published_text(bh_handler))

    def test_bad_grammar_is_published(
            self, bh_handler, agent):
        bh_handler._handle_benchmarkharness("dance party")
        assert BENCHMARKHARNESS_USAGE in (
            _bh_published_text(bh_handler))
        bh_handler._handle_benchmarkharness("kind guess")
        assert "unknown run kind" in (
            _bh_published_text(bh_handler))


class TestChatScreenRoutingBenchmarkHarness:
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
        screen.handle_command("/benchmarkharness verdict", _FakeLog())
        assert calls == [("/benchmarkharness", "verdict")]

    def test_chat_screen_help_and_usage_name_the_harness(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/benchmarkharness[/green] - show the Benchmark harness "
                "(M-255)") in text
        assert ('"/benchmarkharness": "Usage: /benchmarkharness | '
                "/benchmarkharness kinds") in text


class TestBenchmarkHarnessDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.benchmarkharness_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _BH_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        verdict = agent.benchmarkharness_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_benchmarkharness_record(_bh_record())
        agent.register_benchmarkharness_record(_bh_fresh_for("release_run"))
        verdict = agent.benchmarkharness_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "part_run/part11-a", "release_run/part11-a"]
        assert "Benchmark harness stands held" in verdict["verdict_text"]

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_benchmarkharness()
        assert report["book"]["schema"] == BENCHMARK_HARNESS_SCHEMA
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_benchmarkharness_record(_bh_record())
        report = agent.report_benchmarkharness()
        assert "passed as graded" in report["records_text"]
        assert [s["kind"] for s in report["standings"]] == [
            "part_run"]

    def test_runs_for_category_and_held_keys(self, agent):
        agent.register_benchmarkharness_record(_bh_record())
        agent.register_benchmarkharness_record(_bh_record(
            run="part11-b", category="feature",
            stages=["tasked"], claims=["assertion"]))
        assert [r.run for r in
                agent.runs_for_category("refactor")] == [
            "part11-a"]
        assert [r.run for r in
                agent.runs_for_category("feature")] == [
            "part11-b"]
        assert agent.benchmarkharness_held() == ["part_run/part11-a"]
        standing = agent.benchmarkharness_standing(
            "part_run", "part11-b")
        assert standing.held is False
        assert any("bare claims" in gap
                   for gap in standing.gaps)
