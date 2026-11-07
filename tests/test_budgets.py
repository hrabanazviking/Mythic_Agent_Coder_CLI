"""M-107 Budgets as guardrails - pure-layer tests.

TIER: integration

The pure layer is budgets as data: a per-task or
per-session budget with optional limits on tokens,
cost, time and commands (no limit named means
unlimited - no default is invented), a usage
reading in the costs road's own vocabulary, a
mechanical judge (within below 80% of every limit,
warning at or past 80%, exceeded at or past a
limit), a pause report shaped as session news
stating the pause is graceful - never a mid-edit
death - and a registry with deterministic ids.
Nothing here starts a process, runs a command or
spends anything.
"""

import pytest

from mythic_agent.core.budgets import (
    BUDGETS_SLICE,
    BUDGET_DIMENSIONS,
    BUDGET_SCOPES,
    BUDGET_VERDICT_STATUSES,
    PLAIN_EXPLANATION,
    USAGE,
    WARNING_FRACTION,
    Budget,
    BudgetRegistry,
    BudgetUsage,
    BudgetVerdict,
    Usage,
    budget_paused_record,
    budget_report_record,
    build_budget,
    build_usage,
    format_budget,
    format_budget_report,
    format_budgets,
    format_budgets_screen,
    format_verdict,
    judge_budget,
    normalize_budget_id,
    normalize_budget_scope,
    parse_budgets_args,
    validate_budget,
    validate_usage,
)


def _budget(**kwargs):
    kwargs.setdefault("label", "drafting budget")
    kwargs.setdefault("token_limit", 1000)
    return build_budget(kwargs)


def _registry(*budgets):
    registry = BudgetRegistry()
    for budget in budgets:
        registry.register(budget)
    return registry


# -- constants and word readings ---------------------------------------


def test_constants_and_usage():
    assert BUDGETS_SLICE == "M-107"
    assert BUDGET_SCOPES == ("task", "session")
    assert BUDGET_DIMENSIONS == ("tokens", "cost", "time", "commands")
    assert BUDGET_VERDICT_STATUSES == ("within", "warning", "exceeded")
    assert WARNING_FRACTION == 0.8
    assert USAGE.startswith("Usage: /budgets")
    assert "graceful pause" in PLAIN_EXPLANATION
    assert "never a mid-edit death" in PLAIN_EXPLANATION
    assert "unlimited" in PLAIN_EXPLANATION


def test_scope_word_readings():
    assert normalize_budget_scope("task") == "task"
    assert normalize_budget_scope("per-task") == "task"
    assert normalize_budget_scope("PER_TASK") == "task"
    assert normalize_budget_scope("session") == "session"
    assert normalize_budget_scope("Per-Session") == "session"
    assert normalize_budget_id("budget-1") == "budget-1"
    with pytest.raises(ValueError):
        normalize_budget_scope("project")
    with pytest.raises(ValueError):
        normalize_budget_scope(None)
    with pytest.raises(ValueError):
        normalize_budget_id("two words")
    with pytest.raises(ValueError):
        normalize_budget_id("")


# -- the budget itself ---------------------------------------------------


def test_budget_defaults_are_unlimited():
    budget = Budget()
    assert budget.scope == "task"
    assert budget.limits == {
        "tokens": None, "cost": None, "time": None, "commands": None}
    record = budget.to_record()
    assert record["type"] == "budget"
    assert record["slice"] == "M-107"
    assert record["token_limit"] is None


def test_budget_build_spellings():
    budget = build_budget({
        "kind": "per-session", "name": "long session",
        "max_tokens": 500, "cost_usd": 2.5, "minutes": 30,
        "max_commands": 12})
    assert budget.scope == "session"
    assert budget.label == "long session"
    assert budget.token_limit == 500
    assert budget.cost_limit == 2.5
    assert budget.time_limit_seconds == 1800.0
    assert budget.command_limit == 12
    assert budget.display_label == "long session"
    assert Budget(scope="session").display_label == "per-session budget"


def test_budget_time_spellings_agree_or_refuse():
    budget = build_budget({"time": 120, "time_limit_minutes": 2})
    assert budget.time_limit_seconds == 120.0
    with pytest.raises(ValueError):
        build_budget({"time_limit_seconds": 90, "minutes": 2})


def test_budget_conflicting_spellings_refuse():
    with pytest.raises(ValueError):
        build_budget({"token_limit": 100, "max_tokens": 200})
    with pytest.raises(ValueError):
        build_budget({"scope": "task", "kind": "session"})
    same = build_budget({"token_limit": 100, "tokens": 100})
    assert same.token_limit == 100


def test_budget_unknown_keys_and_shapes_refuse():
    with pytest.raises(ValueError):
        build_budget({"token_limit": 100, "surprise": 1})
    with pytest.raises(ValueError):
        build_budget("token_limit=100")
    with pytest.raises(ValueError):
        validate_budget(42)


