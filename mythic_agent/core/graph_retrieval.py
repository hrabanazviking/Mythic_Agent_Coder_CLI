"""Retrieval over the code graph (All-Features roadmap slice M-152).

Part VII continues. The roadmap's words:
``vector RAG (existing) married to Part III's symbol
graph - retrieval returns *connected* code, not
confetti.``

What already shipped, and what this slice adds:

* Vector RAG already runs in this repo: the memory
  layer's vector providers
  (``memory/vector_db.py``) search archived text by
  embedding and answer ``{score, text, metadata}``
  mappings, and the context layer's semantic road
  (``context/semantic.py``, Slice 057) scores files
  against a query with a deterministic tf-idf model -
  no external embeddings, no network. Both answer
  with ranked hits, and both stop there: a hit stands
  alone, with nothing of the code around it.
* Part III's symbol graph
  (``context/symbol_graph.py``, M-046) knows the code
  itself: definitions, references, imports and call
  edges extracted per language from the M-043 parses,
  name-based resolution with its ambiguity recorded,
  and per-symbol queries (``definitions_named``,
  ``references_to``, ``callers_of``, ``callees_of``,
  ``imports_of``, ``file_edges``). Nothing married
  the ranked hits to that graph.
* This slice is that marriage, as a pure layer: a
  seed hit validated as data (its file, its symbol
  where it names one, its score, and its source -
  the semantic road, a vector provider, the symbol
  road, or a manual naming), an expansion that walks
  the shipped graph FROM each seed through its own
  query roads and returns the connected code -
  the seed itself, the definitions standing beside
  it in its file, its callers and callees, its
  reference sites, the files it imports and the
  files that import it - every piece carrying its
  provenance (which seed, which relation, how far),
  a bundle holding the expansion in deterministic
  ranked order with its skipped seeds and its
  over-cap count named, a panel DERIVED from the
  bundle, the shipped data file
  (``mythic_agent/data/graph_retrieval.yaml``)
  holding one example book in exactly the shape a
  real book file takes, a loader for a book file
  anywhere on disk, seed roads that build seeds from
  the shipped semantic scoring BY IMPORT, from
  vector-provider results in their shipped shape,
  and from a query's own symbol mentions read off
  the graph, and a small in-memory registry model.
  The agent layer owns holding bundles for a
  session and running a retrieval over a workspace.

Honesty rules, enforced here and pinned by tests:

* **Connected, or named as not connected.** Every
  returned piece names the seed it grew from, the
  relation that connects it, and its distance from
  that seed. A seed naming a file or symbol the
  graph does not hold returns nothing and stands in
  the bundle's ``skipped`` with its reason - it is
  never silently relocated to some other file, and
  never dressed up as a hit.
* **Resolution stays the graph's own.** Expansion
  reads definitions, references, imports and calls
  through the shipped graph's queries, so its
  name-based resolution - ambiguity recorded, all
  sites carried - is this layer's resolution too.
  Nothing here re-parses source, re-scores files
  with a second model, or dresses a name match as
  a type proof; type-true resolution remains the
  LSP road (M-050).
* **Ranking is deterministic.** A piece's score is
  its seed's score, halved at each hop
  (``GRAPH_DECAY``); order is score, then distance,
  then relation (in ``RELATIONS`` order), then
  path, symbol and line - two expansions of the
  same seeds over the same graph stand in the same
  order, every time. Pieces beyond the node cap are
  counted in ``omitted``, never silently dropped.
* **The panel is derived, never stored loose.**
  Its rows are the bundle's pieces carried whole,
  in ranked order, and its totals are the pieces'
  own counts; a stored panel or bundle whose rows,
  totals, counts or account disagree with the
  derived shape refuses.
* **Data only - retrieving runs no model and
  changes no code.** A bundle here is validated
  data: no model is called, no file is edited, no
  live context is assembled, and nothing persists
  beyond the session journal news the agent layer
  publishes. The seed roads read the shipped
  semantic corpus as data and the graph as data.
* **Malformed refuses.** A duplicate bundle id in
  one book, two pieces with one identity in one
  bundle, a seed naming no path, a non-positive or
  non-finite score, and unknown keys in a seed, a
  piece, a bundle, a panel or a book mapping all
  raise instead of being skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..context.semantic import score_corpus, tokenize
from ..context.symbol_graph import MODULE_CALLER, SymbolGraph
from ..resources import load_resource
from .crew_members import normalize_member_id
from .validation import ValidationError

__all__ = [
    "PLAIN_EXPLANATION",
    "GRAPH_DECAY",
    "GRAPH_RETRIEVAL_RESOURCE",
    "GRAPH_RETRIEVAL_SCHEMA",
    "GRAPH_RETRIEVAL_SLICE",
    "MAX_RETRIEVAL_DEPTH",
    "RELATIONS",
    "SEED_SOURCES",
    "USAGE",
    "ConnectedNode",
    "GraphRelationCount",
    "GraphRetrievalRegistry",
    "RetrievalBook",
    "RetrievalBundle",
    "RetrievalPanel",
    "RetrievalSeed",
    "book_record",
    "build_book",
    "build_bundle",
    "build_node",
    "build_panel",
    "build_seed",
    "bundle_record",
    "derive_panel",
    "expand_retrieval",
    "format_graph_retrieval_screen",
    "format_node",
    "format_nodes",
    "format_panel",
    "format_seeds",
    "load_graph_retrieval",
    "load_graph_retrieval_file",
    "node_record",
    "panel_plain_words",
    "panel_record",
    "parse_graphsearch_args",
    "plain_words",
    "retrieve",
    "seeds_from_query",
    "seeds_from_semantic",
    "seeds_from_vector_results",
    "validate_book",
    "validate_bundle",
    "validate_node",
    "validate_panel",
    "validate_seed",
]

GRAPH_RETRIEVAL_SLICE = "M-152"

#: The packaged data resource holding the example book.
GRAPH_RETRIEVAL_RESOURCE = "graph_retrieval.yaml"

#: The schema word a graph-retrieval file must carry.
GRAPH_RETRIEVAL_SCHEMA = "mythic.graph_retrieval/1"

#: How much of a seed's score one hop keeps.
GRAPH_DECAY = 0.5

#: The deepest expansion this layer walks.
MAX_RETRIEVAL_DEPTH = 2

#: The connecting relations, in ranking order.
RELATIONS = (
    "seed", "definition", "caller", "callee",
    "reference", "import", "imported-by", "file-neighbour")

_RELATION_RANK = {name: index for index, name in enumerate(RELATIONS)}

#: Where a seed may come from: the shipped roads.
SEED_SOURCES = ("semantic", "vector", "symbol", "manual")

_SEED_KEYS = frozenset({
    "seed_id", "id", "path", "file", "doc_id",
    "symbol", "name", "score", "relevance", "source",
})

_NODE_KEYS = frozenset({
    "node_id", "id", "path", "file", "symbol", "name",
    "kind", "relation", "distance", "seed_score",
    "score", "seed_id", "provenance", "detail",
    "line",
})

_RELATION_COUNT_KEYS = frozenset({"relation", "nodes", "count"})

_BUNDLE_KEYS = frozenset({
    "bundle_id", "id", "query", "depth",
    "seeds", "nodes", "pieces",
    "total_nodes", "total", "total_seeds",
    "file_count", "omitted", "skipped",
    "relation_counts", "relations", "account", "statements",
})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "rows", "nodes", "pieces",
    "total_nodes", "total", "total_seeds",
    "file_count", "omitted", "skipped",
    "relation_counts", "relations", "account", "statements",
})

_BOOK_KEYS = frozenset({"title", "name"})

_GRAPH_RETRIEVAL_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "bundles", "panels",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Graph retrieval at the M-151 slice boundary"

#: The shipped example's bundle ids, in held order,
#: pinned by the loader.
_EXAMPLE_BUNDLE_IDS = ("retrieval-m151-boundary",)

#: The shipped example bundle's query, pinned.
_EXAMPLE_QUERY = "compaction glass-box summary versions journal"

#: The shipped example's one panel id, and its rows
#: in ranked order, pinned by the loader.
_EXAMPLE_PANEL_ID = "panel-m151-boundary"

_EXAMPLE_PANEL_ROW_IDS = (
    "node-1", "node-2", "node-3", "node-4", "node-5", "node-6")

PLAIN_EXPLANATION = (
    "Retrieval over the code graph: the existing "
    "vector and semantic search names the seeds, and "
    "Part III's symbol graph grows each seed into the "
    "code connected to it - retrieval returns "
    "connected code, not confetti. A seed names one "
    "hit (its file, its symbol where it names one, "
    "its score, and its source among the shipped "
    "roads). The expansion walks the graph from each "
    "seed: the seed itself, the definitions beside "
    "it, its callers and callees, its reference "
    "sites, and the files it imports or is imported "
    "by - every piece carrying its provenance, its "
    "relation and its distance, ranked "
    "deterministically by its seed's score halved at "
    "each hop. A seed the graph cannot answer for "
    "stands skipped with its reason, pieces beyond "
    "the cap are counted, and the panel is derived "
    "from the bundle at call time. This layer holds "
    "retrievals as data only: it calls no model, "
    "edits no code, assembles no live context and "
    "persists nothing."
)

USAGE = (
    "Usage: /graphsearch, /graphsearch show, "
    "/graphsearch node <node-id>, "
    "/graphsearch seeds, /graphsearch panel"
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_title(value: Any, what: str = "a title") -> str:
    text = _clean_text(value, what)
    if len(text) > 120 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"120 characters, got {len(text)} characters")
    return text


def _check_long_text(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if len(text) > 2000 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"2000 characters, got {len(text)} characters")
    return text


def _check_query(value: Any) -> str:
    text = _clean_text(value, "a retrieval query")
    if len(text) > 500 or "\x00" in text:
        raise ValueError(
            f"a retrieval query must be plain text of at most "
            f"500 characters, got {len(text)} characters")
    return text


def _check_path(value: Any, what: str = "a seed's path") -> str:
    text = _clean_text(value, what)
    if len(text) > 300 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"300 characters, got {len(text)} characters")
    if text.startswith(("/", "\\")) or text[1:3] == ":\\":
        raise ValueError(
            f"{what} must be a workspace-relative path, "
            f"got {text!r}")
    if any(part == ".." for part in text.replace("\\", "/").split("/")):
        raise ValueError(
            f"{what} must stay inside the workspace, "
            f"got {text!r}")
    return text


def _check_symbol(value: Any, what: str = "a symbol") -> str:
    text = _clean_text(value, what)
    if len(text) > 120 or any(ch.isspace() for ch in text):
        raise ValueError(
            f"{what} must be one word of at most "
            f"120 characters, got {text!r}")
    return text


def _check_score(value: Any, what: str = "a seed's score") -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{what} must be a number, got {value!r}")
    score = float(value)
    if score != score or score in (float("inf"), float("-inf")):
        raise ValueError(f"{what} must be finite, got {value!r}")
    if score <= 0:
        raise ValueError(f"{what} must be positive, got {value!r}")
    if score > 1_000_000:
        raise ValueError(f"{what} is implausibly large, got {value!r}")
    return score


def _check_count(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a count, got {value!r}")
    if value < 0:
        raise ValueError(f"{what} must not be negative, got {value!r}")
    return value


def _check_line(value: Any) -> Optional[int]:
    if value is None:
        return None
    line = _check_count(value, "a piece's line")
    if line < 1:
        raise ValueError(f"a piece's line must be at least 1, got {value!r}")
    return line


def _check_account(value: Any) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"an account must be a list of statements, "
            f"got {value!r}")
    account = tuple(
        _check_long_text(a, "an account statement")
        for a in value)
    if not account:
        raise ValueError("an account carries at least one statement")
    if len(account) > 16:
        raise ValueError(
            f"an account carries at most 16 statements, "
            f"got {len(account)}")
    if len(set(account)) != len(account):
        raise ValueError("an account states one statement twice")
    return account


def _pick_any(mapping: Dict[str, Any], spellings: Tuple[str, ...],
              what: str) -> Any:
    values = [mapping[s] for s in spellings if s in mapping]
    if not values:
        return None
    if any(value != values[0] for value in values[1:]):
        raise ValueError(f"a mapping names two different {what}")
    return values[0]


def _check_provenance(value: Any) -> str:
    text = _clean_text(value, "a piece's provenance")
    if len(text) > 300 or "\x00" in text:
        raise ValueError(
            f"a piece's provenance must be plain text of at most "
            f"300 characters, got {len(text)} characters")
    return text


def _check_skipped(value: Any) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) \
            or not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a bundle's skipped seeds must be a list of "
            f"reasons, got {value!r}")
    reasons = tuple(
        _check_provenance(r) for r in value)
    if len(reasons) > 32:
        raise ValueError(
            f"a bundle names at most 32 skipped seeds, "
            f"got {len(reasons)}")
    return reasons


# ---------------------------------------------------------------------
# The seed: one ranked hit, as data - its file, its symbol
# where it names one, its score, and the road it came by.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class RetrievalSeed:
    """One retrieval seed: a ranked hit the graph grows.

    ``path`` is the hit's workspace-relative file;
    ``symbol`` is the definition the hit names, where
    it names one (a file-level hit names none);
    ``score`` is the hitting road's own score, kept
    whole - every piece grown from this seed derives
    its rank from it; ``source`` is the shipped road
    the hit came by, one of ``SEED_SOURCES``.
    """

    path: str
    score: float
    source: str
    symbol: Optional[str] = None
    seed_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.seed_id is not None:
            object.__setattr__(
                self, "seed_id",
                normalize_member_id(self.seed_id))
        object.__setattr__(
            self, "path", _check_path(self.path))
        object.__setattr__(
            self, "score", _check_score(self.score))
        source = _clean_text(self.source, "a seed's source")
        if source not in SEED_SOURCES:
            raise ValueError(
                f"a seed's source must be one of "
                f"{', '.join(SEED_SOURCES)}, got {source!r}")
        object.__setattr__(self, "source", source)
        if self.symbol is not None:
            object.__setattr__(
                self, "symbol",
                _check_symbol(self.symbol, "a seed's symbol"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "graph_retrieval_seed",
            "slice": GRAPH_RETRIEVAL_SLICE,
            "seed_id": self.seed_id,
            "path": self.path,
            "symbol": self.symbol,
            "score": self.score,
            "source": self.source,
        }


def validate_seed(seed: Any) -> RetrievalSeed:
    """Validate one seed into a RetrievalSeed.

    Accepts a seed or a mapping naming a ``path``
    (or ``file`` / ``doc_id``), a ``score`` (or
    ``relevance``), a ``source``, an optional
    ``symbol`` (or ``name``) and an optional
    ``seed_id`` (or ``id``). Naming two spellings of
    one field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(seed, RetrievalSeed):
        return seed
    if not isinstance(seed, dict):
        raise ValueError(
            f"a retrieval seed must be a mapping, "
            f"got {seed!r}")
    unknown = set(seed) - _SEED_KEYS
    if unknown:
        raise ValueError(
            "unknown seed keys: %s"
            % ", ".join(sorted(unknown)))
    path = _pick_any(seed, ("path", "file", "doc_id"), "paths")
    if path is None:
        raise ValueError("a retrieval seed is missing its path")
    score = _pick_any(seed, ("score", "relevance"), "scores")
    if score is None:
        raise ValueError("a retrieval seed is missing its score")
    source = _pick_any(seed, ("source",), "sources")
    if source is None:
        raise ValueError("a retrieval seed is missing its source")
    kwargs: Dict[str, Any] = {
        "path": path, "score": score, "source": source}
    symbol = _pick_any(seed, ("symbol", "name"), "symbols")
    if symbol is not None:
        kwargs["symbol"] = symbol
    seed_id = _pick_any(seed, ("seed_id", "id"), "seed ids")
    if seed_id is not None:
        kwargs["seed_id"] = seed_id
    return RetrievalSeed(**kwargs)


