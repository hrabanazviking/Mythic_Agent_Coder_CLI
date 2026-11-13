"""M-247 CI bridges - pure + agent layer tests.

TIER: unit

CI results enter the session as facts only when they rest on
held evidence; workflow changes are proposed only as drafts,
manual-dispatch by default on Volmarr's repos (M-227).
"""
import pytest

from mythic_agent.core.ci_bridges import (
    BARE_CLAIMS,
    CONCLUSIONS,
    HELD_EVIDENCE,
    PROVIDERS,
    STAGES,
    CIRecord,
    ProviderEntry,
    ProviderRegistry,
    WorkflowDraft,
    default_registry,
    derive_standing,
    format_provider,
    format_providers,
    format_record,
    propose_draft,
)
from mythic_agent.core.validation import ValidationError


def held_record(**kw):
    base = dict(provider="github_actions", workflow="CI", ref="main",
                conclusion="passed", stages=STAGES, claims=("run_ref",))
    base.update(kw)
    return CIRecord(**base)


def test_registry_holds_four_providers():
    reg = default_registry()
    assert reg.ids() == ("github_actions", "gitlab_ci",
                         "bitbucket_pipelines", "local_manual")


def test_registry_unknown_provider_refused_by_name():
    with pytest.raises(ValidationError, match="unknown ci provider: circle"):
        default_registry().get("circle")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate ci provider"):
        ProviderRegistry(PROVIDERS + PROVIDERS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        ProviderRegistry([ProviderEntry("x", "", "run", "why")])


def test_provider_words_differ_by_provider():
    reg = default_registry()
    assert reg.get("github_actions").run_word == "workflow run"
    assert reg.get("gitlab_ci").run_word == "pipeline"


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


def test_record_unknown_provider_refused():
    with pytest.raises(ValidationError, match="unknown ci provider"):
        derive_standing(held_record(provider="circle"))


def test_record_names_workflow_and_ref():
    with pytest.raises(ValidationError, match="no workflow"):
        held_record(workflow=" ").validate()
    with pytest.raises(ValidationError, match="no ref"):
        held_record(ref="").validate()


def test_record_conclusion_must_be_known():
    with pytest.raises(ValidationError, match="unknown ci conclusion"):
        held_record(conclusion="green").validate()
    for conclusion in CONCLUSIONS:
        held_record(conclusion=conclusion).validate()


def test_record_claim_kind_must_be_known():
    with pytest.raises(ValidationError, match="unknown ci evidence kind"):
        held_record(claims=("vibes",)).validate()
    for kind in HELD_EVIDENCE + BARE_CLAIMS:
        held_record(claims=(kind,)).validate()


def test_draft_defaults_to_manual_dispatch():
    draft = propose_draft("github_actions", "CI", "add a cache step")
    assert draft.trigger == "workflow_dispatch" and draft.applied is False


def test_draft_automatic_trigger_refused():
    with pytest.raises(ValidationError, match="manually"):
        propose_draft("github_actions", "CI", "x", trigger="push")


def test_draft_never_applied():
    with pytest.raises(ValidationError, match="drafts only"):
        WorkflowDraft("github_actions", "CI", "x", applied=True).validate()


def test_draft_names_workflow_and_change():
    with pytest.raises(ValidationError, match="no workflow"):
        propose_draft("github_actions", " ", "x")
    with pytest.raises(ValidationError, match="no change"):
        propose_draft("github_actions", "CI", " ")


def test_format_lines():
    reg = default_registry()
    assert "GitHub Actions" in format_provider(reg.get("github_actions"))
    assert format_providers(reg).count("\n") == 3
    line = format_record(held_record())
    assert "held as fact" in line and "passed" in line
    open_line = format_record(held_record(claims=()))
    assert "open:" in open_line

# ---------------------------------------------------------------------
# M-247 agent layer: the agent holds the shipped provider
# registry and one run record per provider and workflow
# for the session, records, viewed standings and proposed
# drafts are published as session news through the
# checkpoint road (journal-first, deduped per record,
# standing and draft), standings, the index and the
# verdict are derived at call time from the held records
# - a run stands held only on a full legal walk resting
# on held evidence - workflow changes are proposed only
# as drafts, manual dispatch by default, never applied,
# and the registry is session state, never a stored
# setting. This layer calls no CI API, fetches no run,
# changes no workflow and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    CIBRIDGES_USAGE,
    parse_cibridges_args,
)
from mythic_agent.core.ci_bridges import (
    CI_BRIDGE_SCHEMA,
    PLAIN_EXPLANATION,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore

ROOT = _Path(__file__).resolve().parent.parent

_CI_EVENT_TYPES = (
    "cibridges_record", "cibridges_standing", "cibridges_draft")

ALL_PROVIDERS = ["github_actions", "gitlab_ci",
                 "bitbucket_pipelines", "local_manual"]


def _ci_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _ci_record(**overrides):
    raw = {
        "provider": "github_actions",
        "workflow": "CI",
        "ref": "main",
        "conclusion": "passed",
        "stages": list(STAGES),
        "claims": ["run_ref"],
    }
    raw.update(overrides)
    return raw


def _held_for(provider, workflow="CI"):
    return _ci_record(provider=provider, workflow=workflow)


class TestCIBridgesAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_providers(
            self, agent):
        status = agent.cibridges_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["cibridges_book"]["schema"] == (
            CI_BRIDGE_SCHEMA)
        assert [p["id"] for p in status[
            "cibridges_book"]["providers"]] == ALL_PROVIDERS
        assert status["cibridges_book"]["records"] == []
        assert status["cibridges_book"]["drafts"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "GitHub Actions" in status["providers_text"]
        assert "workflow run" in status["providers_text"]
        assert "none held this session" in status["screen"]
        assert "held evidence" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == CIBRIDGES_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._cibridges_registry()
        assert agent._cibridges_registry() is first
        assert agent._cibridges_store is first
        for name in ("cibridges_providers",
                     "cibridges_book",
                     "cibridges_status",
                     "get_cibridges_provider",
                     "get_cibridges_record",
                     "cibridges_standing",
                     "records_for_conclusion",
                     "cibridges_held",
                     "cibridges_index",
                     "cibridges_verdict",
                     "propose_cibridges_draft",
                     "get_cibridges_draft",
                     "cibridges_drafts",
                     "report_cibridges"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_cibridges_registry", "cibridges_providers",
            "cibridges_book", "cibridges_status",
            "get_cibridges_provider",
            "get_cibridges_record",
            "cibridges_standing", "records_for_conclusion",
            "cibridges_held", "cibridges_index",
            "cibridges_verdict",
            "register_cibridges_record",
            "register_cibridges_records",
            "record_cibridges_records",
            "view_cibridges", "propose_cibridges_draft",
            "report_cibridges",
            "_publish_cibridges_record",
            "_cibridges_screen",
            "_cibridges_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.cibridges_status()
        entry = agent.get_cibridges_provider("gitlab_ci")
        assert entry.run_word == "pipeline"
        standing = agent.cibridges_standing(
            "github_actions", "CI")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert agent.cibridges_held() == []
        assert agent.records_for_conclusion("passed") == []
        agent.cibridges_index()
        agent.cibridges_verdict()
        agent.report_cibridges()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _CI_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown ci provider"):
            agent.get_cibridges_provider("circle")
        with pytest.raises(ValueError, match="unknown ci provider"):
            agent.cibridges_standing("circle", "CI")
        with pytest.raises(ValueError, match="holds no ci record"):
            agent.get_cibridges_record("github_actions", "CI")
        with pytest.raises(ValueError):
            agent.records_for_conclusion("")
        with pytest.raises(ValueError, match="unknown conclusion"):
            agent.records_for_conclusion("green")
        agent.close()


class TestCIBridgesAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_cibridges_record(_ci_record())
        assert result["record"]["provider"] == "github_actions"
        assert result["record"]["workflow"] == "CI"
        assert result["record_news"]["type"] == (
            "cibridges_record")
        assert "held as fact" in result["screen"]
        status = agent.cibridges_status()
        assert [r["provider"] for r in status["records"]] == [
            "github_actions"]
        assert status["book"]["records"][0]["workflow"] == (
            "CI")
        assert status["held"] == ["github_actions/CI"]
        assert status["open"] == []
        assert "held as fact" in status["records_text"]
        assert len(_ci_events(
            store, session_id, "cibridges_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_cibridges_record(_ci_record())
        with pytest.raises(ValueError, match="github_actions"):
            agent.register_cibridges_record(
                _ci_record(ref="dev"))
        assert len(_ci_events(
            store, session_id, "cibridges_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_cibridges_record(
                _ci_record(claims=["vibes"]))
        assert agent.cibridges_status()["records"] == []
        assert _ci_events(
            store, session_id, "cibridges_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_cibridges_records([
            _held_for("gitlab_ci"), _ci_record()])
        assert result["count"] == 2
        assert [r["provider"] for r in result["records_news"]] == [
            "gitlab_ci", "github_actions"]
        assert len(_ci_events(
            store, session_id, "cibridges_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_cibridges_records(
            [_held_for("bitbucket_pipelines")])
        assert result["count"] == 1
        assert result["book"]["schema"] == CI_BRIDGE_SCHEMA
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_cibridges_records(
                [_held_for("bitbucket_pipelines")])
        assert len(_ci_events(
            store, session_id, "cibridges_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_cibridges_record(_ci_record())
        result = agent.view_cibridges("github_actions", "CI")
        assert result["provider"]["id"] == "github_actions"
        assert result["standing"]["held"] is True
        assert result["record"]["workflow"] == "CI"
        assert result["record_news"]["type"] == (
            "cibridges_standing")
        assert result["held_record_news"]["type"] == (
            "cibridges_record")
        assert len(_ci_events(
            store, session_id, "cibridges_record")) == 1
        assert len(_ci_events(
            store, session_id, "cibridges_standing")) == 1
        result = agent.view_cibridges("gitlab_ci", "CI")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_ci_events(
            store, session_id, "cibridges_standing")) == 2
        agent.close()


class TestCIBridgesDrafts:
    def test_propose_draft_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.propose_cibridges_draft(
            "github_actions", "CI", "add a cache step")
        assert result["draft"]["trigger"] == (
            "workflow_dispatch")
        assert result["draft"]["applied"] is False
        assert result["draft_news"]["type"] == (
            "cibridges_draft")
        assert "add a cache step" in result["screen"]
        draft = agent.get_cibridges_draft(
            "github_actions", "CI")
        assert draft.change == "add a cache step"
        assert [d.workflow for d in agent.cibridges_drafts()] == [
            "CI"]
        assert len(_ci_events(
            store, session_id, "cibridges_draft")) == 1
        agent.close()

    def test_draft_automatic_trigger_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="manually"):
            agent.propose_cibridges_draft(
                "github_actions", "CI", "x", trigger="push")
        assert agent.cibridges_drafts() == []
        assert _ci_events(
            store, session_id, "cibridges_draft") == []
        agent.close()

    def test_duplicate_draft_refuses(self, agent):
        agent.propose_cibridges_draft(
            "github_actions", "CI", "add a cache step")
        with pytest.raises(ValueError, match="github_actions"):
            agent.propose_cibridges_draft(
                "github_actions", "CI", "a second telling")
        with pytest.raises(ValueError,
                           match="holds no workflow draft"):
            agent.get_cibridges_draft("gitlab_ci", "CI")


class TestCIBridgesParseArgs:
    def test_parse_args_well(self):
        assert parse_cibridges_args("") == (
            "show", None, (), None)
        assert parse_cibridges_args(None) == (
            "show", None, (), None)
        assert parse_cibridges_args("providers") == (
            "providers", None, (), None)
        assert parse_cibridges_args("provider gitlab_ci") == (
            "provider", "gitlab_ci", (), None)
        assert parse_cibridges_args(
            "record github_actions CI") == (
            "record", ("github_actions", "CI"), (), None)
        assert parse_cibridges_args(
            "standing gitlab_ci Pipeline") == (
            "standing", ("gitlab_ci", "Pipeline"), (), None)
        assert parse_cibridges_args("draft") == (
            "drafts", None, (), None)
        assert parse_cibridges_args(
            "draft github_actions CI") == (
            "draft", ("github_actions", "CI"), (), None)
        assert parse_cibridges_args("verdict") == (
            "verdict", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "provider", "record",
                    "record github_actions",
                    "providers now", "standing gitlab_ci",
                    "draft github_actions CI extra"):
            with pytest.raises(ValueError) as caught:
                parse_cibridges_args(bad)
            assert str(caught.value) == CIBRIDGES_USAGE


class TestCIBridgesTerminalRoad:
    def test_show_providers_provider_record_standing_drafts_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/cibridges")
        assert "GitHub Actions (github_actions)" in text
        assert "none held this session" in text
        _, _, text = _slash(agent, "/cibridges providers")
        assert "Local manual run" in text
        _, _, text = _slash(agent, "/cibridges provider gitlab_ci")
        assert "pipeline" in text
        _, _, text = _slash(
            agent, "/cibridges record github_actions CI")
        assert "holds no ci record" in text
        _, _, text = _slash(
            agent, "/cibridges standing github_actions CI")
        assert "github_actions/CI: CI open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/cibridges draft")
        assert "Workflow drafts: none held" in text
        _, _, text = _slash(agent, "/cibridges verdict")
        assert "CI stands open" in text
        agent.register_cibridges_record(_ci_record())
        _, _, text = _slash(
            agent, "/cibridges record github_actions CI")
        assert "held as fact" in text
        _, _, text = _slash(
            agent, "/cibridges standing github_actions CI")
        assert "github_actions/CI: CI held as fact" in text
        _, _, text = _slash(agent, "/cibridges index")
        assert "held as fact" in text
        agent.propose_cibridges_draft(
            "github_actions", "CI", "add a cache step")
        _, _, text = _slash(
            agent, "/cibridges draft github_actions CI")
        assert "add a cache step" in text
        assert "never applied" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/cibridges [show|providers|provider <provider>|"
                "record <provider> <workflow>|"
                "standing <provider> <workflow>|"
                "draft [<provider> <workflow>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/cibridges dance party")
        assert text == CIBRIDGES_USAGE
        _, _, text = _slash(agent, "/cibridges provider circle")
        assert "unknown ci provider" in text


@pytest.fixture()
def ci_handler(agent, monkeypatch):
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


def _ci_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCIBridgesHandler:
    def test_show_is_default(self, ci_handler, agent):
        ci_handler._handle_cibridges("")
        assert "GitHub Actions (github_actions)" in (
            _ci_published_text(ci_handler))

    def test_provider_record_and_verdict(
            self, ci_handler, agent):
        ci_handler._handle_cibridges("provider gitlab_ci")
        assert "pipeline" in (
            _ci_published_text(ci_handler))
        agent.register_cibridges_record(_ci_record())
        ci_handler._handle_cibridges(
            "record github_actions CI")
        assert "held as fact" in (
            _ci_published_text(ci_handler))
        ci_handler._handle_cibridges("verdict")
        assert "CI stands held" in (
            _ci_published_text(ci_handler))

    def test_bad_grammar_is_published(
            self, ci_handler, agent):
        ci_handler._handle_cibridges("dance party")
        assert CIBRIDGES_USAGE in (
            _ci_published_text(ci_handler))
        ci_handler._handle_cibridges("provider circle")
        assert "unknown ci provider" in (
            _ci_published_text(ci_handler))


class TestChatScreenRoutingCIBridges:
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
        screen.handle_command("/cibridges verdict", _FakeLog())
        assert calls == [("/cibridges", "verdict")]

    def test_chat_screen_help_and_usage_name_the_bridges(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/cibridges[/green] - show the CI bridges "
                "(M-247)") in text
        assert ('"/cibridges": "Usage: /cibridges | '
                "/cibridges providers") in text


class TestCIBridgesDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.cibridges_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _CI_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        verdict = agent.cibridges_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_cibridges_record(_ci_record())
        agent.register_cibridges_record(_held_for("gitlab_ci"))
        verdict = agent.cibridges_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "github_actions/CI", "gitlab_ci/CI"]
        assert "CI stands held" in verdict["verdict_text"]

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_cibridges()
        assert report["book"]["schema"] == CI_BRIDGE_SCHEMA
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_cibridges_record(_ci_record())
        report = agent.report_cibridges()
        assert "held as fact" in report["records_text"]
        assert [s["provider"] for s in report["standings"]] == [
            "github_actions"]

    def test_records_for_conclusion_and_held_keys(self, agent):
        agent.register_cibridges_record(_ci_record())
        agent.register_cibridges_record(_ci_record(
            provider="github_actions", workflow="Lint",
            conclusion="failed", stages=["seen"],
            claims=["assertion"]))
        assert [r.workflow for r in
                agent.records_for_conclusion("passed")] == [
            "CI"]
        assert [r.workflow for r in
                agent.records_for_conclusion("failed")] == [
            "Lint"]
        assert agent.cibridges_held() == ["github_actions/CI"]
        standing = agent.cibridges_standing(
            "github_actions", "Lint")
        assert standing.held is False
        assert any("bare claims" in gap
                   for gap in standing.gaps)
