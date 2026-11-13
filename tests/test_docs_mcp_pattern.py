"""M-252 Docs MCP pattern - pure-layer tests.

TIER: unit

Sessions, campaigns, memories and configs leave only as a
recorded record in an open format; an absent record reads
as unknown and a stale one as stale, never as a fact,
and this book only proposes export proposals - leaving is
as easy as arriving.
"""
import pytest

from mythic_agent.core.docs_mcp_pattern import (
    BARE_CLAIMS,
    ATTACH_SCOPES,
    FRESH_LIMIT_SECONDS,
    HELD_EVIDENCE,
    PROJECTS,
    STAGES,
    AttachmentDraft,
    AttachmentRecord,
    ProjectEntry,
    ProjectRegistry,
    default_registry,
    derive_standing,
    format_project,
    format_projects,
    format_record,
    prepare_proposal,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(project="mojo", record="attach-42",
                scope="full", title="Leave with everything",
                subject="Session 42 in mythic-coder",
                observed_at="2026-11-12T12:00:00", age_seconds=60,
                stages=STAGES, claims=("manifest_ref",))
    base.update(kw)
    return AttachmentRecord(**base)


def test_registry_holds_four_projects_open_only():
    reg = default_registry()
    assert reg.ids() == ("mojo", "python",
                         "rust", "generic")
    assert all(e.bridge == "recorded" for e in reg.entries())


def test_registry_unknown_project_refused_by_name():
    with pytest.raises(ValidationError, match="unknown docs project: guess"):
        default_registry().get("guess")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate docs project"):
        ProjectRegistry(PROJECTS + PROJECTS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        ProjectRegistry([ProjectEntry("x", "", "thing", "JSON", "open", "why")])


def test_entry_proprietary_format_refused():
    with pytest.raises(ValidationError, match="recorded data only"):
        ProjectRegistry([ProjectEntry("x", "X", "thing", "remote_mcp", "live", "why")])


def test_project_words_and_formats_differ_by_project():
    reg = default_registry()
    assert reg.get("mojo").item_word == "doc"
    assert reg.get("python").item_word == "reference"
    assert reg.get("rust").item_word == "doc"
    assert reg.get("generic").item_word == "page"
    assert reg.get("mojo").transport == "remote_mcp"
    assert reg.get("python").transport == "remote_mcp"
    assert reg.get("rust").transport == "stdio_mcp"
    assert reg.get("generic").transport == "recorded_mcp"


def test_fresh_held_record_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held and standing.stage == "held"
    assert standing.freshness == "current" and standing.gaps == ()


def test_bare_claims_only_stands_open():
    standing = derive_standing(fresh_record(claims=("assertion",)))
    assert not standing.held
    assert any("bare claims" in g for g in standing.gaps)


def test_no_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=()))
    assert not standing.held
    assert any("no held evidence" in g for g in standing.gaps)


def test_unfinished_walk_stands_open():
    standing = derive_standing(fresh_record(stages=("named", "described")))
    assert not standing.held and standing.stage == "described"


def test_walk_must_open_at_listed():
    standing = derive_standing(
        fresh_record(stages=("described", "checked", "held")))
    assert not standing.held
    assert any("open at named" in g for g in standing.gaps)


def test_walk_rejects_skipped_stage():
    standing = derive_standing(
        fresh_record(stages=("named", "checked", "held")))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_stale_record_stands_open_as_stale():
    standing = derive_standing(
        fresh_record(age_seconds=FRESH_LIMIT_SECONDS + 1))
    assert not standing.held and standing.freshness == "stale"
    assert any("stale" in g for g in standing.gaps)
    fresh = derive_standing(
        fresh_record(age_seconds=FRESH_LIMIT_SECONDS))
    assert fresh.held and fresh.freshness == "current"


def test_unknown_scope_or_no_subject_stands_open():
    standing = derive_standing(fresh_record(scope="unknown"))
    assert not standing.held
    assert any("scope" in g for g in standing.gaps)
    standing = derive_standing(fresh_record(subject=""))
    assert not standing.held
    assert any("subject" in g for g in standing.gaps)


