"""M-269 Release shaping - pure-layer tests.

TIER: unit

Proven, shaping or NOT READY per feature release, in the
release itself: a release counts READY only on held proof
measured in the release itself resting on held evidence,
a shaping release only where the ready part rests on held
evidence and the rest is owned in the open, and a not
ready release only with its owner and reason recorded -
an unready release admitted in the open is honest.
"""
import pytest

from mythic_agent.core.release_shaping import (
    RELEASES,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    ReleaseShapingEntry,
    ReleaseShapingRegistry,
    ReleaseShapingRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_release,
    format_releases,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(release="R-03",
                work="release-2026-11-a",
                date="2026-11-13", disposition="READY",
                owner="yrsa",
                proof_kind="ready-and-held",
                stages=STAGES,
                claims=("evidence_ref", "test_ref"))
    base.update(kw)
    return ReleaseShapingRecord(**base)


def shaping_record(**kw):
    base = dict(release="R-05",
                work="release-2026-11-a",
                date="2026-11-13", disposition="SHAPING",
                owner="yrsa",
                proof_kind="partially-held",
                stages=STAGES,
                claims=("test_ref",))
    base.update(kw)
    return ReleaseShapingRecord(**base)


def not_ready_record(**kw):
    base = dict(release="R-07",
                work="release-2026-11-a",
                date="2026-11-13", disposition="NOT_READY",
                owner="yrsa",
                proof_kind="none",
                stages=STAGES,
                claims=("test_ref",))
    base.update(kw)
    return ReleaseShapingRecord(**base)


def full_book(**overrides):
    records = []
    for release_id in default_registry().combinations():
        if release_id in ("R-01", "R-02", "R-03"):
            kw = dict(release=release_id, work="release-2026-11-a",
                      date="2026-11-13", disposition="READY",
                      owner="yrsa",
                      proof_kind="ready-and-held",
                      stages=STAGES,
                      claims=("evidence_ref", "test_ref"))
        elif release_id in ("R-04", "R-05", "R-06", "R-07"):
            kw = dict(release=release_id, work="release-2026-11-a",
                      date="2026-11-13", disposition="SHAPING",
                      owner="yrsa",
                      proof_kind="partially-held",
                      stages=STAGES,
                      claims=("test_ref",))
        else:
            kw = dict(release=release_id, work="release-2026-11-a",
                      date="2026-11-13", disposition="NOT_READY",
                      owner="yrsa",
                      proof_kind="none",
                      stages=STAGES,
                      claims=("test_ref",))
        kw.update(overrides.get(release_id, {}))
        records.append(ReleaseShapingRecord(**kw))
    return records


def test_registry_holds_twelve_releases_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "R-01"
    assert reg.ids()[-1] == "R-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_releases_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("R-01").doctrine == "version-truth"
    assert reg.get("R-01").subject == "version-number"
    assert reg.get("R-02").subject == "release-notes-shape"
    assert reg.get("R-03").subject == "readiness-gate"
    assert reg.get("R-04").subject == "release-shape"
    assert reg.get("R-11").doctrine == "version-truth"
    assert reg.get("R-11").subject == "install-shape"
    assert reg.get("R-12").doctrine == "release-duty"
    assert DISPOSITIONS == ("READY", "SHAPING", "NOT_READY")


def test_registry_unknown_release_refused_by_name():
    with pytest.raises(ValidationError, match="unknown release: C-99"):
        default_registry().get("C-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate release"):
        ReleaseShapingRegistry(RELEASES + RELEASES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        ReleaseShapingRegistry([ReleaseShapingEntry("R-01", "version-truth", "version-number", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        ReleaseShapingRegistry([ReleaseShapingEntry("R-01", "version-truth", "version-number", "published", "why")])
    with pytest.raises(ValidationError, match="labelled"):
        ReleaseShapingRegistry([ReleaseShapingEntry("R-01", "version-truth", "version-number", "listed", "why", labelled=False)])
    with pytest.raises(ValidationError, match="evidenced"):
        ReleaseShapingRegistry([ReleaseShapingEntry("R-01", "version-truth", "version-number", "listed", "why", evidenced=False)])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown release doctrine"):
        ReleaseShapingRegistry([ReleaseShapingEntry("R-01", "M-999", "version-number", "listed", "why")])


def test_record_ready_measured_and_held_stands_held():
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


def test_record_ready_on_shaping_proof_stands_open():
    standing = derive_standing(fresh_record(proof_kind="partially-held"))
    assert not standing.held
    assert any("tells the truth" in g for g in standing.gaps)


def test_record_ready_without_evidence_ref_stands_open():
    standing = derive_standing(fresh_record(claims=("test_ref",)))
    assert not standing.held
    assert any("no held" in g for g in standing.gaps)


def test_record_ready_on_bare_claims_stands_open():
    standing = derive_standing(fresh_record(claims=("feeling",)))
    assert not standing.held
    assert any("bare claims only" in g for g in standing.gaps)


def test_record_shaping_with_owner_stands_held():
    standing = derive_standing(shaping_record())
    assert standing.held
    assert standing.grade == "held"


def test_record_shaping_without_owner_stands_open():
    standing = derive_standing(shaping_record(owner=""))
    assert not standing.held
    assert any("not a road" in g for g in standing.gaps)


def test_record_not_ready_silent_stands_open():
    standing = derive_standing(not_ready_record(claims=()))
    assert not standing.held
    assert any("silent" in g for g in standing.gaps)


def test_record_without_date_stands_open():
    standing = derive_standing(fresh_record(date=""))
    assert not standing.held
    assert any("no report date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_ready_with_shaping_releases():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.ready_releases == ("R-01", "R-02", "R-03")
    assert len(verdict.shaping_releases) == 4
    assert len(verdict.not_ready_releases) == 5
    assert verdict.missing_releases == ()


def test_verdict_missing_release_stops_the_report():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_releases == ("R-12",)
    assert any("R-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_report():
    verdict = derive_verdict(full_book(**{"R-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("R-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_release_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("release-a", "R-01", "findings as dispositioned",
                            "2026-11-13", 3, 4, 5, 12,
                            claims=("evidence_ref",))
    assert report.state == "ready"
    shared = prepare_report("release-a", "R-01", "findings as dispositioned",
                            "2026-11-13", 3, 4, 5, 12,
                            claims=("evidence_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("release-a", "R-01", "findings", "2026-11-13",
                       3, 4, 5, 12, claims=("evidence_ref",), state="sealed")
    with pytest.raises(ValidationError, match="release complete"):
        prepare_report("release-a", "R-01", "findings", "2026-11-13",
                       3, 2, 2, 12, claims=("evidence_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("release-a", "R-01", "findings", "2026-11-13",
                       3, 4, 5, 12, claims=("feeling",))
    assert "R-01" in format_release(default_registry().get("R-01"))
    assert "R-12" in format_releases()
    assert "READY" in format_record(fresh_record())
    assert "SHAPING" in format_records([shaping_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
    from pathlib import Path as _P
    _src = (_P(__file__).resolve().parent.parent
            / "mythic_agent" / "core" / "release_shaping.py").read_text(
                encoding="utf-8")
    assert "open(" not in _src
    assert "socket" not in _src
    assert "subprocess" not in _src
    assert "urllib" not in _src


# ---------------------------------------------------------------------
# M-269 Release shaping - agent layer. The pure book is held
# by a session registry in the agent layer alone: releases are read
# from the shipped registry, capture records are held one by one for
# the session, records, viewed standings and held reports are
# published as session news through the checkpoint road
# (journal-first, deduped per record, standing and verdict),
# standings, the index and the verdict are derived at call time from
# the held records - an release stands held only when its finding
# counts READY on ready-and-held evidence resting on held local
# evidence, or stands SHAPING or NOT READY with a named owner in the open -
# audit reports are held only as reports, state ready by default,
# may be marked shared by a human, a certification claimed only
# when every release stands answered, and never inflated, and the
# registry is session state, never a stored setting. This layer
# runs no attack, reads no sandbox code and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    RELEASESHAPING_USAGE,
    parse_releaseshaping_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.release_shaping import (
    PLAIN_EXPLANATION,
    RELEASE_SHAPING_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_RS_EVENT_TYPES = (
    "releaseshaping_record", "releaseshaping_standing",
    "releaseshaping_verdict")

ALL_FAMILIES = ["R-01", "R-02", "R-03", "R-04", "R-05", "R-06",
             "R-07", "R-08", "R-09", "R-10", "R-11", "R-12"]


def _rs_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _rs_record(**overrides):
    raw = {
        "release": "R-01",
        "work": "release-2026-11-a",
        "date": "2026-11-13",
        "disposition": "READY",
        "owner": "yrsa",
        "proof_kind": "ready-and-held",
        "stages": list(STAGES),
        "claims": ["evidence_ref", "test_ref"],
    }
    raw.update(overrides)
    return raw


def _rs_fresh_for(release, work="release-2026-11-a"):
    return _rs_record(release=release, work=work)


class TestReleaseShapingAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_releases(
            self, agent):
        status = agent.releaseshaping_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["releaseshaping_book"]["schema"] == (
            RELEASE_SHAPING_SCHEMA)
        assert [c["id"] for c in status[
            "releaseshaping_book"]["releases"]] == ALL_FAMILIES
        assert status["releaseshaping_book"]["records"] == []
        assert status["releaseshaping_book"]["reports"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "R-01" in status["releases_text"]
        assert "standing listed" in status["releases_text"]
        assert "none recorded this session" in status["screen"]
        assert "release shaping" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == RELEASESHAPING_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._releaseshaping_registry()
        assert agent._releaseshaping_registry() is first
        assert agent._releaseshaping_store is first
        for name in ("releaseshaping_releases",
                     "releaseshaping_book",
                     "releaseshaping_status",
                     "get_releaseshaping_release",
                     "get_releaseshaping_record",
                     "releaseshaping_standing",
                     "releases_for_disposition",
                     "releaseshaping_held",
                     "releaseshaping_index",
                     "releaseshaping_verdict",
                     "prepare_releaseshaping_report",
                     "get_releaseshaping_report",
                     "releaseshaping_reports",
                     "report_releaseshaping"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_releaseshaping_registry",
            "releaseshaping_releases",
            "releaseshaping_book",
            "releaseshaping_status",
            "get_releaseshaping_release",
            "get_releaseshaping_record",
            "releaseshaping_standing", "releases_for_disposition",
            "releaseshaping_held", "releaseshaping_index",
            "releaseshaping_verdict",
            "register_releaseshaping_record",
            "register_releaseshaping_records",
            "record_releaseshaping_records",
            "view_releaseshaping",
            "prepare_releaseshaping_report",
            "get_releaseshaping_report",
            "releaseshaping_reports",
            "report_releaseshaping",
            "_publish_releaseshaping_record",
            "_releaseshaping_screen",
            "_releaseshaping_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.releaseshaping_status()
        entry = agent.get_releaseshaping_release("R-01")
        assert entry.doctrine == "version-truth"
        assert entry.subject == "version-number"
        standing = agent.releaseshaping_standing("R-01")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.grade == "open"
        assert agent.releaseshaping_held() == []
        assert agent.releases_for_disposition("READY") == []
        agent.releaseshaping_index()
        agent.releaseshaping_verdict()
        agent.report_releaseshaping()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _RS_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown release"):
            agent.get_releaseshaping_release("guess")
        with pytest.raises(ValueError, match="unknown release"):
            agent.releaseshaping_standing("guess")
        with pytest.raises(ValueError, match="holds no"):
            agent.get_releaseshaping_record("R-01")
        with pytest.raises(ValueError):
            agent.releases_for_disposition("")
        agent.close()


class TestReleaseShapingAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_releaseshaping_record(
            _rs_record())
        assert result["record"]["release"] == "R-01"
        assert result["record_news"]["type"] == (
            "releaseshaping_record")
        assert "held as answered" in result["screen"]
        status = agent.releaseshaping_status()
        assert [r["release"] for r in status["records"]] == [
            "R-01"]
        assert status["book"]["records"][0]["work"] == (
            "release-2026-11-a")
        assert status["held"] == ["R-01"]
        assert status["open"] == []
        assert "held as answered" in status["records_text"]
        assert len(_rs_records(
            store, session_id, "releaseshaping_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_releaseshaping_record(_rs_record())
        with pytest.raises(ValueError, match="R-01"):
            agent.register_releaseshaping_record(
                _rs_record(work="release-2026-11-b"))
        assert len(_rs_records(
            store, session_id, "releaseshaping_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_releaseshaping_record(
                _rs_record(claims=["vibes"]))
        assert agent.releaseshaping_status()["records"] == []
        assert _rs_records(
            store, session_id, "releaseshaping_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_releaseshaping_records([
            _rs_fresh_for("R-02"), _rs_record()])
        assert result["count"] == 2
        assert [r["release"] for r in result["records_news"]] == [
            "R-02", "R-01"]
        assert len(_rs_records(
            store, session_id, "releaseshaping_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_releaseshaping_records(
            [_rs_fresh_for("R-02")])
        assert result["count"] == 1
        assert result["book"]["schema"] == (
            RELEASE_SHAPING_SCHEMA)
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_releaseshaping_records(
                [_rs_fresh_for("R-02")])
        assert len(_rs_records(
            store, session_id, "releaseshaping_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_releaseshaping_record(_rs_record())
        result = agent.view_releaseshaping("R-01")
        assert result["release"]["id"] == "R-01"
        assert result["standing"]["held"] is True
        assert result["record"]["work"] == "release-2026-11-a"
        assert result["record_news"]["type"] == (
            "releaseshaping_standing")
        assert result["held_record_news"]["type"] == (
            "releaseshaping_record")
        assert len(_rs_records(
            store, session_id, "releaseshaping_record")) == 1
        assert len(_rs_records(
            store, session_id, "releaseshaping_standing")) == 1
        result = agent.view_releaseshaping("R-03")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_rs_records(
            store, session_id, "releaseshaping_standing")) == 2
        agent.close()


class TestReleaseShapingReports:
    def test_prepare_report_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_releaseshaping_report(
            "release-2026-11", "release-1",
            "every release answered",
            "2026-11-13", 3, 4, 5, 12,
            claims=("evidence_ref", "test_ref"))
        assert result["report"]["state"] == "ready"
        assert result["report"]["certified"] is False
        assert result["report"]["inflated"] is False
        assert result["report_news"]["type"] == (
            "releaseshaping_verdict")
        assert "every release answered" in result["screen"]
        report = agent.get_releaseshaping_report(
            "release-2026-11")
        assert report.entry == "release-1"
        assert [r.book for r in
                agent.releaseshaping_reports()] == [
            "release-2026-11"]
        assert len(_rs_records(
            store, session_id, "releaseshaping_verdict")) == 1
        agent.close()

    def test_report_unshared_state_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared"):
            agent.prepare_releaseshaping_report(
                "release-2026-11", "release-1", "x",
                "2026-11-13", 3, 4, 5, 12,
                claims=("evidence_ref",), state="executed")
        assert agent.releaseshaping_reports() == []
        assert _rs_records(
            store, session_id, "releaseshaping_verdict") == []
        agent.close()

    def test_duplicate_report_refuses(self, agent):
        agent.prepare_releaseshaping_report(
            "release-2026-11", "release-1",
            "every release answered", "2026-11-13", 3, 4, 5, 12,
            claims=("evidence_ref",))
        with pytest.raises(ValueError, match="release-2026-11"):
            agent.prepare_releaseshaping_report(
                "release-2026-11", "release-2",
                "a second telling", "2026-11-13", 3, 4, 5, 12,
                claims=("evidence_ref",))
        with pytest.raises(ValueError,
                           match="holds no"):
            agent.get_releaseshaping_report("release-2026-12")


class TestReleaseShapingParseArgs:
    def test_parse_args_well(self):
        assert parse_releaseshaping_args("") == (
            "show", None, (), None)
        assert parse_releaseshaping_args(None) == (
            "show", None, (), None)
        assert parse_releaseshaping_args("releases") == (
            "releases", None, (), None)
        assert parse_releaseshaping_args(
            "release R-01") == (
            "release", "R-01", (), None)
        assert parse_releaseshaping_args(
            "record R-01") == (
            "record", "R-01", (), None)
        assert parse_releaseshaping_args(
            "standing R-02") == (
            "standing", "R-02", (), None)
        assert parse_releaseshaping_args("report") == (
            "reports", None, (), None)
        assert parse_releaseshaping_args(
            "report release-2026-11") == (
            "report", "release-2026-11", (), None)
        assert parse_releaseshaping_args("verdict") == (
            "verdict", None, (), None)
        assert parse_releaseshaping_args("index") == (
            "index", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "release", "record",
                    "record R-01 extra",
                    "releases now", "standing",
                    "report a b"):
            with pytest.raises(ValueError) as caught:
                parse_releaseshaping_args(bad)
            assert str(caught.value) == RELEASESHAPING_USAGE


class TestReleaseShapingTerminalRoad:
    def test_show_releases_release_record_standing_report_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/releaseshaping")
        assert "R-01" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/releaseshaping releases")
        assert "version-number" in text
        assert "R-03" in text
        _, _, text = _slash(
            agent, "/releaseshaping release R-01")
        assert "version-number" in text
        _, _, text = _slash(
            agent, "/releaseshaping record R-01")
        assert "holds no" in text
        _, _, text = _slash(
            agent, "/releaseshaping standing R-01")
        assert "R-01:" in text
        assert "open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/releaseshaping report")
        assert "none held" in text
        _, _, text = _slash(agent, "/releaseshaping verdict")
        assert "Release shaping stands open" in text
        agent.register_releaseshaping_record(_rs_record())
        _, _, text = _slash(
            agent, "/releaseshaping record R-01")
        assert "held as answered" in text
        _, _, text = _slash(
            agent, "/releaseshaping standing R-01")
        assert "held as answered" in text
        _, _, text = _slash(agent, "/releaseshaping index")
        assert "held as answered" in text
        agent.prepare_releaseshaping_report(
            "release-2026-11", "release-1",
            "every release answered", "2026-11-13", 3, 4, 5, 12,
            claims=("evidence_ref",))
        _, _, text = _slash(
            agent, "/releaseshaping report release-2026-11")
        assert "every release answered" in text
        assert "never inflated" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/releaseshaping [show|releases|"
                "release <release>|"
                "record <release>|"
                "standing <release>|"
                "report [<book>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/releaseshaping dance party")
        assert text == RELEASESHAPING_USAGE
        _, _, text = _slash(
            agent, "/releaseshaping release guess")
        assert "unknown release" in text


@pytest.fixture()
def rs_handler(agent, monkeypatch):
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


def _rs_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestReleaseShapingHandler:
    def test_show_is_default(self, rs_handler, agent):
        rs_handler._handle_releaseshaping("")
        assert "R-01" in (
            _rs_published_text(rs_handler))
        assert "version-number" in (
            _rs_published_text(rs_handler))

    def test_release_record_and_verdict(
            self, rs_handler, agent):
        rs_handler._handle_releaseshaping(
            "release R-01")
        assert "version-number" in (
            _rs_published_text(rs_handler))
        agent.register_releaseshaping_record(_rs_record())
        rs_handler._handle_releaseshaping(
            "record R-01")
        assert "held as answered" in (
            _rs_published_text(rs_handler))
        rs_handler._handle_releaseshaping("verdict")
        assert "Release shaping stands held" in (
            _rs_published_text(rs_handler))

    def test_bad_grammar_is_published(
            self, rs_handler, agent):
        rs_handler._handle_releaseshaping("dance party")
        assert RELEASESHAPING_USAGE in (
            _rs_published_text(rs_handler))
        rs_handler._handle_releaseshaping("release guess")
        assert "unknown release" in (
            _rs_published_text(rs_handler))


class TestChatScreenRoutingReleaseShaping:
    def test_releases_as_system_command(self, monkeypatch):
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
        screen.handle_command("/releaseshaping verdict",
                              _FakeLog())
        assert calls == [("/releaseshaping", "verdict")]

    def test_chat_screen_help_and_usage_name_the_audit(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/releaseshaping[/green] - show the "
                "Release shaping (M-269)") in text
        assert ('"/releaseshaping": "Usage: '
                "/releaseshaping | "
                "/releaseshaping releases") in text


class TestReleaseShapingDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.releaseshaping_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _RS_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        _rp = ROOT / "README.md"
        _rb = _rp.read_bytes() if _rp.exists() else None
        verdict = agent.releaseshaping_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_releaseshaping_record(_rs_record())
        agent.register_releaseshaping_record(
            _rs_fresh_for("R-02", work="release-2026-11-b"))
        verdict = agent.releaseshaping_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "R-01", "R-02"]
        assert "Release shaping stands held" in (
            verdict["verdict_text"])
        assert not _rp.exists() or _rp.read_bytes() == _rb

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_releaseshaping()
        assert report["book"]["schema"] == (
            RELEASE_SHAPING_SCHEMA)
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_releaseshaping_record(_rs_record())
        report = agent.report_releaseshaping()
        assert "held as answered" in report["records_text"]
        assert [s["release"] for s in report["standings"]] == [
            "R-01"]

    def test_releases_for_disposition_and_held_keys(self, agent):
        agent.register_releaseshaping_record(_rs_record())
        agent.register_releaseshaping_record(
            _rs_fresh_for("R-02", work="release-2026-11-b"))
        agent.register_releaseshaping_record(_rs_record(
            release="R-03", work="release-2026-11-c",
            disposition="NOT_READY", owner="",
            proof_kind="none",
            stages=["named"], claims=["assertion"]))
        assert [r.work for r in
                agent.releases_for_disposition("READY")] == [
            "release-2026-11-a", "release-2026-11-b"]
        assert agent.releaseshaping_held() == ["R-01", "R-02"]
        standing = agent.releaseshaping_standing(
            "R-03")
        assert standing.held is False
