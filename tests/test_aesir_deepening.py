"""M-245 Aesir deepening — pure-layer tests.

TIER: unit

The pure layer holds Aesir's honest capability reports,
the per-role selection book, and the derived router ask
as data. A report may narrow Aesir's documented v1
ceiling, never widen it; a selection names a real crew
office or refuses by name; an ask is granted only what
the report grants, names the resident model only, and
is not shaped at all for an unselected office or an
unreachable server. No session is opened, no model is
called, and no server is probed in this layer.
"""

import pytest

from mythic_agent.core.aesir_deepening import (
    AESIR_SCHEMA,
    CAPABILITY_CEILING,
    NEEDS,
    AesirAsk,
    AesirCapabilityReport,
    SelectionBook,
    format_ask,
    format_report,
    format_selections,
    load_selection_book,
    load_selection_book_file,
    plain_words,
    selection_record,
    shape_ask,
    validate_report,
    validate_selection,
    validate_selection_book,
)
from mythic_agent.core.role_routing import office_ids
from mythic_agent.core.validation import ValidationError

LIVE_REPORT = {
    "streaming": True,
    "tool_calling": False,
    "vision": False,
    "json_mode": False,
    "embeddings": False,
    "resident_models": 1,
    "catalog_is_readiness": False,
    "reachable": True,
    "backend": "cpu",
    "profile": "default",
    "context": 8192,
    "model": "zen-4b",
    "model_digest": "sha256:abc",
}


def live_report(**overrides):
    raw = dict(LIVE_REPORT)
    raw.update(overrides)
    return validate_report(raw)


def test_ceiling_is_aesirs_documented_v1_shape():
    assert CAPABILITY_CEILING == {
        "streaming": True, "tool_calling": False,
        "vision": False, "json_mode": False,
        "embeddings": False, "resident_models": 1}


def test_report_holds_live_fields_whole():
    report = live_report()
    assert isinstance(report, AesirCapabilityReport)
    assert report.model == "zen-4b"
    assert report.context == 8192
    assert report.record()["backend"] == "cpu"


def test_report_missing_live_fields_stay_unknown():
    report = validate_report({"reachable": False})
    assert report.backend is None
    assert report.model is None
    assert report.streaming is True


def test_report_may_narrow_but_never_widen():
    narrowed = live_report(streaming=False)
    assert narrowed.streaming is False
    for key in ("tool_calling", "vision", "json_mode",
                "embeddings"):
        with pytest.raises(ValidationError, match=key):
            live_report(**{key: True})


def test_report_refuses_extra_resident_models():
    with pytest.raises(ValidationError,
                       match="resident_models"):
        live_report(resident_models=2)


def test_report_refuses_catalog_as_readiness():
    with pytest.raises(ValidationError,
                       match="catalog_is_readiness"):
        live_report(catalog_is_readiness=True)


def test_report_refuses_unknown_keys_and_bad_shapes():
    with pytest.raises(ValidationError, match="unknown"):
        live_report(surprise=True)
    with pytest.raises(ValidationError, match="streaming"):
        live_report(streaming="yes")
    with pytest.raises(ValidationError):
        validate_report(["not", "a", "mapping"])


def test_shipped_book_covers_every_office_once():
    book = load_selection_book()
    assert isinstance(book, SelectionBook)
    offices = [s.office for s in book.selections]
    assert sorted(offices) == sorted(office_ids())
    assert len(offices) == len(set(offices))


def test_shipped_book_tool_offices_not_selected():
    book = load_selection_book()
    for office in ("auditor", "forge_worker", "guardian"):
        assert book.for_office(office).selected is False
    for office in ("primary", "scribe", "skald"):
        assert book.for_office(office).selected is True


def test_selection_refuses_unknown_office_by_name():
    with pytest.raises(ValidationError, match="wizard"):
        validate_selection({
            "office": "wizard", "selected": True,
            "reason": "because", "capability": "none"})
    book = load_selection_book()
    with pytest.raises(ValidationError, match="wizard"):
        book.for_office("wizard")


def test_selection_refuses_half_written_records():
    with pytest.raises(ValidationError, match="reason"):
        validate_selection({
            "office": "scribe", "selected": True,
            "reason": "  ", "capability": "streaming"})
    with pytest.raises(ValidationError,
                       match="capability"):
        validate_selection({
            "office": "scribe", "selected": True,
            "reason": "words", "capability": "flight"})


