"""Intelligence cache — parse/graph/LSP results per file hash (M-069).

Part III — Code Intelligence. The roadmap's words for this
slice: "parse/graph/LSP results cached per file hash; a cold
start on a big repo stays fast (measured in Part XI)."

Part III's senses are expensive: the M-043 foundation parses
a file, M-046 extracts its symbol graph, and M-049/M-050 ask
a language server about it. None of that work needs repeating
while the file itself has not changed — and none of it may
ever be *reused* once the file has changed. This module is
the cache that holds those results, in
``mythic_agent/tools/intelligence_cache.py``:

* **Where it lives.** Entries live under the workspace's own
  ``.mythic/intelligence-cache/`` directory (the M-056
  test-history precedent for workspace-local ``.mythic``
  state), one JSON file per entry, written atomically (temp
  file + rename, the ``core/cache.py`` discipline), with the
  hit/miss/stale counters persisted beside them.
* **The key.** Every entry is keyed by kind + workspace-
  relative path + the file's SHA-256 content hash + the
  producer's name. Kinds are exactly ``parse``, ``graph``,
  and ``lsp``; anything else is refused.
* **Invalidation honesty — the heart of the slice.** A
  lookup recomputes the file's CURRENT hash. A changed file
  is a *stale eviction* plus a miss — a stale result is
  never served, not even once. A missing file, a corrupt
  entry, and a producer mismatch are likewise misses, and
  the persisted stats keep the three apart (stale evictions
  are counted separately from plain misses).
* **The live producers.** ``parse`` payloads come from the
  M-043 foundation's :func:`parse_source` (language,
  backend, error truth, definitions) and ``graph`` payloads
  from M-046's :func:`extract_file_graph` record, both
  behind :meth:`IntelligenceCache.get_or_compute`, so a hit
  never re-runs the producer. Producer reads honour the
  symbol graph's own per-file byte cap (262144 bytes) and
  name it when they refuse a larger file.
* **What is honestly NOT computed here.** ``lsp`` payloads
  are stored and looked up only: their producer is the live
  language-server road (M-049/M-050), a server round-trip
  this module never fakes. An ``lsp`` entry exists only when
  that road (or a test standing in its exact shape) put one
  there.
* **The surfaces.** ``Agent.intelligence_cache(...)`` and
  ``/intelcache [show | <file> | warm | clear]`` on the
  terminal and TUI system-command roads, sharing this
  module's parser and formatter. The setting
  ``intelligence_cache`` (on by default) closes the road
  plainly — a switched-off road reads and writes nothing.
  Warming *writes cache entries* — that is the cache's whole
  job — and never writes a source file; ``clear`` removes
  entries and reports the count it removed.
"""

from __future__ import annotations

__all__ = [
    "PLAIN_EXPLANATION",
    "INTELLIGENCE_CACHE_SLICE",
    "USAGE",
    "CACHE_KINDS",
    "PRODUCERS",
    "MAX_PRODUCER_FILE_BYTES",
    "MAX_WARM_FILES",
    "EntryInfo",
    "FileCacheState",
    "IntelligenceCache",
    "IntelligenceCacheReport",
    "WarmResult",
    "cache_dir_for",
    "enabled_from_config",
    "entry_key",
    "format_intelligence_cache_report",
    "intelligence_cache_report",
    "parse_intelcache_args",
    "render_markdown",
    "sha256_hex",
]

import hashlib
import json
import os
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

INTELLIGENCE_CACHE_SLICE = "M-069"

PLAIN_EXPLANATION = (
    "The intelligence cache keeps the coder's expensive "
    "per-file results — parses, symbol graphs, and language-"
    "server results — keyed by each file's content hash, so "
    "re-opening a big repo does not pay for the same work "
    "twice. /intelcache show reports what is cached, "
    "/intelcache <file> reports one file's cached state, "
    "/intelcache warm fills the parse and graph caches for "
    "the workspace, and /intelcache clear empties it. A "
    "changed file is never served a stale result: its old "
    "entry is evicted and the result is recomputed."
)

USAGE = "Usage: /intelcache [show | <file> | warm | clear]"

CACHE_KINDS: Tuple[str, ...] = ("parse", "graph", "lsp")

