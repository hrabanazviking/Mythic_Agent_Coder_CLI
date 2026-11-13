"""M-263 The docs completion - pure-layer tests.

TIER: unit

User guide, method guide, bridge guides and per-part
interface notes reconciled with shipped code: a guide
counts RECONCILED only on reconciliation against the
shipped code itself resting on held code evidence, and
a roaded guide with no owner named stands open.
"""
import pytest

from mythic_agent.core.docs_completion import (
    GUIDES,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    GuideEntry,
    GuideRegistry,
    DocRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_guide,
    format_guides,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(guide="D-03",
                work="docs-2026-11-a",
                date="2026-11-13", disposition="RECONCILED",
                owner="yrsa",
                proof_kind="reconciled-with-code",
                stages=STAGES,
                claims=("code_ref", "journal_ref"))
    base.update(kw)
    return DocRecord(**base)


def roaded_record(**kw):
    base = dict(guide="D-05",
                work="docs-2026-11-a",
                date="2026-11-13", disposition="ROADED",
                owner="yrsa",
                proof_kind="reconciled-with-code",
                stages=STAGES,
                claims=("journal_ref",))
    base.update(kw)
    return DocRecord(**base)


def full_book(**overrides):
    records = []
    for guide_id in default_registry().combinations():
        if guide_id in ("D-01", "D-02", "D-03"):
            kw = dict(guide=guide_id, work="docs-2026-11-a",
                      date="2026-11-13", disposition="RECONCILED",
                      owner="yrsa",
                      proof_kind="reconciled-with-code",
                      stages=STAGES,
                      claims=("code_ref", "journal_ref"))
        else:
            kw = dict(guide=guide_id, work="docs-2026-11-a",
                      date="2026-11-13", disposition="ROADED",
                      owner="yrsa",
                      proof_kind="reconciled-with-code",
                      stages=STAGES,
                      claims=("journal_ref",))
        kw.update(overrides.get(guide_id, {}))
        records.append(DocRecord(**kw))
    return records


def test_registry_holds_twelve_guides_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "D-01"
    assert reg.ids()[-1] == "D-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_guides_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("D-01").doctrine == "shipped-code"
    assert reg.get("D-01").subject == "user-guide"
    assert reg.get("D-03").subject == "bridge-guides"
    assert reg.get("D-05").subject == "install-and-setup"
    assert reg.get("D-11").doctrine == "method"
    assert reg.get("D-11").subject == "jarl-mode-guide"
    assert reg.get("D-12").doctrine == "shipped-code"
    assert DISPOSITIONS == ("RECONCILED", "ROADED")


def test_registry_unknown_guide_refused_by_name():
    with pytest.raises(ValidationError, match="unknown guide: D-99"):
        default_registry().get("D-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate guide"):
        GuideRegistry(GUIDES + GUIDES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        GuideRegistry([GuideEntry("D-01", "M-199", "keyboard-task", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        GuideRegistry([GuideEntry("D-01", "shipped-code", "user-guide", "published", "why")])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown guide doctrine"):
        GuideRegistry([GuideEntry("D-01", "M-999", "keyboard-task", "listed", "why")])


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


def test_record_reconciled_on_historical_evidence_stands_open():
    standing = derive_standing(fresh_record(proof_kind="historical-only"))
    assert not standing.held
    assert any("no inheritance" in g for g in standing.gaps)


def test_record_reconciled_without_code_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("journal_ref",)))
    assert not standing.held
    assert any("no held code evidence" in g for g in standing.gaps)


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
    assert any("no docs date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_ready_with_roaded_guides():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.reconciled_guides == ("D-01", "D-02", "D-03")
    assert len(verdict.roaded_guides) == 9
    assert verdict.missing_guides == ()


def test_verdict_missing_guide_stops_the_docs():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_guides == ("D-12",)
    assert any("D-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_docs():
    verdict = derive_verdict(full_book(**{"D-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("D-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_guide_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("docs-a", "D-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("code_ref",))
    assert report.state == "ready"
    shared = prepare_report("docs-a", "D-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("code_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("docs-a", "D-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("code_ref",), state="sealed")
    with pytest.raises(ValidationError, match="docs complete"):
        prepare_report("docs-a", "D-01", "findings", "2026-11-13",
                       3, 5, 12, claims=("code_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("docs-a", "D-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("feeling",))
    assert "D-01" in format_guide(default_registry().get("D-01"))
    assert "D-12" in format_guides()
    assert "RECONCILED" in format_record(fresh_record())
    assert "ROADED" in format_records([roaded_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)

# ---------------------------------------------------------------------


# ---------------------------------------------------------------------
# M-263 Docs completion - agent layer. The pure book is held
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
    DOCSCOMPLETION_USAGE,
    parse_docscompletion_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.docs_completion import (
    PLAIN_EXPLANATION,
    DOCS_COMPLETION_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_SA_EVENT_TYPES = (
    "docscompletion_record", "docscompletion_standing",
    "docscompletion_verdict")

ALL_GUIDES = ["D-01", "D-02", "D-03", "D-04", "D-05", "D-06",
             "D-07", "D-08", "D-09", "D-10", "D-11", "D-12"]


def _dc_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _dc_record(**overrides):
    raw = {
        "guide": "D-01",
        "work": "docs-2026-11-a",
        "date": "2026-11-13",
        "disposition": "RECONCILED",
        "owner": "yrsa",
        "proof_kind": "reconciled-with-code",
        "stages": list(STAGES),
        "claims": ["code_ref", "journal_ref"],
    }
    raw.update(overrides)
    return raw


def _dc_fresh_for(guide, work="docs-2026-11-a"):
    return _dc_record(guide=guide, work=work)


class TestDocsCompletionAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_areas(
            self, agent):
        status = agent.docscompletion_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["docscompletion_book"]["schema"] == (
            DOCS_COMPLETION_SCHEMA)
        assert [c["id"] for c in status[
            "docscompletion_book"]["guides"]] == ALL_GUIDES
        assert status["docscompletion_book"]["records"] == []
        assert status["docscompletion_book"]["reports"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "D-01" in status["guides_text"]
        assert "standing listed" in status["guides_text"]
        assert "none recorded this session" in status["screen"]
        assert "docs completion" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == DOCSCOMPLETION_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._docscompletion_registry()
        assert agent._docscompletion_registry() is first
        assert agent._docscompletion_store is first
        for name in ("docscompletion_guides",
                     "docscompletion_book",
                     "docscompletion_status",
                     "get_docscompletion_guide",
                     "get_docscompletion_record",
                     "docscompletion_standing",
                     "docs_for_disposition",
                     "docscompletion_held",
                     "docscompletion_index",
                     "docscompletion_verdict",
                     "prepare_docscompletion_report",
                     "get_docscompletion_report",
                     "docscompletion_reports",
                     "report_docscompletion"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_docscompletion_registry",
            "docscompletion_guides",
            "docscompletion_book",
            "docscompletion_status",
            "get_docscompletion_guide",
            "get_docscompletion_record",
            "docscompletion_standing", "docs_for_disposition",
            "docscompletion_held", "docscompletion_index",
            "docscompletion_verdict",
            "register_docscompletion_record",
            "register_docscompletion_records",
            "record_docscompletion_records",
            "view_docscompletion",
            "prepare_docscompletion_report",
            "get_docscompletion_report",
            "docscompletion_reports",
            "report_docscompletion",
            "_publish_docscompletion_record",
            "_docscompletion_screen",
            "_docscompletion_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.docscompletion_status()
        entry = agent.get_docscompletion_guide("D-01")
        assert entry.doctrine == "shipped-code"
        assert entry.subject == "user-guide"
        standing = agent.docscompletion_standing("D-01")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.grade == "open"
        assert agent.docscompletion_held() == []
        assert agent.docs_for_disposition("RECONCILED") == []
        agent.docscompletion_index()
        agent.docscompletion_verdict()
        agent.report_docscompletion()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _SA_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown guide"):
            agent.get_docscompletion_guide("guess")
        with pytest.raises(ValueError, match="unknown guide"):
            agent.docscompletion_standing("guess")
        with pytest.raises(ValueError, match="holds no"):
            agent.get_docscompletion_record("D-01")
        with pytest.raises(ValueError):
            agent.docs_for_disposition("")
        agent.close()


class TestDocsCompletionAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_docscompletion_record(
            _dc_record())
        assert result["record"]["guide"] == "D-01"
        assert result["record_news"]["type"] == (
            "docscompletion_record")
        assert "held as answered" in result["screen"]
        status = agent.docscompletion_status()
        assert [r["guide"] for r in status["records"]] == [
            "D-01"]
        assert status["book"]["records"][0]["work"] == (
            "docs-2026-11-a")
        assert status["held"] == ["D-01"]
        assert status["open"] == []
        assert "held as answered" in status["records_text"]
        assert len(_dc_records(
            store, session_id, "docscompletion_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_docscompletion_record(_dc_record())
        with pytest.raises(ValueError, match="D-01"):
            agent.register_docscompletion_record(
                _dc_record(work="docs-2026-11-b"))
        assert len(_dc_records(
            store, session_id, "docscompletion_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_docscompletion_record(
                _dc_record(claims=["vibes"]))
        assert agent.docscompletion_status()["records"] == []
        assert _dc_records(
            store, session_id, "docscompletion_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_docscompletion_records([
            _dc_fresh_for("D-05"), _dc_record()])
        assert result["count"] == 2
        assert [r["guide"] for r in result["records_news"]] == [
            "D-05", "D-01"]
        assert len(_dc_records(
            store, session_id, "docscompletion_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_docscompletion_records(
            [_dc_fresh_for("D-05")])
        assert result["count"] == 1
        assert result["book"]["schema"] == (
            DOCS_COMPLETION_SCHEMA)
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_docscompletion_records(
                [_dc_fresh_for("D-05")])
        assert len(_dc_records(
            store, session_id, "docscompletion_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_docscompletion_record(_dc_record())
        result = agent.view_docscompletion("D-01")
        assert result["guide"]["id"] == "D-01"
        assert result["standing"]["held"] is True
        assert result["record"]["work"] == "docs-2026-11-a"
        assert result["record_news"]["type"] == (
            "docscompletion_standing")
        assert result["held_record_news"]["type"] == (
            "docscompletion_record")
        assert len(_dc_records(
            store, session_id, "docscompletion_record")) == 1
        assert len(_dc_records(
            store, session_id, "docscompletion_standing")) == 1
        result = agent.view_docscompletion("D-02")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_dc_records(
            store, session_id, "docscompletion_standing")) == 2
        agent.close()


class TestDocsCompletionReports:
    def test_prepare_report_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_docscompletion_report(
            "docs-2026-11", "release-1",
            "every guide answered",
            "2026-11-13", 1, 11, 12,
            claims=("local_run_ref", "journal_ref"))
        assert result["report"]["state"] == "ready"
        assert result["report"]["certified"] is False
        assert result["report"]["inflated"] is False
        assert result["report_news"]["type"] == (
            "docscompletion_verdict")
        assert "every guide answered" in result["screen"]
        report = agent.get_docscompletion_report(
            "docs-2026-11")
        assert report.entry == "release-1"
        assert [r.book for r in
                agent.docscompletion_reports()] == [
            "docs-2026-11"]
        assert len(_dc_records(
            store, session_id, "docscompletion_verdict")) == 1
        agent.close()

    def test_report_unshared_state_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared"):
            agent.prepare_docscompletion_report(
                "docs-2026-11", "release-1", "x",
                "2026-11-13", 1, 11, 12,
                claims=("local_run_ref",), state="executed")
        assert agent.docscompletion_reports() == []
        assert _dc_records(
            store, session_id, "docscompletion_verdict") == []
        agent.close()

    def test_duplicate_report_refuses(self, agent):
        agent.prepare_docscompletion_report(
            "docs-2026-11", "release-1",
            "every guide answered", "2026-11-13", 1, 11, 12,
            claims=("local_run_ref",))
        with pytest.raises(ValueError, match="docs-2026-11"):
            agent.prepare_docscompletion_report(
                "docs-2026-11", "release-2",
                "a second telling", "2026-11-13", 1, 11, 12,
                claims=("local_run_ref",))
        with pytest.raises(ValueError,
                           match="holds no"):
            agent.get_docscompletion_report("docs-2026-12")


class TestDocsCompletionParseArgs:
    def test_parse_args_well(self):
        assert parse_docscompletion_args("") == (
            "show", None, (), None)
        assert parse_docscompletion_args(None) == (
            "show", None, (), None)
        assert parse_docscompletion_args("guides") == (
            "guides", None, (), None)
        assert parse_docscompletion_args(
            "guide D-01") == (
            "guide", "D-01", (), None)
        assert parse_docscompletion_args(
            "record D-01") == (
            "record", "D-01", (), None)
        assert parse_docscompletion_args(
            "standing D-03") == (
            "standing", "D-03", (), None)
        assert parse_docscompletion_args("report") == (
            "reports", None, (), None)
        assert parse_docscompletion_args(
            "report docs-2026-11") == (
            "report", "docs-2026-11", (), None)
        assert parse_docscompletion_args("verdict") == (
            "verdict", None, (), None)
        assert parse_docscompletion_args("index") == (
            "index", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "guide", "record",
                    "record D-01 extra",
                    "guides now", "standing",
                    "report a b"):
            with pytest.raises(ValueError) as caught:
                parse_docscompletion_args(bad)
            assert str(caught.value) == DOCSCOMPLETION_USAGE


class TestDocsCompletionTerminalRoad:
    def test_show_areas_area_record_standing_report_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/docscompletion")
        assert "D-01" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/docscompletion guides")
        assert "user-guide" in text
        assert "D-12" in text
        _, _, text = _slash(
            agent, "/docscompletion guide D-01")
        assert "user-guide" in text
        _, _, text = _slash(
            agent, "/docscompletion record D-01")
        assert "holds no" in text
        _, _, text = _slash(
            agent, "/docscompletion standing D-01")
        assert "D-01:" in text
        assert "open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/docscompletion report")
        assert "none held" in text
        _, _, text = _slash(agent, "/docscompletion verdict")
        assert "Docs completion stands open" in text
        agent.register_docscompletion_record(_dc_record())
        _, _, text = _slash(
            agent, "/docscompletion record D-01")
        assert "held as answered" in text
        _, _, text = _slash(
            agent, "/docscompletion standing D-01")
        assert "held as answered" in text
        _, _, text = _slash(agent, "/docscompletion index")
        assert "held as answered" in text
        agent.prepare_docscompletion_report(
            "docs-2026-11", "release-1",
            "every guide answered", "2026-11-13", 1, 11, 12,
            claims=("local_run_ref",))
        _, _, text = _slash(
            agent, "/docscompletion report docs-2026-11")
        assert "every guide answered" in text
        assert "never inflated" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/docscompletion [show|guides|"
                "guide <guide>|"
                "record <guide>|"
                "standing <guide>|"
                "report [<book>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/docscompletion dance party")
        assert text == DOCSCOMPLETION_USAGE
        _, _, text = _slash(
            agent, "/docscompletion guide guess")
        assert "unknown guide" in text


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


def _dc_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestDocsCompletionHandler:
    def test_show_is_default(self, sa_handler, agent):
        sa_handler._handle_docscompletion("")
        assert "D-01" in (
            _dc_published_text(sa_handler))
        assert "user-guide" in (
            _dc_published_text(sa_handler))

    def test_area_record_and_verdict(
            self, sa_handler, agent):
        sa_handler._handle_docscompletion(
            "guide D-01")
        assert "user-guide" in (
            _dc_published_text(sa_handler))
        agent.register_docscompletion_record(_dc_record())
        sa_handler._handle_docscompletion(
            "record D-01")
        assert "held as answered" in (
            _dc_published_text(sa_handler))
        sa_handler._handle_docscompletion("verdict")
        assert "Docs completion stands held" in (
            _dc_published_text(sa_handler))

    def test_bad_grammar_is_published(
            self, sa_handler, agent):
        sa_handler._handle_docscompletion("dance party")
        assert DOCSCOMPLETION_USAGE in (
            _dc_published_text(sa_handler))
        sa_handler._handle_docscompletion("guide guess")
        assert "unknown guide" in (
            _dc_published_text(sa_handler))


class TestChatScreenRoutingDocsCompletion:
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
        screen.handle_command("/docscompletion verdict",
                              _FakeLog())
        assert calls == [("/docscompletion", "verdict")]

    def test_chat_screen_help_and_usage_name_the_audit(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/docscompletion[/green] - show the "
                "Docs completion (M-263)") in text
        assert ('"/docscompletion": "Usage: '
                "/docscompletion | "
                "/docscompletion guides") in text


class TestDocsCompletionDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.docscompletion_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _SA_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        verdict = agent.docscompletion_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_docscompletion_record(_dc_record())
        agent.register_docscompletion_record(
            _dc_fresh_for("D-05", work="docs-2026-11-b"))
        verdict = agent.docscompletion_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "D-01", "D-05"]
        assert "Docs completion stands held" in (
            verdict["verdict_text"])

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_docscompletion()
        assert report["book"]["schema"] == (
            DOCS_COMPLETION_SCHEMA)
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_docscompletion_record(_dc_record())
        report = agent.report_docscompletion()
        assert "held as answered" in report["records_text"]
        assert [s["guide"] for s in report["standings"]] == [
            "D-01"]

    def test_docs_for_disposition_and_held_keys(self, agent):
        agent.register_docscompletion_record(_dc_record())
        agent.register_docscompletion_record(
            _dc_fresh_for("D-05", work="docs-2026-11-b"))
        agent.register_docscompletion_record(_dc_record(
            guide="D-02", work="docs-2026-11-c",
            disposition="ROADED", owner="",
            proof_kind="none",
            stages=["named"], claims=["assertion"]))
        assert [r.work for r in
                agent.docs_for_disposition("RECONCILED")] == [
            "docs-2026-11-a", "docs-2026-11-b"]
        assert agent.docscompletion_held() == ["D-01", "D-05"]
        standing = agent.docscompletion_standing(
            "D-02")
        assert standing.held is False