def test_record_unknown_project_and_missing_fields_refused():
    with pytest.raises(ValidationError, match="unknown docs project"):
        derive_standing(fresh_record(project="guess"))
    with pytest.raises(ValidationError, match="no record"):
        fresh_record(record=" ").validate()
    with pytest.raises(ValidationError, match="no observed time"):
        fresh_record(observed_at="").validate()


def test_record_scope_words_must_be_known():
    with pytest.raises(ValidationError, match="unknown attachment record scope"):
        fresh_record(scope="green").validate()
    for scope in ATTACH_SCOPES:
        fresh_record(scope=scope).validate()


def test_record_claim_project_and_age_must_be_known():
    with pytest.raises(ValidationError, match="unknown attachment evidence kind"):
        fresh_record(claims=("vibes",)).validate()
    for project in HELD_EVIDENCE + BARE_CLAIMS:
        fresh_record(claims=(project,)).validate()
    with pytest.raises(ValidationError, match="non-negative"):
        fresh_record(age_seconds=-1).validate()


def test_proposal_defaults_to_ready_state():
    proposal = prepare_proposal("mythic-coder", "mojo", "attach-42",
                          "export the session")
    assert proposal.state == "ready" and proposal.attached is False


def test_proposal_locked_or_gated_state_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_proposal("b", "mojo", "export-1", "x", state="locked")
    shared = prepare_proposal("b", "mojo", "export-1", "x", state="shared")
    assert shared.state == "shared" and shared.attached is False


def test_proposal_never_attached_and_format_lines():
    with pytest.raises(ValidationError, match="never attached"):
        AttachmentDraft("b", "mojo", "export-1", "x", attached=True).validate()
    with pytest.raises(ValidationError, match="no bridge"):
        prepare_proposal(" ", "mojo", "export-1", "x")
    with pytest.raises(ValidationError, match="no record"):
        prepare_proposal("b", "mojo", " ", "x")
    with pytest.raises(ValidationError, match="proposes nothing"):
        prepare_proposal("b", "mojo", "export-1", " ")
    reg = default_registry()
    assert "Mojo Docs" in format_project(reg.get("mojo"))
    assert "recorded knowledge bridge" in format_project(reg.get("generic"))
    assert format_projects(reg).count("\n") == 3
    line = format_record(fresh_record())
    assert "held as bridge" in line and "attach-42" in line
    open_line = format_record(fresh_record(claims=()))
    assert "open:" in open_line


# ---------------------------------------------------------------------
# M-252 agent layer: the agent holds the shipped project
# registry and one attachment record per project and record for
# the session, records, viewed standings and proposed
# proposals are published as session news through the
# checkpoint road (journal-first, deduped per record,
# standing and proposal), standings, the index and the
# verdict are derived at call time from the held records -
# an record is a fact only when it rests on held evidence -
# bridge proposals are proposed only as proposals, state
# ready by default, may be marked shared by a human,
# and never attached or built, and the registry is session
# state, never a stored setting. This layer opens no
# export listener, calls no host API, probes no network
# and exports nothing here.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    DOCSMCP_USAGE,
    parse_docsmcp_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.docs_mcp_pattern import (
    PLAIN_EXPLANATION,
    DOCS_MCP_PATTERN_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_DM_EVENT_TYPES = (
    "docsmcp_record", "docsmcp_standing", "docsmcp_proposal")

ALL_PROJECTS = ["mojo", "python", "rust", "generic"]


def _dm_records(store, session_id, project):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == project]


def _dm_record(**overrides):
    raw = {
        "project": "mojo",
        "record": "attach-42",
        "scope": "full",
        "title": "Fix the seam",
        "subject": "PR 42 in mythic-coder",
        "observed_at": "2026-11-12T12:00:00",
        "age_seconds": 60,
        "stages": list(STAGES),
        "claims": ["manifest_ref"],
    }
    raw.update(overrides)
    return raw


def _fresh_for(project, record="attach-42"):
    return _dm_record(project=project, record=record)


class TestDocsMcpPatternAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_projects(
            self, agent):
        status = agent.docsmcp_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["docsmcp_book"]["schema"] == (
            DOCS_MCP_PATTERN_SCHEMA)
        assert [p["id"] for p in status[
            "docsmcp_book"]["projects"]] == ALL_PROJECTS
        assert status["docsmcp_book"]["records"] == []
        assert status["docsmcp_book"]["proposals"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "Mojo Docs" in status["projects_text"]
        assert "recorded knowledge bridge" in status["projects_text"]
        assert "none recorded this session" in status["screen"]
        assert "in one step" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == DOCSMCP_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._docsmcp_registry()
        assert agent._docsmcp_registry() is first
        assert agent._docsmcp_store is first
        for name in ("docsmcp_projects",
                     "docsmcp_book",
                     "docsmcp_status",
                     "get_docsmcp_project",
                     "get_docsmcp_record",
                     "docsmcp_standing",
                     "attachments_for_scope",
                     "docsmcp_held",
                     "docsmcp_index",
                     "docsmcp_verdict",
                     "prepare_docsmcp_proposal",
                     "get_docsmcp_proposal",
                     "docsmcp_proposals",
                     "report_docsmcp"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_docsmcp_registry", "docsmcp_projects",
            "docsmcp_book", "docsmcp_status",
            "get_docsmcp_project",
            "get_docsmcp_record",
            "docsmcp_standing", "attachments_for_scope",
            "docsmcp_held", "docsmcp_index",
            "docsmcp_verdict",
            "register_docsmcp_record",
            "register_docsmcp_records",
            "record_docsmcp_records",
            "view_docsmcp", "prepare_docsmcp_proposal",
            "report_docsmcp",
            "_publish_docsmcp_record",
            "_docsmcp_screen",
            "_docsmcp_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.docsmcp_status()
        entry = agent.get_docsmcp_project("generic")
        assert entry.item_word == "page"
        standing = agent.docsmcp_standing(
            "mojo", "attach-42")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.freshness == "stale"
        assert agent.docsmcp_held() == []
        assert agent.attachments_for_scope("full") == []
        agent.docsmcp_index()
        agent.docsmcp_verdict()
        agent.report_docsmcp()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _DM_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown docs project"):
            agent.get_docsmcp_project("guess")
        with pytest.raises(ValueError, match="unknown docs project"):
            agent.docsmcp_standing("guess", "attach-42")
        with pytest.raises(ValueError, match="holds no attachment record"):
            agent.get_docsmcp_record("mojo", "attach-42")
        with pytest.raises(ValueError):
            agent.attachments_for_scope("")
        with pytest.raises(ValueError, match="unknown attachment record scope"):
            agent.attachments_for_scope("green")
        agent.close()


class TestDocsMcpPatternAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_docsmcp_record(_dm_record())
        assert result["record"]["project"] == "mojo"
        assert result["record"]["record"] == "attach-42"
        assert result["record_news"]["type"] == (
            "docsmcp_record")
        assert "held as bridge" in result["screen"]
        status = agent.docsmcp_status()
        assert [r["project"] for r in status["records"]] == [
            "mojo"]
        assert status["book"]["records"][0]["record"] == (
            "attach-42")
        assert status["held"] == ["mojo/attach-42"]
        assert status["open"] == []
        assert "held as bridge" in status["records_text"]
        assert len(_dm_records(
            store, session_id, "docsmcp_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_docsmcp_record(_dm_record())
        with pytest.raises(ValueError, match="mojo"):
            agent.register_docsmcp_record(
                _dm_record(title="A second telling"))
        assert len(_dm_records(
            store, session_id, "docsmcp_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_docsmcp_record(
                _dm_record(claims=["vibes"]))
        assert agent.docsmcp_status()["records"] == []
        assert _dm_records(
            store, session_id, "docsmcp_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_docsmcp_records([
            _fresh_for("generic"), _dm_record()])
        assert result["count"] == 2
        assert [r["project"] for r in result["records_news"]] == [
            "generic", "mojo"]
        assert len(_dm_records(
            store, session_id, "docsmcp_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_docsmcp_records(
            [_fresh_for("python")])
        assert result["count"] == 1
        assert result["book"]["schema"] == DOCS_MCP_PATTERN_SCHEMA
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_docsmcp_records(
                [_fresh_for("python")])
        assert len(_dm_records(
            store, session_id, "docsmcp_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_docsmcp_record(_dm_record())
        result = agent.view_docsmcp("mojo", "attach-42")
        assert result["project"]["id"] == "mojo"
        assert result["standing"]["held"] is True
        assert result["record"]["record"] == "attach-42"
        assert result["record_news"]["type"] == (
            "docsmcp_standing")
        assert result["held_record_news"]["type"] == (
            "docsmcp_record")
        assert len(_dm_records(
            store, session_id, "docsmcp_record")) == 1
        assert len(_dm_records(
            store, session_id, "docsmcp_standing")) == 1
        result = agent.view_docsmcp("generic", "attach-42")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_dm_records(
            store, session_id, "docsmcp_standing")) == 2
        agent.close()


class TestDocsMcpPatternProposals:
    def test_prepare_proposal_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_docsmcp_proposal(
            "mythic-coder", "mojo", "attach-42", "attach the Mojo docs bridge")
        assert result["proposal"]["state"] == (
            "ready")
        assert result["proposal"]["attached"] is False
        assert result["proposal_news"]["type"] == (
            "docsmcp_proposal")
        assert "attach the Mojo docs bridge" in result["screen"]
        proposal = agent.get_docsmcp_proposal(
            "mythic-coder")
        assert proposal.project == "mojo"
        assert [d.bridge for d in agent.docsmcp_proposals()] == [
            "mythic-coder"]
        assert len(_dm_records(
            store, session_id, "docsmcp_proposal")) == 1
        agent.close()

    def test_proposal_unshared_execution_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared only"):
            agent.prepare_docsmcp_proposal(
                "mythic-coder", "mojo", "attach-42", "x",
                state="executed")
        assert agent.docsmcp_proposals() == []
        assert _dm_records(
            store, session_id, "docsmcp_proposal") == []
        agent.close()

    def test_duplicate_proposal_refuses(self, agent):
        agent.prepare_docsmcp_proposal(
            "mythic-coder", "mojo", "attach-42", "attach the Mojo docs bridge")
        with pytest.raises(ValueError, match="mythic-coder"):
            agent.prepare_docsmcp_proposal(
                "mythic-coder", "python", "issue-7", "a second telling")
        with pytest.raises(ValueError,
                           match="holds no bridge proposal"):
            agent.get_docsmcp_proposal("samverk")


class TestDocsMcpPatternParseArgs:
    def test_parse_args_well(self):
        assert parse_docsmcp_args("") == (
            "show", None, (), None)
        assert parse_docsmcp_args(None) == (
            "show", None, (), None)
        assert parse_docsmcp_args("projects") == (
            "projects", None, (), None)
        assert parse_docsmcp_args("project generic") == (
            "project", "generic", (), None)
        assert parse_docsmcp_args(
            "record mojo attach-42") == (
            "record", ("mojo", "attach-42"), (), None)
        assert parse_docsmcp_args(
            "standing python issue-7") == (
            "standing", ("python", "issue-7"), (), None)
        assert parse_docsmcp_args("propose") == (
            "proposals", None, (), None)
        assert parse_docsmcp_args(
            "propose mythic-coder") == (
            "propose", "mythic-coder", (), None)
        assert parse_docsmcp_args("verdict") == (
            "verdict", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "project", "record",
                    "record sessions",
                    "projects now", "standing campaigns",
                    "propose mythic-coder extra"):
            with pytest.raises(ValueError) as caught:
                parse_docsmcp_args(bad)
            assert str(caught.value) == DOCSMCP_USAGE


class TestDocsMcpPatternTerminalRoad:
    def test_show_projects_project_record_standing_propose_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/docsmcp")
        assert "Mojo Docs (mojo)" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/docsmcp projects")
        assert "Python Docs" in text
        _, _, text = _slash(agent, "/docsmcp project generic")
        assert "recorded_mcp" in text
        _, _, text = _slash(
            agent, "/docsmcp record mojo attach-42")
        assert "holds no attachment record" in text
        _, _, text = _slash(
            agent, "/docsmcp standing mojo attach-42")
        assert "mojo/attach-42: attachment open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/docsmcp propose")
        assert "Bridge proposal: none held" in text
        _, _, text = _slash(agent, "/docsmcp verdict")
        assert "Docs MCP pattern stands open" in text
        agent.register_docsmcp_record(_dm_record())
        _, _, text = _slash(
            agent, "/docsmcp record mojo attach-42")
        assert "held as bridge" in text
        _, _, text = _slash(
            agent, "/docsmcp standing mojo attach-42")
        assert "mojo/attach-42: attachment held as bridge" in text
        _, _, text = _slash(agent, "/docsmcp index")
        assert "held as bridge" in text
        agent.prepare_docsmcp_proposal(
            "mythic-coder", "mojo", "attach-42", "attach the Mojo docs bridge")
        _, _, text = _slash(
            agent, "/docsmcp propose mythic-coder")
        assert "attach the Mojo docs bridge" in text
        assert "never attached" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/docsmcp [show|projects|project <project>|"
                "record <project> <record>|"
                "standing <project> <record>|"
                "propose [<bridge>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/docsmcp dance party")
        assert text == DOCSMCP_USAGE
        _, _, text = _slash(agent, "/docsmcp project guess")
        assert "unknown docs project" in text


@pytest.fixture()
def dm_handler(agent, monkeypatch):
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


def _dm_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestDocsMcpPatternHandler:
    def test_show_is_default(self, dm_handler, agent):
        dm_handler._handle_docsmcp("")
        assert "Mojo Docs (mojo)" in (
            _dm_published_text(dm_handler))

    def test_project_record_and_verdict(
            self, dm_handler, agent):
        dm_handler._handle_docsmcp("project generic")
        assert "recorded_mcp" in (
            _dm_published_text(dm_handler))
        agent.register_docsmcp_record(_dm_record())
        dm_handler._handle_docsmcp(
            "record mojo attach-42")
        assert "held as bridge" in (
            _dm_published_text(dm_handler))
        dm_handler._handle_docsmcp("verdict")
        assert "Docs MCP pattern stands held" in (
            _dm_published_text(dm_handler))

    def test_bad_grammar_is_published(
            self, dm_handler, agent):
        dm_handler._handle_docsmcp("dance party")
        assert DOCSMCP_USAGE in (
            _dm_published_text(dm_handler))
        dm_handler._handle_docsmcp("project guess")
        assert "unknown docs project" in (
            _dm_published_text(dm_handler))


class TestChatScreenRoutingDocsMcpPattern:
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
        screen.handle_command("/docsmcp verdict", _FakeLog())
        assert calls == [("/docsmcp", "verdict")]

    def test_chat_screen_help_and_usage_name_the_doors(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/docsmcp[/green] - show the Docs MCP pattern "
                "(M-252)") in text
        assert ('"/docsmcp": "Usage: /docsmcp | '
                "/docsmcp projects") in text


class TestDocsMcpPatternDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.docsmcp_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _DM_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        verdict = agent.docsmcp_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_docsmcp_record(_dm_record())
        agent.register_docsmcp_record(_fresh_for("python"))
        verdict = agent.docsmcp_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "mojo/attach-42", "python/attach-42"]
        assert "Docs MCP pattern stands held" in verdict["verdict_text"]

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_docsmcp()
        assert report["book"]["schema"] == DOCS_MCP_PATTERN_SCHEMA
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_docsmcp_record(_dm_record())
        report = agent.report_docsmcp()
        assert "held as bridge" in report["records_text"]
        assert [s["project"] for s in report["standings"]] == [
            "mojo"]

    def test_attachments_for_scope_and_held_keys(self, agent):
        agent.register_docsmcp_record(_dm_record())
        agent.register_docsmcp_record(_dm_record(
            record="issue-9", scope="index_only",
            stages=["named"], claims=["assertion"]))
        assert [r.record for r in
                agent.attachments_for_scope("full")] == [
            "attach-42"]
        assert [r.record for r in
                agent.attachments_for_scope("index_only")] == [
            "issue-9"]
        assert agent.docsmcp_held() == ["mojo/attach-42"]
        standing = agent.docsmcp_standing(
            "mojo", "issue-9")
        assert standing.held is False
        assert any("bare claims" in gap
                   for gap in standing.gaps)
