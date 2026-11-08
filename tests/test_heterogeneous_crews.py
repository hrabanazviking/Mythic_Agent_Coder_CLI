"""M-129 Heterogeneous crews - pure-layer tests.

TIER: integration

The pure layer is the crew's heterogeneity as
data: the evidence (assignments - which member
rides which provider on which model, under which
budget - the Part V budgets composed from M-107,
and the usage readings) validated as data, the
shipped example crew plan held in a data file, a
loader that reads a plan from any file, the
verdicts and route states derived mechanically
from the evidence alone and from the shipped Part
II truth - an unknown route, a missing budget,
and a member over budget, the roadmap's three
judgements - a verdict record and a report record
shaped as session news, and a registry. Nothing
here spawns a live crew, calls a real provider,
performs routing or billing or claims a Part VIII
board: heterogeneity is data only, and the
coordinator acts on the verdicts through later
roads.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.budgets import Budget, BudgetUsage
from mythic_agent.core.crew_members import load_casting
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.heterogeneous_crews import (
    HETERO_RESOURCE,
    HETERO_SCHEMA,
    HETERO_SLICE,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_KINDS,
    HeteroAssignment,
    HeteroReading,
    HeteroReport,
    HeteroVerdict,
    HeterogeneousCrew,
    HeterogeneousCrewRegistry,
    RouteState,
    assignment_record,
    build_assignment,
    build_reading,
    build_verdict,
    format_hetero_screen,
    format_kinds,
    format_routes,
    format_verdict,
    format_verdicts,
    judge_hetero,
    load_heterogeneous_crew,
    load_heterogeneous_crew_file,
    normalize_model,
    normalize_provider,
    normalize_verdict_kind,
    parse_hetero_args,
    plain_words,
    reading_record,
    report_plain_words,
    report_record,
    validate_assignment,
    validate_plan,
    validate_reading,
    validate_report,
    validate_verdict,
    verdict_record,
)

ROOT = Path(__file__).resolve().parents[1]


def _casting():
    return load_casting().members


def _assignment(**kwargs):
    kwargs.setdefault("member", "architect")
    kwargs.setdefault("provider", "anthropic")
    kwargs.setdefault("model", "claude-sonnet-4-5")
    kwargs.setdefault("budget_id", "arch-budget")
    return HeteroAssignment(**kwargs)


def _reading(**kwargs):
    kwargs.setdefault("member", "architect")
    kwargs.setdefault("usage", BudgetUsage(tokens_used=10))
    return HeteroReading(**kwargs)


def _budget(**kwargs):
    kwargs.setdefault("budget_id", "arch-budget")
    kwargs.setdefault("label", "Architect budget")
    kwargs.setdefault("scope", "session")
    kwargs.setdefault("token_limit", 200000)
    return Budget(**kwargs)


def _plan_data():
    return {
        "schema": HETERO_SCHEMA, "slice": HETERO_SLICE,
        "keeper": "architect",
        "assignments": [
            {"member": "architect", "provider": "anthropic",
             "model": "claude-sonnet-4-5",
             "budget_id": "arch-budget"},
        ],
        "budgets": [
            {"budget_id": "arch-budget", "label": "Architect budget",
             "scope": "session", "token_limit": 200000},
        ],
        "readings": [
            {"member": "architect", "tokens_used": 10},
        ]}


def _write_plan(tmp_path, data):
    path = tmp_path / "plan.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def _clean_evidence():
    return {
        "assignments": [
            {"member": "architect", "provider": "anthropic",
             "model": "claude-sonnet-4-5",
             "budget_id": "arch-budget"},
            {"member": "forge_worker", "provider": "ollama",
             "model": "llama3.1", "budget_id": "forge-budget"},
        ],
        "budgets": [
            {"budget_id": "arch-budget", "scope": "session",
             "token_limit": 200000},
            {"budget_id": "forge-budget", "scope": "task",
             "token_limit": 40000},
        ],
        "readings": [
            {"member": "architect", "tokens_used": 10},
            {"member": "forge_worker", "tokens_used": 10},
        ]}


# -- constants and word readings --------------------------------------------


def test_constants_and_usage():
    assert HETERO_SLICE == "M-129"
    assert HETERO_SCHEMA == "mythic.heterogeneous_crews/1"
    assert HETERO_RESOURCE == "heterogeneous_crews.yaml"
    assert VERDICT_KINDS == (
        "unknown_route", "missing_budget", "over_budget")
    assert USAGE.startswith("Usage: /hetero")
    assert "routes" in USAGE and "kinds" in USAGE
    assert "different models on different providers" in PLAIN_EXPLANATION
    assert "Claude Architect" in PLAIN_EXPLANATION
    assert "local-LLM Forge Worker" in PLAIN_EXPLANATION
    assert "no Part VIII board" in PLAIN_EXPLANATION
    assert "as data only" in PLAIN_EXPLANATION
    assert "spawns no live crew" in PLAIN_EXPLANATION
    assert "calls no real provider" in PLAIN_EXPLANATION


def test_kind_provider_model_readings_and_refusals():
    assert normalize_verdict_kind("route") == "unknown_route"
    assert normalize_verdict_kind("Unknown-Route") == "unknown_route"
    assert normalize_verdict_kind("budget") == "missing_budget"
    assert normalize_verdict_kind("UNBUDGETED") == "missing_budget"
    assert normalize_verdict_kind("over") == "over_budget"
    assert normalize_verdict_kind("Exceeded") == "over_budget"
    for bad in ("stall", "blocked", "", None, 3):
        with pytest.raises(ValueError):
            normalize_verdict_kind(bad)
    # Provider readings are the M-019 registry's, aliases included.
    assert normalize_provider("anthropic") == "anthropic"
    assert normalize_provider("Claude") == "anthropic"
    assert normalize_provider("LOCAL") == "ollama"
    assert normalize_provider("gpt") == "openai"
    for bad in ("not-a-provider", "", None, 4):
        with pytest.raises(ValueError):
            normalize_provider(bad)
    assert normalize_model("llama3.1") == "llama3.1"
    assert normalize_model(
        "meta-llama/Llama-3.3-70B") == "meta-llama/Llama-3.3-70B"
    for bad in ("", "   ", None, 5, "x" * 201):
        with pytest.raises(ValueError):
            normalize_model(bad)


# -- the evidence records ----------------------------------------------------


def test_assignment_and_reading_construction_and_records():
    assignment = _assignment()
    record = assignment.to_record()
    assert record["type"] == "hetero_assignment"
    assert record["slice"] == "M-129"
    assert record["provider"] == "anthropic"
    assert record["budget_id"] == "arch-budget"
    # The provider word on construction is the registry reading.
    assert _assignment(provider="claude").provider == "anthropic"
    reading = _reading()
    assert reading.usage.tokens_used == 10
    reading_dict = reading.to_record()
    assert reading_dict["type"] == "hetero_reading"
    assert reading_dict["tokens_used"] == 10
    assert reading_dict["cost_used"] == 0.0
    news = assignment_record(assignment)
    assert news["news"] is True
    assert news["headline"] == \
        "architect rides claude-sonnet-4-5 on anthropic."
    news = reading_record(reading)
    assert news["news"] is True
    assert "10 tokens" in news["headline"]


def test_evidence_refusals():
    with pytest.raises(ValueError):
        _assignment(member="bad member")
    with pytest.raises(ValueError):
        _assignment(provider="not-a-provider")
    with pytest.raises(ValueError):
        _assignment(model="")
    with pytest.raises(ValueError):
        _assignment(budget_id="bad budget!")
    with pytest.raises(ValueError):
        _reading(member="")
    with pytest.raises(ValueError):
        _reading(usage=BudgetUsage(tokens_used=-1))


def test_evidence_validator_aliases_and_refusals():
    assignment = validate_assignment(
        {"member_id": "architect", "provider_name": "claude",
         "model_name": "claude-sonnet-4-5", "budget": "arch-budget",
         "id": "assignment-9"})
    assert assignment.member == "architect"
    assert assignment.provider == "anthropic"
    assert assignment.assignment_id == "assignment-9"
    assert build_assignment(assignment) is assignment
    assert build_assignment(
        member="architect", provider="anthropic",
        model="claude-sonnet-4-5",
        budget_id="arch-budget") == _assignment()
    with pytest.raises(ValueError):
        validate_assignment(
            {"member": "architect", "member_id": "scribe",
             "provider": "anthropic", "model": "claude-sonnet-4-5"})
    with pytest.raises(ValueError):
        validate_assignment(
            {"member": "architect", "provider": "anthropic",
             "model": "claude-sonnet-4-5", "surprise": 1})
    with pytest.raises(ValueError):
        validate_assignment({"member": "architect"})
    with pytest.raises(ValueError):
        validate_assignment("not an assignment")
    reading = validate_reading(
        {"member_id": "architect", "tokens": 42,
         "id": "reading-9"})
    assert reading.usage.tokens_used == 42
    assert reading.reading_id == "reading-9"
    reading = validate_reading(
        {"member": "architect", "usage": {"cost_used": 1.5}})
    assert reading.usage.cost_used == 1.5
    assert build_reading(reading) is reading
    assert build_reading(
        member="architect", tokens_used=3).usage.tokens_used == 3
    with pytest.raises(ValueError):
        validate_reading(
            {"member": "architect", "usage": {"tokens_used": 1},
             "tokens_used": 1})
    with pytest.raises(ValueError):
        validate_reading(
            {"member": "architect", "tokens_used": 1,
             "tokens": 2})
    with pytest.raises(ValueError):
        validate_reading({"tokens_used": 1})


# -- the shipped example plan --------------------------------------------------


def test_shipped_plan_loads_as_the_example():
    plan = load_heterogeneous_crew()
    assert plan.keeper == "architect"
    assert len(plan.assignments) == 4
    assert len(plan.budgets) == 2
    assert len(plan.readings) == 2
    assert [(a.member, a.provider) for a in plan.assignments] == [
        ("architect", "anthropic"), ("forge_worker", "ollama"),
        ("scribe", "openai"), ("cartographer", "ollama"),
    ]
    # The budgets are the shipped M-107 budgets, composed.
    assert all(isinstance(b, Budget) for b in plan.budgets)
    assert plan.budget_for("forge-budget").token_limit == 40000
    with pytest.raises(KeyError):
        plan.budget_for("scribe-budget")
    assert [r.member for r in plan.readings_for("architect")] == [
        "architect"]
    # Every member named is a shipped member.
    member_ids = {m.member_id for m in _casting()}
    for assignment in plan.assignments:
        assert assignment.member in member_ids
    for reading in plan.readings:
        assert reading.member in member_ids
    assert validate_plan(
        yaml.safe_load(
            (ROOT / "mythic_agent" / "data" / HETERO_RESOURCE)
            .read_text(encoding="utf-8")),
        require_example=True) == []


def test_shipped_example_check_refuses_drift():
    data = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / HETERO_RESOURCE)
        .read_text(encoding="utf-8"))
    data["assignments"][0]["model"] = "claude-opus-4-1"
    problems = validate_plan(data, require_example=True)
    assert any("exactly the four assignments" in p for p in problems)
    # The same file is a well-formed plan without the check.
    assert validate_plan(data) == []
    data = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / HETERO_RESOURCE)
        .read_text(encoding="utf-8"))
    data["keeper"] = "scribe"
    problems = validate_plan(data, require_example=True)
    assert any("kept by the architect" in p for p in problems)


def test_example_plan_yields_exactly_three_verdicts():
    plan = load_heterogeneous_crew()
    report = plan.report()
    assert [v.kind for v in report.verdicts] == [
        "unknown_route", "missing_budget", "over_budget"]
    unknown, missing, over = report.verdicts
    assert (unknown.member, unknown.model) == (
        "cartographer", "llama9.9")
    assert (missing.member, missing.provider) == ("scribe", "openai")
    assert (over.member, over.provider) == ("forge_worker", "ollama")
    # Heterogeneous across providers, models and localities.
    assert report.heterogeneous is True
    assert report.providers == ("anthropic", "ollama", "openai")
    assert set(report.localities) == {"local", "remote"}
    architect = report.route_for("architect")
    assert architect.locality == "remote"
    assert architect.context_tokens == 200000
    assert architect.budget_status == "within"
    forge = report.route_for("forge_worker")
    assert forge.is_local is True
    assert forge.context_tokens == 131072
    assert forge.budget_status == "exceeded"
    scribe = report.route_for("scribe")
    assert scribe.switchable is True
    assert scribe.budget_status == "unbudgeted"
    cartographer = report.route_for("cartographer")
    # M-027 truth: an unlisted model's context is unknown.
    assert cartographer.context_tokens is None
    assert report.is_clean is False
    assert validate_report(plan, report) == []
    with pytest.raises(KeyError):
        report.route_for("polymath")


# -- the judge -------------------------------------------------------------------


def test_clean_evidence_yields_no_verdicts():
    evidence = _clean_evidence()
    assert judge_hetero(evidence) == ()
    plan = HeterogeneousCrew(
        assignments=[build_assignment(a)
                     for a in evidence["assignments"]],
        budgets=[_budget(), Budget(
            budget_id="forge-budget", scope="task",
            token_limit=40000)],
        readings=[build_reading(r) for r in evidence["readings"]],
        keeper="architect")
    report = plan.report()
    assert report.is_clean is True
    assert report.heterogeneous is True
    assert report.route_for("architect").budget_status == "within"
    assert validate_report(evidence, report) == []
    # The same evidence always yields the same verdicts.
    assert judge_hetero(evidence) == judge_hetero(evidence)


def test_unknown_route_verdict_and_precedence():
    evidence = _clean_evidence()
    evidence["assignments"][1]["model"] = "llama9.9"
    evidence["assignments"][1]["budget_id"] = "no-such-budget"
    verdicts = judge_hetero(evidence)
    # Route precedence: one verdict for the assignment,
    # the unknown route, never also a missing budget.
    assert [v.kind for v in verdicts] == ["unknown_route"]
    assert "llama3.1, llama3.2" in verdicts[0].detail


def test_missing_budget_verdicts():
    evidence = _clean_evidence()
    evidence["assignments"][0]["budget_id"] = "ghost-budget"
    del evidence["assignments"][1]["budget_id"]
    verdicts = judge_hetero(evidence)
    assert [v.kind for v in verdicts] == [
        "missing_budget", "missing_budget"]
    assert "ghost-budget" in verdicts[0].detail
    assert "no budget" in verdicts[1].detail


def test_over_budget_and_warning_is_no_verdict():
    evidence = _clean_evidence()
    evidence["readings"][1]["tokens_used"] = 45000
    verdicts = judge_hetero(evidence)
    assert [v.kind for v in verdicts] == ["over_budget"]
    assert "exceeded on tokens" in verdicts[0].detail
    # At 85% of the limit the M-107 judge warns; a
    # warning is a route standing, not a verdict.
    evidence["readings"][1]["tokens_used"] = 34000
    assert judge_hetero(evidence) == ()
    plan = HeterogeneousCrew(
        assignments=[build_assignment(a)
                     for a in evidence["assignments"]],
        budgets=[_budget(), Budget(
            budget_id="forge-budget", scope="task",
            token_limit=40000)],
        readings=[build_reading(r) for r in evidence["readings"]],
        keeper="architect")
    assert plan.report().route_for(
        "forge_worker").budget_status == "warning"


def test_reading_for_unassigned_member_is_ignored():
    evidence = _clean_evidence()
    evidence["readings"].append(
        {"member": "polymath", "tokens_used": 999999})
    assert judge_hetero(evidence) == ()


def test_homogeneous_crews_are_not_heterogeneous():
    evidence = {
        "assignments": [
            {"member": "architect", "provider": "anthropic",
             "model": "claude-sonnet-4-5"},
            {"member": "auditor", "provider": "anthropic",
             "model": "claude-sonnet-4-5"},
        ], "budgets": [], "readings": []}
    plan = HeterogeneousCrew(
        assignments=[build_assignment(a)
                     for a in evidence["assignments"]],
        keeper="architect")
    report = plan.report()
    assert report.heterogeneous is False
    assert report.providers == ("anthropic",)
    assert report.localities == ("remote",)


# -- verdicts, route states and reports -------------------------------------------


def test_verdict_and_route_state_validation():
    verdict = HeteroVerdict(
        kind="route", member="scribe", provider="openai",
        model="gpt-5", title="A title", detail="A detail")
    assert verdict.kind == "unknown_route"
    record = verdict.to_record()
    assert record["type"] == "hetero_verdict"
    assert record["slice"] == "M-129"
    fields = {key: record[key] for key in (
        "kind", "member", "provider", "model", "title", "detail")}
    assert validate_verdict(fields) == verdict
    assert build_verdict(verdict) is verdict
    with pytest.raises(ValueError):
        validate_verdict(
            {"kind": "unknown_route", "member": "scribe"})
    with pytest.raises(ValueError):
        HeteroVerdict(
            kind="stall", member="scribe", provider="openai",
            model="gpt-5", title="T", detail="D")
    route = RouteState(
        member="architect", provider="anthropic",
        model="claude-sonnet-4-5", locality="remote",
        dialect="native_sdk", switchable=False,
        context_tokens=200000, budget_id="arch-budget",
        budget_status="within")
    assert route.to_record()["type"] == "hetero_route"
    # Route truth is the registry's: a wrong locality,
    # dialect or switchable reading refuses.
    with pytest.raises(ValueError):
        RouteState(
            member="architect", provider="anthropic",
            model="claude-sonnet-4-5", locality="local",
            dialect="native_sdk", switchable=False)
    with pytest.raises(ValueError):
        RouteState(
            member="architect", provider="anthropic",
            model="claude-sonnet-4-5", locality="remote",
            dialect="native_sdk", switchable=True)
    with pytest.raises(ValueError):
        RouteState(
            member="architect", provider="anthropic",
            model="claude-sonnet-4-5", locality="remote",
            dialect="native_sdk", budget_status="rich")


def test_report_validation_names_a_wrong_report():
    evidence = _clean_evidence()
    plan = load_heterogeneous_crew()
    problems = validate_report(evidence, plan.report())
    assert len(problems) == 1
    assert "does not hold exactly" in problems[0]
    assert validate_report(evidence, "not a report") == [
        "a hetero report is needed, got 'not a report'"]


def test_plan_construction_and_mapping_refusals():
    with pytest.raises(ValueError):
        HeterogeneousCrew(assignments=[], keeper="architect")
    with pytest.raises(ValueError):
        HeterogeneousCrew(
            assignments=[_assignment(), _assignment()],
            keeper="architect")
    with pytest.raises(ValueError):
        HeterogeneousCrew(
            assignments=[_assignment()],
            budgets=[_budget(), _budget()], keeper="architect")
    with pytest.raises(ValueError):
        HeterogeneousCrew(
            assignments=[_assignment()],
            budgets=[Budget(scope="task", token_limit=5)],
            keeper="architect")
    with pytest.raises(ValueError):
        HeterogeneousCrew(
            assignments=[_assignment()],
            readings=[_reading(), _reading()], keeper="architect")
    data = _plan_data()
    data["schema"] = "mythic.other/1"
    assert any("schema" in p for p in validate_plan(data))
    data = _plan_data()
    data["surprise"] = 1
    assert any("unknown crew plan keys" in p
               for p in validate_plan(data))
    data = _plan_data()
    data["assignments"].append(dict(data["assignments"][0]))
    assert any("assigned twice" in p for p in validate_plan(data))
    with pytest.raises(ValidationError):
        load_heterogeneous_crew(_plan_data())


def test_plan_file_roundtrip_and_refusals(tmp_path):
    plan = load_heterogeneous_crew_file(
        _write_plan(tmp_path, _plan_data()))
    assert plan.keeper == "architect"
    assert len(plan.assignments) == 1
    assert plan.report().is_clean is True
    with pytest.raises(FileNotFoundError):
        load_heterogeneous_crew_file(tmp_path / "missing.yaml")
    bad = _plan_data()
    bad["assignments"][0]["provider"] = "not-a-provider"
    with pytest.raises(ValidationError):
        load_heterogeneous_crew_file(_write_plan(tmp_path, bad))


# -- the registry -------------------------------------------------------------------


def test_registry_deterministic_ids_and_refusals():
    registry = HeterogeneousCrewRegistry()
    budget = registry.register_budget(_budget())
    assert budget.budget_id == "arch-budget"
    with pytest.raises(ValueError):
        registry.register_budget(_budget())
    with pytest.raises(ValueError):
        registry.register_budget(Budget(scope="task"))
    first = registry.register_assignment(_assignment())
    assert first.assignment_id == "assignment-1"
    named = registry.register_assignment(_assignment(
        assignment_id="assignment-3", member="scribe",
        provider="openai", model="gpt-5", budget_id=None))
    assert named.assignment_id == "assignment-3"
    skipped = registry.register_assignment(_assignment(
        member="auditor", provider="anthropic",
        model="claude-opus-4-1", budget_id=None))
    assert skipped.assignment_id == "assignment-2"
    with pytest.raises(ValueError):
        registry.register_assignment(_assignment())
    reading = registry.register_reading(_reading())
    assert reading.reading_id == "reading-1"
    with pytest.raises(ValueError):
        registry.register_reading(_reading())
    assert registry.get_assignment("assignment-1").member == "architect"
    assert registry.get_reading("reading-1").member == "architect"
    assert registry.get_budget("arch-budget").scope == "session"
    with pytest.raises(KeyError):
        registry.get_assignment("assignment-9")
    with pytest.raises(KeyError):
        registry.get_budget("nope")


def test_registry_holds_a_plan_and_judges_it():
    registry = HeterogeneousCrewRegistry()
    assignments, budgets, readings = registry.register_plan(
        load_heterogeneous_crew())
    assert len(assignments) == 4
    assert len(budgets) == 2
    assert len(readings) == 2
    assert [a.assignment_id for a in assignments] == [
        f"assignment-{n}" for n in range(1, 5)]
    assert [v.kind for v in registry.verdicts()] == [
        "unknown_route", "missing_budget", "over_budget"]
    assert registry.report().heterogeneous is True
    assert [v.kind for v in registry.for_member("scribe")] == [
        "missing_budget"]
    assert validate_report(registry, registry.report()) == []


# -- records, formatters and the parser ----------------------------------------------


def test_records_and_plain_words():
    plan = load_heterogeneous_crew()
    report = plan.report()
    verdict = report.verdicts[0]
    assert plain_words(verdict).startswith(verdict.title + " - ")
    record = verdict_record(verdict)
    assert record["news"] is True
    assert record["headline"] == plain_words(verdict)
    whole = report_record(report)
    assert whole["type"] == "hetero_report"
    assert whole["count"] == 3
    assert whole["heterogeneous"] is True
    assert len(whole["verdicts"]) == 3
    assert len(whole["routes"]) == 4
    assert "3 verdicts stand" in report_plain_words(report)
    clean = HeteroReport()
    assert "crew plan is clean" in report_plain_words(clean)


def test_formatters():
    text = format_verdicts()
    assert "Heterogeneous crews: 3 verdicts stand" in text
    assert "unknown_route" in text
    assert format_verdict(load_heterogeneous_crew(
    ).report().verdicts[1]).startswith("  missing_budget:")
    routes = format_routes()
    assert "architect: claude-sonnet-4-5 on anthropic" in routes
    assert "context unknown" in routes
    assert "Verdict kinds: unknown_route" in format_kinds()
    screen = format_hetero_screen()
    assert screen.startswith("Heterogeneous crews (M-129)")
    assert USAGE in screen
    assert format_verdicts([]) == (
        "Heterogeneous crews: clean. No unknown route, "
        "missing budget or over-budget member stands.")
    assert format_routes(
        HeteroReport()) == "Crew routes: no assignment is held yet."


def test_parser():
    assert parse_hetero_args("") == ("show", None)
    assert parse_hetero_args(None) == ("show", None)
    assert parse_hetero_args("show") == ("show", None)
    assert parse_hetero_args("verdicts") == ("show", None)
    assert parse_hetero_args("show scribe") == ("show", "scribe")
    assert parse_hetero_args("scribe") == ("show", "scribe")
    assert parse_hetero_args("routes") == ("routes", None)
    assert parse_hetero_args("kinds") == ("kinds", None)
    for bad in ("show a b", "routes now", "kinds x", 5):
        with pytest.raises(ValueError):
            parse_hetero_args(bad)


def test_module_purity():
    source = (
        ROOT / "mythic_agent" / "core" / "heterogeneous_crews.py"
    ).read_text(encoding="utf-8")
    assert "subprocess" not in source
    assert "Popen" not in source
    assert "os.system" not in source
    assert "agents.llm" not in source
    assert "import os" not in source


# -- agent layer -----------------------------------------------------------
#
# M-129 agent layer: the agent holds a
# HeterogeneousCrewRegistry for the session
# (session state only, no new setting), a plan is
# recorded by being registered - published as its
# assignment_record / reading_record session news
# through the checkpoint road, deduped per
# evidence id (the budgets are the M-107 layer's
# own records and are held without news) - the
# verdicts are published as verdict_record session
# news and the report as ONE report_record session
# event holding every verdict and route, deduped
# per report, and the /hetero surface rides both
# roads on the pure parser + formatters. Status,
# find, plan and report reads register and publish
# nothing. This layer spawns no live crew, calls
# no real provider, performs no routing or billing
# and builds no board - Part VIII does not exist
# yet, so the screen is where the verdicts are
# visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _hetero_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


class TestHeteroAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.hetero_status()
        assert status["assignments"] == []
        assert status["budgets"] == []
        assert status["readings"] == []
        assert status["plan"]["keeper"] == "architect"
        assert len(status["plan"]["assignments"]) == 4
        assert len(status["plan"]["budgets"]) == 2
        assert len(status["plan"]["readings"]) == 2
        assert status["report"]["type"] == "hetero_report"
        assert status["report"]["count"] == 3
        assert status["report"]["heterogeneous"] is True
        assert "Heterogeneous crews: 3 verdicts stand" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert agent._hetero_crew_registry() is \
            agent._hetero_crew_registry()
        assert agent._hetero_crew_store is \
            agent._hetero_crew_registry()

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.hetero_status()
        found = agent.find_hetero_verdicts("scribe")
        assert [v.kind for v in found] == ["missing_budget"]
        assert agent.heterogeneous_crew().keeper == "architect"
        report = agent.hetero_report()
        assert [v.kind for v in report.verdicts] == [
            "unknown_route", "missing_budget", "over_budget"]
        registry = agent._hetero_crew_registry()
        assert registry.list_assignments() == ()
        assert registry.list_budgets() == ()
        assert registry.list_readings() == ()
        for kind in ("hetero_assignment", "hetero_reading",
                     "hetero_verdict", "hetero_report"):
            assert _hetero_events(store, session_id, kind) == []
        agent.close()

    def test_unheld_evidence_raises_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.get_hetero_assignment("assignment-1")
        with pytest.raises(KeyError):
            agent.get_hetero_budget("arch-budget")
        with pytest.raises(KeyError):
            agent.get_hetero_reading("reading-1")

    def test_find_unknown_member_raises_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.find_hetero_verdicts("nobody")

    def test_status_after_register_shows_the_held_evidence(
            self, agent):
        agent.register_hetero_budget(_budget())
        agent.register_hetero_assignment(_assignment())
        status = agent.hetero_status()
        assert [a["member"] for a in status["assignments"]] == [
            "architect"]
        assert [b["budget_id"] for b in status["budgets"]] == [
            "arch-budget"]
        assert "Heterogeneous crews: clean." in status["screen"]
        assert len(status["plan"]["assignments"]) == 4


class TestHeteroAgentRegister:
    def test_register_assignment_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_hetero_assignment(_assignment())
        assert outcome["assignment"]["member"] == "architect"
        assert outcome["assignment"]["assignment_id"] == "assignment-1"
        assert outcome["record"]["type"] == "hetero_assignment"
        assert outcome["record"]["news"] is True
        assert agent.get_hetero_assignment(
            "assignment-1").provider == "anthropic"
        events = _hetero_events(store, session_id, "hetero_assignment")
        assert len(events) == 1
        assert events[0]["member"] == "architect"
        # Deduped per assignment id: no second event.
        agent._publish_hetero_record(outcome["record"])
        assert len(_hetero_events(
            store, session_id, "hetero_assignment")) == 1
        # Foreign record types are never published on these roads.
        agent._publish_hetero_record(
            {"type": "crew_delegation", "assignment_id": "assignment-9"})
        agent._publish_hetero_record(
            {"type": "hetero_verdict", "reading_id": "reading-9"})
        agent._publish_hetero_verdict_record(
            {"type": "hetero_report", "verdicts": []})
        agent._publish_hetero_report_record(
            {"type": "hetero_verdict", "verdicts": [], "routes": []})
        assert len(_hetero_events(
            store, session_id, "hetero_assignment")) == 1
        assert _hetero_events(store, session_id, "hetero_reading") == []
        assert _hetero_events(store, session_id, "hetero_verdict") == []
        assert _hetero_events(store, session_id, "hetero_report") == []
        agent.close()

    def test_register_reading_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_hetero_reading(_reading())
        assert outcome["reading"]["member"] == "architect"
        assert outcome["reading"]["reading_id"] == "reading-1"
        assert outcome["record"]["type"] == "hetero_reading"
        assert outcome["record"]["news"] is True
        assert agent.get_hetero_reading(
            "reading-1").usage.tokens_used == 10
        events = _hetero_events(store, session_id, "hetero_reading")
        assert len(events) == 1
        assert events[0]["member"] == "architect"
        agent.close()

    def test_register_budget_holds_without_news(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_hetero_budget(_budget())
        assert outcome["budget"]["budget_id"] == "arch-budget"
        assert agent.get_hetero_budget(
            "arch-budget").token_limit == 200000
        # Budgets are the M-107 layer's own records:
        # holding one publishes no session news here.
        assert _hetero_events(store, session_id, "budget") == []
        assert _hetero_events(
            store, session_id, "hetero_assignment") == []
        agent.close()

    def test_record_plan_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_heterogeneous_crew()
        assert outcome["count"] == 8
        assert [a["assignment_id"] for a in outcome["assignments"]] == \
            [f"assignment-{n}" for n in range(1, 5)]
        assert [r["reading_id"] for r in outcome["readings"]] == \
            [f"reading-{n}" for n in range(1, 3)]
        assert [b["budget_id"] for b in outcome["budgets"]] == [
            "arch-budget", "forge-budget"]
        assert agent.get_hetero_assignment(
            "assignment-1").member == "architect"
        assert agent.get_hetero_reading(
            "reading-1").member == "architect"
        status = agent.hetero_status()
        assert len(status["assignments"]) == 4
        assert len(status["budgets"]) == 2
        assert len(status["readings"]) == 2
        assert [v.kind for v in agent.hetero_report().verdicts] == [
            "unknown_route", "missing_budget", "over_budget"]
        assert len(_hetero_events(
            store, session_id, "hetero_assignment")) == 4
        assert len(_hetero_events(
            store, session_id, "hetero_reading")) == 2
        agent.close()

    def test_record_same_plan_twice_refuses(self, agent):
        agent.record_heterogeneous_crew()
        with pytest.raises(ValueError):
            agent.record_heterogeneous_crew()
        registry = agent._hetero_crew_registry()
        assert len(registry.list_assignments()) == 4
        assert len(registry.list_readings()) == 2

    def test_plan_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        outcome = agent.record_heterogeneous_crew(
            load_heterogeneous_crew_file(
                _write_plan(tmp_path, _plan_data())))
        assert outcome["count"] == 3
        assert agent.get_hetero_assignment(
            "assignment-1").member == "architect"
        assert agent.heterogeneous_crew().keeper == "architect"
        assert agent.hetero_report().is_clean is True

    def test_find_prefers_the_held_evidence(self, agent):
        agent.register_hetero_assignment(_assignment(
            member="scribe", provider="ollama", model="llama9.9",
            budget_id=None))
        found = agent.find_hetero_verdicts("scribe")
        assert [v.kind for v in found] == ["unknown_route"]
        # Held session, member held in no held verdict: KeyError,
        # no silent fall back to the example plan - the
        # forge_worker is in the example's over-budget verdict.
        with pytest.raises(KeyError):
            agent.find_hetero_verdicts("forge_worker")


class TestHeteroAgentReport:
    def test_report_publishes_one_report_event_for_all_verdicts(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.record_heterogeneous_crew()
        outcome = agent.report_hetero()
        assert outcome["count"] == 3
        assert outcome["record"]["type"] == "hetero_report"
        assert outcome["record"]["count"] == 3
        assert "Heterogeneous crews: 3 verdicts stand" in \
            outcome["screen"]
        verdicts = _hetero_events(store, session_id, "hetero_verdict")
        assert len(verdicts) == 3
        reports = _hetero_events(store, session_id, "hetero_report")
        # ONE report event holds all three verdicts.
        assert len(reports) == 1
        assert reports[0]["count"] == 3
        assert len(reports[0]["verdicts"]) == 3
        assert len(reports[0]["routes"]) == 4
        # Reporting again on the same evidence publishes
        # nothing new.
        agent.report_hetero()
        assert len(_hetero_events(
            store, session_id, "hetero_verdict")) == 3
        assert len(_hetero_events(
            store, session_id, "hetero_report")) == 1
        # Newly held evidence grows the report: a new report.
        agent.register_hetero_assignment(_assignment(
            member="polymath", provider="ollama", model="llama9.9",
            budget_id=None))
        outcome = agent.report_hetero()
        assert outcome["count"] == 4
        assert len(_hetero_events(
            store, session_id, "hetero_report")) == 2
        agent.close()

    def test_report_with_clean_evidence_publishes_a_clean_report_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_hetero_budget(_budget())
        agent.register_hetero_assignment(_assignment())
        outcome = agent.report_hetero()
        assert outcome["count"] == 0
        assert outcome["record"]["clean"] is True
        assert outcome["screen"].startswith(
            "Heterogeneous crews: clean.")
        assert _hetero_events(store, session_id, "hetero_verdict") == []
        reports = _hetero_events(store, session_id, "hetero_report")
        assert len(reports) == 1
        assert reports[0]["clean"] is True
        agent.report_hetero()
        assert len(_hetero_events(
            store, session_id, "hetero_report")) == 1
        agent.close()

    def test_no_spawn_or_provider_road_for_hetero(self, agent):
        # This layer holds the crew as data: it spawns
        # no live crew, calls no real provider,
        # performs no routing or billing and builds no
        # board - Part VIII does not exist yet.
        assert not hasattr(agent, "spawn_hetero_crew")
        assert not hasattr(agent, "call_provider")
        assert not hasattr(agent, "hetero_board")


class TestHeteroTerminalSurface:
    def test_show_routes_and_kinds(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/hetero")
        assert "Heterogeneous crews: 3 verdicts stand" in text
        _, _, text = _slash(agent, "/hetero show scribe")
        assert "Heterogeneous crews: 1 verdicts stand" in text
        assert "missing_budget" in text
        _, _, text = _slash(agent, "/hetero routes")
        assert "architect: claude-sonnet-4-5 on anthropic " \
            "(remote, context 200000); budget within." in text
        _, _, text = _slash(agent, "/hetero kinds")
        assert text.startswith("Verdict kinds:")

    def test_bare_member_shows_theirs(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/hetero forge_worker")
        assert "over_budget" in text
        _, _, text = _slash(agent, "/hetero cartographer")
        assert "unknown_route" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert "/hetero [show|show <member>|routes|kinds]" in text
        _, _, text = _slash(agent, "/hetero dance")
        assert "no verdict stands on the member" in text
        _, _, text = _slash(agent, "/hetero dance party")
        assert text == USAGE


@pytest.fixture()
def hetero_handler(agent, monkeypatch):
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


def _hetero_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestHeteroCommand:
    def test_show_is_default(self, hetero_handler, agent):
        hetero_handler._handle_hetero("")
        assert "Heterogeneous crews: 3 verdicts stand" in \
            _hetero_published_text(hetero_handler)

    def test_show_one_routes_and_kinds(self, hetero_handler, agent):
        hetero_handler._handle_hetero("show scribe")
        assert "missing_budget" in _hetero_published_text(hetero_handler)
        hetero_handler._handle_hetero("routes")
        assert "budget exceeded" in \
            _hetero_published_text(hetero_handler)
        hetero_handler._handle_hetero("kinds")
        assert "Verdict kinds:" in _hetero_published_text(hetero_handler)

    def test_bad_grammar_is_published(self, hetero_handler, agent):
        hetero_handler._handle_hetero("dance party")
        assert USAGE in _hetero_published_text(hetero_handler)


class TestChatScreenRoutingHetero:
    def test_hetero_routes_as_system_command(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import MainChatScreen

        class _FakeLog:
            def __init__(self):
                self.lines = []

            def write(self, *args, **kwargs):
                self.lines.append(" ".join(str(a) for a in args))

        calls = []
        monkeypatch.setattr(
            chat_screen.SecureAPI, "publish_system_command",
            staticmethod(lambda cmd, args: calls.append((cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        screen.handle_command("/hetero kinds", _FakeLog())
        assert calls == [("/hetero", "kinds")]
