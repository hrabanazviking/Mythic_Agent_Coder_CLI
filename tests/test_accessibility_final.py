"""M-262 Accessibility final gate - pure-layer tests.

TIER: unit

The Part V doctrine + M-118 red-team pack + an
shipped-TUI re-run of the sandbox/jail code,
findings clean or roaded with owners: a finding
counts PASSED only on the gate's own independent
read resting on held local evidence, and a
roaded finding with no owner named stands open.
"""
import pytest

from mythic_agent.core.accessibility_final import (
    CHECKS,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    CheckEntry,
    CheckRegistry,
    GateRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_check,
    format_checks,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(check="A-03",
                task="tui-2026-11-a",
                date="2026-11-13", disposition="PASSED",
                owner="yrsa",
                proof_kind="shipped-tui-rerun",
                stages=STAGES,
                claims=("rerun_ref", "journal_ref"))
    base.update(kw)
    return GateRecord(**base)


def roaded_record(**kw):
    base = dict(check="A-05",
                task="tui-2026-11-a",
                date="2026-11-13", disposition="ROADED",
                owner="yrsa",
                proof_kind="shipped-tui-rerun",
                stages=STAGES,
                claims=("journal_ref",))
    base.update(kw)
    return GateRecord(**base)


def full_book(**overrides):
    records = []
    for check_id in default_registry().combinations():
        if check_id in ("A-01", "A-02", "A-03"):
            kw = dict(check=check_id, task="tui-2026-11-a",
                      date="2026-11-13", disposition="PASSED",
                      owner="yrsa",
                      proof_kind="shipped-tui-rerun",
                      stages=STAGES,
                      claims=("rerun_ref", "journal_ref"))
        else:
            kw = dict(check=check_id, task="tui-2026-11-a",
                      date="2026-11-13", disposition="ROADED",
                      owner="yrsa",
                      proof_kind="shipped-tui-rerun",
                      stages=STAGES,
                      claims=("journal_ref",))
        kw.update(overrides.get(check_id, {}))
        records.append(GateRecord(**kw))
    return records


def test_registry_holds_twelve_checks_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "A-01"
    assert reg.ids()[-1] == "A-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_checks_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("A-01").doctrine == "M-199"
    assert reg.get("A-01").subject == "keyboard-task"
    assert reg.get("A-03").subject == "contrast-body"
    assert reg.get("A-05").subject == "reduced-motion"
    assert reg.get("A-11").doctrine == "M-016"
    assert reg.get("A-11").subject == "setup-traversal"
    assert reg.get("A-12").doctrine == "M-199"
    assert DISPOSITIONS == ("PASSED", "ROADED")


def test_registry_unknown_check_refused_by_name():
    with pytest.raises(ValidationError, match="unknown check: A-99"):
        default_registry().get("A-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate check"):
        CheckRegistry(CHECKS + CHECKS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        CheckRegistry([CheckEntry("A-01", "M-199", "keyboard-task", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        CheckRegistry([CheckEntry("A-01", "M-199", "keyboard-task", "published", "why")])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown check doctrine"):
        CheckRegistry([CheckEntry("A-01", "M-999", "keyboard-task", "listed", "why")])


def test_record_passed_shipped_rerun_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held
    assert standing.grade == "held"
    assert standing.gaps == ()


def test_record_incomplete_walk_stands_open():
    standing = derive_standing(fresh_record(stages=STAGES[:3]))
    assert not standing.held
    assert any("not held" in g for g in standing.gaps)


def test_record_bad_stage_step_stands_open():
    bad = ("named", "judged", "dispositioned", "held")
    standing = derive_standing(fresh_record(stages=bad))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_record_clean_on_historical_evidence_stands_open():
    standing = derive_standing(fresh_record(proof_kind="historical-only"))
    assert not standing.held
    assert any("no inheritance" in g for g in standing.gaps)


def test_record_clean_without_local_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("journal_ref",)))
    assert not standing.held
    assert any("no held rerun evidence" in g for g in standing.gaps)


def test_record_clean_on_bare_claims_stands_open():
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
    assert any("no gate date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_ready_with_roaded_checks():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.passed_checks == ("A-01", "A-02", "A-03")
    assert len(verdict.roaded_checks) == 9
    assert verdict.missing_checks == ()


def test_verdict_missing_check_stops_the_gate():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_checks == ("A-12",)
    assert any("A-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_gate():
    verdict = derive_verdict(full_book(**{"A-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("A-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_check_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("gate-a", "A-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("rerun_ref",))
    assert report.state == "ready"
    shared = prepare_report("gate-a", "A-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("rerun_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("gate-a", "A-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("rerun_ref",), state="sealed")
    with pytest.raises(ValidationError, match="gate closed"):
        prepare_report("gate-a", "A-01", "findings", "2026-11-13",
                       3, 5, 12, claims=("rerun_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("gate-a", "A-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("feeling",))
    assert "A-01" in format_check(default_registry().get("A-01"))
    assert "A-12" in format_checks()
    assert "PASSED" in format_record(fresh_record())
    assert "ROADED" in format_records([roaded_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)

# ---------------------------------------------------------------------


# ---------------------------------------------------------------------
# M-262 Accessibility final gate - agent layer. The pure book is held
# by a session registry in the agent layer alone: checks are read
# from the shipped registry, capture records are held one by one for
# the session, records, viewed standings and held reports are
# published as session news through the checkpoint road
# (journal-first, deduped per record, standing and verdict),
# standings, the index and the verdict are derived at call time from
# the held records - an check stands held only when its finding
# counts PASSED on shipped-tui-rerun evidence resting on held local
# evidence, or stands ROADED with a named owner in the open -
# audit reports are held only as reports, state ready by default,
# may be marked shared by a human, a certification claimed only
# when every check stands answered, and never inflated, and the
# registry is session state, never a stored setting. This layer
# runs no attack, reads no sandbox code and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    ACCESSIBILITYFINAL_USAGE,
    parse_accessibilityfinal_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.accessibility_final import (
    PLAIN_EXPLANATION,
    ACCESSIBILITY_FINAL_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_SA_EVENT_TYPES = (
    "accessibilityfinal_record", "accessibilityfinal_standing",
    "accessibilityfinal_verdict")

ALL_CHECKS = ["A-01", "A-02", "A-03", "A-04", "A-05", "A-06",
             "A-07", "A-08", "A-09", "A-10", "A-11", "A-12"]


def _af_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _af_record(**overrides):
    raw = {
        "check": "A-01",
        "task": "tui-2026-11-a",
        "date": "2026-11-13",
        "disposition": "PASSED",
        "owner": "yrsa",
        "proof_kind": "shipped-tui-rerun",
        "stages": list(STAGES),
        "claims": ["rerun_ref", "journal_ref"],
    }
    raw.update(overrides)
    return raw


def _af_fresh_for(check, task="tui-2026-11-a"):
    return _af_record(check=check, task=task)


class TestAccessibilityFinalAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_areas(
            self, agent):
        status = agent.accessibilityfinal_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["accessibilityfinal_book"]["schema"] == (
            ACCESSIBILITY_FINAL_SCHEMA)
        assert [c["id"] for c in status[
            "accessibilityfinal_book"]["checks"]] == ALL_CHECKS
        assert status["accessibilityfinal_book"]["records"] == []
        assert status["accessibilityfinal_book"]["reports"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "A-01" in status["checks_text"]
        assert "standing listed" in status["checks_text"]
        assert "none recorded this session" in status["screen"]
        assert "accessibility final gate" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == ACCESSIBILITYFINAL_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._accessibilityfinal_registry()
        assert agent._accessibilityfinal_registry() is first
        assert agent._accessibilityfinal_store is first
        for name in ("accessibilityfinal_checks",
                     "accessibilityfinal_book",
                     "accessibilityfinal_status",
                     "get_accessibilityfinal_check",
                     "get_accessibilityfinal_record",
                     "accessibilityfinal_standing",
                     "gates_for_disposition",
                     "accessibilityfinal_held",
                     "accessibilityfinal_index",
                     "accessibilityfinal_verdict",
                     "prepare_accessibilityfinal_report",
                     "get_accessibilityfinal_report",
                     "accessibilityfinal_reports",
                     "report_accessibilityfinal"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_accessibilityfinal_registry",
            "accessibilityfinal_checks",
            "accessibilityfinal_book",
            "accessibilityfinal_status",
            "get_accessibilityfinal_check",
            "get_accessibilityfinal_record",
            "accessibilityfinal_standing", "gates_for_disposition",
            "accessibilityfinal_held", "accessibilityfinal_index",
            "accessibilityfinal_verdict",
            "register_accessibilityfinal_record",
            "register_accessibilityfinal_records",
            "record_accessibilityfinal_records",
            "view_accessibilityfinal",
            "prepare_accessibilityfinal_report",
            "get_accessibilityfinal_report",
            "accessibilityfinal_reports",
            "report_accessibilityfinal",
            "_publish_accessibilityfinal_record",
            "_accessibilityfinal_screen",
            "_accessibilityfinal_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.accessibilityfinal_status()
        entry = agent.get_accessibilityfinal_check("A-01")
        assert entry.doctrine == "M-199"
        assert entry.subject == "keyboard-task"
        standing = agent.accessibilityfinal_standing("A-01")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.grade == "open"
        assert agent.accessibilityfinal_held() == []
        assert agent.gates_for_disposition("PASSED") == []
        agent.accessibilityfinal_index()
        agent.accessibilityfinal_verdict()
        agent.report_accessibilityfinal()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _SA_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown check"):
            agent.get_accessibilityfinal_check("guess")
        with pytest.raises(ValueError, match="unknown check"):
            agent.accessibilityfinal_standing("guess")
        with pytest.raises(ValueError, match="holds no"):
            agent.get_accessibilityfinal_record("A-01")
        with pytest.raises(ValueError):
            agent.gates_for_disposition("")
        agent.close()


class TestAccessibilityFinalAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_accessibilityfinal_record(
            _af_record())
        assert result["record"]["check"] == "A-01"
        assert result["record_news"]["type"] == (
            "accessibilityfinal_record")
        assert "held as answered" in result["screen"]
        status = agent.accessibilityfinal_status()
        assert [r["check"] for r in status["records"]] == [
            "A-01"]
        assert status["book"]["records"][0]["task"] == (
            "tui-2026-11-a")
        assert status["held"] == ["A-01"]
        assert status["open"] == []
        assert "held as answered" in status["records_text"]
        assert len(_af_records(
            store, session_id, "accessibilityfinal_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_accessibilityfinal_record(_af_record())
        with pytest.raises(ValueError, match="A-01"):
            agent.register_accessibilityfinal_record(
                _af_record(task="tui-2026-11-b"))
        assert len(_af_records(
            store, session_id, "accessibilityfinal_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_accessibilityfinal_record(
                _af_record(claims=["vibes"]))
        assert agent.accessibilityfinal_status()["records"] == []
        assert _af_records(
            store, session_id, "accessibilityfinal_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_accessibilityfinal_records([
            _af_fresh_for("A-05"), _af_record()])
        assert result["count"] == 2
        assert [r["check"] for r in result["records_news"]] == [
            "A-05", "A-01"]
        assert len(_af_records(
            store, session_id, "accessibilityfinal_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_accessibilityfinal_records(
            [_af_fresh_for("A-05")])
        assert result["count"] == 1
        assert result["book"]["schema"] == (
            ACCESSIBILITY_FINAL_SCHEMA)
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_accessibilityfinal_records(
                [_af_fresh_for("A-05")])
        assert len(_af_records(
            store, session_id, "accessibilityfinal_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_accessibilityfinal_record(_af_record())
        result = agent.view_accessibilityfinal("A-01")
        assert result["check"]["id"] == "A-01"
        assert result["standing"]["held"] is True
        assert result["record"]["task"] == "tui-2026-11-a"
        assert result["record_news"]["type"] == (
            "accessibilityfinal_standing")
        assert result["held_record_news"]["type"] == (
            "accessibilityfinal_record")
        assert len(_af_records(
            store, session_id, "accessibilityfinal_record")) == 1
        assert len(_af_records(
            store, session_id, "accessibilityfinal_standing")) == 1
        result = agent.view_accessibilityfinal("A-02")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_af_records(
            store, session_id, "accessibilityfinal_standing")) == 2
        agent.close()


class TestPrivacyPrivacyReports:
    def test_prepare_report_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_accessibilityfinal_report(
            "tui-2026-11", "release-1",
            "every check answered",
            "2026-11-13", 1, 11, 12,
            claims=("local_run_ref", "journal_ref"))
        assert result["report"]["state"] == "ready"
        assert result["report"]["certified"] is False
        assert result["report"]["inflated"] is False
        assert result["report_news"]["type"] == (
            "accessibilityfinal_verdict")
        assert "every check answered" in result["screen"]
        report = agent.get_accessibilityfinal_report(
            "tui-2026-11")
        assert report.entry == "release-1"
        assert [r.book for r in
                agent.accessibilityfinal_reports()] == [
            "tui-2026-11"]
        assert len(_af_records(
            store, session_id, "accessibilityfinal_verdict")) == 1
        agent.close()

    def test_report_unshared_state_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared"):
            agent.prepare_accessibilityfinal_report(
                "tui-2026-11", "release-1", "x",
                "2026-11-13", 1, 11, 12,
                claims=("local_run_ref",), state="executed")
        assert agent.accessibilityfinal_reports() == []
        assert _af_records(
            store, session_id, "accessibilityfinal_verdict") == []
        agent.close()

    def test_duplicate_report_refuses(self, agent):
        agent.prepare_accessibilityfinal_report(
            "tui-2026-11", "release-1",
            "every check answered", "2026-11-13", 1, 11, 12,
            claims=("local_run_ref",))
        with pytest.raises(ValueError, match="tui-2026-11"):
            agent.prepare_accessibilityfinal_report(
                "tui-2026-11", "release-2",
                "a second telling", "2026-11-13", 1, 11, 12,
                claims=("local_run_ref",))
        with pytest.raises(ValueError,
                           match="holds no"):
            agent.get_accessibilityfinal_report("audit-2026-12")


class TestAccessibilityFinalParseArgs:
    def test_parse_args_well(self):
        assert parse_accessibilityfinal_args("") == (
            "show", None, (), None)
        assert parse_accessibilityfinal_args(None) == (
            "show", None, (), None)
        assert parse_accessibilityfinal_args("checks") == (
            "checks", None, (), None)
        assert parse_accessibilityfinal_args(
            "check A-01") == (
            "check", "A-01", (), None)
        assert parse_accessibilityfinal_args(
            "record A-01") == (
            "record", "A-01", (), None)
        assert parse_accessibilityfinal_args(
            "standing A-03") == (
            "standing", "A-03", (), None)
        assert parse_accessibilityfinal_args("report") == (
            "reports", None, (), None)
        assert parse_accessibilityfinal_args(
            "report tui-2026-11") == (
            "report", "tui-2026-11", (), None)
        assert parse_accessibilityfinal_args("verdict") == (
            "verdict", None, (), None)
        assert parse_accessibilityfinal_args("index") == (
            "index", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "check", "record",
                    "record A-01 extra",
                    "checks now", "standing",
                    "report a b"):
            with pytest.raises(ValueError) as caught:
                parse_accessibilityfinal_args(bad)
            assert str(caught.value) == ACCESSIBILITYFINAL_USAGE


class TestAccessibilityFinalTerminalRoad:
    def test_show_areas_area_record_standing_report_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/accessibilityfinal")
        assert "A-01" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/accessibilityfinal checks")
        assert "keyboard-task" in text
        assert "A-12" in text
        _, _, text = _slash(
            agent, "/accessibilityfinal check A-01")
        assert "keyboard-task" in text
        _, _, text = _slash(
            agent, "/accessibilityfinal record A-01")
        assert "holds no" in text
        _, _, text = _slash(
            agent, "/accessibilityfinal standing A-01")
        assert "A-01:" in text
        assert "open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/accessibilityfinal report")
        assert "none held" in text
        _, _, text = _slash(agent, "/accessibilityfinal verdict")
        assert "Accessibility final gate stands open" in text
        agent.register_accessibilityfinal_record(_af_record())
        _, _, text = _slash(
            agent, "/accessibilityfinal record A-01")
        assert "held as answered" in text
        _, _, text = _slash(
            agent, "/accessibilityfinal standing A-01")
        assert "held as answered" in text
        _, _, text = _slash(agent, "/accessibilityfinal index")
        assert "held as answered" in text
        agent.prepare_accessibilityfinal_report(
            "tui-2026-11", "release-1",
            "every check answered", "2026-11-13", 1, 11, 12,
            claims=("local_run_ref",))
        _, _, text = _slash(
            agent, "/accessibilityfinal report tui-2026-11")
        assert "every check answered" in text
        assert "never inflated" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/accessibilityfinal [show|checks|"
                "check <check>|"
                "record <check>|"
                "standing <check>|"
                "report [<book>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/accessibilityfinal dance party")
        assert text == ACCESSIBILITYFINAL_USAGE
        _, _, text = _slash(
            agent, "/accessibilityfinal check guess")
        assert "unknown check" in text


@pytest.fixture()
def sa_handler(agent, monkeypatch):
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


def _af_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestAccessibilityFinalHandler:
    def test_show_is_default(self, sa_handler, agent):
        sa_handler._handle_accessibilityfinal("")
        assert "A-01" in (
            _af_published_text(sa_handler))
        assert "keyboard-task" in (
            _af_published_text(sa_handler))

    def test_area_record_and_verdict(
            self, sa_handler, agent):
        sa_handler._handle_accessibilityfinal(
            "check A-01")
        assert "keyboard-task" in (
            _af_published_text(sa_handler))
        agent.register_accessibilityfinal_record(_af_record())
        sa_handler._handle_accessibilityfinal(
            "record A-01")
        assert "held as answered" in (
            _af_published_text(sa_handler))
        sa_handler._handle_accessibilityfinal("verdict")
        assert "Accessibility final gate stands held" in (
            _af_published_text(sa_handler))

    def test_bad_grammar_is_published(
            self, sa_handler, agent):
        sa_handler._handle_accessibilityfinal("dance party")
        assert ACCESSIBILITYFINAL_USAGE in (
            _af_published_text(sa_handler))
        sa_handler._handle_accessibilityfinal("check guess")
        assert "unknown check" in (
            _af_published_text(sa_handler))


class TestChatScreenRoutingAccessibilityFinal:
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
        screen.handle_command("/accessibilityfinal verdict",
                              _FakeLog())
        assert calls == [("/accessibilityfinal", "verdict")]

    def test_chat_screen_help_and_usage_name_the_audit(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/accessibilityfinal[/green] - show the "
                "Accessibility final gate (M-262)") in text
        assert ('"/accessibilityfinal": "Usage: '
                "/accessibilityfinal | "
                "/accessibilityfinal checks") in text


class TestAccessibilityFinalDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.accessibilityfinal_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _SA_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        verdict = agent.accessibilityfinal_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_accessibilityfinal_record(_af_record())
        agent.register_accessibilityfinal_record(
            _af_fresh_for("A-05", task="tui-2026-11-b"))
        verdict = agent.accessibilityfinal_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "A-01", "A-05"]
        assert "Accessibility final gate stands held" in (
            verdict["verdict_text"])

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_accessibilityfinal()
        assert report["book"]["schema"] == (
            ACCESSIBILITY_FINAL_SCHEMA)
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_accessibilityfinal_record(_af_record())
        report = agent.report_accessibilityfinal()
        assert "held as answered" in report["records_text"]
        assert [s["check"] for s in report["standings"]] == [
            "A-01"]

    def test_gates_for_disposition_and_held_keys(self, agent):
        agent.register_accessibilityfinal_record(_af_record())
        agent.register_accessibilityfinal_record(
            _af_fresh_for("A-05", task="tui-2026-11-b"))
        agent.register_accessibilityfinal_record(_af_record(
            check="A-02", task="tui-2026-11-c",
            disposition="ROADED", owner="",
            proof_kind="none",
            stages=["named"], claims=["assertion"]))
        assert [r.task for r in
                agent.gates_for_disposition("PASSED")] == [
            "tui-2026-11-a", "tui-2026-11-b"]
        assert agent.accessibilityfinal_held() == ["A-01", "A-05"]
        standing = agent.accessibilityfinal_standing(
            "A-02")
        assert standing.held is False
