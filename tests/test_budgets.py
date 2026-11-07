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

# -- agent layer: budgets held for a session (M-107) -------------------

import copy as _copy

from mythic_agent.core.sessions import SessionStore


class _OfflineMemoryBudgets:
    def __init__(self):
        self.archived = []

    def search(self, query, top_k=2):
        return []

    def insert(self, text, metadata=None):
        self.archived.append(text)


@pytest.fixture()
def budget_agent(tmp_path, monkeypatch):
    from mythic_agent.agents import llm
    from mythic_agent.core.secure_api import unsubscribe

    config = {"model": "test-model", "base_url": "http://localhost:1/v1",
              "api_keys": {}}
    monkeypatch.setattr(llm.config_manager, "MYTHIC_DIR", tmp_path / "state")
    monkeypatch.setattr(llm.config_manager, "load_config",
                        lambda: _copy.deepcopy(config))
    monkeypatch.setattr(llm.config_manager, "save_config",
                        lambda config: True)
    monkeypatch.setattr(llm, "get_vector_provider",
                        lambda *args: _OfflineMemoryBudgets())
    instance = llm.Agent(project_root=tmp_path)
    from mythic_agent.core.policy import ToolPolicy
    instance.tool_policy = ToolPolicy("trusted")
    yield instance
    unsubscribe("agent_clear_history", instance._handle_clear_history)
    unsubscribe("agent_compact_history", instance._handle_compact_history)


def _budget_events(store, session_id, type_name):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == type_name]


def _drafting_budget(agent, **overrides):
    spec = {"label": "drafting budget", "token_limit": 1000}
    spec.update(overrides)
    return agent.register_budget(spec)


