"""M-249 The WYRD seam - pure-layer tests.

TIER: unit

World-state enters a campaign only as a recorded snapshot
with provenance and a timestamp; an absent snapshot reads
as unknown and a stale one as stale, never as current
fact, and the seam only advises campaigns.
"""
import pytest

from mythic_agent.core.wyrd_seam import (
    AVAILABILITIES,
    BARE_CLAIMS,
    FORGE_STATES,
    FRESH_LIMIT_SECONDS,
    HELD_EVIDENCE,
    LOAD_BANDS,
    SOURCES,
    STAGES,
    AdviceDraft,
    NodeSnapshot,
    SourceEntry,
    SourceRegistry,
    default_registry,
    derive_standing,
    format_snapshot,
    format_source,
    format_sources,
    propose_advice,
)
from mythic_agent.core.validation import ValidationError


def fresh_snapshot(**kw):
    base = dict(source="wyrd_engine", node="purplelongship",
                availability="free", forge_state="hot",
                load_band="light", campaign_position="M-249 building",
                observed_at="2026-11-12T12:00:00", age_seconds=60,
                stages=STAGES, claims=("engine_ref",))
    base.update(kw)
    return NodeSnapshot(**base)


def test_registry_holds_four_sources_recorded_only():
    reg = default_registry()
    assert reg.ids() == ("wyrd_engine", "manual_report",
                         "campaign_journal", "keeper_report")
    assert all(e.transport == "recorded" for e in reg.entries())


