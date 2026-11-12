"""M-246 Git host parity - pure-layer tests.

TIER: unit

The pure layer holds git hosts as registry entries like
providers, and one parity record per host as data. Parity
standing is DERIVED at call time against the parity walk
(registered, mapped, crafted, evidenced, held): a record
stands held only on a full legal walk resting on held
evidence, and stands open - named in its gaps - on a bare
claim, an illegal step, a short walk, or no evidence at
all. No host is called, no repo is cloned, and nothing is
pushed in this layer.
"""

import pytest

from mythic_agent.core.git_host_parity import (
    BARE_CLAIMS,
    CRAFTS,
    GIT_HOST_SCHEMA,
    HELD_EVIDENCE,
    HOSTS,
    STAGES,
    TRANSITIONS,
    HostEntry,
    ParityRecord,
    derive_standing,
    format_hosts,
    format_parity,
    host_record,
    legal_step,
    load_host_registry,
    load_host_registry_file,
    parity_gaps,
    plain_words,
    validate_host_entry,
    validate_host_registry,
    validate_parity_record,
)
from mythic_agent.core.validation import ValidationError

FULL_WALK = ["registered", "mapped", "crafted",
             "evidenced", "held"]


def held_record(**overrides):
    raw = {
        "host": "gitlab",
        "crafts": ["clone", "branch", "request", "merge"],
        "stages": list(FULL_WALK),
        "claims": ["remote_ref", "request_ref", "parity_ref"],
        "detail": "The GitLab walk, evidenced craft by craft.",
    }
    raw.update(overrides)
    return validate_parity_record(raw)


def test_hosts_are_the_three_named_forges():
    assert HOSTS == ("github", "gitlab", "bitbucket")
    assert GIT_HOST_SCHEMA == "mythic.git_host_parity/1"


def test_stages_and_transitions_form_one_walk():
    assert STAGES == ("registered", "mapped", "crafted",
                      "evidenced", "held")
    assert TRANSITIONS["registered"] == ("mapped",)
    assert TRANSITIONS["held"] == ()
    assert set(TRANSITIONS) == set(STAGES)


def test_crafts_are_the_host_agnostic_git_craft():
    assert CRAFTS == ("clone", "branch", "commit", "push",
                      "request", "issue", "review", "merge")
    assert "remote_ref" in HELD_EVIDENCE
    assert "assertion" in BARE_CLAIMS


def test_shipped_registry_covers_every_host_once():
    registry = load_host_registry()
    assert [h.host for h in registry.hosts] == list(HOSTS)


def test_shipped_registry_names_each_request_word():
    registry = load_host_registry()
    assert registry.for_host("gitlab").request_word == (
        "merge request")
    assert registry.for_host("github").request_word == (
        "pull request")
    assert registry.for_host("bitbucket").request_word == (
        "pull request")


def test_host_entry_refuses_unknown_host_by_name():
    with pytest.raises(ValidationError, match="unknown host"):
        validate_host_entry({
            "host": "sourceforge", "label": "SourceForge",
            "request_word": "pull request",
            "reason": "Not a host this book holds."})


def test_host_entry_refuses_half_written_records():
    with pytest.raises(ValidationError, match="reason"):
        validate_host_entry({
            "host": "github", "label": "GitHub",
            "request_word": "pull request", "reason": "  "})
    with pytest.raises(ValidationError,
                       match="request word"):
        validate_host_entry({
            "host": "github", "label": "GitHub",
            "request_word": "change ask",
            "reason": "A word no host gives the craft."})
    with pytest.raises(ValidationError, match="unknown"):
        validate_host_entry({
            "host": "github", "label": "GitHub",
            "request_word": "pull request",
            "reason": "Fine.", "extra": 1})


def test_registry_refuses_wrong_schema_and_duplicates():
    entry = {"host": "github", "label": "GitHub",
             "request_word": "pull request",
             "reason": "The first host."}
    with pytest.raises(ValidationError, match="schema"):
        validate_host_registry(
            {"schema": "mythic.other/9", "hosts": [entry]})
    with pytest.raises(ValidationError, match="duplicate"):
        validate_host_registry({
            "schema": GIT_HOST_SCHEMA,
            "hosts": [entry, dict(entry)]})


