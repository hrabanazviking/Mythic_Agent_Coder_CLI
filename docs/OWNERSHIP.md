# Source Ownership Map

> **GENERATED FILE — do not edit by hand.**
> Regenerate with: `python scripts/gen_ownership.py`
> Generated at: 2026-10-10T10:08:28Z

Ownership is derived from real git history: for each module the owner is the top author by commit count touching that file (ties resolve to the most recently active author). Share is the owner's commit count divided by the total commit count on the file.

## Per-author rollup

Total modules: **95**

| Author | Modules owned | File commits | Share of modules |
| --- | ---: | ---: | ---: |
| Yrsa Freydisdottir | 66 | 128 | 69.5% |
| Volmarr Wyrd | 29 | 178 | 30.5% |

## Per-module ownership

| Module | Owner | Owner share | Commits (owner / total) | Last touch |
| --- | --- | ---: | ---: | --- |
| `mythic_agent/__init__.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-06-05 |
| `mythic_agent/__version__.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-09 |
| `mythic_agent/agents/__init__.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-06-06 |
| `mythic_agent/agents/command_handler.py` | Volmarr Wyrd | 60.0% | 6 / 10 | 2026-10-10 |
| `mythic_agent/agents/context.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/agents/llm.py` | Volmarr Wyrd | 87.1% | 27 / 31 | 2026-10-10 |
| `mythic_agent/agents/parallel.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/agents/planning.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/agents/prompts.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/agents/recovery.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/agents/tasks.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/agents/tools.py` | Volmarr Wyrd | 77.8% | 14 / 18 | 2026-10-10 |
| `mythic_agent/bench.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/cli.py` | Volmarr Wyrd | 72.7% | 8 / 11 | 2026-10-10 |
| `mythic_agent/constants.py` | Volmarr Wyrd | 85.7% | 6 / 7 | 2026-10-10 |
| `mythic_agent/core/__init__.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-06-06 |
| `mythic_agent/core/arch_conformance.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/audio.py` | Volmarr Wyrd | 66.7% | 4 / 6 | 2026-10-10 |
| `mythic_agent/core/audit.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/cache.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/config_manager.py` | Volmarr Wyrd | 90.0% | 9 / 10 | 2026-10-10 |
| `mythic_agent/core/costs.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/dead_code_scan.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/determinism.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-10 |
| `mythic_agent/core/edits.py` | Yrsa Freydisdottir | 50.0% | 1 / 2 | 2026-10-10 |
| `mythic_agent/core/engine.py` | Volmarr Wyrd | 55.6% | 5 / 9 | 2026-10-10 |
| `mythic_agent/core/exceptions.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-10 |
| `mythic_agent/core/execution.py` | Yrsa Freydisdottir | 60.0% | 6 / 10 | 2026-10-10 |
| `mythic_agent/core/journal.py` | Yrsa Freydisdottir | 100.0% | 3 / 3 | 2026-10-10 |
| `mythic_agent/core/lifecycle.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-10 |
| `mythic_agent/core/metrics.py` | Yrsa Freydisdottir | 100.0% | 3 / 3 | 2026-10-10 |
| `mythic_agent/core/mythic_logging.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/notifications.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/policy.py` | Volmarr Wyrd | 66.7% | 2 / 3 | 2026-10-10 |
| `mythic_agent/core/progress.py` | Yrsa Freydisdottir | 100.0% | 3 / 3 | 2026-10-10 |
| `mythic_agent/core/recovery.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/redaction.py` | Yrsa Freydisdottir | 75.0% | 3 / 4 | 2026-10-10 |
| `mythic_agent/core/repo_census.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/runtime.py` | Volmarr Wyrd | 80.0% | 4 / 5 | 2026-10-10 |
| `mythic_agent/core/sandbox.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/secrets_audit.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/secure_api.py` | Volmarr Wyrd | 62.5% | 5 / 8 | 2026-10-10 |
| `mythic_agent/core/sessions.py` | Yrsa Freydisdottir | 50.0% | 2 / 4 | 2026-10-10 |
| `mythic_agent/core/storage.py` | Yrsa Freydisdottir | 50.0% | 1 / 2 | 2026-10-10 |
| `mythic_agent/core/thread_audit.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-10 |
| `mythic_agent/core/tool_schemas.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/transcript.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/tts.py` | Volmarr Wyrd | 87.5% | 7 / 8 | 2026-10-10 |
| `mythic_agent/core/type_coverage.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/validation.py` | Yrsa Freydisdottir | 100.0% | 3 / 3 | 2026-10-10 |
| `mythic_agent/core/workspace.py` | Yrsa Freydisdottir | 50.0% | 1 / 2 | 2026-10-10 |
| `mythic_agent/data/__init__.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-06-06 |
| `mythic_agent/data/data_loader.py` | Yrsa Freydisdottir | 66.7% | 2 / 3 | 2026-10-10 |
| `mythic_agent/doctor.py` | Yrsa Freydisdottir | 100.0% | 3 / 3 | 2026-10-10 |
| `mythic_agent/integrations/__init__.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-09 |
| `mythic_agent/integrations/github.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/knowledge/__init__.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-09 |
| `mythic_agent/knowledge/graph.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/mcp_server.py` | Yrsa Freydisdottir | 50.0% | 3 / 6 | 2026-10-10 |
| `mythic_agent/memory/__init__.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-06-06 |
| `mythic_agent/memory/core_memory.py` | Volmarr Wyrd | 60.0% | 3 / 5 | 2026-10-10 |
| `mythic_agent/memory/long_term.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/memory/preferences.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/memory/scopes.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/memory/vector_db.py` | Volmarr Wyrd | 75.0% | 6 / 8 | 2026-10-10 |
| `mythic_agent/onboarding.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/providers/__init__.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-09 |
| `mythic_agent/providers/anthropic.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/providers/base.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/providers/google.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/providers/ollama.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/providers/registry.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/resources.py` | Yrsa Freydisdottir | 66.7% | 2 / 3 | 2026-10-10 |
| `mythic_agent/terminal.py` | Volmarr Wyrd | 57.1% | 4 / 7 | 2026-10-10 |
| `mythic_agent/tools/__init__.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-09 |
| `mythic_agent/tools/code_index.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/tools/docgen.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/tools/review.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/tools/smart_files.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/tutorials.py` | Yrsa Freydisdottir | 50.0% | 1 / 2 | 2026-10-10 |
| `mythic_agent/ui/__init__.py` | Yrsa Freydisdottir | 50.0% | 1 / 2 | 2026-10-09 |
| `mythic_agent/ui/components/__init__.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-06-06 |
| `mythic_agent/ui/components/modals.py` | Volmarr Wyrd | 80.0% | 4 / 5 | 2026-10-10 |
| `mythic_agent/ui/components/subagent_editor.py` | Volmarr Wyrd | 87.5% | 7 / 8 | 2026-10-10 |
| `mythic_agent/ui/components/subagent_modal.py` | Volmarr Wyrd | 66.7% | 2 / 3 | 2026-10-10 |
| `mythic_agent/ui/main_app.py` | Volmarr Wyrd | 75.0% | 6 / 8 | 2026-10-10 |
| `mythic_agent/ui/markdown.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/ui/screens/__init__.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-06-06 |
| `mythic_agent/ui/screens/chat_screen.py` | Volmarr Wyrd | 90.9% | 30 / 33 | 2026-10-10 |
| `mythic_agent/ui/screens/setup_screen.py` | Volmarr Wyrd | 90.9% | 10 / 11 | 2026-10-10 |
| `mythic_agent/ui/screens/splash_screen.py` | Volmarr Wyrd | 66.7% | 2 / 3 | 2026-10-10 |
| `mythic_agent/ui/shortcuts.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/ui/themes.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/workflow/__init__.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-09 |
| `mythic_agent/workflow/slice_runner.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |

