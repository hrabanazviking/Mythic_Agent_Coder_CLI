"""M-270 The roadmap audit - pure-layer tests.

TIER: unit

DONE with evidence, PARTIAL with its road, or NOT PROVEN
with its reason per roadmap part, in the closing twin: a
part counts DONE only on held proof measured in the
campaign itself resting on held evidence, a partial part
only where the done part rests on held evidence and the
rest is roaded in the open, and a not proven part only
with its owner and reason recorded - a not proven part
admitted in the open is honest.
"""
import pytest

from mythic_agent.core.roadmap_audit import (
    AUDIT_PARTS,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    RoadmapAuditEntry,
    RoadmapAuditRegistry,
    RoadmapAuditRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_part,
    format_parts,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(part="A-03",
                work="audit-2026-11-a",
                date="2026-11-13", disposition="DONE",
                owner="yrsa",
                proof_kind="done-and-held",
                stages=STAGES,
                claims=("evidence_ref", "test_ref"))
    base.update(kw)
    return RoadmapAuditRecord(**base)


def partial_record(**kw):
    base = dict(part="A-05",
                work="audit-2026-11-a",
                date="2026-11-13", disposition="PARTIAL",
                owner="yrsa",
                proof_kind="partially-held",
                stages=STAGES,
                claims=("test_ref",))
    base.update(kw)
    return RoadmapAuditRecord(**base)


def not_proven_record(**kw):
    base = dict(part="A-07",
                work="audit-2026-11-a",
                date="2026-11-13", disposition="NOT_PROVEN",
                owner="yrsa",
                proof_kind="none",
                stages=STAGES,
                claims=("test_ref",))
    base.update(kw)
    return RoadmapAuditRecord(**base)


def full_book(**overrides):
    records = []
    for part_id in default_registry().combinations():
        if part_id in ("A-01", "A-02", "A-03"):
            kw = dict(part=part_id, work="audit-2026-11-a",
                      date="2026-11-13", disposition="DONE",
                      owner="yrsa",
                      proof_kind="done-and-held",
                      stages=STAGES,
                      claims=("evidence_ref", "test_ref"))
        elif part_id in ("A-04", "A-05", "A-06", "A-07"):
            kw = dict(part=part_id, work="audit-2026-11-a",
                      date="2026-11-13", disposition="PARTIAL",
                      owner="yrsa",
                      proof_kind="partially-held",
                      stages=STAGES,
                      claims=("test_ref",))
        else:
            kw = dict(part=part_id, work="audit-2026-11-a",
                      date="2026-11-13", disposition="NOT_PROVEN",
                      owner="yrsa",
                      proof_kind="none",
                      stages=STAGES,
                      claims=("test_ref",))
        kw.update(overrides.get(part_id, {}))
        records.append(RoadmapAuditRecord(**kw))
    return records


def test_registry_holds_twelve_parts_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "A-01"
    assert reg.ids()[-1] == "A-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_parts_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("A-01").doctrine == "audit-truth"
    assert reg.get("A-01").subject == "part-01"
    assert reg.get("A-02").subject == "part-02"
    assert reg.get("A-03").subject == "part-03"
    assert reg.get("A-04").subject == "part-04"
    assert reg.get("A-11").doctrine == "road-honesty"
    assert reg.get("A-11").subject == "part-11"
    assert reg.get("A-12").doctrine == "audit-duty"
    assert DISPOSITIONS == ("DONE", "PARTIAL", "NOT_PROVEN")


def test_registry_unknown_part_refused_by_name():
    with pytest.raises(ValidationError, match="unknown part: C-99"):
        default_registry().get("C-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate part"):
        RoadmapAuditRegistry(AUDIT_PARTS + AUDIT_PARTS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        RoadmapAuditRegistry([RoadmapAuditEntry("A-01", "audit-truth", "part-01", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        RoadmapAuditRegistry([RoadmapAuditEntry("A-01", "audit-truth", "part-01", "published", "why")])
    with pytest.raises(ValidationError, match="labelled"):
        RoadmapAuditRegistry([RoadmapAuditEntry("A-01", "audit-truth", "part-01", "listed", "why", labelled=False)])
    with pytest.raises(ValidationError, match="evidenced"):
        RoadmapAuditRegistry([RoadmapAuditEntry("A-01", "audit-truth", "part-01", "listed", "why", evidenced=False)])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown part doctrine"):
        RoadmapAuditRegistry([RoadmapAuditEntry("A-01", "M-999", "part-01", "listed", "why")])


def test_record_done_measured_and_held_stands_held():
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


def test_record_done_on_partial_proof_stands_open():
    standing = derive_standing(fresh_record(proof_kind="partially-held"))
    assert not standing.held
    assert any("tells the truth" in g for g in standing.gaps)


def test_record_done_without_evidence_ref_stands_open():
    standing = derive_standing(fresh_record(claims=("test_ref",)))
    assert not standing.held
    assert any("no held" in g for g in standing.gaps)


def test_record_done_on_bare_claims_stands_open():
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


def test_verdict_full_book_done_with_partial_parts():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.done_parts == ("A-01", "A-02", "A-03")
    assert len(verdict.partial_parts) == 4
    assert len(verdict.not_proven_parts) == 5
    assert verdict.missing_parts == ()


def test_verdict_missing_part_stops_the_report():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_parts == ("A-12",)
    assert any("A-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_report():
    verdict = derive_verdict(full_book(**{"A-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("A-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_part_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_done_and_shared_states():
    report = prepare_report("audit-a", "A-01", "findings as dispositioned",
                            "2026-11-13", 3, 4, 5, 12,
                            claims=("evidence_ref",))
    assert report.state == "ready"
    shared = prepare_report("audit-a", "A-01", "findings as dispositioned",
                            "2026-11-13", 3, 4, 5, 12,
                            claims=("evidence_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("audit-a", "A-01", "findings", "2026-11-13",
                       3, 4, 5, 12, claims=("evidence_ref",), state="sealed")
    with pytest.raises(ValidationError, match="part complete"):
        prepare_report("audit-a", "A-01", "findings", "2026-11-13",
                       3, 2, 2, 12, claims=("evidence_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("audit-a", "A-01", "findings", "2026-11-13",
                       3, 4, 5, 12, claims=("feeling",))
    assert "A-01" in format_part(default_registry().get("A-01"))
    assert "A-12" in format_parts()
    assert "DONE" in format_record(fresh_record())
    assert "PARTIAL" in format_records([partial_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
    from pathlib import Path as _P
    _src = (_P(__file__).resolve().parent.parent
            / "mythic_agent" / "core" / "roadmap_audit.py").read_text(
                encoding="utf-8")
    assert "open(" not in _src
    assert "socket" not in _src
    assert "subprocess" not in _src
    assert "urllib" not in _src


# ---------------------------------------------------------------------
# M-270 Roadmap audit - agent layer. The pure book is held
# by a session registry in the agent layer alone: parts are read
# from the shipped registry, capture records are held one by one for
# the session, records, viewed standings and held reports are
# published as session news through the checkpoint road
# (journal-first, deduped per record, standing and verdict),
# standings, the index and the verdict are derived at call time from
# the held records - an part stands held only when its finding
# counts DONE on done-and-held evidence resting on held local
# evidence, or stands PARTIAL or NOT PROVEN with a named owner in the open -
# audit reports are held only as reports, state ready by default,
# may be marked shared by a human, a certification claimed only
# when every part stands answered, and never inflated, and the
# registry is session state, never a stored setting. This layer
# runs no attack, reads no sandbox code and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    ROADMAPAUDIT_USAGE,
    parse_roadmapaudit_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.roadmap_audit import (
    PLAIN_EXPLANATION,
    ROADMAP_AUDIT_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_RA_EVENT_TYPES = (
    "roadmapaudit_record", "roadmapaudit_standing",
    "roadmapaudit_verdict")

ALL_FAMILIES = ["A-01", "A-02", "A-03", "A-04", "A-05", "A-06",
             "A-07", "A-08", "A-09", "A-10", "A-11", "A-12"]


def _ra_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _ra_record(**overrides):
    raw = {
        "part": "A-01",
        "work": "part-2026-11-a",
        "date": "2026-11-13",
        "disposition": "DONE",
        "owner": "yrsa",
        "proof_kind": "done-and-held",
        "stages": list(STAGES),
        "claims": ["evidence_ref", "test_ref"],
    }
    raw.update(overrides)
    return raw


def _ra_fresh_for(part, work="part-2026-11-a"):
    return _ra_record(part=part, work=work)


class TestRoadmapAuditAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_parts(
            self, agent):
        status = agent.roadmapaudit_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["roadmapaudit_book"]["schema"] == (
            ROADMAP_AUDIT_SCHEMA)
        assert [c["id"] for c in status[
            "roadmapaudit_book"]["parts"]] == ALL_FAMILIES
        assert status["roadmapaudit_book"]["records"] == []
        assert status["roadmapaudit_book"]["reports"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "A-01" in status["parts_text"]
        assert "standing listed" in status["parts_text"]
        assert "none recorded this session" in status["screen"]
        assert "roadmap audit" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == ROADMAPAUDIT_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._roadmapaudit_registry()
        assert agent._roadmapaudit_registry() is first
        assert agent._roadmapaudit_store is first
        for name in ("roadmapaudit_parts",
                     "roadmapaudit_book",
                     "roadmapaudit_status",
                     "get_roadmapaudit_part",
                     "get_roadmapaudit_record",
                     "roadmapaudit_standing",
                     "parts_for_disposition",
                     "roadmapaudit_held",
                     "roadmapaudit_index",
                     "roadmapaudit_verdict",
                     "prepare_roadmapaudit_report",
                     "get_roadmapaudit_report",
                     "roadmapaudit_reports",
                     "report_roadmapaudit"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_roadmapaudit_registry",
            "roadmapaudit_parts",
            "roadmapaudit_book",
            "roadmapaudit_status",
            "get_roadmapaudit_part",
            "get_roadmapaudit_record",
            "roadmapaudit_standing", "parts_for_disposition",
            "roadmapaudit_held", "roadmapaudit_index",
            "roadmapaudit_verdict",
            "register_roadmapaudit_record",
            "register_roadmapaudit_records",
            "record_roadmapaudit_records",
            "view_roadmapaudit",
            "prepare_roadmapaudit_report",
            "get_roadmapaudit_report",
            "roadmapaudit_reports",
            "report_roadmapaudit",
            "_publish_roadmapaudit_record",
            "_roadmapaudit_screen",
            "_roadmapaudit_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.roadmapaudit_status()
        entry = agent.get_roadmapaudit_part("A-01")
        assert entry.doctrine == "audit-truth"
        assert entry.subject == "part-01"
        standing = agent.roadmapaudit_standing("A-01")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.grade == "open"
        assert agent.roadmapaudit_held() == []
        assert agent.parts_for_disposition("DONE") == []
        agent.roadmapaudit_index()
        agent.roadmapaudit_verdict()
        agent.report_roadmapaudit()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _RA_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown part"):
            agent.get_roadmapaudit_part("guess")
        with pytest.raises(ValueError, match="unknown part"):
            agent.roadmapaudit_standing("guess")
        with pytest.raises(ValueError, match="holds no"):
            agent.get_roadmapaudit_record("A-01")
        with pytest.raises(ValueError):
            agent.parts_for_disposition("")
        agent.close()


class TestRoadmapAuditAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_roadmapaudit_record(
            _ra_record())
        assert result["record"]["part"] == "A-01"
        assert result["record_news"]["type"] == (
            "roadmapaudit_record")
        assert "held as answered" in result["screen"]
        status = agent.roadmapaudit_status()
        assert [r["part"] for r in status["records"]] == [
            "A-01"]
        assert status["book"]["records"][0]["work"] == (
            "part-2026-11-a")
        assert status["held"] == ["A-01"]
        assert status["open"] == []
        assert "held as answered" in status["records_text"]
        assert len(_ra_records(
            store, session_id, "roadmapaudit_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_roadmapaudit_record(_ra_record())
        with pytest.raises(ValueError, match="A-01"):
            agent.register_roadmapaudit_record(
                _ra_record(work="part-2026-11-b"))
        assert len(_ra_records(
            store, session_id, "roadmapaudit_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_roadmapaudit_record(
                _ra_record(claims=["vibes"]))
        assert agent.roadmapaudit_status()["records"] == []
        assert _ra_records(
            store, session_id, "roadmapaudit_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_roadmapaudit_records([
            _ra_fresh_for("A-02"), _ra_record()])
        assert result["count"] == 2
        assert [r["part"] for r in result["records_news"]] == [
            "A-02", "A-01"]
        assert len(_ra_records(
            store, session_id, "roadmapaudit_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_roadmapaudit_records(
            [_ra_fresh_for("A-02")])
        assert result["count"] == 1
        assert result["book"]["schema"] == (
            ROADMAP_AUDIT_SCHEMA)
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_roadmapaudit_records(
                [_ra_fresh_for("A-02")])
        assert len(_ra_records(
            store, session_id, "roadmapaudit_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_roadmapaudit_record(_ra_record())
        result = agent.view_roadmapaudit("A-01")
        assert result["part"]["id"] == "A-01"
        assert result["standing"]["held"] is True
        assert result["record"]["work"] == "part-2026-11-a"
        assert result["record_news"]["type"] == (
            "roadmapaudit_standing")
        assert result["held_record_news"]["type"] == (
            "roadmapaudit_record")
        assert len(_ra_records(
            store, session_id, "roadmapaudit_record")) == 1
        assert len(_ra_records(
            store, session_id, "roadmapaudit_standing")) == 1
        result = agent.view_roadmapaudit("A-03")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_ra_records(
            store, session_id, "roadmapaudit_standing")) == 2
        agent.close()


class TestRoadmapAuditReports:
    def test_prepare_report_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_roadmapaudit_report(
            "part-2026-11", "part-1",
            "every part answered",
            "2026-11-13", 3, 4, 5, 12,
            claims=("evidence_ref", "test_ref"))
        assert result["report"]["state"] == "ready"
        assert result["report"]["certified"] is False
        assert result["report"]["inflated"] is False
        assert result["report_news"]["type"] == (
            "roadmapaudit_verdict")
        assert "every part answered" in result["screen"]
        report = agent.get_roadmapaudit_report(
            "part-2026-11")
        assert report.entry == "part-1"
        assert [r.book for r in
                agent.roadmapaudit_reports()] == [
            "part-2026-11"]
        assert len(_ra_records(
            store, session_id, "roadmapaudit_verdict")) == 1
        agent.close()

    def test_report_unshared_state_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared"):
            agent.prepare_roadmapaudit_report(
                "part-2026-11", "part-1", "x",
                "2026-11-13", 3, 4, 5, 12,
                claims=("evidence_ref",), state="executed")
        assert agent.roadmapaudit_reports() == []
        assert _ra_records(
            store, session_id, "roadmapaudit_verdict") == []
        agent.close()

    def test_duplicate_report_refuses(self, agent):
        agent.prepare_roadmapaudit_report(
            "part-2026-11", "part-1",
            "every part answered", "2026-11-13", 3, 4, 5, 12,
            claims=("evidence_ref",))
        with pytest.raises(ValueError, match="part-2026-11"):
            agent.prepare_roadmapaudit_report(
                "part-2026-11", "part-2",
                "a second telling", "2026-11-13", 3, 4, 5, 12,
                claims=("evidence_ref",))
        with pytest.raises(ValueError,
                           match="holds no"):
            agent.get_roadmapaudit_report("part-2026-12")


class TestRoadmapAuditParseArgs:
    def test_parse_args_well(self):
        assert parse_roadmapaudit_args("") == (
            "show", None, (), None)
        assert parse_roadmapaudit_args(None) == (
            "show", None, (), None)
        assert parse_roadmapaudit_args("parts") == (
            "parts", None, (), None)
        assert parse_roadmapaudit_args(
            "part A-01") == (
            "part", "A-01", (), None)
        assert parse_roadmapaudit_args(
            "record A-01") == (
            "record", "A-01", (), None)
        assert parse_roadmapaudit_args(
            "standing A-02") == (
            "standing", "A-02", (), None)
        assert parse_roadmapaudit_args("report") == (
            "reports", None, (), None)
        assert parse_roadmapaudit_args(
            "report part-2026-11") == (
            "report", "part-2026-11", (), None)
        assert parse_roadmapaudit_args("verdict") == (
            "verdict", None, (), None)
        assert parse_roadmapaudit_args("index") == (
            "index", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "part", "record",
                    "record A-01 extra",
                    "parts now", "standing",
                    "report a b"):
            with pytest.raises(ValueError) as caught:
                parse_roadmapaudit_args(bad)
            assert str(caught.value) == ROADMAPAUDIT_USAGE


class TestRoadmapAuditTerminalRoad:
    def test_show_parts_part_record_standing_report_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/roadmapaudit")
        assert "A-01" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/roadmapaudit parts")
        assert "part-01" in text
        assert "A-03" in text
        _, _, text = _slash(
            agent, "/roadmapaudit part A-01")
        assert "part-01" in text
        _, _, text = _slash(
            agent, "/roadmapaudit record A-01")
        assert "holds no" in text
        _, _, text = _slash(
            agent, "/roadmapaudit standing A-01")
        assert "A-01:" in text
        assert "open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/roadmapaudit report")
        assert "none held" in text
        _, _, text = _slash(agent, "/roadmapaudit verdict")
        assert "Roadmap audit stands open" in text
        agent.register_roadmapaudit_record(_ra_record())
        _, _, text = _slash(
            agent, "/roadmapaudit record A-01")
        assert "held as answered" in text
        _, _, text = _slash(
            agent, "/roadmapaudit standing A-01")
        assert "held as answered" in text
        _, _, text = _slash(agent, "/roadmapaudit index")
        assert "held as answered" in text
        agent.prepare_roadmapaudit_report(
            "part-2026-11", "part-1",
            "every part answered", "2026-11-13", 3, 4, 5, 12,
            claims=("evidence_ref",))
        _, _, text = _slash(
            agent, "/roadmapaudit report part-2026-11")
        assert "every part answered" in text
        assert "never inflated" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/roadmapaudit [show|parts|"
                "part <part>|"
                "record <part>|"
                "standing <part>|"
                "report [<book>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/roadmapaudit dance party")
        assert text == ROADMAPAUDIT_USAGE
        _, _, text = _slash(
            agent, "/roadmapaudit part guess")
        assert "unknown part" in text


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


def _ra_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestRoadmapAuditHandler:
    def test_show_is_default(self, ra_handler, agent):
        ra_handler._handle_roadmapaudit("")
        assert "A-01" in (
            _ra_published_text(ra_handler))
        assert "part-01" in (
            _ra_published_text(ra_handler))

    def test_part_record_and_verdict(
            self, ra_handler, agent):
        ra_handler._handle_roadmapaudit(
            "part A-01")
        assert "part-01" in (
            _ra_published_text(ra_handler))
        agent.register_roadmapaudit_record(_ra_record())
        ra_handler._handle_roadmapaudit(
            "record A-01")
        assert "held as answered" in (
            _ra_published_text(ra_handler))
        ra_handler._handle_roadmapaudit("verdict")
        assert "Roadmap audit stands held" in (
            _ra_published_text(ra_handler))

    def test_bad_grammar_is_published(
            self, ra_handler, agent):
        ra_handler._handle_roadmapaudit("dance party")
        assert ROADMAPAUDIT_USAGE in (
            _ra_published_text(ra_handler))
        ra_handler._handle_roadmapaudit("part guess")
        assert "unknown part" in (
            _ra_published_text(ra_handler))


class TestChatScreenRoutingRoadmapAudit:
    def test_parts_as_system_command(self, monkeypatch):
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
        screen.handle_command("/roadmapaudit verdict",
                              _FakeLog())
        assert calls == [("/roadmapaudit", "verdict")]

    def test_chat_screen_help_and_usage_name_the_audit(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/roadmapaudit[/green] - show the "
                "Roadmap audit (M-270)") in text
        assert ('"/roadmapaudit": "Usage: '
                "/roadmapaudit | "
                "/roadmapaudit parts") in text


class TestRoadmapAuditDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.roadmapaudit_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _RA_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        _rp = ROOT / "README.md"
        _rb = _rp.read_bytes() if _rp.exists() else None
        verdict = agent.roadmapaudit_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_roadmapaudit_record(_ra_record())
        agent.register_roadmapaudit_record(
            _ra_fresh_for("A-02", work="part-2026-11-b"))
        verdict = agent.roadmapaudit_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "A-01", "A-02"]
        assert "Roadmap audit stands held" in (
            verdict["verdict_text"])
        assert not _rp.exists() or _rp.read_bytes() == _rb

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_roadmapaudit()
        assert report["book"]["schema"] == (
            ROADMAP_AUDIT_SCHEMA)
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_roadmapaudit_record(_ra_record())
        report = agent.report_roadmapaudit()
        assert "held as answered" in report["records_text"]
        assert [s["part"] for s in report["standings"]] == [
            "A-01"]

    def test_parts_for_disposition_and_held_keys(self, agent):
        agent.register_roadmapaudit_record(_ra_record())
        agent.register_roadmapaudit_record(
            _ra_fresh_for("A-02", work="part-2026-11-b"))
        agent.register_roadmapaudit_record(_ra_record(
            part="A-03", work="part-2026-11-c",
            disposition="NOT_PROVEN", owner="",
            proof_kind="none",
            stages=["named"], claims=["assertion"]))
        assert [r.work for r in
                agent.parts_for_disposition("DONE")] == [
            "part-2026-11-a", "part-2026-11-b"]
        assert agent.roadmapaudit_held() == ["A-01", "A-02"]
        standing = agent.roadmapaudit_standing(
            "A-03")
        assert standing.held is False