def build_seed(seed: Any = None, **kwargs: Any) -> RetrievalSeed:
    """Build one validated seed, from a mapping or field words."""
    if isinstance(seed, RetrievalSeed) and not kwargs:
        return seed
    if isinstance(seed, dict) or seed is None:
        merged: Dict[str, Any] = {}
        if isinstance(seed, dict):
            merged.update(seed)
        merged.update(kwargs)
        return validate_seed(merged)
    raise ValueError(
        f"a retrieval seed must be a mapping, got {seed!r}")


def _check_seed_ref(value: Any) -> RetrievalSeed:
    if isinstance(value, RetrievalSeed):
        return value
    if isinstance(value, dict):
        return validate_seed(value)
    raise ValueError(f"a retrieval seed is needed, got {value!r}")


# ---------------------------------------------------------------------
# The piece: one connected code site, grown from one seed -
# its relation, its distance, and its provenance.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ConnectedNode:
    """One piece of connected code, grown from one seed.

    ``path`` and ``symbol`` name the code (a
    file-level piece names no symbol); ``kind`` is
    the definition kind where the graph carries one,
    or the honest word for what stands there
    (``file``, ``module``, ``unresolved``);
    ``relation`` is how this piece connects to its
    seed, one of ``RELATIONS``; ``distance`` is its
    hops from the seed (0 for the seed itself, which
    is the only piece whose relation is ``seed``);
    ``seed_score`` is its seed's own score, kept
    whole - the piece's rank is derived from it at
    call time, halved at each hop; ``seed_id`` names
    the seed it grew from, where the seed carries an
    id; ``provenance`` says in plain words why this
    piece stands here; ``line`` is its line in its
    file, where the graph names one.
    """

    path: str
    relation: str
    distance: int
    seed_score: float
    provenance: str
    symbol: Optional[str] = None
    kind: str = "file"
    seed_id: Optional[str] = None
    line: Optional[int] = None
    node_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.node_id is not None:
            object.__setattr__(
                self, "node_id",
                normalize_member_id(self.node_id))
        if self.seed_id is not None:
            object.__setattr__(
                self, "seed_id",
                normalize_member_id(self.seed_id))
        object.__setattr__(
            self, "path", _check_path(self.path, "a piece's path"))
        relation = _clean_text(self.relation, "a piece's relation")
        if relation not in _RELATION_RANK:
            raise ValueError(
                f"a piece's relation must be one of "
                f"{', '.join(RELATIONS)}, got {relation!r}")
        object.__setattr__(self, "relation", relation)
        distance = _check_count(self.distance, "a piece's distance")
        if distance > MAX_RETRIEVAL_DEPTH:
            raise ValueError(
                f"a piece stands at most {MAX_RETRIEVAL_DEPTH} "
                f"hops from its seed, got {distance}")
        object.__setattr__(self, "distance", distance)
        if relation == "seed" and distance != 0:
            raise ValueError(
                "the seed piece itself stands at distance 0")
        if relation != "seed" and distance == 0:
            raise ValueError(
                "only the seed piece itself stands at distance 0")
        object.__setattr__(
            self, "seed_score",
            _check_score(self.seed_score, "a piece's seed score"))
        object.__setattr__(
            self, "provenance", _check_provenance(self.provenance))
        if self.symbol is not None:
            object.__setattr__(
                self, "symbol",
                _check_symbol(self.symbol, "a piece's symbol"))
        object.__setattr__(
            self, "kind", _check_title(self.kind, "a piece's kind"))
        object.__setattr__(self, "line", _check_line(self.line))

    @property
    def score(self) -> float:
        """This piece's rank score, derived at call time."""
        return self.seed_score * (GRAPH_DECAY ** self.distance)

    @property
    def identity(self) -> Tuple[str, Optional[str], str]:
        """What makes this piece one piece in a bundle."""
        return (self.path, self.symbol, self.relation)

    @property
    def sort_key(self) -> Tuple[Any, ...]:
        """This piece's place in ranked order (derived)."""
        return (
            -self.score, self.distance,
            _RELATION_RANK[self.relation], self.path,
            self.symbol or "", self.line or 0)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "graph_retrieval_node",
            "slice": GRAPH_RETRIEVAL_SLICE,
            "node_id": self.node_id,
            "path": self.path,
            "symbol": self.symbol,
            "kind": self.kind,
            "relation": self.relation,
            "distance": self.distance,
            "seed_score": self.seed_score,
            "score": self.score,
            "seed_id": self.seed_id,
            "provenance": self.provenance,
            "line": self.line,
        }


