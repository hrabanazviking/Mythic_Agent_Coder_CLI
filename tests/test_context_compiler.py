"""
TIER: unit
Tests for the context compiler core (Slice 051), the token budget
planner (Slice 052) and protocol-group preservation (Slice 053).
"""

import threading

import pytest

from mythic_agent.context import (
    BudgetPlanner,
    CachedSource,
    CompiledContext,
    ContextBlock,
    ContextCompilationCancelled,
    ContextCompiler,
    MessageGroup,
    TokenEstimator,
    format_compiled,
    group_protocol_messages,
    truncate_groups,
    truncate_text,
)
from mythic_agent.context.compiler import CompileContext


# ---------------------------------------------------------------------------
# Slice 052: TokenEstimator
# ---------------------------------------------------------------------------

def test_estimator_heuristic_backend_when_tiktoken_absent():
    est = TokenEstimator()
    assert est.backend == "heuristic"
    assert est.count("hello world, this is a test") > 0


def test_estimator_counts_are_deterministic():
    est = TokenEstimator()
    text = "def rebuild_system_prompt(self):\n    pass\n" * 50
    assert est.count(text) == est.count(text)
    assert est.count("") == 0
    assert est.count_message("user", "hi") > est.count("hi")


def test_estimator_uses_tiktoken_when_available(monkeypatch):
    import sys
    import types

    fake = types.ModuleType("tiktoken")

    class FakeEncoding:
        def encode(self, text):
            return text.split()

    fake.get_encoding = lambda model: FakeEncoding()
    monkeypatch.setitem(sys.modules, "tiktoken", fake)
    est = TokenEstimator()
    assert est.backend == "tiktoken"
    assert est.count("one two three") == 3


def test_estimator_tiktoken_failure_falls_back_to_heuristic(monkeypatch):
    import sys
    import types

    fake = types.ModuleType("tiktoken")
    fake.get_encoding = lambda model: (_ for _ in ()).throw(RuntimeError("nope"))
    monkeypatch.setitem(sys.modules, "tiktoken", fake)
    est = TokenEstimator()
    assert est.backend == "heuristic"
    assert est.count("abcdefgh") == 2


# ---------------------------------------------------------------------------
# Slice 052: BudgetPlanner + truncate_text
# ---------------------------------------------------------------------------

def test_allocate_sums_to_total_and_is_deterministic():
    planner = BudgetPlanner()
    shares = {"instructions": 0.2, "files": 0.5, "diff": 0.3}
    first = planner.allocate(1000, shares)
    second = planner.allocate(1000, shares)
    assert first == second
    assert sum(first.values()) == 1000
    assert first["files"] >= first["instructions"]


def test_allocate_normalizes_shares():
    planner = BudgetPlanner()
    result = planner.allocate(100, {"a": 2.0, "b": 2.0})
    assert sum(result.values()) == 100
    assert result["a"] == result["b"] == 50


def test_allocate_zero_total_gives_zeroes():
    planner = BudgetPlanner()
    assert planner.allocate(0, {"a": 1.0, "b": 1.0}) == {"a": 0, "b": 0}


def test_allocate_rejects_bad_input():
    planner = BudgetPlanner()
    with pytest.raises(ValueError):
        planner.allocate(100, {})
    with pytest.raises(ValueError):
        planner.allocate(100, {"a": -1.0})
    with pytest.raises(ValueError):
        planner.allocate(-5, {"a": 1.0})


def test_truncate_text_returns_fitting_text_unchanged():
    est = TokenEstimator()
    assert truncate_text("short", 100, est) == "short"


def test_truncate_text_marks_and_prefers_word_boundary():
    est = TokenEstimator()
    text = "alpha beta gamma delta epsilon zeta eta theta"
    out = truncate_text(text, 8, est)
    assert out.endswith("... [truncated]")
    assert est.count(out) <= 8
    # no partial word left dangling
    assert not out[:-len("... [truncated]")].rstrip().endswith("alp")


def test_truncate_text_boundary_behavior():
    est = TokenEstimator()
    assert truncate_text("hello", 0, est) == ""
    assert truncate_text("hello", -3, est) == ""
    # budget too small for the marker: best-effort slice of the marker
    tiny = truncate_text("hello world", 1, est)
    assert est.count(tiny) <= 1


# ---------------------------------------------------------------------------
# Slice 053: protocol groups
# ---------------------------------------------------------------------------

def _tool_messages():
    return [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "fix it"},
        {"role": "assistant", "content": "",
         "tool_calls": [{"id": "c1", "name": "read", "arguments": "{}"},
                        {"id": "c2", "name": "write", "arguments": "{}"}]},
        {"role": "tool", "tool_call_id": "c1", "content": "r1"},
        {"role": "tool", "tool_call_id": "c2", "content": "r2"},
        {"role": "assistant", "content": "done"},
    ]