def test_book_refuses_wrong_schema_and_duplicates():
    with pytest.raises(ValidationError, match="schema"):
        validate_selection_book({"schema": "other/9",
                                 "selections": []})
    row = {"office": "scribe", "selected": True,
           "reason": "words", "capability": "streaming"}
    with pytest.raises(ValidationError, match="duplicate"):
        validate_selection_book({
            "schema": AESIR_SCHEMA,
            "selections": [row, dict(row)]})


def test_book_loads_from_any_file(tmp_path):
    path = tmp_path / "book.yaml"
    path.write_text(
        "schema: mythic.aesir_deepening/1\n"
        "selections:\n"
        "- office: scribe\n  selected: true\n"
        "  capability: streaming\n  reason: words\n",
        encoding="utf-8")
    book = load_selection_book_file(path)
    assert book.for_office("scribe").selected is True


def test_selection_record_is_plain_data():
    book = load_selection_book()
    record = selection_record(book, "scribe")
    assert record["office"] == "scribe"
    assert record["selected"] is True


def test_ask_grants_only_what_the_report_grants():
    book = load_selection_book()
    ask = shape_ask(book, live_report(), "scribe",
                    needs=("streaming", "tool_calling"))
    assert isinstance(ask, AesirAsk)
    assert ask.shaped is True
    assert ask.road == "aesir"
    assert ask.granted == ("streaming",)
    assert ask.refused == ("tool_calling",)
    assert ask.model == "zen-4b"


def test_ask_reshapes_json_mode_to_boolean_subset():
    book = load_selection_book()
    ask = shape_ask(book, live_report(), "skald",
                    needs=("json_mode",))
    assert "json_mode" in ask.refused
    assert "structured_boolean" in ask.granted


def test_ask_names_only_the_resident_model():
    book = load_selection_book()
    ask = shape_ask(book, live_report(), "scribe",
                    model="some-other-model")
    assert ask.model is None
    assert "model:some-other-model" in ask.refused
    ask = shape_ask(book, live_report(), "scribe",
                    model="zen-4b")
    assert ask.model == "zen-4b"


def test_ask_not_shaped_for_unselected_office():
    book = load_selection_book()
    ask = shape_ask(book, live_report(), "auditor",
                    needs=("streaming",))
    assert ask.shaped is False
    assert ask.road == "session_default"
    assert ask.granted == ()


def test_ask_not_shaped_when_aesir_is_silent():
    book = load_selection_book()
    report = validate_report({"reachable": False})
    ask = shape_ask(book, report, "scribe",
                    needs=("streaming",))
    assert ask.shaped is False
    assert ask.road == "session_default"


def test_ask_refuses_unknown_needs_by_name():
    book = load_selection_book()
    with pytest.raises(ValidationError, match="flight"):
        shape_ask(book, live_report(), "scribe",
                  needs=("flight",))
    assert "flight" not in NEEDS


def test_formatters_speak_plainly():
    book = load_selection_book()
    report = live_report()
    assert "zen-4b" in format_report(report)
    assert "scribe" in format_selections(book)
    ask = shape_ask(book, report, "scribe",
                    needs=("streaming",))
    assert "scribe" in format_ask(ask)
    assert "Aesir" in plain_words()
