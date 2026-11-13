"""M-251 Export everything - pure-layer tests.

TIER: unit

Sessions, campaigns, memories and configs leave only as a
recorded record in an open format; an absent record reads
as unknown and a stale one as stale, never as a fact,
and this book only prepares export drafts - leaving is
as easy as arriving.
"""
import pytest

from mythic_agent.core.export_everything import (
    BARE_CLAIMS,
    RECORD_SCOPES,
    FRESH_LIMIT_SECONDS,
    HELD_EVIDENCE,
    KINDS,
    STAGES,
    ExportDraft,
    ExportRecord,
    KindEntry,
    KindRegistry,
    default_registry,
    derive_standing,
    format_kind,
    format_kinds,
    format_record,
    prepare_draft,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(kind="sessions", record="export-42",
                scope="full", title="Leave with everything",
                subject="Session 42 in mythic-coder",
                observed_at="2026-11-12T12:00:00", age_seconds=60,
                stages=STAGES, claims=("content_ref",))
    base.update(kw)
    return ExportRecord(**base)


def test_registry_holds_four_kinds_open_only():
    reg = default_registry()
    assert reg.ids() == ("sessions", "campaigns",
                         "memories", "configs")
    assert all(e.openness == "open" for e in reg.entries())


def test_registry_unknown_kind_refused_by_name():
    with pytest.raises(ValidationError, match="unknown export kind: guess"):
        default_registry().get("guess")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate export kind"):
        KindRegistry(KINDS + KINDS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        KindRegistry([KindEntry("x", "", "thing", "JSON", "open", "why")])


def test_entry_proprietary_format_refused():
    with pytest.raises(ValidationError, match="open formats only"):
        KindRegistry([KindEntry("x", "X", "thing", "LockedBin", "locked", "why")])


def test_kind_words_and_formats_differ_by_kind():
    reg = default_registry()
    assert reg.get("sessions").item_word == "session"
    assert reg.get("campaigns").item_word == "campaign"
    assert reg.get("memories").item_word == "memory"
    assert reg.get("configs").item_word == "config"
    assert reg.get("sessions").format_name == "JSON"
    assert reg.get("campaigns").format_name == "Markdown"
    assert reg.get("memories").format_name == "Markdown"
    assert reg.get("configs").format_name == "YAML"


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
    standing = derive_standing(fresh_record(stages=("listed", "gathered")))
    assert not standing.held and standing.stage == "gathered"


def test_walk_must_open_at_listed():
    standing = derive_standing(
        fresh_record(stages=("gathered", "checked", "held")))
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


def test_record_unknown_kind_and_missing_fields_refused():
    with pytest.raises(ValidationError, match="unknown export kind"):
        derive_standing(fresh_record(kind="guess"))
    with pytest.raises(ValidationError, match="no record"):
        fresh_record(record=" ").validate()
    with pytest.raises(ValidationError, match="no observed time"):
        fresh_record(observed_at="").validate()


def test_record_scope_words_must_be_known():
    with pytest.raises(ValidationError, match="unknown export record scope"):
        fresh_record(scope="green").validate()
    for scope in RECORD_SCOPES:
        fresh_record(scope=scope).validate()


def test_record_claim_kind_and_age_must_be_known():
    with pytest.raises(ValidationError, match="unknown export evidence kind"):
        fresh_record(claims=("vibes",)).validate()
    for kind in HELD_EVIDENCE + BARE_CLAIMS:
        fresh_record(claims=(kind,)).validate()
    with pytest.raises(ValidationError, match="non-negative"):
        fresh_record(age_seconds=-1).validate()


def test_draft_defaults_to_ready_state():
    draft = prepare_draft("mythic-coder", "sessions", "export-42",
                          "export the session")
    assert draft.state == "ready" and draft.exported is False


def test_draft_locked_or_gated_state_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_draft("b", "sessions", "export-1", "x", state="locked")
    shared = prepare_draft("b", "sessions", "export-1", "x", state="shared")
    assert shared.state == "shared" and shared.exported is False


def test_draft_never_exported_and_format_lines():
    with pytest.raises(ValidationError, match="never exported"):
        ExportDraft("b", "sessions", "export-1", "x", exported=True).validate()
    with pytest.raises(ValidationError, match="no bundle"):
        prepare_draft(" ", "sessions", "export-1", "x")
    with pytest.raises(ValidationError, match="no record"):
        prepare_draft("b", "sessions", " ", "x")
    with pytest.raises(ValidationError, match="drafts nothing"):
        prepare_draft("b", "sessions", "export-1", " ")
    reg = default_registry()
    assert "Sessions" in format_kind(reg.get("sessions"))
    assert "via open" in format_kind(reg.get("configs"))
    assert format_kinds(reg).count("\n") == 3
    line = format_record(fresh_record())
    assert "held as open" in line and "export-42" in line
    open_line = format_record(fresh_record(claims=()))
    assert "open:" in open_line


# ---------------------------------------------------------------------
# M-251 agent layer: the agent holds the shipped kind
# registry and one export record per kind and record for
# the session, records, viewed standings and prepared
# drafts are published as session news through the
# checkpoint road (journal-first, deduped per record,
# standing and draft), standings, the index and the
# verdict are derived at call time from the held records -
# an record is a fact only when it rests on held evidence -
# bundle drafts are prepared only as drafts, state
# ready by default, may be marked shared by a human,
# and never exported or built, and the registry is session
# state, never a stored setting. This layer opens no
# export listener, calls no host API, probes no network
# and exports nothing here.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    EXPORTEVERYTHING_USAGE,
    parse_exporteverything_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.export_everything import (
    PLAIN_EXPLANATION,
    EXPORT_EVERYTHING_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_EE_EVENT_TYPES = (
    "exporteverything_record", "exporteverything_standing", "exporteverything_draft")

ALL_KINDS = ["sessions", "campaigns", "memories", "configs"]


def _ee_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _ee_record(**overrides):
    raw = {
        "kind": "sessions",
        "record": "export-42",
        "scope": "full",
        "title": "Fix the seam",
        "subject": "PR 42 in mythic-coder",
        "observed_at": "2026-11-12T12:00:00",
        "age_seconds": 60,
        "stages": list(STAGES),
        "claims": ["content_ref"],
    }
    raw.update(overrides)
    return raw


def _fresh_for(kind, record="export-42"):
    return _ee_record(kind=kind, record=record)


class TestExportEverythingAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_kinds(
            self, agent):
        status = agent.exporteverything_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["exporteverything_book"]["schema"] == (
            EXPORT_EVERYTHING_SCHEMA)
        assert [p["id"] for p in status[
            "exporteverything_book"]["kinds"]] == ALL_KINDS
        assert status["exporteverything_book"]["records"] == []
        assert status["exporteverything_book"]["drafts"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "Sessions" in status["kinds_text"]
        assert "via open" in status["kinds_text"]
        assert "none recorded this session" in status["screen"]
        assert "leaving is as easy as arriving" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == EXPORTEVERYTHING_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._exporteverything_registry()
        assert agent._exporteverything_registry() is first
        assert agent._exporteverything_store is first
        for name in ("exporteverything_kinds",
                     "exporteverything_book",
                     "exporteverything_status",
                     "get_exporteverything_kind",
                     "get_exporteverything_record",
                     "exporteverything_standing",
                     "records_for_scope",
                     "exporteverything_held",
                     "exporteverything_index",
                     "exporteverything_verdict",
                     "prepare_exporteverything_draft",
                     "get_exporteverything_draft",
                     "exporteverything_drafts",
                     "report_exporteverything"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_exporteverything_registry", "exporteverything_kinds",
            "exporteverything_book", "exporteverything_status",
            "get_exporteverything_kind",
            "get_exporteverything_record",
            "exporteverything_standing", "records_for_scope",
            "exporteverything_held", "exporteverything_index",
            "exporteverything_verdict",
            "register_exporteverything_record",
            "register_exporteverything_records",
            "record_exporteverything_records",
            "view_exporteverything", "prepare_exporteverything_draft",
            "report_exporteverything",
            "_publish_exporteverything_record",
            "_exporteverything_screen",
            "_exporteverything_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.exporteverything_status()
        entry = agent.get_exporteverything_kind("configs")
        assert entry.item_word == "config"
        standing = agent.exporteverything_standing(
            "sessions", "export-42")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.freshness == "stale"
        assert agent.exporteverything_held() == []
        assert agent.records_for_scope("full") == []
        agent.exporteverything_index()
        agent.exporteverything_verdict()
        agent.report_exporteverything()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _EE_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown export kind"):
            agent.get_exporteverything_kind("guess")
        with pytest.raises(ValueError, match="unknown export kind"):
            agent.exporteverything_standing("guess", "export-42")
        with pytest.raises(ValueError, match="holds no export record"):
            agent.get_exporteverything_record("sessions", "export-42")
        with pytest.raises(ValueError):
            agent.records_for_scope("")
        with pytest.raises(ValueError, match="unknown export record scope"):
            agent.records_for_scope("green")
        agent.close()


class TestExportEverythingAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_exporteverything_record(_ee_record())
        assert result["record"]["kind"] == "sessions"
        assert result["record"]["record"] == "export-42"
        assert result["record_news"]["type"] == (
            "exporteverything_record")
        assert "held as open" in result["screen"]
        status = agent.exporteverything_status()
        assert [r["kind"] for r in status["records"]] == [
            "sessions"]
        assert status["book"]["records"][0]["record"] == (
            "export-42")
        assert status["held"] == ["sessions/export-42"]
        assert status["open"] == []
        assert "held as open" in status["records_text"]
        assert len(_ee_records(
            store, session_id, "exporteverything_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_exporteverything_record(_ee_record())
        with pytest.raises(ValueError, match="sessions"):
            agent.register_exporteverything_record(
                _ee_record(title="A second telling"))
        assert len(_ee_records(
            store, session_id, "exporteverything_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_exporteverything_record(
                _ee_record(claims=["vibes"]))
        assert agent.exporteverything_status()["records"] == []
        assert _ee_records(
            store, session_id, "exporteverything_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_exporteverything_records([
            _fresh_for("configs"), _ee_record()])
        assert result["count"] == 2
        assert [r["kind"] for r in result["records_news"]] == [
            "configs", "sessions"]
        assert len(_ee_records(
            store, session_id, "exporteverything_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_exporteverything_records(
            [_fresh_for("campaigns")])
        assert result["count"] == 1
        assert result["book"]["schema"] == EXPORT_EVERYTHING_SCHEMA
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_exporteverything_records(
                [_fresh_for("campaigns")])
        assert len(_ee_records(
            store, session_id, "exporteverything_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_exporteverything_record(_ee_record())
        result = agent.view_exporteverything("sessions", "export-42")
        assert result["kind"]["id"] == "sessions"
        assert result["standing"]["held"] is True
        assert result["record"]["record"] == "export-42"
        assert result["record_news"]["type"] == (
            "exporteverything_standing")
        assert result["held_record_news"]["type"] == (
            "exporteverything_record")
        assert len(_ee_records(
            store, session_id, "exporteverything_record")) == 1
        assert len(_ee_records(
            store, session_id, "exporteverything_standing")) == 1
        result = agent.view_exporteverything("configs", "export-42")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_ee_records(
            store, session_id, "exporteverything_standing")) == 2
        agent.close()


class TestExportEverythingDrafts:
    def test_prepare_draft_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_exporteverything_draft(
            "mythic-coder", "sessions", "export-42", "build the seam fix")
        assert result["draft"]["state"] == (
            "ready")
        assert result["draft"]["exported"] is False
        assert result["draft_news"]["type"] == (
            "exporteverything_draft")
        assert "build the seam fix" in result["screen"]
        draft = agent.get_exporteverything_draft(
            "mythic-coder")
        assert draft.kind == "sessions"
        assert [d.bundle for d in agent.exporteverything_drafts()] == [
            "mythic-coder"]
        assert len(_ee_records(
            store, session_id, "exporteverything_draft")) == 1
        agent.close()

    def test_draft_unshared_execution_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared only"):
            agent.prepare_exporteverything_draft(
                "mythic-coder", "sessions", "export-42", "x",
                state="executed")
        assert agent.exporteverything_drafts() == []
        assert _ee_records(
            store, session_id, "exporteverything_draft") == []
        agent.close()

    def test_duplicate_draft_refuses(self, agent):
        agent.prepare_exporteverything_draft(
            "mythic-coder", "sessions", "export-42", "build the seam fix")
        with pytest.raises(ValueError, match="mythic-coder"):
            agent.prepare_exporteverything_draft(
                "mythic-coder", "campaigns", "issue-7", "a second telling")
        with pytest.raises(ValueError,
                           match="holds no bundle draft"):
            agent.get_exporteverything_draft("samverk")


class TestExportEverythingParseArgs:
    def test_parse_args_well(self):
        assert parse_exporteverything_args("") == (
            "show", None, (), None)
        assert parse_exporteverything_args(None) == (
            "show", None, (), None)
        assert parse_exporteverything_args("kinds") == (
            "kinds", None, (), None)
        assert parse_exporteverything_args("kind configs") == (
            "kind", "configs", (), None)
        assert parse_exporteverything_args(
            "record sessions export-42") == (
            "record", ("sessions", "export-42"), (), None)
        assert parse_exporteverything_args(
            "standing campaigns issue-7") == (
            "standing", ("campaigns", "issue-7"), (), None)
        assert parse_exporteverything_args("prepare") == (
            "drafts", None, (), None)
        assert parse_exporteverything_args(
            "prepare mythic-coder") == (
            "prepare", "mythic-coder", (), None)
        assert parse_exporteverything_args("verdict") == (
            "verdict", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "kind", "record",
                    "record sessions",
                    "kinds now", "standing campaigns",
                    "prepare mythic-coder extra"):
            with pytest.raises(ValueError) as caught:
                parse_exporteverything_args(bad)
            assert str(caught.value) == EXPORTEVERYTHING_USAGE


class TestExportEverythingTerminalRoad:
    def test_show_kinds_kind_record_standing_prepare_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/exporteverything")
        assert "Sessions (sessions)" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/exporteverything kinds")
        assert "Campaigns" in text
        _, _, text = _slash(agent, "/exporteverything kind configs")
        assert "YAML" in text
        _, _, text = _slash(
            agent, "/exporteverything record sessions export-42")
        assert "holds no export record" in text
        _, _, text = _slash(
            agent, "/exporteverything standing sessions export-42")
        assert "sessions/export-42: export open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/exporteverything prepare")
        assert "Bundle draft: none held" in text
        _, _, text = _slash(agent, "/exporteverything verdict")
        assert "Export everything stands open" in text
        agent.register_exporteverything_record(_ee_record())
        _, _, text = _slash(
            agent, "/exporteverything record sessions export-42")
        assert "held as open" in text
        _, _, text = _slash(
            agent, "/exporteverything standing sessions export-42")
        assert "sessions/export-42: export held as open" in text
        _, _, text = _slash(agent, "/exporteverything index")
        assert "held as open" in text
        agent.prepare_exporteverything_draft(
            "mythic-coder", "sessions", "export-42", "build the seam fix")
        _, _, text = _slash(
            agent, "/exporteverything prepare mythic-coder")
        assert "build the seam fix" in text
        assert "never exported" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/exporteverything [show|kinds|kind <kind>|"
                "record <kind> <record>|"
                "standing <kind> <record>|"
                "prepare [<bundle>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/exporteverything dance party")
        assert text == EXPORTEVERYTHING_USAGE
        _, _, text = _slash(agent, "/exporteverything kind guess")
        assert "unknown export kind" in text


@pytest.fixture()
def ee_handler(agent, monkeypatch):
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


def _ee_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestExportEverythingHandler:
    def test_show_is_default(self, ee_handler, agent):
        ee_handler._handle_exporteverything("")
        assert "Sessions (sessions)" in (
            _ee_published_text(ee_handler))

    def test_kind_record_and_verdict(
            self, ee_handler, agent):
        ee_handler._handle_exporteverything("kind configs")
        assert "YAML" in (
            _ee_published_text(ee_handler))
        agent.register_exporteverything_record(_ee_record())
        ee_handler._handle_exporteverything(
            "record sessions export-42")
        assert "held as open" in (
            _ee_published_text(ee_handler))
        ee_handler._handle_exporteverything("verdict")
        assert "Export everything stands held" in (
            _ee_published_text(ee_handler))

    def test_bad_grammar_is_published(
            self, ee_handler, agent):
        ee_handler._handle_exporteverything("dance party")
        assert EXPORTEVERYTHING_USAGE in (
            _ee_published_text(ee_handler))
        ee_handler._handle_exporteverything("kind guess")
        assert "unknown export kind" in (
            _ee_published_text(ee_handler))


class TestChatScreenRoutingExportEverything:
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
        screen.handle_command("/exporteverything verdict", _FakeLog())
        assert calls == [("/exporteverything", "verdict")]

    def test_chat_screen_help_and_usage_name_the_doors(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/exporteverything[/green] - show the Export everything "
                "(M-251)") in text
        assert ('"/exporteverything": "Usage: /exporteverything | '
                "/exporteverything kinds") in text


class TestExportEverythingDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.exporteverything_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _EE_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        verdict = agent.exporteverything_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_exporteverything_record(_ee_record())
        agent.register_exporteverything_record(_fresh_for("campaigns"))
        verdict = agent.exporteverything_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "sessions/export-42", "campaigns/export-42"]
        assert "Export everything stands held" in verdict["verdict_text"]

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_exporteverything()
        assert report["book"]["schema"] == EXPORT_EVERYTHING_SCHEMA
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_exporteverything_record(_ee_record())
        report = agent.report_exporteverything()
        assert "held as open" in report["records_text"]
        assert [s["kind"] for s in report["standings"]] == [
            "sessions"]

    def test_records_for_scope_and_held_keys(self, agent):
        agent.register_exporteverything_record(_ee_record())
        agent.register_exporteverything_record(_ee_record(
            record="issue-9", scope="snapshot",
            stages=["listed"], claims=["assertion"]))
        assert [r.record for r in
                agent.records_for_scope("full")] == [
            "export-42"]
        assert [r.record for r in
                agent.records_for_scope("snapshot")] == [
            "issue-9"]
        assert agent.exporteverything_held() == ["sessions/export-42"]
        standing = agent.exporteverything_standing(
            "sessions", "issue-9")
        assert standing.held is False
        assert any("bare claims" in gap
                   for gap in standing.gaps)
