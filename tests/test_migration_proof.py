"""M-265 Migration proof - pure-layer tests.

TIER: unit

A workspace from the current release opens in the new
one - sessions, journals, configs, memories intact: an
area counts PROVEN only on the old workspace actually
opening in the new release resting on held workspace
evidence, and a roaded area with no owner named stands
open.
"""
import pytest

from mythic_agent.core.migration_proof import (
    AREAS,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    MigrationEntry,
    MigrationRegistry,
    MigrationRecord,
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
    base = dict(area="G-03",
                work="migration-2026-11-a",
                date="2026-11-13", disposition="PROVEN",
                owner="yrsa",
                proof_kind="opened-in-new-release",
                stages=STAGES,
                claims=("workspace_ref", "journal_ref"))
    base.update(kw)
    return MigrationRecord(**base)


def roaded_record(**kw):
    base = dict(area="G-05",
                work="migration-2026-11-a",
                date="2026-11-13", disposition="ROADED",
                owner="yrsa",
                proof_kind="opened-in-new-release",
                stages=STAGES,
                claims=("journal_ref",))
    base.update(kw)
    return MigrationRecord(**base)


def full_book(**overrides):
    records = []
    for area_id in default_registry().combinations():
        if area_id in ("G-01", "G-02", "G-03"):
            kw = dict(area=area_id, work="migration-2026-11-a",
                      date="2026-11-13", disposition="PROVEN",
                      owner="yrsa",
                      proof_kind="opened-in-new-release",
                      stages=STAGES,
                      claims=("workspace_ref", "journal_ref"))
        else:
            kw = dict(area=area_id, work="migration-2026-11-a",
                      date="2026-11-13", disposition="ROADED",
                      owner="yrsa",
                      proof_kind="opened-in-new-release",
                      stages=STAGES,
                      claims=("journal_ref",))
        kw.update(overrides.get(area_id, {}))
        records.append(MigrationRecord(**kw))
    return records


def test_registry_holds_twelve_areas_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "G-01"
    assert reg.ids()[-1] == "G-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_areas_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("G-01").doctrine == "forward-compat"
    assert reg.get("G-01").subject == "session-store"
    assert reg.get("G-02").subject == "journal-store"
    assert reg.get("G-03").subject == "config-store"
    assert reg.get("G-04").subject == "memory-store"
    assert reg.get("G-11").doctrine == "standing-law"
    assert reg.get("G-11").subject == "key-vault-refs"
    assert reg.get("G-12").doctrine == "proof-duty"
    assert DISPOSITIONS == ("PROVEN", "ROADED")


def test_registry_unknown_area_refused_by_name():
    with pytest.raises(ValidationError, match="unknown area: G-99"):
        default_registry().get("G-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate area"):
        MigrationRegistry(AREAS + AREAS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        MigrationRegistry([MigrationEntry("G-01", "forward-compat", "session-store", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        MigrationRegistry([MigrationEntry("G-01", "forward-compat", "session-store", "published", "why")])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown area doctrine"):
        MigrationRegistry([MigrationEntry("G-01", "M-999", "session-store", "listed", "why")])


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


def test_record_proven_on_historical_evidence_stands_open():
    standing = derive_standing(fresh_record(proof_kind="historical-only"))
    assert not standing.held
    assert any("no inheritance" in g for g in standing.gaps)


def test_record_proven_without_workspace_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("journal_ref",)))
    assert not standing.held
    assert any("no held workspace evidence" in g for g in standing.gaps)


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
    assert any("no migration date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_ready_with_roaded_areas():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.proven_areas == ("G-01", "G-02", "G-03")
    assert len(verdict.roaded_areas) == 9
    assert verdict.missing_areas == ()


def test_verdict_missing_area_stops_the_migration():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_areas == ("G-12",)
    assert any("G-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_migration():
    verdict = derive_verdict(full_book(**{"G-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("G-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_area_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("migration-a", "G-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("workspace_ref",))
    assert report.state == "ready"
    shared = prepare_report("migration-a", "G-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("workspace_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("migration-a", "G-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("workspace_ref",), state="sealed")
    with pytest.raises(ValidationError, match="migration complete"):
        prepare_report("migration-a", "G-01", "findings", "2026-11-13",
                       3, 5, 12, claims=("workspace_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("migration-a", "G-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("feeling",))
    assert "G-01" in format_area(default_registry().get("G-01"))
    assert "G-12" in format_areas()
    assert "PROVEN" in format_record(fresh_record())
    assert "ROADED" in format_records([roaded_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
    from pathlib import Path as _P
    _src = (_P(__file__).resolve().parent.parent
            / "mythic_agent" / "core" / "migration_proof.py").read_text(
                encoding="utf-8")
    assert "open(" not in _src
    assert "socket" not in _src
    assert "subprocess" not in _src
    assert "urllib" not in _src

# ---------------------------------------------------------------------


# ---------------------------------------------------------------------
# M-265 Migration proof - agent layer. The pure book is held
# by a session registry in the agent layer alone: areas are read
# from the shipped registry, capture records are held one by one for
# the session, records, viewed standings and held reports are
# published as session news through the checkpoint road
# (journal-first, deduped per record, standing and verdict),
# standings, the index and the verdict are derived at call time from
# the held records - an area stands held only when its finding
# counts PROVEN on opened-in-new-release evidence resting on held local
# evidence, or stands ROADED with a named owner in the open -
# audit reports are held only as reports, state ready by default,
# may be marked shared by a human, a certification claimed only
# when every area stands answered, and never inflated, and the
# registry is session state, never a stored setting. This layer
# runs no attack, reads no sandbox code and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    MIGRATIONPROOF_USAGE,
    parse_migrationproof_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.migration_proof import (
    PLAIN_EXPLANATION,
    MIGRATION_PROOF_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_MP_EVENT_TYPES = (
    "migrationproof_record", "migrationproof_standing",
    "migrationproof_verdict")

ALL_AREAS = ["G-01", "G-02", "G-03", "G-04", "G-05", "G-06",
             "G-07", "G-08", "G-09", "G-10", "G-11", "G-12"]


def _mp_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _mp_record(**overrides):
    raw = {
        "area": "G-01",
        "work": "migration-2026-11-a",
        "date": "2026-11-13",
        "disposition": "PROVEN",
        "owner": "yrsa",
        "proof_kind": "opened-in-new-release",
        "stages": list(STAGES),
        "claims": ["workspace_ref", "journal_ref"],
    }
    raw.update(overrides)
    return raw


def _mp_fresh_for(area, work="migration-2026-11-a"):
    return _mp_record(area=area, work=work)


class TestMigrationProofAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_areas(
            self, agent):
        status = agent.migrationproof_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["migrationproof_book"]["schema"] == (
            MIGRATION_PROOF_SCHEMA)
        assert [c["id"] for c in status[
            "migrationproof_book"]["areas"]] == ALL_AREAS
        assert status["migrationproof_book"]["records"] == []
        assert status["migrationproof_book"]["reports"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "G-01" in status["areas_text"]
        assert "standing listed" in status["areas_text"]
        assert "none recorded this session" in status["screen"]
        assert "Migration proof" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == MIGRATIONPROOF_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._migrationproof_registry()
        assert agent._migrationproof_registry() is first
        assert agent._migrationproof_store is first
        for name in ("migrationproof_areas",
                     "migrationproof_book",
                     "migrationproof_status",
                     "get_migrationproof_area",
                     "get_migrationproof_record",
                     "migrationproof_standing",
                     "areas_for_disposition",
                     "migrationproof_held",
                     "migrationproof_index",
                     "migrationproof_verdict",
                     "prepare_migrationproof_report",
                     "get_migrationproof_report",
                     "migrationproof_reports",
                     "report_migrationproof"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_migrationproof_registry",
            "migrationproof_areas",
            "migrationproof_book",
            "migrationproof_status",
            "get_migrationproof_area",
            "get_migrationproof_record",
            "migrationproof_standing", "areas_for_disposition",
            "migrationproof_held", "migrationproof_index",
            "migrationproof_verdict",
            "register_migrationproof_record",
            "register_migrationproof_records",
            "record_migrationproof_records",
            "view_migrationproof",
            "prepare_migrationproof_report",
            "get_migrationproof_report",
            "migrationproof_reports",
            "report_migrationproof",
            "_publish_migrationproof_record",
            "_migrationproof_screen",
            "_migrationproof_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.migrationproof_status()
        entry = agent.get_migrationproof_area("G-01")
        assert entry.doctrine == "forward-compat"
        assert entry.subject == "session-store"
        standing = agent.migrationproof_standing("G-01")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.grade == "open"
        assert agent.migrationproof_held() == []
        assert agent.areas_for_disposition("PROVEN") == []
        agent.migrationproof_index()
        agent.migrationproof_verdict()
        agent.report_migrationproof()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _MP_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown area"):
            agent.get_migrationproof_area("guess")
        with pytest.raises(ValueError, match="unknown area"):
            agent.migrationproof_standing("guess")
        with pytest.raises(ValueError, match="holds no"):
            agent.get_migrationproof_record("G-01")
        with pytest.raises(ValueError):
            agent.areas_for_disposition("")
        agent.close()


class TestMigrationProofAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_migrationproof_record(
            _mp_record())
        assert result["record"]["area"] == "G-01"
        assert result["record_news"]["type"] == (
            "migrationproof_record")
        assert "held as answered" in result["screen"]
        status = agent.migrationproof_status()
        assert [r["area"] for r in status["records"]] == [
            "G-01"]
        assert status["book"]["records"][0]["work"] == (
            "migration-2026-11-a")
        assert status["held"] == ["G-01"]
        assert status["open"] == []
        assert "held as answered" in status["records_text"]
        assert len(_mp_records(
            store, session_id, "migrationproof_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_migrationproof_record(_mp_record())
        with pytest.raises(ValueError, match="G-01"):
            agent.register_migrationproof_record(
                _mp_record(work="migration-2026-11-b"))
        assert len(_mp_records(
            store, session_id, "migrationproof_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_migrationproof_record(
                _mp_record(claims=["vibes"]))
        assert agent.migrationproof_status()["records"] == []
        assert _mp_records(
            store, session_id, "migrationproof_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_migrationproof_records([
            _mp_fresh_for("G-05"), _mp_record()])
        assert result["count"] == 2
        assert [r["area"] for r in result["records_news"]] == [
            "G-05", "G-01"]
        assert len(_mp_records(
            store, session_id, "migrationproof_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_migrationproof_records(
            [_mp_fresh_for("G-05")])
        assert result["count"] == 1
        assert result["book"]["schema"] == (
            MIGRATION_PROOF_SCHEMA)
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_migrationproof_records(
                [_mp_fresh_for("G-05")])
        assert len(_mp_records(
            store, session_id, "migrationproof_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_migrationproof_record(_mp_record())
        result = agent.view_migrationproof("G-01")
        assert result["area"]["id"] == "G-01"
        assert result["standing"]["held"] is True
        assert result["record"]["work"] == "migration-2026-11-a"
        assert result["record_news"]["type"] == (
            "migrationproof_standing")
        assert result["held_record_news"]["type"] == (
            "migrationproof_record")
        assert len(_mp_records(
            store, session_id, "migrationproof_record")) == 1
        assert len(_mp_records(
            store, session_id, "migrationproof_standing")) == 1
        result = agent.view_migrationproof("G-02")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_mp_records(
            store, session_id, "migrationproof_standing")) == 2
        agent.close()


class TestMigrationProofReports:
    def test_prepare_report_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_migrationproof_report(
            "migration-2026-11", "release-1",
            "every area answered",
            "2026-11-13", 1, 11, 12,
            claims=("local_run_ref", "journal_ref"))
        assert result["report"]["state"] == "ready"
        assert result["report"]["certified"] is False
        assert result["report"]["inflated"] is False
        assert result["report_news"]["type"] == (
            "migrationproof_verdict")
        assert "every area answered" in result["screen"]
        report = agent.get_migrationproof_report(
            "migration-2026-11")
        assert report.entry == "release-1"
        assert [r.book for r in
                agent.migrationproof_reports()] == [
            "migration-2026-11"]
        assert len(_mp_records(
            store, session_id, "migrationproof_verdict")) == 1
        agent.close()

    def test_report_unshared_state_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared"):
            agent.prepare_migrationproof_report(
                "migration-2026-11", "release-1", "x",
                "2026-11-13", 1, 11, 12,
                claims=("local_run_ref",), state="executed")
        assert agent.migrationproof_reports() == []
        assert _mp_records(
            store, session_id, "migrationproof_verdict") == []
        agent.close()

    def test_duplicate_report_refuses(self, agent):
        agent.prepare_migrationproof_report(
            "migration-2026-11", "release-1",
            "every area answered", "2026-11-13", 1, 11, 12,
            claims=("local_run_ref",))
        with pytest.raises(ValueError, match="migration-2026-11"):
            agent.prepare_migrationproof_report(
                "migration-2026-11", "release-2",
                "a second telling", "2026-11-13", 1, 11, 12,
                claims=("local_run_ref",))
        with pytest.raises(ValueError,
                           match="holds no"):
            agent.get_migrationproof_report("migration-2026-12")


class TestMigrationProofParseArgs:
    def test_parse_args_well(self):
        assert parse_migrationproof_args("") == (
            "show", None, (), None)
        assert parse_migrationproof_args(None) == (
            "show", None, (), None)
        assert parse_migrationproof_args("areas") == (
            "areas", None, (), None)
        assert parse_migrationproof_args(
            "area G-01") == (
            "area", "G-01", (), None)
        assert parse_migrationproof_args(
            "record G-01") == (
            "record", "G-01", (), None)
        assert parse_migrationproof_args(
            "standing G-03") == (
            "standing", "G-03", (), None)
        assert parse_migrationproof_args("report") == (
            "reports", None, (), None)
        assert parse_migrationproof_args(
            "report migration-2026-11") == (
            "report", "migration-2026-11", (), None)
        assert parse_migrationproof_args("verdict") == (
            "verdict", None, (), None)
        assert parse_migrationproof_args("index") == (
            "index", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "area", "record",
                    "record G-01 extra",
                    "areas now", "standing",
                    "report a b"):
            with pytest.raises(ValueError) as caught:
                parse_migrationproof_args(bad)
            assert str(caught.value) == MIGRATIONPROOF_USAGE


class TestMigrationProofTerminalRoad:
    def test_show_areas_area_record_standing_report_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/migrationproof")
        assert "G-01" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/migrationproof areas")
        assert "session-store" in text
        assert "G-12" in text
        _, _, text = _slash(
            agent, "/migrationproof area G-01")
        assert "session-store" in text
        _, _, text = _slash(
            agent, "/migrationproof record G-01")
        assert "holds no" in text
        _, _, text = _slash(
            agent, "/migrationproof standing G-01")
        assert "G-01:" in text
        assert "open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/migrationproof report")
        assert "none held" in text
        _, _, text = _slash(agent, "/migrationproof verdict")
        assert "Migration proof stands open" in text
        agent.register_migrationproof_record(_mp_record())
        _, _, text = _slash(
            agent, "/migrationproof record G-01")
        assert "held as answered" in text
        _, _, text = _slash(
            agent, "/migrationproof standing G-01")
        assert "held as answered" in text
        _, _, text = _slash(agent, "/migrationproof index")
        assert "held as answered" in text
        agent.prepare_migrationproof_report(
            "migration-2026-11", "release-1",
            "every area answered", "2026-11-13", 1, 11, 12,
            claims=("local_run_ref",))
        _, _, text = _slash(
            agent, "/migrationproof report migration-2026-11")
        assert "every area answered" in text
        assert "never inflated" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/migrationproof [show|areas|"
                "area <area>|"
                "record <area>|"
                "standing <area>|"
                "report [<book>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/migrationproof dance party")
        assert text == MIGRATIONPROOF_USAGE
        _, _, text = _slash(
            agent, "/migrationproof area guess")
        assert "unknown area" in text


@pytest.fixture()
def mp_handler(agent, monkeypatch):
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


def _mp_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestMigrationProofHandler:
    def test_show_is_default(self, mp_handler, agent):
        mp_handler._handle_migrationproof("")
        assert "G-01" in (
            _mp_published_text(mp_handler))
        assert "session-store" in (
            _mp_published_text(mp_handler))

    def test_area_record_and_verdict(
            self, mp_handler, agent):
        mp_handler._handle_migrationproof(
            "area G-01")
        assert "session-store" in (
            _mp_published_text(mp_handler))
        agent.register_migrationproof_record(_mp_record())
        mp_handler._handle_migrationproof(
            "record G-01")
        assert "held as answered" in (
            _mp_published_text(mp_handler))
        mp_handler._handle_migrationproof("verdict")
        assert "Migration proof stands held" in (
            _mp_published_text(mp_handler))

    def test_bad_grammar_is_published(
            self, mp_handler, agent):
        mp_handler._handle_migrationproof("dance party")
        assert MIGRATIONPROOF_USAGE in (
            _mp_published_text(mp_handler))
        mp_handler._handle_migrationproof("area guess")
        assert "unknown area" in (
            _mp_published_text(mp_handler))


class TestChatScreenRoutingMigrationProof:
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
        screen.handle_command("/migrationproof verdict",
                              _FakeLog())
        assert calls == [("/migrationproof", "verdict")]

    def test_chat_screen_help_and_usage_name_the_audit(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/migrationproof[/green] - show the "
                "Migration proof (M-265)") in text
        assert ('"/migrationproof": "Usage: '
                "/migrationproof | "
                "/migrationproof areas") in text


class TestMigrationProofDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.migrationproof_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _MP_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        _rp = ROOT / "README.md"
        _rb = _rp.read_bytes() if _rp.exists() else None
        verdict = agent.migrationproof_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_migrationproof_record(_mp_record())
        agent.register_migrationproof_record(
            _mp_fresh_for("G-05", work="migration-2026-11-b"))
        verdict = agent.migrationproof_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "G-01", "G-05"]
        assert "Migration proof stands held" in (
            verdict["verdict_text"])
        assert not _rp.exists() or _rp.read_bytes() == _rb

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_migrationproof()
        assert report["book"]["schema"] == (
            MIGRATION_PROOF_SCHEMA)
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_migrationproof_record(_mp_record())
        report = agent.report_migrationproof()
        assert "held as answered" in report["records_text"]
        assert [s["area"] for s in report["standings"]] == [
            "G-01"]

    def test_areas_for_disposition_and_held_keys(self, agent):
        agent.register_migrationproof_record(_mp_record())
        agent.register_migrationproof_record(
            _mp_fresh_for("G-05", work="migration-2026-11-b"))
        agent.register_migrationproof_record(_mp_record(
            area="G-02", work="migration-2026-11-c",
            disposition="ROADED", owner="",
            proof_kind="none",
            stages=["named"], claims=["assertion"]))
        assert [r.work for r in
                agent.areas_for_disposition("PROVEN")] == [
            "migration-2026-11-a", "migration-2026-11-b"]
        assert agent.migrationproof_held() == ["G-01", "G-05"]
        standing = agent.migrationproof_standing(
            "G-02")
        assert standing.held is False
