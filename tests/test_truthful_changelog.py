"""M-268 Truthful changelog - pure-layer tests.

TIER: unit

Proven, partial or NOT PROVEN per feature family, in the
release itself: a family counts PROVEN only on held proof
measured in the release itself resting on held evidence,
a partial family only where the proven part rests on held
evidence and the rest is owned in the open, and a not
proven family only with its owner and reason recorded -
an unproven family admitted in the open is honest.
"""
import pytest

from mythic_agent.core.truthful_changelog import (
    FAMILIES,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    TruthfulChangelogEntry,
    TruthfulChangelogRegistry,
    TruthfulChangelogRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_family,
    format_families,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(family="C-03",
                work="changelog-2026-11-a",
                date="2026-11-13", disposition="PROVEN",
                owner="yrsa",
                proof_kind="measured-and-held",
                stages=STAGES,
                claims=("evidence_ref", "test_ref"))
    base.update(kw)
    return TruthfulChangelogRecord(**base)


def partial_record(**kw):
    base = dict(family="C-05",
                work="changelog-2026-11-a",
                date="2026-11-13", disposition="PARTIAL",
                owner="yrsa",
                proof_kind="partially-held",
                stages=STAGES,
                claims=("test_ref",))
    base.update(kw)
    return TruthfulChangelogRecord(**base)


def not_proven_record(**kw):
    base = dict(family="C-07",
                work="changelog-2026-11-a",
                date="2026-11-13", disposition="NOT_PROVEN",
                owner="yrsa",
                proof_kind="none",
                stages=STAGES,
                claims=("test_ref",))
    base.update(kw)
    return TruthfulChangelogRecord(**base)


def full_book(**overrides):
    records = []
    for family_id in default_registry().combinations():
        if family_id in ("C-01", "C-02", "C-03"):
            kw = dict(family=family_id, work="changelog-2026-11-a",
                      date="2026-11-13", disposition="PROVEN",
                      owner="yrsa",
                      proof_kind="measured-and-held",
                      stages=STAGES,
                      claims=("evidence_ref", "test_ref"))
        elif family_id in ("C-04", "C-05", "C-06", "C-07"):
            kw = dict(family=family_id, work="changelog-2026-11-a",
                      date="2026-11-13", disposition="PARTIAL",
                      owner="yrsa",
                      proof_kind="partially-held",
                      stages=STAGES,
                      claims=("test_ref",))
        else:
            kw = dict(family=family_id, work="changelog-2026-11-a",
                      date="2026-11-13", disposition="NOT_PROVEN",
                      owner="yrsa",
                      proof_kind="none",
                      stages=STAGES,
                      claims=("test_ref",))
        kw.update(overrides.get(family_id, {}))
        records.append(TruthfulChangelogRecord(**kw))
    return records


def test_registry_holds_twelve_families_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "C-01"
    assert reg.ids()[-1] == "C-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_families_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("C-01").doctrine == "truth-in-release"
    assert reg.get("C-01").subject == "provider-ocean-family"
    assert reg.get("C-02").subject == "code-intelligence-family"
    assert reg.get("C-03").subject == "editors-hand-family"
    assert reg.get("C-04").subject == "sandbox-family"
    assert reg.get("C-11").doctrine == "truth-in-release"
    assert reg.get("C-11").subject == "core-cli-family"
    assert reg.get("C-12").doctrine == "proof-duty"
    assert DISPOSITIONS == ("PROVEN", "PARTIAL", "NOT_PROVEN")


def test_registry_unknown_family_refused_by_name():
    with pytest.raises(ValidationError, match="unknown family: C-99"):
        default_registry().get("C-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate family"):
        TruthfulChangelogRegistry(FAMILIES + FAMILIES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        TruthfulChangelogRegistry([TruthfulChangelogEntry("C-01", "truth-in-release", "provider-ocean-family", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        TruthfulChangelogRegistry([TruthfulChangelogEntry("C-01", "truth-in-release", "provider-ocean-family", "published", "why")])
    with pytest.raises(ValidationError, match="labelled"):
        TruthfulChangelogRegistry([TruthfulChangelogEntry("C-01", "truth-in-release", "provider-ocean-family", "listed", "why", labelled=False)])
    with pytest.raises(ValidationError, match="evidenced"):
        TruthfulChangelogRegistry([TruthfulChangelogEntry("C-01", "truth-in-release", "provider-ocean-family", "listed", "why", evidenced=False)])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown family doctrine"):
        TruthfulChangelogRegistry([TruthfulChangelogEntry("C-01", "M-999", "provider-ocean-family", "listed", "why")])


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


def test_verdict_full_book_ready_with_partial_families():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.proven_families == ("C-01", "C-02", "C-03")
    assert len(verdict.partial_families) == 4
    assert len(verdict.not_proven_families) == 5
    assert verdict.missing_families == ()


def test_verdict_missing_family_stops_the_report():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_families == ("C-12",)
    assert any("C-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_report():
    verdict = derive_verdict(full_book(**{"C-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("C-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_family_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("changelog-a", "C-01", "findings as dispositioned",
                            "2026-11-13", 3, 4, 5, 12,
                            claims=("evidence_ref",))
    assert report.state == "ready"
    shared = prepare_report("changelog-a", "C-01", "findings as dispositioned",
                            "2026-11-13", 3, 4, 5, 12,
                            claims=("evidence_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("changelog-a", "C-01", "findings", "2026-11-13",
                       3, 4, 5, 12, claims=("evidence_ref",), state="sealed")
    with pytest.raises(ValidationError, match="changelog complete"):
        prepare_report("changelog-a", "C-01", "findings", "2026-11-13",
                       3, 2, 2, 12, claims=("evidence_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("changelog-a", "C-01", "findings", "2026-11-13",
                       3, 4, 5, 12, claims=("feeling",))
    assert "C-01" in format_family(default_registry().get("C-01"))
    assert "C-12" in format_families()
    assert "PROVEN" in format_record(fresh_record())
    assert "PARTIAL" in format_records([partial_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
    from pathlib import Path as _P
    _src = (_P(__file__).resolve().parent.parent
            / "mythic_agent" / "core" / "truthful_changelog.py").read_text(
                encoding="utf-8")
    assert "open(" not in _src
    assert "socket" not in _src
    assert "subprocess" not in _src
    assert "urllib" not in _src

# ---------------------------------------------------------------------
# M-268 Truthful changelog - agent layer. The pure book is held
# by a session registry in the agent layer alone: families are read
# from the shipped registry, capture records are held one by one for
# the session, records, viewed standings and held reports are
# published as session news through the checkpoint road
# (journal-first, deduped per record, standing and verdict),
# standings, the index and the verdict are derived at call time from
# the held records - an family stands held only when its finding
# counts PROVEN on measured-and-held evidence resting on held local
# evidence, or stands PARTIAL or NOT PROVEN with a named owner in the open -
# audit reports are held only as reports, state ready by default,
# may be marked shared by a human, a certification claimed only
# when every family stands answered, and never inflated, and the
# registry is session state, never a stored setting. This layer
# runs no attack, reads no sandbox code and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    TRUTHFULCHANGELOG_USAGE,
    parse_truthfulchangelog_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.truthful_changelog import (
    PLAIN_EXPLANATION,
    TRUTHFUL_CHANGELOG_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_TC_EVENT_TYPES = (
    "truthfulchangelog_record", "truthfulchangelog_standing",
    "truthfulchangelog_verdict")

ALL_FAMILIES = ["C-01", "C-02", "C-03", "C-04", "C-05", "C-06",
             "C-07", "C-08", "C-09", "C-10", "C-11", "C-12"]


def _tc_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _tc_record(**overrides):
    raw = {
        "family": "C-01",
        "work": "changelog-2026-11-a",
        "date": "2026-11-13",
        "disposition": "PROVEN",
        "owner": "yrsa",
        "proof_kind": "measured-and-held",
        "stages": list(STAGES),
        "claims": ["evidence_ref", "test_ref"],
    }
    raw.update(overrides)
    return raw


def _tc_fresh_for(family, work="changelog-2026-11-a"):
    return _tc_record(family=family, work=work)


class TestTruthfulChangelogAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_families(
            self, agent):
        status = agent.truthfulchangelog_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["truthfulchangelog_book"]["schema"] == (
            TRUTHFUL_CHANGELOG_SCHEMA)
        assert [c["id"] for c in status[
            "truthfulchangelog_book"]["families"]] == ALL_FAMILIES
        assert status["truthfulchangelog_book"]["records"] == []
        assert status["truthfulchangelog_book"]["reports"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "C-01" in status["families_text"]
        assert "standing listed" in status["families_text"]
        assert "none recorded this session" in status["screen"]
        assert "truthful changelog" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == TRUTHFULCHANGELOG_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._truthfulchangelog_registry()
        assert agent._truthfulchangelog_registry() is first
        assert agent._truthfulchangelog_store is first
        for name in ("truthfulchangelog_families",
                     "truthfulchangelog_book",
                     "truthfulchangelog_status",
                     "get_truthfulchangelog_family",
                     "get_truthfulchangelog_record",
                     "truthfulchangelog_standing",
                     "families_for_disposition",
                     "truthfulchangelog_held",
                     "truthfulchangelog_index",
                     "truthfulchangelog_verdict",
                     "prepare_truthfulchangelog_report",
                     "get_truthfulchangelog_report",
                     "truthfulchangelog_reports",
                     "report_truthfulchangelog"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_truthfulchangelog_registry",
            "truthfulchangelog_families",
            "truthfulchangelog_book",
            "truthfulchangelog_status",
            "get_truthfulchangelog_family",
            "get_truthfulchangelog_record",
            "truthfulchangelog_standing", "families_for_disposition",
            "truthfulchangelog_held", "truthfulchangelog_index",
            "truthfulchangelog_verdict",
            "register_truthfulchangelog_record",
            "register_truthfulchangelog_records",
            "record_truthfulchangelog_records",
            "view_truthfulchangelog",
            "prepare_truthfulchangelog_report",
            "get_truthfulchangelog_report",
            "truthfulchangelog_reports",
            "report_truthfulchangelog",
            "_publish_truthfulchangelog_record",
            "_truthfulchangelog_screen",
            "_truthfulchangelog_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.truthfulchangelog_status()
        entry = agent.get_truthfulchangelog_family("C-01")
        assert entry.doctrine == "truth-in-release"
        assert entry.subject == "provider-ocean-family"
        standing = agent.truthfulchangelog_standing("C-01")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.grade == "open"
        assert agent.truthfulchangelog_held() == []
        assert agent.families_for_disposition("PROVEN") == []
        agent.truthfulchangelog_index()
        agent.truthfulchangelog_verdict()
        agent.report_truthfulchangelog()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _TC_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown family"):
            agent.get_truthfulchangelog_family("guess")
        with pytest.raises(ValueError, match="unknown family"):
            agent.truthfulchangelog_standing("guess")
        with pytest.raises(ValueError, match="holds no"):
            agent.get_truthfulchangelog_record("C-01")
        with pytest.raises(ValueError):
            agent.families_for_disposition("")
        agent.close()


class TestTruthfulChangelogAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_truthfulchangelog_record(
            _tc_record())
        assert result["record"]["family"] == "C-01"
        assert result["record_news"]["type"] == (
            "truthfulchangelog_record")
        assert "held as answered" in result["screen"]
        status = agent.truthfulchangelog_status()
        assert [r["family"] for r in status["records"]] == [
            "C-01"]
        assert status["book"]["records"][0]["work"] == (
            "changelog-2026-11-a")
        assert status["held"] == ["C-01"]
        assert status["open"] == []
        assert "held as answered" in status["records_text"]
        assert len(_tc_records(
            store, session_id, "truthfulchangelog_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_truthfulchangelog_record(_tc_record())
        with pytest.raises(ValueError, match="C-01"):
            agent.register_truthfulchangelog_record(
                _tc_record(work="changelog-2026-11-b"))
        assert len(_tc_records(
            store, session_id, "truthfulchangelog_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_truthfulchangelog_record(
                _tc_record(claims=["vibes"]))
        assert agent.truthfulchangelog_status()["records"] == []
        assert _tc_records(
            store, session_id, "truthfulchangelog_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_truthfulchangelog_records([
            _tc_fresh_for("C-02"), _tc_record()])
        assert result["count"] == 2
        assert [r["family"] for r in result["records_news"]] == [
            "C-02", "C-01"]
        assert len(_tc_records(
            store, session_id, "truthfulchangelog_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_truthfulchangelog_records(
            [_tc_fresh_for("C-02")])
        assert result["count"] == 1
        assert result["book"]["schema"] == (
            TRUTHFUL_CHANGELOG_SCHEMA)
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_truthfulchangelog_records(
                [_tc_fresh_for("C-02")])
        assert len(_tc_records(
            store, session_id, "truthfulchangelog_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_truthfulchangelog_record(_tc_record())
        result = agent.view_truthfulchangelog("C-01")
        assert result["family"]["id"] == "C-01"
        assert result["standing"]["held"] is True
        assert result["record"]["work"] == "changelog-2026-11-a"
        assert result["record_news"]["type"] == (
            "truthfulchangelog_standing")
        assert result["held_record_news"]["type"] == (
            "truthfulchangelog_record")
        assert len(_tc_records(
            store, session_id, "truthfulchangelog_record")) == 1
        assert len(_tc_records(
            store, session_id, "truthfulchangelog_standing")) == 1
        result = agent.view_truthfulchangelog("C-03")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_tc_records(
            store, session_id, "truthfulchangelog_standing")) == 2
        agent.close()


class TestTruthfulChangelogReports:
    def test_prepare_report_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_truthfulchangelog_report(
            "changelog-2026-11", "release-1",
            "every family answered",
            "2026-11-13", 3, 4, 5, 12,
            claims=("evidence_ref", "test_ref"))
        assert result["report"]["state"] == "ready"
        assert result["report"]["certified"] is False
        assert result["report"]["inflated"] is False
        assert result["report_news"]["type"] == (
            "truthfulchangelog_verdict")
        assert "every family answered" in result["screen"]
        report = agent.get_truthfulchangelog_report(
            "changelog-2026-11")
        assert report.entry == "release-1"
        assert [r.book for r in
                agent.truthfulchangelog_reports()] == [
            "changelog-2026-11"]
        assert len(_tc_records(
            store, session_id, "truthfulchangelog_verdict")) == 1
        agent.close()

    def test_report_unshared_state_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared"):
            agent.prepare_truthfulchangelog_report(
                "changelog-2026-11", "release-1", "x",
                "2026-11-13", 3, 4, 5, 12,
                claims=("evidence_ref",), state="executed")
        assert agent.truthfulchangelog_reports() == []
        assert _tc_records(
            store, session_id, "truthfulchangelog_verdict") == []
        agent.close()

    def test_duplicate_report_refuses(self, agent):
        agent.prepare_truthfulchangelog_report(
            "changelog-2026-11", "release-1",
            "every family answered", "2026-11-13", 3, 4, 5, 12,
            claims=("evidence_ref",))
        with pytest.raises(ValueError, match="changelog-2026-11"):
            agent.prepare_truthfulchangelog_report(
                "changelog-2026-11", "release-2",
                "a second telling", "2026-11-13", 3, 4, 5, 12,
                claims=("evidence_ref",))
        with pytest.raises(ValueError,
                           match="holds no"):
            agent.get_truthfulchangelog_report("changelog-2026-12")


class TestTruthfulChangelogParseArgs:
    def test_parse_args_well(self):
        assert parse_truthfulchangelog_args("") == (
            "show", None, (), None)
        assert parse_truthfulchangelog_args(None) == (
            "show", None, (), None)
        assert parse_truthfulchangelog_args("families") == (
            "families", None, (), None)
        assert parse_truthfulchangelog_args(
            "family C-01") == (
            "family", "C-01", (), None)
        assert parse_truthfulchangelog_args(
            "record C-01") == (
            "record", "C-01", (), None)
        assert parse_truthfulchangelog_args(
            "standing C-02") == (
            "standing", "C-02", (), None)
        assert parse_truthfulchangelog_args("report") == (
            "reports", None, (), None)
        assert parse_truthfulchangelog_args(
            "report changelog-2026-11") == (
            "report", "changelog-2026-11", (), None)
        assert parse_truthfulchangelog_args("verdict") == (
            "verdict", None, (), None)
        assert parse_truthfulchangelog_args("index") == (
            "index", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "family", "record",
                    "record C-01 extra",
                    "families now", "standing",
                    "report a b"):
            with pytest.raises(ValueError) as caught:
                parse_truthfulchangelog_args(bad)
            assert str(caught.value) == TRUTHFULCHANGELOG_USAGE


class TestTruthfulChangelogTerminalRoad:
    def test_show_families_family_record_standing_report_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/truthfulchangelog")
        assert "C-01" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/truthfulchangelog families")
        assert "provider-ocean-family" in text
        assert "C-03" in text
        _, _, text = _slash(
            agent, "/truthfulchangelog family C-01")
        assert "provider-ocean-family" in text
        _, _, text = _slash(
            agent, "/truthfulchangelog record C-01")
        assert "holds no" in text
        _, _, text = _slash(
            agent, "/truthfulchangelog standing C-01")
        assert "C-01:" in text
        assert "open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/truthfulchangelog report")
        assert "none held" in text
        _, _, text = _slash(agent, "/truthfulchangelog verdict")
        assert "Truthful changelog stands open" in text
        agent.register_truthfulchangelog_record(_tc_record())
        _, _, text = _slash(
            agent, "/truthfulchangelog record C-01")
        assert "held as answered" in text
        _, _, text = _slash(
            agent, "/truthfulchangelog standing C-01")
        assert "held as answered" in text
        _, _, text = _slash(agent, "/truthfulchangelog index")
        assert "held as answered" in text
        agent.prepare_truthfulchangelog_report(
            "changelog-2026-11", "release-1",
            "every family answered", "2026-11-13", 3, 4, 5, 12,
            claims=("evidence_ref",))
        _, _, text = _slash(
            agent, "/truthfulchangelog report changelog-2026-11")
        assert "every family answered" in text
        assert "never inflated" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/truthfulchangelog [show|families|"
                "family <family>|"
                "record <family>|"
                "standing <family>|"
                "report [<book>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/truthfulchangelog dance party")
        assert text == TRUTHFULCHANGELOG_USAGE
        _, _, text = _slash(
            agent, "/truthfulchangelog family guess")
        assert "unknown family" in text


@pytest.fixture()
def tc_handler(agent, monkeypatch):
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


def _tc_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestTruthfulChangelogHandler:
    def test_show_is_default(self, tc_handler, agent):
        tc_handler._handle_truthfulchangelog("")
        assert "C-01" in (
            _tc_published_text(tc_handler))
        assert "provider-ocean-family" in (
            _tc_published_text(tc_handler))

    def test_family_record_and_verdict(
            self, tc_handler, agent):
        tc_handler._handle_truthfulchangelog(
            "family C-01")
        assert "provider-ocean-family" in (
            _tc_published_text(tc_handler))
        agent.register_truthfulchangelog_record(_tc_record())
        tc_handler._handle_truthfulchangelog(
            "record C-01")
        assert "held as answered" in (
            _tc_published_text(tc_handler))
        tc_handler._handle_truthfulchangelog("verdict")
        assert "Truthful changelog stands held" in (
            _tc_published_text(tc_handler))

    def test_bad_grammar_is_published(
            self, tc_handler, agent):
        tc_handler._handle_truthfulchangelog("dance party")
        assert TRUTHFULCHANGELOG_USAGE in (
            _tc_published_text(tc_handler))
        tc_handler._handle_truthfulchangelog("family guess")
        assert "unknown family" in (
            _tc_published_text(tc_handler))


class TestChatScreenRoutingTruthfulChangelog:
    def test_families_as_system_command(self, monkeypatch):
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
        screen.handle_command("/truthfulchangelog verdict",
                              _FakeLog())
        assert calls == [("/truthfulchangelog", "verdict")]

    def test_chat_screen_help_and_usage_name_the_audit(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/truthfulchangelog[/green] - show the "
                "Truthful changelog (M-268)") in text
        assert ('"/truthfulchangelog": "Usage: '
                "/truthfulchangelog | "
                "/truthfulchangelog families") in text


class TestTruthfulChangelogDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.truthfulchangelog_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _TC_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        _rp = ROOT / "README.md"
        _rb = _rp.read_bytes() if _rp.exists() else None
        verdict = agent.truthfulchangelog_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_truthfulchangelog_record(_tc_record())
        agent.register_truthfulchangelog_record(
            _tc_fresh_for("C-02", work="changelog-2026-11-b"))
        verdict = agent.truthfulchangelog_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "C-01", "C-02"]
        assert "Truthful changelog stands held" in (
            verdict["verdict_text"])
        assert not _rp.exists() or _rp.read_bytes() == _rb

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_truthfulchangelog()
        assert report["book"]["schema"] == (
            TRUTHFUL_CHANGELOG_SCHEMA)
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_truthfulchangelog_record(_tc_record())
        report = agent.report_truthfulchangelog()
        assert "held as answered" in report["records_text"]
        assert [s["family"] for s in report["standings"]] == [
            "C-01"]

    def test_families_for_disposition_and_held_keys(self, agent):
        agent.register_truthfulchangelog_record(_tc_record())
        agent.register_truthfulchangelog_record(
            _tc_fresh_for("C-02", work="changelog-2026-11-b"))
        agent.register_truthfulchangelog_record(_tc_record(
            family="C-03", work="changelog-2026-11-c",
            disposition="NOT_PROVEN", owner="",
            proof_kind="none",
            stages=["named"], claims=["assertion"]))
        assert [r.work for r in
                agent.families_for_disposition("PROVEN")] == [
            "changelog-2026-11-a", "changelog-2026-11-b"]
        assert agent.truthfulchangelog_held() == ["C-01", "C-02"]
        standing = agent.truthfulchangelog_standing(
            "C-03")
        assert standing.held is False