## Machine-readable module index

Tests parse this section. Do not hand-edit; regenerate with the script.

```json
{
  "modules": [
    {
      "module": "mythic_agent/__init__.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-06-05"
    },
    {
      "module": "mythic_agent/__version__.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-09"
    },
    {
      "module": "mythic_agent/agents/__init__.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-06-06"
    },
    {
      "module": "mythic_agent/agents/command_handler.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 6,
      "total_commits": 10,
      "share": 0.6,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/agents/context.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/agents/llm.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 27,
      "total_commits": 31,
      "share": 0.871,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/agents/parallel.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/agents/planning.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/agents/prompts.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/agents/recovery.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/agents/tasks.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/agents/tools.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 14,
      "total_commits": 18,
      "share": 0.7778,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/bench.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/cli.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 8,
      "total_commits": 11,
      "share": 0.7273,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/constants.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 6,
      "total_commits": 7,
      "share": 0.8571,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/__init__.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-06-06"
    },
    {
      "module": "mythic_agent/core/arch_conformance.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/audio.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 4,
      "total_commits": 6,
      "share": 0.6667,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/audit.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/cache.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/config_manager.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 9,
      "total_commits": 10,
      "share": 0.9,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/costs.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/dead_code_scan.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/determinism.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/edits.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 2,
      "share": 0.5,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/engine.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 5,
      "total_commits": 9,
      "share": 0.5556,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/exceptions.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/execution.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 6,
      "total_commits": 10,
      "share": 0.6,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/journal.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 3,
      "total_commits": 3,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/lifecycle.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/metrics.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 3,
      "total_commits": 3,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/mythic_logging.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/notifications.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/policy.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 2,
      "total_commits": 3,
      "share": 0.6667,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/progress.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 3,
      "total_commits": 3,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/recovery.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/redaction.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 3,
      "total_commits": 4,
      "share": 0.75,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/repo_census.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/runtime.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 4,
      "total_commits": 5,
      "share": 0.8,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/sandbox.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/secrets_audit.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/secure_api.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 5,
      "total_commits": 8,
      "share": 0.625,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/sessions.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 4,
      "share": 0.5,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/storage.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 2,
      "share": 0.5,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/thread_audit.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/tool_schemas.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/transcript.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/tts.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 7,
      "total_commits": 8,
      "share": 0.875,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/type_coverage.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/validation.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 3,
      "total_commits": 3,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/workspace.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 2,
      "share": 0.5,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/data/__init__.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-06-06"
    },
    {
      "module": "mythic_agent/data/data_loader.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 3,
      "share": 0.6667,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/doctor.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 3,
      "total_commits": 3,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/integrations/__init__.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-09"
    },
    {
      "module": "mythic_agent/integrations/github.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/knowledge/__init__.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-09"
    },
    {
      "module": "mythic_agent/knowledge/graph.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/mcp_server.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 3,
      "total_commits": 6,
      "share": 0.5,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/memory/__init__.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-06-06"
    },
    {
      "module": "mythic_agent/memory/core_memory.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 3,
      "total_commits": 5,
      "share": 0.6,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/memory/long_term.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/memory/preferences.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/memory/scopes.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/memory/vector_db.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 6,
      "total_commits": 8,
      "share": 0.75,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/onboarding.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/providers/__init__.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-09"
    },
    {
      "module": "mythic_agent/providers/anthropic.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/providers/base.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/providers/google.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/providers/ollama.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/providers/registry.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/resources.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 3,
      "share": 0.6667,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/terminal.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 4,
      "total_commits": 7,
      "share": 0.5714,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/tools/__init__.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-09"
    },
    {
      "module": "mythic_agent/tools/code_index.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/tools/docgen.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/tools/review.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/tools/smart_files.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/tutorials.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 2,
      "share": 0.5,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/ui/__init__.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 2,
      "share": 0.5,
      "last_touch": "2026-10-09"
    },
    {
      "module": "mythic_agent/ui/components/__init__.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-06-06"
    },
    {
      "module": "mythic_agent/ui/components/modals.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 4,
      "total_commits": 5,
      "share": 0.8,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/ui/components/subagent_editor.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 7,
      "total_commits": 8,
      "share": 0.875,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/ui/components/subagent_modal.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 2,
      "total_commits": 3,
      "share": 0.6667,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/ui/main_app.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 6,
      "total_commits": 8,
      "share": 0.75,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/ui/markdown.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/ui/screens/__init__.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-06-06"
    },
    {
      "module": "mythic_agent/ui/screens/chat_screen.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 30,
      "total_commits": 33,
      "share": 0.9091,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/ui/screens/setup_screen.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 10,
      "total_commits": 11,
      "share": 0.9091,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/ui/screens/splash_screen.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 2,
      "total_commits": 3,
      "share": 0.6667,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/ui/shortcuts.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/ui/themes.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/workflow/__init__.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-09"
    },
    {
      "module": "mythic_agent/workflow/slice_runner.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-10"
    }
  ],
  "rollup": [
    {
      "author": "Yrsa Freydisdottir",
      "modules_owned": 66,
      "file_commits": 128
    },
    {
      "author": "Volmarr Wyrd",
      "modules_owned": 29,
      "file_commits": 178
    }
  ],
  "total_modules": 95
}
```
