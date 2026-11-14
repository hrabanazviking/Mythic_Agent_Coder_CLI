"""M-272 Final report to Volmarr - pure-layer tests.

TIER: unit

The final report, plain language first - what the coder can
now do, where it beats the field, where it does not yet -
with the evidence index: a section counts PROVEN only on
held proof measured in the campaign itself resting on held
evidence in the index, a partial section only where the
proven part rests on held evidence and its owner is named,
and a not proven section only with its owner and reason
recorded - a not proven section admitted in the open is
honest.
"""
import pytest

from mythic_agent.core.final_report import (
    FINAL_REPORT_ENTRIES,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    FinalReportEntry,
    FinalReportRegistry,
    FinalReportRecord,
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
    base = dict(section="F-03",
                work="report-2026-11-a",
                date="2026-11-13", disposition="PROVEN",
                owner="yrsa",
                proof_kind="proven-and-held",
                stages=STAGES,
                claims=("evidence_ref", "test_ref"))
    base.update(kw)
    return FinalReportRecord(**base)


def partial_record(**kw):
    base = dict(section="F-05",
                work="report-2026-11-a",
                date="2026-11-13", disposition="PARTIAL",
                owner="yrsa",
                proof_kind="partially-held",
                stages=STAGES,
                claims=("test_ref",))
    base.update(kw)
    return FinalReportRecord(**base)


def not_proven_record(**kw):
    base = dict(section="F-07",
                work="report-2026-11-a",
                date="2026-11-13", disposition="NOT_PROVEN",
                owner="yrsa",
                proof_kind="none",
                stages=STAGES,
                claims=("test_ref",))
    base.update(kw)
    return FinalReportRecord(**base)


def full_book(**overrides):
    records = []
    for section_id in default_registry().combinations():
        if section_id in ("F-01", "F-02", "F-03"):
            kw = dict(section=section_id, work="report-2026-11-a",
                      date="2026-11-13", disposition="PROVEN",
                      owner="yrsa",
                      proof_kind="proven-and-held",
                      stages=STAGES,
                      claims=("evidence_ref", "test_ref"))
        elif section_id in ("F-04", "F-05", "F-06", "F-07"):
            kw = dict(section=section_id, work="report-2026-11-a",
                      date="2026-11-13", disposition="PARTIAL",
                      owner="yrsa",
                      proof_kind="partially-held",
                      stages=STAGES,
                      claims=("test_ref",))
        else:
            kw = dict(section=section_id, work="report-2026-11-a",
                      date="2026-11-13", disposition="NOT_PROVEN",
                      owner="yrsa",
                      proof_kind="none",
                      stages=STAGES,
                      claims=("test_ref",))
        kw.update(overrides.get(section_id, {}))
        records.append(FinalReportRecord(**kw))
    return records


def test_registry_holds_twelve_sections_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "F-01"
    assert reg.ids()[-1] == "F-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_sections_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("F-01").doctrine == "plain-language"
    assert reg.get("F-01").subject == "what-it-can-do"
    assert reg.get("F-02").subject == "provider-ocean"
    assert reg.get("F-03").subject == "code-intelligence"
    assert reg.get("F-04").subject == "editors-hand"
    assert reg.get("F-11").doctrine == "field-honesty"
    assert reg.get("F-11").subject == "where-it-falls-short"
    assert reg.get("F-12").doctrine == "report-duty"
    assert DISPOSITIONS == ("PROVEN", "PARTIAL", "NOT_PROVEN")


def test_registry_unknown_section_refused_by_name():
    with pytest.raises(ValidationError, match="unknown section: C-99"):
        default_registry().get("C-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate section"):
        FinalReportRegistry(FINAL_REPORT_ENTRIES + FINAL_REPORT_ENTRIES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        FinalReportRegistry([FinalReportEntry("F-01", "plain-language", "what-it-can-do", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        FinalReportRegistry([FinalReportEntry("F-01", "plain-language", "what-it-can-do", "published", "why")])
    with pytest.raises(ValidationError, match="labelled"):
        FinalReportRegistry([FinalReportEntry("F-01", "plain-language", "what-it-can-do", "listed", "why", labelled=False)])
    with pytest.raises(ValidationError, match="evidenced"):
        FinalReportRegistry([FinalReportEntry("F-01", "plain-language", "what-it-can-do", "listed", "why", evidenced=False)])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown section doctrine"):
        FinalReportRegistry([FinalReportEntry("F-01", "M-999", "what-it-can-do", "listed", "why")])


def test_record_proven_measured_and_held_stands_held():
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


def test_record_proven_on_partial_proof_stands_open():
    standing = derive_standing(fresh_record(proof_kind="partially-held"))
    assert not standing.held
    assert any("tells the truth" in g for g in standing.gaps)


def test_record_proven_without_evidence_ref_stands_open():
    standing = derive_standing(fresh_record(claims=("test_ref",)))
    assert not standing.held
    assert any("no held" in g for g in standing.gaps)


def test_record_proven_on_bare_claims_stands_open():
    standing = derive_standing(fresh_record(claims=("feeling",)))
    assert not standing.held
    assert any("bare claims only" in g for g in standing.gaps)


def test_record_partial_with_owner_stands_held():
    standing = derive_standing(partial_record())
    assert standing.held
    assert standing.grade == "held"


def test_record_partial_without_owner_stands_open():
    standing = derive_standing(partial_record(owner=""))
    assert not standing.held
    assert any("not a road" in g for g in standing.gaps)


def test_record_not_proven_silent_stands_open():
    standing = derive_standing(not_proven_record(claims=()))
    assert not standing.held
    assert any("silent" in g for g in standing.gaps)


def test_record_without_date_stands_open():
    standing = derive_standing(fresh_record(date=""))
    assert not standing.held
    assert any("no report date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_proven_with_partial_sections():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.proven_sections == ("F-01", "F-02", "F-03")
    assert len(verdict.partial_sections) == 4
    assert len(verdict.not_proven_sections) == 5
    assert verdict.missing_sections == ()


def test_verdict_missing_section_stops_the_report():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_sections == ("F-12",)
    assert any("F-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_report():
    verdict = derive_verdict(full_book(**{"F-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("F-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_section_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two records" in g for g in verdict.gaps)


def test_report_proven_and_shared_states():
    report = prepare_report("report-a", "F-01", "sections as dispositioned",
                            "2026-11-13", 3, 4, 5, 12,
                            claims=("evidence_ref",))
    assert report.state == "ready"
    shared = prepare_report("report-a", "F-01", "sections as dispositioned",
                            "2026-11-13", 3, 4, 5, 12,
                            claims=("evidence_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("report-a", "F-01", "sections", "2026-11-13",
                       3, 4, 5, 12, claims=("evidence_ref",), state="sealed")
    with pytest.raises(ValidationError, match="report complete"):
        prepare_report("report-a", "F-01", "sections", "2026-11-13",
                       3, 2, 2, 12, claims=("evidence_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("report-a", "F-01", "sections", "2026-11-13",
                       3, 4, 5, 12, claims=("feeling",))
    assert "F-01" in format_entry(default_registry().get("F-01"))
    assert "F-12" in format_entries()
    assert "PROVEN" in format_record(fresh_record())
    assert "PARTIAL" in format_records([partial_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
    from pathlib import Path as _P
    _src = (_P(__file__).resolve().parent.parent
            / "mythic_agent" / "core" / "final_report.py").read_text(
                encoding="utf-8")
    assert "open(" not in _src
    assert "socket" not in _src
    assert "subprocess" not in _src
    assert "urllib" not in _src


# ---------------------------------------------------------------------
# M-272 Final report - agent layer. The pure book is held
# by a session registry in the agent layer alone: sections are read
# from the shipped registry, capture records are held one by one for
# the session, records, viewed standings and held reports are
# published as session news through the checkpoint road
# (journal-first, deduped per record, standing and verdict),
# standings, the index and the verdict are derived at call time from
# the held records - an section stands held only when its finding
# counts PROVEN on proven-and-held evidence resting on held local
# evidence, or stands PARTIAL or NOT PROVEN with a named owner in the open -
# report reports are held only as reports, state ready by default,
# may be marked shared by a human, a certification claimed only
# when every section stands answered, and never inflated, and the
# registry is session state, never a stored setting. This layer
# runs no attack, reads no sandbox code and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    FINALREPORT_USAGE,
    parse_finalreport_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.final_report import (
    PLAIN_EXPLANATION,
    FINAL_REPORT_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_FR_EVENT_TYPES = (
    "finalreport_record", "finalreport_standing",
    "finalreport_verdict")

ALL_FAMILIES = ["F-01", "F-02", "F-03", "F-04", "F-05", "F-06",
             "F-07", "F-08", "F-09", "F-10", "F-11", "F-12"]


def _fr_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _fr_record(**overrides):
    raw = {
        "section": "F-01",
        "work": "section-2026-11-a",
        "date": "2026-11-13",
        "disposition": "PROVEN",
        "owner": "yrsa",
        "proof_kind": "proven-and-held",
        "stages": list(STAGES),
        "claims": ["evidence_ref", "test_ref"],
    }
    raw.update(overrides)
    return raw


def _fr_fresh_for(section, work="section-2026-11-a"):
    return _fr_record(section=section, work=work)


class TestFinalReportAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_sections(
            self, agent):
        status = agent.finalreport_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["finalreport_book"]["schema"] == (
            FINAL_REPORT_SCHEMA)
        assert [c["id"] for c in status[
            "finalreport_book"]["sections"]] == ALL_FAMILIES
        assert status["finalreport_book"]["records"] == []
        assert status["finalreport_book"]["reports"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "F-01" in status["sections_text"]
        assert "standing listed" in status["sections_text"]
        assert "none recorded this session" in status["screen"]
        assert "final report" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == FINALREPORT_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._finalreport_registry()
        assert agent._finalreport_registry() is first
        assert agent._finalreport_store is first
        for name in ("finalreport_sections",
                     "finalreport_book",
                     "finalreport_status",
                     "get_finalreport_section",
                     "get_finalreport_record",
                     "finalreport_standing",
                     "report_sections_for_disposition",
                     "finalreport_held",
                     "finalreport_index",
                     "finalreport_verdict",
                     "prepare_finalreport_report",
                     "get_finalreport_report",
                     "finalreport_reports",
                     "report_finalreport"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_finalreport_registry",
            "finalreport_sections",
            "finalreport_book",
            "finalreport_status",
            "get_finalreport_section",
            "get_finalreport_record",
            "finalreport_standing", "report_sections_for_disposition",
            "finalreport_held", "finalreport_index",
            "finalreport_verdict",
            "register_finalreport_record",
            "register_finalreport_records",
            "record_finalreport_records",
            "view_finalreport",
            "prepare_finalreport_report",
            "get_finalreport_report",
            "finalreport_reports",
            "report_finalreport",
            "_publish_finalreport_record",
            "_finalreport_screen",
            "_finalreport_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.finalreport_status()
        entry = agent.get_finalreport_section("F-01")
        assert entry.doctrine == "plain-language"
        assert entry.subject == "what-it-can-do"
        standing = agent.finalreport_standing("F-01")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.grade == "open"
        assert agent.finalreport_held() == []
        assert agent.report_sections_for_disposition("PROVEN") == []
        agent.finalreport_index()
        agent.finalreport_verdict()
        agent.report_finalreport()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _FR_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown section"):
            agent.get_finalreport_section("guess")
        with pytest.raises(ValueError, match="unknown section"):
            agent.finalreport_standing("guess")
        with pytest.raises(ValueError, match="holds no"):
            agent.get_finalreport_record("F-01")
        with pytest.raises(ValueError):
            agent.report_sections_for_disposition("")
        agent.close()


class TestFinalReportAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_finalreport_record(
            _fr_record())
        assert result["record"]["section"] == "F-01"
        assert result["record_news"]["type"] == (
            "finalreport_record")
        assert "held as answered" in result["screen"]
        status = agent.finalreport_status()
        assert [r["section"] for r in status["records"]] == [
            "F-01"]
        assert status["book"]["records"][0]["work"] == (
            "section-2026-11-a")
        assert status["held"] == ["F-01"]
        assert status["open"] == []
        assert "held as answered" in status["records_text"]
        assert len(_fr_records(
            store, session_id, "finalreport_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_finalreport_record(_fr_record())
        with pytest.raises(ValueError, match="F-01"):
            agent.register_finalreport_record(
                _fr_record(work="section-2026-11-b"))
        assert len(_fr_records(
            store, session_id, "finalreport_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_finalreport_record(
                _fr_record(claims=["vibes"]))
        assert agent.finalreport_status()["records"] == []
        assert _fr_records(
            store, session_id, "finalreport_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_finalreport_records([
            _fr_fresh_for("F-02"), _fr_record()])
        assert result["count"] == 2
        assert [r["section"] for r in result["records_news"]] == [
            "F-02", "F-01"]
        assert len(_fr_records(
            store, session_id, "finalreport_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_finalreport_records(
            [_fr_fresh_for("F-02")])
        assert result["count"] == 1
        assert result["book"]["schema"] == (
            FINAL_REPORT_SCHEMA)
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_finalreport_records(
                [_fr_fresh_for("F-02")])
        assert len(_fr_records(
            store, session_id, "finalreport_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_finalreport_record(_fr_record())
        result = agent.view_finalreport("F-01")
        assert result["section"]["id"] == "F-01"
        assert result["standing"]["held"] is True
        assert result["record"]["work"] == "section-2026-11-a"
        assert result["record_news"]["type"] == (
            "finalreport_standing")
        assert result["held_record_news"]["type"] == (
            "finalreport_record")
        assert len(_fr_records(
            store, session_id, "finalreport_record")) == 1
        assert len(_fr_records(
            store, session_id, "finalreport_standing")) == 1
        result = agent.view_finalreport("F-03")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_fr_records(
            store, session_id, "finalreport_standing")) == 2
        agent.close()


class TestFinalReportReports:
    def test_prepare_report_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_finalreport_report(
            "section-2026-11", "section-1",
            "every section answered",
            "2026-11-13", 3, 4, 5, 12,
            claims=("evidence_ref", "test_ref"))
        assert result["report"]["state"] == "ready"
        assert result["report"]["certified"] is False
        assert result["report"]["inflated"] is False
        assert result["report_news"]["type"] == (
            "finalreport_verdict")
        assert "every section answered" in result["screen"]
        report = agent.get_finalreport_report(
            "section-2026-11")
        assert report.entry == "section-1"
        assert [r.book for r in
                agent.finalreport_reports()] == [
            "section-2026-11"]
        assert len(_fr_records(
            store, session_id, "finalreport_verdict")) == 1
        agent.close()

    def test_report_unshared_state_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared"):
            agent.prepare_finalreport_report(
                "section-2026-11", "section-1", "x",
                "2026-11-13", 3, 4, 5, 12,
                claims=("evidence_ref",), state="executed")
        assert agent.finalreport_reports() == []
        assert _fr_records(
            store, session_id, "finalreport_verdict") == []
        agent.close()

    def test_duplicate_report_refuses(self, agent):
        agent.prepare_finalreport_report(
            "section-2026-11", "section-1",
            "every section answered", "2026-11-13", 3, 4, 5, 12,
            claims=("evidence_ref",))
        with pytest.raises(ValueError, match="section-2026-11"):
            agent.prepare_finalreport_report(
                "section-2026-11", "section-2",
                "a second telling", "2026-11-13", 3, 4, 5, 12,
                claims=("evidence_ref",))
        with pytest.raises(ValueError,
                           match="holds no"):
            agent.get_finalreport_report("section-2026-12")


class TestFinalReportParseArgs:
    def test_parse_args_well(self):
        assert parse_finalreport_args("") == (
            "show", None, (), None)
        assert parse_finalreport_args(None) == (
            "show", None, (), None)
        assert parse_finalreport_args("sections") == (
            "sections", None, (), None)
        assert parse_finalreport_args(
            "section F-01") == (
            "section", "F-01", (), None)
        assert parse_finalreport_args(
            "record F-01") == (
            "record", "F-01", (), None)
        assert parse_finalreport_args(
            "standing F-02") == (
            "standing", "F-02", (), None)
        assert parse_finalreport_args("report") == (
            "reports", None, (), None)
        assert parse_finalreport_args(
            "report section-2026-11") == (
            "report", "section-2026-11", (), None)
        assert parse_finalreport_args("verdict") == (
            "verdict", None, (), None)
        assert parse_finalreport_args("index") == (
            "index", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "section", "record",
                    "record F-01 extra",
                    "sections now", "standing",
                    "report a b"):
            with pytest.raises(ValueError) as caught:
                parse_finalreport_args(bad)
            assert str(caught.value) == FINALREPORT_USAGE


class TestFinalReportTerminalRoad:
    def test_show_sections_section_record_standing_report_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/finalreport")
        assert "F-01" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/finalreport sections")
        assert "what-it-can-do" in text
        assert "F-03" in text
        _, _, text = _slash(
            agent, "/finalreport section F-01")
        assert "what-it-can-do" in text
        _, _, text = _slash(
            agent, "/finalreport record F-01")
        assert "holds no" in text
        _, _, text = _slash(
            agent, "/finalreport standing F-01")
        assert "F-01:" in text
        assert "open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/finalreport report")
        assert "none held" in text
        _, _, text = _slash(agent, "/finalreport verdict")
        assert "Final report stands open" in text
        agent.register_finalreport_record(_fr_record())
        _, _, text = _slash(
            agent, "/finalreport record F-01")
        assert "held as answered" in text
        _, _, text = _slash(
            agent, "/finalreport standing F-01")
        assert "held as answered" in text
        _, _, text = _slash(agent, "/finalreport index")
        assert "held as answered" in text
        agent.prepare_finalreport_report(
            "section-2026-11", "section-1",
            "every section answered", "2026-11-13", 3, 4, 5, 12,
            claims=("evidence_ref",))
        _, _, text = _slash(
            agent, "/finalreport report section-2026-11")
        assert "every section answered" in text
        assert "never inflated" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/finalreport [show|sections|"
                "section <section>|"
                "record <section>|"
                "standing <section>|"
                "report [<book>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/finalreport dance sectiony")
        assert text == FINALREPORT_USAGE
        _, _, text = _slash(
            agent, "/finalreport section guess")
        assert "unknown section" in text


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


def _fr_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestFinalReportHandler:
    def test_show_is_default(self, ra_handler, agent):
        ra_handler._handle_finalreport("")
        assert "F-01" in (
            _fr_published_text(ra_handler))
        assert "what-it-can-do" in (
            _fr_published_text(ra_handler))

    def test_section_record_and_verdict(
            self, ra_handler, agent):
        ra_handler._handle_finalreport(
            "section F-01")
        assert "what-it-can-do" in (
            _fr_published_text(ra_handler))
        agent.register_finalreport_record(_fr_record())
        ra_handler._handle_finalreport(
            "record F-01")
        assert "held as answered" in (
            _fr_published_text(ra_handler))
        ra_handler._handle_finalreport("verdict")
        assert "Final report stands held" in (
            _fr_published_text(ra_handler))

    def test_bad_grammar_is_published(
            self, ra_handler, agent):
        ra_handler._handle_finalreport("dance sectiony")
        assert FINALREPORT_USAGE in (
            _fr_published_text(ra_handler))
        ra_handler._handle_finalreport("section guess")
        assert "unknown section" in (
            _fr_published_text(ra_handler))


class TestChatScreenRoutingFinalReport:
    def test_sections_as_system_command(self, monkeypatch):
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
        screen.handle_command("/finalreport verdict",
                              _FakeLog())
        assert calls == [("/finalreport", "verdict")]

    def test_chat_screen_help_and_usage_name_the_report(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/finalreport[/green] - show the "
                "Final report (M-272)") in text
        assert ('"/finalreport": "Usage: '
                "/finalreport | "
                "/finalreport sections") in text


class TestFinalReportDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.finalreport_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _FR_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        _rp = ROOT / "README.md"
        _rb = _rp.read_bytes() if _rp.exists() else None
        verdict = agent.finalreport_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_finalreport_record(_fr_record())
        agent.register_finalreport_record(
            _fr_fresh_for("F-02", work="section-2026-11-b"))
        verdict = agent.finalreport_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "F-01", "F-02"]
        assert "Final report stands held" in (
            verdict["verdict_text"])
        assert not _rp.exists() or _rp.read_bytes() == _rb

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_finalreport()
        assert report["book"]["schema"] == (
            FINAL_REPORT_SCHEMA)
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_finalreport_record(_fr_record())
        report = agent.report_finalreport()
        assert "held as answered" in report["records_text"]
        assert [s["section"] for s in report["standings"]] == [
            "F-01"]

    def test_report_sections_for_disposition_and_held_keys(self, agent):
        agent.register_finalreport_record(_fr_record())
        agent.register_finalreport_record(
            _fr_fresh_for("F-02", work="section-2026-11-b"))
        agent.register_finalreport_record(_fr_record(
            section="F-03", work="section-2026-11-c",
            disposition="NOT_PROVEN", owner="",
            proof_kind="none",
            stages=["named"], claims=["assertion"]))
        assert [r.work for r in
                agent.report_sections_for_disposition("PROVEN")] == [
            "section-2026-11-a", "section-2026-11-b"]
        assert agent.finalreport_held() == ["F-01", "F-02"]
        standing = agent.finalreport_standing(
            "F-03")
        assert standing.held is False