class TestBudgetAgentBudgets:
    def test_status_starts_empty(self, budget_agent):
        status = budget_agent.budget_status()
        assert status["budgets"] == []
        assert status["usage"] == {}
        assert status["verdicts"] == []
        assert "Budgets: none." in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["screen"] == format_budgets_screen(
            budget_agent._budget_registry())

    def test_register_holds_the_budget_and_pauses_nothing(
            self, budget_agent, tmp_path):
        store = SessionStore(tmp_path, tmp_path / "state")
        session_id = budget_agent.attach_session(store)
        record = _drafting_budget(budget_agent)
        assert record["type"] == "budget"
        assert record["budget_id"] == "budget-1"
        assert record["token_limit"] == 1000
        status = budget_agent.budget_status()
        assert [b["budget_id"] for b in status["budgets"]] == ["budget-1"]
        assert status["usage"] == {"budget-1": None}
        assert status["verdicts"][0]["status"] == "within"
        assert budget_agent.get_budget_verdict("budget-1").status == "within"
        assert "Budgets: 1 held." in status["screen"]
        # Registering spends nothing and pauses nothing:
        # no usage is held and no session news was published.
        assert budget_agent.get_budget_usage("budget-1") is None
        assert _budget_events(store, session_id, "budget_paused") == []

    def test_register_by_field_words(self, budget_agent):
        record = budget_agent.register_budget(
            label="session cap", scope="session", cost_limit=2.5)
        assert record["budget_id"] == "budget-1"
        assert record["scope"] == "session"
        assert record["cost_limit"] == 2.5
        budget = budget_agent.get_budget("budget-1")
        assert budget.display_label == "session cap"

    def test_unknown_budget_raises_keyerror(self, budget_agent):
        with pytest.raises(KeyError):
            budget_agent.get_budget("budget-99")
        with pytest.raises(KeyError):
            budget_agent.get_budget_usage("budget-99")
        with pytest.raises(KeyError):
            budget_agent.get_budget_verdict("budget-99")
        with pytest.raises(KeyError):
            budget_agent.record_budget_usage(
                "budget-99", {"tokens_used": 1})
        with pytest.raises(KeyError):
            budget_agent.refresh_budget_usage("budget-99")
        with pytest.raises(KeyError):
            budget_agent.budget_check("budget-99")

    def test_recording_usage_moves_the_verdict(self, budget_agent):
        _drafting_budget(budget_agent)
        record = budget_agent.record_budget_usage(
            "budget-1", {"tokens_used": 850})
        assert record["type"] == "budget_usage"
        assert record["tokens_used"] == 850
        assert budget_agent.get_budget_verdict("budget-1").status == "warning"
        status = budget_agent.budget_status()
        assert status["usage"]["budget-1"]["tokens_used"] == 850
        assert status["verdicts"][0]["status"] == "warning"
        # A newer reading replaces the older one.
        budget_agent.record_budget_usage("budget-1", tokens_used=10)
        assert budget_agent.get_budget_verdict("budget-1").status == "within"
        assert budget_agent.get_budget_usage("budget-1").tokens_used == 10

    def test_live_usage_reads_the_real_roads(self, budget_agent, tmp_path):
        from mythic_agent.core.costs import CostTracker
        tracker = CostTracker(tmp_path)
        tracker.record("gpt-4o", input_tokens=1000, output_tokens=500)
        reading = budget_agent.budget_live_usage()
        # Tokens and cost are the costs road's own readings:
        # 1500 tokens at the gpt-4o table price.
        assert reading.tokens_used == 1500
        expected = round(1000 / 1_000_000 * 2.50
                         + 500 / 1_000_000 * 10.0, 6)
        assert reading.cost_used == expected
        # Elapsed time is a real, small clock reading, and
        # no background jobs are held, so no commands.
        assert 0.0 <= reading.time_used_seconds < 60.0
        assert reading.commands_used == 0
        # Reading alone records nothing on any budget.
        _drafting_budget(budget_agent)
        budget_agent.budget_live_usage()
        assert budget_agent.get_budget_usage("budget-1") is None

    def test_refresh_feeds_the_live_reading(self, budget_agent, tmp_path):
        from mythic_agent.core.costs import CostTracker
        CostTracker(tmp_path).record(
            "gpt-4o", input_tokens=2000, output_tokens=0)
        _drafting_budget(budget_agent)
        record = budget_agent.refresh_budget_usage("budget-1")
        assert record["tokens_used"] == 2000
        assert budget_agent.get_budget_usage("budget-1").tokens_used == 2000
        assert budget_agent.get_budget_verdict("budget-1").status == "exceeded"


class TestBudgetCheckPauses:
    def test_exceeded_budget_publishes_paused_exactly_once(
            self, budget_agent, tmp_path):
        store = SessionStore(tmp_path, tmp_path / "state")
        session_id = budget_agent.attach_session(store)
        _drafting_budget(budget_agent)
        budget_agent.record_budget_usage("budget-1", {"tokens_used": 1000})
        result = budget_agent.budget_check()
        assert result["paused_ids"] == ["budget-1"]
        assert result["verdicts"][0]["status"] == "exceeded"
        assert len(result["paused"]) == 1
        paused = result["paused"][0]
        assert paused["type"] == "budget_paused"
        assert paused["graceful"] is True
        assert "graceful pause" in paused["headline"]
        events = _budget_events(store, session_id, "budget_paused")
        assert len(events) == 1
        assert events[0]["budget_id"] == "budget-1"
        assert events[0]["status"] == "exceeded"
        # A repeated check of the same reading is not new news.
        again = budget_agent.budget_check()
        assert again["paused_ids"] == ["budget-1"]
        assert len(_budget_events(store, session_id, "budget_paused")) == 1
        # Spending further past the limit is a new exceeded moment.
        budget_agent.record_budget_usage("budget-1", {"tokens_used": 1250})
        budget_agent.budget_check()
        assert len(_budget_events(store, session_id, "budget_paused")) == 2

    def test_check_within_and_warning_pause_nothing(
            self, budget_agent, tmp_path):
        store = SessionStore(tmp_path, tmp_path / "state")
        session_id = budget_agent.attach_session(store)
        _drafting_budget(budget_agent)
        budget_agent.record_budget_usage("budget-1", {"tokens_used": 100})
        result = budget_agent.budget_check()
        assert result["paused"] == [] and result["paused_ids"] == []
        assert result["reports"] == []
        budget_agent.record_budget_usage("budget-1", {"tokens_used": 900})
        warned = budget_agent.budget_check()
        assert warned["paused"] == []
        assert len(warned["reports"]) == 1
        assert warned["reports"][0]["type"] == "budget_report"
        assert warned["reports"][0]["status"] == "warning"
        assert _budget_events(store, session_id, "budget_paused") == []

    def test_check_one_budget_by_id(self, budget_agent):
        _drafting_budget(budget_agent)
        budget_agent.register_budget({"label": "open", "token_limit": 5})
        budget_agent.record_budget_usage("budget-1", {"tokens_used": 1000})
        budget_agent.record_budget_usage("budget-2", {"tokens_used": 5})
        one = budget_agent.budget_check("budget-2")
        assert [v["budget_id"] for v in one["verdicts"]] == ["budget-2"]
        assert one["paused_ids"] == ["budget-2"]
        both = budget_agent.budget_check()
        assert both["paused_ids"] == ["budget-1", "budget-2"]

    def test_check_without_a_session_still_pauses_in_its_return(
            self, budget_agent):
        _drafting_budget(budget_agent)
        budget_agent.record_budget_usage("budget-1", {"tokens_used": 1000})
        result = budget_agent.budget_check()
        assert result["paused_ids"] == ["budget-1"]
        assert result["paused"][0]["type"] == "budget_paused"