def test_tool_round_is_one_atomic_group():
    groups = group_protocol_messages(_tool_messages())
    kinds = [g.provenance["kind"] for g in groups]
    assert kinds == ["system", "user", "tool-round", "solo"]
    tool_group = groups[2]
    assert len(tool_group.messages) == 3  # call + 2 results


def test_user_with_attachments_is_atomic():
    messages = [{"role": "user",
                 "content": [{"type": "text", "text": "look"},
                             {"type": "image", "data": "abc"}]}]
    groups = group_protocol_messages(messages)
    assert len(groups) == 1
    assert groups[0].provenance["kind"] == "user+attachments"


def test_truncate_groups_never_splits_a_tool_round():
    est = TokenEstimator()
    groups = group_protocol_messages(_tool_messages())

    def cost(group):
        return sum(est.count_message(m["role"], str(m.get("content", "")))
                   for m in group.messages)

    system_cost, user_cost, tool_cost = cost(groups[0]), cost(groups[1]), cost(groups[2])
    # Budget that fits system + user but only PART of the tool round:
    # the whole round must be excluded, never partially included.
    budget = system_cost + user_cost + tool_cost - 1
    out = truncate_groups(groups, budget, est)
    roles = [(m["role"], m.get("tool_call_id")) for m in out]
    tool_msgs = [r for r in roles if r[0] == "tool"]
    assistant_calls = [m for m in out
                       if m.get("role") == "assistant" and m.get("tool_calls")]
    assert not tool_msgs and not assistant_calls, \
        "partial tool round leaked into the truncated output"
    assert [m["role"] for m in out] == ["system", "user", "assistant"]
    assert out[-1]["content"] == "done"  # the solo tail group still fits


def test_truncate_groups_system_always_kept_even_over_budget():
    est = TokenEstimator()
    groups = group_protocol_messages(_tool_messages())
    out = truncate_groups(groups, 1, est)
    assert out and out[0]["role"] == "system"


def test_truncate_groups_rejects_negative_budget():
    with pytest.raises(ValueError):
        truncate_groups([], -1)


# ---------------------------------------------------------------------------
# Slice 051: ContextCompiler
# ---------------------------------------------------------------------------

class _StaticSource:
    def __init__(self, name, blocks, priority=5, enabled=True):
        self.name = name
        self._blocks = blocks
        self.priority = priority
        self.enabled = enabled
        self.calls = 0

    def collect(self, ctx):
        self.calls += 1
        return list(self._blocks)


def test_compiler_assembles_ordered_blocks(tmp_path):
    compiler = ContextCompiler(tmp_path, budget_tokens=10_000)
    compiler.add_source(_StaticSource("b", [ContextBlock("b1", "B" * 40, priority=3)]))
    compiler.add_source(_StaticSource("a", [ContextBlock("a1", "A" * 40, priority=1)]))
    compiled = compiler.compile("query")
    assert isinstance(compiled, CompiledContext)
    assert [b.name for b in compiled.blocks] == ["a1", "b1"]
    assert compiled.total_tokens <= compiled.budget_tokens
    assert compiled.total_tokens > 0


def test_compiler_missing_workspace_raises():
    with pytest.raises(ValueError):
        ContextCompiler("/nonexistent-workspace-xyz")


def test_compiler_rejects_bad_budgets(tmp_path):
    with pytest.raises(ValueError):
        ContextCompiler(tmp_path, budget_tokens=0)
    with pytest.raises(ValueError):
        ContextCompiler(tmp_path, max_block_tokens=-1)


def test_compiler_skips_failing_source_with_warning(tmp_path):
    class Boom:
        name = "boom"
        priority = 5
        enabled = True

        def collect(self, ctx):
            raise RuntimeError("kaput")

    compiler = ContextCompiler(tmp_path)
    compiler.add_source(Boom())
    compiler.add_source(_StaticSource("ok", [ContextBlock("ok1", "fine")]))
    compiled = compiler.compile()
    assert [b.name for b in compiled.blocks] == ["ok1"]
    assert any("boom" in w for w in compiled.warnings)


def test_compiler_skips_non_block_output(tmp_path):
    compiler = ContextCompiler(tmp_path)
    compiler.add_source(_StaticSource("weird", ["not-a-block"]))
    compiled = compiler.compile()
    assert compiled.blocks == []
    assert compiled.warnings


def test_compiler_truncates_oversized_trimmable_block(tmp_path):
    compiler = ContextCompiler(tmp_path, max_block_tokens=50)
    compiler.add_source(_StaticSource("big", [ContextBlock("big1", "x" * 10_000)]))
    compiled = compiler.compile()
    assert [b.name for b in compiled.blocks] == ["big1"]
    assert compiled.truncated == ["big1"]
    assert compiled.blocks[0].tokens <= 50


