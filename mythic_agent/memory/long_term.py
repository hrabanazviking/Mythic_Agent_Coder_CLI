"""Long-term memory (Slice 42).

``LongTermMemory`` stores durable cross-project facts (learnings, coding
style notes, preferences) and recalls them with a pure-Python TF-IDF
ranker — no external dependencies. Facts persist to
``<workspace>/.mythic/long_term.json``.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "DEFAULT_STORE_NAME",
    "LongTermMemory",
    "MemoryFact",
    "Optional",
    "Path",
    "dataclass",
    "field",
]

import json
import math
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

__all__ = ["LongTermMemory", "MemoryFact", "DEFAULT_STORE_NAME"]

DEFAULT_STORE_NAME = "long_term.json"
_TOKEN_RE = re.compile(r"[a-z0-9_]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


@dataclass
class MemoryFact:
    """A single durable fact with provenance."""
    text: str
    created: float = field(default_factory=time.time)
    tags: list[str] = field(default_factory=list)
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"text": self.text, "created": self.created,
                "tags": list(self.tags), "source": self.source}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryFact":
        return cls(text=data.get("text", ""),
                   created=float(data.get("created", 0.0)),
                   tags=list(data.get("tags", [])),
                   source=str(data.get("source", "")))


class LongTermMemory:
    """Keyword/TF-IDF long-term memory persisted per workspace.

    Args:
        workspace: Project directory. The store lives at
            ``<workspace>/.mythic/long_term.json``. When omitted, the
            current working directory is used.
    """

    def __init__(self, workspace: Optional[str | Path] = None) -> None:
        self.workspace = Path(workspace) if workspace is not None else Path.cwd()
        self.store_path = self.workspace / ".mythic" / DEFAULT_STORE_NAME
        self._facts: list[MemoryFact] = []
        self._lock = threading.Lock()
        self.load()

    # -- storage --------------------------------------------------------

    def store(self, fact: str, *, tags: Optional[list[str]] = None,
              source: str = "") -> MemoryFact:
        """Persist a fact. Duplicate texts are not stored twice."""
        fact = fact.strip()
        if not fact:
            raise ValueError("cannot store an empty fact")
        with self._lock:
            for existing in self._facts:
                if existing.text == fact:
                    # Refresh tags/source on re-store.
                    if tags:
                        for t in tags:
                            if t not in existing.tags:
                                existing.tags.append(t)
                    if source:
                        existing.source = source
                    self._save_locked()
                    return existing
            entry = MemoryFact(text=fact, tags=list(tags or []), source=source)
            self._facts.append(entry)
            self._save_locked()
            return entry

    def forget(self, fact: str) -> bool:
        """Remove a fact by exact text. Returns True if removed."""
        fact = fact.strip()
        with self._lock:
            for i, existing in enumerate(self._facts):
                if existing.text == fact:
                    del self._facts[i]
                    self._save_locked()
                    return True
        return False

    def clear(self) -> int:
        """Remove all facts. Returns the number removed."""
        with self._lock:
            n = len(self._facts)
            self._facts.clear()
            self._save_locked()
            return n

    def __len__(self) -> int:
        with self._lock:
            return len(self._facts)

    def all(self) -> list[MemoryFact]:
        """Return a snapshot of every stored fact."""
        with self._lock:
            return list(self._facts)

    # -- recall ----------------------------------------------------------

    def _idf(self, corpus_tokens: list[list[str]]) -> dict[str, float]:
        """Inverse document frequency over the fact corpus."""
        n_docs = max(len(corpus_tokens), 1)
        df: dict[str, int] = {}
        for tokens in corpus_tokens:
            for tok in set(tokens):
                df[tok] = df.get(tok, 0) + 1
        return {tok: math.log((1 + n_docs) / (1 + c)) + 1.0
                for tok, c in df.items()}

    def _score(self, query_tokens: list[str],
               facts: list[MemoryFact]) -> list[tuple[float, MemoryFact]]:
        """Score *facts* against tokenized query; sorted (score, fact)."""
        docs: list[list[str]] = []
        for f in facts:
            docs.append(_tokenize(f.text) + [t.lower() for t in f.tags])
        idf = self._idf(docs)

        def tfidf(tokens: list[str]) -> dict[str, float]:
            tf: dict[str, float] = {}
            for tok in tokens:
                tf[tok] = tf.get(tok, 0.0) + 1.0
            n = len(tokens) or 1
            return {tok: (c / n) * idf.get(tok, 1.0) for tok, c in tf.items()}

        q_vec = tfidf(query_tokens)
        q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0
        query_set = set(query_tokens)

        scored: list[tuple[float, MemoryFact]] = []
        for fact, tokens in zip(facts, docs):
            d_vec = tfidf(tokens)
            dot = sum(q_vec.get(t, 0.0) * d_vec.get(t, 0.0) for t in q_vec)
            d_norm = math.sqrt(sum(v * v for v in d_vec.values())) or 1.0
            cosine = dot / (q_norm * d_norm)
            overlap = len(query_set & set(tokens)) / max(len(query_set), 1)
            score = 0.7 * cosine + 0.3 * overlap
            if score > 0:
                scored.append((score, fact))
        scored.sort(key=lambda s: s[0], reverse=True)
        return scored

    def recall(self, query: str, top_k: int = 5) -> list[str]:
        """Return up to *top_k* fact texts most relevant to *query*.

        Scores combine TF-IDF cosine similarity with a bonus for exact
        query-token overlap and tag matches. Empty or unmatched queries
        return an empty list.
        """
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []
        with self._lock:
            facts = list(self._facts)
        if not facts:
            return []
        scored = self._score(query_tokens, facts)
        return [f.text for _, f in scored[:max(top_k, 0)]]

    def recall_with_scores(self, query: str,
                           top_k: int = 5) -> list[tuple[str, float]]:
        """Like :meth:`recall` but also returns relevance scores."""
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []
        with self._lock:
            facts = list(self._facts)
        scored = self._score(query_tokens, facts)
        return [(f.text, s) for s, f in scored[:max(top_k, 0)]]

    # -- persistence -----------------------------------------------------

    def _save_locked(self) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.store_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps([f.to_dict() for f in self._facts],
                                  indent=2, ensure_ascii=False),
                       encoding="utf-8")
        tmp.replace(self.store_path)

    def load(self) -> "LongTermMemory":
        """Reload facts from disk (no-op when the store is missing)."""
        with self._lock:
            if not self.store_path.exists():
                self._facts = []
                return self
            try:
                data = json.loads(self.store_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._facts = []
                return self
            self._facts = [MemoryFact.from_dict(d) for d in data
                           if isinstance(d, dict) and d.get("text")]
        return self

    def export(self, path: str | Path) -> Path:
        """Export facts to *path* as JSON (privacy: caller chooses destination)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            path.write_text(json.dumps([f.to_dict() for f in self._facts],
                                       indent=2, ensure_ascii=False),
                            encoding="utf-8")
        return path

    def import_facts(self, path: str | Path) -> int:
        """Import facts from a JSON export. Returns the number added."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        added = 0
        for d in data:
            if isinstance(d, dict) and d.get("text"):
                before = len(self)
                self.store(d["text"], tags=d.get("tags"), source=d.get("source", ""))
                if len(self) > before:
                    added += 1
        return added