@pytest.mark.parametrize("field,value", [
    ("token_limit", 0), ("token_limit", -5), ("token_limit", True),
    ("token_limit", 1.5), ("command_limit", 0),
    ("command_limit", False), ("cost_limit", 0), ("cost_limit", -1.0),
    ("cost_limit", True), ("cost_limit", "5"),
    ("time_limit_seconds", 0), ("time_limit_seconds", -30),
])
def test_budget_bad_limits_refuse(field, value):
    with pytest.raises(ValueError):
        Budget(**{field: value})


def test_budget_is_frozen():
    budget = _budget()
    with pytest.raises(Exception):
        budget.token_limit = 5


# -- the usage reading ---------------------------------------------------


def test_usage_build_spellings_and_defaults():
    assert Usage is BudgetUsage
    fresh = build_usage()
    assert fresh.amounts == {
        "tokens": 0, "cost": 0.0, "time": 0.0, "commands": 0}
    usage = build_usage({
        "tokens": 250, "spend": 1.25, "elapsed_minutes": 3,
        "command_count": 7})
    assert usage.tokens_used == 250
    assert usage.cost_used == 1.25
    assert usage.time_used_seconds == 180.0
    assert usage.commands_used == 7
    assert usage.to_record()["type"] == "budget_usage"


@pytest.mark.parametrize("field,value", [
    ("tokens_used", -1), ("tokens_used", True), ("tokens_used", 2.5),
    ("cost_used", -0.5), ("cost_used", False),
    ("time_used_seconds", -1), ("commands_used", -2),
])
def test_usage_bad_amounts_refuse(field, value):
    with pytest.raises(ValueError):
        BudgetUsage(**{field: value})
    with pytest.raises(ValueError):
        validate_usage({"mystery": 1})


# -- the mechanical judge --------------------------------------------------


def test_judge_within_and_no_usage():
    budget = _budget()
    assert judge_budget(budget).status == "within"
    verdict = judge_budget(budget, {"tokens_used": 100})
    assert verdict.status == "within"
    assert verdict.exceeded_dimensions == ()
    assert verdict.warning_dimensions == ()


def test_judge_warning_boundary():
    budget = _budget()
    assert judge_budget(budget, {"tokens_used": 799}).status == "within"
    verdict = judge_budget(budget, {"tokens_used": 800})
    assert verdict.status == "warning"
    assert verdict.warning_dimensions == ("tokens",)
    assert verdict.readings["tokens"] == {
        "used": 800, "limit": 1000, "fraction": 0.8}


@pytest.mark.parametrize("usage,dimension", [
    ({"tokens_used": 1000}, "tokens"),
    ({"cost_used": 5.0}, "cost"),
    ({"time_used_seconds": 600}, "time"),
    ({"commands_used": 10}, "commands"),
])
def test_judge_exceeded_per_dimension(usage, dimension):
    budget = build_budget({
        "token_limit": 1000, "cost_limit": 5.0,
        "time_limit_seconds": 600, "command_limit": 10})
    verdict = judge_budget(budget, usage)
    assert verdict.status == "exceeded"
    assert verdict.exceeded_dimensions == (dimension,)


def test_judge_over_limit_and_multiple_dimensions():
    budget = build_budget({"token_limit": 100, "command_limit": 4})
    verdict = judge_budget(
        budget, {"tokens_used": 250, "commands_used": 4})
    assert verdict.status == "exceeded"
    assert verdict.exceeded_dimensions == ("tokens", "commands")
    record = verdict.to_record()
    assert record["type"] == "budget_verdict"
    assert record["exceeded"] == ["tokens", "commands"]
    assert record["readings"]["tokens"] == {"used": 250, "limit": 100}


def test_judge_unlimited_dimensions_never_pause():
    budget = build_budget({"label": "open", "token_limit": 10})
    verdict = judge_budget(budget, {
        "tokens_used": 5, "cost_used": 99999.0,
        "time_used_seconds": 10 ** 9, "commands_used": 10 ** 6})
    assert verdict.status == "within"
    empty = judge_budget(Budget(), {"tokens_used": 10 ** 9})
    assert empty.status == "within"


def test_verdict_cannot_disagree_with_itself():
    with pytest.raises(ValueError):
        BudgetVerdict(status="exceeded", token_limit=100, tokens_used=10)
    with pytest.raises(ValueError):
        BudgetVerdict(
            status="within", exceeded_dimensions=("tokens",),
            token_limit=100, tokens_used=100)
    with pytest.raises(ValueError):
        BudgetVerdict(status="sideways")


# -- the pause / report records --------------------------------------------


def test_paused_record_shape_and_graceful_words():
    budget = _budget(budget_id="budget-9")
    record = budget_paused_record(budget, {"tokens_used": 1000})
    assert record is not None
    assert record["type"] == "budget_paused"
    assert record["news"] is True
    assert record["slice"] == "M-107"
    assert record["budget_id"] == "budget-9"
    assert record["status"] == "exceeded"
    assert record["exceeded"] == ["tokens"]
    assert record["graceful"] is True
    assert "graceful pause" in record["headline"]
    assert "never a mid-edit death" in record["headline"]
    assert "1000 of 1000 tokens" in record["headline"]
    assert format_budget_report(record) == record["headline"]


