"""Disk-backed cache for LLM responses keyed by prompt hash.

Identical prompts (same model parameters, same rendered prompt) produce
identical responses, so caching them on disk saves latency, tokens, and
provider quota. Entries expire after a TTL (default 1 hour) and the cache
can be inspected or cleared via ``mythic cache --stats`` / ``--clear``.

Security: entries live under a 0o700 directory and are written atomically
(temp file + rename) so a crash can never leave a half-written entry.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "DEFAULT_TTL_SECONDS",
    "Optional",
    "Path",
    "ResponseCache",
    "default_cache_dir",
    "log",
]

import hashlib
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 3600  # 1 hour
_STATS_FILENAME = "stats.json"


def default_cache_dir() -> Path:
    """Cache directory under the Mythic state dir (honors MYTHIC_HOME env)."""
    root = os.environ.get("MYTHIC_HOME", str(Path.home() / ".mythic"))
    return Path(root).expanduser().resolve() / "cache"


class ResponseCache:
    """Disk-based LLM response cache with SHA256 keys and TTL expiry.

    Parameters
    ----------
    cache_dir:
        Directory holding one ``<sha256>.json`` file per cached response.
        Created (0o700) if missing.
    ttl_seconds:
        How long an entry stays valid. Expired entries are treated as
        misses and removed on read.
    """

    def __init__(self, cache_dir: str | os.PathLike[str] | None = None,
                 ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self.cache_dir = Path(cache_dir) if cache_dir is not None else default_cache_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(self.cache_dir, 0o700)
        except OSError:  # pragma: no cover - best effort on odd filesystems
            pass
        self.ttl_seconds = ttl_seconds
        self._stats_path = self.cache_dir / _STATS_FILENAME
        self._hits = 0
        self._misses = 0
        self._load_stats()

    # ------------------------------------------------------------------
    # hashing
    # ------------------------------------------------------------------
    @staticmethod
    def hash_prompt(prompt: str) -> str:
        """SHA256 hex digest of a prompt string (stable cache key)."""
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # core operations
    # ------------------------------------------------------------------
    def _entry_path(self, prompt_hash: str) -> Path:
        return self.cache_dir / f"{prompt_hash}.json"

    def get(self, prompt_hash: str) -> Optional[str]:
        """Return the cached response, or None on miss/expiry/corruption."""
        path = self._entry_path(prompt_hash)
        try:
            raw = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            self._record_miss()
            return None
        except OSError:
            log.warning("cache: unreadable entry %s", path.name)
            self._record_miss()
            return None
        try:
            entry = json.loads(raw)
            response = entry["response"]
            created_at = float(entry["created_at"])
        except (ValueError, KeyError, TypeError):
            log.warning("cache: corrupt entry %s; evicting", path.name)
            self._evict(path)
            self._record_miss()
            return None
        if time.time() - created_at > self.ttl_seconds:
            self._evict(path)
            self._record_miss()
            return None
        self._record_hit()
        return response

    def put(self, prompt_hash: str, response: str) -> None:
        """Store a response under its prompt hash (atomic write)."""
        payload = json.dumps(
            {"response": response, "created_at": time.time()},
            ensure_ascii=False,
        )
        fd, tmp = tempfile.mkstemp(dir=self.cache_dir, prefix=".entry-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self._entry_path(prompt_hash))
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def clear(self) -> int:
        """Remove all cached entries (keeps the stats file). Returns count."""
        removed = 0
        for path in self.cache_dir.glob("*.json"):
            if path.name == _STATS_FILENAME:
                continue
            try:
                path.unlink()
                removed += 1
            except OSError:
                log.warning("cache: could not remove %s", path.name)
        return removed

    # ------------------------------------------------------------------
    # introspection
    # ------------------------------------------------------------------
    def stats(self) -> dict[str, Any]:
        """Snapshot: entries, hits, misses, disk size, TTL, directory."""
        entries = 0
        size_bytes = 0
        for path in self.cache_dir.glob("*.json"):
            if path.name == _STATS_FILENAME:
                continue
            entries += 1
            try:
                size_bytes += path.stat().st_size
            except OSError:
                pass
        return {
            "cache_dir": str(self.cache_dir),
            "entries": entries,
            "hits": self._hits,
            "misses": self._misses,
            "size_bytes": size_bytes,
            "ttl_seconds": self.ttl_seconds,
        }

    # ------------------------------------------------------------------
    # internal stats persistence
    # ------------------------------------------------------------------
    def _load_stats(self) -> None:
        try:
            data = json.loads(self._stats_path.read_text(encoding="utf-8"))
            self._hits = int(data.get("hits", 0))
            self._misses = int(data.get("misses", 0))
        except (OSError, ValueError, TypeError, AttributeError):
            self._hits = 0
            self._misses = 0

    def _save_stats(self) -> None:
        try:
            self._stats_path.write_text(
                json.dumps({"hits": self._hits, "misses": self._misses}),
                encoding="utf-8",
            )
        except OSError:  # pragma: no cover - stats are best effort
            log.warning("cache: could not persist stats")

    def _record_hit(self) -> None:
        self._hits += 1
        self._save_stats()

    def _record_miss(self) -> None:
        self._misses += 1
        self._save_stats()

    def _evict(self, path: Path) -> None:
        try:
            path.unlink()
        except OSError:
            log.warning("cache: could not evict %s", path.name)