def test_compiler_drops_non_trimmable_oversized_block(tmp_path):
    compiler = ContextCompiler(tmp_path, max_block_tokens=50)
    compiler.add_source(_StaticSource(
        "big", [ContextBlock("big1", "x" * 10_000, trimmable=False)]))
    compiled = compiler.compile()
    assert compiled.blocks == []
    assert compiled.dropped == ["big1"]


def test_compiler_drops_empty_blocks(tmp_path):
    compiler = ContextCompiler(tmp_path)
    compiler.add_source(_StaticSource("e", [ContextBlock("e1", "   ")]))
    compiled = compiler.compile()
    assert compiled.blocks == []
    assert compiled.dropped == ["e1"]


def test_compiler_mandatory_blocks_survive_budget(tmp_path):
    compiler = ContextCompiler(tmp_path, budget_tokens=10)
    compiler.add_source(_StaticSource(
        "sys", [ContextBlock("must", "mandatory instructions", priority=0)]))
    compiler.add_source(_StaticSource(
        "opt", [ContextBlock("opt1", "optional " * 100, priority=9)]))
    compiled = compiler.compile()
    assert [b.name for b in compiled.blocks] == ["must"]
    assert "opt1" in compiled.dropped


def test_compiler_redacts_secrets(tmp_path):
    secret = "sk-test-secret-abcdef123456"
    compiler = ContextCompiler(tmp_path, config={"api_keys": {"x": secret}})
    compiler.add_source(_StaticSource("s", [ContextBlock("s1", f"key={secret} end")]))
    compiled = compiler.compile()
    assert secret not in compiled.blocks[0].content
    assert "[REDACTED]" in compiled.blocks[0].content


def test_compiler_cross_workspace_isolation(tmp_path):
    ws_a = tmp_path / "a"
    ws_b = tmp_path / "b"
    ws_a.mkdir()
    ws_b.mkdir()
    (ws_b / "secret.txt").write_text("b-secret")

    class Sneaky:
        name = "sneaky"
        priority = 5
        enabled = True

        def collect(self, ctx):
            # Attempt to read outside the bound workspace: must fail.
            from mythic_agent.core.workspace import assert_within_workspace
            assert_within_workspace(ctx.workspace, ws_b / "secret.txt")
            return [ContextBlock("leak", "should never appear")]

    compiler = ContextCompiler(ws_a)
    compiler.add_source(Sneaky())
    compiled = compiler.compile()
    assert compiled.blocks == []
    assert any("sneaky" in w for w in compiled.warnings)
    for block in compiled.blocks:
        assert block.provenance["workspace"] == str(ws_a)


def test_compiler_disabled_sources_are_skipped(tmp_path):
    compiler = ContextCompiler(tmp_path)
    compiler.add_source(_StaticSource("off", [ContextBlock("x", "x")], enabled=False))
    assert compiler.compile().blocks == []


def test_compiler_cancellation_before_and_during(tmp_path):
    compiler = ContextCompiler(tmp_path)
    compiler.add_source(_StaticSource("s", [ContextBlock("x", "x")]))
    event = threading.Event()
    event.set()
    compiler.cancel_event = event
    with pytest.raises(ContextCompilationCancelled):
        compiler.compile()

    fired = threading.Event()

    class Tripper:
        name = "tripper"
        priority = 5
        enabled = True

        def collect(self, ctx):
            fired.set()
            return [ContextBlock("x", "x")]

    compiler2 = ContextCompiler(tmp_path, cancel_event=fired)
    compiler2.add_source(Tripper())
    compiler2.add_source(_StaticSource("later", [ContextBlock("y", "y")]))
    with pytest.raises(ContextCompilationCancelled):
        compiler2.compile()


def test_cached_source_staleness(tmp_path):
    inner = _StaticSource("s", [ContextBlock("x", "v1")])
    cached = CachedSource(inner, ttl_seconds=3600)
    compiler = ContextCompiler(tmp_path)
    compiler.add_source(cached)
    first = compiler.compile("q")
    second = compiler.compile("q")
    assert inner.calls == 1
    assert first.blocks[0].content == second.blocks[0].content == "v1"
    cached.invalidate()
    compiler.compile("q")
    assert inner.calls == 2


def test_cached_source_zero_ttl_always_fresh(tmp_path):
    inner = _StaticSource("s", [ContextBlock("x", "v1")])
    cached = CachedSource(inner, ttl_seconds=0)
    compiler = ContextCompiler(tmp_path)
    compiler.add_source(cached)
    compiler.compile("q")
    compiler.compile("q")
    assert inner.calls == 2


def test_cached_source_rejects_negative_ttl():
    with pytest.raises(ValueError):
        CachedSource(_StaticSource("s", []), ttl_seconds=-1)


def test_format_compiled_includes_provenance(tmp_path):
    compiler = ContextCompiler(tmp_path)
    compiler.add_source(_StaticSource("s", [ContextBlock("n", "body")]))
    text = format_compiled(compiler.compile())
    assert "body" in text and "n" in text and "s" in text
