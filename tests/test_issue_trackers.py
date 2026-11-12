"""M-248 Issue trackers beyond git hosts - pure-layer tests.

TIER: unit

Issues enter the session as facts only when they rest on
held evidence; trackers are MCP-first and read-mostly, and
any write is proposed only as a draft, by approval.
"""
import pytest

from mythic_agent.core.issue_trackers import (
    BARE_CLAIMS,
    HELD_EVIDENCE,
    ISSUE_STATES,
    STAGES,
    TRACKERS,
    IssueRecord,
    TrackerEntry,
    TrackerRegistry,
    WriteDraft,
    default_registry,
    derive_standing,
    format_record,
    format_tracker,
    format_trackers,
    propose_write,
)
from mythic_agent.core.validation import ValidationError


def held_record(**kw):
    base = dict(tracker="linear", issue_key="ENG-1",
                title="Fix the bridge", state="open",
                stages=STAGES, claims=("issue_ref",))
    base.update(kw)
    return IssueRecord(**base)


def test_registry_holds_three_trackers_mcp_first():
    reg = default_registry()
    assert reg.ids() == ("linear", "jira", "generic_mcp")
    assert all(e.transport == "mcp" for e in reg.entries())


def test_registry_unknown_tracker_refused_by_name():
    with pytest.raises(ValidationError, match="unknown issue tracker: asana"):
        default_registry().get("asana")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate issue tracker"):
        TrackerRegistry(TRACKERS + TRACKERS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        TrackerRegistry([TrackerEntry("x", "", "issue", "mcp", "why")])


def test_entry_non_mcp_transport_refused():
    with pytest.raises(ValidationError, match="MCP-first"):
        TrackerRegistry([TrackerEntry("x", "X", "issue", "rest", "why")])


def test_tracker_words_differ_by_tracker():
    reg = default_registry()
    assert reg.get("linear").issue_word == "issue"
    assert reg.get("jira").issue_word == "ticket"
    assert reg.get("generic_mcp").issue_word == "work item"


def test_held_record_stands_held():
    standing = derive_standing(held_record())
    assert standing.held and standing.stage == "held" and standing.gaps == ()


def test_bare_claims_only_stands_open():
    standing = derive_standing(held_record(claims=("assertion",)))
    assert not standing.held
    assert any("bare claims" in g for g in standing.gaps)


def test_no_evidence_stands_open():
    standing = derive_standing(held_record(claims=()))
    assert not standing.held
    assert any("no held evidence" in g for g in standing.gaps)


def test_unfinished_walk_stands_open():
    standing = derive_standing(held_record(stages=("seen", "fetched")))
    assert not standing.held and standing.stage == "fetched"


def test_walk_must_open_at_seen():
    standing = derive_standing(held_record(stages=("fetched", "read", "held")))
    assert not standing.held
    assert any("open at seen" in g for g in standing.gaps)


def test_walk_rejects_skipped_stage():
    standing = derive_standing(held_record(stages=("seen", "read", "held")))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_record_unknown_tracker_refused():
    with pytest.raises(ValidationError, match="unknown issue tracker"):
        derive_standing(held_record(tracker="asana"))


def test_record_names_issue_and_title():
    with pytest.raises(ValidationError, match="no issue"):
        held_record(issue_key=" ").validate()
    with pytest.raises(ValidationError, match="no title"):
        held_record(title="").validate()


def test_record_state_must_be_known():
    with pytest.raises(ValidationError, match="unknown issue state"):
        held_record(state="green").validate()
    for state in ISSUE_STATES:
        held_record(state=state).validate()


def test_record_claim_kind_must_be_known():
    with pytest.raises(ValidationError, match="unknown issue evidence kind"):
        held_record(claims=("vibes",)).validate()
    for kind in HELD_EVIDENCE + BARE_CLAIMS:
        held_record(claims=(kind,)).validate()


def test_write_draft_defaults_to_pending_approval():
    draft = propose_write("linear", "ENG-1", "close as done")
    assert draft.approval == "pending" and draft.applied is False


def test_write_unapproved_execution_refused():
    with pytest.raises(ValidationError, match="by approval only"):
        propose_write("linear", "ENG-1", "x", approval="executed")
    approved = propose_write("jira", "OPS-2", "x", approval="approved")
    assert approved.approval == "approved" and approved.applied is False


def test_write_draft_never_applied():
    with pytest.raises(ValidationError, match="drafts only"):
        WriteDraft("linear", "ENG-1", "x", applied=True).validate()
    with pytest.raises(ValidationError, match="no issue"):
        propose_write("linear", " ", "x")
    with pytest.raises(ValidationError, match="no change"):
        propose_write("linear", "ENG-1", " ")


def test_format_lines():
    reg = default_registry()
    assert "Linear" in format_tracker(reg.get("linear"))
    assert "via mcp" in format_tracker(reg.get("jira"))
    assert format_trackers(reg).count("\n") == 2
    line = format_record(held_record())
    assert "held as fact" in line and "ENG-1" in line
    open_line = format_record(held_record(claims=()))
    assert "open:" in open_line


# ---------------------------------------------------------------------
# M-248 agent layer: the agent holds the shipped tracker
# registry and one issue record per tracker and issue_key
# for the session, records, viewed standings and proposed
# drafts are published as session news through the
# checkpoint road (journal-first, deduped per record,
# standing and draft), standings, the index and the
# verdict are derived at call time from the held records
# - a run stands held only on a full legal walk resting
# on held evidence - tracker writes are proposed only
# as drafts, approval pending by default, may be marked approved by a human, and never applied,
# and the registry is session state, never a stored
# setting. This layer calls no tracker API, fetches no issue,
# changes no issue_key and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    ISSUETRACKERS_USAGE,
    parse_issuetrackers_args,
)
from mythic_agent.core.issue_trackers import (
    ISSUE_TRACKER_SCHEMA,
    PLAIN_EXPLANATION,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore

ROOT = _Path(__file__).resolve().parent.parent

_IT_EVENT_TYPES = (
    "issuetrackers_record", "issuetrackers_standing", "issuetrackers_draft")

ALL_TRACKERS = ["linear", "jira", "generic_mcp"]


def _issue_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _issue_record(**overrides):
    raw = {
        "tracker": "linear",
        "issue_key": "ENG-1",
        "title": "Fix the bridge",
        "state": "open",
        "stages": list(STAGES),
        "claims": ["issue_ref"],
    }
    raw.update(overrides)
    return raw


def _held_for(tracker, issue_key="ENG-1"):
    return _issue_record(tracker=tracker, issue_key=issue_key)


class TestIssueTrackersAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_trackers(
            self, agent):
        status = agent.issuetrackers_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["issuetrackers_book"]["schema"] == (
            ISSUE_TRACKER_SCHEMA)
        assert [p["id"] for p in status[
            "issuetrackers_book"]["trackers"]] == ALL_TRACKERS
        assert status["issuetrackers_book"]["records"] == []
        assert status["issuetrackers_book"]["drafts"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "Linear" in status["trackers_text"]
        assert "via mcp" in status["trackers_text"]
        assert "none held this session" in status["screen"]
        assert "held evidence" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == ISSUETRACKERS_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._issuetrackers_registry()
        assert agent._issuetrackers_registry() is first
        assert agent._issuetrackers_store is first
        for name in ("issuetrackers_trackers",
                     "issuetrackers_book",
                     "issuetrackers_status",
                     "get_issuetrackers_tracker",
                     "get_issuetrackers_record",
                     "issuetrackers_standing",
                     "records_for_state",
                     "issuetrackers_held",
                     "issuetrackers_index",
                     "issuetrackers_verdict",
                     "propose_issuetrackers_draft",
                     "get_issuetrackers_draft",
                     "issuetrackers_drafts",
                     "report_issuetrackers"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_issuetrackers_registry", "issuetrackers_trackers",
            "issuetrackers_book", "issuetrackers_status",
            "get_issuetrackers_tracker",
            "get_issuetrackers_record",
            "issuetrackers_standing", "records_for_state",
            "issuetrackers_held", "issuetrackers_index",
            "issuetrackers_verdict",
            "register_issuetrackers_record",
            "register_issuetrackers_records",
            "record_issuetrackers_records",
            "view_issuetrackers", "propose_issuetrackers_draft",
            "report_issuetrackers",
            "_publish_issuetrackers_record",
            "_issuetrackers_screen",
            "_issuetrackers_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.issuetrackers_status()
        entry = agent.get_issuetrackers_tracker("jira")
        assert entry.issue_word == "ticket"
        standing = agent.issuetrackers_standing(
            "linear", "ENG-1")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert agent.issuetrackers_held() == []
        assert agent.records_for_state("open") == []
        agent.issuetrackers_index()
        agent.issuetrackers_verdict()
        agent.report_issuetrackers()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _IT_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown issue tracker"):
            agent.get_issuetrackers_tracker("circle")
        with pytest.raises(ValueError, match="unknown issue tracker"):
            agent.issuetrackers_standing("circle", "ENG-1")
        with pytest.raises(ValueError, match="holds no issue record"):
            agent.get_issuetrackers_record("linear", "ENG-1")
        with pytest.raises(ValueError):
            agent.records_for_state("")
        with pytest.raises(ValueError, match="unknown issue state"):
            agent.records_for_state("green")
        agent.close()


class TestIssueTrackersAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_issuetrackers_record(_issue_record())
        assert result["record"]["tracker"] == "linear"
        assert result["record"]["issue_key"] == "ENG-1"
        assert result["record_news"]["type"] == (
            "issuetrackers_record")
        assert "held as fact" in result["screen"]
        status = agent.issuetrackers_status()
        assert [r["tracker"] for r in status["records"]] == [
            "linear"]
        assert status["book"]["records"][0]["issue_key"] == (
            "ENG-1")
        assert status["held"] == ["linear/ENG-1"]
        assert status["open"] == []
        assert "held as fact" in status["records_text"]
        assert len(_issue_events(
            store, session_id, "issuetrackers_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_issuetrackers_record(_issue_record())
        with pytest.raises(ValueError, match="linear"):
            agent.register_issuetrackers_record(
                _issue_record(ref="dev"))
        assert len(_issue_events(
            store, session_id, "issuetrackers_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_issuetrackers_record(
                _issue_record(claims=["vibes"]))
        assert agent.issuetrackers_status()["records"] == []
        assert _issue_events(
            store, session_id, "issuetrackers_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_issuetrackers_records([
            _held_for("jira"), _issue_record()])
        assert result["count"] == 2
        assert [r["tracker"] for r in result["records_news"]] == [
            "jira", "linear"]
        assert len(_issue_events(
            store, session_id, "issuetrackers_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_issuetrackers_records(
            [_held_for("generic_mcp")])
        assert result["count"] == 1
        assert result["book"]["schema"] == ISSUE_TRACKER_SCHEMA
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_issuetrackers_records(
                [_held_for("generic_mcp")])
        assert len(_issue_events(
            store, session_id, "issuetrackers_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_issuetrackers_record(_issue_record())
        result = agent.view_issuetrackers("linear", "ENG-1")
        assert result["tracker"]["id"] == "linear"
        assert result["standing"]["held"] is True
        assert result["record"]["issue_key"] == "ENG-1"
        assert result["record_news"]["type"] == (
            "issuetrackers_standing")
        assert result["held_record_news"]["type"] == (
            "issuetrackers_record")
        assert len(_issue_events(
            store, session_id, "issuetrackers_record")) == 1
        assert len(_issue_events(
            store, session_id, "issuetrackers_standing")) == 1
        result = agent.view_issuetrackers("jira", "ENG-1")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_issue_events(
            store, session_id, "issuetrackers_standing")) == 2
        agent.close()


class TestIssueTrackersDrafts:
    def test_propose_write_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.propose_issuetrackers_draft(
            "linear", "ENG-1", "add a cache step")
        assert result["draft"]["approval"] == (
            "pending")
        assert result["draft"]["applied"] is False
        assert result["draft_news"]["type"] == (
            "issuetrackers_draft")
        assert "add a cache step" in result["screen"]
        draft = agent.get_issuetrackers_draft(
            "linear", "ENG-1")
        assert draft.change == "add a cache step"
        assert [d.issue_key for d in agent.issuetrackers_drafts()] == [
            "ENG-1"]
        assert len(_issue_events(
            store, session_id, "issuetrackers_draft")) == 1
        agent.close()

    def test_draft_unapproved_execution_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="by approval only"):
            agent.propose_issuetrackers_draft(
                "linear", "ENG-1", "x", approval="executed")
        assert agent.issuetrackers_drafts() == []
        assert _issue_events(
            store, session_id, "issuetrackers_draft") == []
        agent.close()

    def test_duplicate_draft_refuses(self, agent):
        agent.propose_issuetrackers_draft(
            "linear", "ENG-1", "add a cache step")
        with pytest.raises(ValueError, match="linear"):
            agent.propose_issuetrackers_draft(
                "linear", "ENG-1", "a second telling")
        with pytest.raises(ValueError,
                           match="holds no write draft"):
            agent.get_issuetrackers_draft("jira", "ENG-1")


class TestIssueTrackersParseArgs:
    def test_parse_args_well(self):
        assert parse_issuetrackers_args("") == (
            "show", None, (), None)
        assert parse_issuetrackers_args(None) == (
            "show", None, (), None)
        assert parse_issuetrackers_args("trackers") == (
            "trackers", None, (), None)
        assert parse_issuetrackers_args("tracker jira") == (
            "tracker", "jira", (), None)
        assert parse_issuetrackers_args(
            "record linear ENG-1") == (
            "record", ("linear", "ENG-1"), (), None)
        assert parse_issuetrackers_args(
            "standing jira OPS-2") == (
            "standing", ("jira", "OPS-2"), (), None)
        assert parse_issuetrackers_args("draft") == (
            "drafts", None, (), None)
        assert parse_issuetrackers_args(
            "draft linear ENG-1") == (
            "draft", ("linear", "ENG-1"), (), None)
        assert parse_issuetrackers_args("verdict") == (
            "verdict", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "tracker", "record",
                    "record linear",
                    "trackers now", "standing jira",
                    "draft linear ENG-1 extra"):
            with pytest.raises(ValueError) as caught:
                parse_issuetrackers_args(bad)
            assert str(caught.value) == ISSUETRACKERS_USAGE


class TestIssueTrackersTerminalRoad:
    def test_show_trackers_tracker_record_standing_drafts_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/issuetrackers")
        assert "Linear (linear)" in text
        assert "none held this session" in text
        _, _, text = _slash(agent, "/issuetrackers trackers")
        assert "Generic MCP tracker" in text
        _, _, text = _slash(agent, "/issuetrackers tracker jira")
        assert "ticket" in text
        _, _, text = _slash(
            agent, "/issuetrackers record linear ENG-1")
        assert "holds no issue record" in text
        _, _, text = _slash(
            agent, "/issuetrackers standing linear ENG-1")
        assert "linear/ENG-1: issue open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/issuetrackers draft")
        assert "Write drafts: none held" in text
        _, _, text = _slash(agent, "/issuetrackers verdict")
        assert "Issues stand open" in text
        agent.register_issuetrackers_record(_issue_record())
        _, _, text = _slash(
            agent, "/issuetrackers record linear ENG-1")
        assert "held as fact" in text
        _, _, text = _slash(
            agent, "/issuetrackers standing linear ENG-1")
        assert "linear/ENG-1: issue held as fact" in text
        _, _, text = _slash(agent, "/issuetrackers index")
        assert "held as fact" in text
        agent.propose_issuetrackers_draft(
            "linear", "ENG-1", "add a cache step")
        _, _, text = _slash(
            agent, "/issuetrackers draft linear ENG-1")
        assert "add a cache step" in text
        assert "never applied" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/issuetrackers [show|trackers|tracker <tracker>|"
                "record <tracker> <issue>|"
                "standing <tracker> <issue>|"
                "draft [<tracker> <issue>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/issuetrackers dance party")
        assert text == ISSUETRACKERS_USAGE
        _, _, text = _slash(agent, "/issuetrackers tracker circle")
        assert "unknown issue tracker" in text


@pytest.fixture()
def it_handler(agent, monkeypatch):
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


def _issue_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestIssueTrackersHandler:
    def test_show_is_default(self, it_handler, agent):
        it_handler._handle_issuetrackers("")
        assert "Linear (linear)" in (
            _issue_published_text(it_handler))

    def test_provider_record_and_verdict(
            self, it_handler, agent):
        it_handler._handle_issuetrackers("tracker jira")
        assert "ticket" in (
            _issue_published_text(it_handler))
        agent.register_issuetrackers_record(_issue_record())
        it_handler._handle_issuetrackers(
            "record linear ENG-1")
        assert "held as fact" in (
            _issue_published_text(it_handler))
        it_handler._handle_issuetrackers("verdict")
        assert "Issues stand held" in (
            _issue_published_text(it_handler))

    def test_bad_grammar_is_published(
            self, it_handler, agent):
        it_handler._handle_issuetrackers("dance party")
        assert ISSUETRACKERS_USAGE in (
            _issue_published_text(it_handler))
        it_handler._handle_issuetrackers("tracker circle")
        assert "unknown issue tracker" in (
            _issue_published_text(it_handler))


class TestChatScreenRoutingIssueTrackers:
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
        screen.handle_command("/issuetrackers verdict", _FakeLog())
        assert calls == [("/issuetrackers", "verdict")]

    def test_chat_screen_help_and_usage_name_the_bridges(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/issuetrackers[/green] - show the Issue trackers "
                "(M-248)") in text
        assert ('"/issuetrackers": "Usage: /issuetrackers | '
                "/issuetrackers trackers") in text


class TestIssueTrackersDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.issuetrackers_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _IT_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        verdict = agent.issuetrackers_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_issuetrackers_record(_issue_record())
        agent.register_issuetrackers_record(_held_for("jira"))
        verdict = agent.issuetrackers_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "linear/ENG-1", "jira/ENG-1"]
        assert "Issues stand held" in verdict["verdict_text"]

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_issuetrackers()
        assert report["book"]["schema"] == ISSUE_TRACKER_SCHEMA
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_issuetrackers_record(_issue_record())
        report = agent.report_issuetrackers()
        assert "held as fact" in report["records_text"]
        assert [s["tracker"] for s in report["standings"]] == [
            "linear"]

    def test_records_for_state_and_held_keys(self, agent):
        agent.register_issuetrackers_record(_issue_record())
        agent.register_issuetrackers_record(_issue_record(
            tracker="linear", issue_key="ENG-2",
            state="blocked", stages=["seen"],
            claims=["assertion"]))
        assert [r.issue_key for r in
                agent.records_for_state("open")] == [
            "ENG-1"]
        assert [r.issue_key for r in
                agent.records_for_state("blocked")] == [
            "ENG-2"]
        assert agent.issuetrackers_held() == ["linear/ENG-1"]
        standing = agent.issuetrackers_standing(
            "linear", "ENG-2")
        assert standing.held is False
        assert any("bare claims" in gap
                   for gap in standing.gaps)