def validate_node(node: Any, seed: Any = None) -> ConnectedNode:
    """Validate one piece into a ConnectedNode.

    Accepts a piece or a mapping naming a ``path``
    (or ``file``), a ``relation``, a ``distance``, a
    ``seed_score``, a ``provenance`` (or ``detail``),
    an optional ``symbol`` (or ``name``), ``kind``,
    ``seed_id``, ``line`` and ``node_id`` (or
    ``id``). A named ``score`` is judged against the
    score derived from the seed score and distance
    and refuses on disagreement - a piece's rank is
    derived, never stored loose. With *seed* given,
    the piece is judged against that seed: its seed
    id and seed score must be the seed's own.
    """
    if isinstance(node, ConnectedNode):
        current = node
    elif isinstance(node, dict):
        unknown = set(node) - _NODE_KEYS
        if unknown:
            raise ValueError(
                "unknown node keys: %s"
                % ", ".join(sorted(unknown)))
        path = _pick_any(node, ("path", "file"), "paths")
        if path is None:
            raise ValueError("a connected piece is missing its path")
        relation = _pick_any(node, ("relation",), "relations")
        if relation is None:
            raise ValueError("a connected piece is missing its relation")
        distance = _pick_any(node, ("distance",), "distances")
        if distance is None:
            raise ValueError("a connected piece is missing its distance")
        seed_score = _pick_any(node, ("seed_score",), "seed scores")
        if seed_score is None:
            raise ValueError(
                "a connected piece is missing its seed score")
        provenance = _pick_any(
            node, ("provenance", "detail"), "provenances")
        if provenance is None:
            raise ValueError(
                "a connected piece is missing its provenance")
        kwargs: Dict[str, Any] = {
            "path": path, "relation": relation,
            "distance": distance, "seed_score": seed_score,
            "provenance": provenance}
        symbol = _pick_any(node, ("symbol", "name"), "symbols")
        if symbol is not None:
            kwargs["symbol"] = symbol
        kind = _pick_any(node, ("kind",), "kinds")
        if kind is not None:
            kwargs["kind"] = kind
        seed_id = _pick_any(node, ("seed_id",), "seed ids")
        if seed_id is not None:
            kwargs["seed_id"] = seed_id
        line = _pick_any(node, ("line",), "lines")
        if line is not None:
            kwargs["line"] = line
        node_id = _pick_any(node, ("node_id", "id"), "node ids")
        if node_id is not None:
            kwargs["node_id"] = node_id
        current = ConnectedNode(**kwargs)
        named_score = _pick_any(node, ("score",), "scores")
        if named_score is not None:
            named = _check_score(named_score, "a piece's score")
            if abs(named - current.score) > 1e-9:
                raise ValueError(
                    "a stored score disagrees with the score "
                    "derived from its seed score and distance - "
                    "a piece's rank is derived, never stored loose")
    else:
        raise ValueError(
            f"a connected piece must be a mapping, got {node!r}")
    if seed is not None:
        wanted = _check_seed_ref(seed)
        if current.seed_id != wanted.seed_id:
            raise ValueError(
                "a stored piece names a seed other than "
                "the seed it is judged against")
        if current.seed_score != wanted.score:
            raise ValueError(
                "a stored piece's seed score disagrees "
                "with its seed's own score")
    return current


def build_node(node: Any = None, seed: Any = None,
               **kwargs: Any) -> ConnectedNode:
    """Build one validated piece, from a mapping or field words."""
    if isinstance(node, ConnectedNode) and not kwargs:
        return validate_node(node, seed)
    if isinstance(node, dict) or node is None:
        merged: Dict[str, Any] = {}
        if isinstance(node, dict):
            merged.update(node)
        merged.update(kwargs)
        return validate_node(merged, seed)
    return validate_node(node, seed)


def _check_node_ref(value: Any) -> ConnectedNode:
    if isinstance(value, ConnectedNode):
        return value
    if isinstance(value, dict):
        return validate_node(value)
    raise ValueError(f"a connected piece is needed, got {value!r}")


# ---------------------------------------------------------------------
# Tallies, the account, and the bundle: one expansion, as
# data - its seeds, its pieces in ranked order, what was
# skipped and what stood beyond the cap, all named.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class GraphRelationCount:
    """One relation's count in a bundle or panel."""

    relation: str
    nodes: int

    def __post_init__(self) -> None:
        relation = _clean_text(
            self.relation, "a relation count's relation")
        if relation not in _RELATION_RANK:
            raise ValueError(
                f"a relation count's relation must be one of "
                f"{', '.join(RELATIONS)}, got {relation!r}")
        object.__setattr__(self, "relation", relation)
        object.__setattr__(
            self, "nodes",
            _check_count(self.nodes, "a relation count's nodes"))

    def to_record(self) -> Dict[str, Any]:
        return {"relation": self.relation, "nodes": self.nodes}


def _check_relation_count_ref(value: Any) -> GraphRelationCount:
    if isinstance(value, GraphRelationCount):
        return value
    if isinstance(value, dict):
        unknown = set(value) - _RELATION_COUNT_KEYS
        if unknown:
            raise ValueError(
                "unknown relation-count keys: %s"
                % ", ".join(sorted(unknown)))
        relation = _pick_any(value, ("relation",), "relations")
        if relation is None:
            raise ValueError("a relation count is missing its relation")
        nodes = _pick_any(value, ("nodes", "count"), "counts")
        if nodes is None:
            raise ValueError("a relation count is missing its nodes")
        return GraphRelationCount(relation=relation, nodes=nodes)
    raise ValueError(f"a relation count is needed, got {value!r}")


def _relation_counts(
        nodes: Tuple[ConnectedNode, ...]
        ) -> Tuple[GraphRelationCount, ...]:
    tally: Dict[str, int] = {}
    for node in nodes:
        tally[node.relation] = tally.get(node.relation, 0) + 1
    return tuple(
        GraphRelationCount(relation=relation, nodes=tally[relation])
        for relation in RELATIONS if relation in tally)


def _retrieval_account(total_seeds: int,
                       nodes: Tuple[ConnectedNode, ...],
                       omitted: int,
                       skipped: Tuple[str, ...]) -> Tuple[str, ...]:
    counts = _relation_counts(nodes)
    if counts:
        by_relation = ", ".join(
            f"{count.relation} {count.nodes}" for count in counts)
        first = (
            f"The bundle holds {len(nodes)} connected pieces "
            f"from {total_seeds} seed(s): {by_relation}.")
    else:
        first = (
            f"The bundle holds 0 connected pieces "
            f"from {total_seeds} seed(s).")
    files = len({node.path for node in nodes})
    second = (
        f"They span {files} file(s); every piece names its "
        f"seed and how it connects - retrieval returns "
        f"connected code, not confetti.")
    if skipped:
        third = (
            f"{len(skipped)} seed(s) named no graphed code "
            f"and stand skipped with their reasons.")
    else:
        third = (
            "No seed was skipped: every seed named code "
            "the graph holds.")
    if omitted:
        fourth = (
            f"{omitted} further connected piece(s) stood "
            f"beyond the node cap and are counted, not "
            f"dropped silently.")
    else:
        fourth = "Nothing stood beyond the node cap."
    return (
        first, second, third, fourth,
        "Ranking is deterministic: seed score first, "
        "halved at each hop, then distance, relation, "
        "path, symbol and line.")


