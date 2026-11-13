"""M-264 README care - pure-layer tests.

TIER: unit

The repo README extended by hand with the new story,
nothing removed: a section counts EXTENDED only on
hand extension against the README as it stands resting
on held README evidence, and a roaded section with no
owner named stands open.
"""
import pytest

from mythic_agent.core.readme_care import (
    SECTIONS,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    CareEntry,
    CareRegistry,
    CareRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_section,
    format_sections,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(section="R-03",
                work="readme-2026-11-a",
                date="2026-11-13", disposition="EXTENDED",
                owner="yrsa",
                proof_kind="extended-by-hand",
                stages=STAGES,
                claims=("readme_ref", "journal_ref"))
    base.update(kw)
    return CareRecord(**base)


def roaded_record(**kw):
    base = dict(section="R-05",
                work="readme-2026-11-a",
                date="2026-11-13", disposition="ROADED",
                owner="yrsa",
                proof_kind="extended-by-hand",
                stages=STAGES,
                claims=("journal_ref",))
    base.update(kw)
    return CareRecord(**base)


def full_book(**overrides):
    records = []
    for section_id in default_registry().combinations():
        if section_id in ("R-01", "R-02", "R-03"):
            kw = dict(section=section_id, work="readme-2026-11-a",
                      date="2026-11-13", disposition="EXTENDED",
                      owner="yrsa",
                      proof_kind="extended-by-hand",
                      stages=STAGES,
                      claims=("readme_ref", "journal_ref"))
        else:
            kw = dict(section=section_id, work="readme-2026-11-a",
                      date="2026-11-13", disposition="ROADED",
                      owner="yrsa",
                      proof_kind="extended-by-hand",
                      stages=STAGES,
                      claims=("journal_ref",))
        kw.update(overrides.get(section_id, {}))
        records.append(CareRecord(**kw))
    return records


def test_registry_holds_twelve_sections_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "R-01"
    assert reg.ids()[-1] == "R-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_sections_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("R-01").doctrine == "new-story"
    assert reg.get("R-01").subject == "opening-story"
    assert reg.get("R-03").subject == "provider-ocean-story"
    assert reg.get("R-05").subject == "sandbox-story"
    assert reg.get("R-11").doctrine == "standing-law"
    assert reg.get("R-11").subject == "care-law-note"
    assert reg.get("R-12").doctrine == "care-duty"
    assert DISPOSITIONS == ("EXTENDED", "ROADED")


def test_registry_unknown_section_refused_by_name():
    with pytest.raises(ValidationError, match="unknown section: R-99"):
        default_registry().get("R-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate section"):
        CareRegistry(SECTIONS + SECTIONS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        CareRegistry([CareEntry("R-01", "M-199", "keyboard-task", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        CareRegistry([CareEntry("R-01", "standing-law", "opening-story", "published", "why")])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown section doctrine"):
        CareRegistry([CareEntry("R-01", "M-999", "keyboard-task", "listed", "why")])


def test_record_extended_by_hand_stands_held():
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


def test_record_reconciled_on_historical_evidence_stands_open():
    standing = derive_standing(fresh_record(proof_kind="historical-only"))
    assert not standing.held
    assert any("no inheritance" in g for g in standing.gaps)


def test_record_reconciled_without_code_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("journal_ref",)))
    assert not standing.held
    assert any("no held README evidence" in g for g in standing.gaps)


def test_record_reconciled_on_bare_claims_stands_open():
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
    assert any("no care date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_ready_with_roaded_sections():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.extended_sections == ("R-01", "R-02", "R-03")
    assert len(verdict.roaded_sections) == 9
    assert verdict.missing_sections == ()


def test_verdict_missing_section_stops_the_readme():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_sections == ("R-12",)
    assert any("R-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_readme():
    verdict = derive_verdict(full_book(**{"R-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("R-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_section_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("readme-a", "R-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("readme_ref",))
    assert report.state == "ready"
    shared = prepare_report("readme-a", "R-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("readme_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("readme-a", "R-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("readme_ref",), state="sealed")
    with pytest.raises(ValidationError, match="README complete"):
        prepare_report("readme-a", "R-01", "findings", "2026-11-13",
                       3, 5, 12, claims=("readme_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("readme-a", "R-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("feeling",))
    assert "R-01" in format_section(default_registry().get("R-01"))
    assert "R-12" in format_sections()
    assert "EXTENDED" in format_record(fresh_record())
    assert "ROADED" in format_records([roaded_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
    from pathlib import Path as _P
    _src = (_P(__file__).resolve().parent.parent
            / "mythic_agent" / "core" / "readme_care.py").read_text(
                encoding="utf-8")
    assert "README.md" not in _src
    assert "open(" not in _src
    assert "socket" not in _src
    assert "subprocess" not in _src
    assert "urllib" not in _src

# ---------------------------------------------------------------------


# ---------------------------------------------------------------------
# M-264 README care - agent layer. The pure book is held
# by a session registry in the agent layer alone: guides are read
# from the shipped registry, capture records are held one by one for
# the session, records, viewed standings and held reports are
# published as session news through the checkpoint road
# (journal-first, deduped per record, standing and verdict),
# standings, the index and the verdict are derived at call time from
# the held records - an guide stands held only when its finding
# counts RECONCILED on reconciled-with-code evidence resting on held local
# evidence, or stands ROADED with a named owner in the open -
# audit reports are held only as reports, state ready by default,
# may be marked shared by a human, a certification claimed only
# when every guide stands answered, and never inflated, and the
# registry is session state, never a stored setting. This layer
# runs no attack, reads no sandbox code and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    READMECARE_USAGE,
    parse_readmecare_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.readme_care import (
    PLAIN_EXPLANATION,
    README_CARE_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_RC_EVENT_TYPES = (
    "readmecare_record", "readmecare_standing",
    "readmecare_verdict")

ALL_SECTIONS = ["R-01", "R-02", "R-03", "R-04", "R-05", "R-06",
             "R-07", "R-08", "R-09", "R-10", "R-11", "R-12"]


def _rc_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _rc_record(**overrides):
    raw = {
        "section": "R-01",
        "work": "readme-2026-11-a",
        "date": "2026-11-13",
        "disposition": "EXTENDED",
        "owner": "yrsa",
        "proof_kind": "extended-by-hand",
        "stages": list(STAGES),
        "claims": ["readme_ref", "journal_ref"],
    }
    raw.update(overrides)
    return raw


def _rc_fresh_for(section, work="readme-2026-11-a"):
    return _rc_record(section=section, work=work)


class TestReadmeCareAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_areas(
            self, agent):
        status = agent.readmecare_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["readmecare_book"]["schema"] == (
            README_CARE_SCHEMA)
        assert [c["id"] for c in status[
            "readmecare_book"]["sections"]] == ALL_SECTIONS
        assert status["readmecare_book"]["records"] == []
        assert status["readmecare_book"]["reports"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "R-01" in status["sections_text"]
        assert "standing listed" in status["sections_text"]
        assert "none recorded this session" in status["screen"]
        assert "README care" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == READMECARE_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._readmecare_registry()
        assert agent._readmecare_registry() is first
        assert agent._readmecare_store is first
        for name in ("readmecare_sections",
                     "readmecare_book",
                     "readmecare_status",
                     "get_readmecare_section",
                     "get_readmecare_record",
                     "readmecare_standing",
                     "sections_for_disposition",
                     "readmecare_held",
                     "readmecare_index",
                     "readmecare_verdict",
                     "prepare_readmecare_report",
                     "get_readmecare_report",
                     "readmecare_reports",
                     "report_readmecare"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_readmecare_registry",
            "readmecare_sections",
            "readmecare_book",
            "readmecare_status",
            "get_readmecare_section",
            "get_readmecare_record",
            "readmecare_standing", "sections_for_disposition",
            "readmecare_held", "readmecare_index",
            "readmecare_verdict",
            "register_readmecare_record",
            "register_readmecare_records",
            "record_readmecare_records",
            "view_readmecare",
            "prepare_readmecare_report",
            "get_readmecare_report",
            "readmecare_reports",
            "report_readmecare",
            "_publish_readmecare_record",
            "_readmecare_screen",
            "_readmecare_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.readmecare_status()
        entry = agent.get_readmecare_section("R-01")
        assert entry.doctrine == "new-story"
        assert entry.subject == "opening-story"
        standing = agent.readmecare_standing("R-01")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.grade == "open"
        assert agent.readmecare_held() == []
        assert agent.sections_for_disposition("EXTENDED") == []
        agent.readmecare_index()
        agent.readmecare_verdict()
        agent.report_readmecare()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _RC_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown section"):
            agent.get_readmecare_section("guess")
        with pytest.raises(ValueError, match="unknown section"):
            agent.readmecare_standing("guess")
        with pytest.raises(ValueError, match="holds no"):
            agent.get_readmecare_record("R-01")
        with pytest.raises(ValueError):
            agent.sections_for_disposition("")
        agent.close()


class TestReadmeCareAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_readmecare_record(
            _rc_record())
        assert result["record"]["section"] == "R-01"
        assert result["record_news"]["type"] == (
            "readmecare_record")
        assert "held as answered" in result["screen"]
        status = agent.readmecare_status()
        assert [r["section"] for r in status["records"]] == [
            "R-01"]
        assert status["book"]["records"][0]["work"] == (
            "readme-2026-11-a")
        assert status["held"] == ["R-01"]
        assert status["open"] == []
        assert "held as answered" in status["records_text"]
        assert len(_rc_records(
            store, session_id, "readmecare_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_readmecare_record(_rc_record())
        with pytest.raises(ValueError, match="R-01"):
            agent.register_readmecare_record(
                _rc_record(work="readme-2026-11-b"))
        assert len(_rc_records(
            store, session_id, "readmecare_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_readmecare_record(
                _rc_record(claims=["vibes"]))
        assert agent.readmecare_status()["records"] == []
        assert _rc_records(
            store, session_id, "readmecare_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_readmecare_records([
            _rc_fresh_for("R-05"), _rc_record()])
        assert result["count"] == 2
        assert [r["section"] for r in result["records_news"]] == [
            "R-05", "R-01"]
        assert len(_rc_records(
            store, session_id, "readmecare_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_readmecare_records(
            [_rc_fresh_for("R-05")])
        assert result["count"] == 1
        assert result["book"]["schema"] == (
            README_CARE_SCHEMA)
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_readmecare_records(
                [_rc_fresh_for("R-05")])
        assert len(_rc_records(
            store, session_id, "readmecare_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_readmecare_record(_rc_record())
        result = agent.view_readmecare("R-01")
        assert result["section"]["id"] == "R-01"
        assert result["standing"]["held"] is True
        assert result["record"]["work"] == "readme-2026-11-a"
        assert result["record_news"]["type"] == (
            "readmecare_standing")
        assert result["held_record_news"]["type"] == (
            "readmecare_record")
        assert len(_rc_records(
            store, session_id, "readmecare_record")) == 1
        assert len(_rc_records(
            store, session_id, "readmecare_standing")) == 1
        result = agent.view_readmecare("R-02")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_rc_records(
            store, session_id, "readmecare_standing")) == 2
        agent.close()


class TestReadmeCareReports:
    def test_prepare_report_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_readmecare_report(
            "readme-2026-11", "release-1",
            "every guide answered",
            "2026-11-13", 1, 11, 12,
            claims=("local_run_ref", "journal_ref"))
        assert result["report"]["state"] == "ready"
        assert result["report"]["certified"] is False
        assert result["report"]["inflated"] is False
        assert result["report_news"]["type"] == (
            "readmecare_verdict")
        assert "every guide answered" in result["screen"]
        report = agent.get_readmecare_report(
            "readme-2026-11")
        assert report.entry == "release-1"
        assert [r.book for r in
                agent.readmecare_reports()] == [
            "readme-2026-11"]
        assert len(_rc_records(
            store, session_id, "readmecare_verdict")) == 1
        agent.close()

    def test_report_unshared_state_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared"):
            agent.prepare_readmecare_report(
                "readme-2026-11", "release-1", "x",
                "2026-11-13", 1, 11, 12,
                claims=("local_run_ref",), state="executed")
        assert agent.readmecare_reports() == []
        assert _rc_records(
            store, session_id, "readmecare_verdict") == []
        agent.close()

    def test_duplicate_report_refuses(self, agent):
        agent.prepare_readmecare_report(
            "readme-2026-11", "release-1",
            "every guide answered", "2026-11-13", 1, 11, 12,
            claims=("local_run_ref",))
        with pytest.raises(ValueError, match="readme-2026-11"):
            agent.prepare_readmecare_report(
                "readme-2026-11", "release-2",
                "a second telling", "2026-11-13", 1, 11, 12,
                claims=("local_run_ref",))
        with pytest.raises(ValueError,
                           match="holds no"):
            agent.get_readmecare_report("readme-2026-12")


class TestReadmeCareParseArgs:
    def test_parse_args_well(self):
        assert parse_readmecare_args("") == (
            "show", None, (), None)
        assert parse_readmecare_args(None) == (
            "show", None, (), None)
        assert parse_readmecare_args("sections") == (
            "sections", None, (), None)
        assert parse_readmecare_args(
            "section R-01") == (
            "section", "R-01", (), None)
        assert parse_readmecare_args(
            "record R-01") == (
            "record", "R-01", (), None)
        assert parse_readmecare_args(
            "standing R-03") == (
            "standing", "R-03", (), None)
        assert parse_readmecare_args("report") == (
            "reports", None, (), None)
        assert parse_readmecare_args(
            "report readme-2026-11") == (
            "report", "readme-2026-11", (), None)
        assert parse_readmecare_args("verdict") == (
            "verdict", None, (), None)
        assert parse_readmecare_args("index") == (
            "index", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "section", "record",
                    "record R-01 extra",
                    "sections now", "standing",
                    "report a b"):
            with pytest.raises(ValueError) as caught:
                parse_readmecare_args(bad)
            assert str(caught.value) == READMECARE_USAGE


class TestReadmeCareTerminalRoad:
    def test_show_areas_area_record_standing_report_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/readmecare")
        assert "R-01" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/readmecare sections")
        assert "opening-story" in text
        assert "R-12" in text
        _, _, text = _slash(
            agent, "/readmecare section R-01")
        assert "opening-story" in text
        _, _, text = _slash(
            agent, "/readmecare record R-01")
        assert "holds no" in text
        _, _, text = _slash(
            agent, "/readmecare standing R-01")
        assert "R-01:" in text
        assert "open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/readmecare report")
        assert "none held" in text
        _, _, text = _slash(agent, "/readmecare verdict")
        assert "README care stands open" in text
        agent.register_readmecare_record(_rc_record())
        _, _, text = _slash(
            agent, "/readmecare record R-01")
        assert "held as answered" in text
        _, _, text = _slash(
            agent, "/readmecare standing R-01")
        assert "held as answered" in text
        _, _, text = _slash(agent, "/readmecare index")
        assert "held as answered" in text
        agent.prepare_readmecare_report(
            "readme-2026-11", "release-1",
            "every guide answered", "2026-11-13", 1, 11, 12,
            claims=("local_run_ref",))
        _, _, text = _slash(
            agent, "/readmecare report readme-2026-11")
        assert "every guide answered" in text
        assert "never inflated" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/readmecare [show|sections|"
                "section <section>|"
                "record <section>|"
                "standing <section>|"
                "report [<book>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/readmecare dance party")
        assert text == READMECARE_USAGE
        _, _, text = _slash(
            agent, "/readmecare section guess")
        assert "unknown section" in text


@pytest.fixture()
def rc_handler(agent, monkeypatch):
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


def _rc_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestReadmeCareHandler:
    def test_show_is_default(self, rc_handler, agent):
        rc_handler._handle_readmecare("")
        assert "R-01" in (
            _rc_published_text(rc_handler))
        assert "opening-story" in (
            _rc_published_text(rc_handler))

    def test_area_record_and_verdict(
            self, rc_handler, agent):
        rc_handler._handle_readmecare(
            "section R-01")
        assert "opening-story" in (
            _rc_published_text(rc_handler))
        agent.register_readmecare_record(_rc_record())
        rc_handler._handle_readmecare(
            "record R-01")
        assert "held as answered" in (
            _rc_published_text(rc_handler))
        rc_handler._handle_readmecare("verdict")
        assert "README care stands held" in (
            _rc_published_text(rc_handler))

    def test_bad_grammar_is_published(
            self, rc_handler, agent):
        rc_handler._handle_readmecare("dance party")
        assert READMECARE_USAGE in (
            _rc_published_text(rc_handler))
        rc_handler._handle_readmecare("section guess")
        assert "unknown section" in (
            _rc_published_text(rc_handler))


class TestChatScreenRoutingReadmeCare:
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
        screen.handle_command("/readmecare verdict",
                              _FakeLog())
        assert calls == [("/readmecare", "verdict")]

    def test_chat_screen_help_and_usage_name_the_audit(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/readmecare[/green] - show the "
                "README care (M-264)") in text
        assert ('"/readmecare": "Usage: '
                "/readmecare | "
                "/readmecare sections") in text


class TestReadmeCareDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.readmecare_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _RC_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        _rp = ROOT / "README.md"
        _rb = _rp.read_bytes() if _rp.exists() else None
        verdict = agent.readmecare_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_readmecare_record(_rc_record())
        agent.register_readmecare_record(
            _rc_fresh_for("R-05", work="readme-2026-11-b"))
        verdict = agent.readmecare_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "R-01", "R-05"]
        assert "README care stands held" in (
            verdict["verdict_text"])
        assert not _rp.exists() or _rp.read_bytes() == _rb

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_readmecare()
        assert report["book"]["schema"] == (
            README_CARE_SCHEMA)
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_readmecare_record(_rc_record())
        report = agent.report_readmecare()
        assert "held as answered" in report["records_text"]
        assert [s["section"] for s in report["standings"]] == [
            "R-01"]

    def test_sections_for_disposition_and_held_keys(self, agent):
        agent.register_readmecare_record(_rc_record())
        agent.register_readmecare_record(
            _rc_fresh_for("R-05", work="readme-2026-11-b"))
        agent.register_readmecare_record(_rc_record(
            section="R-02", work="readme-2026-11-c",
            disposition="ROADED", owner="",
            proof_kind="none",
            stages=["named"], claims=["assertion"]))
        assert [r.work for r in
                agent.sections_for_disposition("EXTENDED")] == [
            "readme-2026-11-a", "readme-2026-11-b"]
        assert agent.readmecare_held() == ["R-01", "R-05"]
        standing = agent.readmecare_standing(
            "R-02")
        assert standing.held is False
