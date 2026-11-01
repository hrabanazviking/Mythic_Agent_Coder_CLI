"""Long-context strategy per model (All-Features roadmap slice M-038).

Part II — The Provider Ocean — closes its context road here.
How much of the repository Mythic loads up front, and how it
loads it, is chosen from the model's capability truth — not
from one fixed habit for every door.

What already shipped, and what this slice adds:

* M-027 (``mythic_agent.core.model_capabilities``) stores the
  per-model truth: ``context_tokens`` known, or honestly
  unknown — never guessed.
* The context runtime (``mythic_agent.context.runtime``,
  elder slices 051–060) compiles file context from explicit
  mentions, git-diff hunks, tf-idf semantic selection, symbol
  selection, and dependency neighbours — but it ran every
  model with the same fixed 2,000-token file-context budget
  and the same selection width, whatever the model's record
  said: a 1M-class Gemini and a 16k gpt-3.5-turbo were fed
  identically, and no surface ever said which road a model
  was on.
* This slice is the strategy layer that reads the truth.
  The pure decision lives here; it is wired into
  ``prompt_file_context`` (the plan's budget and selection
  width drive the live compilation unless the caller passes
  an explicit budget, which always wins) and surfaced
  through ``Agent.context_strategy()`` and ``/longcontext``.

Honesty rules, enforced here and pinned by the slice's tests:

* **The strategy is chosen from capability truth only.** A
  model's strategy comes from its recorded
  ``context_tokens`` in the M-027 data — never from its
  name, its provider's door, or a vendor number remembered
  from elsewhere.
* **1M-class contexts get map-first loading.** A known
  context of 1,000,000 tokens or more leads with the repo
  map, then loads broadly: the file-context budget is a
  quarter of the window and the retrieval selection runs
  wide. (The repo-map source itself is Part III's M-044;
  the plan names it first so the road is ready for it, and
  the budget/selection halves of the plan drive the shipped
  sources today — nothing here claims the map exists yet.)
* **Small contexts get aggressive repo-map + retrieval.** A
  known context under the 1M line cannot be flooded, so the
  map and the retrieval sources do the work: the budget is
  a small named share of the window (a sixteenth, floored
  and capped), and the selection runs harder than the
  shipped default width.
* **Unknown context chooses nothing.** When the record
  says the context size is unknown — a placeholder name, an
  unlisted model, no model at all — the plan says exactly
  that, and falls back to the shipped default budget on the
  retrieval road. No window is invented, and no map-first
  claim is made for a model whose size nobody knows.
* **An explicit budget always wins.** A caller who passes a
  budget to the context runtime gets exactly that budget;
  the strategy only supplies the budget when the caller
  leaves the choice to it.
"""

from __future__ import annotations

__all__ = [
    "LONG_CONTEXT_SLICE",
    "MAP_FIRST_MIN_CONTEXT",
    "PLAIN_EXPLANATION",
    "STRATEGY_IDS",
    "Any",
    "Dict",
    "List",
    "Optional",
    "StrategyPlan",
    "Tuple",
    "format_longcontext_status",
    "format_strategy_plan",
    "parse_longcontext_args",
    "plan_from_config",
    "strategy_for_model",
]

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .model_capabilities import load_capabilities

#: The slice that owns this module.
LONG_CONTEXT_SLICE = "M-038"

#: A known context at or above this many tokens is 1M-class.
MAP_FIRST_MIN_CONTEXT = 1_000_000

#: The shipped default file-context budget (mirrors
#: ``mythic_agent.context.runtime.FILE_CONTEXT_BUDGET_TOKENS``;
#: a test pins the two equal). It is the fallback budget when
#: a model's context is unknown — the road the app already
#: runs, never a claim about the model's window.
_FALLBACK_BUDGET_TOKENS = 2000

#: Map-first loading spends a quarter of the window on file
#: context: the map leads and broad loading follows, with
#: room left for the conversation and the answer.
_MAP_FIRST_BUDGET_DIVISOR = 4

#: Retrieval-first loading spends a sixteenth of the window,
#: floored so a small window still retrieves something real
#: and capped so a merely-large window is not flooded.
_RETRIEVAL_BUDGET_DIVISOR = 16
_RETRIEVAL_BUDGET_FLOOR = 500
_RETRIEVAL_BUDGET_CAP = 8000

