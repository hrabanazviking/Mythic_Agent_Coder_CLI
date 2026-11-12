"""M-250 Webhook doors - pure-layer tests.

TIER: unit

Inbound events enter a campaign only as a recorded event
with provenance and a timestamp; an absent event reads
as unknown and a stale one as stale, never as a fact,
and the doors only propose campaigns - nothing builds
unbidden.
"""
import pytest

from mythic_agent.core.webhook_doors import (
    BARE_CLAIMS,
    EVENT_KINDS,
    FRESH_LIMIT_SECONDS,
    HELD_EVIDENCE,
    SOURCES,
    STAGES,
    InboundEvent,
    ProposalDraft,
    SourceEntry,
    SourceRegistry,
    default_registry,
    derive_standing,
    format_event,
    format_source,
    format_sources,
    propose_proposal,
)
from mythic_agent.core.validation import ValidationError


def fresh_event(**kw):
    base = dict(source="github", event="pr-42",
                kind="pr_opened", title="Fix the seam",
                subject="PR 42 in mythic-coder",
                observed_at="2026-11-12T12:00:00", age_seconds=60,
                stages=STAGES, claims=("payload_ref",))
    base.update(kw)
    return InboundEvent(**base)


def test_registry_holds_four_sources_recorded_only():
    reg = default_registry()
    assert reg.ids() == ("github", "gitlab",
                         "bitbucket", "generic")
    assert all(e.transport == "recorded" for e in reg.entries())


