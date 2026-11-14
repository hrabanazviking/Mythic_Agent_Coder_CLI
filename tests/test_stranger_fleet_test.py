"""M-266 Stranger fleet test - pure-layer tests.

TIER: unit

M-200's stranger + a headless CI run + a crew campaign,
all from docs alone, on a clean machine: an exercise
counts PROVEN only on a docs-only clean-machine run
resting on held evidence, and a roaded exercise with
no owner named stands open.
"""
import pytest

from mythic_agent.core.stranger_fleet_test import (
    EXERCISES,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    StrangerFleetEntry,
    StrangerFleetRegistry,
    StrangerFleetRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_exercise,
    format_exercises,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(exercise="F-02",
                work="fleet-2026-11-a",
                date="2026-11-13", disposition="PROVEN",
                owner="yrsa",
                proof_kind="docs-only-clean-machine",
                stages=STAGES,
                claims=("run_ref", "report_ref"))
    base.update(kw)
    return StrangerFleetRecord(**base)


def roaded_record(**kw):
    base = dict(exercise="F-03",
                work="fleet-2026-11-a",
                date="2026-11-13", disposition="ROADED",
                owner="yrsa",
                proof_kind="docs-only-clean-machine",
                stages=STAGES,
                claims=("report_ref",))
    base.update(kw)
    return StrangerFleetRecord(**base)


def full_book(**overrides):
    records = []
    for exercise_id in default_registry().combinations():
        if exercise_id in ("F-01",):
            kw = dict(exercise=exercise_id, work="fleet-2026-11-a",
                      date="2026-11-13", disposition="PROVEN",
                      owner="yrsa",
                      proof_kind="docs-only-clean-machine",
                      stages=STAGES,
                      claims=("run_ref", "report_ref"))
        else:
            kw = dict(exercise=exercise_id, work="fleet-2026-11-a",
                      date="2026-11-13", disposition="ROADED",
                      owner="yrsa",
                      proof_kind="docs-only-clean-machine",
                      stages=STAGES,
                      claims=("report_ref",))
        kw.update(overrides.get(exercise_id, {}))
        records.append(StrangerFleetRecord(**kw))
    return records


def test_registry_holds_three_exercises_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 3
    assert reg.ids()[0] == "F-01"
    assert reg.ids()[-1] == "F-03"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 3


def test_registry_exercises_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 3
    assert reg.get("F-01").doctrine == "stranger-duty"
    assert reg.get("F-01").subject == "stranger-task"
    assert reg.get("F-02").subject == "headless-ci-run"
    assert reg.get("F-03").subject == "crew-campaign"
    assert reg.get("F-02").doctrine == "ci-duty"
    assert reg.get("F-03").doctrine == "crew-duty"
    assert all(e.docs_only and e.clean_machine for e in reg.entries())
    assert DISPOSITIONS == ("PROVEN", "ROADED")


def test_registry_unknown_exercise_refused_by_name():
    with pytest.raises(ValidationError, match="unknown exercise: F-99"):
        default_registry().get("F-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate exercise"):
        StrangerFleetRegistry(EXERCISES + EXERCISES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        StrangerFleetRegistry([StrangerFleetEntry("F-01", "stranger-duty", "stranger-task", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        StrangerFleetRegistry([StrangerFleetEntry("F-01", "stranger-duty", "stranger-task", "published", "why")])
    with pytest.raises(ValidationError, match="docs-only"):
        StrangerFleetRegistry([StrangerFleetEntry("F-01", "stranger-duty", "stranger-task", "listed", "why", docs_only=False)])
    with pytest.raises(ValidationError, match="clean-machine"):
        StrangerFleetRegistry([StrangerFleetEntry("F-01", "stranger-duty", "stranger-task", "listed", "why", clean_machine=False)])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown exercise doctrine"):
        StrangerFleetRegistry([StrangerFleetEntry("F-01", "M-999", "session-store", "listed", "why")])


def test_record_proven_in_new_release_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held
    assert standing.grade == "held"
    assert standing.gaps == ()


def test_record_incomplete_walk_stands_open():
    standing = derive_standing(fresh_record(stages=STAGES[:3]))
    assert not standing.held
    assert any("not held" in g for g in standing.gaps)


def test_record_bad_stage_step_stands_open():
    bad = ("named", "checked", "dispositioned", "held")
    standing = derive_standing(fresh_record(stages=bad))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_record_proven_on_secondhand_evidence_stands_open():
    standing = derive_standing(fresh_record(proof_kind="secondhand-only"))
    assert not standing.held
    assert any("no secondhand proof" in g for g in standing.gaps)


def test_record_proven_without_run_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("report_ref",)))
    assert not standing.held
    assert any("no held run evidence" in g for g in standing.gaps)


def test_record_proven_on_bare_claims_stands_open():
    standing = derive_standing(fresh_record(claims=("feeling",)))
    assert not standing.held
    assert any("bare claims only" in g for g in standing.gaps)


def test_record_roaded_with_owner_stands_held():
    standing = derive_standing(roaded_record())
    assert standing.held
    assert standing.grade == "held"


def test_record_roaded_without_owner_stands_open():
    standing = derive_standing(roaded_record(owner=""))
    assert not standing.held
    assert any("not a road" in g for g in standing.gaps)


def test_record_roaded_silent_stands_open():
    standing = derive_standing(roaded_record(claims=()))
    assert not standing.held
    assert any("silent" in g for g in standing.gaps)


def test_record_without_date_stands_open():
    standing = derive_standing(fresh_record(date=""))
    assert not standing.held
    assert any("no fleet date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_ready_with_roaded_exercises():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.proven_exercises == ("F-01",)
    assert len(verdict.roaded_exercises) == 2
    assert verdict.missing_exercises == ()


def test_verdict_missing_exercise_stops_the_fleet():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_exercises == ("F-03",)
    assert any("F-03" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_fleet():
    verdict = derive_verdict(full_book(**{"F-01": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("F-01 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_exercise_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("fleet-a", "F-01", "findings as dispositioned",
                            "2026-11-13", 1, 2, 3,
                            claims=("run_ref",))
    assert report.state == "ready"
    shared = prepare_report("fleet-a", "F-01", "findings as dispositioned",
                            "2026-11-13", 1, 2, 3,
                            claims=("run_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("fleet-a", "F-01", "findings", "2026-11-13",
                       1, 2, 3, claims=("run_ref",), state="sealed")
    with pytest.raises(ValidationError, match="fleet test complete"):
        prepare_report("fleet-a", "F-01", "findings", "2026-11-13",
                       1, 1, 3, claims=("run_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("fleet-a", "F-01", "findings", "2026-11-13",
                       1, 2, 3, claims=("feeling",))
    assert "F-01" in format_exercise(default_registry().get("F-01"))
    assert "F-03" in format_exercises()
    assert "PROVEN" in format_record(fresh_record())
    assert "ROADED" in format_records([roaded_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
    from pathlib import Path as _P
    _src = (_P(__file__).resolve().parent.parent
            / "mythic_agent" / "core" / "stranger_fleet_test.py").read_text(
                encoding="utf-8")
    assert "open(" not in _src
    assert "socket" not in _src
    assert "subprocess" not in _src
    assert "urllib" not in _src

# ---------------------------------------------------------------------


# ---------------------------------------------------------------------
# M-266 Stranger fleet test - agent layer. The pure book is held
# by a session registry in the agent layer alone: exercises are read
# from the shipped registry, capture records are held one by one for
# the session, records, viewed standings and held reports are
# published as session news through the checkpoint road
# (journal-first, deduped per record, standing and verdict),
# standings, the index and the verdict are derived at call time from
# the held records - an exercise stands held only when its finding
# counts PROVEN on docs-only-clean-machine evidence resting on held local
# evidence, or stands ROADED with a named owner in the open -
# audit reports are held only as reports, state ready by default,
# may be marked shared by a human, a certification claimed only
# when every exercise stands answered, and never inflated, and the
# registry is session state, never a stored setting. This layer
# runs no attack, reads no sandbox code and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    STRANGERFLEETTEST_USAGE,
    parse_strangerfleettest_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.stranger_fleet_test import (
    PLAIN_EXPLANATION,
    STRANGER_FLEET_TEST_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_SF_EVENT_TYPES = (
    "strangerfleettest_record", "strangerfleettest_standing",
    "strangerfleettest_verdict")

ALL_EXERCISES = ["F-01", "F-02", "F-03"]


def _sf_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _sf_record(**overrides):
    raw = {
        "exercise": "F-01",
        "work": "fleet-2026-11-a",
        "date": "2026-11-13",
        "disposition": "PROVEN",
        "owner": "yrsa",
        "proof_kind": "docs-only-clean-machine",
        "stages": list(STAGES),
        "claims": ["run_ref", "report_ref"],
    }
    raw.update(overrides)
    return raw


def _sf_fresh_for(exercise, work="fleet-2026-11-a"):
    return _sf_record(exercise=exercise, work=work)


class TestStrangerFleetAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_exercises(
            self, agent):
        status = agent.strangerfleettest_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["strangerfleettest_book"]["schema"] == (
            STRANGER_FLEET_TEST_SCHEMA)
        assert [c["id"] for c in status[
            "strangerfleettest_book"]["exercises"]] == ALL_EXERCISES
        assert status["strangerfleettest_book"]["records"] == []
        assert status["strangerfleettest_book"]["reports"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "F-01" in status["exercises_text"]
        assert "standing listed" in status["exercises_text"]
        assert "none recorded this session" in status["screen"]
        assert "stranger fleet test" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == STRANGERFLEETTEST_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._strangerfleettest_registry()
        assert agent._strangerfleettest_registry() is first
        assert agent._strangerfleettest_store is first
        for name in ("strangerfleettest_exercises",
                     "strangerfleettest_book",
                     "strangerfleettest_status",
                     "get_strangerfleettest_exercise",
                     "get_strangerfleettest_record",
                     "strangerfleettest_standing",
                     "exercises_for_disposition",
                     "strangerfleettest_held",
                     "strangerfleettest_index",
                     "strangerfleettest_verdict",
                     "prepare_strangerfleettest_report",
                     "get_strangerfleettest_report",
                     "strangerfleettest_reports",
                     "report_strangerfleettest"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_strangerfleettest_registry",
            "strangerfleettest_exercises",
            "strangerfleettest_book",
            "strangerfleettest_status",
            "get_strangerfleettest_exercise",
            "get_strangerfleettest_record",
            "strangerfleettest_standing", "exercises_for_disposition",
            "strangerfleettest_held", "strangerfleettest_index",
            "strangerfleettest_verdict",
            "register_strangerfleettest_record",
            "register_strangerfleettest_records",
            "record_strangerfleettest_records",
            "view_strangerfleettest",
            "prepare_strangerfleettest_report",
            "get_strangerfleettest_report",
            "strangerfleettest_reports",
            "report_strangerfleettest",
            "_publish_strangerfleettest_record",
            "_strangerfleettest_screen",
            "_strangerfleettest_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.strangerfleettest_status()
        entry = agent.get_strangerfleettest_exercise("F-01")
        assert entry.doctrine == "stranger-duty"
        assert entry.subject == "stranger-task"
        standing = agent.strangerfleettest_standing("F-01")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.grade == "open"
        assert agent.strangerfleettest_held() == []
        assert agent.exercises_for_disposition("PROVEN") == []
        agent.strangerfleettest_index()
        agent.strangerfleettest_verdict()
        agent.report_strangerfleettest()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _SF_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown exercise"):
            agent.get_strangerfleettest_exercise("guess")
        with pytest.raises(ValueError, match="unknown exercise"):
            agent.strangerfleettest_standing("guess")
        with pytest.raises(ValueError, match="holds no"):
            agent.get_strangerfleettest_record("F-01")
        with pytest.raises(ValueError):
            agent.exercises_for_disposition("")
        agent.close()


class TestStrangerFleetAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_strangerfleettest_record(
            _sf_record())
        assert result["record"]["exercise"] == "F-01"
        assert result["record_news"]["type"] == (
            "strangerfleettest_record")
        assert "held as answered" in result["screen"]
        status = agent.strangerfleettest_status()
        assert [r["exercise"] for r in status["records"]] == [
            "F-01"]
        assert status["book"]["records"][0]["work"] == (
            "fleet-2026-11-a")
        assert status["held"] == ["F-01"]
        assert status["open"] == []
        assert "held as answered" in status["records_text"]
        assert len(_sf_records(
            store, session_id, "strangerfleettest_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_strangerfleettest_record(_sf_record())
        with pytest.raises(ValueError, match="F-01"):
            agent.register_strangerfleettest_record(
                _sf_record(work="fleet-2026-11-b"))
        assert len(_sf_records(
            store, session_id, "strangerfleettest_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_strangerfleettest_record(
                _sf_record(claims=["vibes"]))
        assert agent.strangerfleettest_status()["records"] == []
        assert _sf_records(
            store, session_id, "strangerfleettest_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_strangerfleettest_records([
            _sf_fresh_for("F-02"), _sf_record()])
        assert result["count"] == 2
        assert [r["exercise"] for r in result["records_news"]] == [
            "F-02", "F-01"]
        assert len(_sf_records(
            store, session_id, "strangerfleettest_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_strangerfleettest_records(
            [_sf_fresh_for("F-02")])
        assert result["count"] == 1
        assert result["book"]["schema"] == (
            STRANGER_FLEET_TEST_SCHEMA)
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_strangerfleettest_records(
                [_sf_fresh_for("F-02")])
        assert len(_sf_records(
            store, session_id, "strangerfleettest_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_strangerfleettest_record(_sf_record())
        result = agent.view_strangerfleettest("F-01")
        assert result["exercise"]["id"] == "F-01"
        assert result["standing"]["held"] is True
        assert result["record"]["work"] == "fleet-2026-11-a"
        assert result["record_news"]["type"] == (
            "strangerfleettest_standing")
        assert result["held_record_news"]["type"] == (
            "strangerfleettest_record")
        assert len(_sf_records(
            store, session_id, "strangerfleettest_record")) == 1
        assert len(_sf_records(
            store, session_id, "strangerfleettest_standing")) == 1
        result = agent.view_strangerfleettest("F-03")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_sf_records(
            store, session_id, "strangerfleettest_standing")) == 2
        agent.close()


class TestStrangerFleetReports:
    def test_prepare_report_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_strangerfleettest_report(
            "fleet-2026-11", "release-1",
            "every exercise answered",
            "2026-11-13", 1, 2, 3,
            claims=("run_ref", "report_ref"))
        assert result["report"]["state"] == "ready"
        assert result["report"]["certified"] is False
        assert result["report"]["inflated"] is False
        assert result["report_news"]["type"] == (
            "strangerfleettest_verdict")
        assert "every exercise answered" in result["screen"]
        report = agent.get_strangerfleettest_report(
            "fleet-2026-11")
        assert report.entry == "release-1"
        assert [r.book for r in
                agent.strangerfleettest_reports()] == [
            "fleet-2026-11"]
        assert len(_sf_records(
            store, session_id, "strangerfleettest_verdict")) == 1
        agent.close()

    def test_report_unshared_state_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared"):
            agent.prepare_strangerfleettest_report(
                "fleet-2026-11", "release-1", "x",
                "2026-11-13", 1, 2, 3,
                claims=("run_ref",), state="executed")
        assert agent.strangerfleettest_reports() == []
        assert _sf_records(
            store, session_id, "strangerfleettest_verdict") == []
        agent.close()

    def test_duplicate_report_refuses(self, agent):
        agent.prepare_strangerfleettest_report(
            "fleet-2026-11", "release-1",
            "every exercise answered", "2026-11-13", 1, 2, 3,
            claims=("run_ref",))
        with pytest.raises(ValueError, match="fleet-2026-11"):
            agent.prepare_strangerfleettest_report(
                "fleet-2026-11", "release-2",
                "a second telling", "2026-11-13", 1, 2, 3,
                claims=("run_ref",))
        with pytest.raises(ValueError,
                           match="holds no"):
            agent.get_strangerfleettest_report("fleet-2026-12")


class TestStrangerFleetParseArgs:
    def test_parse_args_well(self):
        assert parse_strangerfleettest_args("") == (
            "show", None, (), None)
        assert parse_strangerfleettest_args(None) == (
            "show", None, (), None)
        assert parse_strangerfleettest_args("exercises") == (
            "exercises", None, (), None)
        assert parse_strangerfleettest_args(
            "exercise F-01") == (
            "exercise", "F-01", (), None)
        assert parse_strangerfleettest_args(
            "record F-01") == (
            "record", "F-01", (), None)
        assert parse_strangerfleettest_args(
            "standing F-02") == (
            "standing", "F-02", (), None)
        assert parse_strangerfleettest_args("report") == (
            "reports", None, (), None)
        assert parse_strangerfleettest_args(
            "report fleet-2026-11") == (
            "report", "fleet-2026-11", (), None)
        assert parse_strangerfleettest_args("verdict") == (
            "verdict", None, (), None)
        assert parse_strangerfleettest_args("index") == (
            "index", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "exercise", "record",
                    "record F-01 extra",
                    "exercises now", "standing",
                    "report a b"):
            with pytest.raises(ValueError) as caught:
                parse_strangerfleettest_args(bad)
            assert str(caught.value) == STRANGERFLEETTEST_USAGE


class TestStrangerFleetTerminalRoad:
    def test_show_exercises_exercise_record_standing_report_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/strangerfleettest")
        assert "F-01" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/strangerfleettest exercises")
        assert "stranger-task" in text
        assert "F-03" in text
        _, _, text = _slash(
            agent, "/strangerfleettest exercise F-01")
        assert "stranger-task" in text
        _, _, text = _slash(
            agent, "/strangerfleettest record F-01")
        assert "holds no" in text
        _, _, text = _slash(
            agent, "/strangerfleettest standing F-01")
        assert "F-01:" in text
        assert "open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/strangerfleettest report")
        assert "none held" in text
        _, _, text = _slash(agent, "/strangerfleettest verdict")
        assert "Stranger fleet test stands open" in text
        agent.register_strangerfleettest_record(_sf_record())
        _, _, text = _slash(
            agent, "/strangerfleettest record F-01")
        assert "held as answered" in text
        _, _, text = _slash(
            agent, "/strangerfleettest standing F-01")
        assert "held as answered" in text
        _, _, text = _slash(agent, "/strangerfleettest index")
        assert "held as answered" in text
        agent.prepare_strangerfleettest_report(
            "fleet-2026-11", "release-1",
            "every exercise answered", "2026-11-13", 1, 2, 3,
            claims=("run_ref",))
        _, _, text = _slash(
            agent, "/strangerfleettest report fleet-2026-11")
        assert "every exercise answered" in text
        assert "never inflated" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/strangerfleettest [show|exercises|"
                "exercise <exercise>|"
                "record <exercise>|"
                "standing <exercise>|"
                "report [<book>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/strangerfleettest dance party")
        assert text == STRANGERFLEETTEST_USAGE
        _, _, text = _slash(
            agent, "/strangerfleettest exercise guess")
        assert "unknown exercise" in text


@pytest.fixture()
def sf_handler(agent, monkeypatch):
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


def _sf_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestStrangerFleetHandler:
    def test_show_is_default(self, sf_handler, agent):
        sf_handler._handle_strangerfleettest("")
        assert "F-01" in (
            _sf_published_text(sf_handler))
        assert "stranger-task" in (
            _sf_published_text(sf_handler))

    def test_exercise_record_and_verdict(
            self, sf_handler, agent):
        sf_handler._handle_strangerfleettest(
            "exercise F-01")
        assert "stranger-task" in (
            _sf_published_text(sf_handler))
        agent.register_strangerfleettest_record(_sf_record())
        sf_handler._handle_strangerfleettest(
            "record F-01")
        assert "held as answered" in (
            _sf_published_text(sf_handler))
        sf_handler._handle_strangerfleettest("verdict")
        assert "Stranger fleet test stands held" in (
            _sf_published_text(sf_handler))

    def test_bad_grammar_is_published(
            self, sf_handler, agent):
        sf_handler._handle_strangerfleettest("dance party")
        assert STRANGERFLEETTEST_USAGE in (
            _sf_published_text(sf_handler))
        sf_handler._handle_strangerfleettest("exercise guess")
        assert "unknown exercise" in (
            _sf_published_text(sf_handler))


class TestChatScreenRoutingStrangerFleet:
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
        screen.handle_command("/strangerfleettest verdict",
                              _FakeLog())
        assert calls == [("/strangerfleettest", "verdict")]

    def test_chat_screen_help_and_usage_name_the_audit(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/strangerfleettest[/green] - show the "
                "Stranger fleet test (M-266)") in text
        assert ('"/strangerfleettest": "Usage: '
                "/strangerfleettest | "
                "/strangerfleettest exercises") in text


class TestStrangerFleetDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.strangerfleettest_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _SF_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        _rp = ROOT / "README.md"
        _rb = _rp.read_bytes() if _rp.exists() else None
        verdict = agent.strangerfleettest_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_strangerfleettest_record(_sf_record())
        agent.register_strangerfleettest_record(
            _sf_fresh_for("F-02", work="fleet-2026-11-b"))
        verdict = agent.strangerfleettest_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "F-01", "F-02"]
        assert "Stranger fleet test stands held" in (
            verdict["verdict_text"])
        assert not _rp.exists() or _rp.read_bytes() == _rb

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_strangerfleettest()
        assert report["book"]["schema"] == (
            STRANGER_FLEET_TEST_SCHEMA)
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_strangerfleettest_record(_sf_record())
        report = agent.report_strangerfleettest()
        assert "held as answered" in report["records_text"]
        assert [s["exercise"] for s in report["standings"]] == [
            "F-01"]

    def test_exercises_for_disposition_and_held_keys(self, agent):
        agent.register_strangerfleettest_record(_sf_record())
        agent.register_strangerfleettest_record(
            _sf_fresh_for("F-02", work="fleet-2026-11-b"))
        agent.register_strangerfleettest_record(_sf_record(
            exercise="F-03", work="fleet-2026-11-c",
            disposition="ROADED", owner="",
            proof_kind="none",
            stages=["named"], claims=["assertion"]))
        assert [r.work for r in
                agent.exercises_for_disposition("PROVEN")] == [
            "fleet-2026-11-a", "fleet-2026-11-b"]
        assert agent.strangerfleettest_held() == ["F-01", "F-02"]
        standing = agent.strangerfleettest_standing(
            "F-03")
        assert standing.held is False