# ---------------------------------------------------------------------
# M-245 agent layer: the agent holds a capability
# report and per-office selections for the session,
# reports and selections are published as session
# news through the checkpoint road (journal-first,
# deduped per office and per telling), asks are
# derived at call time from the held report and the
# book - never shaped for an unselected office or a
# silent server - and the index and verdict are
# derived at call time, never held. This layer opens
# no session, calls no model, probes no server and
# rewrites no route.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    AESIRDEEPENING_USAGE,
    parse_aesirdeepening_args,
)
from mythic_agent.core.aesir_deepening import (
    AESIR_SCHEMA,
    PLAIN_EXPLANATION,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore

ROOT = _Path(__file__).resolve().parent.parent

_AESIR_EVENT_TYPES = (
    "aesirdeepening_report", "aesirdeepening_selection",
    "aesirdeepening_ask")

SELECTED_OFFICES = [
    "primary", "polymath", "architect", "cartographer",
    "scribe", "skald"]
UNSELECTED_OFFICES = ["auditor", "forge_worker", "guardian"]


def _aesir_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _selection(**overrides):
    row = {"office": "scribe", "selected": True,
           "reason": "Words for the test hall.",
           "capability": "streaming"}
    row.update(overrides)
    return row


class TestAesirAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_book(
            self, agent):
        status = agent.aesirdeepening_status()
        assert status["report"] is None
        assert status["selections"] == []
        assert status["book"] is None
        assert status["aesirdeepening_book"]["schema"] == (
            AESIR_SCHEMA)
        assert len(status["aesirdeepening_book"][
            "selections"]) == 9
        assert status["selected"] == SELECTED_OFFICES
        assert status["not_selected"] == UNSELECTED_OFFICES
        assert status["index"]["gaps"] == UNSELECTED_OFFICES
        assert status["index"]["total"] == 9
        assert status["verdict"]["verdict"] == "silent"
        assert status["verdict"]["reachable"] is False
        assert "unknown" in status["report_text"]
        assert "scribe" in status["selections_text"]
        assert "silent" in status["screen"]
        assert "Aesir" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == AESIRDEEPENING_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._aesirdeepening_registry()
        assert agent._aesirdeepening_registry() is first
        assert agent._aesirdeepening_store is first
        for name in ("aesirdeepening_book",
                     "aesirdeepening_status",
                     "aesirdeepening_report",
                     "aesirdeepening_ask",
                     "aesirdeepening_index",
                     "aesirdeepening_verdict",
                     "aesirdeepening_selected",
                     "report_aesirdeepening"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_aesirdeepening_registry", "aesirdeepening_book",
            "aesirdeepening_status", "aesirdeepening_report",
            "get_aesirdeepening_selection",
            "selections_for_capability",
            "aesirdeepening_selected", "aesirdeepening_ask",
            "aesirdeepening_index", "aesirdeepening_verdict",
            "register_aesirdeepening_report",
            "register_aesirdeepening_selection",
            "register_aesirdeepening_book",
            "record_aesirdeepening_book",
            "view_aesirdeepening", "report_aesirdeepening",
            "_publish_aesirdeepening_record",
            "_aesirdeepening_screen",
            "_aesirdeepening_effective_report"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.aesirdeepening_status()
        selection = agent.get_aesirdeepening_selection("scribe")
        assert selection.selected is True
        assert [s.office for s in agent.aesirdeepening_selected()] == (
            SELECTED_OFFICES)
        assert [s.office for s in agent.selections_for_capability(
            "streaming")] == [
            "primary", "polymath", "architect", "cartographer",
            "scribe"]
        agent.aesirdeepening_index()
        agent.aesirdeepening_verdict()
        agent.report_aesirdeepening()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _AESIR_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="wizard"):
            agent.get_aesirdeepening_selection("wizard")
        with pytest.raises(ValueError):
            agent.selections_for_capability("")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_aesirdeepening_selection(_selection())
        status = agent.aesirdeepening_status()
        assert [s["office"] for s in status["selections"]] == [
            "scribe"]
        assert status["book"]["selections"][0]["office"] == (
            "scribe")
        assert status["selected"] == ["scribe"]
        assert status["not_selected"] == []
        assert "test hall" in status["screen"]

    def test_held_selection_never_falls_back_to_the_shipped_book(
            self, agent):
        agent.register_aesirdeepening_selection(_selection())
        selection = agent.get_aesirdeepening_selection("scribe")
        assert selection.reason == "Words for the test hall."
        with pytest.raises(ValueError, match="primary"):
            agent.get_aesirdeepening_selection("primary")
        assert [s.office for s in
                agent.aesirdeepening_book().selections] == [
            "scribe"]


class TestAesirAgentHolding:
    def test_register_report_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_aesirdeepening_report(
            live_report())
        assert result["report"]["model"] == "zen-4b"
        assert result["record_news"]["type"] == (
            "aesirdeepening_report")
        assert "zen-4b" in result["screen"]
        events = _aesir_events(
            store, session_id, "aesirdeepening_report")
        assert len(events) == 1
        agent.register_aesirdeepening_report(live_report())
        assert len(_aesir_events(
            store, session_id, "aesirdeepening_report")) == 1
        agent.close()

    def test_register_report_refuses_widening_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValueError, match="tool_calling"):
            agent.register_aesirdeepening_report(
                dict(LIVE_REPORT, tool_calling=True))
        assert agent.aesirdeepening_report() is None
        assert _aesir_events(
            store, session_id, "aesirdeepening_report") == []
        agent.close()

    def test_register_selection_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_aesirdeepening_selection(
            _selection())
        assert result["selection"]["office"] == "scribe"
        assert result["record_news"]["type"] == (
            "aesirdeepening_selection")
        assert len(_aesir_events(
            store, session_id, "aesirdeepening_selection")) == 1
        agent.close()

    def test_duplicate_selection_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_aesirdeepening_selection(_selection())
        with pytest.raises(ValueError, match="scribe"):
            agent.register_aesirdeepening_selection(
                _selection(reason="A second telling."))
        assert len(_aesir_events(
            store, session_id, "aesirdeepening_selection")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_book_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        book = {"schema": AESIR_SCHEMA, "selections": [
            _selection(),
            _selection(office="skald",
                       capability="structured_boolean",
                       reason="Framing for the test hall.")]}
        result = agent.register_aesirdeepening_book(book)
        assert result["count"] == 2
        assert [r["office"] for r in result["records_news"]] == [
            "scribe", "skald"]
        assert len(_aesir_events(
            store, session_id, "aesirdeepening_selection")) == 2
        agent.close()

    def test_record_book_boards_the_shipped_book_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_aesirdeepening_book()
        assert result["count"] == 9
        assert result["book"]["schema"] == AESIR_SCHEMA
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_aesirdeepening_book()
        assert len(_aesir_events(
            store, session_id, "aesirdeepening_selection")) == 9
        agent.close()

    def test_view_target_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_aesirdeepening_report(live_report())
        result = agent.view_aesirdeepening(
            "scribe", needs=("streaming", "tool_calling"))
        assert result["ask"]["shaped"] is True
        assert result["ask"]["granted"] == ["streaming"]
        assert result["ask"]["refused"] == ["tool_calling"]
        assert result["ask"]["model"] == "zen-4b"
        assert result["record_news"]["type"] == (
            "aesirdeepening_ask")
        assert len(_aesir_events(
            store, session_id, "aesirdeepening_ask")) == 1
        assert len(_aesir_events(
            store, session_id, "aesirdeepening_selection")) == 1
        agent.close()

    def test_ask_honest_boundaries(self, agent):
        ask = agent.aesirdeepening_ask(
            "scribe", needs=("streaming",))
        assert ask.shaped is False
        assert ask.road == "session_default"
        agent.register_aesirdeepening_report(live_report())
        ask = agent.aesirdeepening_ask(
            "auditor", needs=("streaming",))
        assert ask.shaped is False
        assert ask.road == "session_default"
        ask = agent.aesirdeepening_ask(
            "scribe", needs=("streaming", "tool_calling"))
        assert ask.shaped is True
        assert ask.granted == ("streaming",)
        assert ask.refused == ("tool_calling",)


class TestAesirParseArgs:
    def test_parse_args_well(self):
        assert parse_aesirdeepening_args("") == (
            "show", None, (), None)
        assert parse_aesirdeepening_args(None) == (
            "show", None, (), None)
        assert parse_aesirdeepening_args("report") == (
            "report", None, (), None)
        assert parse_aesirdeepening_args("selection scribe") == (
            "selection", "scribe", (), None)
        assert parse_aesirdeepening_args(
            "ask scribe streaming model:zen-4b") == (
            "ask", "scribe", ("streaming",), "zen-4b")
        assert parse_aesirdeepening_args("verdict") == (
            "verdict", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "ask", "selection",
                    "report now", "ask scribe model:"):
            with pytest.raises(ValueError) as caught:
                parse_aesirdeepening_args(bad)
            assert str(caught.value) == AESIRDEEPENING_USAGE


class TestAesirTerminalRoad:
    def test_show_report_selections_selection_ask_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/aesirdeepening")
        assert "Aesir per-role selections:" in text
        assert "scribe" in text
        _, _, text = _slash(agent, "/aesirdeepening report")
        assert "reachable: no" in text
        _, _, text = _slash(agent, "/aesirdeepening selections")
        assert "auditor: not selected" in text
        _, _, text = _slash(
            agent, "/aesirdeepening selection scribe")
        assert "scribe: selected for Aesir" in text
        _, _, text = _slash(
            agent, "/aesirdeepening ask scribe streaming")
        assert "no Aesir ask shaped" in text
        _, _, text = _slash(agent, "/aesirdeepening index")
        assert "guardian" in text
        _, _, text = _slash(agent, "/aesirdeepening verdict")
        assert "Aesir is silent" in text
        agent.register_aesirdeepening_report(live_report())
        _, _, text = _slash(agent, "/aesirdeepening report")
        assert "zen-4b" in text
        _, _, text = _slash(
            agent, "/aesirdeepening ask scribe streaming")
        assert "Aesir may be asked" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/aesirdeepening [show|report|selections|"
                "selection <office>|ask <office>|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/aesirdeepening dance party")
        assert text == AESIRDEEPENING_USAGE
        _, _, text = _slash(
            agent, "/aesirdeepening selection wizard")
        assert "unknown office" in text


@pytest.fixture()
def aesir_handler(agent, monkeypatch):
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


def _aesir_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestAesirHandler:
    def test_show_is_default(self, aesir_handler, agent):
        aesir_handler._handle_aesirdeepening("")
        assert "Aesir per-role selections:" in (
            _aesir_published_text(aesir_handler))

    def test_selection_ask_and_verdict(
            self, aesir_handler, agent):
        aesir_handler._handle_aesirdeepening("selection scribe")
        assert "scribe: selected for Aesir" in (
            _aesir_published_text(aesir_handler))
        aesir_handler._handle_aesirdeepening("ask auditor")
        assert "no Aesir ask shaped" in (
            _aesir_published_text(aesir_handler))
        aesir_handler._handle_aesirdeepening("verdict")
        assert "Aesir is silent" in (
            _aesir_published_text(aesir_handler))

    def test_bad_grammar_is_published(
            self, aesir_handler, agent):
        aesir_handler._handle_aesirdeepening("dance party")
        assert AESIRDEEPENING_USAGE in (
            _aesir_published_text(aesir_handler))
        aesir_handler._handle_aesirdeepening("selection wizard")
        assert "unknown office" in (
            _aesir_published_text(aesir_handler))


class TestChatScreenRoutingAesir:
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
        screen.handle_command("/aesirdeepening verdict", _FakeLog())
        assert calls == [("/aesirdeepening", "verdict")]

    def test_chat_screen_help_and_usage_name_the_deepening(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/aesirdeepening[/green] - show the Aesir "
                "deepening (M-245)") in text
        assert ('"/aesirdeepening": "Usage: /aesirdeepening | '
                "/aesirdeepening report") in text


class TestAesirDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.aesirdeepening_index()
        assert result["index"]["gaps"] == UNSELECTED_OFFICES
        assert result["index"]["selected"] == SELECTED_OFFICES
        assert "scribe" in result["index_text"]
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _AESIR_EVENT_TYPES] == []
        agent.close()

    def test_verdict_silent_then_answering(self, agent):
        verdict = agent.aesirdeepening_verdict()
        assert verdict["verdict"]["verdict"] == "silent"
        assert verdict["verdict"]["model"] is None
        agent.register_aesirdeepening_report(live_report())
        verdict = agent.aesirdeepening_verdict()
        assert verdict["verdict"]["verdict"] == "answering"
        assert verdict["verdict"]["model"] == "zen-4b"
        assert "selected offices" in verdict["verdict_text"]

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_aesirdeepening()
        assert report["book"]["schema"] == AESIR_SCHEMA
        assert report["verdict"]["verdict"] == "silent"
        assert report["asks"] and all(
            not ask["shaped"] for ask in report["asks"])
        agent.register_aesirdeepening_report(live_report())
        report = agent.report_aesirdeepening()
        assert "zen-4b" in report["report_text"]
        assert all(ask["shaped"] for ask in report["asks"])
