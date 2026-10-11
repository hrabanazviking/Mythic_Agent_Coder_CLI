"""Context compiler package (roadmap slices 051-060).

Assembles the model prompt from pluggable, workspace-isolated sources
under a token budget:

* :mod:`mythic_agent.context.compiler` -- ContextCompiler core (051)
* :mod:`mythic_agent.context.budget` -- token estimation + budget planning (052)
* :mod:`mythic_agent.context.groups` -- atomic protocol-group truncation (053)
* :mod:`mythic_agent.context.instructions` -- repo instruction resolver + precedence (054/055)
* :mod:`mythic_agent.context.files` -- explicit @-mention file context (056)
* :mod:`mythic_agent.context.semantic` -- tf-idf semantic file selection (057)
* :mod:`mythic_agent.context.symbols` -- ast symbol-aware selection (058)
* :mod:`mythic_agent.context.deps` -- ast dependency-aware selection (059)
* :mod:`mythic_agent.context.gitdiff` -- git-diff-aware context (060)
* :mod:`mythic_agent.context.runtime` -- agent prompt-path glue

The compiler hooks into the agent only when the
``context_compiler_enabled`` runtime setting is true (default false).
"""

from __future__ import annotations

__all__ = [
    "BudgetPlanner",
    "CachedSource",
    "CompileContext",
    "CompiledContext",
    "ContextBlock",
    "ContextCompilationCancelled",
    "ContextCompiler",
    "ContextError",
    "ContextSource",
    "ExplicitFileContext",
    "ExplicitFilesSource",
    "GitDiff",
    "GitDiffSource",
    "ImportGraph",
    "InstructionFile",
    "InstructionResolver",
    "InstructionSource",
    "MessageGroup",
    "PrecedenceResult",
    "SemanticFilesSource",
    "SemanticSelection",
    "Symbol",
    "SymbolFilesSource",
    "SymbolIndex",
    "TokenEstimator",
    "apply_precedence",
    "build_corpus",
    "build_import_graph",
    "collect_git_diff",
    "extract_imports",
    "extract_mentions",
    "extract_symbols",
    "format_compiled",
    "group_protocol_messages",
    "index_workspace",
    "instruction_context_block",
    "module_key",
    "parse_directives",
    "prompt_file_context",
    "rank_by_symbol_mentions",
    "related_modules",
    "resolve_mentions",
    "score_corpus",
    "select_by_symbols",
    "select_files",
    "select_related",
    "truncate_groups",
    "truncate_text",
]

from .budget import BudgetPlanner, TokenEstimator, truncate_text
from .compiler import (
    CachedSource,
    CompileContext,
    CompiledContext,
    ContextBlock,
    ContextCompilationCancelled,
    ContextCompiler,
    ContextError,
    ContextSource,
    format_compiled,
)
from .deps import (
    ImportGraph,
    build_import_graph,
    extract_imports,
    module_key,
    related_modules,
    select_related,
)
from .files import (
    ExplicitFileContext,
    ExplicitFilesSource,
    extract_mentions,
    resolve_mentions,
)
from .gitdiff import GitDiff, GitDiffSource, collect_git_diff
from .groups import MessageGroup, group_protocol_messages, truncate_groups
from .instructions import (
    InstructionFile,
    InstructionResolver,
    InstructionSource,
    PrecedenceResult,
    apply_precedence,
    parse_directives,
)
from .runtime import instruction_context_block, prompt_file_context
from .semantic import (
    SemanticFilesSource,
    SemanticSelection,
    build_corpus,
    score_corpus,
    select_files,
)
from .symbols import (
    Symbol,
    SymbolFilesSource,
    SymbolIndex,
    extract_symbols,
    index_workspace,
    rank_by_symbol_mentions,
    select_by_symbols,
)
