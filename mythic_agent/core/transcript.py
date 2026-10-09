"""Memory-bounded conversation transcript with disk spillover.

A long session's transcript can grow without limit, so ``BoundedTranscript``
keeps only the most recent ``max_tokens`` worth of turns in memory. When a
new turn would push the hot window over budget, the oldest turns are
appended to a JSONL spill file on disk, oldest-first. The full transcript
can always be reconstructed in order via :meth:`get_all`.

Token counting uses a cheap character heuristic (~4 chars/token). It is not
model-exact; it exists to bound memory, not to budget API spend.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

_CHARS_PER_TOKEN = 4


def _estimate_tokens(text: str) -> int:
    """Heuristic token count for memory-bounding purposes."""
    return max(1, len(text) // _CHARS_PER_TOKEN)


class BoundedTranscript:
    """Turn buffer that spills the oldest turns to disk when over budget.

    Parameters
    ----------
    max_tokens:
        Maximum estimated tokens held in memory. Must be positive.
    spill_dir:
        Where JSONL spill files go. Created (0o700) lazily on first spill.
        Defaults to a process-local temp dir so tests never touch user data.
    """

    def __init__(self, max_tokens: int,
                 spill_dir: str | os.PathLike[str] | None = None) -> None:
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        self.max_tokens = max_tokens
        self._spill_dir = Path(spill_dir) if spill_dir is not None else None
        self._turns: list[dict[str, Any]] = []
        self._in_memory_tokens = 0
        self._spill_count = 0
        self._spill_tokens = 0
        self._spill_path: Path | None = None

    # ------------------------------------------------------------------
    # mutation
    # ------------------------------------------------------------------
    def add(self, turn: dict[str, Any]) -> None:
        """Append a turn (``{"role": ..., "content": ...}``) and spill if over budget."""
        if not isinstance(turn, dict) or not isinstance(turn.get("content"), str):
            raise TypeError("turn must be a dict with a str 'content' field")
        tokens = _estimate_tokens(turn["content"])
        self._turns.append(dict(turn))
        self._in_memory_tokens += tokens
        self._spill_to_budget()

    # ------------------------------------------------------------------
    # access
    # ------------------------------------------------------------------
    def get(self) -> list[dict[str, Any]]:
        """The in-memory hot window (most recent turns), oldest-first."""
        return [dict(t) for t in self._turns]

    def get_all(self) -> list[dict[str, Any]]:
        """Full transcript: spilled turns (oldest-first) + hot window."""
        spilled = self._read_spilled()
        return spilled + self.get()

    def stats(self) -> dict[str, Any]:
        """Introspection: counts and token estimates, in memory and spilled."""
        return {
            "in_memory_turns": len(self._turns),
            "in_memory_tokens": self._in_memory_tokens,
            "spilled_turns": self._spill_count,
            "spilled_tokens": self._spill_tokens,
            "max_tokens": self.max_tokens,
            "spill_file": str(self._spill_path) if self._spill_path else None,
        }

    # ------------------------------------------------------------------
    # spilling
    # ------------------------------------------------------------------
    def _spill_path_for(self) -> Path:
        if self._spill_path is None:
            base = self._spill_dir or Path(
                os.environ.get("TMPDIR", "/tmp")) / "mythic_transcript_spills"
            base.mkdir(parents=True, exist_ok=True, mode=0o700)
            name = f"spill_{os.getpid()}_{int(time.time() * 1000)}.jsonl"
            self._spill_path = base / name
        return self._spill_path

    def _spill_to_budget(self) -> None:
        """Move oldest turns to disk until the hot window fits the budget."""
        # Always keep the newest turn, even if it alone exceeds the budget.
        while len(self._turns) > 1 and self._in_memory_tokens > self.max_tokens:
            turn = self._turns.pop(0)
            tokens = _estimate_tokens(turn["content"])
            self._in_memory_tokens -= tokens
            self._write_spill(turn, tokens)

    def _write_spill(self, turn: dict[str, Any], tokens: int) -> None:
        path = self._spill_path_for()
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(turn, ensure_ascii=False) + "\n")
        self._spill_count += 1
        self._spill_tokens += tokens

    def _read_spilled(self) -> list[dict[str, Any]]:
        if self._spill_path is None or not self._spill_path.exists():
            return []
        turns: list[dict[str, Any]] = []
        with self._spill_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    turns.append(json.loads(line))
        return turns