PRODUCERS: Dict[str, str] = {
    "parse": "m043-parse/1",
    "graph": "m046-graph/1",
    "lsp": "m049-lsp/1",
}

# The symbol graph's own per-file cap (context/symbol_graph
# MAX_GRAPH_FILE_BYTES): producer reads refuse larger files
# and name the cap, exactly as the graph build does.
MAX_PRODUCER_FILE_BYTES = 262_144

MAX_WARM_FILES = 500

_STATS_FILENAME = "stats.json"

_SKIP_DIRS = {"__pycache__"}


def enabled_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """The intelligence cache is on unless config says so."""
    if not config:
        return True
    return config.get("intelligence_cache", True) is not False


def cache_dir_for(workspace: Any) -> Path:
    """The workspace's intelligence-cache directory."""
    return Path(workspace).resolve() / ".mythic" / "intelligence-cache"


def sha256_hex(data: bytes) -> str:
    """SHA-256 hex digest of *data* (the cache's hash)."""
    return hashlib.sha256(data).hexdigest()


def entry_key(kind: str, rel_path: str, file_hash: str,
              producer: str) -> str:
    """The entry key for one (kind, path, hash, producer)."""
    raw = "\0".join((kind, rel_path, file_hash, producer))
    return sha256_hex(raw.encode("utf-8"))


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EntryInfo:
    """One cached entry's account (never its payload)."""

    kind: str = ""
    path: str = ""
    file_hash: str = ""
    producer: str = ""
    size_bytes: int = 0
    created_at: float = 0.0

    def record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "path": self.path,
                "file_hash": self.file_hash,
                "producer": self.producer,
                "size_bytes": self.size_bytes,
                "created_at": self.created_at}


@dataclass
class FileCacheState:
    """One file's per-kind cache state against its current hash."""

    path: str = ""
    file_hash: Optional[str] = None
    states: Dict[str, str] = field(default_factory=dict)

    def state_for(self, kind: str) -> str:
        """One kind's state: hit-ready | stale | absent."""
        return self.states.get(kind, "absent")

    def hit_ready_kinds(self) -> Tuple[str, ...]:
        """The kinds a lookup would serve from cache right now."""
        return tuple(k for k in CACHE_KINDS
                     if self.state_for(k) == "hit-ready")

    def record(self) -> Dict[str, Any]:
        return {"path": self.path, "file_hash": self.file_hash,
                "states": dict(self.states)}


@dataclass
class WarmResult:
    """One warm run's account."""

    files_seen: int = 0
    parse_filled: int = 0
    graph_filled: int = 0
    hits: int = 0
    skipped: List[Tuple[str, str]] = field(default_factory=list)
    capped: bool = False

    def filled(self) -> int:
        """Entries computed (not served) during this warm run."""
        return self.parse_filled + self.graph_filled

    def record(self) -> Dict[str, Any]:
        return {"files_seen": self.files_seen,
                "parse_filled": self.parse_filled,
                "graph_filled": self.graph_filled,
                "hits": self.hits,
                "skipped": [[p, r] for p, r in self.skipped],
                "capped": self.capped}


# ---------------------------------------------------------------------------
# The cache
# ---------------------------------------------------------------------------