#: Selection widths (semantic + symbol sources): map-first
#: loads widest, retrieval-first runs harder than the shipped
#: default of 3, and the unknown road keeps the default.
_MAP_FIRST_TOP_N = 8
_RETRIEVAL_TOP_N = 5
_FALLBACK_TOP_N = 3

#: The strategy ids, in the order the chooser tries them.
STRATEGY_IDS: Tuple[str, ...] = ("map_first", "retrieval_first", "unknown")

#: Long-context strategy explained in plain words — the
#: sentence every surface shows. The window a model is known
#: to have decides how the repository is loaded for it; an
#: unknown window is named unknown, never dressed up.
PLAIN_EXPLANATION = (
    "Long-context strategy: how much of the repository is "
    "loaded for a model is chosen from that model's recorded "
    "context size. A model known to hold a million tokens or "
    "more loads map-first — the repo map leads, then broad "
    "file loading inside a quarter of the window. A model "
    "with a smaller known window leans on the repo map and "
    "retrieval instead — a small, named share of the window, "
    "with the retrieval selection run harder. When a model's "
    "context size is unknown, no strategy is claimed: the "
    "app says so and uses its ordinary default budget on the "
    "retrieval road."
)


@dataclass(frozen=True)
class StrategyPlan:
    """One model's long-context strategy, with its plain reason.

    ``context_tokens`` is the model's recorded M-027 truth:
    a positive int, or None when the size is unknown.
    ``strategy`` is one of :data:`STRATEGY_IDS`.
    ``budget_tokens`` is the file-context budget the plan
    gives the context compiler, ``top_n`` the semantic and
    symbol selection width, and ``load_order`` the order the
    plan loads in — the repo map first on both known roads
    (its source is Part III's M-044; see the module docstring
    for exactly what is wired today).
    """

    model: str
    context_tokens: Optional[int]
    strategy: str
    budget_tokens: int
    top_n: int
    map_first: bool
    retrieval_aggressive: bool
    load_order: Tuple[str, ...]
    reason: str

    def record(self) -> Dict[str, Any]:
        """This plan as a plain mapping."""
        return {
            "model": self.model,
            "context_tokens": self.context_tokens,
            "strategy": self.strategy,
            "budget_tokens": self.budget_tokens,
            "top_n": self.top_n,
            "map_first": self.map_first,
            "retrieval_aggressive": self.retrieval_aggressive,
            "load_order": list(self.load_order),
            "reason": self.reason,
        }


def _context_word(context_tokens: Optional[int]) -> str:
    if context_tokens is None:
        return "unknown"
    return f"{context_tokens:,} tokens"