def test_registry_loads_from_any_file(tmp_path):
    path = tmp_path / "hosts.yaml"
    path.write_text(
        "schema: mythic.git_host_parity/1\n"
        "hosts:\n"
        "- host: github\n"
        "  label: GitHub\n"
        "  request_word: pull request\n"
        "  reason: Loaded from a plain file.\n",
        encoding="utf-8")
    registry = load_host_registry_file(path)
    assert registry.for_host("github").label == "GitHub"


def test_host_record_is_plain_data():
    registry = load_host_registry()
    record = host_record(registry, "gitlab")
    assert record["host"] == "gitlab"
    assert record["label"] == "GitLab"
    entry = registry.for_host("github")
    assert isinstance(entry, HostEntry)
    assert entry.record()["request_word"] == "pull request"
    with pytest.raises(ValidationError, match="unknown host"):
        host_record(registry, "codeberg")


def test_parity_record_holds_walk_whole():
    record = held_record()
    assert isinstance(record, ParityRecord)
    assert record.stage == "held"
    assert record.record()["stages"] == FULL_WALK
    assert record.record()["claims"] == [
        "remote_ref", "request_ref", "parity_ref"]


def test_parity_refuses_unknown_craft_by_name():
    with pytest.raises(ValidationError, match="craft"):
        held_record(crafts=["teleport"])


def test_parity_refuses_unknown_stage_and_claim():
    with pytest.raises(ValidationError, match="stage"):
        held_record(stages=["registered", "teleported"])
    with pytest.raises(ValidationError, match="claim"):
        held_record(claims=["vibes"])
    with pytest.raises(ValidationError, match="detail"):
        held_record(detail=" ")


def test_legal_steps_follow_the_walk():
    assert legal_step("registered", "mapped")
    assert legal_step("evidenced", "held")
    assert not legal_step("registered", "held")
    assert not legal_step("held", "mapped")
    assert not legal_step("nowhere", "mapped")


def test_standing_held_only_on_full_walk_with_evidence():
    standing = derive_standing(held_record())
    assert standing.standing == "held"
    assert standing.gaps == ()
    assert standing.stage == "held"
    assert standing.record()["host"] == "gitlab"


def test_standing_open_when_walk_stops_early():
    standing = derive_standing(held_record(
        stages=["registered", "mapped", "crafted"]))
    assert standing.standing == "open"
    assert any("not held" in gap for gap in standing.gaps)


def test_standing_open_on_illegal_step():
    gaps = parity_gaps(held_record(
        stages=["registered", "crafted", "evidenced",
                "held"]))
    assert any("not in the parity walk" in gap
               for gap in gaps)
    gaps = parity_gaps(held_record(
        stages=["mapped", "crafted", "evidenced", "held"]))
    assert any("walk opens at" in gap for gap in gaps)


def test_standing_open_on_bare_claims():
    standing = derive_standing(held_record(
        claims=["remote_ref", "assertion"]))
    assert standing.standing == "open"
    assert any("bare claims" in gap
               for gap in standing.gaps)


def test_standing_open_when_held_without_evidence():
    standing = derive_standing(held_record(claims=[]))
    assert standing.standing == "open"
    assert any("no held evidence" in gap
               for gap in standing.gaps)


def test_standing_open_with_no_craft_named():
    standing = derive_standing(held_record(crafts=[]))
    assert standing.standing == "open"
    assert any("no git craft" in gap for gap in standing.gaps)
    empty = derive_standing(held_record(stages=[], claims=[],
                                        crafts=[]))
    assert any("not begun" in gap for gap in empty.gaps)


def test_plain_words_and_formatters_speak_plainly():
    words = plain_words()
    assert "host-agnostic" in words
    assert "registry entries like providers" in words
    assert "ever claimed without held evidence" in words
    registry = load_host_registry()
    block = format_hosts(registry)
    assert "GitHub" in block and "GitLab" in block
    assert "Bitbucket" in block and "merge request" in block
    text = format_parity(held_record())
    assert "gitlab: parity held" in text
    open_text = format_parity(held_record(
        stages=["registered"], claims=["memory"]))
    assert "parity open" in open_text
    assert "gap:" in open_text