class IntelligenceCache:
    """Disk-backed per-file intelligence cache for one workspace.

    Entries are keyed by kind + relative path + the file's
    SHA-256 content hash + producer name. A lookup recomputes
    the file's current hash: a changed file evicts its stale
    entry and misses — stale is never served.
    """

    def __init__(self, workspace: Any, *, create: bool = True) -> None:
        self.root = Path(workspace).resolve()
        self.cache_dir = cache_dir_for(self.root)
        if create:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._stats_path = self.cache_dir / _STATS_FILENAME
        self._hits = 0
        self._misses = 0
        self._stale = 0
        self._load_stats()

    # -- paths ---------------------------------------------------------

    def _resolve(self, rel_path: str) -> Tuple[Path, str]:
        """Resolve *rel_path* inside the workspace, or refuse."""
        raw = Path(rel_path)
        if raw.is_absolute():
            candidate = raw.resolve()
        else:
            candidate = (self.root / raw).resolve()
        try:
            rel = str(candidate.relative_to(self.root))
        except ValueError:
            raise ValueError(
                f"{rel_path!r} is outside the workspace "
                f"{self.root} — the intelligence cache only "
                "holds this workspace's files") from None
        return candidate, rel

    def _entry_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    # -- stats -----------------------------------------------------------

    def _load_stats(self) -> None:
        try:
            data = json.loads(
                self._stats_path.read_text(encoding="utf-8"))
            self._hits = int(data.get("hits", 0))
            self._misses = int(data.get("misses", 0))
            self._stale = int(data.get("stale_evictions", 0))
        except (OSError, ValueError, TypeError, AttributeError):
            self._hits = 0
            self._misses = 0
            self._stale = 0

    def _save_stats(self) -> None:
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._stats_path.write_text(json.dumps({
                "hits": self._hits, "misses": self._misses,
                "stale_evictions": self._stale}), encoding="utf-8")
        except OSError:
            pass  # stats are best effort, as in core/cache.py

    # -- entry scan ------------------------------------------------------

    def _scan_entries(self) -> List[Tuple[str, Dict[str, Any], int]]:
        """(key, stored-fields, size) for every readable entry."""
        out: List[Tuple[str, Dict[str, Any], int]] = []
        if not self.cache_dir.is_dir():
            return out
        for path in sorted(self.cache_dir.glob("*.json")):
            if path.name == _STATS_FILENAME:
                continue
            try:
                stored = json.loads(path.read_text(encoding="utf-8"))
                size = path.stat().st_size
            except (OSError, ValueError):
                continue
            if isinstance(stored, dict):
                out.append((path.stem, stored, size))
        return out

    def entries(self) -> List[EntryInfo]:
        """Every cached entry's account, sorted by path + kind."""
        infos = [EntryInfo(
            kind=str(stored.get("kind", "")),
            path=str(stored.get("path", "")),
            file_hash=str(stored.get("file_hash", "")),
            producer=str(stored.get("producer", "")),
            size_bytes=size,
            created_at=float(stored.get("created_at", 0.0) or 0.0))
            for _key, stored, size in self._scan_entries()]
        infos.sort(key=lambda e: (e.path, e.kind))
        return infos

    def kind_counts(self) -> Dict[str, int]:
        """Entry counts per kind (every kind named, even at 0)."""
        counts = {kind: 0 for kind in CACHE_KINDS}
        for info in self.entries():
            if info.kind in counts:
                counts[info.kind] += 1
        return counts

    def stats(self) -> Dict[str, Any]:
        """Snapshot: entries, per-kind counts, size, counters."""
        infos = self.entries()
        return {
            "cache_dir": str(self.cache_dir),
            "entries": len(infos),
            "per_kind": self.kind_counts(),
            "size_bytes": sum(i.size_bytes for i in infos),
            "hits": self._hits,
            "misses": self._misses,
            "stale_evictions": self._stale,
        }

    # -- core operations -------------------------------------------------

    def _check_kind(self, kind: str) -> str:
        kind = (kind or "").strip().lower()
        if kind not in CACHE_KINDS:
            raise ValueError(
                f"unknown cache kind {kind!r} — the kinds are "
                f"{', '.join(CACHE_KINDS)}")
        return kind

    def _producer_for(self, kind: str,
                      producer: Optional[str]) -> str:
        return producer or PRODUCERS[kind]

    def put(self, rel_path: str, kind: str, payload: Dict[str, Any],
            *, producer: Optional[str] = None) -> EntryInfo:
        """Store *payload* for the file's CURRENT content hash."""
        kind = self._check_kind(kind)
        if not isinstance(payload, dict):
            raise ValueError(
                f"cache payloads are mappings, got "
                f"{type(payload).__name__}")
        candidate, rel = self._resolve(rel_path)
        try:
            data = candidate.read_bytes()
        except OSError as exc:
            raise ValueError(
                f"cannot cache {rel!r}: the file cannot be "
                f"read ({exc})") from None
        file_hash = sha256_hex(data)
        producer = self._producer_for(kind, producer)
        key = entry_key(kind, rel, file_hash, producer)
        stored = {"kind": kind, "path": rel,
                  "file_hash": file_hash, "producer": producer,
                  "created_at": time.time(), "payload": payload}
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.cache_dir,
                                   prefix=".entry-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(stored, ensure_ascii=False))
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self._entry_path(key))
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
        return EntryInfo(kind=kind, path=rel, file_hash=file_hash,
                         producer=producer,
                         size_bytes=self._entry_path(key).stat().st_size,
                         created_at=stored["created_at"])

    def get(self, rel_path: str, kind: str,
            *, producer: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """The cached payload, or None — never a stale payload.

        The file's current hash is recomputed on every call.
        A changed file evicts its stale entry (counted as a
        stale eviction) and misses; a missing file, a corrupt
        entry, and a producer mismatch also miss.
        """
        kind = self._check_kind(kind)
        candidate, rel = self._resolve(rel_path)
        producer = self._producer_for(kind, producer)
        try:
            data = candidate.read_bytes()
        except OSError:
            self._evict_path_kind(rel, kind)
            self._misses += 1
            self._save_stats()
            return None
        file_hash = sha256_hex(data)
        key = entry_key(kind, rel, file_hash, producer)
        path = self._entry_path(key)
        if path.is_file():
            try:
                stored = json.loads(path.read_text(encoding="utf-8"))
                payload = stored["payload"]
                if (stored.get("kind") != kind
                        or stored.get("path") != rel
                        or stored.get("file_hash") != file_hash
                        or stored.get("producer") != producer
                        or not isinstance(payload, dict)):
                    raise ValueError("entry fields do not match its key")
            except (ValueError, KeyError, TypeError):
                self._evict(path)
                self._misses += 1
                self._save_stats()
                return None
            self._hits += 1
            self._save_stats()
            return payload
        # No entry under the current hash: a same-path/kind entry
        # under an OLD hash is stale — evict it, count it apart.
        stale_found = False
        for old_key, stored, _size in self._scan_entries():
            if (stored.get("path") == rel
                    and stored.get("kind") == kind
                    and stored.get("producer") == producer
                    and stored.get("file_hash") != file_hash):
                self._evict(self._entry_path(old_key))
                stale_found = True
        if stale_found:
            self._stale += 1
        self._misses += 1
        self._save_stats()
        return None

    def _evict(self, path: Path) -> None:
        try:
            path.unlink()
        except OSError:
            pass

    def _evict_path_kind(self, rel: str, kind: str) -> None:
        for key, stored, _size in self._scan_entries():
            if stored.get("path") == rel and stored.get("kind") == kind:
                self._evict(self._entry_path(key))

    def check(self, rel_path: str) -> FileCacheState:
        """One file's per-kind state against its CURRENT hash."""
        candidate, rel = self._resolve(rel_path)
        try:
            file_hash: Optional[str] = sha256_hex(candidate.read_bytes())
        except OSError:
            file_hash = None
        states: Dict[str, str] = {}
        by_kind: Dict[str, List[Dict[str, Any]]] = {}
        for _key, stored, _size in self._scan_entries():
            if stored.get("path") == rel:
                by_kind.setdefault(str(stored.get("kind", "")), []).append(
                    stored)
        for kind in CACHE_KINDS:
            found = by_kind.get(kind, [])
            if file_hash is not None and any(
                    s.get("file_hash") == file_hash for s in found):
                states[kind] = "hit-ready"
            elif found:
                states[kind] = "stale"
            else:
                states[kind] = "absent"
        return FileCacheState(path=rel, file_hash=file_hash,
                              states=states)

    def get_or_compute(self, rel_path: str, kind: str,
                       compute: Callable[[], Dict[str, Any]],
                       *, producer: Optional[str] = None,
                       ) -> Tuple[Dict[str, Any], bool]:
        """(payload, hit) — compute + store on a miss only."""
        kind = self._check_kind(kind)
        cached = self.get(rel_path, kind, producer=producer)
        if cached is not None:
            return cached, True
        payload = compute()
        self.put(rel_path, kind, payload, producer=producer)
        return payload, False

    # -- live producers ----------------------------------------------------

    def _producer_source(self, rel_path: str) -> Tuple[str, str, str]:
        """(rel, language, source) for a producer read, or raise."""
        candidate, rel = self._resolve(rel_path)
        try:
            data = candidate.read_bytes()
        except OSError as exc:
            raise ValueError(
                f"cannot read {rel!r} for the intelligence "
                f"cache ({exc})") from None
        if len(data) > MAX_PRODUCER_FILE_BYTES:
            raise ValueError(
                f"{rel!r} is {len(data)} bytes, over the "
                f"producer cap of {MAX_PRODUCER_FILE_BYTES} "
                "bytes (the symbol graph's own per-file cap) "
                "— it is not cached by the parse/graph producers")
        try:
            source = data.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError(
                f"{rel!r} is not utf-8 text — the parse/graph "
                "producers do not cache it") from None
        from ..core.tree_sitter_foundation import detect_language
        language = detect_language(candidate.name)
        if language is None:
            raise ValueError(
                f"{rel!r} has no catalogued language (its "
                "extension is not in the M-043 catalogue) — "
                "there is no parse or graph to cache for it")
        return rel, language, source

    def cached_parse(self, rel_path: str,
                     ) -> Tuple[Dict[str, Any], bool]:
        """(parse payload, hit) via the M-043 foundation."""
        rel, language, source = self._producer_source(rel_path)

        def _compute() -> Dict[str, Any]:
            from ..core.tree_sitter_foundation import parse_source
            parsed = parse_source(language, source)
            return {
                "language": parsed.language,
                "backend": parsed.backend,
                "has_error": parsed.has_error,
                "definitions": [
                    {"name": d.name, "kind": d.kind,
                     "language": d.language,
                     "node_type": d.node_type,
                     "start_point": list(d.start_point),
                     "end_point": list(d.end_point)}
                    for d in parsed.definitions],
            }

        return self.get_or_compute(rel, "parse", _compute)

    def cached_graph(self, rel_path: str,
                     ) -> Tuple[Dict[str, Any], bool]:
        """(per-file graph payload, hit) via M-046's extraction."""
        rel, language, source = self._producer_source(rel_path)

        def _compute() -> Dict[str, Any]:
            from ..context.symbol_graph import extract_file_graph
            return dict(extract_file_graph(rel, language, source).record())

        return self.get_or_compute(rel, "graph", _compute)

    # -- warm + clear ------------------------------------------------------

    def warm(self, *, max_files: int = MAX_WARM_FILES) -> WarmResult:
        """Fill parse+graph for every catalogued source file.

        Files are walked in sorted order, dot-directories and
        the cache's own home skipped. A file whose producer
        refuses it (grammar-less, oversized, not utf-8) is a
        named skip, never a silent one. LSP results are not
        warmed — no server is run on this road.
        """
        if max_files <= 0:
            raise ValueError("max_files must be positive")
        from ..core.tree_sitter_foundation import detect_language
        result = WarmResult()
        candidates: List[Path] = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = sorted(
                d for d in dirnames
                if not d.startswith(".") and d not in _SKIP_DIRS)
            for name in sorted(filenames):
                if detect_language(name) is not None:
                    candidates.append(Path(dirpath) / name)
        for candidate in candidates:
            if result.files_seen >= max_files:
                result.capped = True
                break
            rel = str(candidate.relative_to(self.root))
            result.files_seen += 1
            for kind, road in (("parse", self.cached_parse),
                               ("graph", self.cached_graph)):
                try:
                    _payload, hit = road(rel)
                except Exception as exc:
                    result.skipped.append((rel, f"{kind}: {exc}"))
                    continue
                if hit:
                    result.hits += 1
                elif kind == "parse":
                    result.parse_filled += 1
                else:
                    result.graph_filled += 1
        return result

    def clear(self) -> int:
        """Remove every entry (stats counters are kept)."""
        removed = 0
        if not self.cache_dir.is_dir():
            return 0
        for path in self.cache_dir.glob("*.json"):
            if path.name == _STATS_FILENAME:
                continue
            try:
                path.unlink()
                removed += 1
            except OSError:
                pass
        return removed


# ---------------------------------------------------------------------------
# The report surface
# ---------------------------------------------------------------------------

@dataclass
class IntelligenceCacheReport:
    """One intelligence-cache call's whole account."""

    kind: str = "show"  # show | file | warm | clear
    status: str = "ok"  # ok | disabled | error
    stats: Dict[str, Any] = field(default_factory=dict)
    entries: List[EntryInfo] = field(default_factory=list)
    file_state: Optional[FileCacheState] = None
    warm_result: Optional[WarmResult] = None
    cleared: int = 0
    note: str = ""

    def totals(self) -> Tuple[int, int]:
        """(entries, size in bytes) from the report's own stats."""
        return (int(self.stats.get("entries", 0)),
                int(self.stats.get("size_bytes", 0)))

    def per_kind(self) -> Dict[str, int]:
        """Per-kind entry counts from the report's own stats."""
        counts = self.stats.get("per_kind", {})
        return {kind: int(counts.get(kind, 0)) for kind in CACHE_KINDS}

    def record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "status": self.status,
                "stats": dict(self.stats),
                "entries": [e.record() for e in self.entries],
                "file_state": (self.file_state.record()
                               if self.file_state else None),
                "warm": (self.warm_result.record()
                         if self.warm_result else None),
                "cleared": self.cleared, "note": self.note}