@dataclass(frozen=True)
class RetrievalBundle:
    """One retrieval over the code graph, as a validated bundle.

    ``query`` is the words the retrieval answered;
    ``seeds`` are the hits it grew from, in held
    order; ``nodes`` are the connected pieces, in
    ranked order (score, distance, relation, path,
    symbol, line), each carrying its positional
    ``node-N`` id where ids stand; ``depth`` is how
    far the expansion walked; ``omitted`` counts the
    pieces that stood beyond the node cap;
    ``skipped`` names each seed the graph could not
    answer for, with its reason; ``account`` is read
    off those numbers - a stored account that
    disagrees with the derived one refuses at
    construction, as do pieces out of ranked order,
    two pieces with one identity, and a piece naming
    a seed the bundle does not hold.
    """

    query: str
    seeds: Tuple[RetrievalSeed, ...]
    nodes: Tuple[ConnectedNode, ...]
    depth: int = 1
    omitted: int = 0
    skipped: Tuple[str, ...] = ()
    account: Tuple[str, ...] = ()
    bundle_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.bundle_id is not None:
            object.__setattr__(
                self, "bundle_id",
                normalize_member_id(self.bundle_id))
        object.__setattr__(
            self, "query", _check_query(self.query))
        if isinstance(self.seeds, (str, bytes)) \
                or not isinstance(self.seeds, (list, tuple)):
            raise ValueError(
                f"a bundle's seeds must be a list of seeds, "
                f"got {self.seeds!r}")
        seeds = tuple(_check_seed_ref(s) for s in self.seeds)
        if not seeds:
            raise ValueError(
                "a retrieval bundle grows from at least one seed")
        seen_seed_ids = set()
        for seed in seeds:
            if seed.seed_id is not None:
                if seed.seed_id in seen_seed_ids:
                    raise ValueError(
                        f"a seed named {seed.seed_id!r} "
                        f"already exists in this bundle")
                seen_seed_ids.add(seed.seed_id)
        object.__setattr__(self, "seeds", seeds)
        depth = _check_count(self.depth, "a bundle's depth")
        if depth > MAX_RETRIEVAL_DEPTH:
            raise ValueError(
                f"a bundle's depth is at most "
                f"{MAX_RETRIEVAL_DEPTH}, got {depth}")
        object.__setattr__(self, "depth", depth)
        if isinstance(self.nodes, (str, bytes)) \
                or not isinstance(self.nodes, (list, tuple)):
            raise ValueError(
                f"a bundle's pieces must be a list of pieces, "
                f"got {self.nodes!r}")
        nodes = tuple(_check_node_ref(n) for n in self.nodes)
        seen_identities = set()
        for node in nodes:
            if node.identity in seen_identities:
                raise ValueError(
                    f"two pieces stand as one piece in this "
                    f"bundle: {node.path} "
                    f"{node.symbol or '-'} ({node.relation})")
            seen_identities.add(node.identity)
            if node.seed_id is not None \
                    and node.seed_id not in seen_seed_ids:
                raise ValueError(
                    f"a piece names seed {node.seed_id!r}, "
                    f"which this bundle does not hold")
            matched = [
                s for s in seeds
                if s.seed_id == node.seed_id]
            if matched and node.seed_score != matched[0].score:
                raise ValueError(
                    "a piece's seed score disagrees with "
                    "the score of the seed it names")
        keys = [node.sort_key for node in nodes]
        if keys != sorted(keys):
            raise ValueError(
                "a bundle's pieces must stand in ranked "
                "order (score, distance, relation, path, "
                "symbol, line)")
        idded = [node.node_id is not None for node in nodes]
        if any(idded):
            if not all(idded):
                raise ValueError(
                    "a bundle's pieces carry their ids "
                    "together or not at all")
            expected = tuple(
                f"node-{index}" for index in range(1, len(nodes) + 1))
            if tuple(node.node_id for node in nodes) != expected:
                raise ValueError(
                    "a bundle's piece ids are their ranked "
                    "positions: node-1, node-2, in order")
        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(
            self, "omitted",
            _check_count(self.omitted, "a bundle's omitted count"))
        skipped = _check_skipped(self.skipped)
        object.__setattr__(self, "skipped", skipped)
        if self.account:
            account = _check_account(self.account)
            derived = _retrieval_account(
                len(seeds), nodes, self.omitted, skipped)
            if account != derived:
                raise ValueError(
                    "a stored account disagrees with the "
                    "account derived from its bundle")
            object.__setattr__(self, "account", account)

    @property
    def total_nodes(self) -> int:
        """How many pieces stand in the bundle, derived."""
        return len(self.nodes)

    @property
    def total_seeds(self) -> int:
        """How many seeds the bundle grew from, derived."""
        return len(self.seeds)

    @property
    def file_count(self) -> int:
        """How many files the pieces span, derived."""
        return len({node.path for node in self.nodes})

    @property
    def relation_counts(self) -> Tuple[GraphRelationCount, ...]:
        """The per-relation tallies, derived."""
        return _relation_counts(self.nodes)

    def node_for(self, node_id: Any) -> ConnectedNode:
        """The piece one id names in this bundle."""
        wanted = normalize_member_id(node_id)
        for node in self.nodes:
            if node.node_id == wanted:
                return node
        raise KeyError(f"no piece in the bundle: {wanted!r}")

    def seed_ids(self) -> Tuple[str, ...]:
        """Every held seed id, in held order."""
        return tuple(s.seed_id for s in self.seeds if s.seed_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "graph_retrieval_bundle",
            "slice": GRAPH_RETRIEVAL_SLICE,
            "bundle_id": self.bundle_id,
            "query": self.query,
            "depth": self.depth,
            "seeds": [s.to_record() for s in self.seeds],
            "nodes": [n.to_record() for n in self.nodes],
            "total_nodes": self.total_nodes,
            "total_seeds": self.total_seeds,
            "file_count": self.file_count,
            "omitted": self.omitted,
            "skipped": list(self.skipped),
            "relation_counts": [
                c.to_record() for c in self.relation_counts],
            "account": list(self.account),
        }


def _bundle_totals(mapping: Dict[str, Any],
                   current: RetrievalBundle) -> None:
    named_nodes = _pick_any(
        mapping, ("total_nodes", "total"), "total pieces")
    if named_nodes is not None \
            and _check_count(named_nodes, "a total pieces count") \
            != current.total_nodes:
        raise ValueError(
            "a stored total pieces count disagrees with "
            "the bundle's own pieces")
    named_seeds = _pick_any(mapping, ("total_seeds",), "total seeds")
    if named_seeds is not None \
            and _check_count(named_seeds, "a total seeds count") \
            != current.total_seeds:
        raise ValueError(
            "a stored total seeds count disagrees with "
            "the bundle's own seeds")
    named_files = _pick_any(mapping, ("file_count",), "file counts")
    if named_files is not None \
            and _check_count(named_files, "a file count") \
            != current.file_count:
        raise ValueError(
            "a stored file count disagrees with the "
            "bundle's own pieces")
    named_relations = _pick_any(
        mapping, ("relation_counts", "relations"), "relation counts")
    if named_relations is not None:
        tallied = tuple(
            _check_relation_count_ref(c) for c in named_relations)
        if tallied != current.relation_counts:
            raise ValueError(
                "stored relation counts disagree with "
                "the bundle's own pieces")


def validate_bundle(bundle: Any, graph: Any = None,
                    seeds: Any = None) -> RetrievalBundle:
    """Validate one bundle into a RetrievalBundle.

    Accepts a bundle or a mapping naming a ``query``,
    a ``depth``, ``seeds``, ``nodes`` (or ``pieces``),
    an ``omitted`` count, ``skipped`` reasons, an
    ``account`` (or ``statements``) and an optional
    ``bundle_id`` (or ``id``). Named totals and
    relation counts are judged against the bundle's
    own pieces and refuse on disagreement; a mapping
    naming no account is held to the derived account
    (the account is filled in, derived, never stored
    loose). With *graph* given, the bundle is judged
    against the expansion that graph and *seeds*
    (the bundle's own seeds, by default) derive: a
    stored bundle whose pieces, skipped seeds or
    omitted count disagree with the derived
    expansion refuses.
    """
    if isinstance(bundle, RetrievalBundle):
        current = bundle
        mapping = None
    elif isinstance(bundle, dict):
        mapping = bundle
        unknown = set(bundle) - _BUNDLE_KEYS
        if unknown:
            raise ValueError(
                "unknown bundle keys: %s"
                % ", ".join(sorted(unknown)))
        query = _pick_any(bundle, ("query",), "queries")
        if query is None:
            raise ValueError("a retrieval bundle is missing its query")
        held_seeds = _pick_any(bundle, ("seeds",), "seeds")
        if held_seeds is None:
            raise ValueError("a retrieval bundle is missing its seeds")
        held_nodes = _pick_any(
            bundle, ("nodes", "pieces"), "pieces")
        if held_nodes is None:
            raise ValueError("a retrieval bundle is missing its pieces")
        kwargs: Dict[str, Any] = {
            "query": query, "seeds": held_seeds, "nodes": held_nodes}
        depth = _pick_any(bundle, ("depth",), "depths")
        if depth is not None:
            kwargs["depth"] = depth
        omitted = _pick_any(bundle, ("omitted",), "omitted counts")
        if omitted is not None:
            kwargs["omitted"] = omitted
        skipped = _pick_any(bundle, ("skipped",), "skipped seeds")
        if skipped is not None:
            kwargs["skipped"] = skipped
        account = _pick_any(
            bundle, ("account", "statements"), "accounts")
        if account is not None:
            kwargs["account"] = account
        bundle_id = _pick_any(bundle, ("bundle_id", "id"), "bundle ids")
        if bundle_id is not None:
            kwargs["bundle_id"] = bundle_id
        current = RetrievalBundle(**kwargs)
        _bundle_totals(bundle, current)
    else:
        raise ValueError(
            f"a retrieval bundle must be a mapping, got {bundle!r}")
    if not current.account:
        current = replace(
            current,
            account=_retrieval_account(
                current.total_seeds, current.nodes,
                current.omitted, current.skipped))
    if graph is not None:
        derived = expand_retrieval(
            graph, seeds if seeds is not None else current.seeds,
            query=current.query, depth=current.depth,
            bundle_id=current.bundle_id)
        if (current.nodes != derived.nodes
                or current.skipped != derived.skipped
                or current.omitted != derived.omitted):
            raise ValueError(
                "a stored bundle disagrees with the "
                "expansion derived from its graph and seeds")
    return current


def build_bundle(bundle: Any = None, **kwargs: Any) -> RetrievalBundle:
    """Build one validated bundle, from a mapping or field words."""
    if isinstance(bundle, RetrievalBundle) and not kwargs:
        return validate_bundle(bundle)
    if isinstance(bundle, dict) or bundle is None:
        merged: Dict[str, Any] = {}
        if isinstance(bundle, dict):
            merged.update(bundle)
        merged.update(kwargs)
        return validate_bundle(merged)
    raise ValueError(
        f"a retrieval bundle is needed, got {bundle!r}")


def _check_bundle_ref(value: Any) -> RetrievalBundle:
    if isinstance(value, RetrievalBundle):
        return validate_bundle(value)
    if isinstance(value, dict):
        return validate_bundle(value)
    raise ValueError(f"a retrieval bundle is needed, got {value!r}")


