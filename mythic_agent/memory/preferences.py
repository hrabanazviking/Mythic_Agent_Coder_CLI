"""Persistent user preference store.

Records simple preference patterns ("always use X tool", "I prefer Y", ...)
learned from conversation turns and surfaces them back to the agent as
"You usually prefer ..." suggestions that can be injected into prompts.

Storage layout: <workspace>/.mythic/preferences.json
"""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_PREF_DIR_NAME = ".mythic"
_PREF_FILE_NAME = "preferences.json"

# Pattern table for learn_from_turn().  Each entry maps a case-insensitive
# regex to a (preference_key, value_group_index) pair.  The regex should
# contain exactly one capture group that holds the preferred value.
_PATTERN_TABLE: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\balways\s+use\s+(.+?)(?:\.|$)", re.IGNORECASE), "tool"),
    (re.compile(r"\bnever\s+use\s+(.+?)(?:\.|$)", re.IGNORECASE), "avoid_tool"),
    (re.compile(r"\bprefer\s+(.+?)\s+over\s+(.+?)(?:\.|$)", re.IGNORECASE), "preference"),
    (re.compile(r"\bi\s+prefer\s+(.+?)(?:\.|$)", re.IGNORECASE), "preference"),
    (re.compile(r"\bi\s+like\s+(.+?)\s+(?:best|most)(?:\.|$)", re.IGNORECASE), "preference"),
    (re.compile(r"\bdon'?t\s+use\s+(.+?)(?:\.|$)", re.IGNORECASE), "avoid_tool"),
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PreferenceStore:
    """Learns and persists user preferences for one workspace.

    Args:
        workspace: Path to the workspace root. Preferences are stored at
            ``<workspace>/.mythic/preferences.json`` so different projects
            keep independent preference sets.
    """

    def __init__(self, workspace: str | os.PathLike[str]):
        self.workspace = Path(workspace)
        self.store_dir = self.workspace / _PREF_DIR_NAME
        self.store_file = self.store_dir / _PREF_FILE_NAME
        self._lock = threading.Lock()
        self._prefs: dict[str, dict[str, Any]] = {}
        self._load()

    # ------------------------------------------------------------------ IO

    def _load(self) -> None:
        """Load preferences from disk; self-heal on corruption."""
        with self._lock:
            self._prefs = {}
            if not self.store_file.exists():
                return
            try:
                with open(self.store_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self._prefs = data
            except json.JSONDecodeError as e:
                logger.error(
                    "Preference store corrupted at %s. Self-healing... Error: %s",
                    self.store_file,
                    e,
                )
                try:
                    os.replace(self.store_file, self.store_file.with_suffix(".json.corrupted"))
                except OSError:
                    pass
            except Exception as e:  # pragma: no cover - defensive
                logger.error("Failed to load preferences from %s: %s", self.store_file, e)

    def _atomic_save(self) -> None:
        """Lock-assumed atomic write via temp file + replace."""
        temp_path: Optional[str] = None
        try:
            self.store_dir.mkdir(parents=True, exist_ok=True)
            fd, temp_path = tempfile.mkstemp(
                dir=self.store_dir, prefix="preferences_", suffix=".tmp"
            )
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._prefs, f, indent=2, sort_keys=True)
            os.replace(temp_path, self.store_file)
        except Exception as e:  # pragma: no cover - defensive
            logger.error("Failed to save preferences to %s: %s", self.store_file, e)
            if temp_path is not None:
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def _save(self) -> None:
        with self._lock:
            self._atomic_save()

    # -------------------------------------------------------------- public

    def record(self, preference: str, value: str) -> None:
        """Record a preference; repeated recordings strengthen the entry.

        Args:
            preference: The preference key, e.g. ``"test_runner"``.
            value: The preferred value, e.g. ``"pytest"``.
        """
        entry = self._prefs.get(preference)
        if entry is None:
            entry = {"value": value, "count": 0}
            self._prefs[preference] = entry
        entry["value"] = value
        entry["count"] = int(entry.get("count", 0)) + 1
        entry["last_used"] = _utc_now_iso()
        self._save()

    def get(self, preference: str, default: Optional[str] = None) -> Optional[str]:
        """Return the recorded value for *preference*, or *default*."""
        entry = self._prefs.get(preference)
        if entry is None:
            return default
        return entry.get("value", default)

    def forget(self, preference: str) -> bool:
        """Remove a recorded preference. Returns True if one existed."""
        with self._lock:
            existed = self._prefs.pop(preference, None) is not None
        if existed:
            self._save()
        return existed

    def all(self) -> dict[str, str]:
        """Return every recorded preference as ``{key: value}``."""
        return {k: v.get("value") for k, v in self._prefs.items() if "value" in v}

    def suggest(self, top_n: int = 5) -> str:
        """Render the strongest preferences as "you usually prefer X" hints.

        Entries are ordered by reinforcement count (descending). Returns an
        empty string when nothing has been recorded yet.
        """
        ranked = sorted(
            self._prefs.items(),
            key=lambda kv: int(kv[1].get("count", 0)),
            reverse=True,
        )[: max(0, top_n)]
        lines: list[str] = []
        for key, entry in ranked:
            value = entry.get("value")
            if value is None:
                continue
            readable_key = key.replace("_", " ")
            lines.append(f"You usually prefer '{value}' for {readable_key}.")
        return "\n".join(lines)

    def learn_from_turn(
        self, user_msg: str, agent_action: Optional[str] = None
    ) -> list[tuple[str, str]]:
        """Extract simple preference patterns from one conversation turn.

        Scans the user message for expressions like "always use X", "never
        use X", "I prefer X over Y", "I like X best", "don't use X", records
        each match, and returns the extracted ``(preference, value)`` pairs.

        Args:
            user_msg: The user's raw message text.
            agent_action: Reserved for future agent-side patterns; currently
                unused.
        """
        extracted: list[tuple[str, str]] = []
        for pattern, pref_key in _PATTERN_TABLE:
            for match in pattern.finditer(user_msg or ""):
                value = match.group(1).strip().strip("'\"")
                # Trim trailing sentence fragments the regex may have caught.
                value = re.split(r"\s+(?:for|to|when|because)\s+", value, maxsplit=1)[0].strip()
                if value and len(value) <= 200:
                    self.record(pref_key, value)
                    extracted.append((pref_key, value))
        return extracted