def _closed(kind: str) -> IntelligenceCacheReport:
    return IntelligenceCacheReport(
        kind=kind, status="disabled",
        note=("the intelligence cache is off (the "
              "intelligence_cache setting), so nothing was "
              "read or written on this road"))


def intelligence_cache_report(
        workspace: Any, mode: str = "show", *,
        target: Optional[str] = None,
        enabled: bool = True,
) -> IntelligenceCacheReport:
    """One intelligence-cache account.

    Modes: ``show`` (entries + persisted counters), ``file``
    (one file's per-kind state against its current hash),
    ``warm`` (fill parse+graph for the workspace), ``clear``
    (remove every entry). Raises :class:`ValueError` for an
    unknown mode or a file target outside the workspace.
    """
    kind = (mode or "show").strip().lower()
    if kind not in ("show", "file", "warm", "clear"):
        raise ValueError(f"{USAGE} — unknown mode {mode!r}")
    if not enabled:
        return _closed(kind)
    root = Path(workspace).resolve() if workspace else Path.cwd()
    if kind == "file":
        if not target:
            raise ValueError(f"{USAGE} — this road needs its file")
        cache = IntelligenceCache(root, create=False)
        state = cache.check(target)
        return IntelligenceCacheReport(
            kind=kind, stats=cache.stats(), file_state=state,
            note=("per-kind state against the file's current "
                  "hash — a stale kind is recomputed on its "
                  "next lookup, never served"))
    if kind == "warm":
        cache = IntelligenceCache(root)
        warm = cache.warm()
        return IntelligenceCacheReport(
            kind=kind, stats=cache.stats(),
            entries=cache.entries(), warm_result=warm,
            note=("parse and graph results filled per file "
                  "hash; language-server results are not "
                  "warmed — no server is run on this road"))
    if kind == "clear":
        cache = IntelligenceCache(root, create=False)
        removed = cache.clear()
        return IntelligenceCacheReport(
            kind=kind, stats=cache.stats(), cleared=removed,
            note=f"removed {removed} cached entr"
                 f"{'y' if removed == 1 else 'ies'}; the "
                 "hit/miss/stale counters are kept")
    cache = IntelligenceCache(root, create=False)
    return IntelligenceCacheReport(
        kind=kind, stats=cache.stats(), entries=cache.entries(),
        note=("cached per file hash under the workspace's "
              ".mythic/intelligence-cache/ — a changed file's "
              "entry is evicted on its next lookup, never served"))


