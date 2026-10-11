"""
TIER: unit
Tests for semantic file selection via local tf-idf keyword scoring
(Slice 057). No embeddings, no network: deterministic ranking only.
"""

import pytest

from mythic_agent.context import (
    ContextCompiler,
    SemanticFilesSource,
    build_corpus,
    score_corpus,
    select_files,
    tokenize,
)
from mythic_agent.context.semantic import CorpusDoc


def _ws(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "auth.py").write_text(
        "def login(user, password):\n    return authenticate(user, password)\n")
    (tmp_path / "billing.py").write_text(
        "def charge_card(card):\n    return invoice_total(card)\n")
    (tmp_path / "readme.md").write_text("# project\nnothing relevant here\n")
    return tmp_path


# ---------------------------------------------------------------------------
# tokenize / scoring
# ---------------------------------------------------------------------------

def test_tokenize_lowercases_and_splits():
    assert tokenize("Hello, WORLD_123!") == ["hello", "world", "123"]


def test_score_ranks_relevant_doc_first():
    docs = [
        CorpusDoc("a.py", "login password authenticate user session"),
        CorpusDoc("b.py", "invoice billing charge card payment"),
    ]
    for doc in docs:
        counts = {}
        for token in tokenize(doc.text):
            counts[token] = counts.get(token, 0) + 1
        doc.term_counts = counts
    ranked = score_corpus("how does login authenticate the user session", docs)
    assert ranked[0][0].doc_id == "a.py"
    assert ranked[0][1] > 0


def test_score_is_deterministic():
    docs = [CorpusDoc("a.py", "alpha beta gamma " * 10),
            CorpusDoc("b.py", "alpha delta " * 10)]
    for doc in docs:
        counts = {}
        for token in tokenize(doc.text):
            counts[token] = counts.get(token, 0) + 1
        doc.term_counts = counts
    first = [(d.doc_id, s) for d, s in score_corpus("alpha gamma", docs)]
    second = [(d.doc_id, s) for d, s in score_corpus("alpha gamma", docs)]
    assert first == second


def test_score_empty_query_or_corpus():
    docs = [CorpusDoc("a.py", "hello")]
    assert score_corpus("", docs) == []
    assert score_corpus("hello", []) == []


def test_score_ties_broken_by_doc_id():
    docs = [CorpusDoc("b.py", "same words here"),
            CorpusDoc("a.py", "same words here")]
    for doc in docs:
        counts = {}
        for token in tokenize(doc.text):
            counts[token] = counts.get(token, 0) + 1
        doc.term_counts = counts
    ranked = score_corpus("same words", docs)
    assert [d.doc_id for d, _ in ranked] == ["a.py", "b.py"]


# ---------------------------------------------------------------------------
# corpus building
# ---------------------------------------------------------------------------

def test_build_corpus_indexes_workspace(tmp_path):
    ws = _ws(tmp_path)
    docs, warnings = build_corpus(ws)
    ids = {d.doc_id for d in docs}
    assert {"auth.py", "billing.py", "readme.md"} <= ids
    assert warnings == []


def test_build_corpus_skips_binary_and_bad_encoding(tmp_path):
    ws = _ws(tmp_path)
    (ws / "blob.py").write_bytes(b"\x00\x01binary")
    (ws / "latin.py").write_bytes("héllo".encode("latin-1"))
    docs, warnings = build_corpus(ws)
    ids = {d.doc_id for d in docs}
    assert "blob.py" not in ids and "latin.py" not in ids
    assert any("latin.py" in w for w in warnings)


def test_build_corpus_cross_workspace_isolation(tmp_path):
    ws_a = _ws(tmp_path / "a")
    _ws(tmp_path / "b")
    docs, _ = build_corpus(ws_a)
    # Only ws_a's own files are indexed; nothing from the sibling workspace.
    assert {d.doc_id for d in docs} == {"auth.py", "billing.py", "readme.md"}


# ---------------------------------------------------------------------------
# selection
# ---------------------------------------------------------------------------

def test_select_files_top_n_within_budget(tmp_path):
    ws = _ws(tmp_path)
    selection = select_files("user login password authenticate", ws,
                             top_n=1, budget_tokens=10_000)
    assert [d.doc_id for d in selection.files] == ["auth.py"]
    assert selection.scores["auth.py"] > 0


def test_select_files_budget_excludes_oversized(tmp_path):
    ws = _ws(tmp_path)
    selection = select_files("user login password authenticate", ws,
                             top_n=5, budget_tokens=1)
    assert selection.files == []


def test_select_files_rejects_bad_args(tmp_path):
    ws = _ws(tmp_path)
    with pytest.raises(ValueError):
        select_files("q", ws, top_n=0)
    with pytest.raises(ValueError):
        select_files("q", ws, budget_tokens=-1)


def test_semantic_source_via_compiler(tmp_path):
    ws = _ws(tmp_path)
    compiler = ContextCompiler(ws)
    compiler.add_source(SemanticFilesSource(top_n=2, budget_tokens=10_000))
    compiled = compiler.compile("how does login authenticate the user")
    ids = [b.name for b in compiled.blocks]
    assert ids and ids[0] == "semantic:auth.py"
    assert "relevance" in compiled.blocks[0].content


def test_semantic_source_empty_query_yields_nothing(tmp_path):
    ws = _ws(tmp_path)
    compiler = ContextCompiler(ws)
    compiler.add_source(SemanticFilesSource())
    assert compiler.compile("").blocks == []
