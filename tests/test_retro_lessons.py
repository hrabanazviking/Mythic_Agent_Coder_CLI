"""M-271 Retro and lessons - pure-layer tests.

TIER: unit

The campaign retrospective written into the self-improving
ledger, lesson by lesson, patterns worth keeping named as
skill candidates: a pattern counts KEPT only on held proof
measured in the campaign itself resting on held evidence
written in the ledger, a roaded lesson only where its road
rests on held evidence and its owner is named, and a dropped
lesson only with its owner and reason recorded - a dropped
lesson admitted in the open is honest.
"""
import pytest

from mythic_agent.core.retro_lessons import (
    RETRO_ENTRIES,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    RetroEntry,
    RetroRegistry,
    RetroRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_entry,
    format_entries,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(lesson="L-03",
                work="retro-2026-11-a",
                date="2026-11-13", disposition="KEPT",
                owner="yrsa",
                proof_kind="kept-and-held",
                stages=STAGES,
                claims=("ledger_ref", "test_ref"))
    base.update(kw)
    return RetroRecord(**base)


def roaded_record(**kw):
    base = dict(lesson="L-05",
                work="retro-2026-11-a",
                date="2026-11-13", disposition="ROADED",
                owner="yrsa",
                proof_kind="roaded-open",
                stages=STAGES,
                claims=("test_ref",))
    base.update(kw)
    return RetroRecord(**base)


def dropped_record(**kw):
    base = dict(lesson="L-07",
                work="retro-2026-11-a",
                date="2026-11-13", disposition="DROPPED",
                owner="yrsa",
                proof_kind="none",
                stages=STAGES,
                claims=("test_ref",))
    base.update(kw)
    return RetroRecord(**base)


def full_book(**overrides):
    records = []
    for lesson_id in default_registry().combinations():
        if lesson_id in ("L-01", "L-02", "L-03"):
            kw = dict(lesson=lesson_id, work="retro-2026-11-a",
                      date="2026-11-13", disposition="KEPT",
                      owner="yrsa",
                      proof_kind="kept-and-held",
                      stages=STAGES,
                      claims=("ledger_ref", "test_ref"))
        elif lesson_id in ("L-04", "L-05", "L-06", "L-07"):
            kw = dict(lesson=lesson_id, work="retro-2026-11-a",
                      date="2026-11-13", disposition="ROADED",
                      owner="yrsa",
                      proof_kind="roaded-open",
                      stages=STAGES,
                      claims=("test_ref",))
        else:
            kw = dict(lesson=lesson_id, work="retro-2026-11-a",
                      date="2026-11-13", disposition="DROPPED",
                      owner="yrsa",
                      proof_kind="none",
                      stages=STAGES,
                      claims=("test_ref",))
        kw.update(overrides.get(lesson_id, {}))
        records.append(RetroRecord(**kw))
    return records


def test_registry_holds_twelve_lessons_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "L-01"
    assert reg.ids()[-1] == "L-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_lessons_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("L-01").doctrine == "campaign-evidence"
    assert reg.get("L-01").subject == "banking-discipline"
    assert reg.get("L-02").subject == "stall-guard"
    assert reg.get("L-03").subject == "verify-from-disk"
    assert reg.get("L-04").subject == "closure-heals"
    assert reg.get("L-11").doctrine == "self-improving"
    assert reg.get("L-11").subject == "honest-boundary"
    assert reg.get("L-12").doctrine == "self-improving"
    assert DISPOSITIONS == ("KEPT", "ROADED", "DROPPED")


def test_registry_unknown_lesson_refused_by_name():
    with pytest.raises(ValidationError, match="unknown lesson: C-99"):
        default_registry().get("C-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate lesson"):
        RetroRegistry(RETRO_ENTRIES + RETRO_ENTRIES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        RetroRegistry([RetroEntry("L-01", "campaign-evidence", "banking-discipline", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        RetroRegistry([RetroEntry("L-01", "campaign-evidence", "banking-discipline", "published", "why")])
    with pytest.raises(ValidationError, match="labelled"):
        RetroRegistry([RetroEntry("L-01", "campaign-evidence", "banking-discipline", "listed", "why", labelled=False)])
    with pytest.raises(ValidationError, match="evidenced"):
        RetroRegistry([RetroEntry("L-01", "campaign-evidence", "banking-discipline", "listed", "why", evidenced=False)])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown lesson doctrine"):
        RetroRegistry([RetroEntry("L-01", "M-999", "banking-discipline", "listed", "why")])


def test_record_kept_measured_and_held_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held
    assert standing.grade == "held"
    assert standing.gaps == ()


def test_record_incomplete_walk_stands_open():
    standing = derive_standing(fresh_record(stages=STAGES[:3]))
    assert not standing.held
    assert any("not held" in g for g in standing.gaps)


def test_record_bad_stage_step_stands_open():
    bad = ("named", "evidenced", "dispositioned", "held")
    standing = derive_standing(fresh_record(stages=bad))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_record_kept_on_roaded_proof_stands_open():
    standing = derive_standing(fresh_record(proof_kind="roaded-open"))
    assert not standing.held
    assert any("tells the truth" in g for g in standing.gaps)


def test_record_kept_without_ledger_ref_stands_open():
    standing = derive_standing(fresh_record(claims=("test_ref",)))
    assert not standing.held
    assert any("no held" in g for g in standing.gaps)


def test_record_kept_on_bare_claims_stands_open():
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


def test_record_dropped_silent_stands_open():
    standing = derive_standing(dropped_record(claims=()))
    assert not standing.held
    assert any("silent" in g for g in standing.gaps)


def test_record_without_date_stands_open():
    standing = derive_standing(fresh_record(date=""))
    assert not standing.held
    assert any("no report date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_kept_with_roaded_lessons():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.kept_lessons == ("L-01", "L-02", "L-03")
    assert len(verdict.roaded_lessons) == 4
    assert len(verdict.dropped_lessons) == 5
    assert verdict.missing_lessons == ()


def test_verdict_missing_lesson_stops_the_report():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_lessons == ("L-12",)
    assert any("L-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_report():
    verdict = derive_verdict(full_book(**{"L-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("L-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_lesson_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two records" in g for g in verdict.gaps)


def test_report_kept_and_shared_states():
    report = prepare_report("retro-a", "L-01", "lessons as dispositioned",
                            "2026-11-13", 3, 4, 5, 12,
                            claims=("ledger_ref",))
    assert report.state == "ready"
    shared = prepare_report("retro-a", "L-01", "lessons as dispositioned",
                            "2026-11-13", 3, 4, 5, 12,
                            claims=("ledger_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("retro-a", "L-01", "lessons", "2026-11-13",
                       3, 4, 5, 12, claims=("ledger_ref",), state="sealed")
    with pytest.raises(ValidationError, match="retro complete"):
        prepare_report("retro-a", "L-01", "lessons", "2026-11-13",
                       3, 2, 2, 12, claims=("ledger_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("retro-a", "L-01", "lessons", "2026-11-13",
                       3, 4, 5, 12, claims=("feeling",))
    assert "L-01" in format_entry(default_registry().get("L-01"))
    assert "L-12" in format_entries()
    assert "KEPT" in format_record(fresh_record())
    assert "ROADED" in format_records([roaded_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
    from pathlib import Path as _P
    _src = (_P(__file__).resolve().parent.parent
            / "mythic_agent" / "core" / "retro_lessons.py").read_text(
                encoding="utf-8")
    assert "open(" not in _src
    assert "socket" not in _src
    assert "subprocess" not in _src
    assert "urllib" not in _src


# ---------------------------------------------------------------------
# M-271 Retro and lessons - agent layer. The pure book is held
# by a session registry in the agent layer alone: lessons are read
# from the shipped registry, capture records are held one by one for
# the session, records, viewed standings and held reports are
# published as session news through the checkpoint road
# (journal-first, deduped per record, standing and verdict),
# standings, the index and the verdict are derived at call time from
# the held records - an lesson stands held only when its finding
# counts KEPT on kept-and-held evidence resting on held local
# evidence, or stands ROADED or DROPPED with a named owner in the open -
# audit reports are held only as reports, state ready by default,
# may be marked shared by a human, a certification claimed only
# when every lesson stands answered, and never inflated, and the
# registry is session state, never a stored setting. This layer
# runs no attack, reads no sandbox code and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    RETROLESSONS_USAGE,
    parse_retrolessons_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.retro_lessons import (
    PLAIN_EXPLANATION,
    RETRO_LESSONS_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_RL_EVENT_TYPES = (
    "retrolessons_record", "retrolessons_standing",
    "retrolessons_verdict")

ALL_FAMILIES = ["L-01", "L-02", "L-03", "L-04", "L-05", "L-06",
             "L-07", "L-08", "L-09", "L-10", "L-11", "L-12"]


def _rl_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _rl_record(**overrides):
    raw = {
        "lesson": "L-01",
        "work": "lesson-2026-11-a",
        "date": "2026-11-13",
        "disposition": "KEPT",
        "owner": "yrsa",
        "proof_kind": "kept-and-held",
        "stages": list(STAGES),
        "claims": ["ledger_ref", "test_ref"],
    }
    raw.update(overrides)
    return raw


def _rl_fresh_for(lesson, work="lesson-2026-11-a"):
    return _rl_record(lesson=lesson, work=work)


class TestRetroLessonsAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_lessons(
            self, agent):
        status = agent.retrolessons_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["retrolessons_book"]["schema"] == (
            RETRO_LESSONS_SCHEMA)
        assert [c["id"] for c in status[
            "retrolessons_book"]["lessons"]] == ALL_FAMILIES
        assert status["retrolessons_book"]["records"] == []
        assert status["retrolessons_book"]["reports"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "L-01" in status["lessons_text"]
        assert "standing listed" in status["lessons_text"]
        assert "none recorded this session" in status["screen"]
        assert "campaign retro" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == RETROLESSONS_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._retrolessons_registry()
        assert agent._retrolessons_registry() is first
        assert agent._retrolessons_store is first
        for name in ("retrolessons_lessons",
                     "retrolessons_book",
                     "retrolessons_status",
                     "get_retrolessons_lesson",
                     "get_retrolessons_record",
                     "retrolessons_standing",
                     "lessons_for_disposition",
                     "retrolessons_held",
                     "retrolessons_index",
                     "retrolessons_verdict",
                     "prepare_retrolessons_report",
                     "get_retrolessons_report",
                     "retrolessons_reports",
                     "report_retrolessons"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_retrolessons_registry",
            "retrolessons_lessons",
            "retrolessons_book",
            "retrolessons_status",
            "get_retrolessons_lesson",
            "get_retrolessons_record",
            "retrolessons_standing", "lessons_for_disposition",
            "retrolessons_held", "retrolessons_index",
            "retrolessons_verdict",
            "register_retrolessons_record",
            "register_retrolessons_records",
            "record_retrolessons_records",
            "view_retrolessons",
            "prepare_retrolessons_report",
            "get_retrolessons_report",
            "retrolessons_reports",
            "report_retrolessons",
            "_publish_retrolessons_record",
            "_retrolessons_screen",
            "_retrolessons_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.retrolessons_status()
        entry = agent.get_retrolessons_lesson("L-01")
        assert entry.doctrine == "campaign-evidence"
        assert entry.subject == "banking-discipline"
        standing = agent.retrolessons_standing("L-01")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.grade == "open"
        assert agent.retrolessons_held() == []
        assert agent.lessons_for_disposition("KEPT") == []
        agent.retrolessons_index()
        agent.retrolessons_verdict()
        agent.report_retrolessons()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _RL_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown lesson"):
            agent.get_retrolessons_lesson("guess")
        with pytest.raises(ValueError, match="unknown lesson"):
            agent.retrolessons_standing("guess")
        with pytest.raises(ValueError, match="holds no"):
            agent.get_retrolessons_record("L-01")
        with pytest.raises(ValueError):
            agent.lessons_for_disposition("")
        agent.close()


class TestRetroLessonsAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_retrolessons_record(
            _rl_record())
        assert result["record"]["lesson"] == "L-01"
        assert result["record_news"]["type"] == (
            "retrolessons_record")
        assert "held as answered" in result["screen"]
        status = agent.retrolessons_status()
        assert [r["lesson"] for r in status["records"]] == [
            "L-01"]
        assert status["book"]["records"][0]["work"] == (
            "lesson-2026-11-a")
        assert status["held"] == ["L-01"]
        assert status["open"] == []
        assert "held as answered" in status["records_text"]
        assert len(_rl_records(
            store, session_id, "retrolessons_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_retrolessons_record(_rl_record())
        with pytest.raises(ValueError, match="L-01"):
            agent.register_retrolessons_record(
                _rl_record(work="lesson-2026-11-b"))
        assert len(_rl_records(
            store, session_id, "retrolessons_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_retrolessons_record(
                _rl_record(claims=["vibes"]))
        assert agent.retrolessons_status()["records"] == []
        assert _rl_records(
            store, session_id, "retrolessons_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_retrolessons_records([
            _rl_fresh_for("L-02"), _rl_record()])
        assert result["count"] == 2
        assert [r["lesson"] for r in result["records_news"]] == [
            "L-02", "L-01"]
        assert len(_rl_records(
            store, session_id, "retrolessons_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_retrolessons_records(
            [_rl_fresh_for("L-02")])
        assert result["count"] == 1
        assert result["book"]["schema"] == (
            RETRO_LESSONS_SCHEMA)
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_retrolessons_records(
                [_rl_fresh_for("L-02")])
        assert len(_rl_records(
            store, session_id, "retrolessons_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_retrolessons_record(_rl_record())
        result = agent.view_retrolessons("L-01")
        assert result["lesson"]["id"] == "L-01"
        assert result["standing"]["held"] is True
        assert result["record"]["work"] == "lesson-2026-11-a"
        assert result["record_news"]["type"] == (
            "retrolessons_standing")
        assert result["held_record_news"]["type"] == (
            "retrolessons_record")
        assert len(_rl_records(
            store, session_id, "retrolessons_record")) == 1
        assert len(_rl_records(
            store, session_id, "retrolessons_standing")) == 1
        result = agent.view_retrolessons("L-03")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_rl_records(
            store, session_id, "retrolessons_standing")) == 2
        agent.close()


class TestRetroReports:
    def test_prepare_report_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_retrolessons_report(
            "lesson-2026-11", "lesson-1",
            "every lesson answered",
            "2026-11-13", 3, 4, 5, 12,
            claims=("ledger_ref", "test_ref"))
        assert result["report"]["state"] == "ready"
        assert result["report"]["certified"] is False
        assert result["report"]["inflated"] is False
        assert result["report_news"]["type"] == (
            "retrolessons_verdict")
        assert "every lesson answered" in result["screen"]
        report = agent.get_retrolessons_report(
            "lesson-2026-11")
        assert report.entry == "lesson-1"
        assert [r.book for r in
                agent.retrolessons_reports()] == [
            "lesson-2026-11"]
        assert len(_rl_records(
            store, session_id, "retrolessons_verdict")) == 1
        agent.close()

    def test_report_unshared_state_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared"):
            agent.prepare_retrolessons_report(
                "lesson-2026-11", "lesson-1", "x",
                "2026-11-13", 3, 4, 5, 12,
                claims=("evidence_ref",), state="executed")
        assert agent.retrolessons_reports() == []
        assert _rl_records(
            store, session_id, "retrolessons_verdict") == []
        agent.close()

    def test_duplicate_report_refuses(self, agent):
        agent.prepare_retrolessons_report(
            "lesson-2026-11", "lesson-1",
            "every lesson answered", "2026-11-13", 3, 4, 5, 12,
            claims=("evidence_ref",))
        with pytest.raises(ValueError, match="lesson-2026-11"):
            agent.prepare_retrolessons_report(
                "lesson-2026-11", "lesson-2",
                "a second telling", "2026-11-13", 3, 4, 5, 12,
                claims=("evidence_ref",))
        with pytest.raises(ValueError,
                           match="holds no"):
            agent.get_retrolessons_report("lesson-2026-12")


class TestRetroLessonsParseArgs:
    def test_parse_args_well(self):
        assert parse_retrolessons_args("") == (
            "show", None, (), None)
        assert parse_retrolessons_args(None) == (
            "show", None, (), None)
        assert parse_retrolessons_args("lessons") == (
            "lessons", None, (), None)
        assert parse_retrolessons_args(
            "lesson L-01") == (
            "lesson", "L-01", (), None)
        assert parse_retrolessons_args(
            "record L-01") == (
            "record", "L-01", (), None)
        assert parse_retrolessons_args(
            "standing L-02") == (
            "standing", "L-02", (), None)
        assert parse_retrolessons_args("report") == (
            "reports", None, (), None)
        assert parse_retrolessons_args(
            "report lesson-2026-11") == (
            "report", "lesson-2026-11", (), None)
        assert parse_retrolessons_args("verdict") == (
            "verdict", None, (), None)
        assert parse_retrolessons_args("index") == (
            "index", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "lesson", "record",
                    "record L-01 extra",
                    "lessons now", "standing",
                    "report a b"):
            with pytest.raises(ValueError) as caught:
                parse_retrolessons_args(bad)
            assert str(caught.value) == RETROLESSONS_USAGE


class TestRetroLessonsTerminalRoad:
    def test_show_lessons_lesson_record_standing_report_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/retrolessons")
        assert "L-01" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/retrolessons lessons")
        assert "banking-discipline" in text
        assert "L-03" in text
        _, _, text = _slash(
            agent, "/retrolessons lesson L-01")
        assert "banking-discipline" in text
        _, _, text = _slash(
            agent, "/retrolessons record L-01")
        assert "holds no" in text
        _, _, text = _slash(
            agent, "/retrolessons standing L-01")
        assert "L-01:" in text
        assert "open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/retrolessons report")
        assert "none held" in text
        _, _, text = _slash(agent, "/retrolessons verdict")
        assert "Retro and lessons stands open" in text
        agent.register_retrolessons_record(_rl_record())
        _, _, text = _slash(
            agent, "/retrolessons record L-01")
        assert "held as answered" in text
        _, _, text = _slash(
            agent, "/retrolessons standing L-01")
        assert "held as answered" in text
        _, _, text = _slash(agent, "/retrolessons index")
        assert "held as answered" in text
        agent.prepare_retrolessons_report(
            "lesson-2026-11", "lesson-1",
            "every lesson answered", "2026-11-13", 3, 4, 5, 12,
            claims=("evidence_ref",))
        _, _, text = _slash(
            agent, "/retrolessons report lesson-2026-11")
        assert "every lesson answered" in text
        assert "never inflated" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/retrolessons [show|lessons|"
                "lesson <lesson>|"
                "record <lesson>|"
                "standing <lesson>|"
                "report [<book>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/retrolessons dance lessony")
        assert text == RETROLESSONS_USAGE
        _, _, text = _slash(
            agent, "/retrolessons lesson guess")
        assert "unknown lesson" in text


@pytest.fixture()
def ra_handler(agent, monkeypatch):
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


def _rl_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestRetroLessonsHandler:
    def test_show_is_default(self, ra_handler, agent):
        ra_handler._handle_retrolessons("")
        assert "L-01" in (
            _rl_published_text(ra_handler))
        assert "banking-discipline" in (
            _rl_published_text(ra_handler))

    def test_lesson_record_and_verdict(
            self, ra_handler, agent):
        ra_handler._handle_retrolessons(
            "lesson L-01")
        assert "banking-discipline" in (
            _rl_published_text(ra_handler))
        agent.register_retrolessons_record(_rl_record())
        ra_handler._handle_retrolessons(
            "record L-01")
        assert "held as answered" in (
            _rl_published_text(ra_handler))
        ra_handler._handle_retrolessons("verdict")
        assert "Retro and lessons stands held" in (
            _rl_published_text(ra_handler))

    def test_bad_grammar_is_published(
            self, ra_handler, agent):
        ra_handler._handle_retrolessons("dance lessony")
        assert RETROLESSONS_USAGE in (
            _rl_published_text(ra_handler))
        ra_handler._handle_retrolessons("lesson guess")
        assert "unknown lesson" in (
            _rl_published_text(ra_handler))


class TestChatScreenRoutingRetroLessons:
    def test_lessons_as_system_command(self, monkeypatch):
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
        screen.handle_command("/retrolessons verdict",
                              _FakeLog())
        assert calls == [("/retrolessons", "verdict")]

    def test_chat_screen_help_and_usage_name_the_audit(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/retrolessons[/green] - show the "
                "Retro and lessons (M-271)") in text
        assert ('"/retrolessons": "Usage: '
                "/retrolessons | "
                "/retrolessons lessons") in text


class TestRetroLessonsDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.retrolessons_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _RL_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        _rp = ROOT / "README.md"
        _rb = _rp.read_bytes() if _rp.exists() else None
        verdict = agent.retrolessons_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_retrolessons_record(_rl_record())
        agent.register_retrolessons_record(
            _rl_fresh_for("L-02", work="lesson-2026-11-b"))
        verdict = agent.retrolessons_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "L-01", "L-02"]
        assert "Retro and lessons stands held" in (
            verdict["verdict_text"])
        assert not _rp.exists() or _rp.read_bytes() == _rb

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_retrolessons()
        assert report["book"]["schema"] == (
            RETRO_LESSONS_SCHEMA)
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_retrolessons_record(_rl_record())
        report = agent.report_retrolessons()
        assert "held as answered" in report["records_text"]
        assert [s["lesson"] for s in report["standings"]] == [
            "L-01"]

    def test_lessons_for_disposition_and_held_keys(self, agent):
        agent.register_retrolessons_record(_rl_record())
        agent.register_retrolessons_record(
            _rl_fresh_for("L-02", work="lesson-2026-11-b"))
        agent.register_retrolessons_record(_rl_record(
            lesson="L-03", work="lesson-2026-11-c",
            disposition="DROPPED", owner="",
            proof_kind="none",
            stages=["named"], claims=["assertion"]))
        assert [r.work for r in
                agent.lessons_for_disposition("KEPT")] == [
            "lesson-2026-11-a", "lesson-2026-11-b"]
        assert agent.retrolessons_held() == ["L-01", "L-02"]
        standing = agent.retrolessons_standing(
            "L-03")
        assert standing.held is False