# ---------------------------------------------------------------------
# The panel: one bundle accounted for, derived at call time.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class RetrievalPanel:
    """The graph-retrieval panel, derived from one bundle.

    ``rows`` are the bundle's pieces carried whole,
    in ranked order; ``total_nodes`` and
    ``total_seeds`` are the bundle's own counts;
    ``file_count`` is the files the pieces span;
    ``relation_counts`` are the per-relation tallies
    in ``RELATIONS`` order; ``omitted`` and
    ``skipped`` are the bundle's own; ``account`` is
    read off those numbers. A panel whose rows stand
    out of ranked order, or whose totals are not its
    own rows' counts, refuses at construction;
    :func:`validate_panel` judged against a bundle
    refuses a stored panel that disagrees with the
    derived one.
    """

    rows: Tuple[ConnectedNode, ...] = ()
    total_nodes: int = 0
    total_seeds: int = 0
    file_count: int = 0
    relation_counts: Tuple[GraphRelationCount, ...] = ()
    omitted: int = 0
    skipped: Tuple[str, ...] = ()
    account: Tuple[str, ...] = ()
    panel_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id",
                normalize_member_id(self.panel_id))
        if isinstance(self.rows, (str, bytes)) \
                or not isinstance(self.rows, (list, tuple)):
            raise ValueError(
                f"a panel's rows must be a list of pieces, "
                f"got {self.rows!r}")
        rows = tuple(_check_node_ref(r) for r in self.rows)
        seen_identities = set()
        for row in rows:
            if row.identity in seen_identities:
                raise ValueError(
                    f"two panel rows stand as one piece: "
                    f"{row.path} {row.symbol or '-'} "
                    f"({row.relation})")
            seen_identities.add(row.identity)
        keys = [row.sort_key for row in rows]
        if keys != sorted(keys):
            raise ValueError(
                "a panel's rows must stand in ranked order")
        object.__setattr__(self, "rows", rows)
        object.__setattr__(
            self, "total_nodes",
            _check_count(self.total_nodes, "a panel's total pieces"))
        object.__setattr__(
            self, "total_seeds",
            _check_count(self.total_seeds, "a panel's total seeds"))
        object.__setattr__(
            self, "file_count",
            _check_count(self.file_count, "a panel's file count"))
        if self.total_nodes != len(rows):
            raise ValueError(
                "a panel's total pieces must be its own "
                "rows' count")
        if self.file_count != len({row.path for row in rows}):
            raise ValueError(
                "a panel's file count must be its own "
                "rows' files counted")
        if isinstance(self.relation_counts, (str, bytes)) \
                or not isinstance(self.relation_counts, (list, tuple)):
            raise ValueError(
                f"a panel's relation counts must be a list, "
                f"got {self.relation_counts!r}")
        relation_counts = tuple(
            _check_relation_count_ref(c)
            for c in self.relation_counts)
        if relation_counts != _relation_counts(rows):
            raise ValueError(
                "a panel's relation counts must be its "
                "own rows' tallies")
        object.__setattr__(self, "relation_counts", relation_counts)
        object.__setattr__(
            self, "omitted",
            _check_count(self.omitted, "a panel's omitted count"))
        skipped = _check_skipped(self.skipped)
        object.__setattr__(self, "skipped", skipped)
        if self.account:
            account = _check_account(self.account)
            derived = _retrieval_account(
                self.total_seeds, rows, self.omitted, skipped)
            if account != derived:
                raise ValueError(
                    "a stored account disagrees with the "
                    "account derived from its panel")
            object.__setattr__(self, "account", account)

    def row_for(self, node_id: Any) -> ConnectedNode:
        """The panel row one piece id names in this panel."""
        wanted = normalize_member_id(node_id)
        for row in self.rows:
            if row.node_id == wanted:
                return row
        raise KeyError(f"no row in the panel: piece {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "graph_retrieval_panel",
            "slice": GRAPH_RETRIEVAL_SLICE,
            "panel_id": self.panel_id,
            "rows": [row.to_record() for row in self.rows],
            "total_nodes": self.total_nodes,
            "total_seeds": self.total_seeds,
            "file_count": self.file_count,
            "relation_counts": [
                c.to_record() for c in self.relation_counts],
            "omitted": self.omitted,
            "skipped": list(self.skipped),
            "account": list(self.account),
        }


def derive_panel(source: Any) -> RetrievalPanel:
    """Derive the panel from one bundle.

    The rows are the bundle's pieces carried whole,
    in the bundle's ranked order, and the tallies are
    read off the rows. *source* is a bundle or a
    registry (whose latest bundle answers). A source
    holding no bundle refuses - a panel of nothing
    is no panel.
    """
    if isinstance(source, GraphRetrievalRegistry):
        bundle = source.latest_bundle()
    else:
        bundle = _check_bundle_ref(source)
    rows = bundle.nodes
    return RetrievalPanel(
        rows=rows,
        total_nodes=bundle.total_nodes,
        total_seeds=bundle.total_seeds,
        file_count=bundle.file_count,
        relation_counts=bundle.relation_counts,
        omitted=bundle.omitted,
        skipped=bundle.skipped,
        account=_retrieval_account(
            bundle.total_seeds, rows,
            bundle.omitted, bundle.skipped))


