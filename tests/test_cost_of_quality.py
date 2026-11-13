"""M-267 Cost-of-quality report - pure-layer tests.

TIER: unit

Benchmark scores against spend per model route - the
honest shopping guide for the user's own money: a route
counts PROVEN only on scores measured against spend
actually paid resting on held evidence, and a roaded
route with no owner named stands open.
"""
import pytest

from mythic_agent.core.cost_of_quality import (
    ROUTES,
    BARE_CLAIMS,
    DISPOSITIONS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    STAGES,
    CostOfQualityEntry,
    CostOfQualityRegistry,
    CostOfQualityRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_route,
    format_routes,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(route="Q-03",
                work="cost-2026-11-a",
                date="2026-11-13", disposition="PROVEN",
                owner="yrsa",
                proof_kind="measured-and-priced",
                stages=STAGES,
                claims=("benchmark_ref", "spend_ref"))
    base.update(kw)
    return CostOfQualityRecord(**base)


def roaded_record(**kw):
    base = dict(route="Q-05",
                work="cost-2026-11-a",
                date="2026-11-13", disposition="ROADED",
                owner="yrsa",
                proof_kind="measured-and-priced",
                stages=STAGES,
                claims=("spend_ref",))
    base.update(kw)
    return CostOfQualityRecord(**base)


def full_book(**overrides):
    records = []
    for route_id in default_registry().combinations():
        if route_id in ("Q-01", "Q-02", "Q-03"):
            kw = dict(route=route_id, work="cost-2026-11-a",
                      date="2026-11-13", disposition="PROVEN",
                      owner="yrsa",
                      proof_kind="measured-and-priced",
                      stages=STAGES,
                      claims=("benchmark_ref", "spend_ref"))
        else:
            kw = dict(route=route_id, work="cost-2026-11-a",
                      date="2026-11-13", disposition="ROADED",
                      owner="yrsa",
                      proof_kind="measured-and-priced",
                      stages=STAGES,
                      claims=("spend_ref",))
        kw.update(overrides.get(route_id, {}))
        records.append(CostOfQualityRecord(**kw))
    return records


def test_registry_holds_twelve_routes_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "Q-01"
    assert reg.ids()[-1] == "Q-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_routes_cover_the_doctrine_sources():
    reg = default_registry()
    pairs = {(e.doctrine, e.subject) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("Q-01").doctrine == "honest-shopping"
    assert reg.get("Q-01").subject == "local-free-route"
    assert reg.get("Q-02").subject == "local-aesir-route"
    assert reg.get("Q-03").subject == "cheap-cloud-route"
    assert reg.get("Q-04").subject == "mid-cloud-route"
    assert reg.get("Q-11").doctrine == "standing-law"
    assert reg.get("Q-11").subject == "spend-ledger-route"
    assert reg.get("Q-12").doctrine == "proof-duty"
    assert DISPOSITIONS == ("PROVEN", "ROADED")


def test_registry_unknown_route_refused_by_name():
    with pytest.raises(ValidationError, match="unknown route: Q-99"):
        default_registry().get("Q-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate route"):
        CostOfQualityRegistry(ROUTES + ROUTES[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        CostOfQualityRegistry([CostOfQualityEntry("Q-01", "honest-shopping", "local-free-route", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        CostOfQualityRegistry([CostOfQualityEntry("Q-01", "honest-shopping", "local-free-route", "published", "why")])
    with pytest.raises(ValidationError, match="benchmarked"):
        CostOfQualityRegistry([CostOfQualityEntry("Q-01", "honest-shopping", "local-free-route", "listed", "why", benchmarked=False)])
    with pytest.raises(ValidationError, match="priced"):
        CostOfQualityRegistry([CostOfQualityEntry("Q-01", "honest-shopping", "local-free-route", "listed", "why", priced=False)])


def test_entry_unknown_doctrine_refused():
    with pytest.raises(ValidationError, match="unknown route doctrine"):
        CostOfQualityRegistry([CostOfQualityEntry("Q-01", "M-999", "local-free-route", "listed", "why")])


def test_record_proven_measured_and_priced_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held
    assert standing.grade == "held"
    assert standing.gaps == ()


def test_record_incomplete_walk_stands_open():
    standing = derive_standing(fresh_record(stages=STAGES[:3]))
    assert not standing.held
    assert any("not held" in g for g in standing.gaps)


def test_record_bad_stage_step_stands_open():
    bad = ("named", "priced", "dispositioned", "held")
    standing = derive_standing(fresh_record(stages=bad))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_record_proven_on_vendor_claim_stands_open():
    standing = derive_standing(fresh_record(proof_kind="vendor-claim-only"))
    assert not standing.held
    assert any("no vendor word" in g for g in standing.gaps)


def test_record_proven_without_benchmark_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("spend_ref",)))
    assert not standing.held
    assert any("no held benchmark evidence" in g for g in standing.gaps)


def test_record_proven_on_bare_claims_stands_open():
    standing = derive_standing(fresh_record(claims=("feeling",)))
    assert not standing.held
    assert any("bare claims only" in g for g in standing.gaps)


def test_record_roaded_with_owner_stands_held():
    standing = derive_standing(roaded_record())
    assert standing.held
    assert standing.grade == "held"


def test_record_roaded_without_owner_stands_open():
    standing = derive_standing(roaded_record(owner=""))
    assert not standing.held
    assert any("not a road" in g for g in standing.gaps)


def test_record_roaded_silent_stands_open():
    standing = derive_standing(roaded_record(claims=()))
    assert not standing.held
    assert any("silent" in g for g in standing.gaps)


def test_record_without_date_stands_open():
    standing = derive_standing(fresh_record(date=""))
    assert not standing.held
    assert any("no report date" in g for g in standing.gaps)


def test_record_unknown_disposition_refused():
    with pytest.raises(ValidationError, match="unknown record disposition"):
        derive_standing(fresh_record(disposition="MAYBE"))


def test_verdict_full_book_ready_with_roaded_routes():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.proven_routes == ("Q-01", "Q-02", "Q-03")
    assert len(verdict.roaded_routes) == 9
    assert verdict.missing_routes == ()


def test_verdict_missing_route_stops_the_report():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_routes == ("Q-12",)
    assert any("Q-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_report():
    verdict = derive_verdict(full_book(**{"Q-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("Q-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_route_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two findings" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("cost-a", "Q-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("benchmark_ref",))
    assert report.state == "ready"
    shared = prepare_report("cost-a", "Q-01", "findings as dispositioned",
                            "2026-11-13", 3, 9, 12,
                            claims=("benchmark_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_and_short_certified_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("cost-a", "Q-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("benchmark_ref",), state="sealed")
    with pytest.raises(ValidationError, match="cost report complete"):
        prepare_report("cost-a", "Q-01", "findings", "2026-11-13",
                       3, 5, 12, claims=("benchmark_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("cost-a", "Q-01", "findings", "2026-11-13",
                       3, 9, 12, claims=("feeling",))
    assert "Q-01" in format_route(default_registry().get("Q-01"))
    assert "Q-12" in format_routes()
    assert "PROVEN" in format_record(fresh_record())
    assert "ROADED" in format_records([roaded_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
    from pathlib import Path as _P
    _src = (_P(__file__).resolve().parent.parent
            / "mythic_agent" / "core" / "cost_of_quality.py").read_text(
                encoding="utf-8")
    assert "open(" not in _src
    assert "socket" not in _src
    assert "subprocess" not in _src
    assert "urllib" not in _src

# ---------------------------------------------------------------------


# ---------------------------------------------------------------------
# M-267 Cost-of-quality report - agent layer. The pure book is held
# by a session registry in the agent layer alone: routes are read
# from the shipped registry, capture records are held one by one for
# the session, records, viewed standings and held reports are
# published as session news through the checkpoint road
# (journal-first, deduped per record, standing and verdict),
# standings, the index and the verdict are derived at call time from
# the held records - an route stands held only when its finding
# counts PROVEN on measured-and-priced evidence resting on held local
# evidence, or stands ROADED with a named owner in the open -
# audit reports are held only as reports, state ready by default,
# may be marked shared by a human, a certification claimed only
# when every route stands answered, and never inflated, and the
# registry is session state, never a stored setting. This layer
# runs no attack, reads no sandbox code and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    COSTOFQUALITY_USAGE,
    parse_costofquality_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.cost_of_quality import (
    PLAIN_EXPLANATION,
    COST_OF_QUALITY_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_CQ_EVENT_TYPES = (
    "costofquality_record", "costofquality_standing",
    "costofquality_verdict")

ALL_ROUTES = ["Q-01", "Q-02", "Q-03", "Q-04", "Q-05", "Q-06",
             "Q-07", "Q-08", "Q-09", "Q-10", "Q-11", "Q-12"]


def _cq_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _cq_record(**overrides):
    raw = {
        "route": "Q-01",
        "work": "cost-2026-11-a",
        "date": "2026-11-13",
        "disposition": "PROVEN",
        "owner": "yrsa",
        "proof_kind": "measured-and-priced",
        "stages": list(STAGES),
        "claims": ["benchmark_ref", "spend_ref"],
    }
    raw.update(overrides)
    return raw


def _cq_fresh_for(route, work="cost-2026-11-a"):
    return _cq_record(route=route, work=work)


class TestCostOfQualityAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_routes(
            self, agent):
        status = agent.costofquality_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["costofquality_book"]["schema"] == (
            COST_OF_QUALITY_SCHEMA)
        assert [c["id"] for c in status[
            "costofquality_book"]["routes"]] == ALL_ROUTES
        assert status["costofquality_book"]["records"] == []
        assert status["costofquality_book"]["reports"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "Q-01" in status["routes_text"]
        assert "standing listed" in status["routes_text"]
        assert "none recorded this session" in status["screen"]
        assert "cost-of-quality report" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == COSTOFQUALITY_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._costofquality_registry()
        assert agent._costofquality_registry() is first
        assert agent._costofquality_store is first
        for name in ("costofquality_routes",
                     "costofquality_book",
                     "costofquality_status",
                     "get_costofquality_route",
                     "get_costofquality_record",
                     "costofquality_standing",
                     "routes_for_disposition",
                     "costofquality_held",
                     "costofquality_index",
                     "costofquality_verdict",
                     "prepare_costofquality_report",
                     "get_costofquality_report",
                     "costofquality_reports",
                     "report_costofquality"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_costofquality_registry",
            "costofquality_routes",
            "costofquality_book",
            "costofquality_status",
            "get_costofquality_route",
            "get_costofquality_record",
            "costofquality_standing", "routes_for_disposition",
            "costofquality_held", "costofquality_index",
            "costofquality_verdict",
            "register_costofquality_record",
            "register_costofquality_records",
            "record_costofquality_records",
            "view_costofquality",
            "prepare_costofquality_report",
            "get_costofquality_report",
            "costofquality_reports",
            "report_costofquality",
            "_publish_costofquality_record",
            "_costofquality_screen",
            "_costofquality_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.costofquality_status()
        entry = agent.get_costofquality_route("Q-01")
        assert entry.doctrine == "honest-shopping"
        assert entry.subject == "local-free-route"
        standing = agent.costofquality_standing("Q-01")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.grade == "open"
        assert agent.costofquality_held() == []
        assert agent.routes_for_disposition("PROVEN") == []
        agent.costofquality_index()
        agent.costofquality_verdict()
        agent.report_costofquality()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _CQ_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown route"):
            agent.get_costofquality_route("guess")
        with pytest.raises(ValueError, match="unknown route"):
            agent.costofquality_standing("guess")
        with pytest.raises(ValueError, match="holds no"):
            agent.get_costofquality_record("Q-01")
        with pytest.raises(ValueError):
            agent.routes_for_disposition("")
        agent.close()


class TestCostOfQualityAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_costofquality_record(
            _cq_record())
        assert result["record"]["route"] == "Q-01"
        assert result["record_news"]["type"] == (
            "costofquality_record")
        assert "held as answered" in result["screen"]
        status = agent.costofquality_status()
        assert [r["route"] for r in status["records"]] == [
            "Q-01"]
        assert status["book"]["records"][0]["work"] == (
            "cost-2026-11-a")
        assert status["held"] == ["Q-01"]
        assert status["open"] == []
        assert "held as answered" in status["records_text"]
        assert len(_cq_records(
            store, session_id, "costofquality_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_costofquality_record(_cq_record())
        with pytest.raises(ValueError, match="Q-01"):
            agent.register_costofquality_record(
                _cq_record(work="cost-2026-11-b"))
        assert len(_cq_records(
            store, session_id, "costofquality_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_costofquality_record(
                _cq_record(claims=["vibes"]))
        assert agent.costofquality_status()["records"] == []
        assert _cq_records(
            store, session_id, "costofquality_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_costofquality_records([
            _cq_fresh_for("Q-02"), _cq_record()])
        assert result["count"] == 2
        assert [r["route"] for r in result["records_news"]] == [
            "Q-02", "Q-01"]
        assert len(_cq_records(
            store, session_id, "costofquality_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_costofquality_records(
            [_cq_fresh_for("Q-02")])
        assert result["count"] == 1
        assert result["book"]["schema"] == (
            COST_OF_QUALITY_SCHEMA)
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_costofquality_records(
                [_cq_fresh_for("Q-02")])
        assert len(_cq_records(
            store, session_id, "costofquality_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_costofquality_record(_cq_record())
        result = agent.view_costofquality("Q-01")
        assert result["route"]["id"] == "Q-01"
        assert result["standing"]["held"] is True
        assert result["record"]["work"] == "cost-2026-11-a"
        assert result["record_news"]["type"] == (
            "costofquality_standing")
        assert result["held_record_news"]["type"] == (
            "costofquality_record")
        assert len(_cq_records(
            store, session_id, "costofquality_record")) == 1
        assert len(_cq_records(
            store, session_id, "costofquality_standing")) == 1
        result = agent.view_costofquality("Q-03")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_cq_records(
            store, session_id, "costofquality_standing")) == 2
        agent.close()


class TestCostOfQualityReports:
    def test_prepare_report_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_costofquality_report(
            "cost-2026-11", "release-1",
            "every route answered",
            "2026-11-13", 3, 9, 12,
            claims=("benchmark_ref", "spend_ref"))
        assert result["report"]["state"] == "ready"
        assert result["report"]["certified"] is False
        assert result["report"]["inflated"] is False
        assert result["report_news"]["type"] == (
            "costofquality_verdict")
        assert "every route answered" in result["screen"]
        report = agent.get_costofquality_report(
            "cost-2026-11")
        assert report.entry == "release-1"
        assert [r.book for r in
                agent.costofquality_reports()] == [
            "cost-2026-11"]
        assert len(_cq_records(
            store, session_id, "costofquality_verdict")) == 1
        agent.close()

    def test_report_unshared_state_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared"):
            agent.prepare_costofquality_report(
                "cost-2026-11", "release-1", "x",
                "2026-11-13", 3, 9, 12,
                claims=("benchmark_ref",), state="executed")
        assert agent.costofquality_reports() == []
        assert _cq_records(
            store, session_id, "costofquality_verdict") == []
        agent.close()

    def test_duplicate_report_refuses(self, agent):
        agent.prepare_costofquality_report(
            "cost-2026-11", "release-1",
            "every route answered", "2026-11-13", 3, 9, 12,
            claims=("benchmark_ref",))
        with pytest.raises(ValueError, match="cost-2026-11"):
            agent.prepare_costofquality_report(
                "cost-2026-11", "release-2",
                "a second telling", "2026-11-13", 3, 9, 12,
                claims=("benchmark_ref",))
        with pytest.raises(ValueError,
                           match="holds no"):
            agent.get_costofquality_report("cost-2026-12")


class TestCostOfQualityParseArgs:
    def test_parse_args_well(self):
        assert parse_costofquality_args("") == (
            "show", None, (), None)
        assert parse_costofquality_args(None) == (
            "show", None, (), None)
        assert parse_costofquality_args("routes") == (
            "routes", None, (), None)
        assert parse_costofquality_args(
            "route Q-01") == (
            "route", "Q-01", (), None)
        assert parse_costofquality_args(
            "record Q-01") == (
            "record", "Q-01", (), None)
        assert parse_costofquality_args(
            "standing Q-02") == (
            "standing", "Q-02", (), None)
        assert parse_costofquality_args("report") == (
            "reports", None, (), None)
        assert parse_costofquality_args(
            "report cost-2026-11") == (
            "report", "cost-2026-11", (), None)
        assert parse_costofquality_args("verdict") == (
            "verdict", None, (), None)
        assert parse_costofquality_args("index") == (
            "index", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "route", "record",
                    "record Q-01 extra",
                    "routes now", "standing",
                    "report a b"):
            with pytest.raises(ValueError) as caught:
                parse_costofquality_args(bad)
            assert str(caught.value) == COSTOFQUALITY_USAGE


class TestCostOfQualityTerminalRoad:
    def test_show_routes_route_record_standing_report_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/costofquality")
        assert "Q-01" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/costofquality routes")
        assert "local-free-route" in text
        assert "Q-03" in text
        _, _, text = _slash(
            agent, "/costofquality route Q-01")
        assert "local-free-route" in text
        _, _, text = _slash(
            agent, "/costofquality record Q-01")
        assert "holds no" in text
        _, _, text = _slash(
            agent, "/costofquality standing Q-01")
        assert "Q-01:" in text
        assert "open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/costofquality report")
        assert "none held" in text
        _, _, text = _slash(agent, "/costofquality verdict")
        assert "Cost-of-quality report stands open" in text
        agent.register_costofquality_record(_cq_record())
        _, _, text = _slash(
            agent, "/costofquality record Q-01")
        assert "held as answered" in text
        _, _, text = _slash(
            agent, "/costofquality standing Q-01")
        assert "held as answered" in text
        _, _, text = _slash(agent, "/costofquality index")
        assert "held as answered" in text
        agent.prepare_costofquality_report(
            "cost-2026-11", "release-1",
            "every route answered", "2026-11-13", 3, 9, 12,
            claims=("benchmark_ref",))
        _, _, text = _slash(
            agent, "/costofquality report cost-2026-11")
        assert "every route answered" in text
        assert "never inflated" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/costofquality [show|routes|"
                "route <route>|"
                "record <route>|"
                "standing <route>|"
                "report [<book>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/costofquality dance party")
        assert text == COSTOFQUALITY_USAGE
        _, _, text = _slash(
            agent, "/costofquality route guess")
        assert "unknown route" in text


@pytest.fixture()
def cq_handler(agent, monkeypatch):
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


def _cq_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestCostOfQualityHandler:
    def test_show_is_default(self, cq_handler, agent):
        cq_handler._handle_costofquality("")
        assert "Q-01" in (
            _cq_published_text(cq_handler))
        assert "local-free-route" in (
            _cq_published_text(cq_handler))

    def test_route_record_and_verdict(
            self, cq_handler, agent):
        cq_handler._handle_costofquality(
            "route Q-01")
        assert "local-free-route" in (
            _cq_published_text(cq_handler))
        agent.register_costofquality_record(_cq_record())
        cq_handler._handle_costofquality(
            "record Q-01")
        assert "held as answered" in (
            _cq_published_text(cq_handler))
        cq_handler._handle_costofquality("verdict")
        assert "Cost-of-quality report stands held" in (
            _cq_published_text(cq_handler))

    def test_bad_grammar_is_published(
            self, cq_handler, agent):
        cq_handler._handle_costofquality("dance party")
        assert COSTOFQUALITY_USAGE in (
            _cq_published_text(cq_handler))
        cq_handler._handle_costofquality("route guess")
        assert "unknown route" in (
            _cq_published_text(cq_handler))


class TestChatScreenRoutingCostOfQuality:
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
        screen.handle_command("/costofquality verdict",
                              _FakeLog())
        assert calls == [("/costofquality", "verdict")]

    def test_chat_screen_help_and_usage_name_the_audit(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/costofquality[/green] - show the "
                "Cost-of-quality report (M-267)") in text
        assert ('"/costofquality": "Usage: '
                "/costofquality | "
                "/costofquality routes") in text


class TestCostOfQualityDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.costofquality_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _CQ_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        _rp = ROOT / "README.md"
        _rb = _rp.read_bytes() if _rp.exists() else None
        verdict = agent.costofquality_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_costofquality_record(_cq_record())
        agent.register_costofquality_record(
            _cq_fresh_for("Q-02", work="cost-2026-11-b"))
        verdict = agent.costofquality_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "Q-01", "Q-02"]
        assert "Cost-of-quality report stands held" in (
            verdict["verdict_text"])
        assert not _rp.exists() or _rp.read_bytes() == _rb

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_costofquality()
        assert report["book"]["schema"] == (
            COST_OF_QUALITY_SCHEMA)
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_costofquality_record(_cq_record())
        report = agent.report_costofquality()
        assert "held as answered" in report["records_text"]
        assert [s["route"] for s in report["standings"]] == [
            "Q-01"]

    def test_routes_for_disposition_and_held_keys(self, agent):
        agent.register_costofquality_record(_cq_record())
        agent.register_costofquality_record(
            _cq_fresh_for("Q-02", work="cost-2026-11-b"))
        agent.register_costofquality_record(_cq_record(
            route="Q-03", work="cost-2026-11-c",
            disposition="ROADED", owner="",
            proof_kind="none",
            stages=["named"], claims=["assertion"]))
        assert [r.work for r in
                agent.routes_for_disposition("PROVEN")] == [
            "cost-2026-11-a", "cost-2026-11-b"]
        assert agent.costofquality_held() == ["Q-01", "Q-02"]
        standing = agent.costofquality_standing(
            "Q-03")
        assert standing.held is False