def test_registry_unknown_source_refused_by_name():
    with pytest.raises(ValidationError, match="unknown wyrd source: guess"):
        default_registry().get("guess")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate wyrd source"):
        SourceRegistry(SOURCES + SOURCES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        SourceRegistry([SourceEntry("x", "", "snapshot", "recorded", "why")])


def test_entry_live_transport_refused():
    with pytest.raises(ValidationError, match="recorded data only"):
        SourceRegistry([SourceEntry("x", "X", "snapshot", "live", "why")])


def test_source_words_differ_by_source():
    reg = default_registry()
    assert reg.get("wyrd_engine").snapshot_word == "snapshot"
    assert reg.get("manual_report").snapshot_word == "report"
    assert reg.get("campaign_journal").snapshot_word == "entry"
    assert reg.get("keeper_report").snapshot_word == "report"


def test_fresh_held_snapshot_stands_held():
    standing = derive_standing(fresh_snapshot())
    assert standing.held and standing.stage == "held"
    assert standing.freshness == "current" and standing.gaps == ()


def test_bare_claims_only_stands_open():
    standing = derive_standing(fresh_snapshot(claims=("assertion",)))
    assert not standing.held
    assert any("bare claims" in g for g in standing.gaps)


def test_no_evidence_stands_open():
    standing = derive_standing(fresh_snapshot(claims=()))
    assert not standing.held
    assert any("no held evidence" in g for g in standing.gaps)


def test_unfinished_walk_stands_open():
    standing = derive_standing(fresh_snapshot(stages=("reported", "recorded")))
    assert not standing.held and standing.stage == "recorded"


def test_walk_must_open_at_reported():
    standing = derive_standing(
        fresh_snapshot(stages=("recorded", "checked", "held")))
    assert not standing.held
    assert any("open at reported" in g for g in standing.gaps)


def test_walk_rejects_skipped_stage():
    standing = derive_standing(
        fresh_snapshot(stages=("reported", "checked", "held")))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_stale_snapshot_stands_open_as_stale():
    standing = derive_standing(
        fresh_snapshot(age_seconds=FRESH_LIMIT_SECONDS + 1))
    assert not standing.held and standing.freshness == "stale"
    assert any("stale" in g for g in standing.gaps)
    fresh = derive_standing(
        fresh_snapshot(age_seconds=FRESH_LIMIT_SECONDS))
    assert fresh.held and fresh.freshness == "current"


def test_unknown_availability_or_forge_stands_open():
    standing = derive_standing(fresh_snapshot(availability="unknown"))
    assert not standing.held
    assert any("availability" in g for g in standing.gaps)
    standing = derive_standing(fresh_snapshot(forge_state="unknown"))
    assert not standing.held
    assert any("forge state" in g for g in standing.gaps)


def test_snapshot_unknown_source_and_missing_fields_refused():
    with pytest.raises(ValidationError, match="unknown wyrd source"):
        derive_standing(fresh_snapshot(source="guess"))
    with pytest.raises(ValidationError, match="no node"):
        fresh_snapshot(node=" ").validate()
    with pytest.raises(ValidationError, match="no observed time"):
        fresh_snapshot(observed_at="").validate()


def test_snapshot_state_words_must_be_known():
    with pytest.raises(ValidationError, match="unknown availability"):
        fresh_snapshot(availability="green").validate()
    with pytest.raises(ValidationError, match="unknown forge state"):
        fresh_snapshot(forge_state="green").validate()
    with pytest.raises(ValidationError, match="unknown load band"):
        fresh_snapshot(load_band="green").validate()
    for availability in AVAILABILITIES:
        fresh_snapshot(availability=availability).validate()
    for forge_state in FORGE_STATES:
        fresh_snapshot(forge_state=forge_state).validate()
    for load_band in LOAD_BANDS:
        fresh_snapshot(load_band=load_band).validate()


def test_snapshot_claim_kind_and_age_must_be_known():
    with pytest.raises(ValidationError, match="unknown wyrd evidence kind"):
        fresh_snapshot(claims=("vibes",)).validate()
    for kind in HELD_EVIDENCE + BARE_CLAIMS:
        fresh_snapshot(claims=(kind,)).validate()
    with pytest.raises(ValidationError, match="non-negative"):
        fresh_snapshot(age_seconds=-1).validate()


def test_advice_defaults_to_pending_approval():
    draft = propose_advice("mythic-coder", "purplelongship",
                           "build M-249 there")
    assert draft.approval == "pending" and draft.applied is False


def test_advice_unapproved_execution_refused():
    with pytest.raises(ValidationError, match="by approval only"):
        propose_advice("c", "n", "x", approval="executed")
    approved = propose_advice("c", "n", "x", approval="approved")
    assert approved.approval == "approved" and approved.applied is False


def test_advice_never_applied_and_format_lines():
    with pytest.raises(ValidationError, match="advisory only"):
        AdviceDraft("c", "n", "x", applied=True).validate()
    with pytest.raises(ValidationError, match="no campaign"):
        propose_advice(" ", "n", "x")
    with pytest.raises(ValidationError, match="no node"):
        propose_advice("c", " ", "x")
    with pytest.raises(ValidationError, match="proposes nothing"):
        propose_advice("c", "n", " ")
    reg = default_registry()
    assert "WYRD engine" in format_source(reg.get("wyrd_engine"))
    assert "via recorded" in format_source(reg.get("keeper_report"))
    assert format_sources(reg).count("\n") == 3
    line = format_snapshot(fresh_snapshot())
    assert "current as recorded" in line and "purplelongship" in line
    open_line = format_snapshot(fresh_snapshot(claims=()))
    assert "open:" in open_line


# ---------------------------------------------------------------------
# M-249 agent layer: the agent holds the shipped source
# registry and one node snapshot per source and node for
# the session, snapshots, viewed standings and proposed
# advice are published as session news through the
# checkpoint road (journal-first, deduped per snapshot,
# standing and advice), standings, the index and the
# verdict are derived at call time from the held
# snapshots - a node stands current only on a full legal
# walk resting on held evidence within the fresh limit -
# campaign advice is proposed only as a draft, approval
# pending by default, may be marked approved by a human,
# and never applied, and the registry is session state,
# never a stored setting. This layer calls no WYRD engine
# API, probes no machine, measures no load and reroutes
# no campaign.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    WYRDSEAM_USAGE,
    parse_wyrdseam_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.wyrd_seam import (
    PLAIN_EXPLANATION,
    WYRD_SEAM_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_WY_EVENT_TYPES = (
    "wyrdseam_snapshot", "wyrdseam_standing", "wyrdseam_advice")

ALL_SOURCES = ["wyrd_engine", "manual_report",
               "campaign_journal", "keeper_report"]


def _wyrd_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _wyrd_snapshot(**overrides):
    raw = {
        "source": "wyrd_engine",
        "node": "purplelongship",
        "availability": "free",
        "forge_state": "hot",
        "load_band": "light",
        "campaign_position": "M-249 building",
        "observed_at": "2026-11-12T12:00:00",
        "age_seconds": 60,
        "stages": list(STAGES),
        "claims": ["engine_ref"],
    }
    raw.update(overrides)
    return raw


def _fresh_for(source, node="purplelongship"):
    return _wyrd_snapshot(source=source, node=node)


class TestWyrdSeamAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_sources(
            self, agent):
        status = agent.wyrdseam_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["wyrdseam_book"]["schema"] == (
            WYRD_SEAM_SCHEMA)
        assert [p["id"] for p in status[
            "wyrdseam_book"]["sources"]] == ALL_SOURCES
        assert status["wyrdseam_book"]["records"] == []
        assert status["wyrdseam_book"]["drafts"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "WYRD engine" in status["sources_text"]
        assert "via recorded" in status["sources_text"]
        assert "none recorded this session" in status["screen"]
        assert "never as current fact" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == WYRDSEAM_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._wyrdseam_registry()
        assert agent._wyrdseam_registry() is first
        assert agent._wyrdseam_store is first
        for name in ("wyrdseam_sources",
                     "wyrdseam_book",
                     "wyrdseam_status",
                     "get_wyrdseam_source",
                     "get_wyrdseam_snapshot",
                     "wyrdseam_standing",
                     "snapshots_for_availability",
                     "wyrdseam_held",
                     "wyrdseam_index",
                     "wyrdseam_verdict",
                     "propose_wyrdseam_advice",
                     "get_wyrdseam_advice",
                     "wyrdseam_advices",
                     "report_wyrdseam"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_wyrdseam_registry", "wyrdseam_sources",
            "wyrdseam_book", "wyrdseam_status",
            "get_wyrdseam_source",
            "get_wyrdseam_snapshot",
            "wyrdseam_standing", "snapshots_for_availability",
            "wyrdseam_held", "wyrdseam_index",
            "wyrdseam_verdict",
            "register_wyrdseam_snapshot",
            "register_wyrdseam_snapshots",
            "record_wyrdseam_snapshots",
            "view_wyrdseam", "propose_wyrdseam_advice",
            "report_wyrdseam",
            "_publish_wyrdseam_record",
            "_wyrdseam_screen",
            "_wyrdseam_effective_snapshot"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.wyrdseam_status()
        entry = agent.get_wyrdseam_source("campaign_journal")
        assert entry.snapshot_word == "entry"
        standing = agent.wyrdseam_standing(
            "wyrd_engine", "purplelongship")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.freshness == "stale"
        assert agent.wyrdseam_held() == []
        assert agent.snapshots_for_availability("free") == []
        agent.wyrdseam_index()
        agent.wyrdseam_verdict()
        agent.report_wyrdseam()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _WY_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown wyrd source"):
            agent.get_wyrdseam_source("guess")
        with pytest.raises(ValueError, match="unknown wyrd source"):
            agent.wyrdseam_standing("guess", "purplelongship")
        with pytest.raises(ValueError, match="holds no world-state snapshot"):
            agent.get_wyrdseam_snapshot("wyrd_engine", "purplelongship")
        with pytest.raises(ValueError):
            agent.snapshots_for_availability("")
        with pytest.raises(ValueError, match="unknown availability"):
            agent.snapshots_for_availability("green")
        agent.close()


class TestWyrdSeamAgentHolding:
    def test_register_snapshot_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_wyrdseam_snapshot(_wyrd_snapshot())
        assert result["record"]["source"] == "wyrd_engine"
        assert result["record"]["node"] == "purplelongship"
        assert result["record_news"]["type"] == (
            "wyrdseam_snapshot")
        assert "current as recorded" in result["screen"]
        status = agent.wyrdseam_status()
        assert [r["source"] for r in status["records"]] == [
            "wyrd_engine"]
        assert status["book"]["records"][0]["node"] == (
            "purplelongship")
        assert status["held"] == ["wyrd_engine/purplelongship"]
        assert status["open"] == []
        assert "current as recorded" in status["records_text"]
        assert len(_wyrd_events(
            store, session_id, "wyrdseam_snapshot")) == 1
        agent.close()

    def test_duplicate_snapshot_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_wyrdseam_snapshot(_wyrd_snapshot())
        with pytest.raises(ValueError, match="wyrd_engine"):
            agent.register_wyrdseam_snapshot(
                _wyrd_snapshot(load_band="heavy"))
        assert len(_wyrd_events(
            store, session_id, "wyrdseam_snapshot")) == 1
        agent.close()

    def test_register_snapshot_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_wyrdseam_snapshot(
                _wyrd_snapshot(claims=["vibes"]))
        assert agent.wyrdseam_status()["records"] == []
        assert _wyrd_events(
            store, session_id, "wyrdseam_snapshot") == []
        agent.close()

    def test_register_snapshots_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_wyrdseam_snapshots([
            _fresh_for("keeper_report"), _wyrd_snapshot()])
        assert result["count"] == 2
        assert [r["source"] for r in result["records_news"]] == [
            "keeper_report", "wyrd_engine"]
        assert len(_wyrd_events(
            store, session_id, "wyrdseam_snapshot")) == 2
        agent.close()

    def test_record_snapshots_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_wyrdseam_snapshots(
            [_fresh_for("manual_report")])
        assert result["count"] == 1
        assert result["book"]["schema"] == WYRD_SEAM_SCHEMA
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_wyrdseam_snapshots(
                [_fresh_for("manual_report")])
        assert len(_wyrd_events(
            store, session_id, "wyrdseam_snapshot")) == 1
        agent.close()

    def test_view_snapshot_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_wyrdseam_snapshot(_wyrd_snapshot())
        result = agent.view_wyrdseam("wyrd_engine", "purplelongship")
        assert result["source"]["id"] == "wyrd_engine"
        assert result["standing"]["held"] is True
        assert result["record"]["node"] == "purplelongship"
        assert result["record_news"]["type"] == (
            "wyrdseam_standing")
        assert result["held_record_news"]["type"] == (
            "wyrdseam_snapshot")
        assert len(_wyrd_events(
            store, session_id, "wyrdseam_snapshot")) == 1
        assert len(_wyrd_events(
            store, session_id, "wyrdseam_standing")) == 1
        result = agent.view_wyrdseam("keeper_report", "purplelongship")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_wyrd_events(
            store, session_id, "wyrdseam_standing")) == 2
        agent.close()


class TestWyrdSeamAdvice:
    def test_propose_advice_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.propose_wyrdseam_advice(
            "mythic-coder", "purplelongship", "build M-249 there")
        assert result["draft"]["approval"] == (
            "pending")
        assert result["draft"]["applied"] is False
        assert result["draft_news"]["type"] == (
            "wyrdseam_advice")
        assert "build M-249 there" in result["screen"]
        draft = agent.get_wyrdseam_advice(
            "mythic-coder")
        assert draft.node == "purplelongship"
        assert [d.campaign for d in agent.wyrdseam_advices()] == [
            "mythic-coder"]
        assert len(_wyrd_events(
            store, session_id, "wyrdseam_advice")) == 1
        agent.close()

    def test_advice_unapproved_execution_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="by approval only"):
            agent.propose_wyrdseam_advice(
                "mythic-coder", "purplelongship", "x",
                approval="executed")
        assert agent.wyrdseam_advices() == []
        assert _wyrd_events(
            store, session_id, "wyrdseam_advice") == []
        agent.close()

    def test_duplicate_advice_refuses(self, agent):
        agent.propose_wyrdseam_advice(
            "mythic-coder", "purplelongship", "build M-249 there")
        with pytest.raises(ValueError, match="mythic-coder"):
            agent.propose_wyrdseam_advice(
                "mythic-coder", "mimir", "a second telling")
        with pytest.raises(ValueError,
                           match="holds no campaign advice"):
            agent.get_wyrdseam_advice("samverk")


class TestWyrdSeamParseArgs:
    def test_parse_args_well(self):
        assert parse_wyrdseam_args("") == (
            "show", None, (), None)
        assert parse_wyrdseam_args(None) == (
            "show", None, (), None)
        assert parse_wyrdseam_args("sources") == (
            "sources", None, (), None)
        assert parse_wyrdseam_args("source keeper_report") == (
            "source", "keeper_report", (), None)
        assert parse_wyrdseam_args(
            "snapshot wyrd_engine purplelongship") == (
            "snapshot", ("wyrd_engine", "purplelongship"), (), None)
        assert parse_wyrdseam_args(
            "standing keeper_report mimir") == (
            "standing", ("keeper_report", "mimir"), (), None)
        assert parse_wyrdseam_args("advice") == (
            "advices", None, (), None)
        assert parse_wyrdseam_args(
            "advice mythic-coder") == (
            "advice", "mythic-coder", (), None)
        assert parse_wyrdseam_args("verdict") == (
            "verdict", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "source", "snapshot",
                    "snapshot wyrd_engine",
                    "sources now", "standing keeper_report",
                    "advice mythic-coder extra"):
            with pytest.raises(ValueError) as caught:
                parse_wyrdseam_args(bad)
            assert str(caught.value) == WYRDSEAM_USAGE


class TestWyrdSeamTerminalRoad:
    def test_show_sources_source_snapshot_standing_advice_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/wyrdseam")
        assert "WYRD engine (wyrd_engine)" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/wyrdseam sources")
        assert "Campaign journal" in text
        _, _, text = _slash(agent, "/wyrdseam source keeper_report")
        assert "report" in text
        _, _, text = _slash(
            agent, "/wyrdseam snapshot wyrd_engine purplelongship")
        assert "holds no world-state snapshot" in text
        _, _, text = _slash(
            agent, "/wyrdseam standing wyrd_engine purplelongship")
        assert "wyrd_engine/purplelongship: world-state open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/wyrdseam advice")
        assert "Campaign advice: none held" in text
        _, _, text = _slash(agent, "/wyrdseam verdict")
        assert "World-state stands open" in text
        agent.register_wyrdseam_snapshot(_wyrd_snapshot())
        _, _, text = _slash(
            agent, "/wyrdseam snapshot wyrd_engine purplelongship")
        assert "current as recorded" in text
        _, _, text = _slash(
            agent, "/wyrdseam standing wyrd_engine purplelongship")
        assert "wyrd_engine/purplelongship: world-state current as recorded" in text
        _, _, text = _slash(agent, "/wyrdseam index")
        assert "current as recorded" in text
        agent.propose_wyrdseam_advice(
            "mythic-coder", "purplelongship", "build M-249 there")
        _, _, text = _slash(
            agent, "/wyrdseam advice mythic-coder")
        assert "build M-249 there" in text
        assert "never applied" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/wyrdseam [show|sources|source <source>|"
                "snapshot <source> <node>|"
                "standing <source> <node>|"
                "advice [<campaign>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/wyrdseam dance party")
        assert text == WYRDSEAM_USAGE
        _, _, text = _slash(agent, "/wyrdseam source guess")
        assert "unknown wyrd source" in text


@pytest.fixture()
def wyrd_handler(agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY
    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _wyrd_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestWyrdSeamHandler:
    def test_show_is_default(self, wyrd_handler, agent):
        wyrd_handler._handle_wyrdseam("")
        assert "WYRD engine (wyrd_engine)" in (
            _wyrd_published_text(wyrd_handler))

    def test_source_snapshot_and_verdict(
            self, wyrd_handler, agent):
        wyrd_handler._handle_wyrdseam("source keeper_report")
        assert "report" in (
            _wyrd_published_text(wyrd_handler))
        agent.register_wyrdseam_snapshot(_wyrd_snapshot())
        wyrd_handler._handle_wyrdseam(
            "snapshot wyrd_engine purplelongship")
        assert "current as recorded" in (
            _wyrd_published_text(wyrd_handler))
        wyrd_handler._handle_wyrdseam("verdict")
        assert "World-state stands held" in (
            _wyrd_published_text(wyrd_handler))

    def test_bad_grammar_is_published(
            self, wyrd_handler, agent):
        wyrd_handler._handle_wyrdseam("dance party")
        assert WYRDSEAM_USAGE in (
            _wyrd_published_text(wyrd_handler))
        wyrd_handler._handle_wyrdseam("source guess")
        assert "unknown wyrd source" in (
            _wyrd_published_text(wyrd_handler))


class TestChatScreenRoutingWyrdSeam:
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
        screen.handle_command("/wyrdseam verdict", _FakeLog())
        assert calls == [("/wyrdseam", "verdict")]

    def test_chat_screen_help_and_usage_name_the_seam(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/wyrdseam[/green] - show the WYRD seam "
                "(M-249)") in text
        assert ('"/wyrdseam": "Usage: /wyrdseam | '
                "/wyrdseam sources") in text


class TestWyrdSeamDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.wyrdseam_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _WY_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        verdict = agent.wyrdseam_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_wyrdseam_snapshot(_wyrd_snapshot())
        agent.register_wyrdseam_snapshot(_fresh_for("keeper_report"))
        verdict = agent.wyrdseam_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "wyrd_engine/purplelongship", "keeper_report/purplelongship"]
        assert "World-state stands held" in verdict["verdict_text"]

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_wyrdseam()
        assert report["book"]["schema"] == WYRD_SEAM_SCHEMA
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_wyrdseam_snapshot(_wyrd_snapshot())
        report = agent.report_wyrdseam()
        assert "current as recorded" in report["records_text"]
        assert [s["source"] for s in report["standings"]] == [
            "wyrd_engine"]

    def test_snapshots_for_availability_and_held_keys(self, agent):
        agent.register_wyrdseam_snapshot(_wyrd_snapshot())
        agent.register_wyrdseam_snapshot(_wyrd_snapshot(
            source="wyrd_engine", node="mimir",
            availability="busy", stages=["reported"],
            claims=["assertion"]))
        assert [r.node for r in
                agent.snapshots_for_availability("free")] == [
            "purplelongship"]
        assert [r.node for r in
                agent.snapshots_for_availability("busy")] == [
            "mimir"]
        assert agent.wyrdseam_held() == ["wyrd_engine/purplelongship"]
        standing = agent.wyrdseam_standing(
            "wyrd_engine", "mimir")
        assert standing.held is False
        assert any("bare claims" in gap
                   for gap in standing.gaps)