def validate_panel(panel: Any, source: Any = None) -> RetrievalPanel:
    """Validate one panel into a RetrievalPanel.

    Accepts a panel or a mapping naming ``rows`` (or
    ``nodes`` / ``pieces``), a ``total_nodes`` (or
    ``total``), a ``total_seeds``, a ``file_count``,
    ``relation_counts`` (or ``relations``), an
    ``omitted`` count, ``skipped`` reasons, an
    ``account`` (or ``statements``) and an optional
    ``panel_id`` (or ``id``). A mapping naming no
    account is held to the derived account. With
    *source* given (a bundle), the panel is judged
    against the panel derived from that bundle: a
    stored panel whose rows, totals, counts or
    account disagree with the derived panel refuses.
    """
    if isinstance(panel, RetrievalPanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS
        if unknown:
            raise ValueError(
                "unknown panel keys: %s"
                % ", ".join(sorted(unknown)))
        rows = _pick_any(
            panel, ("rows", "nodes", "pieces"), "rows")
        if rows is None:
            raise ValueError("a panel is missing its rows")
        total = _pick_any(
            panel, ("total_nodes", "total"), "total pieces")
        if total is None:
            raise ValueError("a panel is missing its total pieces")
        total_seeds = _pick_any(panel, ("total_seeds",), "total seeds")
        if total_seeds is None:
            raise ValueError("a panel is missing its total seeds")
        file_count = _pick_any(panel, ("file_count",), "file counts")
        if file_count is None:
            raise ValueError("a panel is missing its file count")
        relation_counts = _pick_any(
            panel, ("relation_counts", "relations"), "relation counts")
        if relation_counts is None:
            raise ValueError("a panel is missing its relation counts")
        kwargs: Dict[str, Any] = {
            "rows": rows, "total_nodes": total,
            "total_seeds": total_seeds, "file_count": file_count,
            "relation_counts": relation_counts}
        omitted = _pick_any(panel, ("omitted",), "omitted counts")
        if omitted is not None:
            kwargs["omitted"] = omitted
        skipped = _pick_any(panel, ("skipped",), "skipped seeds")
        if skipped is not None:
            kwargs["skipped"] = skipped
        account = _pick_any(
            panel, ("account", "statements"), "accounts")
        if account is not None:
            kwargs["account"] = account
        panel_id = _pick_any(panel, ("panel_id", "id"), "panel ids")
        if panel_id is not None:
            kwargs["panel_id"] = panel_id
        current = RetrievalPanel(**kwargs)
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if not current.account:
        current = replace(
            current,
            account=_retrieval_account(
                current.total_seeds, current.rows,
                current.omitted, current.skipped))
    if source is not None:
        derived = derive_panel(source)
        if (current.rows != derived.rows
                or current.total_nodes != derived.total_nodes
                or current.total_seeds != derived.total_seeds
                or current.file_count != derived.file_count
                or current.relation_counts != derived.relation_counts
                or current.omitted != derived.omitted
                or current.skipped != derived.skipped
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagrees with the panel "
                "derived from its bundle")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> RetrievalPanel:
    """Build one validated panel, from a mapping or field words."""
    if isinstance(panel, RetrievalPanel) and not kwargs:
        return validate_panel(panel, source)
    if isinstance(panel, dict) or panel is None:
        merged: Dict[str, Any] = {}
        if isinstance(panel, dict):
            merged.update(panel)
        merged.update(kwargs)
        return validate_panel(merged, source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The expansion: the graph walked from each seed, through the
# graph's own query roads - connected code, with provenance.
# ---------------------------------------------------------------------


def _graph_paths(graph: SymbolGraph) -> set:
    paths = set(graph.file_edges())
    paths.update(d.path for d in graph.definitions)
    paths.update(r.path for r in graph.references)
    paths.update(i.path for i in graph.imports)
    paths.update(c.path for c in graph.calls)
    return paths


def _kind_of(graph: SymbolGraph, path: str,
             name: Optional[str]) -> str:
    """The definition kind of one name in one file, honestly."""
    if name is None:
        return "file"
    if name == MODULE_CALLER:
        return "module"
    for definition in graph.definitions_in(path):
        if definition.name.lower() == name.lower():
            return definition.kind
    for definition in graph.definitions_named(name):
        return definition.kind
    return "unresolved"


def _offer(best: Dict[Tuple[str, Optional[str], str], ConnectedNode],
           node: ConnectedNode) -> None:
    """Offer one candidate piece to the expansion.

    One identity stands once in a bundle: the offer
    standing in ranked order first (nearest, then
    best-scored, then by relation, path, symbol and
    line, with the seed id breaking a last tie) is
    the one kept - deterministic on every machine.
    """
    current = best.get(node.identity)
    if current is None:
        best[node.identity] = node
        return
    challenger = (node.sort_key, node.seed_id or "")
    holder = (current.sort_key, current.seed_id or "")
    if challenger < holder:
        best[node.identity] = node


def _expand_anchor(graph: SymbolGraph, name: str,
                   seed: RetrievalSeed, distance: int,
                   best: Dict[Tuple[str, Optional[str], str],
                              ConnectedNode]) -> None:
    """Grow caller, callee and reference pieces for one name."""
    for edge in graph.callers_of(name):
        _offer(best, ConnectedNode(
            path=edge.path, relation="caller", distance=distance,
            seed_score=seed.score,
            provenance=(
                f"calls {name} at {edge.path}:{edge.line}, "
                f"one hop from the seed" if distance == 1 else
                f"calls {name} at {edge.path}:{edge.line}, "
                f"{distance} hops from the seed"),
            symbol=edge.caller,
            kind=_kind_of(graph, edge.path, edge.caller),
            seed_id=seed.seed_id, line=edge.line))
    for edge in graph.callees_of(name):
        target_path = edge.path
        target_kind = "unresolved"
        if edge.resolved_to:
            by_id = {d.id: d for d in graph.definitions}
            owner = by_id.get(edge.resolved_to[0])
            if owner is not None:
                target_path = owner.path
                target_kind = owner.kind
        _offer(best, ConnectedNode(
            path=target_path, relation="callee", distance=distance,
            seed_score=seed.score,
            provenance=(
                f"called by {name} at {edge.path}:{edge.line}"),
            symbol=edge.callee, kind=target_kind,
            seed_id=seed.seed_id, line=edge.line))
    for site in graph.references_to(name):
        _offer(best, ConnectedNode(
            path=site.path, relation="reference", distance=distance,
            seed_score=seed.score,
            provenance=(
                f"references {name} at "
                f"{site.path}:{site.line}"),
            symbol=site.enclosing,
            kind=_kind_of(graph, site.path, site.enclosing),
            seed_id=seed.seed_id, line=site.line))


def _expand_file(graph: SymbolGraph, path: str,
                 seed: RetrievalSeed, distance: int,
                 best: Dict[Tuple[str, Optional[str], str],
                            ConnectedNode],
                 skipped: list) -> None:
    """Grow definition, import and neighbour pieces for one file."""
    anchor_names = set()
    if seed.symbol is not None:
        anchor_names.add(seed.symbol.lower())
    for definition in graph.definitions_in(path):
        if definition.name.lower() in anchor_names:
            continue
        _offer(best, ConnectedNode(
            path=path, relation="definition", distance=distance,
            seed_score=seed.score,
            provenance=(
                f"defined in the seed's file, {path}"),
            symbol=definition.name, kind=definition.kind,
            seed_id=seed.seed_id, line=definition.line))
    imported = set()
    for edge in graph.imports_of(path):
        if edge.resolved_path:
            imported.add(edge.resolved_path)
            _offer(best, ConnectedNode(
                path=edge.resolved_path, relation="import",
                distance=distance, seed_score=seed.score,
                provenance=(
                    f"imported by the seed's file as "
                    f"{edge.module} (line {edge.line})"),
                seed_id=seed.seed_id))
        else:
            skipped.append(
                f"import {edge.module} in {path} resolves "
                f"to no workspace file")
    edges = graph.file_edges()
    for source_path in sorted(edges):
        if path in edges[source_path] and source_path != path:
            _offer(best, ConnectedNode(
                path=source_path, relation="imported-by",
                distance=distance, seed_score=seed.score,
                provenance=(
                    f"imports or calls into the seed's "
                    f"file, {path}"),
                seed_id=seed.seed_id))
    for target in edges.get(path, ()):
        if target in imported:
            continue
        _offer(best, ConnectedNode(
            path=target, relation="file-neighbour",
            distance=distance, seed_score=seed.score,
            provenance=(
                f"the seed's file references or calls "
                f"into {target}"),
            seed_id=seed.seed_id))


def expand_retrieval(graph: Any, seeds: Any, *, query: Any = "",
                     depth: int = 1, max_nodes: int = 64,
                     bundle_id: Any = None) -> RetrievalBundle:
    """Expand seeds over the code graph into one bundle.

    *graph* is the shipped symbol graph
    (``context/symbol_graph.py``), read through its
    own query roads - never re-parsed here. Each seed
    grows, at distance 1, the definitions beside it
    in its file, its anchors' callers, callees and
    reference sites, the files its file imports, the
    files that import its file, and its file's other
    graph neighbours; at depth 2 the symbols met at
    distance 1 grow their own callers, callees and
    references one hop further. A seed naming a file
    the graph does not hold, or a symbol its file
    does not define, grows nothing and stands in the
    bundle's ``skipped`` with its reason. Pieces are
    ranked deterministically and capped at
    *max_nodes*, the rest counted in ``omitted``.
    An expansion with no seeds at all refuses.
    """
    if not isinstance(graph, SymbolGraph):
        raise ValueError(
            f"a symbol graph is needed, got {graph!r}")
    if isinstance(seeds, (str, bytes)) \
            or not isinstance(seeds, (list, tuple)):
        raise ValueError(
            f"retrieval seeds must be a list of seeds, "
            f"got {seeds!r}")
    held = []
    for index, raw in enumerate(seeds, start=1):
        seed = _check_seed_ref(raw)
        if seed.seed_id is None:
            seed = replace(seed, seed_id=f"seed-{index}")
        held.append(seed)
    if not held:
        raise ValueError(
            "a retrieval grows from at least one seed - "
            "with no seed there is nothing to connect")
    depth = _check_count(depth, "a retrieval depth")
    if depth > MAX_RETRIEVAL_DEPTH:
        raise ValueError(
            f"a retrieval depth is at most "
            f"{MAX_RETRIEVAL_DEPTH}, got {depth}")
    max_nodes = _check_count(max_nodes, "a retrieval node cap")
    if max_nodes < 1:
        raise ValueError("a retrieval node cap must be at least 1")
    if bundle_id is not None:
        bundle_id = normalize_member_id(bundle_id)
    query_text = ""
    if isinstance(query, str) and query.strip():
        query_text = _check_query(query)
    if not query_text:
        query_text = (
            f"graph retrieval from {len(held)} named seed(s)")
    paths = _graph_paths(graph)
    best: Dict[Tuple[str, Optional[str], str], ConnectedNode] = {}
    skipped: list = []
    for seed in held:
        if seed.path not in paths:
            skipped.append(
                f"seed {seed.seed_id} names {seed.path}, "
                f"which the graph does not hold")
            continue
        anchors = [
            d for d in graph.definitions_in(seed.path)
            if seed.symbol is None
            or d.name.lower() == seed.symbol.lower()]
        if seed.symbol is not None and not anchors:
            elsewhere = graph.definitions_named(seed.symbol)
            if elsewhere:
                skipped.append(
                    f"seed {seed.seed_id} names "
                    f"{seed.symbol} in {seed.path}, but the "
                    f"graph defines it at "
                    f"{elsewhere[0].path} - not relocated")
            else:
                skipped.append(
                    f"seed {seed.seed_id} names "
                    f"{seed.symbol}, which the graph "
                    f"does not define")
            continue
        if seed.symbol is not None:
            anchor = anchors[0]
            _offer(best, ConnectedNode(
                path=seed.path, relation="seed", distance=0,
                seed_score=seed.score,
                provenance=(
                    f"the seed itself: a {seed.source} hit "
                    f"scoring {seed.score}"),
                symbol=seed.symbol, kind=anchor.kind,
                seed_id=seed.seed_id, line=anchor.line))
        else:
            _offer(best, ConnectedNode(
                path=seed.path, relation="seed", distance=0,
                seed_score=seed.score,
                provenance=(
                    f"the seed itself: a {seed.source} hit "
                    f"scoring {seed.score}"),
                seed_id=seed.seed_id))
        if depth >= 1:
            for anchor in anchors:
                _expand_anchor(
                    graph, anchor.name, seed, 1, best)
            _expand_file(graph, seed.path, seed, 1, best, skipped)
        if depth >= 2:
            frontier = sorted(
                (node for node in best.values()
                 if node.distance == 1 and node.symbol
                 and node.seed_id == seed.seed_id
                 and node.relation in (
                     "definition", "caller", "callee")),
                key=lambda node: node.sort_key)
            grown = set()
            for node in frontier:
                key = (seed.seed_id, node.symbol.lower())
                if key in grown:
                    continue
                grown.add(key)
                _expand_anchor(
                    graph, node.symbol, seed, 2, best)
    ranked = sorted(best.values(), key=lambda node: node.sort_key)
    omitted = 0
    if len(ranked) > max_nodes:
        omitted = len(ranked) - max_nodes
        ranked = ranked[:max_nodes]
    numbered = tuple(
        replace(node, node_id=f"node-{index}")
        for index, node in enumerate(ranked, start=1))
    skipped_tuple = tuple(dict.fromkeys(skipped))
    return RetrievalBundle(
        query=query_text, seeds=tuple(held), nodes=numbered,
        depth=depth, omitted=omitted, skipped=skipped_tuple,
        account=_retrieval_account(
            len(held), numbered, omitted, skipped_tuple),
        bundle_id=bundle_id)


# ---------------------------------------------------------------------
# Seed roads: the shipped searches, married to the graph -
# semantic scoring by import, vector results in their shipped
# shape, and a query's own symbol mentions read off the graph.
# ---------------------------------------------------------------------


def seeds_from_semantic(query: Any, docs: Any, *,
                        top_n: int = 5) -> Tuple[RetrievalSeed, ...]:
    """Build seeds from the shipped semantic scoring.

    *docs* are the semantic road's own corpus
    documents (``context/semantic.py``), scored
    against *query* by that road's ``score_corpus``
    BY IMPORT - the same tf-idf figures the context
    compiler's semantic source ranks by, never a
    second scoring model. The best *top_n* scoring
    files become ``semantic`` seeds carrying their
    scores whole. A query or corpus that scores
    nothing yields no seeds, honestly.
    """
    top_n = _check_count(top_n, "a seed count")
    if top_n < 1:
        raise ValueError("a seed count must be at least 1")
    ranked = score_corpus(_check_query(query), list(docs))
    seeds = []
    for doc, score in ranked[:top_n]:
        seeds.append(RetrievalSeed(
            path=doc.doc_id, score=float(score),
            source="semantic",
            seed_id=f"seed-{len(seeds) + 1}"))
    return tuple(seeds)


def seeds_from_vector_results(results: Any, *,
                              top_n: int = 5
                              ) -> Tuple[RetrievalSeed, ...]:
    """Build seeds from vector-provider search results.

    *results* are result mappings in the shipped
    vector providers' own shape
    (``memory/vector_db.py``): a ``score``, a
    ``text``, and ``metadata``. The metadata must
    name the hit's file - ``path`` (or ``doc_id`` /
    ``file``) - and may name its ``symbol`` (or
    ``name``); a vector hit naming no file cannot be
    married to the graph and refuses, rather than
    standing as confetti with a guessed home. The
    best *top_n* become ``vector`` seeds carrying
    their scores whole.
    """
    top_n = _check_count(top_n, "a seed count")
    if top_n < 1:
        raise ValueError("a seed count must be at least 1")
    if isinstance(results, (str, bytes)) \
            or not isinstance(results, (list, tuple)):
        raise ValueError(
            f"vector results must be a list, got {results!r}")
    seeds = []
    for result in results:
        if not isinstance(result, dict):
            raise ValueError(
                f"a vector result must be a mapping, "
                f"got {result!r}")
        metadata = result.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise ValueError(
                f"a vector result's metadata must be a "
                f"mapping, got {metadata!r}")
        path = None
        for key in ("path", "doc_id", "file"):
            if metadata.get(key):
                path = metadata[key]
                break
        if path is None and result.get("path"):
            path = result["path"]
        if path is None:
            raise ValueError(
                "a vector result names no file in its "
                "metadata - it cannot be married to the "
                "graph, and refuses rather than guessing")
        score = result.get("score")
        if score is None:
            raise ValueError(
                "a vector result names no score - its "
                "rank cannot be carried, and it refuses")
        symbol = metadata.get("symbol") or metadata.get("name")
        kwargs: Dict[str, Any] = {
            "path": path, "score": score, "source": "vector",
            "seed_id": f"seed-{len(seeds) + 1}"}
        if symbol:
            kwargs["symbol"] = symbol
        seeds.append(RetrievalSeed(**kwargs))
    seeds.sort(key=lambda seed: (-seed.score, seed.path,
                                 seed.symbol or ""))
    return tuple(seeds[:top_n])


def seeds_from_query(graph: Any, query: Any, *,
                     top_n: int = 5) -> Tuple[RetrievalSeed, ...]:
    """Build seeds from a query's own symbol mentions.

    The query's words are the semantic road's own
    tokens (``tokenize`` BY IMPORT); a definition
    whose name - or whose name's own underscore
    parts - the query names becomes a ``symbol``
    seed, scored by how many of its name's parts the
    query names. One seed stands per definition
    site: a name defined twice seeds both sites,
    ambiguity carried, never silently picked. A
    query naming no defined symbol yields no seeds,
    honestly.
    """
    if not isinstance(graph, SymbolGraph):
        raise ValueError(
            f"a symbol graph is needed, got {graph!r}")
    top_n = _check_count(top_n, "a seed count")
    if top_n < 1:
        raise ValueError("a seed count must be at least 1")
    tokens = set(tokenize(_check_query(query)))
    if not tokens:
        return ()
    found = []
    for definition in graph.definitions:
        parts = {
            part for part in definition.name.lower().split("_")
            if part}
        matched = len(parts & tokens)
        if definition.name.lower() in tokens:
            matched = max(matched, len(parts), 1)
        if matched:
            found.append((definition, float(matched)))
    found.sort(key=lambda pair: (
        -pair[1], pair[0].path, pair[0].name, pair[0].line))
    seeds = []
    for definition, score in found[:top_n]:
        seeds.append(RetrievalSeed(
            path=definition.path, score=score, source="symbol",
            symbol=definition.name,
            seed_id=f"seed-{len(seeds) + 1}"))
    return tuple(seeds)


def retrieve(graph: Any, query: Any, *, docs: Any = None,
             depth: int = 1, top_seeds: int = 5,
             max_nodes: int = 64,
             bundle_id: Any = None) -> RetrievalBundle:
    """Retrieve over the graph for one query, in one road.

    Seeds are married from both shipped roads: the
    query's own symbol mentions read off the graph,
    and - with *docs* given, the semantic road's
    corpus documents - that road's tf-idf scores.
    Seeds naming one site merge, keeping the better
    score. With no seed from either road, the
    retrieval refuses honestly: the graph holds
    nothing this query names, and returning the
    whole repo would be confetti, not retrieval.
    """
    query_text = _check_query(query)
    merged: Dict[Tuple[str, Optional[str]], RetrievalSeed] = {}
    candidates = list(seeds_from_query(graph, query_text,
                                       top_n=top_seeds))
    if docs is not None:
        candidates.extend(seeds_from_semantic(
            query_text, docs, top_n=top_seeds))
    for seed in candidates:
        key = (seed.path, seed.symbol)
        current = merged.get(key)
        if current is None or seed.score > current.score:
            merged[key] = seed
    if not merged:
        raise ValueError(
            "no seed names code this query can grow: the "
            "query mentions no defined symbol and the "
            "semantic road scored no file - retrieval "
            "returns nothing rather than confetti")
    seeds = sorted(
        merged.values(),
        key=lambda seed: (-seed.score, seed.path,
                          seed.symbol or ""))
    renumbered = tuple(
        replace(seed, seed_id=f"seed-{index}")
        for index, seed in enumerate(seeds, start=1))
    return expand_retrieval(
        graph, renumbered, query=query_text, depth=depth,
        max_nodes=max_nodes, bundle_id=bundle_id)


# ---------------------------------------------------------------------
# The book: bundles in held order, panels judged - the book
# file's shape, of which the shipped example is one.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class RetrievalBook:
    """One graph-retrieval book: its bundles, in held order.

    ``bundles`` are the retrieval bundles, in held
    order; ``panels`` are the book's derivations -
    panels of the book's bundles, judged against the
    bundles they derive from by :func:`validate_book`;
    ``canon_note`` is the book's own note. This book
    is the book file's shape: the shipped example is
    one book, and a real book file is a new file in
    this shape.
    """

    title: str = ""
    bundles: Tuple[RetrievalBundle, ...] = ()
    panels: Tuple[RetrievalPanel, ...] = ()
    canon_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book's title"))
        if isinstance(self.bundles, (str, bytes)) \
                or not isinstance(self.bundles, (list, tuple)):
            raise ValueError(
                f"a book's bundles must be a list of "
                f"retrieval bundles, got {self.bundles!r}")
        bundles = tuple(_check_bundle_ref(b) for b in self.bundles)
        if not bundles:
            raise ValueError(
                "a graph-retrieval book holds at least one bundle")
        seen_ids = set()
        for bundle in bundles:
            if bundle.bundle_id is not None:
                if bundle.bundle_id in seen_ids:
                    raise ValueError(
                        f"a bundle named {bundle.bundle_id!r} "
                        f"already exists")
                seen_ids.add(bundle.bundle_id)
        object.__setattr__(self, "bundles", bundles)
        if isinstance(self.panels, (str, bytes)) \
                or not isinstance(self.panels, (list, tuple)):
            raise ValueError(
                f"a book's panels must be a list of panels, "
                f"got {self.panels!r}")
        panels = tuple(
            p if isinstance(p, RetrievalPanel) else validate_panel(p)
            for p in self.panels)
        seen_panels = set()
        for panel in panels:
            if panel.panel_id is not None:
                if panel.panel_id in seen_panels:
                    raise ValueError(
                        f"a panel named {panel.panel_id!r} "
                        f"already exists")
                seen_panels.add(panel.panel_id)
        object.__setattr__(self, "panels", panels)
        if not isinstance(self.canon_note, str):
            raise ValueError("a book's note must be text")
        object.__setattr__(
            self, "canon_note", self.canon_note.strip())

    def bundle_for(self, bundle_id: Any) -> RetrievalBundle:
        """The bundle one id names in this book."""
        wanted = normalize_member_id(bundle_id)
        for bundle in self.bundles:
            if bundle.bundle_id == wanted:
                return bundle
        raise KeyError(f"no bundle in the book: {wanted!r}")

    def panel_for(self, panel_id: Any) -> RetrievalPanel:
        """The stored panel one id names in this book."""
        wanted = normalize_member_id(panel_id)
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel in the book: {wanted!r}")

    def bundle_ids(self) -> Tuple[str, ...]:
        """Every held bundle id, in held order."""
        return tuple(b.bundle_id for b in self.bundles if b.bundle_id)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "graph_retrieval_book",
            "slice": GRAPH_RETRIEVAL_SLICE,
            "title": self.title,
            "bundle_ids": list(self.bundle_ids()),
            "bundle_count": len(self.bundles),
            "panel_count": len(self.panels),
        }


def validate_book(data: Any, *, require_example: bool = False
                  ) -> RetrievalBook:
    """Validate one graph-retrieval mapping into a book.

    The mapping names a ``schema`` (the
    graph-retrieval schema word), a ``guide`` mapping
    (its ``title``), a ``bundles`` list and an
    optional ``panels`` list. Every bundle stands on
    its own validation, then the whole is judged:
    bundle ids unique, and every stored panel judged
    against a bundle of the book it derives from.
    With ``require_example`` the shipped example is
    held to its pinned shape: the pinned title,
    bundle, query and panel rows. Problems raise
    :class:`ValidationError` or ``ValueError``.
    """
    if isinstance(data, RetrievalBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"a graph-retrieval book must be a mapping, got {data!r}")
    unknown = set(data) - _GRAPH_RETRIEVAL_KEYS
    if unknown:
        raise ValidationError(
            "unknown graph-retrieval keys: %s"
            % ", ".join(sorted(unknown)))
    if data.get("schema") != GRAPH_RETRIEVAL_SCHEMA:
        raise ValidationError(
            f"a graph-retrieval book must carry schema "
            f"{GRAPH_RETRIEVAL_SCHEMA!r}, got {data.get('schema')!r}")
    bundles = _pick_any(data, ("bundles",), "bundles")
    if bundles is None:
        raise ValidationError(
            "a graph-retrieval book is missing its bundles")
    if not isinstance(bundles, (list, tuple)):
        raise ValidationError(
            "a graph-retrieval book's bundles must be a list")
    if data.get("panels") is not None \
            and not isinstance(data["panels"], (list, tuple)):
        raise ValidationError(
            "a graph-retrieval book's panels must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError(
            "a graph-retrieval book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError(
                "a graph-retrieval book is missing its title")
        note = data.get("canon_note") or ""
        if not isinstance(note, str):
            raise ValidationError(
                "a graph-retrieval book's note must be text")
        book = RetrievalBook(
            title=title, bundles=tuple(bundles),
            panels=tuple(data.get("panels") or ()),
            canon_note=note)
        for panel in book.panels:
            judged = False
            for bundle in book.bundles:
                try:
                    validate_panel(panel, bundle)
                    judged = True
                    break
                except ValueError:
                    continue
            if not judged:
                raise ValidationError(
                    "a stored panel derives from no bundle "
                    "of its book")
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example graph-retrieval book's "
                "title is not the pinned title")
        if book.bundle_ids() != _EXAMPLE_BUNDLE_IDS:
            raise ValidationError(
                "the shipped example's bundles are not "
                "the pinned bundles")
        bundle = book.bundles[0]
        if bundle.query != _EXAMPLE_QUERY:
            raise ValidationError(
                "the shipped example bundle's query is "
                "not the pinned query")
        if bundle.total_seeds != 1 or bundle.total_nodes != 6:
            raise ValidationError(
                "the shipped example bundle does not hold "
                "its pinned seed and piece counts")
        panel = book.panel_for(_EXAMPLE_PANEL_ID)
        if tuple(r.node_id for r in panel.rows) \
                != _EXAMPLE_PANEL_ROW_IDS:
            raise ValidationError(
                "the shipped example panel does not name "
                "its pinned rows in ranked order")
    return book


