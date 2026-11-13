"""M-256 Published-yardstick runs - pure-layer tests.

TIER: unit

SWE-bench-style public sets run where licences allow,
results reported with model, cost, and date -
comparable to the field's claims, never inflated: a
set whose licence is not held is listed-only and can
hold no run, and a report missing its model, cost or
date stands open.
"""
import pytest

from mythic_agent.core.published_yardstick import (
    BARE_CLAIMS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    LICENCE_STANDINGS,
    REPORT_STATES,
    STAGES,
    YARDSTICKS,
    RunDraft,
    RunRecord,
    YardstickEntry,
    YardstickRegistry,
    default_registry,
    derive_standing,
    format_record,
    format_records,
    format_yardstick,
    format_yardsticks,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(yardstick="swe_bench", run="2026-11-a",
                model="mythic-coder-7b", cost=12.5,
                date="2026-11-12", score=42.5,
                stages=STAGES,
                claims=("licence_ref", "run_log_ref"))
    base.update(kw)
    return RunRecord(**base)


def test_registry_holds_four_yardsticks_listed_only():
    reg = default_registry()
    assert reg.ids() == ("swe_bench", "swe_bench_lite",
                         "swe_bench_verified",
                         "swe_bench_multimodal")
    assert all(e.standing == "listed" for e in reg.entries())


def test_registry_unknown_yardstick_refused_by_name():
    with pytest.raises(ValidationError, match="unknown yardstick: guess"):
        default_registry().get("guess")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate yardstick"):
        YardstickRegistry(YARDSTICKS + YARDSTICKS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        YardstickRegistry([YardstickEntry(
            "x", "", "run", "MIT", "held", 100, "listed", "why")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        YardstickRegistry([YardstickEntry(
            "x", "X", "run", "MIT", "held", 100, "published", "why")])


def test_licence_standings_held_and_listed_only():
    reg = default_registry()
    assert reg.get("swe_bench").licence == "MIT"
    assert reg.get("swe_bench").licence_standing == "held"
    assert reg.get("swe_bench_lite").licence_standing == "held"
    assert reg.get("swe_bench_verified").licence_standing == "held"
    multi = reg.get("swe_bench_multimodal")
    assert multi.licence_standing == "listed_only"
    assert LICENCE_STANDINGS == ("held", "listed_only")
    assert all(e.max_score == 100 for e in reg.entries())


def test_fresh_record_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held is True
    assert standing.grade == "held"
    assert standing.stage == "held"
    assert standing.gaps == ()


def test_walk_skip_gap_named():
    standing = derive_standing(
        fresh_record(stages=("named", "run", "reported", "held")))
    assert standing.held is False
    assert any("named -> run" in g for g in standing.gaps)


def test_unheld_stage_stands_open():
    standing = derive_standing(
        fresh_record(stages=("named", "licensed", "run")))
    assert standing.held is False
    assert any("not held" in g for g in standing.gaps)


def test_listed_only_yardstick_never_held():
    standing = derive_standing(
        fresh_record(yardstick="swe_bench_multimodal"))
    assert standing.held is False
    assert any("listed-only" in g for g in standing.gaps)


def test_licence_without_licence_evidence_gap_named():
    standing = derive_standing(
        fresh_record(claims=("run_log_ref", "report_ref")))
    assert standing.held is False
    assert any("licence rests on no held licence evidence" in g
               for g in standing.gaps)


def test_bare_claims_only_stands_open():
    standing = derive_standing(
        fresh_record(claims=("feeling", "summary")))
    assert standing.held is False
    assert any("no held evidence" in g for g in standing.gaps)
    assert any("bare claims only" in g for g in standing.gaps)


def test_report_missing_model_stands_open():
    standing = derive_standing(fresh_record(model=""))
    assert standing.held is False
    assert any("names no model" in g for g in standing.gaps)


def test_report_missing_cost_stands_open():
    standing = derive_standing(fresh_record(cost=None))
    assert standing.held is False
    assert any("names no cost" in g for g in standing.gaps)


def test_report_missing_date_stands_open():
    standing = derive_standing(fresh_record(date=""))
    assert standing.held is False
    assert any("names no run date" in g for g in standing.gaps)


def test_missing_score_stands_open():
    standing = derive_standing(fresh_record(score=None))
    assert standing.held is False
    assert any("reports no score" in g for g in standing.gaps)


def test_bad_dates_refused():
    for bad in ("2026-13-40", "12 Nov 2026", "2026/11/12"):
        with pytest.raises(ValidationError, match="unknown run date"):
            derive_standing(fresh_record(date=bad))


def test_bad_costs_refused():
    with pytest.raises(ValidationError, match="cost is negative"):
        derive_standing(fresh_record(cost=-1.0))
    with pytest.raises(ValidationError, match="unknown run cost"):
        derive_standing(fresh_record(cost="free"))


def test_score_bounds_refused():
    with pytest.raises(ValidationError, match="never inflated"):
        derive_standing(fresh_record(score=100.5))
    with pytest.raises(ValidationError, match="score is negative"):
        derive_standing(fresh_record(score=-1.0))


def test_unknown_evidence_kind_refused():
    with pytest.raises(ValidationError, match="unknown run evidence kind"):
        derive_standing(fresh_record(claims=("hunch",)))


def test_unknown_model_type_refused():
    with pytest.raises(ValidationError, match="unknown run model"):
        derive_standing(fresh_record(model=42))


def test_evidence_kinds_partition():
    assert set(HELD_EVIDENCE) | set(BARE_CLAIMS) == set(EVIDENCE_KINDS)
    assert "licence_ref" in HELD_EVIDENCE
    assert "licence_ref" not in BARE_CLAIMS


def test_report_ready_and_shared():
    draft = prepare_report(
        "swe_bench", "swe_bench", "2026-11-a",
        "42.5 resolved, reported as run",
        "mythic-coder-7b", 12.5, "2026-11-12", 42.5,
        claims=("licence_ref", "report_ref"))
    assert draft.state == "ready"
    shared = prepare_report(
        "swe_bench", "swe_bench", "2026-11-a",
        "42.5 resolved, reported as run",
        "mythic-coder-7b", 12.5, "2026-11-12", 42.5,
        claims=("licence_ref", "report_ref"), state="shared")
    assert shared.state == "shared"
    assert REPORT_STATES == ("ready", "shared")


def test_report_sealed_state_and_inflated_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report(
            "swe_bench", "swe_bench", "2026-11-a", "x",
            "mythic-coder-7b", 12.5, "2026-11-12", 42.5,
            claims=("licence_ref",), state="sealed")
    draft = RunDraft(
        "swe_bench", "swe_bench", "2026-11-a",
        "beat the whole field", "mythic-coder-7b", 12.5,
        "2026-11-12", 42.5, ("licence_ref",), inflated=True)
    with pytest.raises(ValidationError, match="never inflated"):
        draft.validate()


def test_report_refusals_and_formats():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report(
            "swe_bench", "swe_bench", "2026-11-a",
            "we feel it did well", "mythic-coder-7b", 12.5,
            "2026-11-12", 42.5, claims=("feeling",))
    with pytest.raises(ValidationError, match="never inflated"):
        prepare_report(
            "swe_bench", "swe_bench", "2026-11-a", "x",
            "mythic-coder-7b", 12.5, "2026-11-12", 140.0,
            claims=("licence_ref",))
    with pytest.raises(ValidationError, match="names no model"):
        prepare_report(
            "swe_bench", "swe_bench", "2026-11-a", "x",
            "", 12.5, "2026-11-12", 42.5,
            claims=("licence_ref",))
    with pytest.raises(ValidationError, match="cost is negative"):
        prepare_report(
            "swe_bench", "swe_bench", "2026-11-a", "x",
            "mythic-coder-7b", -2.0, "2026-11-12", 42.5,
            claims=("licence_ref",))
    text = format_record(fresh_record())
    assert "swe_bench/2026-11-a" in text
    assert "score 42.5 of 100" in text
    assert "held as reported" in text
    open_text = format_record(fresh_record(model=""))
    assert "open:" in open_text
    assert "SWE-bench Verified" in format_yardsticks()
    joined = format_records([fresh_record(),
                             fresh_record(run="2026-11-b")])
    assert joined.count("\n") == 1
    assert "listed_only" in format_yardstick(
        default_registry().get("swe_bench_multimodal"))


# ---------------------------------------------------------------------
# M-256 agent layer: the agent holds the shipped yardstick
# registry and one run record per yardstick and run for
# the session, records, viewed standings and held
# reports are published as session news through the
# checkpoint road (journal-first, deduped per record,
# standing and report), standings, the index and the
# verdict are derived at call time from the held records -
# a run stands held only when its licence rests on held
# evidence and its report carries model, cost and date
# together - run reports are held only as reports, state
# ready by default, may be marked shared by a human,
# and never inflated, and the registry is session
# state, never a stored setting. This layer runs no
# benchmark, downloads no set, executes no grading test
# and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    PUBLISHEDYARDSTICK_USAGE,
    parse_publishedyardstick_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.published_yardstick import (
    PLAIN_EXPLANATION,
    PUBLISHED_YARDSTICK_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_PY_EVENT_TYPES = (
    "publishedyardstick_record", "publishedyardstick_standing", "publishedyardstick_report")

ALL_YARDSTICKS = ["swe_bench", "swe_bench_lite",
                  "swe_bench_verified", "swe_bench_multimodal"]


def _py_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _py_record(**overrides):
    raw = {
        "yardstick": "swe_bench",
        "run": "2026-11-a",
        "model": "mythic-coder-7b",
        "cost": 12.5,
        "date": "2026-11-12",
        "score": 42.5,
        "stages": list(STAGES),
        "claims": ["licence_ref", "run_log_ref"],
    }
    raw.update(overrides)
    return raw


def _py_fresh_for(yardstick, run="2026-11-a"):
    return _py_record(yardstick=yardstick, run=run)


class TestPublishedYardstickAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_yardsticks(
            self, agent):
        status = agent.publishedyardstick_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["publishedyardstick_book"]["schema"] == (
            PUBLISHED_YARDSTICK_SCHEMA)
        assert [p["id"] for p in status[
            "publishedyardstick_book"]["yardsticks"]] == ALL_YARDSTICKS
        assert status["publishedyardstick_book"]["records"] == []
        assert status["publishedyardstick_book"]["reports"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "SWE-bench" in status["yardsticks_text"]
        assert "standing listed" in status["yardsticks_text"]
        assert "none recorded this session" in status["screen"]
        assert "Published yardsticks" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == PUBLISHEDYARDSTICK_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._publishedyardstick_registry()
        assert agent._publishedyardstick_registry() is first
        assert agent._publishedyardstick_store is first
        for name in ("publishedyardstick_yardsticks",
                     "publishedyardstick_book",
                     "publishedyardstick_status",
                     "get_publishedyardstick_yardstick",
                     "get_publishedyardstick_record",
                     "publishedyardstick_standing",
                     "runs_for_model",
                     "publishedyardstick_held",
                     "publishedyardstick_index",
                     "publishedyardstick_verdict",
                     "prepare_publishedyardstick_report",
                     "get_publishedyardstick_report",
                     "publishedyardstick_reports",
                     "report_publishedyardstick"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_publishedyardstick_registry", "publishedyardstick_yardsticks",
            "publishedyardstick_book", "publishedyardstick_status",
            "get_publishedyardstick_yardstick",
            "get_publishedyardstick_record",
            "publishedyardstick_standing", "runs_for_model",
            "publishedyardstick_held", "publishedyardstick_index",
            "publishedyardstick_verdict",
            "register_publishedyardstick_record",
            "register_publishedyardstick_records",
            "record_publishedyardstick_records",
            "view_publishedyardstick", "prepare_publishedyardstick_report",
            "report_publishedyardstick",
            "_publish_publishedyardstick_record",
            "_publishedyardstick_screen",
            "_publishedyardstick_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.publishedyardstick_status()
        entry = agent.get_publishedyardstick_yardstick("swe_bench_verified")
        assert entry.item_word == "run"
        standing = agent.publishedyardstick_standing(
            "swe_bench", "2026-11-a")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.grade == "open"
        assert agent.publishedyardstick_held() == []
        assert agent.runs_for_model("mythic-coder-7b") == []
        agent.publishedyardstick_index()
        agent.publishedyardstick_verdict()
        agent.report_publishedyardstick()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _PY_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown yardstick"):
            agent.get_publishedyardstick_yardstick("guess")
        with pytest.raises(ValueError, match="unknown yardstick"):
            agent.publishedyardstick_standing("guess", "2026-11-a")
        with pytest.raises(ValueError, match="holds no run record"):
            agent.get_publishedyardstick_record("swe_bench", "2026-11-a")
        with pytest.raises(ValueError):
            agent.runs_for_model("")
        agent.close()


class TestPublishedYardstickAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_publishedyardstick_record(_py_record())
        assert result["record"]["yardstick"] == "swe_bench"
        assert result["record"]["run"] == "2026-11-a"
        assert result["record_news"]["type"] == (
            "publishedyardstick_record")
        assert "held as reported" in result["screen"]
        status = agent.publishedyardstick_status()
        assert [r["yardstick"] for r in status["records"]] == [
            "swe_bench"]
        assert status["book"]["records"][0]["run"] == (
            "2026-11-a")
        assert status["held"] == ["swe_bench/2026-11-a"]
        assert status["open"] == []
        assert "held as reported" in status["records_text"]
        assert len(_py_records(
            store, session_id, "publishedyardstick_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_publishedyardstick_record(_py_record())
        with pytest.raises(ValueError, match="swe_bench"):
            agent.register_publishedyardstick_record(
                _py_record(model="another-model"))
        assert len(_py_records(
            store, session_id, "publishedyardstick_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_publishedyardstick_record(
                _py_record(claims=["vibes"]))
        assert agent.publishedyardstick_status()["records"] == []
        assert _py_records(
            store, session_id, "publishedyardstick_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_publishedyardstick_records([
            _py_fresh_for("swe_bench_verified"), _py_record()])
        assert result["count"] == 2
        assert [r["yardstick"] for r in result["records_news"]] == [
            "swe_bench_verified", "swe_bench"]
        assert len(_py_records(
            store, session_id, "publishedyardstick_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_publishedyardstick_records(
            [_py_fresh_for("swe_bench_verified")])
        assert result["count"] == 1
        assert result["book"]["schema"] == PUBLISHED_YARDSTICK_SCHEMA
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_publishedyardstick_records(
                [_py_fresh_for("swe_bench_verified")])
        assert len(_py_records(
            store, session_id, "publishedyardstick_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_publishedyardstick_record(_py_record())
        result = agent.view_publishedyardstick("swe_bench", "2026-11-a")
        assert result["yardstick"]["id"] == "swe_bench"
        assert result["standing"]["held"] is True
        assert result["record"]["run"] == "2026-11-a"
        assert result["record_news"]["type"] == (
            "publishedyardstick_standing")
        assert result["held_record_news"]["type"] == (
            "publishedyardstick_record")
        assert len(_py_records(
            store, session_id, "publishedyardstick_record")) == 1
        assert len(_py_records(
            store, session_id, "publishedyardstick_standing")) == 1
        result = agent.view_publishedyardstick("swe_bench_lite", "2026-11-a")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_py_records(
            store, session_id, "publishedyardstick_standing")) == 2
        agent.close()


class TestPublishedYardstickReports:
    def test_prepare_report_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_publishedyardstick_report(
            "swe_bench", "swe_bench", "2026-11-a",
            "42.5 resolved, reported as run", "mythic-coder-7b",
            12.5, "2026-11-12", 42.5,
            claims=("licence_ref", "report_ref"))
        assert result["report"]["state"] == (
            "ready")
        assert result["report"]["inflated"] is False
        assert result["report_news"]["type"] == (
            "publishedyardstick_report")
        assert "42.5 resolved, reported as run" in result["screen"]
        report = agent.get_publishedyardstick_report(
            "swe_bench")
        assert report.entry == "swe_bench"
        assert [d.yardstick for d in agent.publishedyardstick_reports()] == [
            "swe_bench"]
        assert len(_py_records(
            store, session_id, "publishedyardstick_report")) == 1
        agent.close()

    def test_report_unshared_execution_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared only"):
            agent.prepare_publishedyardstick_report(
                "swe_bench", "swe_bench", "2026-11-a", "x",
                "mythic-coder-7b", 12.5, "2026-11-12", 42.5,
                claims=("licence_ref",), state="executed")
        assert agent.publishedyardstick_reports() == []
        assert _py_records(
            store, session_id, "publishedyardstick_report") == []
        agent.close()

    def test_duplicate_report_refuses(self, agent):
        agent.prepare_publishedyardstick_report(
            "swe_bench", "swe_bench", "2026-11-a",
            "42.5 resolved, reported as run", "mythic-coder-7b",
            12.5, "2026-11-12", 42.5, claims=("licence_ref",))
        with pytest.raises(ValueError, match="swe_bench"):
            agent.prepare_publishedyardstick_report(
                "swe_bench", "swe_bench_lite", "2026-11-b",
                "a second telling", "mythic-coder-7b",
                9.0, "2026-11-12", 30.0, claims=("licence_ref",))
        with pytest.raises(ValueError,
                           match="holds no run report"):
            agent.get_publishedyardstick_report("swe_bench_lite")


class TestPublishedYardstickParseArgs:
    def test_parse_args_well(self):
        assert parse_publishedyardstick_args("") == (
            "show", None, (), None)
        assert parse_publishedyardstick_args(None) == (
            "show", None, (), None)
        assert parse_publishedyardstick_args("yardsticks") == (
            "yardsticks", None, (), None)
        assert parse_publishedyardstick_args("yardstick swe_bench_lite") == (
            "yardstick", "swe_bench_lite", (), None)
        assert parse_publishedyardstick_args(
            "record swe_bench 2026-11-a") == (
            "record", ("swe_bench", "2026-11-a"), (), None)
        assert parse_publishedyardstick_args(
            "standing swe_bench_verified v-1") == (
            "standing", ("swe_bench_verified", "v-1"), (), None)
        assert parse_publishedyardstick_args("report") == (
            "reports", None, (), None)
        assert parse_publishedyardstick_args(
            "report swe_bench") == (
            "report", "swe_bench", (), None)
        assert parse_publishedyardstick_args("verdict") == (
            "verdict", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "yardstick", "record",
                    "record swe_bench",
                    "yardsticks now", "standing swe_bench",
                    "report swe_bench extra"):
            with pytest.raises(ValueError) as caught:
                parse_publishedyardstick_args(bad)
            assert str(caught.value) == PUBLISHEDYARDSTICK_USAGE


class TestPublishedYardstickTerminalRoad:
    def test_show_yardsticks_yardstick_record_standing_report_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/publishedyardstick")
        assert "SWE-bench (swe_bench)" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/publishedyardstick yardsticks")
        assert "SWE-bench Verified" in text
        _, _, text = _slash(agent, "/publishedyardstick yardstick swe_bench_lite")
        assert "licence MIT (held)" in text
        _, _, text = _slash(
            agent, "/publishedyardstick record swe_bench 2026-11-a")
        assert "holds no run record" in text
        _, _, text = _slash(
            agent, "/publishedyardstick standing swe_bench 2026-11-a")
        assert "swe_bench/2026-11-a: run open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/publishedyardstick report")
        assert "Run report: none held" in text
        _, _, text = _slash(agent, "/publishedyardstick verdict")
        assert "Published yardsticks stand open" in text
        agent.register_publishedyardstick_record(_py_record())
        _, _, text = _slash(
            agent, "/publishedyardstick record swe_bench 2026-11-a")
        assert "held as reported" in text
        _, _, text = _slash(
            agent, "/publishedyardstick standing swe_bench 2026-11-a")
        assert "swe_bench/2026-11-a: run held as reported" in text
        _, _, text = _slash(agent, "/publishedyardstick index")
        assert "held as reported" in text
        agent.prepare_publishedyardstick_report(
            "swe_bench", "swe_bench", "2026-11-a",
            "42.5 resolved, reported as run", "mythic-coder-7b",
            12.5, "2026-11-12", 42.5, claims=("licence_ref",))
        _, _, text = _slash(
            agent, "/publishedyardstick report swe_bench")
        assert "42.5 resolved, reported as run" in text
        assert "never inflated" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/publishedyardstick [show|yardsticks|yardstick <yardstick>|"
                "record <yardstick> <run>|"
                "standing <yardstick> <run>|"
                "report [<yardstick>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/publishedyardstick dance party")
        assert text == PUBLISHEDYARDSTICK_USAGE
        _, _, text = _slash(agent, "/publishedyardstick yardstick guess")
        assert "unknown yardstick" in text


@pytest.fixture()
def py_handler(agent, monkeypatch):
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


def _py_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestPublishedYardstickHandler:
    def test_show_is_default(self, py_handler, agent):
        py_handler._handle_publishedyardstick("")
        assert "SWE-bench (swe_bench)" in (
            _py_published_text(py_handler))

    def test_yardstick_record_and_verdict(
            self, py_handler, agent):
        py_handler._handle_publishedyardstick("yardstick swe_bench_lite")
        assert "licence MIT" in (
            _py_published_text(py_handler))
        agent.register_publishedyardstick_record(_py_record())
        py_handler._handle_publishedyardstick(
            "record swe_bench 2026-11-a")
        assert "held as reported" in (
            _py_published_text(py_handler))
        py_handler._handle_publishedyardstick("verdict")
        assert "Published yardsticks stand held" in (
            _py_published_text(py_handler))

    def test_bad_grammar_is_published(
            self, py_handler, agent):
        py_handler._handle_publishedyardstick("dance party")
        assert PUBLISHEDYARDSTICK_USAGE in (
            _py_published_text(py_handler))
        py_handler._handle_publishedyardstick("yardstick guess")
        assert "unknown yardstick" in (
            _py_published_text(py_handler))


class TestChatScreenRoutingPublishedYardstick:
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
        screen.handle_command("/publishedyardstick verdict", _FakeLog())
        assert calls == [("/publishedyardstick", "verdict")]

    def test_chat_screen_help_and_usage_name_the_yardsticks(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/publishedyardstick[/green] - show the Published yardsticks "
                "(M-256)") in text
        assert ('"/publishedyardstick": "Usage: /publishedyardstick | '
                "/publishedyardstick yardsticks") in text


class TestPublishedYardstickDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.publishedyardstick_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _PY_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        verdict = agent.publishedyardstick_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_publishedyardstick_record(_py_record())
        agent.register_publishedyardstick_record(_py_fresh_for("swe_bench_verified"))
        verdict = agent.publishedyardstick_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "swe_bench/2026-11-a", "swe_bench_verified/2026-11-a"]
        assert "Published yardsticks stand held" in verdict["verdict_text"]

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_publishedyardstick()
        assert report["book"]["schema"] == PUBLISHED_YARDSTICK_SCHEMA
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_publishedyardstick_record(_py_record())
        report = agent.report_publishedyardstick()
        assert "held as reported" in report["records_text"]
        assert [s["yardstick"] for s in report["standings"]] == [
            "swe_bench"]

    def test_runs_for_model_and_held_keys(self, agent):
        agent.register_publishedyardstick_record(_py_record())
        agent.register_publishedyardstick_record(_py_record(
            run="2026-11-b", model="other-model",
            stages=["named"], claims=["assertion"]))
        assert [r.run for r in
                agent.runs_for_model("mythic-coder-7b")] == [
            "2026-11-a"]
        assert [r.run for r in
                agent.runs_for_model("other-model")] == [
            "2026-11-b"]
        assert agent.publishedyardstick_held() == ["swe_bench/2026-11-a"]
        standing = agent.publishedyardstick_standing(
            "swe_bench", "2026-11-b")
        assert standing.held is False
        assert any("bare claims" in gap
                   for gap in standing.gaps)
