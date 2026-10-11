"""Semantic file selection via local tf-idf keyword scoring (Slice 057).

No external embeddings dependency: files are scored against the query
with a deterministic tf-idf model over lowercased alphanumeric tokens.
The top-N files that fit the budget become context blocks.
"""

from __future__ import annotations

__all__ = [
    "CorpusDoc",
    "SemanticSelection",
    "build_corpus",
    "score_corpus",
    "select_files",
    "tokenize",
]

import logging
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import re

from ..core.workspace import assert_within_workspace, canonical_workspace_root
from .budget import TokenEstimator
from .compiler import ContextBlock, ContextSource


WORD_RE = re.compile(r"[a-z0-9]+")

EXTENSIONS = (".py", ".md", ".txt", ".toml", ".yaml", ".yml", ".json", ".cfg", ".ini")
MAX_FILES = 200
MAX_FILE_BYTES = 65_536
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
              "dist", "build", ".hg", ".svn"}


def tokenize(text: str) -> list[str]:
    """Lowercased alphanumeric tokens."""
    return WORD_RE.findall(text.lower())


@dataclass
class CorpusDoc:
    """One indexed document."""

    doc_id: str  # workspace-relative path
    text: str
    term_counts: dict[str, int] = field(default_factory=dict)


def build_corpus(
    workspace: Path | str,
    *,
    extensions: tuple[str, ...] = EXTENSIONS,
    max_files: int = MAX_FILES,
    max_file_bytes: int = MAX_FILE_BYTES,
) -> tuple[list[CorpusDoc], list[str]]:
    """Index text files under *workspace*; returns (docs, warnings)."""
    root = canonical_workspace_root(workspace)
    docs: list[CorpusDoc] = []
    warnings: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames
                             if d not in _SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            if len(docs) >= max_files:
                warnings.append(f"corpus file cap reached ({max_files})")
                return docs, warnings
            if not name.lower().endswith(extensions):
                continue
            candidate = Path(dirpath) / name
            try:
                resolved = assert_within_workspace(root, candidate)
            except Exception as exc:
                warnings.append(f"blocked {candidate}: {exc}")
                continue
            try:
                raw = resolved.read_bytes()
            except OSError as exc:
                warnings.append(f"unreadable {resolved}: {exc}")
                continue
            if len(raw) > max_file_bytes or b"\x00" in raw:
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                warnings.append(f"malformed (not utf-8): {resolved}")
                continue
            if not text.strip():
                continue
            counts: dict[str, int] = {}
            for token in tokenize(text):
                counts[token] = counts.get(token, 0) + 1
            docs.append(CorpusDoc(
                doc_id=str(resolved.relative_to(root)), text=text,
                term_counts=counts))
    return docs, warnings


def score_corpus(query: str, docs: list[CorpusDoc]) -> list[tuple[CorpusDoc, float]]:
    """Rank *docs* against *query* with tf-idf; deterministic."""
    query_terms = tokenize(query or "")
    if not query_terms or not docs:
        return []
    doc_count = len(docs)
    doc_freq: dict[str, int] = {}
    for doc in docs:
        for term in doc.term_counts:
            doc_freq[term] = doc_freq.get(term, 0) + 1
    idf = {term: math.log((1 + doc_count) / (1 + freq)) + 1.0
           for term, freq in doc_freq.items()}
    scored: list[tuple[CorpusDoc, float]] = []
    for doc in docs:
        score = 0.0
        for term in query_terms:
            tf = doc.term_counts.get(term)
            if tf:
                score += (1.0 + math.log(tf)) * idf[term]
        if score > 0:
            scored.append((doc, score))
    # Deterministic: score desc, then doc_id asc.
    scored.sort(key=lambda pair: (-pair[1], pair[0].doc_id))
    return scored


@dataclass
class SemanticSelection:
    """Outcome of :func:`select_files`."""

    files: list[CorpusDoc]
    scores: dict[str, float]
    warnings: list[str]


def select_files(
    query: str,
    workspace: Path | str,
    *,
    top_n: int = 5,
    budget_tokens: int = 2000,
    estimator: TokenEstimator | None = None,
    extensions: tuple[str, ...] = EXTENSIONS,
) -> SemanticSelection:
    """Select up to *top_n* files by tf-idf score inside *budget_tokens*."""
    if top_n <= 0:
        raise ValueError("top_n must be positive")
    if budget_tokens < 0:
        raise ValueError("budget_tokens must be non-negative")
    estimator = estimator or TokenEstimator()
    docs, warnings = build_corpus(workspace, extensions=extensions)
    ranked = score_corpus(query, docs)
    selected: list[CorpusDoc] = []
    scores: dict[str, float] = {}
    remaining = budget_tokens
    for doc, score in ranked:
        if len(selected) >= top_n:
            break
        cost = estimator.count(doc.text)
        if cost <= remaining:
            selected.append(doc)
            scores[doc.doc_id] = score
            remaining -= cost
    return SemanticSelection(files=selected, scores=scores, warnings=warnings)


class SemanticFilesSource(ContextSource):
    """Compiler source selecting files by tf-idf query match (Slice 057)."""

    def __init__(self, *, priority: int = 4, enabled: bool = True,
                 top_n: int = 5, budget_tokens: int = 2000) -> None:
        self.name = "semantic-files"
        self.priority = priority
        self.enabled = enabled
        self.top_n = top_n
        self.budget_tokens = budget_tokens

    def collect(self, ctx) -> list[ContextBlock]:
        if not (ctx.query or "").strip():
            return []
        selection = select_files(ctx.query, ctx.workspace, top_n=self.top_n,
                                 budget_tokens=self.budget_tokens)
        for warning in selection.warnings:
            logging.getLogger(__name__).warning("semantic-files: %s", warning)
        blocks = []
        for doc in selection.files:
            blocks.append(ContextBlock(
                name=f"semantic:{doc.doc_id}",
                content=f"--- {doc.doc_id} (relevance "
                        f"{selection.scores[doc.doc_id]:.2f}) ---\n{doc.text}",
                priority=self.priority,
                provenance={"doc_id": doc.doc_id,
                            "score": selection.scores[doc.doc_id]}))
        return blocks