def test_registry_unknown_source_refused_by_name():
    with pytest.raises(ValidationError, match="unknown webhook source: guess"):
        default_registry().get("guess")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate webhook source"):
        SourceRegistry(SOURCES + SOURCES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        SourceRegistry([SourceEntry("x", "", "event", "recorded", "why")])


def test_entry_live_transport_refused():
    with pytest.raises(ValidationError, match="recorded data only"):
        SourceRegistry([SourceEntry("x", "X", "event", "live", "why")])


def test_source_words_differ_by_source():
    reg = default_registry()
    assert reg.get("github").event_word == "event"
    assert reg.get("gitlab").event_word == "event"
    assert reg.get("bitbucket").event_word == "event"
    assert reg.get("generic").event_word == "delivery"


def test_fresh_held_event_stands_held():
    standing = derive_standing(fresh_event())
    assert standing.held and standing.stage == "held"
    assert standing.freshness == "current" and standing.gaps == ()


def test_bare_claims_only_stands_open():
    standing = derive_standing(fresh_event(claims=("assertion",)))
    assert not standing.held
    assert any("bare claims" in g for g in standing.gaps)


def test_no_evidence_stands_open():
    standing = derive_standing(fresh_event(claims=()))
    assert not standing.held
    assert any("no held evidence" in g for g in standing.gaps)


def test_unfinished_walk_stands_open():
    standing = derive_standing(fresh_event(stages=("received", "recorded")))
    assert not standing.held and standing.stage == "recorded"


def test_walk_must_open_at_received():
    standing = derive_standing(
        fresh_event(stages=("recorded", "checked", "held")))
    assert not standing.held
    assert any("open at received" in g for g in standing.gaps)


def test_walk_rejects_skipped_stage():
    standing = derive_standing(
        fresh_event(stages=("received", "checked", "held")))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_stale_event_stands_open_as_stale():
    standing = derive_standing(
        fresh_event(age_seconds=FRESH_LIMIT_SECONDS + 1))
    assert not standing.held and standing.freshness == "stale"
    assert any("stale" in g for g in standing.gaps)
    fresh = derive_standing(
        fresh_event(age_seconds=FRESH_LIMIT_SECONDS))
    assert fresh.held and fresh.freshness == "current"


def test_unknown_kind_or_no_subject_stands_open():
    standing = derive_standing(fresh_event(kind="unknown"))
    assert not standing.held
    assert any("kind" in g for g in standing.gaps)
    standing = derive_standing(fresh_event(subject=""))
    assert not standing.held
    assert any("subject" in g for g in standing.gaps)


def test_event_unknown_source_and_missing_fields_refused():
    with pytest.raises(ValidationError, match="unknown webhook source"):
        derive_standing(fresh_event(source="guess"))
    with pytest.raises(ValidationError, match="no event"):
        fresh_event(event=" ").validate()
    with pytest.raises(ValidationError, match="no observed time"):
        fresh_event(observed_at="").validate()


def test_event_kind_words_must_be_known():
    with pytest.raises(ValidationError, match="unknown webhook event kind"):
        fresh_event(kind="green").validate()
    for kind in EVENT_KINDS:
        fresh_event(kind=kind).validate()


def test_event_claim_kind_and_age_must_be_known():
    with pytest.raises(ValidationError, match="unknown webhook evidence kind"):
        fresh_event(claims=("vibes",)).validate()
    for kind in HELD_EVIDENCE + BARE_CLAIMS:
        fresh_event(claims=(kind,)).validate()
    with pytest.raises(ValidationError, match="non-negative"):
        fresh_event(age_seconds=-1).validate()


def test_proposal_defaults_to_pending_approval():
    draft = propose_proposal("mythic-coder", "github", "pr-42",
                             "build the seam fix")
    assert draft.approval == "pending" and draft.applied is False


def test_proposal_unapproved_execution_refused():
    with pytest.raises(ValidationError, match="by approval only"):
        propose_proposal("c", "github", "pr-1", "x", approval="executed")
    approved = propose_proposal("c", "github", "pr-1", "x", approval="approved")
    assert approved.approval == "approved" and approved.applied is False


def test_proposal_never_applied_and_format_lines():
    with pytest.raises(ValidationError, match="proposals only"):
        ProposalDraft("c", "github", "pr-1", "x", applied=True).validate()
    with pytest.raises(ValidationError, match="no campaign"):
        propose_proposal(" ", "github", "pr-1", "x")
    with pytest.raises(ValidationError, match="no event"):
        propose_proposal("c", "github", " ", "x")
    with pytest.raises(ValidationError, match="proposes nothing"):
        propose_proposal("c", "github", "pr-1", " ")
    reg = default_registry()
    assert "GitHub" in format_source(reg.get("github"))
    assert "via recorded" in format_source(reg.get("generic"))
    assert format_sources(reg).count("\n") == 3
    line = format_event(fresh_event())
    assert "held as recorded" in line and "pr-42" in line
    open_line = format_event(fresh_event(claims=()))
    assert "open:" in open_line


# ---------------------------------------------------------------------
# M-250 agent layer: the agent holds the shipped source
# registry and one inbound event per source and event for
# the session, events, viewed standings and proposed
# proposals are published as session news through the
# checkpoint road (journal-first, deduped per event,
# standing and proposal), standings, the index and the
# verdict are derived at call time from the held events -
# an event is a fact only when it rests on held evidence -
# campaign proposals are proposed only as drafts, approval
# pending by default, may be marked approved by a human,
# and never applied or built, and the registry is session
# state, never a stored setting. This layer opens no
# webhook listener, calls no host API, probes no network
# and builds nothing unbidden.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    WEBHOOKDOORS_USAGE,
    parse_webhookdoors_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.webhook_doors import (
    PLAIN_EXPLANATION,
    WEBHOOK_DOORS_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_WH_EVENT_TYPES = (
    "webhookdoors_event", "webhookdoors_standing", "webhookdoors_proposal")

ALL_SOURCES = ["github", "gitlab", "bitbucket", "generic"]


def _wh_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _wh_event(**overrides):
    raw = {
        "source": "github",
        "event": "pr-42",
        "kind": "pr_opened",
        "title": "Fix the seam",
        "subject": "PR 42 in mythic-coder",
        "observed_at": "2026-11-12T12:00:00",
        "age_seconds": 60,
        "stages": list(STAGES),
        "claims": ["payload_ref"],
    }
    raw.update(overrides)
    return raw


def _fresh_for(source, event="pr-42"):
    return _wh_event(source=source, event=event)


class TestWebhookDoorsAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_sources(
            self, agent):
        status = agent.webhookdoors_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["webhookdoors_book"]["schema"] == (
            WEBHOOK_DOORS_SCHEMA)
        assert [p["id"] for p in status[
            "webhookdoors_book"]["sources"]] == ALL_SOURCES
        assert status["webhookdoors_book"]["records"] == []
        assert status["webhookdoors_book"]["drafts"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "GitHub" in status["sources_text"]
        assert "via recorded" in status["sources_text"]
        assert "none recorded this session" in status["screen"]
        assert "nothing builds unbidden" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == WEBHOOKDOORS_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._webhookdoors_registry()
        assert agent._webhookdoors_registry() is first
        assert agent._webhookdoors_store is first
        for name in ("webhookdoors_sources",
                     "webhookdoors_book",
                     "webhookdoors_status",
                     "get_webhookdoors_source",
                     "get_webhookdoors_event",
                     "webhookdoors_standing",
                     "events_for_kind",
                     "webhookdoors_held",
                     "webhookdoors_index",
                     "webhookdoors_verdict",
                     "propose_webhookdoors_proposal",
                     "get_webhookdoors_proposal",
                     "webhookdoors_proposals",
                     "report_webhookdoors"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_webhookdoors_registry", "webhookdoors_sources",
            "webhookdoors_book", "webhookdoors_status",
            "get_webhookdoors_source",
            "get_webhookdoors_event",
            "webhookdoors_standing", "events_for_kind",
            "webhookdoors_held", "webhookdoors_index",
            "webhookdoors_verdict",
            "register_webhookdoors_event",
            "register_webhookdoors_events",
            "record_webhookdoors_events",
            "view_webhookdoors", "propose_webhookdoors_proposal",
            "report_webhookdoors",
            "_publish_webhookdoors_record",
            "_webhookdoors_screen",
            "_webhookdoors_effective_event"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.webhookdoors_status()
        entry = agent.get_webhookdoors_source("generic")
        assert entry.event_word == "delivery"
        standing = agent.webhookdoors_standing(
            "github", "pr-42")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.freshness == "stale"
        assert agent.webhookdoors_held() == []
        assert agent.events_for_kind("pr_opened") == []
        agent.webhookdoors_index()
        agent.webhookdoors_verdict()
        agent.report_webhookdoors()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _WH_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown webhook source"):
            agent.get_webhookdoors_source("guess")
        with pytest.raises(ValueError, match="unknown webhook source"):
            agent.webhookdoors_standing("guess", "pr-42")
        with pytest.raises(ValueError, match="holds no inbound event"):
            agent.get_webhookdoors_event("github", "pr-42")
        with pytest.raises(ValueError):
            agent.events_for_kind("")
        with pytest.raises(ValueError, match="unknown webhook event kind"):
            agent.events_for_kind("green")
        agent.close()


class TestWebhookDoorsAgentHolding:
    def test_register_event_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_webhookdoors_event(_wh_event())
        assert result["record"]["source"] == "github"
        assert result["record"]["event"] == "pr-42"
        assert result["record_news"]["type"] == (
            "webhookdoors_event")
        assert "held as recorded" in result["screen"]
        status = agent.webhookdoors_status()
        assert [r["source"] for r in status["records"]] == [
            "github"]
        assert status["book"]["records"][0]["event"] == (
            "pr-42")
        assert status["held"] == ["github/pr-42"]
        assert status["open"] == []
        assert "held as recorded" in status["records_text"]
        assert len(_wh_events(
            store, session_id, "webhookdoors_event")) == 1
        agent.close()

    def test_duplicate_event_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_webhookdoors_event(_wh_event())
        with pytest.raises(ValueError, match="github"):
            agent.register_webhookdoors_event(
                _wh_event(title="A second telling"))
        assert len(_wh_events(
            store, session_id, "webhookdoors_event")) == 1
        agent.close()

    def test_register_event_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_webhookdoors_event(
                _wh_event(claims=["vibes"]))
        assert agent.webhookdoors_status()["records"] == []
        assert _wh_events(
            store, session_id, "webhookdoors_event") == []
        agent.close()

    def test_register_events_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_webhookdoors_events([
            _fresh_for("generic"), _wh_event()])
        assert result["count"] == 2
        assert [r["source"] for r in result["records_news"]] == [
            "generic", "github"]
        assert len(_wh_events(
            store, session_id, "webhookdoors_event")) == 2
        agent.close()

    def test_record_events_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_webhookdoors_events(
            [_fresh_for("gitlab")])
        assert result["count"] == 1
        assert result["book"]["schema"] == WEBHOOK_DOORS_SCHEMA
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_webhookdoors_events(
                [_fresh_for("gitlab")])
        assert len(_wh_events(
            store, session_id, "webhookdoors_event")) == 1
        agent.close()

    def test_view_event_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_webhookdoors_event(_wh_event())
        result = agent.view_webhookdoors("github", "pr-42")
        assert result["source"]["id"] == "github"
        assert result["standing"]["held"] is True
        assert result["record"]["event"] == "pr-42"
        assert result["record_news"]["type"] == (
            "webhookdoors_standing")
        assert result["held_record_news"]["type"] == (
            "webhookdoors_event")
        assert len(_wh_events(
            store, session_id, "webhookdoors_event")) == 1
        assert len(_wh_events(
            store, session_id, "webhookdoors_standing")) == 1
        result = agent.view_webhookdoors("generic", "pr-42")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_wh_events(
            store, session_id, "webhookdoors_standing")) == 2
        agent.close()


class TestWebhookDoorsProposals:
    def test_propose_proposal_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.propose_webhookdoors_proposal(
            "mythic-coder", "github", "pr-42", "build the seam fix")
        assert result["draft"]["approval"] == (
            "pending")
        assert result["draft"]["applied"] is False
        assert result["draft_news"]["type"] == (
            "webhookdoors_proposal")
        assert "build the seam fix" in result["screen"]
        draft = agent.get_webhookdoors_proposal(
            "mythic-coder")
        assert draft.source == "github"
        assert [d.campaign for d in agent.webhookdoors_proposals()] == [
            "mythic-coder"]
        assert len(_wh_events(
            store, session_id, "webhookdoors_proposal")) == 1
        agent.close()

    def test_proposal_unapproved_execution_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="by approval only"):
            agent.propose_webhookdoors_proposal(
                "mythic-coder", "github", "pr-42", "x",
                approval="executed")
        assert agent.webhookdoors_proposals() == []
        assert _wh_events(
            store, session_id, "webhookdoors_proposal") == []
        agent.close()

    def test_duplicate_proposal_refuses(self, agent):
        agent.propose_webhookdoors_proposal(
            "mythic-coder", "github", "pr-42", "build the seam fix")
        with pytest.raises(ValueError, match="mythic-coder"):
            agent.propose_webhookdoors_proposal(
                "mythic-coder", "gitlab", "issue-7", "a second telling")
        with pytest.raises(ValueError,
                           match="holds no campaign proposal"):
            agent.get_webhookdoors_proposal("samverk")


class TestWebhookDoorsParseArgs:
    def test_parse_args_well(self):
        assert parse_webhookdoors_args("") == (
            "show", None, (), None)
        assert parse_webhookdoors_args(None) == (
            "show", None, (), None)
        assert parse_webhookdoors_args("sources") == (
            "sources", None, (), None)
        assert parse_webhookdoors_args("source generic") == (
            "source", "generic", (), None)
        assert parse_webhookdoors_args(
            "event github pr-42") == (
            "event", ("github", "pr-42"), (), None)
        assert parse_webhookdoors_args(
            "standing gitlab issue-7") == (
            "standing", ("gitlab", "issue-7"), (), None)
        assert parse_webhookdoors_args("propose") == (
            "proposals", None, (), None)
        assert parse_webhookdoors_args(
            "propose mythic-coder") == (
            "propose", "mythic-coder", (), None)
        assert parse_webhookdoors_args("verdict") == (
            "verdict", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "source", "event",
                    "event github",
                    "sources now", "standing gitlab",
                    "propose mythic-coder extra"):
            with pytest.raises(ValueError) as caught:
                parse_webhookdoors_args(bad)
            assert str(caught.value) == WEBHOOKDOORS_USAGE


class TestWebhookDoorsTerminalRoad:
    def test_show_sources_source_event_standing_propose_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/webhookdoors")
        assert "GitHub (github)" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/webhookdoors sources")
        assert "GitLab" in text
        _, _, text = _slash(agent, "/webhookdoors source generic")
        assert "delivery" in text
        _, _, text = _slash(
            agent, "/webhookdoors event github pr-42")
        assert "holds no inbound event" in text
        _, _, text = _slash(
            agent, "/webhookdoors standing github pr-42")
        assert "github/pr-42: webhook open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/webhookdoors propose")
        assert "Campaign proposal: none held" in text
        _, _, text = _slash(agent, "/webhookdoors verdict")
        assert "Webhook doors stand open" in text
        agent.register_webhookdoors_event(_wh_event())
        _, _, text = _slash(
            agent, "/webhookdoors event github pr-42")
        assert "held as recorded" in text
        _, _, text = _slash(
            agent, "/webhookdoors standing github pr-42")
        assert "github/pr-42: webhook held as recorded" in text
        _, _, text = _slash(agent, "/webhookdoors index")
        assert "held as recorded" in text
        agent.propose_webhookdoors_proposal(
            "mythic-coder", "github", "pr-42", "build the seam fix")
        _, _, text = _slash(
            agent, "/webhookdoors propose mythic-coder")
        assert "build the seam fix" in text
        assert "never applied" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/webhookdoors [show|sources|source <source>|"
                "event <source> <event>|"
                "standing <source> <event>|"
                "propose [<campaign>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/webhookdoors dance party")
        assert text == WEBHOOKDOORS_USAGE
        _, _, text = _slash(agent, "/webhookdoors source guess")
        assert "unknown webhook source" in text


@pytest.fixture()
def wh_handler(agent, monkeypatch):
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


def _wh_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestWebhookDoorsHandler:
    def test_show_is_default(self, wh_handler, agent):
        wh_handler._handle_webhookdoors("")
        assert "GitHub (github)" in (
            _wh_published_text(wh_handler))

    def test_source_event_and_verdict(
            self, wh_handler, agent):
        wh_handler._handle_webhookdoors("source generic")
        assert "delivery" in (
            _wh_published_text(wh_handler))
        agent.register_webhookdoors_event(_wh_event())
        wh_handler._handle_webhookdoors(
            "event github pr-42")
        assert "held as recorded" in (
            _wh_published_text(wh_handler))
        wh_handler._handle_webhookdoors("verdict")
        assert "Webhook doors stand held" in (
            _wh_published_text(wh_handler))

    def test_bad_grammar_is_published(
            self, wh_handler, agent):
        wh_handler._handle_webhookdoors("dance party")
        assert WEBHOOKDOORS_USAGE in (
            _wh_published_text(wh_handler))
        wh_handler._handle_webhookdoors("source guess")
        assert "unknown webhook source" in (
            _wh_published_text(wh_handler))


class TestChatScreenRoutingWebhookDoors:
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
        screen.handle_command("/webhookdoors verdict", _FakeLog())
        assert calls == [("/webhookdoors", "verdict")]

    def test_chat_screen_help_and_usage_name_the_doors(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/webhookdoors[/green] - show the Webhook doors "
                "(M-250)") in text
        assert ('"/webhookdoors": "Usage: /webhookdoors | '
                "/webhookdoors sources") in text


class TestWebhookDoorsDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.webhookdoors_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _WH_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        verdict = agent.webhookdoors_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_webhookdoors_event(_wh_event())
        agent.register_webhookdoors_event(_fresh_for("gitlab"))
        verdict = agent.webhookdoors_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "github/pr-42", "gitlab/pr-42"]
        assert "Webhook doors stand held" in verdict["verdict_text"]

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_webhookdoors()
        assert report["book"]["schema"] == WEBHOOK_DOORS_SCHEMA
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_webhookdoors_event(_wh_event())
        report = agent.report_webhookdoors()
        assert "held as recorded" in report["records_text"]
        assert [s["source"] for s in report["standings"]] == [
            "github"]

    def test_events_for_kind_and_held_keys(self, agent):
        agent.register_webhookdoors_event(_wh_event())
        agent.register_webhookdoors_event(_wh_event(
            event="issue-9", kind="issue_filed",
            stages=["received"], claims=["assertion"]))
        assert [r.event for r in
                agent.events_for_kind("pr_opened")] == [
            "pr-42"]
        assert [r.event for r in
                agent.events_for_kind("issue_filed")] == [
            "issue-9"]
        assert agent.webhookdoors_held() == ["github/pr-42"]
        standing = agent.webhookdoors_standing(
            "github", "issue-9")
        assert standing.held is False
        assert any("bare claims" in gap
                   for gap in standing.gaps)
