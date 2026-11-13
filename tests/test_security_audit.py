"""M-260 Security audit - pure-layer tests.

TIER: unit

The Part V doctrine + M-118 red-team pack + an
independent read of the sandbox/jail code,
findings fixed or roaded with owners: a finding
counts FIXED only on the audit's own independent
read resting on held local evidence, and a
roaded finding with no owner named stands open.
"""
import pytest

from mythic_agent.core.security_audit import (
    AREAS,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    AreaEntry,
    AreaRegistry,
    FindingRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_area,
    format_areas,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(area="S-03",
                run="audit-2026-11-a",
                date="2026-11-13", disposition="FIXED",
                owner="yrsa",
                proof_kind="independent-read",
                stages=STAGES,
                claims=("local_run_ref", "report_ref"))
    base.update(kw)
    return FindingRecord(**base)


def roaded_record(**kw):
    base = dict(area="S-05",
                run="audit-2026-11-a",
                date="2026-11-13", disposition="ROADED",
                owner="yrsa",
                proof_kind="independent-read",
                stages=STAGES,
                claims=("report_ref",))
    base.update(kw)
    return FindingRecord(**base)


def full_book(**overrides):
    records = []
    for area_id in default_registry().combinations():
        if area_id in ("S-01", "S-02", "S-03"):
            kw = dict(area=area_id, run="audit-2026-11-a",
                      date="2026-11-13", disposition="FIXED",
                      owner="yrsa",
                      proof_kind="independent-read",
                      stages=STAGES,
                      claims=("local_run_ref", "report_ref"))
        else:
            kw = dict(area=area_id, run="audit-2026-11-a",
                      date="2026-11-13", disposition="ROADED",
                      owner="yrsa",
                      proof_kind="independent-read",
                      stages=STAGES,
                      claims=("report_ref",))
        kw.update(overrides.get(area_id, {}))
        records.append(FindingRecord(**kw))
    return records


def test_registry_holds_twelve_areas_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "S-01"
    assert reg.ids()[-1] == "S-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_areas_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("S-01").doctrine == "M-095"
    assert reg.get("S-01").subject == "permission-profiles"
    assert reg.get("S-03").subject == "os-sandbox"
    assert reg.get("S-05").subject == "path-jail"
    assert reg.get("S-11").doctrine == "M-118"
    assert reg.get("S-11").subject == "red-team-pack"
    assert reg.get("S-12").doctrine == "M-119"
    assert DISPOSITIONS == ("FIXED", "ROADED")


def test_registry_unknown_area_refused_by_name():
    with pytest.raises(ValidationError, match="unknown area: S-99"):
        default_registry().get("S-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate area"):
        AreaRegistry(AREAS + AREAS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        AreaRegistry([AreaEntry("S-01", "M-095", "permission-profiles", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        AreaRegistry([AreaEntry("S-01", "M-095", "permission-profiles", "published", "why")])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown area doctrine"):
        AreaRegistry([AreaEntry("S-01", "M-999", "permission-profiles", "listed", "why")])


def test_record_fixed_independent_read_stands_held():
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


def test_record_fixed_on_historical_evidence_stands_open():
    standing = derive_standing(fresh_record(proof_kind="historical-only"))
    assert not standing.held
    assert any("no inheritance" in g for g in standing.gaps)


def test_record_fixed_without_local_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("report_ref",)))
    assert not standing.held
    assert any("no held local evidence" in g for g in standing.gaps)


def test_record_fixed_on_bare_claims_stands_open():
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
    assert any("no audit date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_ready_with_roaded_areas():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.fixed_areas == ("S-01", "S-02", "S-03")
    assert len(verdict.roaded_areas) == 9
    assert verdict.missing_areas == ()


def test_verdict_missing_area_stops_the_audit():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_areas == ("S-12",)
    assert any("S-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_audit():
    verdict = derive_verdict(full_book(**{"S-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("S-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_area_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("audit-a", "S-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("local_run_ref",))
    assert report.state == "ready"
    shared = prepare_report("audit-a", "S-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("local_run_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("audit-a", "S-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("local_run_ref",), state="sealed")
    with pytest.raises(ValidationError, match="audit closed"):
        prepare_report("audit-a", "S-01", "findings", "2026-11-13",
                       3, 5, 12, claims=("local_run_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("audit-a", "S-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("feeling",))
    assert "S-01" in format_area(default_registry().get("S-01"))
    assert "S-12" in format_areas()
    assert "FIXED" in format_record(fresh_record())
    assert "ROADED" in format_records([roaded_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)

# ---------------------------------------------------------------------
# M-260 Security audit - agent layer. The pure book is held
# by a session registry in the agent layer alone: areas are read
# from the shipped registry, finding records are held one by one for
# the session, records, viewed standings and held reports are
# published as session news through the checkpoint road
# (journal-first, deduped per record, standing and verdict),
# standings, the index and the verdict are derived at call time from
# the held records - an area stands held only when its finding
# counts FIXED on independent-read evidence resting on held local
# evidence, or stands ROADED with a named owner in the open -
# audit reports are held only as reports, state ready by default,
# may be marked shared by a human, a certification claimed only
# when every area stands answered, and never inflated, and the
# registry is session state, never a stored setting. This layer
# runs no attack, reads no sandbox code and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    SECURITYAUDIT_USAGE,
    parse_securityaudit_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.security_audit import (
    PLAIN_EXPLANATION,
    SECURITY_AUDIT_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_SA_EVENT_TYPES = (
    "securityaudit_record", "securityaudit_standing",
    "securityaudit_verdict")

ALL_AREAS = ["S-01", "S-02", "S-03", "S-04", "S-05", "S-06",
             "S-07", "S-08", "S-09", "S-10", "S-11", "S-12"]


def _sa_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _sa_record(**overrides):
    raw = {
        "area": "S-01",
        "run": "audit-2026-11-a",
        "date": "2026-11-13",
        "disposition": "FIXED",
        "owner": "yrsa",
        "proof_kind": "independent-read",
        "stages": list(STAGES),
        "claims": ["local_run_ref", "journal_ref"],
    }
    raw.update(overrides)
    return raw


def _sa_fresh_for(area, run="audit-2026-11-a"):
    return _sa_record(area=area, run=run)


class TestSecurityAuditAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_areas(
            self, agent):
        status = agent.securityaudit_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["securityaudit_book"]["schema"] == (
            SECURITY_AUDIT_SCHEMA)
        assert [c["id"] for c in status[
            "securityaudit_book"]["areas"]] == ALL_AREAS
        assert status["securityaudit_book"]["records"] == []
        assert status["securityaudit_book"]["reports"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "S-01" in status["areas_text"]
        assert "standing listed" in status["areas_text"]
        assert "none recorded this session" in status["screen"]
        assert "security audit" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == SECURITYAUDIT_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._securityaudit_registry()
        assert agent._securityaudit_registry() is first
        assert agent._securityaudit_store is first
        for name in ("securityaudit_areas",
                     "securityaudit_book",
                     "securityaudit_status",
                     "get_securityaudit_area",
                     "get_securityaudit_record",
                     "securityaudit_standing",
                     "records_for_disposition",
                     "securityaudit_held",
                     "securityaudit_index",
                     "securityaudit_verdict",
                     "prepare_securityaudit_report",
                     "get_securityaudit_report",
                     "securityaudit_reports",
                     "report_securityaudit"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_securityaudit_registry",
            "securityaudit_areas",
            "securityaudit_book",
            "securityaudit_status",
            "get_securityaudit_area",
            "get_securityaudit_record",
            "securityaudit_standing", "records_for_disposition",
            "securityaudit_held", "securityaudit_index",
            "securityaudit_verdict",
            "register_securityaudit_record",
            "register_securityaudit_records",
            "record_securityaudit_records",
            "view_securityaudit",
            "prepare_securityaudit_report",
            "get_securityaudit_report",
            "securityaudit_reports",
            "report_securityaudit",
            "_publish_securityaudit_record",
            "_securityaudit_screen",
            "_securityaudit_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.securityaudit_status()
        entry = agent.get_securityaudit_area("S-01")
        assert entry.doctrine == "M-095"
        assert entry.subject == "permission-profiles"
        standing = agent.securityaudit_standing("S-01")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.grade == "open"
        assert agent.securityaudit_held() == []
        assert agent.records_for_disposition("FIXED") == []
        agent.securityaudit_index()
        agent.securityaudit_verdict()
        agent.report_securityaudit()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _SA_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown area"):
            agent.get_securityaudit_area("guess")
        with pytest.raises(ValueError, match="unknown area"):
            agent.securityaudit_standing("guess")
        with pytest.raises(ValueError, match="holds no"):
            agent.get_securityaudit_record("S-01")
        with pytest.raises(ValueError):
            agent.records_for_disposition("")
        agent.close()


class TestSecurityAuditAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_securityaudit_record(
            _sa_record())
        assert result["record"]["area"] == "S-01"
        assert result["record_news"]["type"] == (
            "securityaudit_record")
        assert "held as answered" in result["screen"]
        status = agent.securityaudit_status()
        assert [r["area"] for r in status["records"]] == [
            "S-01"]
        assert status["book"]["records"][0]["run"] == (
            "audit-2026-11-a")
        assert status["held"] == ["S-01"]
        assert status["open"] == []
        assert "held as answered" in status["records_text"]
        assert len(_sa_records(
            store, session_id, "securityaudit_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_securityaudit_record(_sa_record())
        with pytest.raises(ValueError, match="S-01"):
            agent.register_securityaudit_record(
                _sa_record(run="audit-2026-11-b"))
        assert len(_sa_records(
            store, session_id, "securityaudit_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_securityaudit_record(
                _sa_record(claims=["vibes"]))
        assert agent.securityaudit_status()["records"] == []
        assert _sa_records(
            store, session_id, "securityaudit_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_securityaudit_records([
            _sa_fresh_for("S-05"), _sa_record()])
        assert result["count"] == 2
        assert [r["area"] for r in result["records_news"]] == [
            "S-05", "S-01"]
        assert len(_sa_records(
            store, session_id, "securityaudit_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_securityaudit_records(
            [_sa_fresh_for("S-05")])
        assert result["count"] == 1
        assert result["book"]["schema"] == (
            SECURITY_AUDIT_SCHEMA)
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_securityaudit_records(
                [_sa_fresh_for("S-05")])
        assert len(_sa_records(
            store, session_id, "securityaudit_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_securityaudit_record(_sa_record())
        result = agent.view_securityaudit("S-01")
        assert result["area"]["id"] == "S-01"
        assert result["standing"]["held"] is True
        assert result["record"]["run"] == "audit-2026-11-a"
        assert result["record_news"]["type"] == (
            "securityaudit_standing")
        assert result["held_record_news"]["type"] == (
            "securityaudit_record")
        assert len(_sa_records(
            store, session_id, "securityaudit_record")) == 1
        assert len(_sa_records(
            store, session_id, "securityaudit_standing")) == 1
        result = agent.view_securityaudit("S-02")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_sa_records(
            store, session_id, "securityaudit_standing")) == 2
        agent.close()


class TestSecurityAuditReports:
    def test_prepare_report_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_securityaudit_report(
            "audit-2026-11", "release-1",
            "every area answered",
            "2026-11-13", 1, 11, 12,
            claims=("local_run_ref", "report_ref"))
        assert result["report"]["state"] == "ready"
        assert result["report"]["certified"] is False
        assert result["report"]["inflated"] is False
        assert result["report_news"]["type"] == (
            "securityaudit_verdict")
        assert "every area answered" in result["screen"]
        report = agent.get_securityaudit_report(
            "audit-2026-11")
        assert report.entry == "release-1"
        assert [r.book for r in
                agent.securityaudit_reports()] == [
            "audit-2026-11"]
        assert len(_sa_records(
            store, session_id, "securityaudit_verdict")) == 1
        agent.close()

    def test_report_unshared_state_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared"):
            agent.prepare_securityaudit_report(
                "audit-2026-11", "release-1", "x",
                "2026-11-13", 1, 11, 12,
                claims=("local_run_ref",), state="executed")
        assert agent.securityaudit_reports() == []
        assert _sa_records(
            store, session_id, "securityaudit_verdict") == []
        agent.close()

    def test_duplicate_report_refuses(self, agent):
        agent.prepare_securityaudit_report(
            "audit-2026-11", "release-1",
            "every area answered", "2026-11-13", 1, 11, 12,
            claims=("local_run_ref",))
        with pytest.raises(ValueError, match="audit-2026-11"):
            agent.prepare_securityaudit_report(
                "audit-2026-11", "release-2",
                "a second telling", "2026-11-13", 1, 11, 12,
                claims=("local_run_ref",))
        with pytest.raises(ValueError,
                           match="holds no"):
            agent.get_securityaudit_report("audit-2026-12")


class TestSecurityAuditParseArgs:
    def test_parse_args_well(self):
        assert parse_securityaudit_args("") == (
            "show", None, (), None)
        assert parse_securityaudit_args(None) == (
            "show", None, (), None)
        assert parse_securityaudit_args("areas") == (
            "areas", None, (), None)
        assert parse_securityaudit_args(
            "area S-01") == (
            "area", "S-01", (), None)
        assert parse_securityaudit_args(
            "record S-01") == (
            "record", "S-01", (), None)
        assert parse_securityaudit_args(
            "standing S-03") == (
            "standing", "S-03", (), None)
        assert parse_securityaudit_args("report") == (
            "reports", None, (), None)
        assert parse_securityaudit_args(
            "report audit-2026-11") == (
            "report", "audit-2026-11", (), None)
        assert parse_securityaudit_args("verdict") == (
            "verdict", None, (), None)
        assert parse_securityaudit_args("index") == (
            "index", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "area", "record",
                    "record S-01 extra",
                    "areas now", "standing",
                    "report a b"):
            with pytest.raises(ValueError) as caught:
                parse_securityaudit_args(bad)
            assert str(caught.value) == SECURITYAUDIT_USAGE


class TestSecurityAuditTerminalRoad:
    def test_show_areas_area_record_standing_report_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/securityaudit")
        assert "S-01" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/securityaudit areas")
        assert "permission-profiles" in text
        assert "S-12" in text
        _, _, text = _slash(
            agent, "/securityaudit area S-01")
        assert "permission-profiles" in text
        _, _, text = _slash(
            agent, "/securityaudit record S-01")
        assert "holds no" in text
        _, _, text = _slash(
            agent, "/securityaudit standing S-01")
        assert "S-01:" in text
        assert "open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/securityaudit report")
        assert "none held" in text
        _, _, text = _slash(agent, "/securityaudit verdict")
        assert "Security audit stands open" in text
        agent.register_securityaudit_record(_sa_record())
        _, _, text = _slash(
            agent, "/securityaudit record S-01")
        assert "held as answered" in text
        _, _, text = _slash(
            agent, "/securityaudit standing S-01")
        assert "held as answered" in text
        _, _, text = _slash(agent, "/securityaudit index")
        assert "held as answered" in text
        agent.prepare_securityaudit_report(
            "audit-2026-11", "release-1",
            "every area answered", "2026-11-13", 1, 11, 12,
            claims=("local_run_ref",))
        _, _, text = _slash(
            agent, "/securityaudit report audit-2026-11")
        assert "every area answered" in text
        assert "never inflated" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/securityaudit [show|areas|"
                "area <area>|"
                "record <area>|"
                "standing <area>|"
                "report [<book>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/securityaudit dance party")
        assert text == SECURITYAUDIT_USAGE
        _, _, text = _slash(
            agent, "/securityaudit area guess")
        assert "unknown area" in text


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


def _sa_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestSecurityAuditHandler:
    def test_show_is_default(self, sa_handler, agent):
        sa_handler._handle_securityaudit("")
        assert "S-01" in (
            _sa_published_text(sa_handler))
        assert "permission-profiles" in (
            _sa_published_text(sa_handler))

    def test_area_record_and_verdict(
            self, sa_handler, agent):
        sa_handler._handle_securityaudit(
            "area S-01")
        assert "permission-profiles" in (
            _sa_published_text(sa_handler))
        agent.register_securityaudit_record(_sa_record())
        sa_handler._handle_securityaudit(
            "record S-01")
        assert "held as answered" in (
            _sa_published_text(sa_handler))
        sa_handler._handle_securityaudit("verdict")
        assert "Security audit stands held" in (
            _sa_published_text(sa_handler))

    def test_bad_grammar_is_published(
            self, sa_handler, agent):
        sa_handler._handle_securityaudit("dance party")
        assert SECURITYAUDIT_USAGE in (
            _sa_published_text(sa_handler))
        sa_handler._handle_securityaudit("area guess")
        assert "unknown area" in (
            _sa_published_text(sa_handler))


class TestChatScreenRoutingSecurityAudit:
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
        screen.handle_command("/securityaudit verdict",
                              _FakeLog())
        assert calls == [("/securityaudit", "verdict")]

    def test_chat_screen_help_and_usage_name_the_audit(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/securityaudit[/green] - show the "
                "Security audit (M-260)") in text
        assert ('"/securityaudit": "Usage: '
                "/securityaudit | "
                "/securityaudit areas") in text


class TestSecurityAuditDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.securityaudit_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _SA_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        verdict = agent.securityaudit_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_securityaudit_record(_sa_record())
        agent.register_securityaudit_record(
            _sa_fresh_for("S-05", run="audit-2026-11-b"))
        verdict = agent.securityaudit_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "S-01", "S-05"]
        assert "Security audit stands held" in (
            verdict["verdict_text"])

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_securityaudit()
        assert report["book"]["schema"] == (
            SECURITY_AUDIT_SCHEMA)
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_securityaudit_record(_sa_record())
        report = agent.report_securityaudit()
        assert "held as answered" in report["records_text"]
        assert [s["area"] for s in report["standings"]] == [
            "S-01"]

    def test_records_for_disposition_and_held_keys(self, agent):
        agent.register_securityaudit_record(_sa_record())
        agent.register_securityaudit_record(
            _sa_fresh_for("S-05", run="audit-2026-11-b"))
        agent.register_securityaudit_record(_sa_record(
            area="S-02", run="audit-2026-11-c",
            disposition="ROADED", owner="",
            proof_kind="none",
            stages=["named"], claims=["assertion"]))
        assert [r.run for r in
                agent.records_for_disposition("FIXED")] == [
            "audit-2026-11-a", "audit-2026-11-b"]
        assert agent.securityaudit_held() == ["S-01", "S-05"]
        standing = agent.securityaudit_standing(
            "S-02")
        assert standing.held is False
