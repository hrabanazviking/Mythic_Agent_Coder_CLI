#!/usr/bin/env python3
"""Source ownership map generator (roadmap 005 / R-005).

Reads real git history (read-only git commands) and generates
``docs/OWNERSHIP.md``: per-module owner (top author by commit count +
share), last-touch commit date, and a per-author rollup.

Stdlib only. Never commits, never writes anything except the doc.
Usage:
    python scripts/gen_ownership.py [--out PATH]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = REPO_ROOT / "mythic_agent"
DEFAULT_DOC = REPO_ROOT / "docs" / "OWNERSHIP.md"
REGEN_CMD = "python scripts/gen_ownership.py"

# The line carrying the generation timestamp. Tests ignore exactly this line
# (by prefix) when checking freshness; keep it stable and unique.
TIMESTAMP_LINE_PREFIX = "Generated at: "
MACHINE_FENCE = "```json"


class ZeroHistoryError(RuntimeError):
    """Raised when a module has zero git history. Fails LOUDLY, never skips."""


def _git(args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def discover_modules() -> list[str]:
    """All mythic_agent/**/*.py modules, repo-relative POSIX paths, no __pycache__."""
    mods = sorted(
        str(p.relative_to(REPO_ROOT)).replace("\\", "/")
        for p in PACKAGE_DIR.rglob("*.py")
        if "__pycache__" not in p.parts
    )
    if not mods:
        raise RuntimeError("no modules found under mythic_agent/")
    return mods


def ownership_for_file(rel: str) -> dict:
    """Owner data for one module. All authorship comes from real `git log`."""
    authors = [
        line for line in _git(["log", "--format=%an", "--", rel]).splitlines() if line
    ]
    if not authors:
        raise ZeroHistoryError(f"module has zero git history: {rel}")
    counts = Counter(authors)
    total = sum(counts.values())
    top_author, top_n = counts.most_common(1)[0]
    last_touch = _git(
        ["log", "-1", "--format=%ad", "--date=short", "--", rel]
    ).strip()
    if not last_touch:
        raise ZeroHistoryError(f"module has zero git history: {rel}")
    return {
        "module": rel,
        "owner": top_author,
        "owner_commits": top_n,
        "total_commits": total,
        "share": top_n / total,
        "last_touch": last_touch,
        "authors": dict(counts),
    }


def build_rollup(entries: list[dict]) -> list[dict]:
    by_author: dict[str, dict] = {}
    for e in entries:
        row = by_author.setdefault(
            e["owner"], {"author": e["owner"], "modules_owned": 0, "file_commits": 0}
        )
        row["modules_owned"] += 1
        row["file_commits"] += e["owner_commits"]
    return sorted(by_author.values(), key=lambda r: -r["modules_owned"])


def render(entries: list[dict], rollup: list[dict], generated_at: str) -> str:
    n = len(entries)
    lines: list[str] = []
    lines.append("# Source Ownership Map")
    lines.append("")
    lines.append("> **GENERATED FILE — do not edit by hand.**")
    lines.append(f"> Regenerate with: `{REGEN_CMD}`")
    lines.append(f"> {TIMESTAMP_LINE_PREFIX}{generated_at}")
    lines.append("")
    lines.append(
        "Ownership is derived from real git history: for each module the owner is "
        "the top author by commit count touching that file (ties resolve to the "
        "most recently active author). Share is the owner's commit count divided "
        "by the total commit count on the file."
    )
    lines.append("")
    lines.append("## Per-author rollup")
    lines.append("")
    lines.append(f"Total modules: **{n}**")
    lines.append("")
    lines.append("| Author | Modules owned | File commits | Share of modules |")
    lines.append("| --- | ---: | ---: | ---: |")
    for r in rollup:
        share = r["modules_owned"] / n
        lines.append(
            f"| {r['author']} | {r['modules_owned']} | {r['file_commits']} | "
            f"{share:.1%} |"
        )
    lines.append("")
    lines.append("## Per-module ownership")
    lines.append("")
    lines.append(
        "| Module | Owner | Owner share | Commits (owner / total) | Last touch |"
    )
    lines.append("| --- | --- | ---: | ---: | --- |")
    for e in entries:
        lines.append(
            f"| `{e['module']}` | {e['owner']} | {e['share']:.1%} | "
            f"{e['owner_commits']} / {e['total_commits']} | {e['last_touch']} |"
        )
    lines.append("")
    lines.append("## Machine-readable module index")
    lines.append("")
    lines.append(
        "Tests parse this section. Do not hand-edit; regenerate with the script."
    )
    lines.append("")
    payload = {
        "modules": [
            {
                "module": e["module"],
                "owner": e["owner"],
                "owner_commits": e["owner_commits"],
                "total_commits": e["total_commits"],
                "share": round(e["share"], 4),
                "last_touch": e["last_touch"],
            }
            for e in entries
        ],
        "rollup": rollup,
        "total_modules": n,
    }
    lines.append(MACHINE_FENCE)
    lines.append(json.dumps(payload, indent=2, ensure_ascii=False))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def generate() -> tuple[str, str]:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = [ownership_for_file(m) for m in discover_modules()]
    rollup = build_rollup(entries)
    return render(entries, rollup, generated_at), generated_at


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate docs/OWNERSHIP.md")
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_DOC,
        help="where to write the doc (default: docs/OWNERSHIP.md)",
    )
    args = parser.parse_args(argv)
    doc, generated_at = generate()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(doc, encoding="utf-8")
    print(f"wrote {args.out} ({generated_at})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
