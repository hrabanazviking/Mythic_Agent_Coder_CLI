# Repository Truth Census — Receipt

*Tool:* `repo_census/R-001` (`mythic_agent.core.repo_census`)
*Generated:* 2026-10-10T09:46:02+00:00 (UTC)
*Digest:* `dd12a4513aff496bc5186b57c2d689cbd7a5dcd768c1c98c265c79d4ecb59053`

## Census

| Measure | Value |
|---|---|
| Package files (`mythic_agent/`) | 88 |
| Code lines (excl. blanks/comments) | 13150 |
| Classes | 123 |
| Functions | 806 |
| Test files (`tests/`) | 44 |
| Collected tests | 502 |
| Modules | 88 |

## Modules (88)

- `mythic_agent`
- `mythic_agent.__version__`
- `mythic_agent.agents`
- `mythic_agent.agents.command_handler`
- `mythic_agent.agents.context`
- `mythic_agent.agents.llm`
- `mythic_agent.agents.parallel`
- `mythic_agent.agents.planning`
- `mythic_agent.agents.prompts`
- `mythic_agent.agents.recovery`
- `mythic_agent.agents.tasks`
- `mythic_agent.agents.tools`
- `mythic_agent.bench`
- `mythic_agent.cli`
- `mythic_agent.constants`
- `mythic_agent.core`
- `mythic_agent.core.audio`
- `mythic_agent.core.audit`
- `mythic_agent.core.cache`
- `mythic_agent.core.config_manager`
- `mythic_agent.core.costs`
- `mythic_agent.core.dead_code_scan`
- `mythic_agent.core.edits`
- `mythic_agent.core.engine`
- `mythic_agent.core.execution`
- `mythic_agent.core.journal`
- `mythic_agent.core.metrics`
- `mythic_agent.core.mythic_logging`
- `mythic_agent.core.notifications`
- `mythic_agent.core.policy`
- `mythic_agent.core.progress`
- `mythic_agent.core.redaction`
- `mythic_agent.core.repo_census`
- `mythic_agent.core.runtime`
- `mythic_agent.core.sandbox`
- `mythic_agent.core.secrets_audit`
- `mythic_agent.core.secure_api`
- `mythic_agent.core.sessions`
- `mythic_agent.core.storage`
- `mythic_agent.core.transcript`
- `mythic_agent.core.tts`
- `mythic_agent.core.type_coverage`
- `mythic_agent.core.validation`
- `mythic_agent.core.workspace`
- `mythic_agent.data`
- `mythic_agent.data.data_loader`
- `mythic_agent.doctor`
- `mythic_agent.integrations`
- `mythic_agent.integrations.github`
- `mythic_agent.knowledge`
- `mythic_agent.knowledge.graph`
- `mythic_agent.mcp_server`
- `mythic_agent.memory`
- `mythic_agent.memory.core_memory`
- `mythic_agent.memory.long_term`
- `mythic_agent.memory.preferences`
- `mythic_agent.memory.scopes`
- `mythic_agent.memory.vector_db`
- `mythic_agent.onboarding`
- `mythic_agent.providers`
- `mythic_agent.providers.anthropic`
- `mythic_agent.providers.base`
- `mythic_agent.providers.google`
- `mythic_agent.providers.ollama`
- `mythic_agent.providers.registry`
- `mythic_agent.resources`
- `mythic_agent.terminal`
- `mythic_agent.tools`
- `mythic_agent.tools.code_index`
- `mythic_agent.tools.docgen`
- `mythic_agent.tools.review`
- `mythic_agent.tools.smart_files`
- `mythic_agent.tutorials`
- `mythic_agent.ui`
- `mythic_agent.ui.components`
- `mythic_agent.ui.components.modals`
- `mythic_agent.ui.components.subagent_editor`
- `mythic_agent.ui.components.subagent_modal`
- `mythic_agent.ui.main_app`
- `mythic_agent.ui.markdown`
- `mythic_agent.ui.screens`
- `mythic_agent.ui.screens.chat_screen`
- `mythic_agent.ui.screens.setup_screen`
- `mythic_agent.ui.screens.splash_screen`
- `mythic_agent.ui.shortcuts`
- `mythic_agent.ui.themes`
- `mythic_agent.workflow`
- `mythic_agent.workflow.slice_runner`

## How to regenerate

This document is **generated from the tool** — do not hand-edit the
numbers. Re-run from the repository root with the project venv:

```sh
./venv/bin/python -m mythic_agent.core.repo_census receipt \
    --out docs/REPO_CENSUS.md
```

The JSON snapshot equivalent:

```sh
./venv/bin/python -m mythic_agent.core.repo_census snapshot \
    --out docs/REPO_CENSUS.json
```

Drift check against a snapshot:

```python
from mythic_agent.core.repo_census import verify_snapshot
drift = verify_snapshot("docs/REPO_CENSUS.json")
assert not drift, drift
```