# ---------------------------------------------------------------------
# M-246 agent layer: the agent holds the shipped host
# registry and one parity record per host for the
# session, records and viewed standings are published
# as session news through the checkpoint road
# (journal-first, deduped per host and per telling),
# standings, the index and the verdict are derived at
# call time from the held records - a host stands held
# only on a full legal walk resting on held evidence -
# and the registry is session state, never a stored
# setting. This layer calls no host API, clones
# nothing, pushes nothing and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    GITHOSTPARITY_USAGE,
    parse_githostparity_args,
)
from mythic_agent.core.git_host_parity import (
    PLAIN_EXPLANATION,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore

ROOT = _Path(__file__).resolve().parent.parent

_PARITY_EVENT_TYPES = (
    "githostparity_record", "githostparity_standing")

ALL_HOSTS = ["github", "gitlab", "bitbucket"]


def _parity_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _parity_record(**overrides):
    raw = {
        "host": "gitlab",
        "crafts": ["clone", "branch", "request", "merge"],
        "stages": list(FULL_WALK),
        "claims": ["remote_ref", "request_ref", "parity_ref"],
        "detail": "The GitLab walk, evidenced craft by craft.",
    }
    raw.update(overrides)
    return raw


def _held_for(host):
    return _parity_record(
        host=host,
        detail=f"The {host} walk, evidenced craft by craft.")


class TestGitHostParityAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_registry(
            self, agent):
        status = agent.githostparity_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["githostparity_book"]["schema"] == (
            GIT_HOST_SCHEMA)
        assert [h["host"] for h in status[
            "githostparity_book"]["hosts"]] == ALL_HOSTS
        assert status["githostparity_book"]["records"] == []
        assert status["held"] == []
        assert status["open"] == ALL_HOSTS
        assert status["index"]["gaps"] == ALL_HOSTS
        assert status["index"]["total"] == 3
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "GitLab" in status["hosts_text"]
        assert "merge request" in status["hosts_text"]
        assert "none held this session" in status["screen"]
        assert "host-agnostic" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == GITHOSTPARITY_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._githostparity_registry()
        assert agent._githostparity_registry() is first
        assert agent._githostparity_store is first
        for name in ("githostparity_hosts",
                     "githostparity_book",
                     "githostparity_status",
                     "get_githostparity_host",
                     "get_githostparity_record",
                     "githostparity_standing",
                     "records_for_craft",
                     "githostparity_held",
                     "githostparity_index",
                     "githostparity_verdict",
                     "report_githostparity"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_githostparity_registry", "githostparity_hosts",
            "githostparity_book", "githostparity_status",
            "get_githostparity_host",
            "get_githostparity_record",
            "githostparity_standing", "records_for_craft",
            "githostparity_held", "githostparity_index",
            "githostparity_verdict",
            "register_githostparity_record",
            "register_githostparity_records",
            "record_githostparity_records",
            "view_githostparity", "report_githostparity",
            "_publish_githostparity_record",
            "_githostparity_screen",
            "_githostparity_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.githostparity_status()
        entry = agent.get_githostparity_host("gitlab")
        assert entry.request_word == "merge request"
        standing = agent.githostparity_standing("github")
        assert standing.standing == "open"
        assert agent.githostparity_held() == []
        assert agent.records_for_craft("clone") == []
        agent.githostparity_index()
        agent.githostparity_verdict()
        agent.report_githostparity()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _PARITY_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown host"):
            agent.get_githostparity_host("codeberg")
        with pytest.raises(ValueError, match="unknown host"):
            agent.githostparity_standing("codeberg")
        with pytest.raises(ValueError, match="no parity record"):
            agent.get_githostparity_record("github")
        with pytest.raises(ValueError):
            agent.records_for_craft("")
        with pytest.raises(ValueError, match="unknown craft"):
            agent.records_for_craft("teleport")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_githostparity_record(_parity_record())
        status = agent.githostparity_status()
        assert [r["host"] for r in status["records"]] == [
            "gitlab"]
        assert status["book"]["records"][0]["host"] == (
            "gitlab")
        assert status["held"] == ["gitlab"]
        assert status["open"] == ["github", "bitbucket"]
        assert "gitlab: parity held" in status["screen"]
        assert "gitlab: parity held" in status[
            "records_text"]

    def test_held_record_never_falls_back_to_another_host(
            self, agent):
        agent.register_githostparity_record(_parity_record())
        record = agent.get_githostparity_record("gitlab")
        assert record.detail == (
            "The GitLab walk, evidenced craft by craft.")
        with pytest.raises(ValueError, match="github"):
            agent.get_githostparity_record("github")
        assert [r.host for r in
                agent._githostparity_registry()
                .list_records()] == ["gitlab"]
        assert [r["host"] for r in
                agent.githostparity_book()["records"]] == [
            "gitlab"]


class TestGitHostParityAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_githostparity_record(
            _parity_record())
        assert result["record"]["host"] == "gitlab"
        assert result["record_news"]["type"] == (
            "githostparity_record")
        assert "gitlab: parity held" in result["screen"]
        assert len(_parity_events(
            store, session_id, "githostparity_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_githostparity_record(_parity_record())
        with pytest.raises(ValueError, match="gitlab"):
            agent.register_githostparity_record(
                _parity_record(detail="A second telling."))
        assert len(_parity_events(
            store, session_id, "githostparity_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="claim"):
            agent.register_githostparity_record(
                _parity_record(claims=["vibes"]))
        assert agent.githostparity_status()["records"] == []
        assert _parity_events(
            store, session_id, "githostparity_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_githostparity_records([
            _held_for("github"), _parity_record()])
        assert result["count"] == 2
        assert [r["host"] for r in result["records_news"]] == [
            "github", "gitlab"]
        assert len(_parity_events(
            store, session_id, "githostparity_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_githostparity_records(
            [_held_for("bitbucket")])
        assert result["count"] == 1
        assert result["book"]["schema"] == GIT_HOST_SCHEMA
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_githostparity_records(
                [_held_for("bitbucket")])
        assert len(_parity_events(
            store, session_id, "githostparity_record")) == 1
        agent.close()

    def test_view_host_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_githostparity_record(_parity_record())
        result = agent.view_githostparity("gitlab")
        assert result["host"]["host"] == "gitlab"
        assert result["standing"]["standing"] == "held"
        assert result["record"]["host"] == "gitlab"
        assert result["record_news"]["type"] == (
            "githostparity_standing")
        assert result["held_record_news"]["type"] == (
            "githostparity_record")
        assert len(_parity_events(
            store, session_id, "githostparity_record")) == 1
        assert len(_parity_events(
            store, session_id, "githostparity_standing")) == 1
        result = agent.view_githostparity("github")
        assert result["standing"]["standing"] == "open"
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_parity_events(
            store, session_id, "githostparity_standing")) == 2
        agent.close()


class TestGitHostParityParseArgs:
    def test_parse_args_well(self):
        assert parse_githostparity_args("") == (
            "show", None, (), None)
        assert parse_githostparity_args(None) == (
            "show", None, (), None)
        assert parse_githostparity_args("hosts") == (
            "hosts", None, (), None)
        assert parse_githostparity_args("host gitlab") == (
            "host", "gitlab", (), None)
        assert parse_githostparity_args("record github") == (
            "record", "github", (), None)
        assert parse_githostparity_args(
            "standing bitbucket") == (
            "standing", "bitbucket", (), None)
        assert parse_githostparity_args("verdict") == (
            "verdict", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "host", "record",
                    "hosts now", "standing gitlab extra"):
            with pytest.raises(ValueError) as caught:
                parse_githostparity_args(bad)
            assert str(caught.value) == GITHOSTPARITY_USAGE


class TestGitHostParityTerminalRoad:
    def test_show_hosts_host_record_standing_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/githostparity")
        assert "Git hosts, held as registry entries:" in text
        assert "none held this session" in text
        _, _, text = _slash(agent, "/githostparity hosts")
        assert "Bitbucket" in text
        _, _, text = _slash(agent, "/githostparity host gitlab")
        assert "the request craft is a merge request" in text
        _, _, text = _slash(
            agent, "/githostparity record gitlab")
        assert "holds no parity record" in text
        _, _, text = _slash(
            agent, "/githostparity standing github")
        assert "github: parity open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/githostparity index")
        assert "bitbucket: parity open" in text
        _, _, text = _slash(agent, "/githostparity verdict")
        assert "Parity stands open" in text
        agent.register_githostparity_record(_parity_record())
        _, _, text = _slash(
            agent, "/githostparity record gitlab")
        assert "gitlab: parity held" in text
        _, _, text = _slash(
            agent, "/githostparity standing gitlab")
        assert "gitlab: parity held" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/githostparity [show|hosts|host <host>|"
                "record <host>|standing <host>|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/githostparity dance party")
        assert text == GITHOSTPARITY_USAGE
        _, _, text = _slash(
            agent, "/githostparity host codeberg")
        assert "unknown host" in text


@pytest.fixture()
def parity_handler(agent, monkeypatch):
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


def _parity_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestGitHostParityHandler:
    def test_show_is_default(self, parity_handler, agent):
        parity_handler._handle_githostparity("")
        assert "Git hosts, held as registry entries:" in (
            _parity_published_text(parity_handler))

    def test_host_record_and_verdict(
            self, parity_handler, agent):
        parity_handler._handle_githostparity("host gitlab")
        assert "the request craft is a merge request" in (
            _parity_published_text(parity_handler))
        agent.register_githostparity_record(_parity_record())
        parity_handler._handle_githostparity("record gitlab")
        assert "gitlab: parity held" in (
            _parity_published_text(parity_handler))
        parity_handler._handle_githostparity("verdict")
        assert "Parity stands open" in (
            _parity_published_text(parity_handler))

    def test_bad_grammar_is_published(
            self, parity_handler, agent):
        parity_handler._handle_githostparity("dance party")
        assert GITHOSTPARITY_USAGE in (
            _parity_published_text(parity_handler))
        parity_handler._handle_githostparity("host codeberg")
        assert "unknown host" in (
            _parity_published_text(parity_handler))


class TestChatScreenRoutingGitHostParity:
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
        screen.handle_command("/githostparity verdict", _FakeLog())
        assert calls == [("/githostparity", "verdict")]

    def test_chat_screen_help_and_usage_name_the_parity(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/githostparity[/green] - show the Git host "
                "parity (M-246)") in text
        assert ('"/githostparity": "Usage: /githostparity | '
                "/githostparity hosts") in text


class TestGitHostParityDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.githostparity_index()
        assert result["index"]["gaps"] == ALL_HOSTS
        assert result["index"]["held"] == []
        assert "gitlab" in result["index_text"]
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _PARITY_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        verdict = agent.githostparity_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        for host in ALL_HOSTS:
            agent.register_githostparity_record(_held_for(host))
        verdict = agent.githostparity_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == ALL_HOSTS
        assert "Parity stands held" in verdict["verdict_text"]

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_githostparity()
        assert report["book"]["schema"] == GIT_HOST_SCHEMA
        assert report["verdict"]["verdict"] == "open"
        assert "github: parity open" in report["records_text"]
        agent.register_githostparity_record(_parity_record())
        report = agent.report_githostparity()
        assert "gitlab: parity held" in report["records_text"]
        assert [s["host"] for s in report["standings"]] == (
            ALL_HOSTS)

    def test_records_for_craft_and_held_hosts(self, agent):
        agent.register_githostparity_record(_parity_record())
        agent.register_githostparity_record(_parity_record(
            host="github", crafts=["clone"],
            stages=["registered"], claims=["memory"],
            detail="The GitHub walk, barely begun."))
        assert [r.host for r in
                agent.records_for_craft("request")] == [
            "gitlab"]
        assert [r.host for r in
                agent.records_for_craft("clone")] == [
            "gitlab", "github"]
        assert agent.githostparity_held() == ["gitlab"]
        standing = agent.githostparity_standing("github")
        assert standing.standing == "open"
        assert any("bare claims" in gap
                   for gap in standing.gaps)

    def test_book_composes_registry_and_records(self, agent):
        book = agent.githostparity_book()
        assert book["schema"] == GIT_HOST_SCHEMA
        assert [h["host"] for h in book["hosts"]] == ALL_HOSTS
        assert book["records"] == []
        agent.register_githostparity_record(_parity_record())
        book = agent.githostparity_book()
        assert [r["host"] for r in book["records"]] == [
            "gitlab"]
        hosts = agent.githostparity_hosts()
        assert hosts.for_host("bitbucket").label == "Bitbucket"
