"""M-257 Regression court - pure-layer tests.

TIER: unit

Every part's gate results re-run as one battery; a
red anywhere stops the release, not just the part:
a part whose re-run rests on no held gate evidence,
whose counts fall short, or whose outcome stands
red holds the whole road open.
"""
import pytest

from mythic_agent.core.regression_court import (
    BARE_CLAIMS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    OUTCOMES,
    PARTS,
    STAGES,
    CourtRecord,
    PartEntry,
    PartRegistry,
    default_registry,
    derive_standing,
    derive_verdict,
    format_part,
    format_parts,
    format_record,
    format_records,
    prepare_verdict,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(part="part_01", run="court-2026-11-a",
                date="2026-11-12", outcome="green",
                passed=40, total=40,
                stages=STAGES,
                claims=("gate_log_ref", "rerun_log_ref"))
    base.update(kw)
    return CourtRecord(**base)


def full_battery(**overrides):
    records = []
    for entry in default_registry().entries():
        kw = dict(part=entry.id, run="court-2026-11-a",
                  date="2026-11-12", outcome="green",
                  passed=40, total=40, stages=STAGES,
                  claims=("gate_log_ref", "rerun_log_ref"))
        kw.update(overrides.get(entry.id, {}))
        records.append(CourtRecord(**kw))
    return records


def test_registry_holds_eleven_parts_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 11
    assert reg.ids()[0] == "part_01"
    assert reg.ids()[-1] == "part_11"
    assert all(e.standing == "listed" for e in reg.entries())


def test_registry_part_ranges_cover_the_road():
    reg = default_registry()
    assert reg.get("part_01").first_slice == "M-001"
    assert reg.get("part_11").last_slice == "M-272"
    assert reg.get("part_11").label == "The Proof Spine"


def test_registry_unknown_part_refused_by_name():
    with pytest.raises(ValidationError, match="unknown part: part_99"):
        default_registry().get("part_99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate part"):
        PartRegistry(PARTS + PARTS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        PartRegistry([PartEntry(
            "part_01", 1, "I", "", "M-001", "M-018", "listed", "why")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        PartRegistry([PartEntry(
            "part_01", 1, "I", "X", "M-001", "M-018", "published", "why")])


def test_record_complete_green_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held
    assert standing.grade == "held"
    assert standing.gaps == ()


def test_record_incomplete_walk_stands_open():
    standing = derive_standing(fresh_record(stages=STAGES[:3]))
    assert not standing.held
    assert any("not held" in g for g in standing.gaps)


def test_record_bad_stage_step_stands_open():
    bad = ("named", "rerun", "judged", "held")
    standing = derive_standing(fresh_record(stages=bad))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_record_red_outcome_stops_the_release():
    standing = derive_standing(fresh_record(outcome="red"))
    assert not standing.held
    assert any("stops the release" in g for g in standing.gaps)


def test_record_short_counts_stand_open():
    standing = derive_standing(fresh_record(passed=39))
    assert not standing.held
    assert any("fall short" in g for g in standing.gaps)


def test_record_without_gate_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("rerun_log_ref",)))
    assert not standing.held
    assert any("no held gate evidence" in g for g in standing.gaps)


def test_record_bare_claims_only_stand_open():
    standing = derive_standing(fresh_record(claims=("feeling",)))
    assert not standing.held
    assert any("bare claims only" in g for g in standing.gaps)


def test_record_unknown_evidence_kind_refused():
    with pytest.raises(ValidationError, match="unknown record evidence kind"):
        derive_standing(fresh_record(claims=("rumour",)))


def test_record_bad_date_refused():
    with pytest.raises(ValidationError, match="unknown re-run date"):
        derive_standing(fresh_record(date="12/11/2026"))


def test_record_inflated_counts_refused():
    with pytest.raises(ValidationError, match="never inflated"):
        derive_standing(fresh_record(passed=41))


def test_record_unknown_outcome_refused():
    with pytest.raises(ValidationError, match="unknown re-run outcome"):
        derive_standing(fresh_record(outcome="amber"))


def test_verdict_ready_when_every_part_held():
    verdict = derive_verdict(full_battery())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.red_parts == ()
    assert verdict.missing_parts == ()


def test_verdict_one_red_stops_the_whole_release():
    verdict = derive_verdict(full_battery(
        part_05=dict(outcome="red", passed=38)))
    assert not verdict.ready
    assert verdict.red_parts == ("part_05",)


def test_verdict_missing_part_stops_the_release():
    verdict = derive_verdict(full_battery()[:10])
    assert not verdict.ready
    assert verdict.missing_parts == ("part_11",)


def test_verdict_open_record_stops_the_release():
    verdict = derive_verdict(full_battery(
        part_03=dict(claims=("summary",))))
    assert not verdict.ready
    assert any("part_03 stands open" in g for g in verdict.gaps)


def test_prepare_verdict_all_green_may_claim_release():
    draft = prepare_verdict(
        "court-2026-11", "release-1", "every part green",
        "2026-11-12", 11, 11, claims=("gate_log_ref",),
        released=True)
    assert draft.state == "ready"
    assert draft.released


def test_prepare_verdict_release_claim_short_of_green_refused():
    with pytest.raises(ValidationError, match="stops the release"):
        prepare_verdict(
            "court-2026-11", "release-1", "mostly green",
            "2026-11-12", 10, 11, claims=("gate_log_ref",),
            released=True)


def test_prepare_verdict_sealed_state_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_verdict(
            "court-2026-11", "release-1", "every part green",
            "2026-11-12", 11, 11, claims=("gate_log_ref",),
            state="sealed")


def test_format_roads_name_the_part_and_outcome():
    line = format_record(fresh_record())
    assert "part_01" in line
    assert "green" in line
    assert "held as re-run" in line
    part_line = format_part(default_registry().get("part_11"))
    assert "The Proof Spine" in part_line
    assert "M-255-M-272" in part_line
    assert len(format_parts().splitlines()) == 11
    assert len(format_records(full_battery()).splitlines()) == 11
    assert HELD_EVIDENCE[0] == "gate_log_ref"
    assert BARE_CLAIMS[-1] == "summary"
    assert "gate_log_ref" in EVIDENCE_KINDS
    assert OUTCOMES == ("green", "red")


# ---------------------------------------------------------------------
# M-257 agent layer: the agent holds the shipped part
# registry and one re-run record per part and run for
# the session, records, viewed standings and held
# verdicts are published as session news through the
# checkpoint road (journal-first, deduped per record,
# standing and verdict), standings, the index and the
# verdict are derived at call time from the held records -
# a re-run stands held only when its gate rests on held
# gate evidence, its outcome is green and its counts are
# complete - court verdicts are held only as verdicts,
# state ready by default, may be marked shared by a human,
# a release claimed only when every part stands green,
# and never inflated, and the registry is session
# state, never a stored setting. This layer re-runs no
# gate, executes no test and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    REGRESSIONCOURT_USAGE,
    parse_regressioncourt_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.regression_court import (
    PLAIN_EXPLANATION,
    REGRESSION_COURT_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_RC_EVENT_TYPES = (
    "regressioncourt_record", "regressioncourt_standing", "regressioncourt_verdict")

ALL_PARTS = ["part_01", "part_02", "part_03", "part_04",
             "part_05", "part_06", "part_07", "part_08",
             "part_09", "part_10", "part_11"]


def _rc_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _rc_record(**overrides):
    raw = {
        "part": "part_01",
        "run": "court-2026-11-a",
        "date": "2026-11-12",
        "outcome": "green",
        "passed": 40,
        "total": 40,
        "stages": list(STAGES),
        "claims": ["gate_log_ref", "rerun_log_ref"],
    }
    raw.update(overrides)
    return raw


def _rc_fresh_for(part, run="court-2026-11-a"):
    return _rc_record(part=part, run=run)


class TestRegressionCourtAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_parts(
            self, agent):
        status = agent.regressioncourt_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["regressioncourt_book"]["schema"] == (
            REGRESSION_COURT_SCHEMA)
        assert [p["id"] for p in status[
            "regressioncourt_book"]["parts"]] == ALL_PARTS
        assert status["regressioncourt_book"]["records"] == []
        assert status["regressioncourt_book"]["verdicts"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "The Census" in status["parts_text"]
        assert "standing listed" in status["parts_text"]
        assert "none recorded this session" in status["screen"]
        assert "regression court" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == REGRESSIONCOURT_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._regressioncourt_registry()
        assert agent._regressioncourt_registry() is first
        assert agent._regressioncourt_store is first
        for name in ("regressioncourt_parts",
                     "regressioncourt_book",
                     "regressioncourt_status",
                     "get_regressioncourt_part",
                     "get_regressioncourt_record",
                     "regressioncourt_standing",
                     "records_for_outcome",
                     "regressioncourt_held",
                     "regressioncourt_index",
                     "regressioncourt_verdict",
                     "prepare_regressioncourt_draft",
                     "get_regressioncourt_draft",
                     "regressioncourt_drafts",
                     "report_regressioncourt"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_regressioncourt_registry", "regressioncourt_parts",
            "regressioncourt_book", "regressioncourt_status",
            "get_regressioncourt_part",
            "get_regressioncourt_record",
            "regressioncourt_standing", "records_for_outcome",
            "regressioncourt_held", "regressioncourt_index",
            "regressioncourt_verdict",
            "register_regressioncourt_record",
            "register_regressioncourt_records",
            "record_regressioncourt_records",
            "view_regressioncourt", "prepare_regressioncourt_draft",
            "report_regressioncourt",
            "_publish_regressioncourt_record",
            "_regressioncourt_screen",
            "_regressioncourt_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.regressioncourt_status()
        entry = agent.get_regressioncourt_part("part_03")
        assert entry.roman == "III"
        assert entry.label == "Code Intelligence"
        standing = agent.regressioncourt_standing(
            "part_01", "court-2026-11-a")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.grade == "open"
        assert agent.regressioncourt_held() == []
        assert agent.records_for_outcome("green") == []
        agent.regressioncourt_index()
        agent.regressioncourt_verdict()
        agent.report_regressioncourt()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _RC_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown part"):
            agent.get_regressioncourt_part("guess")
        with pytest.raises(ValueError, match="unknown part"):
            agent.regressioncourt_standing("guess", "court-2026-11-a")
        with pytest.raises(ValueError, match="holds no re-run record"):
            agent.get_regressioncourt_record("part_01", "court-2026-11-a")
        with pytest.raises(ValueError):
            agent.records_for_outcome("")
        agent.close()


class TestRegressionCourtAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_regressioncourt_record(_rc_record())
        assert result["record"]["part"] == "part_01"
        assert result["record"]["run"] == "court-2026-11-a"
        assert result["record_news"]["type"] == (
            "regressioncourt_record")
        assert "held as re-run" in result["screen"]
        status = agent.regressioncourt_status()
        assert [r["part"] for r in status["records"]] == [
            "part_01"]
        assert status["book"]["records"][0]["run"] == (
            "court-2026-11-a")
        assert status["held"] == ["part_01/court-2026-11-a"]
        assert status["open"] == []
        assert "held as re-run" in status["records_text"]
        assert len(_rc_records(
            store, session_id, "regressioncourt_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_regressioncourt_record(_rc_record())
        with pytest.raises(ValueError, match="part_01"):
            agent.register_regressioncourt_record(
                _rc_record(outcome="red"))
        assert len(_rc_records(
            store, session_id, "regressioncourt_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_regressioncourt_record(
                _rc_record(claims=["vibes"]))
        assert agent.regressioncourt_status()["records"] == []
        assert _rc_records(
            store, session_id, "regressioncourt_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_regressioncourt_records([
            _rc_fresh_for("part_03"), _rc_record()])
        assert result["count"] == 2
        assert [r["part"] for r in result["records_news"]] == [
            "part_03", "part_01"]
        assert len(_rc_records(
            store, session_id, "regressioncourt_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_regressioncourt_records(
            [_rc_fresh_for("part_03")])
        assert result["count"] == 1
        assert result["book"]["schema"] == REGRESSION_COURT_SCHEMA
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_regressioncourt_records(
                [_rc_fresh_for("part_03")])
        assert len(_rc_records(
            store, session_id, "regressioncourt_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_regressioncourt_record(_rc_record())
        result = agent.view_regressioncourt("part_01", "court-2026-11-a")
        assert result["part"]["id"] == "part_01"
        assert result["standing"]["held"] is True
        assert result["record"]["run"] == "court-2026-11-a"
        assert result["record_news"]["type"] == (
            "regressioncourt_standing")
        assert result["held_record_news"]["type"] == (
            "regressioncourt_record")
        assert len(_rc_records(
            store, session_id, "regressioncourt_record")) == 1
        assert len(_rc_records(
            store, session_id, "regressioncourt_standing")) == 1
        result = agent.view_regressioncourt("part_02", "court-2026-11-a")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_rc_records(
            store, session_id, "regressioncourt_standing")) == 2
        agent.close()


class TestRegressionCourtDrafts:
    def test_prepare_draft_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_regressioncourt_draft(
            "court-2026-11", "battery-a",
            "all eleven parts green", "2026-11-12", 11, 11,
            claims=("gate_log_ref", "report_ref"))
        assert result["draft"]["state"] == "ready"
        assert result["draft"]["inflated"] is False
        assert result["draft_news"]["type"] == (
            "regressioncourt_verdict")
        assert "all eleven parts green" in result["screen"]
        draft = agent.get_regressioncourt_draft("court-2026-11")
        assert draft.entry == "battery-a"
        assert [d.battery for d in agent.regressioncourt_drafts()] == [
            "court-2026-11"]
        assert len(_rc_records(
            store, session_id, "regressioncourt_verdict")) == 1
        agent.close()

    def test_draft_unshared_state_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared"):
            agent.prepare_regressioncourt_draft(
                "court-2026-11", "battery-a", "x",
                "2026-11-12", 11, 11,
                claims=("gate_log_ref",), state="executed")
        assert agent.regressioncourt_drafts() == []
        assert _rc_records(
            store, session_id, "regressioncourt_verdict") == []
        agent.close()

    def test_duplicate_draft_refuses(self, agent):
        agent.prepare_regressioncourt_draft(
            "court-2026-11", "battery-a",
            "all eleven parts green", "2026-11-12", 11, 11,
            claims=("gate_log_ref",))
        with pytest.raises(ValueError, match="court-2026-11"):
            agent.prepare_regressioncourt_draft(
                "court-2026-11", "battery-b",
                "a second telling", "2026-11-12", 11, 11,
                claims=("gate_log_ref",))
        with pytest.raises(ValueError,
                           match="holds no court verdict"):
            agent.get_regressioncourt_draft("court-2026-12")


class TestRegressionCourtParseArgs:
    def test_parse_args_well(self):
        assert parse_regressioncourt_args("") == (
            "show", None, (), None)
        assert parse_regressioncourt_args(None) == (
            "show", None, (), None)
        assert parse_regressioncourt_args("parts") == (
            "parts", None, (), None)
        assert parse_regressioncourt_args("part part_02") == (
            "part", "part_02", (), None)
        assert parse_regressioncourt_args(
            "record part_01 court-2026-11-a") == (
            "record", ("part_01", "court-2026-11-a"), (), None)
        assert parse_regressioncourt_args(
            "standing part_03 v-1") == (
            "standing", ("part_03", "v-1"), (), None)
        assert parse_regressioncourt_args("draft") == (
            "drafts", None, (), None)
        assert parse_regressioncourt_args(
            "draft court-2026-11") == (
            "draft", "court-2026-11", (), None)
        assert parse_regressioncourt_args("verdict") == (
            "verdict", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "part", "record",
                    "record part_01",
                    "parts now", "standing part_01",
                    "draft court extra"):
            with pytest.raises(ValueError) as caught:
                parse_regressioncourt_args(bad)
            assert str(caught.value) == REGRESSIONCOURT_USAGE


class TestRegressionCourtTerminalRoad:
    def test_show_parts_part_record_standing_draft_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/regressioncourt")
        assert "Part I (part_01)" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/regressioncourt parts")
        assert "Code Intelligence" in text
        _, _, text = _slash(agent, "/regressioncourt part part_02")
        assert "The Provider Ocean" in text
        _, _, text = _slash(
            agent, "/regressioncourt record part_01 court-2026-11-a")
        assert "holds no re-run record" in text
        _, _, text = _slash(
            agent, "/regressioncourt standing part_01 court-2026-11-a")
        assert "part_01/court-2026-11-a: run open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/regressioncourt draft")
        assert "none held" in text
        _, _, text = _slash(agent, "/regressioncourt verdict")
        assert "Regression court stand open" in text
        agent.register_regressioncourt_record(_rc_record())
        _, _, text = _slash(
            agent, "/regressioncourt record part_01 court-2026-11-a")
        assert "held as re-run" in text
        _, _, text = _slash(
            agent, "/regressioncourt standing part_01 court-2026-11-a")
        assert "part_01/court-2026-11-a: run held as re-run" in text
        _, _, text = _slash(agent, "/regressioncourt index")
        assert "held as re-run" in text
        agent.prepare_regressioncourt_draft(
            "court-2026-11", "battery-a",
            "all eleven parts green", "2026-11-12", 11, 11,
            claims=("gate_log_ref",))
        _, _, text = _slash(
            agent, "/regressioncourt draft court-2026-11")
        assert "all eleven parts green" in text
        assert "never inflated" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/regressioncourt [show|parts|part <part>|"
                "record <part> <run>|"
                "standing <part> <run>|"
                "draft [<battery>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/regressioncourt dance party")
        assert text == REGRESSIONCOURT_USAGE
        _, _, text = _slash(agent, "/regressioncourt part guess")
        assert "unknown part" in text


@pytest.fixture()
def rc_handler(agent, monkeypatch):
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


def _rc_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestRegressionCourtHandler:
    def test_show_is_default(self, rc_handler, agent):
        rc_handler._handle_regressioncourt("")
        assert "Part I (part_01)" in (
            _rc_published_text(rc_handler))

    def test_part_record_and_verdict(
            self, rc_handler, agent):
        rc_handler._handle_regressioncourt("part part_02")
        assert "The Provider Ocean" in (
            _rc_published_text(rc_handler))
        agent.register_regressioncourt_record(_rc_record())
        rc_handler._handle_regressioncourt(
            "record part_01 court-2026-11-a")
        assert "held as re-run" in (
            _rc_published_text(rc_handler))
        rc_handler._handle_regressioncourt("verdict")
        assert "Regression court stand held" in (
            _rc_published_text(rc_handler))

    def test_bad_grammar_is_published(
            self, rc_handler, agent):
        rc_handler._handle_regressioncourt("dance party")
        assert REGRESSIONCOURT_USAGE in (
            _rc_published_text(rc_handler))
        rc_handler._handle_regressioncourt("part guess")
        assert "unknown part" in (
            _rc_published_text(rc_handler))


class TestChatScreenRoutingRegressionCourt:
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
        screen.handle_command("/regressioncourt verdict", _FakeLog())
        assert calls == [("/regressioncourt", "verdict")]

    def test_chat_screen_help_and_usage_name_the_court(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/regressioncourt[/green] - show the Regression court "
                "(M-257)") in text
        assert ('"/regressioncourt": "Usage: /regressioncourt | '
                "/regressioncourt parts") in text


class TestRegressionCourtDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.regressioncourt_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _RC_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        verdict = agent.regressioncourt_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_regressioncourt_record(_rc_record())
        agent.register_regressioncourt_record(_rc_fresh_for("part_03"))
        verdict = agent.regressioncourt_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "part_01/court-2026-11-a", "part_03/court-2026-11-a"]
        assert "Regression court stand held" in verdict["verdict_text"]

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_regressioncourt()
        assert report["book"]["schema"] == REGRESSION_COURT_SCHEMA
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_regressioncourt_record(_rc_record())
        report = agent.report_regressioncourt()
        assert "held as re-run" in report["records_text"]
        assert [s["part"] for s in report["standings"]] == [
            "part_01"]

    def test_records_for_outcome_and_held_keys(self, agent):
        agent.register_regressioncourt_record(_rc_record())
        agent.register_regressioncourt_record(_rc_record(
            run="court-2026-11-b", outcome="red",
            passed=3, total=40,
            stages=["named"], claims=["assertion"]))
        assert [r.run for r in
                agent.records_for_outcome("green")] == [
            "court-2026-11-a"]
        assert [r.run for r in
                agent.records_for_outcome("red")] == [
            "court-2026-11-b"]
        assert agent.regressioncourt_held() == ["part_01/court-2026-11-a"]
        standing = agent.regressioncourt_standing(
            "part_01", "court-2026-11-b")
        assert standing.held is False
        assert any("bare claims" in gap
                   for gap in standing.gaps)