class TestBudgetsTerminalSurface:
    def test_show_is_the_whole_slice(self, budget_agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(budget_agent, "/budgets")
        assert text.startswith("Budgets (M-107) - ")
        assert "Budgets: none." in text
        assert USAGE in text

    def test_show_one_and_check_via_the_terminal(self, budget_agent):
        from mythic_agent.terminal import _slash
        _drafting_budget(budget_agent)
        _, _, text = _slash(budget_agent, "/budgets show budget-1")
        assert text.startswith("budget-1: ")
        assert "Verdict: within." in text
        budget_agent.record_budget_usage(
            "budget-1", {"tokens_used": 1000})
        _, _, text = _slash(budget_agent, "/budgets check budget-1")
        assert "Verdict: exceeded." in text
        _, _, text = _slash(budget_agent, "/budgets show budget-99")
        assert "unknown budget" in text

    def test_bad_grammar_is_the_usage(self, budget_agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(budget_agent, "/budgets frobnicate x")
        assert text == USAGE
        _, _, text = _slash(budget_agent, "/budgets check a b")
        assert text == USAGE


@pytest.fixture()
def budget_handler(budget_agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY

    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = budget_agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _budget_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestBudgetsCommand:
    def test_show_is_default(self, budget_handler, budget_agent):
        budget_handler._handle_budgets("")
        assert "Budgets: none." in _budget_published_text(budget_handler)

    def test_show_one_via_the_handler(self, budget_handler, budget_agent):
        _drafting_budget(budget_agent)
        budget_handler._handle_budgets("show budget-1")
        assert "budget-1: " in _budget_published_text(budget_handler)

    def test_check_via_the_handler(self, budget_handler, budget_agent):
        _drafting_budget(budget_agent)
        budget_agent.record_budget_usage(
            "budget-1", {"tokens_used": 1000})
        budget_handler._handle_budgets("check")
        assert "Verdict: exceeded." in _budget_published_text(budget_handler)

    def test_bad_grammar_is_published(self, budget_handler, budget_agent):
        budget_handler._handle_budgets("check a b")
        assert "Usage: /budgets" in _budget_published_text(budget_handler)
        budget_handler._handle_budgets("show budget-99")
        assert "unknown budget" in _budget_published_text(budget_handler)


class TestChatScreenRoutingBudgets:
    def test_budgets_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/budgets check", _FakeLog())
        assert calls == [("/budgets", "check")]