def build_book(book: Any = None, **kwargs: Any) -> RetrievalBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, RetrievalBook) and not kwargs:
        return book
    if isinstance(book, dict):
        if "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return RetrievalBook(**merged)
    if book is None:
        return RetrievalBook(**kwargs)
    raise ValueError(f"a graph-retrieval book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> RetrievalBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_graph_retrieval(
        data: Optional[Dict[str, Any]] = None) -> RetrievalBook:
    """Load and validate the shipped example book (or *data*).

    The shipped file is held to the example check:
    the pinned title, bundle and panel - the M-151
    slice boundary book - so the shipped book covers
    the canon this slice exists to hold.
    """
    raw = data if data is not None else load_resource(
        GRAPH_RETRIEVAL_RESOURCE)
    return _book_from(raw, require_example=True)


def load_graph_retrieval_file(path: Any) -> RetrievalBook:
    """Load and validate a graph-retrieval book from a file at *path*.

    Any file in the graph-retrieval shape, anywhere
    on disk, validated whole - a malformed file
    raises :class:`ValidationError` naming the
    problem, and a missing file raises
    ``FileNotFoundError``. The example check is not
    held: a real book stands on its own bundles.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: bundles held one by one, in held order;
# the panel is a derivation, never a holding.
# ---------------------------------------------------------------------


class GraphRetrievalRegistry:
    """One session's graph retrievals, held bundle by bundle.

    The registry holds bundles, never panels: the
    panel is a derivation, read off the latest held
    bundle at call time, so nothing here can hold a
    figure stale.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._bundles: Dict[str, RetrievalBundle] = {}
        self._order: list = []
        self._next_bundle = 1
        if book is not None:
            self.register_book(book)

    def _fresh_bundle_id(self, held_ids: Any) -> str:
        while f"retrieval-{self._next_bundle}" in held_ids:
            self._next_bundle += 1
        fresh = f"retrieval-{self._next_bundle}"
        self._next_bundle += 1
        return fresh

    def register_bundle(self, bundle: Any) -> RetrievalBundle:
        """Register one bundle into the held book.

        A bundle with no id is given a deterministic
        ``retrieval-N`` id. A bundle id already
        standing here refuses.
        """
        validated = _check_bundle_ref(bundle)
        held_ids = set(self._bundles)
        if validated.bundle_id is not None \
                and validated.bundle_id in held_ids:
            raise ValueError(
                f"a bundle named "
                f"{validated.bundle_id!r} already exists")
        if validated.bundle_id is None:
            validated = replace(
                validated,
                bundle_id=self._fresh_bundle_id(held_ids))
        self._bundles[validated.bundle_id] = validated
        self._order.append(validated.bundle_id)
        return validated

    def register_book(self, book: Any) -> RetrievalBook:
        """Register every bundle of one book, in order.

        The first book held sets the title; a later
        book under a different title refuses, as does
        a book naming a held bundle id. The book's
        panels are derivations, not holdings, and are
        not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a "
                "graph-retrieval book under a different title")
        for bundle in validated.bundles:
            if bundle.bundle_id in self._bundles:
                raise ValueError(
                    f"a bundle named "
                    f"{bundle.bundle_id!r} already exists")
        self._title = validated.title
        for bundle in validated.bundles:
            self.register_bundle(bundle)
        return self.book()

    def get_bundle(self, bundle_id: Any) -> RetrievalBundle:
        """The bundle one id names among the held bundles."""
        wanted = normalize_member_id(bundle_id)
        if wanted not in self._bundles:
            raise KeyError(f"unknown retrieval bundle: {wanted!r}")
        return self._bundles[wanted]

    def latest_bundle(self) -> RetrievalBundle:
        """The most recently held bundle."""
        if not self._order:
            raise ValueError("no retrieval bundle is held yet")
        return self._bundles[self._order[-1]]

    def list_bundles(self) -> Tuple[RetrievalBundle, ...]:
        """Every held bundle, in the order they were held."""
        return tuple(self._bundles[b] for b in self._order)

    def book(self) -> RetrievalBook:
        """The held bundles as one validated book."""
        if self._title is None:
            raise ValueError("no graph-retrieval book is held yet")
        return RetrievalBook(
            title=self._title, bundles=self.list_bundles())

    def panel(self) -> RetrievalPanel:
        """Derive the panel of the latest held bundle."""
        return derive_panel(self)


# ---------------------------------------------------------------------
# Retrieval news, shaped as session records.
# ---------------------------------------------------------------------


def node_record(node: Any) -> Dict[str, Any]:
    """The session-news record of one connected piece."""
    current = node if isinstance(node, ConnectedNode) \
        else build_node(node)
    news = current.to_record()
    news["news"] = True
    news["headline"] = (
        f"{current.path} {current.symbol or '(file)'} "
        f"stands {current.relation} to its seed, "
        f"{current.distance} hop(s) away: "
        f"{current.provenance}")
    return news


def bundle_record(bundle: Any) -> Dict[str, Any]:
    """The session-news record of one retrieval bundle."""
    current = bundle if isinstance(bundle, RetrievalBundle) \
        else build_bundle(bundle)
    news = current.to_record()
    news["news"] = True
    news["headline"] = (
        f"Graph retrieval for {current.query!r}: "
        f"{current.total_nodes} connected pieces from "
        f"{current.total_seeds} seed(s) across "
        f"{current.file_count} file(s).")
    return news


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel.

    With *source* given, the panel is first judged
    against the panel that source derives.
    """
    current = validate_panel(panel, source)
    news = current.to_record()
    news["news"] = True
    news["headline"] = (
        f"Graph retrieval panel: {current.total_nodes} "
        f"connected pieces in ranked order from "
        f"{current.total_seeds} seed(s).")
    return news


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one graph-retrieval book."""
    current = book if isinstance(book, RetrievalBook) \
        else build_book(book)
    news = current.to_record()
    news["news"] = True
    news["headline"] = (
        f"Graph retrieval {current.title}: "
        f"{news['bundle_count']} bundles named.")
    return news


def plain_words(node: Any) -> str:
    """One piece, in one plain sentence."""
    current = node if isinstance(node, ConnectedNode) \
        else build_node(node)
    return (
        f"{current.path} {current.symbol or '(file)'} - "
        f"{current.relation}, {current.distance} hop(s) "
        f"from its seed at score {current.score}: "
        f"{current.provenance}")


def panel_plain_words(source: Any) -> str:
    """The panel in plain words, in full.

    Accepts a RetrievalPanel or a RetrievalBook
    (whose latest bundle's panel is told). The panel
    is told whole - its rows in ranked order and its
    account.
    """
    if isinstance(source, RetrievalPanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, RetrievalBook):
        panel = derive_panel(source.bundles[-1])
        title = source.title
    else:
        raise ValueError(
            f"a graph-retrieval source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Connected pieces, in ranked order:")
    for row in panel.rows:
        lines.append(
            f"{row.node_id or '-'}: {row.path} "
            f"{row.symbol or '(file)'} - {row.relation} "
            f"at score {row.score}")
    lines.extend(panel.account)
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /graphsearch grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> RetrievalBook:
    if source is None:
        return load_graph_retrieval()
    if isinstance(source, GraphRetrievalRegistry):
        return source.book()
    if isinstance(source, RetrievalBook):
        return source
    if isinstance(source, RetrievalBundle):
        return RetrievalBook(
            title="One graph retrieval", bundles=(source,))
    raise ValueError(
        f"a graph-retrieval book is needed, got {source!r}")


def format_node(node: Any) -> str:
    """One piece as a screen line."""
    current = node if isinstance(node, ConnectedNode) \
        else build_node(node)
    return (
        f"{current.node_id or '-'}: {current.path} "
        f"{current.symbol or '(file)'} ({current.kind}) - "
        f"{current.relation}, distance "
        f"{current.distance}, score {current.score}: "
        f"{current.provenance}")


def format_nodes(source: Any = None) -> str:
    """Pieces of one bundle, in ranked order.

    With nothing named, the shipped example book's
    first bundle is shown.
    """
    book = _source_book(source)
    bundle = book.bundles[-1]
    lines = [format_node(node) for node in bundle.nodes]
    if not lines:
        lines.append("No connected pieces are held.")
    return "\n".join(lines)


def format_seeds(source: Any = None) -> str:
    """Seeds of one bundle, in held order."""
    book = _source_book(source)
    bundle = book.bundles[-1]
    lines = []
    for seed in bundle.seeds:
        lines.append(
            f"{seed.seed_id or '-'}: {seed.path} "
            f"{seed.symbol or '(file)'} - {seed.source} "
            f"hit at score {seed.score}")
    if not lines:
        lines.append("No seeds are held.")
    return "\n".join(lines)


def format_panel(source: Any = None) -> str:
    """The panel as a screen block: every row and the account.

    Accepts a RetrievalPanel or a RetrievalBook; a
    book shows the panel its latest bundle derives.
    """
    if isinstance(source, RetrievalPanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        panel = derive_panel(book.bundles[-1])
        lines = [f"Panel in {book.title}:"]
    lines.append("Connected pieces, in ranked order:")
    for row in panel.rows:
        lines.append(format_node(row))
    lines.extend(panel.account)
    return "\n".join(lines)


def format_graph_retrieval_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /graphsearch.

    With nothing named, the shipped example
    graph-retrieval book is shown - the example this
    slice ships - so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Graph Retrieval (M-152) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_seeds(book))
    lines.append("")
    lines.append(format_nodes(book))
    lines.append("")
    lines.append(format_panel(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_graphsearch_args(args: Any) -> Tuple[str, Any]:
    """Parse the /graphsearch grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    graph-retrieval book; ``node <node-id>`` shows
    one connected piece; ``seeds`` shows the latest
    bundle's seeds; ``panel`` shows the panel derived
    from the latest bundle. Anything else is a usage
    error naming the grammar. Returns
    ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head in ("panel", "seeds") and len(words) == 1:
        return (head, None)
    if head == "node" and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
