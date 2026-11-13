"""M-253 Bridge permissions audit - pure-layer tests.

TIER: unit

Sessions, campaigns, memories and configs leave only as a
recorded record in an open format; an absent record reads
as unknown and a stale one as stale, never as a fact,
and this book only reports export reports - leaving is
as easy as arriving.
"""
import pytest

from mythic_agent.core.bridge_permissions import (
    BARE_CLAIMS,
    AUDIT_SCOPES,
    FRESH_LIMIT_SECONDS,
    HELD_EVIDENCE,
    BRIDGES,
    STAGES,
    AuditDraft,
    AuditRecord,
    BridgeEntry,
    BridgeRegistry,
    default_registry,
    derive_standing,
    format_bridge,
    format_bridges,
    format_record,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(bridge="github", record="audit-42",
                scope="full", title="Leave with everything",
                subject="Session 42 in mythic-coder",
                observed_at="2026-11-12T12:00:00", age_seconds=60,
                stages=STAGES, claims=("kista_ref",))
    base.update(kw)
    return AuditRecord(**base)


def test_registry_holds_four_bridges_open_only():
    reg = default_registry()
    assert reg.ids() == ("github", "gitlab",
                         "samverk", "samtal")
    assert all(e.standing == "listed" for e in reg.entries())


def test_registry_unknown_bridge_refused_by_name():
    with pytest.raises(ValidationError, match="unknown bridge: guess"):
        default_registry().get("guess")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate bridge"):
        BridgeRegistry(BRIDGES + BRIDGES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        BridgeRegistry([BridgeEntry("x", "", "thing", "JSON", "open", "why")])


def test_entry_proprietary_format_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        BridgeRegistry([BridgeEntry("x", "X", "thing", "remote_mcp", "live", "why")])


def test_bridge_words_and_formats_differ_by_bridge():
    reg = default_registry()
    assert reg.get("github").item_word == "key"
    assert reg.get("gitlab").item_word == "key"
    assert reg.get("samverk").item_word == "ref"
    assert reg.get("samtal").item_word == "ref"
    assert reg.get("github").key_home == "kista:github"
    assert reg.get("gitlab").key_home == "kista:gitlab"
    assert reg.get("samverk").key_home == "kista:samverk"
    assert reg.get("samtal").key_home == "kista:samtal"


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
    standing = derive_standing(fresh_record(stages=("listed", "scoped")))
    assert not standing.held and standing.stage == "scoped"


def test_walk_must_open_at_listed():
    standing = derive_standing(
        fresh_record(stages=("scoped", "checked", "held")))
    assert not standing.held
    assert any("open at listed" in g for g in standing.gaps)


def test_walk_rejects_skipped_stage():
    standing = derive_standing(
        fresh_record(stages=("listed", "checked", "held")))
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


def test_record_unknown_bridge_and_missing_fields_refused():
    with pytest.raises(ValidationError, match="unknown bridge"):
        derive_standing(fresh_record(bridge="guess"))
    with pytest.raises(ValidationError, match="no record"):
        fresh_record(record=" ").validate()
    with pytest.raises(ValidationError, match="no observed time"):
        fresh_record(observed_at="").validate()


def test_record_scope_words_must_be_known():
    with pytest.raises(ValidationError, match="unknown audit record scope"):
        fresh_record(scope="green").validate()
    for scope in AUDIT_SCOPES:
        fresh_record(scope=scope).validate()


def test_record_claim_bridge_and_age_must_be_known():
    with pytest.raises(ValidationError, match="unknown audit evidence kind"):
        fresh_record(claims=("vibes",)).validate()
    for bridge in HELD_EVIDENCE + BARE_CLAIMS:
        fresh_record(claims=(bridge,)).validate()
    with pytest.raises(ValidationError, match="non-negative"):
        fresh_record(age_seconds=-1).validate()


def test_report_defaults_to_ready_state():
    report = prepare_report("mythic-coder", "github", "audit-42",
                          "audit the bridge permissions")
    assert report.state == "ready" and report.granted is False


def test_report_locked_or_gated_state_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("b", "github", "export-1", "x", state="locked")
    shared = prepare_report("b", "github", "export-1", "x", state="shared")
    assert shared.state == "shared" and shared.granted is False


def test_report_never_granted_and_format_lines():
    with pytest.raises(ValidationError, match="never a grant"):
        AuditDraft("b", "github", "export-1", "x", granted=True).validate()
    with pytest.raises(ValidationError, match="no bridge"):
        prepare_report(" ", "github", "export-1", "x")
    with pytest.raises(ValidationError, match="no record"):
        prepare_report("b", "github", " ", "x")
    with pytest.raises(ValidationError, match="reports nothing"):
        prepare_report("b", "github", "export-1", " ")
    reg = default_registry()
    assert "GitHub Bridge" in format_bridge(reg.get("github"))
    assert "audit standing listed" in format_bridge(reg.get("samtal"))
    assert format_bridges(reg).count("\n") == 3
    line = format_record(fresh_record())
    assert "held as audited" in line and "audit-42" in line
    open_line = format_record(fresh_record(claims=()))
    assert "open:" in open_line


# ---------------------------------------------------------------------
# M-253 agent layer: the agent holds the shipped bridge
# registry and one audit record per bridge and record for
# the session, records, viewed standings and reportd
# reports are published as session news through the
# checkpoint road (journal-first, deduped per record,
# standing and report), standings, the index and the
# verdict are derived at call time from the held records -
# an record is a fact only when it rests on held evidence -
# bridge reports are reportd only as reports, state
# ready by default, may be marked shared by a human,
# and never a grant or built, and the registry is session
# state, never a stored setting. This layer opens no
# export listener, calls no host API, probes no network
# and exports nothing here.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    BRIDGEAUDIT_USAGE,
    parse_bridgeaudit_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.bridge_permissions import (
    PLAIN_EXPLANATION,
    BRIDGE_PERMISSIONS_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_DM_EVENT_TYPES = (
    "bridgeaudit_record", "bridgeaudit_standing", "bridgeaudit_report")

ALL_BRIDGES = ["github", "gitlab", "samverk", "samtal"]


def _dm_records(store, session_id, bridge):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == bridge]


def _dm_record(**overrides):
    raw = {
        "bridge": "github",
        "record": "audit-42",
        "scope": "full",
        "title": "Fix the seam",
        "subject": "PR 42 in mythic-coder",
        "observed_at": "2026-11-12T12:00:00",
        "age_seconds": 60,
        "stages": list(STAGES),
        "claims": ["kista_ref"],
    }
    raw.update(overrides)
    return raw


def _fresh_for(bridge, record="audit-42"):
    return _dm_record(bridge=bridge, record=record)


class TestBridgePermissionsAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_bridges(
            self, agent):
        status = agent.bridgeaudit_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["bridgeaudit_book"]["schema"] == (
            BRIDGE_PERMISSIONS_SCHEMA)
        assert [p["id"] for p in status[
            "bridgeaudit_book"]["bridges"]] == ALL_BRIDGES
        assert status["bridgeaudit_book"]["records"] == []
        assert status["bridgeaudit_book"]["reports"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "GitHub Bridge" in status["bridges_text"]
        assert "audit standing listed" in status["bridges_text"]
        assert "none recorded this session" in status["screen"]
        assert "One screen" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == BRIDGEAUDIT_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._bridgeaudit_registry()
        assert agent._bridgeaudit_registry() is first
        assert agent._bridgeaudit_store is first
        for name in ("bridgeaudit_bridges",
                     "bridgeaudit_book",
                     "bridgeaudit_status",
                     "get_bridgeaudit_bridge",
                     "get_bridgeaudit_record",
                     "bridgeaudit_standing",
                     "audits_for_scope",
                     "bridgeaudit_held",
                     "bridgeaudit_index",
                     "bridgeaudit_verdict",
                     "prepare_bridgeaudit_report",
                     "get_bridgeaudit_report",
                     "bridgeaudit_reports",
                     "report_bridgeaudit"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_bridgeaudit_registry", "bridgeaudit_bridges",
            "bridgeaudit_book", "bridgeaudit_status",
            "get_bridgeaudit_bridge",
            "get_bridgeaudit_record",
            "bridgeaudit_standing", "audits_for_scope",
            "bridgeaudit_held", "bridgeaudit_index",
            "bridgeaudit_verdict",
            "register_bridgeaudit_record",
            "register_bridgeaudit_records",
            "record_bridgeaudit_records",
            "view_bridgeaudit", "prepare_bridgeaudit_report",
            "report_bridgeaudit",
            "_publish_bridgeaudit_record",
            "_bridgeaudit_screen",
            "_bridgeaudit_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.bridgeaudit_status()
        entry = agent.get_bridgeaudit_bridge("samtal")
        assert entry.item_word == "ref"
        standing = agent.bridgeaudit_standing(
            "github", "audit-42")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.freshness == "stale"
        assert agent.bridgeaudit_held() == []
        assert agent.audits_for_scope("full") == []
        agent.bridgeaudit_index()
        agent.bridgeaudit_verdict()
        agent.report_bridgeaudit()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _DM_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown bridge"):
            agent.get_bridgeaudit_bridge("guess")
        with pytest.raises(ValueError, match="unknown bridge"):
            agent.bridgeaudit_standing("guess", "audit-42")
        with pytest.raises(ValueError, match="holds no audit record"):
            agent.get_bridgeaudit_record("github", "audit-42")
        with pytest.raises(ValueError):
            agent.audits_for_scope("")
        with pytest.raises(ValueError, match="unknown audit record scope"):
            agent.audits_for_scope("green")
        agent.close()


class TestBridgePermissionsAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_bridgeaudit_record(_dm_record())
        assert result["record"]["bridge"] == "github"
        assert result["record"]["record"] == "audit-42"
        assert result["record_news"]["type"] == (
            "bridgeaudit_record")
        assert "held as audited" in result["screen"]
        status = agent.bridgeaudit_status()
        assert [r["bridge"] for r in status["records"]] == [
            "github"]
        assert status["book"]["records"][0]["record"] == (
            "audit-42")
        assert status["held"] == ["github/audit-42"]
        assert status["open"] == []
        assert "held as audited" in status["records_text"]
        assert len(_dm_records(
            store, session_id, "bridgeaudit_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_bridgeaudit_record(_dm_record())
        with pytest.raises(ValueError, match="github"):
            agent.register_bridgeaudit_record(
                _dm_record(title="A second telling"))
        assert len(_dm_records(
            store, session_id, "bridgeaudit_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_bridgeaudit_record(
                _dm_record(claims=["vibes"]))
        assert agent.bridgeaudit_status()["records"] == []
        assert _dm_records(
            store, session_id, "bridgeaudit_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_bridgeaudit_records([
            _fresh_for("samtal"), _dm_record()])
        assert result["count"] == 2
        assert [r["bridge"] for r in result["records_news"]] == [
            "samtal", "github"]
        assert len(_dm_records(
            store, session_id, "bridgeaudit_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_bridgeaudit_records(
            [_fresh_for("gitlab")])
        assert result["count"] == 1
        assert result["book"]["schema"] == BRIDGE_PERMISSIONS_SCHEMA
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_bridgeaudit_records(
                [_fresh_for("gitlab")])
        assert len(_dm_records(
            store, session_id, "bridgeaudit_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_bridgeaudit_record(_dm_record())
        result = agent.view_bridgeaudit("github", "audit-42")
        assert result["bridge"]["id"] == "github"
        assert result["standing"]["held"] is True
        assert result["record"]["record"] == "audit-42"
        assert result["record_news"]["type"] == (
            "bridgeaudit_standing")
        assert result["held_record_news"]["type"] == (
            "bridgeaudit_record")
        assert len(_dm_records(
            store, session_id, "bridgeaudit_record")) == 1
        assert len(_dm_records(
            store, session_id, "bridgeaudit_standing")) == 1
        result = agent.view_bridgeaudit("samtal", "audit-42")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_dm_records(
            store, session_id, "bridgeaudit_standing")) == 2
        agent.close()


class TestBridgePermissionsReports:
    def test_prepare_report_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_bridgeaudit_report(
            "mythic-coder", "github", "audit-42", "list the GitHub bridge permissions")
        assert result["report"]["state"] == (
            "ready")
        assert result["report"]["granted"] is False
        assert result["report_news"]["type"] == (
            "bridgeaudit_report")
        assert "list the GitHub bridge permissions" in result["screen"]
        report = agent.get_bridgeaudit_report(
            "mythic-coder")
        assert report.entry == "github"
        assert [d.bridge for d in agent.bridgeaudit_reports()] == [
            "mythic-coder"]
        assert len(_dm_records(
            store, session_id, "bridgeaudit_report")) == 1
        agent.close()

    def test_report_unshared_execution_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared only"):
            agent.prepare_bridgeaudit_report(
                "mythic-coder", "github", "audit-42", "x",
                state="executed")
        assert agent.bridgeaudit_reports() == []
        assert _dm_records(
            store, session_id, "bridgeaudit_report") == []
        agent.close()

    def test_duplicate_report_refuses(self, agent):
        agent.prepare_bridgeaudit_report(
            "mythic-coder", "github", "audit-42", "list the GitHub bridge permissions")
        with pytest.raises(ValueError, match="mythic-coder"):
            agent.prepare_bridgeaudit_report(
                "mythic-coder", "gitlab", "issue-7", "a second telling")
        with pytest.raises(ValueError,
                           match="holds no bridge report"):
            agent.get_bridgeaudit_report("samverk")


class TestBridgePermissionsParseArgs:
    def test_parse_args_well(self):
        assert parse_bridgeaudit_args("") == (
            "show", None, (), None)
        assert parse_bridgeaudit_args(None) == (
            "show", None, (), None)
        assert parse_bridgeaudit_args("bridges") == (
            "bridges", None, (), None)
        assert parse_bridgeaudit_args("bridge samtal") == (
            "bridge", "samtal", (), None)
        assert parse_bridgeaudit_args(
            "record github audit-42") == (
            "record", ("github", "audit-42"), (), None)
        assert parse_bridgeaudit_args(
            "standing gitlab issue-7") == (
            "standing", ("gitlab", "issue-7"), (), None)
        assert parse_bridgeaudit_args("report") == (
            "reports", None, (), None)
        assert parse_bridgeaudit_args(
            "report mythic-coder") == (
            "report", "mythic-coder", (), None)
        assert parse_bridgeaudit_args("verdict") == (
            "verdict", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "bridge", "record",
                    "record sessions",
                    "bridges now", "standing campaigns",
                    "report mythic-coder extra"):
            with pytest.raises(ValueError) as caught:
                parse_bridgeaudit_args(bad)
            assert str(caught.value) == BRIDGEAUDIT_USAGE


class TestBridgePermissionsTerminalRoad:
    def test_show_bridges_bridge_record_standing_report_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/bridgeaudit")
        assert "GitHub Bridge (github)" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/bridgeaudit bridges")
        assert "GitLab Bridge" in text
        _, _, text = _slash(agent, "/bridgeaudit bridge samtal")
        assert "kista:samtal" in text
        _, _, text = _slash(
            agent, "/bridgeaudit record github audit-42")
        assert "holds no audit record" in text
        _, _, text = _slash(
            agent, "/bridgeaudit standing github audit-42")
        assert "github/audit-42: audit open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/bridgeaudit report")
        assert "Bridge report: none held" in text
        _, _, text = _slash(agent, "/bridgeaudit verdict")
        assert "Bridge permissions audit stands open" in text
        agent.register_bridgeaudit_record(_dm_record())
        _, _, text = _slash(
            agent, "/bridgeaudit record github audit-42")
        assert "held as audited" in text
        _, _, text = _slash(
            agent, "/bridgeaudit standing github audit-42")
        assert "github/audit-42: audit held as audited" in text
        _, _, text = _slash(agent, "/bridgeaudit index")
        assert "held as audited" in text
        agent.prepare_bridgeaudit_report(
            "mythic-coder", "github", "audit-42", "list the GitHub bridge permissions")
        _, _, text = _slash(
            agent, "/bridgeaudit report mythic-coder")
        assert "list the GitHub bridge permissions" in text
        assert "never a grant" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/bridgeaudit [show|bridges|bridge <bridge>|"
                "record <bridge> <record>|"
                "standing <bridge> <record>|"
                "report [<bridge>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/bridgeaudit dance party")
        assert text == BRIDGEAUDIT_USAGE
        _, _, text = _slash(agent, "/bridgeaudit bridge guess")
        assert "unknown bridge" in text


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


class TestBridgePermissionsHandler:
    def test_show_is_default(self, dm_handler, agent):
        dm_handler._handle_bridgeaudit("")
        assert "GitHub Bridge (github)" in (
            _dm_published_text(dm_handler))

    def test_bridge_record_and_verdict(
            self, dm_handler, agent):
        dm_handler._handle_bridgeaudit("bridge samtal")
        assert "kista:samtal" in (
            _dm_published_text(dm_handler))
        agent.register_bridgeaudit_record(_dm_record())
        dm_handler._handle_bridgeaudit(
            "record github audit-42")
        assert "held as audited" in (
            _dm_published_text(dm_handler))
        dm_handler._handle_bridgeaudit("verdict")
        assert "Bridge permissions audit stands held" in (
            _dm_published_text(dm_handler))

    def test_bad_grammar_is_published(
            self, dm_handler, agent):
        dm_handler._handle_bridgeaudit("dance party")
        assert BRIDGEAUDIT_USAGE in (
            _dm_published_text(dm_handler))
        dm_handler._handle_bridgeaudit("bridge guess")
        assert "unknown bridge" in (
            _dm_published_text(dm_handler))


class TestChatScreenRoutingBridgePermissions:
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
        screen.handle_command("/bridgeaudit verdict", _FakeLog())
        assert calls == [("/bridgeaudit", "verdict")]

    def test_chat_screen_help_and_usage_name_the_doors(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/bridgeaudit[/green] - show the Bridge permissions audit "
                "(M-253)") in text
        assert ('"/bridgeaudit": "Usage: /bridgeaudit | '
                "/bridgeaudit bridges") in text


class TestBridgePermissionsDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.bridgeaudit_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _DM_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        verdict = agent.bridgeaudit_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_bridgeaudit_record(_dm_record())
        agent.register_bridgeaudit_record(_fresh_for("gitlab"))
        verdict = agent.bridgeaudit_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "github/audit-42", "gitlab/audit-42"]
        assert "Bridge permissions audit stands held" in verdict["verdict_text"]

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_bridgeaudit()
        assert report["book"]["schema"] == BRIDGE_PERMISSIONS_SCHEMA
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_bridgeaudit_record(_dm_record())
        report = agent.report_bridgeaudit()
        assert "held as audited" in report["records_text"]
        assert [s["bridge"] for s in report["standings"]] == [
            "github"]

    def test_audits_for_scope_and_held_keys(self, agent):
        agent.register_bridgeaudit_record(_dm_record())
        agent.register_bridgeaudit_record(_dm_record(
            record="issue-9", scope="propose_only",
            stages=["listed"], claims=["assertion"]))
        assert [r.record for r in
                agent.audits_for_scope("full")] == [
            "audit-42"]
        assert [r.record for r in
                agent.audits_for_scope("propose_only")] == [
            "issue-9"]
        assert agent.bridgeaudit_held() == ["github/audit-42"]
        standing = agent.bridgeaudit_standing(
            "github", "issue-9")
        assert standing.held is False
        assert any("bare claims" in gap
                   for gap in standing.gaps)
