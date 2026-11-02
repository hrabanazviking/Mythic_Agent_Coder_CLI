#!/usr/bin/env python3
"""New-provider conformance script (All-Features roadmap slice M-041).

The ship gate for a new registry entry: run the five kit
checks (registry, chat, tools, streaming, errors) against the
entry's door and state the pass/fail evidence plainly, per
check. The kit's live road is the M-020 universal adapter —
the road a new OpenAI-compatible entry joins.

Usage:
    python scripts/provider_test_kit.py <provider> [--base-url URL]
                                        [--model MODEL] [--json]
                                        [--out REPORT.json]

Exit 0 iff the verdict is ``passed`` (nothing failed and chat
was actually proven); 1 on ``failed`` or ``not-proven``;
2 on a usage error (including an unknown provider name).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mythic_agent.core.provider_test_kit import (  # noqa: E402
    format_kit_status,
    run_kit,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the new-provider test kit against a "
                    "registry entry's door (M-041).")
    parser.add_argument("provider",
                        help="Registry provider name (aliases resolve)")
    parser.add_argument("--base-url",
                        help="Aim the kit at another door for this entry")
    parser.add_argument("--model", help="Model override for the kit run")
    parser.add_argument("--json", action="store_true",
                        help="Emit the report as JSON")
    parser.add_argument("--out", help="Also write the JSON report here")
    args = parser.parse_args(argv)
    try:
        report = run_kit(args.provider, base_url=args.base_url,
                         model=args.model)
    except KeyError as exc:
        print(f"provider test kit: {exc}", file=sys.stderr)
        return 2
    record = report.record()
    if args.json:
        print(json.dumps(record, indent=2))
    else:
        print(format_kit_status({"report": record}))
    if args.out:
        Path(args.out).write_text(
            json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return 0 if report.verdict == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
