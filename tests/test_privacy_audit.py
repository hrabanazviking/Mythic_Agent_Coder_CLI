"""M-261 Privacy audit - pure-layer tests.

TIER: unit

The Part V doctrine + M-118 red-team pack + an
network capture of the sandbox/jail code,
findings clean or roaded with owners: a finding
counts CLEAN only on the audit's own independent
read resting on held local evidence, and a
roaded finding with no owner named stands open.
"""
import pytest

from mythic_agent.core.privacy_audit import (
    SURFACES,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    SurfaceEntry,
    SurfaceRegistry,
    CaptureRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_surface,
    format_surfaces,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(surface="P-03",
                run="bench-2026-11-a",
                date="2026-11-13", disposition="CLEAN",
                owner="yrsa",
                proof_kind="network-capture",
                stages=STAGES,
                claims=("capture_ref", "journal_ref"))
    base.update(kw)
    return CaptureRecord(**base)


def roaded_record(**kw):
    base = dict(surface="P-05",
                run="bench-2026-11-a",
                date="2026-11-13", disposition="ROADED",
                owner="yrsa",
                proof_kind="network-capture",
                stages=STAGES,
                claims=("journal_ref",))
    base.update(kw)
    return CaptureRecord(**base)


def full_book(**overrides):
    records = []
    for surface_id in default_registry().combinations():
        if surface_id in ("P-01", "P-02", "P-03"):
            kw = dict(surface=surface_id, run="bench-2026-11-a",
                      date="2026-11-13", disposition="CLEAN",
                      owner="yrsa",
                      proof_kind="network-capture",
                      stages=STAGES,
                      claims=("capture_ref", "journal_ref"))
        else:
            kw = dict(surface=surface_id, run="bench-2026-11-a",
                      date="2026-11-13", disposition="ROADED",
                      owner="yrsa",
                      proof_kind="network-capture",
                      stages=STAGES,
                      claims=("journal_ref",))
        kw.update(overrides.get(surface_id, {}))
        records.append(CaptureRecord(**kw))
    return records


def test_registry_holds_twelve_surfaces_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "P-01"
    assert reg.ids()[-1] == "P-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_surfaces_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("P-01").doctrine == "M-015"
    assert reg.get("P-01").subject == "telemetry"
    assert reg.get("P-03").subject == "benchmark-run"
    assert reg.get("P-05").subject == "dns-lookups"
    assert reg.get("P-11").doctrine == "M-098"
    assert reg.get("P-11").subject == "plugin-loads"
    assert reg.get("P-12").doctrine == "M-119"
    assert DISPOSITIONS == ("CLEAN", "ROADED")


def test_registry_unknown_surface_refused_by_name():
    with pytest.raises(ValidationError, match="unknown surface: P-99"):
        default_registry().get("P-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate surface"):
        SurfaceRegistry(SURFACES + SURFACES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        SurfaceRegistry([SurfaceEntry("P-01", "M-015", "telemetry", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        SurfaceRegistry([SurfaceEntry("P-01", "M-015", "telemetry", "published", "why")])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown surface doctrine"):
        SurfaceRegistry([SurfaceEntry("P-01", "M-999", "permission-profiles", "listed", "why")])


def test_record_clean_network_capture_stands_held():
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
    assert any("no held capture evidence" in g for g in standing.gaps)


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
    assert any("no capture date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_ready_with_roaded_surfaces():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.clean_surfaces == ("P-01", "P-02", "P-03")
    assert len(verdict.roaded_surfaces) == 9
    assert verdict.missing_surfaces == ()


def test_verdict_missing_surface_stops_the_audit():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_surfaces == ("P-12",)
    assert any("P-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_audit():
    verdict = derive_verdict(full_book(**{"P-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("P-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_surface_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("audit-a", "P-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("capture_ref",))
    assert report.state == "ready"
    shared = prepare_report("audit-a", "P-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("capture_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("audit-a", "P-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("capture_ref",), state="sealed")
    with pytest.raises(ValidationError, match="audit closed"):
        prepare_report("audit-a", "P-01", "findings", "2026-11-13",
                       3, 5, 12, claims=("capture_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("audit-a", "P-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("feeling",))
    assert "P-01" in format_surface(default_registry().get("P-01"))
    assert "P-12" in format_surfaces()
    assert "CLEAN" in format_record(fresh_record())
    assert "ROADED" in format_records([roaded_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)

# ---------------------------------------------------------------------


# ---------------------------------------------------------------------
# M-261 Privacy audit - agent layer. The pure book is held
# by a session registry in the agent layer alone: surfaces are read
# from the shipped registry, capture records are held one by one for
# the session, records, viewed standings and held reports are
# published as session news through the checkpoint road
# (journal-first, deduped per record, standing and verdict),
# standings, the index and the verdict are derived at call time from
# the held records - an surface stands held only when its finding
# counts CLEAN on network-capture evidence resting on held local
# evidence, or stands ROADED with a named owner in the open -
# audit reports are held only as reports, state ready by default,
# may be marked shared by a human, a certification claimed only
# when every surface stands answered, and never inflated, and the
# registry is session state, never a stored setting. This layer
# runs no attack, reads no sandbox code and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    PRIVACYAUDIT_USAGE,
    parse_privacyaudit_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.privacy_audit import (
    PLAIN_EXPLANATION,
    PRIVACY_AUDIT_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_SA_EVENT_TYPES = (
    "privacyaudit_record", "privacyaudit_standing",
    "privacyaudit_verdict")

ALL_SURFACES = ["P-01", "P-02", "P-03", "P-04", "P-05", "P-06",
             "P-07", "P-08", "P-09", "P-10", "P-11", "P-12"]


def _pa_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _pa_record(**overrides):
    raw = {
        "surface": "P-01",
        "run": "bench-2026-11-a",
        "date": "2026-11-13",
        "disposition": "CLEAN",
        "owner": "yrsa",
        "proof_kind": "network-capture",
        "stages": list(STAGES),
        "claims": ["capture_ref", "journal_ref"],
    }
    raw.update(overrides)
    return raw


def _pa_fresh_for(surface, run="bench-2026-11-a"):
    return _pa_record(surface=surface, run=run)


class TestPrivacyAuditAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_areas(
            self, agent):
        status = agent.privacyaudit_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["privacyaudit_book"]["schema"] == (
            PRIVACY_AUDIT_SCHEMA)
        assert [c["id"] for c in status[
            "privacyaudit_book"]["surfaces"]] == ALL_SURFACES
        assert status["privacyaudit_book"]["records"] == []
        assert status["privacyaudit_book"]["reports"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "P-01" in status["surfaces_text"]
        assert "standing listed" in status["surfaces_text"]
        assert "none recorded this session" in status["screen"]
        assert "privacy audit" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == PRIVACYAUDIT_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._privacyaudit_registry()
        assert agent._privacyaudit_registry() is first
        assert agent._privacyaudit_store is first
        for name in ("privacyaudit_surfaces",
                     "privacyaudit_book",
                     "privacyaudit_status",
                     "get_privacyaudit_surface",
                     "get_privacyaudit_record",
                     "privacyaudit_standing",
                     "captures_for_disposition",
                     "privacyaudit_held",
                     "privacyaudit_index",
                     "privacyaudit_verdict",
                     "prepare_privacyaudit_report",
                     "get_privacyaudit_report",
                     "privacyaudit_reports",
                     "report_privacyaudit"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_privacyaudit_registry",
            "privacyaudit_surfaces",
            "privacyaudit_book",
            "privacyaudit_status",
            "get_privacyaudit_surface",
            "get_privacyaudit_record",
            "privacyaudit_standing", "captures_for_disposition",
            "privacyaudit_held", "privacyaudit_index",
            "privacyaudit_verdict",
            "register_privacyaudit_record",
            "register_privacyaudit_records",
            "record_privacyaudit_records",
            "view_privacyaudit",
            "prepare_privacyaudit_report",
            "get_privacyaudit_report",
            "privacyaudit_reports",
            "report_privacyaudit",
            "_publish_privacyaudit_record",
            "_privacyaudit_screen",
            "_privacyaudit_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.privacyaudit_status()
        entry = agent.get_privacyaudit_surface("P-01")
        assert entry.doctrine == "M-015"
        assert entry.subject == "telemetry"
        standing = agent.privacyaudit_standing("P-01")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.grade == "open"
        assert agent.privacyaudit_held() == []
        assert agent.captures_for_disposition("CLEAN") == []
        agent.privacyaudit_index()
        agent.privacyaudit_verdict()
        agent.report_privacyaudit()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _SA_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown surface"):
            agent.get_privacyaudit_surface("guess")
        with pytest.raises(ValueError, match="unknown surface"):
            agent.privacyaudit_standing("guess")
        with pytest.raises(ValueError, match="holds no"):
            agent.get_privacyaudit_record("P-01")
        with pytest.raises(ValueError):
            agent.captures_for_disposition("")
        agent.close()


class TestPrivacyAuditAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_privacyaudit_record(
            _pa_record())
        assert result["record"]["surface"] == "P-01"
        assert result["record_news"]["type"] == (
            "privacyaudit_record")
        assert "held as answered" in result["screen"]
        status = agent.privacyaudit_status()
        assert [r["surface"] for r in status["records"]] == [
            "P-01"]
        assert status["book"]["records"][0]["run"] == (
            "bench-2026-11-a")
        assert status["held"] == ["P-01"]
        assert status["open"] == []
        assert "held as answered" in status["records_text"]
        assert len(_pa_records(
            store, session_id, "privacyaudit_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_privacyaudit_record(_pa_record())
        with pytest.raises(ValueError, match="P-01"):
            agent.register_privacyaudit_record(
                _pa_record(run="bench-2026-11-b"))
        assert len(_pa_records(
            store, session_id, "privacyaudit_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_privacyaudit_record(
                _pa_record(claims=["vibes"]))
        assert agent.privacyaudit_status()["records"] == []
        assert _pa_records(
            store, session_id, "privacyaudit_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_privacyaudit_records([
            _pa_fresh_for("P-05"), _pa_record()])
        assert result["count"] == 2
        assert [r["surface"] for r in result["records_news"]] == [
            "P-05", "P-01"]
        assert len(_pa_records(
            store, session_id, "privacyaudit_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_privacyaudit_records(
            [_pa_fresh_for("P-05")])
        assert result["count"] == 1
        assert result["book"]["schema"] == (
            PRIVACY_AUDIT_SCHEMA)
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_privacyaudit_records(
                [_pa_fresh_for("P-05")])
        assert len(_pa_records(
            store, session_id, "privacyaudit_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_privacyaudit_record(_pa_record())
        result = agent.view_privacyaudit("P-01")
        assert result["surface"]["id"] == "P-01"
        assert result["standing"]["held"] is True
        assert result["record"]["run"] == "bench-2026-11-a"
        assert result["record_news"]["type"] == (
            "privacyaudit_standing")
        assert result["held_record_news"]["type"] == (
            "privacyaudit_record")
        assert len(_pa_records(
            store, session_id, "privacyaudit_record")) == 1
        assert len(_pa_records(
            store, session_id, "privacyaudit_standing")) == 1
        result = agent.view_privacyaudit("P-02")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_pa_records(
            store, session_id, "privacyaudit_standing")) == 2
        agent.close()


class TestPrivacyPrivacyReports:
    def test_prepare_report_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_privacyaudit_report(
            "bench-2026-11", "release-1",
            "every surface answered",
            "2026-11-13", 1, 11, 12,
            claims=("local_run_ref", "journal_ref"))
        assert result["report"]["state"] == "ready"
        assert result["report"]["certified"] is False
        assert result["report"]["inflated"] is False
        assert result["report_news"]["type"] == (
            "privacyaudit_verdict")
        assert "every surface answered" in result["screen"]
        report = agent.get_privacyaudit_report(
            "bench-2026-11")
        assert report.entry == "release-1"
        assert [r.book for r in
                agent.privacyaudit_reports()] == [
            "bench-2026-11"]
        assert len(_pa_records(
            store, session_id, "privacyaudit_verdict")) == 1
        agent.close()

    def test_report_unshared_state_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared"):
            agent.prepare_privacyaudit_report(
                "bench-2026-11", "release-1", "x",
                "2026-11-13", 1, 11, 12,
                claims=("local_run_ref",), state="executed")
        assert agent.privacyaudit_reports() == []
        assert _pa_records(
            store, session_id, "privacyaudit_verdict") == []
        agent.close()

    def test_duplicate_report_refuses(self, agent):
        agent.prepare_privacyaudit_report(
            "bench-2026-11", "release-1",
            "every surface answered", "2026-11-13", 1, 11, 12,
            claims=("local_run_ref",))
        with pytest.raises(ValueError, match="bench-2026-11"):
            agent.prepare_privacyaudit_report(
                "bench-2026-11", "release-2",
                "a second telling", "2026-11-13", 1, 11, 12,
                claims=("local_run_ref",))
        with pytest.raises(ValueError,
                           match="holds no"):
            agent.get_privacyaudit_report("audit-2026-12")


class TestPrivacyAuditParseArgs:
    def test_parse_args_well(self):
        assert parse_privacyaudit_args("") == (
            "show", None, (), None)
        assert parse_privacyaudit_args(None) == (
            "show", None, (), None)
        assert parse_privacyaudit_args("surfaces") == (
            "surfaces", None, (), None)
        assert parse_privacyaudit_args(
            "surface P-01") == (
            "surface", "P-01", (), None)
        assert parse_privacyaudit_args(
            "record P-01") == (
            "record", "P-01", (), None)
        assert parse_privacyaudit_args(
            "standing P-03") == (
            "standing", "P-03", (), None)
        assert parse_privacyaudit_args("report") == (
            "reports", None, (), None)
        assert parse_privacyaudit_args(
            "report bench-2026-11") == (
            "report", "bench-2026-11", (), None)
        assert parse_privacyaudit_args("verdict") == (
            "verdict", None, (), None)
        assert parse_privacyaudit_args("index") == (
            "index", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "surface", "record",
                    "record P-01 extra",
                    "surfaces now", "standing",
                    "report a b"):
            with pytest.raises(ValueError) as caught:
                parse_privacyaudit_args(bad)
            assert str(caught.value) == PRIVACYAUDIT_USAGE


class TestPrivacyAuditTerminalRoad:
    def test_show_areas_area_record_standing_report_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/privacyaudit")
        assert "P-01" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/privacyaudit surfaces")
        assert "telemetry" in text
        assert "P-12" in text
        _, _, text = _slash(
            agent, "/privacyaudit surface P-01")
        assert "telemetry" in text
        _, _, text = _slash(
            agent, "/privacyaudit record P-01")
        assert "holds no" in text
        _, _, text = _slash(
            agent, "/privacyaudit standing P-01")
        assert "P-01:" in text
        assert "open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/privacyaudit report")
        assert "none held" in text
        _, _, text = _slash(agent, "/privacyaudit verdict")
        assert "Privacy audit stands open" in text
        agent.register_privacyaudit_record(_pa_record())
        _, _, text = _slash(
            agent, "/privacyaudit record P-01")
        assert "held as answered" in text
        _, _, text = _slash(
            agent, "/privacyaudit standing P-01")
        assert "held as answered" in text
        _, _, text = _slash(agent, "/privacyaudit index")
        assert "held as answered" in text
        agent.prepare_privacyaudit_report(
            "bench-2026-11", "release-1",
            "every surface answered", "2026-11-13", 1, 11, 12,
            claims=("local_run_ref",))
        _, _, text = _slash(
            agent, "/privacyaudit report bench-2026-11")
        assert "every surface answered" in text
        assert "never inflated" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/privacyaudit [show|surfaces|"
                "surface <surface>|"
                "record <surface>|"
                "standing <surface>|"
                "report [<book>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/privacyaudit dance party")
        assert text == PRIVACYAUDIT_USAGE
        _, _, text = _slash(
            agent, "/privacyaudit surface guess")
        assert "unknown surface" in text


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


def _pa_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestPrivacyAuditHandler:
    def test_show_is_default(self, sa_handler, agent):
        sa_handler._handle_privacyaudit("")
        assert "P-01" in (
            _pa_published_text(sa_handler))
        assert "telemetry" in (
            _pa_published_text(sa_handler))

    def test_area_record_and_verdict(
            self, sa_handler, agent):
        sa_handler._handle_privacyaudit(
            "surface P-01")
        assert "telemetry" in (
            _pa_published_text(sa_handler))
        agent.register_privacyaudit_record(_pa_record())
        sa_handler._handle_privacyaudit(
            "record P-01")
        assert "held as answered" in (
            _pa_published_text(sa_handler))
        sa_handler._handle_privacyaudit("verdict")
        assert "Privacy audit stands held" in (
            _pa_published_text(sa_handler))

    def test_bad_grammar_is_published(
            self, sa_handler, agent):
        sa_handler._handle_privacyaudit("dance party")
        assert PRIVACYAUDIT_USAGE in (
            _pa_published_text(sa_handler))
        sa_handler._handle_privacyaudit("surface guess")
        assert "unknown surface" in (
            _pa_published_text(sa_handler))


class TestChatScreenRoutingPrivacyAudit:
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
        screen.handle_command("/privacyaudit verdict",
                              _FakeLog())
        assert calls == [("/privacyaudit", "verdict")]

    def test_chat_screen_help_and_usage_name_the_audit(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/privacyaudit[/green] - show the "
                "Privacy audit (M-261)") in text
        assert ('"/privacyaudit": "Usage: '
                "/privacyaudit | "
                "/privacyaudit surfaces") in text


class TestPrivacyAuditDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.privacyaudit_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _SA_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        verdict = agent.privacyaudit_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_privacyaudit_record(_pa_record())
        agent.register_privacyaudit_record(
            _pa_fresh_for("P-05", run="bench-2026-11-b"))
        verdict = agent.privacyaudit_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "P-01", "P-05"]
        assert "Privacy audit stands held" in (
            verdict["verdict_text"])

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_privacyaudit()
        assert report["book"]["schema"] == (
            PRIVACY_AUDIT_SCHEMA)
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_privacyaudit_record(_pa_record())
        report = agent.report_privacyaudit()
        assert "held as answered" in report["records_text"]
        assert [s["surface"] for s in report["standings"]] == [
            "P-01"]

    def test_captures_for_disposition_and_held_keys(self, agent):
        agent.register_privacyaudit_record(_pa_record())
        agent.register_privacyaudit_record(
            _pa_fresh_for("P-05", run="bench-2026-11-b"))
        agent.register_privacyaudit_record(_pa_record(
            surface="P-02", run="bench-2026-11-c",
            disposition="ROADED", owner="",
            proof_kind="none",
            stages=["named"], claims=["assertion"]))
        assert [r.run for r in
                agent.captures_for_disposition("CLEAN")] == [
            "bench-2026-11-a", "bench-2026-11-b"]
        assert agent.privacyaudit_held() == ["P-01", "P-05"]
        standing = agent.privacyaudit_standing(
            "P-02")
        assert standing.held is False