# ---------------------------------------------------------------------------
# Surfaces: the shared parser + formatters
# ---------------------------------------------------------------------------

def parse_intelcache_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/intelcache`` arguments into a cache request.

    Grammar::

        /intelcache
        /intelcache show
        /intelcache warm
        /intelcache clear
        /intelcache <file>

    Raises :class:`ValueError` on a usage error.
    """
    text = (arguments or "").strip()
    if not text:
        return {"action": "show"}
    tokens = text.split()
    if len(tokens) != 1:
        raise ValueError(f"{USAGE} — name one file, or none")
    head = tokens[0].lower()
    if head in ("show", "warm", "clear"):
        return {"action": head}
    return {"action": "file", "target": tokens[0]}


def format_intelligence_cache_report(status: Dict[str, Any]) -> str:
    """One intelligence-cache call's account, from an Agent status."""
    report = status["report"]
    stats = report["stats"]
    lines = [f"Intelligence cache ({INTELLIGENCE_CACHE_SLICE}): "
             f"{report['kind']} — parse/graph/LSP results "
             "cached per file hash, stale never served."]
    if stats:
        per_kind = stats.get("per_kind", {})
        lines.append(
            f"  {stats.get('entries', 0)} entr"
            f"{'y' if stats.get('entries', 0) == 1 else 'ies'} "
            f"({', '.join(f'{k}: {per_kind.get(k, 0)}' for k in CACHE_KINDS)}), "
            f"{stats.get('size_bytes', 0)} bytes, "
            f"hits {stats.get('hits', 0)}, "
            f"misses {stats.get('misses', 0)}, "
            f"stale evictions {stats.get('stale_evictions', 0)}")
    for entry in report["entries"][:20]:
        lines.append(
            f"  {entry['kind']} {entry['path']} "
            f"(hash {entry['file_hash'][:12]}…, "
            f"{entry['producer']}, {entry['size_bytes']} bytes)")
    if len(report["entries"]) > 20:
        lines.append(f"  … and {len(report['entries']) - 20} more")
    state = report.get("file_state")
    if state:
        lines.append(
            f"  {state['path']}: "
            + ", ".join(f"{k} {state['states'].get(k, 'absent')}"
                        for k in CACHE_KINDS)
            + (f" (current hash {state['file_hash'][:12]}…)"
               if state["file_hash"] else " (file missing)"))
    warm = report.get("warm")
    if warm:
        lines.append(
            f"  warmed {warm['files_seen']} file(s): "
            f"{warm['parse_filled']} parse + "
            f"{warm['graph_filled']} graph filled, "
            f"{warm['hits']} already cached, "
            f"{len(warm['skipped'])} skip(s)")
        for path, reason in warm["skipped"][:10]:
            lines.append(f"    skipped {path}: {reason}")
    if report["kind"] == "clear":
        lines.append(f"  cleared {report['cleared']} entr"
                     f"{'y' if report['cleared'] == 1 else 'ies'}")
    if report["note"]:
        lines.append(f"  {report['note']}")
    lines.append(status["plain_explanation"])
    return "\n".join(lines)


