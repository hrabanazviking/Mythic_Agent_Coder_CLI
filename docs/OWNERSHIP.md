# Source Ownership Map

> **GENERATED FILE — do not edit by hand.**
> Regenerate with: `python scripts/gen_ownership.py`
> Generated at: 2026-11-09T02:34:32Z

Ownership is derived from real git history: for each module the owner is the top author by commit count touching that file (ties resolve to the most recently active author). Share is the owner's commit count divided by the total commit count on the file.

## Per-author rollup

Total modules: **276**

| Author | Modules owned | File commits | Share of modules |
| --- | ---: | ---: | ---: |
| Yrsa Freydisdottir | 161 | 279 | 58.3% |
| Volmarr Wyrd | 115 | 628 | 41.7% |

## Per-module ownership

| Module | Owner | Owner share | Commits (owner / total) | Last touch |
| --- | --- | ---: | ---: | --- |
| `mythic_agent/__init__.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-06-05 |
| `mythic_agent/__version__.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-09 |
| `mythic_agent/agents/__init__.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-06-06 |
| `mythic_agent/agents/command_handler.py` | Volmarr Wyrd | 65.5% | 93 / 142 | 2026-11-08 |
| `mythic_agent/agents/context.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/agents/llm.py` | Volmarr Wyrd | 69.1% | 114 / 165 | 2026-11-08 |
| `mythic_agent/agents/parallel.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/agents/planning.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/agents/prompts.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/agents/recovery.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/agents/tasks.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/agents/tools.py` | Volmarr Wyrd | 60.7% | 17 / 28 | 2026-11-06 |
| `mythic_agent/bench.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/cli.py` | Volmarr Wyrd | 66.7% | 8 / 12 | 2026-11-01 |
| `mythic_agent/constants.py` | Volmarr Wyrd | 85.7% | 6 / 7 | 2026-10-10 |
| `mythic_agent/context/__init__.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-11 |
| `mythic_agent/context/budget.py` | Yrsa Freydisdottir | 100.0% | 3 / 3 | 2026-10-30 |
| `mythic_agent/context/compiler.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-11 |
| `mythic_agent/context/deps.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-11 |
| `mythic_agent/context/files.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-11 |
| `mythic_agent/context/gitdiff.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-11 |
| `mythic_agent/context/groups.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-11 |
| `mythic_agent/context/instructions.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-11 |
| `mythic_agent/context/repo_map.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-01 |
| `mythic_agent/context/repo_map_view.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-01 |
| `mythic_agent/context/runtime.py` | Yrsa Freydisdottir | 100.0% | 3 / 3 | 2026-11-01 |
| `mythic_agent/context/semantic.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-11 |
| `mythic_agent/context/symbol_graph.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-11-01 |
| `mythic_agent/context/symbols.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-11 |
| `mythic_agent/core/__init__.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-06-06 |
| `mythic_agent/core/accessibility_baseline.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-31 |
| `mythic_agent/core/apply_repair.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-02 |
| `mythic_agent/core/approval_moments.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/arcanum_review.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/arch_conformance.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/audio.py` | Volmarr Wyrd | 57.1% | 4 / 7 | 2026-10-31 |
| `mythic_agent/core/audit.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/audit_trail.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/auditor_veto.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/auto_commit.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-05 |
| `mythic_agent/core/background_tasks.py` | Volmarr Wyrd | 100.0% | 2 / 2 | 2026-11-06 |
| `mythic_agent/core/baseline_freeze.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/benchmark_tasks.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/blame_sight.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-06 |
| `mythic_agent/core/budgets.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/cache.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/change_sets.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-05 |
| `mythic_agent/core/character_voices.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/checkpoints.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-05 |
| `mythic_agent/core/commit_craft.py` | Volmarr Wyrd | 50.0% | 1 / 2 | 2026-11-06 |
| `mythic_agent/core/compaction_glassbox.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/config_catalog.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/config_manager.py` | Volmarr Wyrd | 75.0% | 9 / 12 | 2026-10-11 |
| `mythic_agent/core/conflict_workbench.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-05 |
| `mythic_agent/core/context_budget.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/context_recipes.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/cost_court.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/cost_routing.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/costs.py` | Yrsa Freydisdottir | 100.0% | 3 / 3 | 2026-10-10 |
| `mythic_agent/core/crew_comms.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/crew_interrupts.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/crew_members.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/crew_memory.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/crew_replay.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/crew_schedules.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/crew_sizing.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/crew_templates.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/cross_project_memory.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/custom_offices.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/dead_code_scan.py` | Yrsa Freydisdottir | 100.0% | 3 / 3 | 2026-11-02 |
| `mythic_agent/core/deadlock_watch.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/decision_records.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/dependency_census.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/destructive_doctrine.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/determinism.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-10 |
| `mythic_agent/core/diff_theatre.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-06 |
| `mythic_agent/core/dogfood.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/edit_formats.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-11-02 |
| `mythic_agent/core/editor_bridge.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-06 |
| `mythic_agent/core/edits.py` | Volmarr Wyrd | 66.7% | 4 / 6 | 2026-11-06 |
| `mythic_agent/core/engine.py` | Volmarr Wyrd | 55.6% | 5 / 9 | 2026-10-10 |
| `mythic_agent/core/exceptions.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-10 |
| `mythic_agent/core/execution.py` | Yrsa Freydisdottir | 60.0% | 6 / 10 | 2026-10-10 |
| `mythic_agent/core/external_agents.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/failure_fostering.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/fallback_chain.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/feature_census.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-30 |
| `mythic_agent/core/file_guardians.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-05 |
| `mythic_agent/core/fleet_mode.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/forget_quarantine.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/gap_audit.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-30 |
| `mythic_agent/core/generated_code.py` | Volmarr Wyrd | 100.0% | 2 / 2 | 2026-11-06 |
| `mythic_agent/core/graph_retrieval.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/hash_anchored.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-11-02 |
| `mythic_agent/core/heterogeneous_crews.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/hook_packs.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-06 |
| `mythic_agent/core/hooks.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-06 |
| `mythic_agent/core/hunk_review.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-03 |
| `mythic_agent/core/instruction_files.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/issue_slice.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-05 |
| `mythic_agent/core/journal.py` | Yrsa Freydisdottir | 100.0% | 4 / 4 | 2026-10-10 |
| `mythic_agent/core/keeper.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-06 |
| `mythic_agent/core/key_custody.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/kill_switch.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/language_packs.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-02 |
| `mythic_agent/core/large_file_care.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-06 |
| `mythic_agent/core/lifecycle.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-10 |
| `mythic_agent/core/long_context.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-01 |
| `mythic_agent/core/mass_edit_guard.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-06 |
| `mythic_agent/core/mentions.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/merge_discipline.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/method_charter.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/metrics.py` | Yrsa Freydisdottir | 100.0% | 3 / 3 | 2026-10-10 |
| `mythic_agent/core/model_capabilities.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/model_switch.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/multi_repo.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/mythic_logging.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/network_gates.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-06 |
| `mythic_agent/core/notifications.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/offices.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/offline_grace.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/offline_honesty.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-01 |
| `mythic_agent/core/os_sandbox.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-06 |
| `mythic_agent/core/part1_gate.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/part2_gate.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-01 |
| `mythic_agent/core/part3_gate.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-02 |
| `mythic_agent/core/part4_gate.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-06 |
| `mythic_agent/core/part5_gate.py` | Volmarr Wyrd | 100.0% | 2 / 2 | 2026-11-07 |
| `mythic_agent/core/part6_gate.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/patch_exchange.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-06 |
| `mythic_agent/core/path_jail.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-06 |
| `mythic_agent/core/permission_profiles.py` | Volmarr Wyrd | 100.0% | 2 / 2 | 2026-11-06 |
| `mythic_agent/core/plan_mode.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-06 |
| `mythic_agent/core/platform_truth.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/policy.py` | Volmarr Wyrd | 66.7% | 2 / 3 | 2026-10-10 |
| `mythic_agent/core/policy_file.py` | Volmarr Wyrd | 100.0% | 2 / 2 | 2026-11-07 |
| `mythic_agent/core/pr_craft.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-05 |
| `mythic_agent/core/progress.py` | Yrsa Freydisdottir | 100.0% | 3 / 3 | 2026-10-10 |
| `mythic_agent/core/project_memory_map.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/provider_health.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-01 |
| `mythic_agent/core/provider_registry.py` | Yrsa Freydisdottir | 100.0% | 3 / 3 | 2026-10-31 |
| `mythic_agent/core/provider_test_kit.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-01 |
| `mythic_agent/core/rate_limit_weather.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/recovery.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/red_team.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/redaction.py` | Yrsa Freydisdottir | 80.0% | 4 / 5 | 2026-10-10 |
| `mythic_agent/core/remembered_approvals.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-06 |
| `mythic_agent/core/remote_work.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/rename_move.py` | Volmarr Wyrd | 100.0% | 2 / 2 | 2026-11-06 |
| `mythic_agent/core/repo_census.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/research_swarms.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/retry_honesty.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-01 |
| `mythic_agent/core/review_panels.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/rival_config_study.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/roadmap_slices.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/role_routing.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/rollback_drills.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/runtime.py` | Volmarr Wyrd | 80.0% | 4 / 5 | 2026-10-10 |
| `mythic_agent/core/safety_regression.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/sandbox.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/scheduled_work.py` | Volmarr Wyrd | 100.0% | 2 / 2 | 2026-11-06 |
| `mythic_agent/core/secret_hygiene.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/secrets_audit.py` | Yrsa Freydisdottir | 100.0% | 3 / 3 | 2026-10-10 |
| `mythic_agent/core/secure_api.py` | Volmarr Wyrd | 62.5% | 5 / 8 | 2026-10-10 |
| `mythic_agent/core/self_improving_ledger.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/session_branching.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-05 |
| `mythic_agent/core/session_catalog.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/session_memory.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/sessions.py` | Volmarr Wyrd | 50.0% | 3 / 6 | 2026-11-05 |
| `mythic_agent/core/solo_mode.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/stand_ups.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-08 |
| `mythic_agent/core/stash_shelf.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-06 |
| `mythic_agent/core/storage.py` | Yrsa Freydisdottir | 66.7% | 2 / 3 | 2026-10-10 |
| `mythic_agent/core/streaming_discipline.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-01 |
| `mythic_agent/core/subscription_doors.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/task_dealing.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/core/telemetry_review.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/terminology.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/thread_audit.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-10 |
| `mythic_agent/core/tool_schemas.py` | Yrsa Freydisdottir | 100.0% | 3 / 3 | 2026-11-02 |
| `mythic_agent/core/transcript.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/tree_sitter_foundation.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-01 |
| `mythic_agent/core/tts.py` | Volmarr Wyrd | 87.5% | 7 / 8 | 2026-10-10 |
| `mythic_agent/core/type_coverage.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/core/undo_timeline.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-05 |
| `mythic_agent/core/ux_charter.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/validation.py` | Yrsa Freydisdottir | 100.0% | 3 / 3 | 2026-10-10 |
| `mythic_agent/core/vision_routing.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/core/workspace.py` | Yrsa Freydisdottir | 66.7% | 2 / 3 | 2026-10-10 |
| `mythic_agent/core/worktrees.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-11-07 |
| `mythic_agent/data/__init__.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-06-06 |
| `mythic_agent/data/data_loader.py` | Yrsa Freydisdottir | 66.7% | 2 / 3 | 2026-10-10 |
| `mythic_agent/doctor.py` | Yrsa Freydisdottir | 100.0% | 5 / 5 | 2026-11-01 |
| `mythic_agent/integrations/__init__.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-09 |
| `mythic_agent/integrations/github.py` | Yrsa Freydisdottir | 66.7% | 2 / 3 | 2026-11-05 |
| `mythic_agent/integrations/lsp.py` | Yrsa Freydisdottir | 80.0% | 4 / 5 | 2026-11-06 |
| `mythic_agent/knowledge/__init__.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-09 |
| `mythic_agent/knowledge/graph.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/mcp_server.py` | Yrsa Freydisdottir | 57.1% | 4 / 7 | 2026-10-31 |
| `mythic_agent/memory/__init__.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-06-06 |
| `mythic_agent/memory/core_memory.py` | Volmarr Wyrd | 60.0% | 3 / 5 | 2026-10-10 |
| `mythic_agent/memory/long_term.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/memory/preferences.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/memory/scopes.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/memory/vector_db.py` | Volmarr Wyrd | 75.0% | 6 / 8 | 2026-10-10 |
| `mythic_agent/onboarding.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/providers/__init__.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-09 |
| `mythic_agent/providers/aesir.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/providers/anthropic.py` | Yrsa Freydisdottir | 100.0% | 5 / 5 | 2026-10-31 |
| `mythic_agent/providers/base.py` | Yrsa Freydisdottir | 100.0% | 4 / 4 | 2026-10-11 |
| `mythic_agent/providers/capabilities.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-10 |
| `mythic_agent/providers/conformance.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-11 |
| `mythic_agent/providers/context_windows.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-10 |
| `mythic_agent/providers/cost_ledger.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-11 |
| `mythic_agent/providers/deepseek.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-10 |
| `mythic_agent/providers/failover.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-11 |
| `mythic_agent/providers/gateways.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-31 |
| `mythic_agent/providers/google.py` | Yrsa Freydisdottir | 100.0% | 7 / 7 | 2026-10-31 |
| `mythic_agent/providers/health.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-11 |
| `mythic_agent/providers/llamacpp.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-31 |
| `mythic_agent/providers/lmstudio.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-31 |
| `mythic_agent/providers/model_registry.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-10 |
| `mythic_agent/providers/ollama.py` | Yrsa Freydisdottir | 100.0% | 5 / 5 | 2026-10-31 |
| `mythic_agent/providers/openai_compat.py` | Yrsa Freydisdottir | 100.0% | 3 / 3 | 2026-10-31 |
| `mythic_agent/providers/openrouter.py` | Yrsa Freydisdottir | 100.0% | 4 / 4 | 2026-10-31 |
| `mythic_agent/providers/reasoning.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-11 |
| `mythic_agent/providers/registry.py` | Yrsa Freydisdottir | 100.0% | 5 / 5 | 2026-10-31 |
| `mythic_agent/providers/streaming.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-11 |
| `mythic_agent/providers/structured_output.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-11 |
| `mythic_agent/providers/tool_negotiation.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-10 |
| `mythic_agent/providers/usage.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-11 |
| `mythic_agent/providers/vision.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-31 |
| `mythic_agent/providers/vllm.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-10 |
| `mythic_agent/resources.py` | Yrsa Freydisdottir | 66.7% | 2 / 3 | 2026-10-10 |
| `mythic_agent/terminal.py` | Volmarr Wyrd | 66.9% | 91 / 136 | 2026-11-08 |
| `mythic_agent/tools/__init__.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-10-09 |
| `mythic_agent/tools/asset_sight.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-02 |
| `mythic_agent/tools/code_index.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/tools/code_sensing.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-02 |
| `mythic_agent/tools/config_sight.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-11-02 |
| `mythic_agent/tools/coverage_sight.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-02 |
| `mythic_agent/tools/debug_loop.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-01 |
| `mythic_agent/tools/debugger.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-11-01 |
| `mythic_agent/tools/dependency_sight.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-02 |
| `mythic_agent/tools/docgen.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/tools/docs_at_hand.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-02 |
| `mythic_agent/tools/edit_truth.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-11-01 |
| `mythic_agent/tools/format_covenant.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-01 |
| `mythic_agent/tools/intelligence_cache.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-02 |
| `mythic_agent/tools/language_packs.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-02 |
| `mythic_agent/tools/local_search.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-02 |
| `mythic_agent/tools/mojo_sight.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-02 |
| `mythic_agent/tools/review.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/tools/smart_files.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/tools/sql_sight.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-11-02 |
| `mythic_agent/tools/structural_rewrite.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-01 |
| `mythic_agent/tools/structural_search.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-11-01 |
| `mythic_agent/tools/test_intelligence.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-02 |
| `mythic_agent/tools/type_depth.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-02 |
| `mythic_agent/tools/web_search.py` | Yrsa Freydisdottir | 100.0% | 1 / 1 | 2026-11-02 |
| `mythic_agent/tutorials.py` | Yrsa Freydisdottir | 50.0% | 1 / 2 | 2026-10-10 |
| `mythic_agent/ui/__init__.py` | Yrsa Freydisdottir | 50.0% | 1 / 2 | 2026-10-09 |
| `mythic_agent/ui/components/__init__.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-06-06 |
| `mythic_agent/ui/components/modals.py` | Volmarr Wyrd | 80.0% | 4 / 5 | 2026-10-10 |
| `mythic_agent/ui/components/subagent_editor.py` | Volmarr Wyrd | 87.5% | 7 / 8 | 2026-10-10 |
| `mythic_agent/ui/components/subagent_modal.py` | Volmarr Wyrd | 66.7% | 2 / 3 | 2026-10-10 |
| `mythic_agent/ui/main_app.py` | Volmarr Wyrd | 75.0% | 6 / 8 | 2026-10-10 |
| `mythic_agent/ui/markdown.py` | Yrsa Freydisdottir | 100.0% | 2 / 2 | 2026-10-10 |
| `mythic_agent/ui/screens/__init__.py` | Volmarr Wyrd | 100.0% | 1 / 1 | 2026-06-06 |
| `mythic_agent/ui/screens/chat_screen.py` | Volmarr Wyrd | 80.3% | 118 / 147 | 2026-11-08 |
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
      "owner_commits": 93,
      "total_commits": 142,
      "share": 0.6549,
      "last_touch": "2026-11-08"
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
      "owner_commits": 114,
      "total_commits": 165,
      "share": 0.6909,
      "last_touch": "2026-11-08"
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
      "owner_commits": 17,
      "total_commits": 28,
      "share": 0.6071,
      "last_touch": "2026-11-06"
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
      "total_commits": 12,
      "share": 0.6667,
      "last_touch": "2026-11-01"
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
      "module": "mythic_agent/context/__init__.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-11"
    },
    {
      "module": "mythic_agent/context/budget.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 3,
      "total_commits": 3,
      "share": 1.0,
      "last_touch": "2026-10-30"
    },
    {
      "module": "mythic_agent/context/compiler.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-11"
    },
    {
      "module": "mythic_agent/context/deps.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-11"
    },
    {
      "module": "mythic_agent/context/files.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-11"
    },
    {
      "module": "mythic_agent/context/gitdiff.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-11"
    },
    {
      "module": "mythic_agent/context/groups.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-11"
    },
    {
      "module": "mythic_agent/context/instructions.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-11"
    },
    {
      "module": "mythic_agent/context/repo_map.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-01"
    },
    {
      "module": "mythic_agent/context/repo_map_view.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-01"
    },
    {
      "module": "mythic_agent/context/runtime.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 3,
      "total_commits": 3,
      "share": 1.0,
      "last_touch": "2026-11-01"
    },
    {
      "module": "mythic_agent/context/semantic.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-11"
    },
    {
      "module": "mythic_agent/context/symbol_graph.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-11-01"
    },
    {
      "module": "mythic_agent/context/symbols.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-11"
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
      "module": "mythic_agent/core/accessibility_baseline.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/apply_repair.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-02"
    },
    {
      "module": "mythic_agent/core/approval_moments.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/arcanum_review.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
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
      "total_commits": 7,
      "share": 0.5714,
      "last_touch": "2026-10-31"
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
      "module": "mythic_agent/core/audit_trail.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/auditor_veto.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/auto_commit.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-05"
    },
    {
      "module": "mythic_agent/core/background_tasks.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/baseline_freeze.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/benchmark_tasks.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/blame_sight.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/budgets.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
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
      "module": "mythic_agent/core/change_sets.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-05"
    },
    {
      "module": "mythic_agent/core/character_voices.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/checkpoints.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-05"
    },
    {
      "module": "mythic_agent/core/commit_craft.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 2,
      "share": 0.5,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/compaction_glassbox.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/config_catalog.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/config_manager.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 9,
      "total_commits": 12,
      "share": 0.75,
      "last_touch": "2026-10-11"
    },
    {
      "module": "mythic_agent/core/conflict_workbench.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-05"
    },
    {
      "module": "mythic_agent/core/context_budget.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/context_recipes.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/cost_court.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/cost_routing.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/costs.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 3,
      "total_commits": 3,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/crew_comms.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/crew_interrupts.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/crew_members.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/crew_memory.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/crew_replay.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/crew_schedules.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/crew_sizing.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/crew_templates.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/cross_project_memory.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/custom_offices.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/dead_code_scan.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 3,
      "total_commits": 3,
      "share": 1.0,
      "last_touch": "2026-11-02"
    },
    {
      "module": "mythic_agent/core/deadlock_watch.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/decision_records.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/dependency_census.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/destructive_doctrine.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
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
      "module": "mythic_agent/core/diff_theatre.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/dogfood.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/edit_formats.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-11-02"
    },
    {
      "module": "mythic_agent/core/editor_bridge.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/edits.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 4,
      "total_commits": 6,
      "share": 0.6667,
      "last_touch": "2026-11-06"
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
      "module": "mythic_agent/core/external_agents.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/failure_fostering.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/fallback_chain.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/feature_census.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-30"
    },
    {
      "module": "mythic_agent/core/file_guardians.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-05"
    },
    {
      "module": "mythic_agent/core/fleet_mode.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/forget_quarantine.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/gap_audit.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-30"
    },
    {
      "module": "mythic_agent/core/generated_code.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/graph_retrieval.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/hash_anchored.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-11-02"
    },
    {
      "module": "mythic_agent/core/heterogeneous_crews.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/hook_packs.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/hooks.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/hunk_review.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-03"
    },
    {
      "module": "mythic_agent/core/instruction_files.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/issue_slice.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-05"
    },
    {
      "module": "mythic_agent/core/journal.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 4,
      "total_commits": 4,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/keeper.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/key_custody.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/kill_switch.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/language_packs.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-02"
    },
    {
      "module": "mythic_agent/core/large_file_care.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-06"
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
      "module": "mythic_agent/core/long_context.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-01"
    },
    {
      "module": "mythic_agent/core/mass_edit_guard.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/mentions.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/merge_discipline.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/method_charter.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
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
      "module": "mythic_agent/core/model_capabilities.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/model_switch.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/multi_repo.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
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
      "module": "mythic_agent/core/network_gates.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-06"
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
      "module": "mythic_agent/core/offices.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/offline_grace.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/offline_honesty.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-01"
    },
    {
      "module": "mythic_agent/core/os_sandbox.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/part1_gate.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/part2_gate.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-01"
    },
    {
      "module": "mythic_agent/core/part3_gate.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-02"
    },
    {
      "module": "mythic_agent/core/part4_gate.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/part5_gate.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/part6_gate.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/patch_exchange.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/path_jail.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/permission_profiles.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/plan_mode.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/platform_truth.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
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
      "module": "mythic_agent/core/policy_file.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/pr_craft.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-05"
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
      "module": "mythic_agent/core/project_memory_map.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/provider_health.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-01"
    },
    {
      "module": "mythic_agent/core/provider_registry.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 3,
      "total_commits": 3,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/provider_test_kit.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-01"
    },
    {
      "module": "mythic_agent/core/rate_limit_weather.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
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
      "module": "mythic_agent/core/red_team.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/redaction.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 4,
      "total_commits": 5,
      "share": 0.8,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/remembered_approvals.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/remote_work.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/rename_move.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-11-06"
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
      "module": "mythic_agent/core/research_swarms.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/retry_honesty.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-01"
    },
    {
      "module": "mythic_agent/core/review_panels.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/rival_config_study.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/roadmap_slices.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/role_routing.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/rollback_drills.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
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
      "module": "mythic_agent/core/safety_regression.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
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
      "module": "mythic_agent/core/scheduled_work.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/secret_hygiene.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/secrets_audit.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 3,
      "total_commits": 3,
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
      "module": "mythic_agent/core/self_improving_ledger.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/session_branching.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-05"
    },
    {
      "module": "mythic_agent/core/session_catalog.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/session_memory.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/sessions.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 3,
      "total_commits": 6,
      "share": 0.5,
      "last_touch": "2026-11-05"
    },
    {
      "module": "mythic_agent/core/solo_mode.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/stand_ups.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-08"
    },
    {
      "module": "mythic_agent/core/stash_shelf.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-06"
    },
    {
      "module": "mythic_agent/core/storage.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 3,
      "share": 0.6667,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/streaming_discipline.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-01"
    },
    {
      "module": "mythic_agent/core/subscription_doors.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/task_dealing.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
    },
    {
      "module": "mythic_agent/core/telemetry_review.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/terminology.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
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
      "owner_commits": 3,
      "total_commits": 3,
      "share": 1.0,
      "last_touch": "2026-11-02"
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
      "module": "mythic_agent/core/tree_sitter_foundation.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-01"
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
      "module": "mythic_agent/core/undo_timeline.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-05"
    },
    {
      "module": "mythic_agent/core/ux_charter.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
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
      "module": "mythic_agent/core/vision_routing.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/core/workspace.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 3,
      "share": 0.6667,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/core/worktrees.py",
      "owner": "Volmarr Wyrd",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-07"
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
      "owner_commits": 5,
      "total_commits": 5,
      "share": 1.0,
      "last_touch": "2026-11-01"
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
      "total_commits": 3,
      "share": 0.6667,
      "last_touch": "2026-11-05"
    },
    {
      "module": "mythic_agent/integrations/lsp.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 4,
      "total_commits": 5,
      "share": 0.8,
      "last_touch": "2026-11-06"
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
      "owner_commits": 4,
      "total_commits": 7,
      "share": 0.5714,
      "last_touch": "2026-10-31"
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
      "module": "mythic_agent/providers/aesir.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/providers/anthropic.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 5,
      "total_commits": 5,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/providers/base.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 4,
      "total_commits": 4,
      "share": 1.0,
      "last_touch": "2026-10-11"
    },
    {
      "module": "mythic_agent/providers/capabilities.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/providers/conformance.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-11"
    },
    {
      "module": "mythic_agent/providers/context_windows.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/providers/cost_ledger.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-11"
    },
    {
      "module": "mythic_agent/providers/deepseek.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/providers/failover.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-11"
    },
    {
      "module": "mythic_agent/providers/gateways.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/providers/google.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 7,
      "total_commits": 7,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/providers/health.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-11"
    },
    {
      "module": "mythic_agent/providers/llamacpp.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/providers/lmstudio.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/providers/model_registry.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/providers/ollama.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 5,
      "total_commits": 5,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/providers/openai_compat.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 3,
      "total_commits": 3,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/providers/openrouter.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 4,
      "total_commits": 4,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/providers/reasoning.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-11"
    },
    {
      "module": "mythic_agent/providers/registry.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 5,
      "total_commits": 5,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/providers/streaming.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-11"
    },
    {
      "module": "mythic_agent/providers/structured_output.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-11"
    },
    {
      "module": "mythic_agent/providers/tool_negotiation.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-10"
    },
    {
      "module": "mythic_agent/providers/usage.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-10-11"
    },
    {
      "module": "mythic_agent/providers/vision.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-10-31"
    },
    {
      "module": "mythic_agent/providers/vllm.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
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
      "owner_commits": 91,
      "total_commits": 136,
      "share": 0.6691,
      "last_touch": "2026-11-08"
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
      "module": "mythic_agent/tools/asset_sight.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-02"
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
      "module": "mythic_agent/tools/code_sensing.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-02"
    },
    {
      "module": "mythic_agent/tools/config_sight.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-11-02"
    },
    {
      "module": "mythic_agent/tools/coverage_sight.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-02"
    },
    {
      "module": "mythic_agent/tools/debug_loop.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-01"
    },
    {
      "module": "mythic_agent/tools/debugger.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-11-01"
    },
    {
      "module": "mythic_agent/tools/dependency_sight.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-02"
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
      "module": "mythic_agent/tools/docs_at_hand.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-02"
    },
    {
      "module": "mythic_agent/tools/edit_truth.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-11-01"
    },
    {
      "module": "mythic_agent/tools/format_covenant.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-01"
    },
    {
      "module": "mythic_agent/tools/intelligence_cache.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-02"
    },
    {
      "module": "mythic_agent/tools/language_packs.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-02"
    },
    {
      "module": "mythic_agent/tools/local_search.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-02"
    },
    {
      "module": "mythic_agent/tools/mojo_sight.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-02"
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
      "module": "mythic_agent/tools/sql_sight.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-11-02"
    },
    {
      "module": "mythic_agent/tools/structural_rewrite.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-01"
    },
    {
      "module": "mythic_agent/tools/structural_search.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 2,
      "total_commits": 2,
      "share": 1.0,
      "last_touch": "2026-11-01"
    },
    {
      "module": "mythic_agent/tools/test_intelligence.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-02"
    },
    {
      "module": "mythic_agent/tools/type_depth.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-02"
    },
    {
      "module": "mythic_agent/tools/web_search.py",
      "owner": "Yrsa Freydisdottir",
      "owner_commits": 1,
      "total_commits": 1,
      "share": 1.0,
      "last_touch": "2026-11-02"
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
      "owner_commits": 118,
      "total_commits": 147,
      "share": 0.8027,
      "last_touch": "2026-11-08"
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
      "modules_owned": 161,
      "file_commits": 279
    },
    {
      "author": "Volmarr Wyrd",
      "modules_owned": 115,
      "file_commits": 628
    }
  ],
  "total_modules": 276
}
```