def strategy_for_model(model_name: Any,
                       capabilities: Any = None) -> StrategyPlan:
    """The strategy for *model_name*, chosen from capability truth.

    Pure over the M-027 record: a known context at or above
    :data:`MAP_FIRST_MIN_CONTEXT` is map-first; a known
    smaller context is retrieval-first; an unknown context —
    an unlisted or placeholder model, or no model at all —
    chooses nothing and falls back to the shipped default
    budget on the retrieval road, saying so plainly.
    """
    model = model_name.strip() if isinstance(model_name, str) else ""
    caps = capabilities if capabilities is not None else load_capabilities()
    context = caps.for_model(model).context_tokens if model else None
    if context is not None and context >= MAP_FIRST_MIN_CONTEXT:
        budget = context // _MAP_FIRST_BUDGET_DIVISOR
        return StrategyPlan(
            model=model, context_tokens=context, strategy="map_first",
            budget_tokens=budget, top_n=_MAP_FIRST_TOP_N,
            map_first=True, retrieval_aggressive=False,
            load_order=("repo_map", "explicit_files", "git_diff",
                        "semantic", "symbols", "deps"),
            reason=(
                f"{model} is known to hold "
                f"{_context_word(context)} — a million-class "
                "window — so loading is map-first: the repo map "
                "leads, then files load broadly inside a "
                f"file-context budget of {budget:,} tokens (a "
                "quarter of the window), with the retrieval "
                f"selection running wide (top {_MAP_FIRST_TOP_N})."))
    if context is not None:
        budget = min(_RETRIEVAL_BUDGET_CAP,
                     max(_RETRIEVAL_BUDGET_FLOOR,
                         context // _RETRIEVAL_BUDGET_DIVISOR))
        return StrategyPlan(
            model=model, context_tokens=context,
            strategy="retrieval_first",
            budget_tokens=budget, top_n=_RETRIEVAL_TOP_N,
            map_first=False, retrieval_aggressive=True,
            load_order=("repo_map", "semantic", "symbols", "deps",
                        "explicit_files", "git_diff"),
            reason=(
                f"{model} is known to hold "
                f"{_context_word(context)} — under the "
                "million-token line — so the window is not "
                "flooded: the repo map and retrieval do the "
                "work inside a file-context budget of "
                f"{budget:,} tokens (a sixteenth of the "
                "window, floored and capped), with the "
                "retrieval selection run harder than the "
                f"default (top {_RETRIEVAL_TOP_N})."))
    if model:
        reason = (
            f"{model}'s context size is unknown — its "
            "capability record does not say, and a window is "
            "never guessed — so no long-context strategy is "
            "claimed for it. Loading falls back to the "
            "ordinary default: a file-context budget of "
            f"{_FALLBACK_BUDGET_TOKENS:,} tokens on the "
            "retrieval road, until the model's context size "
            "is recorded.")
    else:
        reason = (
            "No model is selected, so there is no capability "
            "record to choose a strategy from. Loading falls "
            "back to the ordinary default: a file-context "
            f"budget of {_FALLBACK_BUDGET_TOKENS:,} tokens on "
            "the retrieval road.")
    return StrategyPlan(
        model=model, context_tokens=None, strategy="unknown",
        budget_tokens=_FALLBACK_BUDGET_TOKENS, top_n=_FALLBACK_TOP_N,
        map_first=False, retrieval_aggressive=False,
        load_order=("semantic", "symbols", "deps",
                    "explicit_files", "git_diff"),
        reason=reason)


def plan_from_config(config: Dict[str, Any],
                     capabilities: Any = None) -> StrategyPlan:
    """The strategy plan for the model *config* selects."""
    if not isinstance(config, dict):
        raise ValueError(
            f"Config must be a mapping, got {type(config).__name__}")
    return strategy_for_model(config.get("model"), capabilities)


def parse_longcontext_args(text: Any) -> Dict[str, Any]:
    """Parse the ``/longcontext`` slash-command argument string.

    Grammar::

        /longcontext          -> the current model's strategy
        /longcontext show     -> the current model's strategy
        /longcontext <model>  -> preview that model's strategy

    Returns a dict with keys ``action`` (``show`` /
    ``preview``) and ``model`` (the named model, or None).
    Raises :class:`ValueError` on a usage error.
    """
    if text is None:
        text = ""
    if not isinstance(text, str):
        raise ValueError(
            "Long-context arguments must be text, got "
            f"{type(text).__name__}")
    stripped = text.strip()
    if not stripped or stripped.lower() in ("show", "status"):
        return {"action": "show", "model": None}
    if stripped.lower().startswith("show "):
        named = stripped[5:].strip()
        if named:
            return {"action": "preview", "model": named}
    return {"action": "preview", "model": stripped}


def format_strategy_plan(plan: StrategyPlan) -> str:
    """One plain paragraph: the strategy, its numbers, its reason."""
    head = (
        f"Long-context strategy for "
        f"{plan.model or 'no model selected'}: {plan.strategy} "
        f"(recorded context: {_context_word(plan.context_tokens)}; "
        f"file-context budget {plan.budget_tokens:,} tokens; "
        f"retrieval selection top {plan.top_n}). ")
    return head + plan.reason


def format_longcontext_status(status: Dict[str, Any]) -> str:
    """The visible status: the model's strategy, in plain words.

    *status* is the agent's long-context status mapping (the
    current model, its plan, and the plain explanation).
    """
    plan = status.get("plan") or {}
    head = (
        f"Long-context strategy for "
        f"{plan.get('model') or 'no model selected'}: "
        f"{plan.get('strategy', 'unknown')} "
        f"(recorded context: "
        f"{_context_word(plan.get('context_tokens'))}; "
        f"file-context budget "
        f"{plan.get('budget_tokens', 0):,} tokens; "
        f"retrieval selection top {plan.get('top_n', 0)}). ")
    lines = [
        head + plan.get("reason", ""),
        PLAIN_EXPLANATION,
        "  An explicit budget passed to the context runtime "
        "always wins over the strategy's budget; the strategy "
        "supplies the budget only when the caller leaves the "
        "choice to it.",
    ]
    return "\n".join(lines)