def test_paused_record_none_until_exceeded():
    budget = _budget()
    assert budget_paused_record(budget, {"tokens_used": 100}) is None
    assert budget_paused_record(budget, {"tokens_used": 900}) is None


def test_report_record_warning_and_exceeded_roads():
    budget = _budget()
    assert budget_report_record(budget, {"tokens_used": 10}) is None
    warning = budget_report_record(budget, {"tokens_used": 850})
    assert warning["type"] == "budget_report"
    assert warning["status"] == "warning"
    assert warning["warning"] == ["tokens"]
    assert "approaching" in warning["headline"]
    paused = budget_report_record(budget, {"tokens_used": 5000})
    assert paused["type"] == "budget_paused"
    with pytest.raises(ValueError):
        format_budget_report({"type": "something_else"})


# -- the registry ------------------------------------------------------------


def test_registry_deterministic_ids_and_dupes():
    registry = _registry(_budget(), _budget(label="second"))
    held = registry.list_budgets()
    assert [b.budget_id for b in held] == ["budget-1", "budget-2"]
    assert registry.get("budget-2").label == "second"
    with pytest.raises(ValueError):
        registry.register(_budget(budget_id="budget-1"))
    with pytest.raises(KeyError):
        registry.get("budget-99")


def test_registry_ids_skip_supplied_numbers():
    registry = BudgetRegistry()
    registry.register(_budget(budget_id="budget-2"))
    first = registry.register(_budget(label="auto one"))
    second = registry.register(_budget(label="auto two"))
    assert first.budget_id == "budget-1"
    assert second.budget_id == "budget-3"


def test_registry_record_usage_and_check():
    registry = _registry(_budget())
    assert registry.get_usage("budget-1") is None
    assert registry.check("budget-1").status == "within"
    registry.record_usage("budget-1", {"tokens_used": 900})
    assert registry.get_usage("budget-1").tokens_used == 900
    assert registry.check("budget-1").status == "warning"
    assert registry.check(
        "budget-1", {"tokens_used": 1000}).status == "exceeded"
    # Checking with an explicit reading records nothing.
    assert registry.get_usage("budget-1").tokens_used == 900
    assert [v.status for v in registry.list_verdicts()] == ["warning"]
    paused = registry.paused_record("budget-1", {"tokens_used": 1000})
    assert paused["type"] == "budget_paused"
    assert registry.paused_record("budget-1") is None
    with pytest.raises(KeyError):
        registry.record_usage("budget-7", {"tokens_used": 1})


# -- the /budgets surface ------------------------------------------------------


def test_parse_budgets_args():
    assert parse_budgets_args("") == ("show", None)
    assert parse_budgets_args(None) == ("show", None)
    assert parse_budgets_args("show") == ("show", None)
    assert parse_budgets_args("show budget-3") == ("show", "budget-3")
    assert parse_budgets_args("budget-3") == ("show", "budget-3")
    assert parse_budgets_args("check") == ("check", None)
    assert parse_budgets_args("check budget-3") == ("check", "budget-3")
    for bad in ("show a b", "check a b", "two words", "show !!", 42):
        with pytest.raises(ValueError):
            parse_budgets_args(bad)


def test_format_budget_words():
    budget = build_budget({
        "budget_id": "budget-1", "label": "drafting", "scope": "session",
        "token_limit": 1000, "time_limit_seconds": 120})
    line = format_budget(budget)
    assert "budget-1" in line
    assert "per-session budget" in line
    assert "tokens: limit 1000 tokens" in line
    assert "cost: unlimited" in line
    assert "time: limit 120 seconds" in line
    assert "commands: unlimited" in line
    verdict = judge_budget(budget, {"tokens_used": 1000})
    assert "Verdict: exceeded." in format_budget(budget, verdict)


def test_format_budgets_empty_and_registry():
    assert format_budgets() == (
        "Budgets: none. No budget guardrails are held.")
    registry = _registry(_budget())
    registry.record_usage("budget-1", {"tokens_used": 900})
    text = format_budgets(registry)
    assert text.startswith("Budgets: 1 held.")
    assert "budget-1" in text
    assert "Verdict: warning." in text


def test_format_verdict_wordings():
    budget = build_budget({"token_limit": 1000, "cost_limit": 5.0})
    within = format_verdict(budget, {"tokens_used": 10})
    assert within.startswith("Budget verdict: within")
    assert "10 of 1000 tokens" in within
    warning = format_verdict(budget, {"cost_used": 4.5})
    assert warning.startswith("Budget verdict: warning")
    assert "$4.50 of $5.00" in warning
    exceeded = format_verdict(judge_budget(budget, {"tokens_used": 1000}))
    assert exceeded.startswith("Budget verdict: exceeded")
    assert "graceful pause" in exceeded
    assert "never a mid-edit death" in exceeded
    open_line = format_verdict(Budget(), {"tokens_used": 5})
    assert "no limits" in open_line


def test_format_budgets_screen():
    screen = format_budgets_screen(_registry(_budget()))
    assert screen.startswith("Budgets (M-107) - ")
    assert PLAIN_EXPLANATION in screen
    assert "Budgets: 1 held." in screen
    assert screen.rstrip().endswith(USAGE)