def render_markdown(report: IntelligenceCacheReport) -> str:
    """Render *report* as a human report, from its own record.

    Built from :meth:`IntelligenceCacheReport.totals`,
    :meth:`IntelligenceCacheReport.per_kind`, each entry's
    :meth:`EntryInfo.record`, the file state's
    :meth:`FileCacheState.hit_ready_kinds`, and the warm
    run's :meth:`WarmResult.filled`, so the rendered page is
    computed from the same values the tests pin.
    """
    n_entries, n_bytes = report.totals()
    per_kind = report.per_kind()
    lines = [
        "# Intelligence Cache — results cached per file hash",
        "",
        f"*Slice {INTELLIGENCE_CACHE_SLICE} of the All-Features "
        "road (Part III — Code Intelligence). A changed file's "
        "entry is evicted on lookup, never served.*",
        "",
        f"**{n_entries} entr{'y' if n_entries == 1 else 'ies'}**, "
        f"**{n_bytes} bytes** — "
        + ", ".join(f"{kind}: {per_kind[kind]}" for kind in CACHE_KINDS)
        + ".",
        "",
    ]
    for entry in report.entries:
        rec = entry.record()
        lines.append(
            f"- `{rec['kind']}` `{rec['path']}` — hash "
            f"`{rec['file_hash'][:12]}…`, producer "
            f"`{rec['producer']}`, {rec['size_bytes']} bytes")
    if report.file_state is not None:
        ready = report.file_state.hit_ready_kinds()
        lines.append("")
        lines.append(
            f"File `{report.file_state.path}`: hit-ready kinds — "
            + (", ".join(ready) if ready else "none"))
    if report.warm_result is not None:
        lines.append("")
        lines.append(
            f"Warm run: {report.warm_result.filled()} entr"
            f"{'y' if report.warm_result.filled() == 1 else 'ies'} "
            f"filled over {report.warm_result.files_seen} file(s), "
            f"{report.warm_result.hits} hit(s).")
    lines.append("")
    return "\n".join(lines)
