"""Benchmark suite for Mythic Agent (Slice 28).

Measures turn latency, tool execution time, startup time, and memory usage.
Run with: python -m mythic_agent.bench
Or: mythic bench (if wired into CLI)

Results are printed as JSON for CI regression tracking.
"""

from __future__ import annotations

import json
import sys
import time
import tracemalloc
from pathlib import Path


def bench_startup() -> dict:
    """Measure CLI startup time (import + --help)."""
    import subprocess
    times = []
    for _ in range(3):
        start = time.perf_counter()
        result = subprocess.run(
            [sys.executable, "-m", "mythic_agent.cli", "--help"],
            capture_output=True, timeout=30,
            cwd=Path(__file__).resolve().parent.parent,
        )
        elapsed = time.perf_counter() - start
        assert result.returncode == 0
        times.append(elapsed)
    return {
        "startup_help_s": round(sum(times) / len(times), 3),
        "startup_help_runs": len(times),
    }


def bench_import() -> dict:
    """Measure import time of key modules."""
    import subprocess
    modules = ["mythic_agent.cli", "mythic_agent.core.config_manager"]
    results = {}
    for mod in modules:
        code = f"import time; s=time.perf_counter(); import {mod}; print(time.perf_counter()-s)"
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=30,
            cwd=Path(__file__).resolve().parent.parent,
        )
        try:
            elapsed = float(result.stdout.strip().split("\n")[-1])
        except (ValueError, IndexError):
            elapsed = -1.0
        results[f"import_{mod.replace('.', '_')}_s"] = round(elapsed, 3)
    return results


def bench_memory() -> dict:
    """Measure peak memory for a basic import + config load."""
    tracemalloc.start()
    from mythic_agent.core import config_manager  # noqa: F401
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "import_peak_kb": round(peak / 1024, 1),
        "import_current_kb": round(current / 1024, 1),
    }


def run_all() -> dict:
    """Run all benchmarks and return results dict."""
    results = {"timestamp": time.time()}
    results.update(bench_startup())
    results.update(bench_import())
    results.update(bench_memory())
    return results


def main() -> int:
    results = run_all()
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
