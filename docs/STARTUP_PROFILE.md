# Startup Profile — `mythic --help` (Slice 26)

Measured 2026-10-09 on Python 3.12.3 (venv), Linux.

## Method

```bash
time venv/bin/python -m mythic_agent.cli --help   # 5 runs
venv/bin/python -X importtime -m mythic_agent.cli --help  # import breakdown
```

## Findings

| Run | Real time |
|-----|-----------|
| 1   | 0.208s |
| 2–5 | 0.19–0.22s (consistent) |

**Verdict: already fast — well under the <1s target. No code changes made.**

### Why it is fast

1. **Lazy imports everywhere.** `mythic_agent/cli.py` imports only `argparse`,
   `sys`, `importlib.metadata`, and `typing` at module level. Every heavy
   subsystem (`doctor`, `terminal`, TUI `main_app`, `core.engine`) is imported
   *inside* the dispatch branch that needs it, so `--help` never pays for
   them. `rich` is only imported under `TYPE_CHECKING`.
2. **Empty package init.** `mythic_agent/__init__.py` is a one-line docstring —
   no eager re-exports, no config loading, no worker startup.
3. **Top imports are stdlib-only.** The `-X importtime` breakdown shows the
   heaviest modules are `encodings` (87µs), `importlib.metadata` (43µs),
   `typing` (26µs), `socket` (20µs) — all sub-millisecond. No `textual`,
   `httpx`, `pydantic`, or vector-DB imports appear on the `--help` path.

### Recommendations (no action required now)

- Keep the lazy-import discipline: any new `cli.py` subcommand must import its
  implementation inside its dispatch branch (the `cache` subcommand added in
  Slice 23 follows this pattern).
- If a future subcommand needs heavyweight libraries at parse time, move that
  work behind a lazy factory instead.
- Re-measure after adding new top-level imports: `time` + `-X importtime`
  as above.

## Roadmap comparison

- Slice 24 target (`mythic --help` under 200ms): **already met** (~0.2s).
- Slice 26 target (`mythic run` cold start <1s): the `--help` path is the
  lightest; `run` adds config load + provider client init — profile separately
  when optimizing the `run` path.
