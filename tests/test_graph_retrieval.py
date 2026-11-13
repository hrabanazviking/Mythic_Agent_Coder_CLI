"""M-152 Retrieval over the code graph - pure-layer tests.

TIER: integration

The pure layer is the marriage as data: seeds (ranked
hits from the shipped semantic road, a vector
provider, the symbol road, or a manual naming),
expanded through the shipped symbol graph into
connected code - every piece carrying its relation,
its distance and its provenance - held in a bundle
in deterministic ranked order, with skipped seeds
and over-cap pieces named, a panel derived from the
bundle, the shipped example book held in a data
file, a loader that reads a book from any file, and
a registry. A stored panel or bundle disagreeing
with its derived shape is refused. Nothing here
calls a model, edits code or assembles live
context: holding a bundle changes nothing but data.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.context.semantic import build_corpus
from mythic_agent.context.symbol_graph import build_symbol_graph
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.graph_retrieval import (
    PLAIN_EXPLANATION,
    GRAPH_DECAY,
    GRAPH_RETRIEVAL_RESOURCE,
    GRAPH_RETRIEVAL_SCHEMA,
    GRAPH_RETRIEVAL_SLICE,
    MAX_RETRIEVAL_DEPTH,
    RELATIONS,
    SEED_SOURCES,
    USAGE,
    ConnectedNode,
    GraphRelationCount,
    GraphRetrievalRegistry,
    RetrievalBook,
    RetrievalBundle,
    RetrievalPanel,
    RetrievalSeed,
    book_record,
    build_book,
    build_bundle,
    build_node,
    build_panel,
    build_seed,
    bundle_record,
    derive_panel,
    expand_retrieval,
    format_graph_retrieval_screen,
    format_node,
    format_nodes,
    format_panel,
    format_seeds,
    load_graph_retrieval,
    load_graph_retrieval_file,
    node_record,
    panel_plain_words,
    panel_record,
    parse_graphsearch_args,
    plain_words,
    retrieve,
    seeds_from_query,
    seeds_from_semantic,
    seeds_from_vector_results,
    validate_book,
    validate_bundle,
    validate_node,
    validate_panel,
    validate_seed,
)

ROOT = Path(__file__).resolve().parents[1]

ALPHA = (
    "def helper_fn(x):\n"
    "    return x + 1\n"
    "\n"
    "def greet(name):\n"
    "    return helper_fn(name)\n"
)
BETA = (
    "from alpha import greet\n"
    "\n"
    "def run():\n"
    "    return greet(\"x\")\n"
)
GAMMA = "def lonely():\n    return 0\n"


def _graph(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "alpha.py").write_text(ALPHA, encoding="utf-8")
    (tmp_path / "beta.py").write_text(BETA, encoding="utf-8")
    (tmp_path / "gamma.py").write_text(GAMMA, encoding="utf-8")
    return build_symbol_graph(tmp_path)


def _seed(**overrides):
    fields = {
        "path": "alpha.py", "symbol": "greet",
        "score": 4.0, "source": "semantic",
        "seed_id": "seed-test",
    }
    fields.update(overrides)
    return build_seed(fields)


def _stored(bundle):
    record = bundle.to_record()
    record.pop("type")
    record.pop("slice")
    for seed in record["seeds"]:
        seed.pop("type")
        seed.pop("slice")
    for node in record["nodes"]:
        node.pop("type")
        node.pop("slice")
    return record


def test_constants_and_usage():
    assert GRAPH_RETRIEVAL_SLICE == "M-152"
    assert GRAPH_RETRIEVAL_SCHEMA == "mythic.graph_retrieval/1"
    assert GRAPH_RETRIEVAL_RESOURCE.endswith("graph_retrieval.yaml")
    assert GRAPH_DECAY == 0.5
    assert MAX_RETRIEVAL_DEPTH == 2
    assert RELATIONS[0] == "seed"
    assert SEED_SOURCES == ("semantic", "vector", "symbol", "manual")
    assert "/graphsearch node <node-id>" in USAGE
    assert "connected code, not confetti" in PLAIN_EXPLANATION
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data"
         / "graph_retrieval.yaml").read_text(encoding="utf-8"))
    assert raw["schema"] == GRAPH_RETRIEVAL_SCHEMA
    assert raw["slice"] == "M-152"


def test_shipped_example_shape():
    book = load_graph_retrieval()
    assert book.title == "Graph retrieval at the M-151 slice boundary"
    assert book.bundle_ids() == ("retrieval-m151-boundary",)
    bundle = book.bundles[0]
    assert bundle.query == "compaction glass-box summary versions journal"
    assert bundle.total_seeds == 1
    assert bundle.total_nodes == 6
    assert bundle.file_count == 4
    seed = bundle.seeds[0]
    assert seed.path == "mythic_agent/core/compaction_glassbox.py"
    assert seed.symbol == "CompactionRecord"
    assert seed.source == "semantic"
    assert [n.relation for n in bundle.nodes] == [
        "seed", "definition", "caller", "callee",
        "reference", "import"]
    assert bundle.nodes[0].score == 4.0
    assert all(n.score == 2.0 for n in bundle.nodes[1:])
    assert len(book.panels) == 1
    assert book.panels[0].panel_id == "panel-m151-boundary"


def test_shipped_panel_is_pinned_and_derived():
    book = load_graph_retrieval()
    panel = book.panels[0]
    assert validate_panel(panel, book.bundles[0]) is panel
    derived = derive_panel(book.bundles[0])
    assert derived.rows == panel.rows
    assert derived.total_nodes == 6
    assert derived.total_seeds == 1
    assert [c.relation for c in derived.relation_counts] == [
        "seed", "definition", "caller", "callee",
        "reference", "import"]
    assert panel.account == derived.account
    assert panel.account[0] == (
        "The bundle holds 6 connected pieces from 1 "
        "seed(s): seed 1, definition 1, caller 1, "
        "callee 1, reference 1, import 1.")


def test_seed_validation_and_aliases():
    seed = validate_seed({
        "doc_id": "alpha.py", "name": "greet",
        "relevance": 2.5, "source": "vector", "id": "seed-alias"})
    assert seed.path == "alpha.py"
    assert seed.symbol == "greet"
    assert seed.score == 2.5
    assert seed.seed_id == "seed-alias"
    plain = build_seed(path="beta.py", score=1, source="manual")
    assert plain.symbol is None
    assert plain.score == 1.0


def test_seed_refusals():
    with pytest.raises(ValueError):
        build_seed({"path": "alpha.py", "score": 1.0,
                    "source": "dreamt-up"})
    with pytest.raises(ValueError):
        build_seed({"path": "alpha.py", "score": 0,
                    "source": "semantic"})
    with pytest.raises(ValueError):
        build_seed({"path": "alpha.py", "score": float("inf"),
                    "source": "semantic"})
    with pytest.raises(ValueError):
        build_seed({"score": 1.0, "source": "semantic"})
    with pytest.raises(ValueError):
        build_seed({"path": "alpha.py", "file": "beta.py",
                    "score": 1.0, "source": "semantic"})
    with pytest.raises(ValueError):
        build_seed({"path": "alpha.py", "score": 1.0,
                    "source": "semantic", "surprise": 1})
    with pytest.raises(ValueError):
        build_seed({"path": "/abs/alpha.py", "score": 1.0,
                    "source": "semantic"})
    with pytest.raises(ValueError):
        build_seed({"path": "../alpha.py", "score": 1.0,
                    "source": "semantic"})


def test_node_score_is_derived_and_judged():
    node = build_node({
        "path": "alpha.py", "symbol": "greet",
        "relation": "seed", "distance": 0,
        "seed_score": 4.0, "score": 4.0,
        "provenance": "the seed itself"})
    assert node.score == 4.0
    deep = build_node({
        "path": "beta.py", "symbol": "run",
        "relation": "caller", "distance": 2,
        "seed_score": 4.0, "provenance": "two hops away"})
    assert deep.score == 1.0
    with pytest.raises(ValueError):
        build_node({
            "path": "alpha.py", "relation": "seed",
            "distance": 0, "seed_score": 4.0, "score": 3.0,
            "provenance": "a stored rank, loose"})
    with pytest.raises(ValueError):
        build_node({
            "path": "alpha.py", "relation": "seed",
            "distance": 1, "seed_score": 4.0,
            "provenance": "the seed stands at distance 0"})
    with pytest.raises(ValueError):
        build_node({
            "path": "alpha.py", "relation": "caller",
            "distance": 0, "seed_score": 4.0,
            "provenance": "only the seed stands at 0"})
    with pytest.raises(ValueError):
        validate_node(node, _seed(score=2.0))
    judged = validate_node(node, _seed(seed_id=None))
    assert judged is node


def test_expansion_returns_connected_code(tmp_path):
    graph = _graph(tmp_path)
    bundle = expand_retrieval(graph, [_seed(seed_id=None)],
                              query="greet")
    assert bundle.total_seeds == 1
    assert bundle.seeds[0].seed_id == "seed-1"
    assert [(n.path, n.symbol, n.relation) for n in bundle.nodes] == [
        ("alpha.py", "greet", "seed"),
        ("alpha.py", "helper_fn", "definition"),
        ("beta.py", "run", "caller"),
        ("alpha.py", "helper_fn", "callee"),
        ("beta.py", "run", "reference"),
        ("beta.py", None, "imported-by"),
    ]
    assert [n.node_id for n in bundle.nodes] == [
        "node-1", "node-2", "node-3", "node-4", "node-5", "node-6"]
    assert bundle.nodes[0].score == 4.0
    assert all(n.score == 2.0 for n in bundle.nodes[1:])
    assert bundle.skipped == ()
    assert bundle.omitted == 0
    assert bundle.file_count == 2
    caller = bundle.nodes[2]
    assert caller.line == 4
    assert "calls greet at beta.py:4" in caller.provenance
    # Deterministic: the same expansion stands in the
    # same order, every time.
    again = expand_retrieval(graph, [_seed(seed_id=None)],
                             query="greet")
    assert again.nodes == bundle.nodes
    assert validate_bundle(bundle, graph) is bundle


def test_expansion_depth_zero_and_two(tmp_path):
    graph = _graph(tmp_path)
    shallow = expand_retrieval(graph, [_seed()], query="greet",
                               depth=0)
    assert [(n.symbol, n.relation) for n in shallow.nodes] == [
        ("greet", "seed")]
    deep = expand_retrieval(graph, [_seed()], query="greet",
                            depth=2)
    assert deep.total_nodes == 9
    far = [n for n in deep.nodes if n.distance == 2]
    assert {(n.path, n.symbol, n.relation) for n in far} == {
        ("alpha.py", "greet", "caller"),
        ("alpha.py", "greet", "callee"),
        ("alpha.py", "greet", "reference"),
    }
    assert all(n.score == 1.0 for n in far)
    with pytest.raises(ValueError):
        expand_retrieval(graph, [_seed()], query="greet", depth=3)


def test_expansion_cap_counts_the_omitted(tmp_path):
    graph = _graph(tmp_path)
    bundle = expand_retrieval(graph, [_seed()], query="greet",
                              max_nodes=3)
    assert bundle.total_nodes == 3
    assert bundle.omitted == 3
    assert "beyond the node cap" in bundle.account[3]


def test_skipped_seeds_are_named_never_relocated(tmp_path):
    graph = _graph(tmp_path)
    missing = expand_retrieval(
        graph, [_seed(path="nope.py", symbol=None)], query="x")
    assert missing.nodes == ()
    assert len(missing.skipped) == 1
    assert "does not hold" in missing.skipped[0]
    misplaced = expand_retrieval(
        graph, [_seed(symbol="run")], query="run")
    assert misplaced.nodes == ()
    assert "not relocated" in misplaced.skipped[0]
    assert "beta.py" in misplaced.skipped[0]
    unknown = expand_retrieval(
        graph, [_seed(symbol="vanished")], query="vanished")
    assert "does not define" in unknown.skipped[0]
    lonely = expand_retrieval(
        graph, [_seed(path="gamma.py", symbol="lonely")],
        query="lonely")
    assert [(n.symbol, n.relation) for n in lonely.nodes] == [
        ("lonely", "seed")]
    with pytest.raises(ValueError):
        expand_retrieval(graph, [], query="greet")
    with pytest.raises(ValueError):
        expand_retrieval("not a graph", [_seed()], query="greet")


def test_seeds_from_query_reads_the_graph(tmp_path):
    graph = _graph(tmp_path)
    seeds = seeds_from_query(graph, "how does greet work")
    assert [(s.path, s.symbol, s.source) for s in seeds] == [
        ("alpha.py", "greet", "symbol")]
    assert seeds[0].score == 1.0
    assert seeds_from_query(graph, "unrelated words entirely") == ()
    both = seeds_from_query(graph, "greet helper_fn", top_n=5)
    assert {s.symbol for s in both} == {"greet", "helper_fn"}


def test_seeds_from_semantic_composes_the_shipped_scoring(tmp_path):
    _graph(tmp_path)
    docs, warnings = build_corpus(tmp_path)
    assert warnings == []
    seeds = seeds_from_semantic("greet helper name", docs)
    assert seeds[0].path == "alpha.py"
    assert seeds[0].source == "semantic"
    assert seeds[0].score > 0
    assert seeds_from_semantic("zzzz qqqq", docs) == ()


def test_seeds_from_vector_results_in_the_shipped_shape():
    seeds = seeds_from_vector_results([
        {"score": 0.5, "text": "run calls greet",
         "metadata": {"path": "beta.py", "symbol": "run"}},
        {"score": 0.9, "text": "greet defined here",
         "metadata": {"doc_id": "alpha.py", "name": "greet"}},
    ])
    assert [(s.path, s.symbol, s.source) for s in seeds] == [
        ("alpha.py", "greet", "vector"),
        ("beta.py", "run", "vector")]
    assert seeds[0].score == 0.9
    with pytest.raises(ValueError):
        seeds_from_vector_results([
            {"score": 0.9, "text": "a hit with no home",
             "metadata": {}}])
    with pytest.raises(ValueError):
        seeds_from_vector_results([
            {"text": "a hit with no rank",
             "metadata": {"path": "alpha.py"}}])


def test_retrieve_marries_both_roads(tmp_path):
    graph = _graph(tmp_path)
    docs, _ = build_corpus(tmp_path)
    bundle = retrieve(graph, "greet", docs=docs)
    assert bundle.total_seeds == 3
    assert {s.source for s in bundle.seeds} == {"symbol", "semantic"}
    seed_nodes = [n for n in bundle.nodes if n.relation == "seed"]
    assert ("alpha.py", "greet") in {
        (n.path, n.symbol) for n in seed_nodes}
    assert any(
        n.relation == "caller" and n.symbol == "run"
        for n in bundle.nodes)
    with pytest.raises(ValueError):
        retrieve(graph, "nothing anywhere names this")
    with pytest.raises(ValueError):
        retrieve(graph, "nothing anywhere names this", docs=docs)


def test_bundle_internal_refusals(tmp_path):
    graph = _graph(tmp_path)
    bundle = expand_retrieval(graph, [_seed()], query="greet")
    nodes = list(bundle.nodes)
    with pytest.raises(ValueError):
        RetrievalBundle(
            query="greet", seeds=bundle.seeds,
            nodes=(nodes[0], nodes[0]))
    with pytest.raises(ValueError):
        RetrievalBundle(
            query="greet", seeds=bundle.seeds,
            nodes=tuple(reversed(nodes)))
    stored = _stored(bundle)
    stored["total_nodes"] = 99
    with pytest.raises(ValueError):
        validate_bundle(stored)
    stored = _stored(bundle)
    stored["account"] = ["A loose account, stored."]
    with pytest.raises(ValueError):
        validate_bundle(stored)
    stored = _stored(bundle)
    stored["nodes"][1]["provenance"] = "tampered provenance"
    with pytest.raises(ValueError):
        validate_bundle(stored, graph)
    assert validate_bundle(_stored(bundle), graph).nodes == bundle.nodes


def test_panel_is_derived_and_judged(tmp_path):
    graph = _graph(tmp_path)
    bundle = expand_retrieval(graph, [_seed()], query="greet")
    panel = derive_panel(bundle)
    assert panel.total_nodes == 6
    assert panel.file_count == 2
    assert panel.row_for("node-3").symbol == "run"
    with pytest.raises(KeyError):
        panel.row_for("node-99")
    with pytest.raises(ValueError):
        RetrievalPanel(
            rows=bundle.nodes, total_nodes=99,
            total_seeds=1, file_count=2,
            relation_counts=bundle.relation_counts)
    stored = panel.to_record()
    for row in stored["rows"]:
        row.pop("type")
        row.pop("slice")
    stored["rows"][0]["provenance"] = "tampered"
    with pytest.raises(ValueError):
        validate_panel(stored, bundle)
    assert build_panel(panel) is panel
    assert build_panel(panel, bundle) is panel


def test_book_validation_refusals():
    with pytest.raises(ValidationError):
        validate_book({"schema": "mythic.other/1"})
    with pytest.raises(ValidationError):
        validate_book({
            "schema": GRAPH_RETRIEVAL_SCHEMA,
            "guide": {"title": "A book"}, "bundles": [],
            "surprise": True})
    book = load_graph_retrieval()
    bundle = book.bundles[0]
    with pytest.raises(ValueError):
        build_book({"title": "Two of one", "bundles": [bundle, bundle]})
    with pytest.raises(ValidationError):
        validate_book({
            "schema": GRAPH_RETRIEVAL_SCHEMA,
            "guide": {"title": "No bundles here"}})


def test_load_graph_retrieval_file_roundtrip(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "graph_retrieval.yaml").read_text(encoding="utf-8")
    path = tmp_path / "graph_retrieval.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_graph_retrieval_file(path)
    assert book.title == "Graph retrieval at the M-151 slice boundary"
    assert book.bundle_ids() == ("retrieval-m151-boundary",)
    with pytest.raises(FileNotFoundError):
        load_graph_retrieval_file(tmp_path / "nope.yaml")


def test_registry_holds_bundles_one_by_one(tmp_path):
    graph = _graph(tmp_path)
    bundle = expand_retrieval(graph, [_seed()], query="greet")
    registry = GraphRetrievalRegistry()
    held = registry.register_bundle(bundle)
    assert held.bundle_id == "retrieval-1"
    unnamed = expand_retrieval(
        graph, [_seed(path="gamma.py", symbol="lonely",
                      seed_id="seed-lonely")], query="lonely")
    fresh = GraphRetrievalRegistry()
    auto = fresh.register_bundle(
        RetrievalBundle(
            query="lonely", seeds=unnamed.seeds,
            nodes=unnamed.nodes, depth=unnamed.depth,
            account=unnamed.account))
    assert auto.bundle_id == "retrieval-1"
    with pytest.raises(ValueError):
        registry.register_bundle(held)
    with pytest.raises(KeyError):
        registry.get_bundle("retrieval-nope")
    assert registry.latest_bundle().bundle_id == held.bundle_id
    assert registry.panel().total_nodes == 6
    book_registry = GraphRetrievalRegistry(load_graph_retrieval())
    assert book_registry.book().title == (
        "Graph retrieval at the M-151 slice boundary")
    assert book_registry.panel().total_nodes == 6


def test_records_and_plain_words(tmp_path):
    graph = _graph(tmp_path)
    bundle = expand_retrieval(graph, [_seed()], query="greet")
    news = bundle_record(bundle)
    assert news["type"] == "graph_retrieval_bundle"
    assert news["slice"] == "M-152"
    assert news["news"] is True
    assert "6 connected pieces" in news["headline"]
    node_news = node_record(bundle.nodes[0])
    assert node_news["type"] == "graph_retrieval_node"
    panel_news = panel_record(derive_panel(bundle))
    assert panel_news["type"] == "graph_retrieval_panel"
    book_news = book_record(load_graph_retrieval())
    assert book_news["type"] == "graph_retrieval_book"
    assert book_news["bundle_count"] == 1
    words = plain_words(bundle.nodes[2])
    assert "beta.py" in words and "caller" in words
    told = panel_plain_words(load_graph_retrieval())
    assert "Graph retrieval at the M-151 slice boundary" in told
    assert "connected code, not confetti" in told


def test_formatters_and_screen(tmp_path):
    graph = _graph(tmp_path)
    bundle = expand_retrieval(graph, [_seed()], query="greet")
    book = RetrievalBook(title="A held retrieval", bundles=(bundle,))
    assert "node-1: alpha.py greet" in format_node(bundle.nodes[0])
    assert "node-3: beta.py run" in format_nodes(book)
    assert "seed-test: alpha.py greet" in format_seeds(book)
    panel_text = format_panel(book)
    assert "Panel in A held retrieval:" in panel_text
    screen = format_graph_retrieval_screen()
    assert "Graph Retrieval (M-152)" in screen
    assert "retrieval-m151-boundary" not in screen
    assert "seed-1: mythic_agent/core/compaction_glassbox.py" in screen
    assert format_graph_retrieval_screen(book).count("node-1") >= 1


def test_parse_graphsearch_args_grammar():
    assert parse_graphsearch_args("") == ("show", None)
    assert parse_graphsearch_args("show") == ("show", None)
    assert parse_graphsearch_args("list") == ("show", None)
    assert parse_graphsearch_args("node node-3") == ("node", "node-3")
    assert parse_graphsearch_args("seeds") == ("seeds", None)
    assert parse_graphsearch_args("panel") == ("panel", None)
    with pytest.raises(ValueError):
        parse_graphsearch_args("dance party")
    with pytest.raises(ValueError):
        parse_graphsearch_args("node")
    with pytest.raises(ValueError):
        parse_graphsearch_args(None if False else 42)


def test_honest_boundary_module_imports_no_live_roads():
    source = (ROOT / "mythic_agent" / "core"
              / "graph_retrieval.py").read_text(encoding="utf-8")
    # The pure layer composes the shipped graph and
    # the shipped semantic scoring by import, and
    # imports no agent, ui or terminal code: holding
    # a bundle can call no model from here.
    assert "from ..context.symbol_graph import" in source
    assert "from ..context.semantic import" in source
    assert "from ..agents" not in source
    assert "from ..ui" not in source
    assert "from ..terminal" not in source
    assert "import agents" not in source


# -- agent layer -----------------------------------------------------------
#
# M-152 agent layer: the agent holds a
# GraphRetrievalRegistry for the session (session
# state only, no new setting), bundles are held by
# being registered - published as their bundle_record
# session news with the derived panel_record, through
# the checkpoint road, deduped per shape - the report
# road renders the held book (or the shipped example
# when unheld) through the pure formatters, a run over
# the workspace builds the shipped graph and semantic
# corpus over project_root and holds the married
# bundle, and the /graphsearch surface rides both
# roads on the pure parser + formatters. Status, get,
# seeds and panel reads register and publish nothing,
# answer from the held registry first and from the
# shipped example only while nothing is held - a held
# session never falls back to the example. The panel
# derives at call time from the latest held bundle,
# never held. This layer calls no model and edits no
# code, and there is no Part VIII board yet, so the
# screen is where the retrieval is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _graph_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_graph_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "graph_retrieval.yaml").read_text(encoding="utf-8")
    path = tmp_path / "graph_retrieval.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


def _bundle(graph):
    return expand_retrieval(graph, [_seed()], query="greet")


class TestGraphRetrievalAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.graph_retrieval_status()
        assert status["bundles"] == []
        assert status["book"] is None
        assert status["graph_retrieval"]["title"] == (
            "Graph retrieval at the M-151 slice boundary")
        assert len(status["graph_retrieval"]["bundles"]) == 1
        assert status["panel"]["total_nodes"] == 6
        assert status["panel"]["total_seeds"] == 1
        assert status["book_record"]["bundle_count"] == 1
        assert "Graph Retrieval (M-152)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._graph_retrieval_registry()
        assert agent._graph_retrieval_registry() is first
        assert agent._graph_retrieval_store is first

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.graph_retrieval_status()
        agent.get_graph_retrieval_bundle("retrieval-m151-boundary")
        agent.get_graph_retrieval_node("node-1")
        agent.graph_retrieval_seeds()
        agent.graph_retrieval_panel()
        agent.report_graph_retrieval()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("graph_retrieval")] == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_graph_retrieval_bundle("retrieval-nope")
        with pytest.raises(KeyError):
            agent.get_graph_retrieval_node("node-99")

    def test_status_after_register_shows_the_held_pieces(
            self, agent, tmp_path):
        graph = _graph(tmp_path / "ws")
        agent.register_graph_retrieval_bundle(_bundle(graph))
        status = agent.graph_retrieval_status()
        assert [b["bundle_id"] for b in status["bundles"]] == [
            "retrieval-1"]
        assert status["book"]["title"] == "Session graph retrieval"
        assert status["panel"]["total_nodes"] == 6

    def test_held_session_never_falls_back_to_the_example(
            self, agent, tmp_path):
        graph = _graph(tmp_path / "ws")
        agent.register_graph_retrieval_bundle(_bundle(graph))
        with pytest.raises(KeyError):
            agent.get_graph_retrieval_bundle("retrieval-m151-boundary")
        node = agent.get_graph_retrieval_node("node-3")
        assert node.path == "beta.py"
        assert agent.graph_retrieval_book().title == (
            "Session graph retrieval")


class TestGraphRetrievalAgentHolding:
    def test_register_bundle_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        graph = _graph(tmp_path / "ws")
        outcome = agent.register_graph_retrieval_bundle(_bundle(graph))
        assert outcome["bundle"]["bundle_id"] == "retrieval-1"
        assert outcome["bundle_news"]["type"] == "graph_retrieval_bundle"
        assert outcome["panel_record"]["type"] == (
            "graph_retrieval_panel")
        events = _graph_events(
            store, session_id, "graph_retrieval_bundle")
        assert len(events) == 1
        assert events[0]["bundle_id"] == "retrieval-1"
        panels = _graph_events(
            store, session_id, "graph_retrieval_panel")
        assert len(panels) == 1
        assert panels[0]["total_nodes"] == 6
        agent._publish_graph_retrieval_record(outcome["bundle_news"])
        agent._publish_graph_retrieval_record(outcome["panel_record"])
        assert len(_graph_events(
            store, session_id, "graph_retrieval_bundle")) == 1
        assert len(_graph_events(
            store, session_id, "graph_retrieval_panel")) == 1
        from mythic_agent.core.context_budget import (
            book_record as _budget_book_record, load_context_budget)
        agent._publish_graph_retrieval_record(
            {"type": "mentions_mention", "mention_id": "mention-x"})
        agent._publish_graph_retrieval_record(
            _budget_book_record(load_context_budget()))
        agent._publish_graph_retrieval_record(
            book_record(load_graph_retrieval()))
        for kind in ("mentions_mention", "context_budget_book",
                     "graph_retrieval_book"):
            assert _graph_events(store, session_id, kind) == []
        agent.close()

    def test_duplicate_bundle_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        graph = _graph(tmp_path / "ws")
        held = agent.register_graph_retrieval_bundle(_bundle(graph))
        with pytest.raises(ValueError):
            agent.register_graph_retrieval_bundle(
                agent.get_graph_retrieval_bundle(
                    held["bundle"]["bundle_id"]))
        assert len(_graph_events(
            store, session_id, "graph_retrieval_bundle")) == 1
        agent.close()

    def test_run_retrieval_over_the_workspace(self, agent, tmp_path):
        (tmp_path / "alpha.py").write_text(ALPHA, encoding="utf-8")
        (tmp_path / "beta.py").write_text(BETA, encoding="utf-8")
        outcome = agent.run_graph_retrieval("greet")
        assert outcome["query"] == "greet"
        bundle = agent.get_graph_retrieval_bundle(
            outcome["bundle"]["bundle_id"])
        assert any(
            n.relation == "seed" and n.symbol == "greet"
            for n in bundle.nodes)
        assert any(
            n.relation == "caller" and n.symbol == "run"
            for n in bundle.nodes)
        with pytest.raises(ValueError):
            agent.run_graph_retrieval("nothing anywhere names this")

    def test_register_book_holds_and_publishes_in_order(self, agent):
        book = build_book({
            "title": "A held retrieval book",
            "bundles": [{
                "query": "greet", "depth": 1,
                "seeds": [{
                    "path": "alpha.py", "symbol": "greet",
                    "score": 4.0, "source": "semantic",
                    "seed_id": "seed-held"}],
                "nodes": [{
                    "path": "alpha.py", "symbol": "greet",
                    "kind": "function", "relation": "seed",
                    "distance": 0, "seed_score": 4.0,
                    "seed_id": "seed-held",
                    "provenance": "the seed itself",
                    "node_id": "node-1"}],
                "bundle_id": "retrieval-held"}]})
        outcome = agent.register_graph_retrieval_book(book)
        assert outcome["count"] == 1
        assert [b["bundle_id"] for b in outcome["bundles_news"]] == [
            "retrieval-held"]
        assert agent.graph_retrieval_book().title == (
            "A held retrieval book")

    def test_register_book_twice_refuses(self, agent):
        agent.register_graph_retrieval_book(load_graph_retrieval())
        with pytest.raises(ValueError):
            agent.register_graph_retrieval_book(load_graph_retrieval())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_graph_retrieval_book()
        assert outcome["count"] == 1
        assert outcome["book"]["title"] == (
            "Graph retrieval at the M-151 slice boundary")
        assert len(_graph_events(
            store, session_id, "graph_retrieval_bundle")) == 1
        assert agent.graph_retrieval_book().panels[0].panel_id == (
            "panel-m151-boundary")
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_graph_retrieval_book()
        with pytest.raises(ValueError):
            agent.record_graph_retrieval_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_graph_book(tmp_path)
        book = load_graph_retrieval_file(path)
        outcome = agent.record_graph_retrieval_book(book)
        assert outcome["count"] == 1
        assert agent.get_graph_retrieval_node("node-4").symbol == (
            "TokenEstimator")

    def test_report_renders_the_example_when_unheld(self, agent):
        report = agent.report_graph_retrieval()
        assert report["book"]["bundle_count"] == 1
        assert "node-1: mythic_agent/core/compaction_glassbox.py" in (
            report["nodes_text"])
        assert "Panel in Graph retrieval" in report["panel_text"]

    def test_report_renders_the_held_book_only(self, agent, tmp_path):
        graph = _graph(tmp_path / "ws")
        agent.register_graph_retrieval_bundle(_bundle(graph))
        report = agent.report_graph_retrieval()
        assert report["book"]["title"] == "Session graph retrieval"
        assert "compaction_glassbox" not in report["nodes_text"]
        assert "node-3: beta.py run" in report["nodes_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_graph_retrieval()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("graph_retrieval")] == []
        agent.close()

    def test_no_live_edit_or_persist_road(self, agent, tmp_path):
        # This layer holds retrievals as data: it calls
        # no model, edits no code, assembles no live
        # context and persists nothing - and there is
        # no Part VIII board yet. Running or holding a
        # retrieval changes no workspace file and no
        # live context: the workspace files and a
        # ContextBuilder's built messages are the same
        # before and after.
        assert not hasattr(agent, "apply_graph_retrieval")
        assert not hasattr(agent, "edit_graph_retrieval")
        assert not hasattr(agent, "persist_graph_retrieval")
        assert not hasattr(agent, "graph_retrieval_board")
        (tmp_path / "alpha.py").write_text(ALPHA, encoding="utf-8")
        (tmp_path / "beta.py").write_text(BETA, encoding="utf-8")
        before = {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")}
        from mythic_agent.agents.context import ContextBuilder
        builder = ContextBuilder(max_tokens=4000)
        builder.add_system("You are the coder.")
        builder.add_turn("user", "Build the slice.")
        built_before = builder.build()
        agent.run_graph_retrieval("greet")
        agent.record_graph_retrieval_book()
        assert builder.build() == built_before
        assert {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")} == before


class TestGraphRetrievalTerminalSurface:
    def test_show_node_seeds_and_panel(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/graphsearch")
        assert "Graph Retrieval (M-152)" in text
        _, _, text = _slash(agent, "/graphsearch node node-1")
        assert "node-1: mythic_agent/core/compaction_glassbox.py" in text
        assert "CompactionRecord" in text
        _, _, text = _slash(agent, "/graphsearch seeds")
        assert "seed-1: mythic_agent/core/compaction_glassbox.py" in text
        _, _, text = _slash(agent, "/graphsearch panel")
        assert "Panel in Graph retrieval" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/graphsearch [show|node <node-id>|seeds|panel]") in text
        _, _, text = _slash(agent, "/graphsearch dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/graphsearch node node-99")
        assert "no piece in the book" in text


@pytest.fixture()
def graphsearch_handler(agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY
    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _graphsearch_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestGraphRetrievalCommand:
    def test_show_is_default(self, graphsearch_handler, agent):
        graphsearch_handler._handle_graphsearch("")
        assert "Graph Retrieval (M-152)" in (
            _graphsearch_published_text(graphsearch_handler))

    def test_node_seeds_and_panel(self, graphsearch_handler, agent):
        graphsearch_handler._handle_graphsearch("node node-1")
        assert "CompactionRecord" in _graphsearch_published_text(
            graphsearch_handler)
        graphsearch_handler._handle_graphsearch("seeds")
        assert "seed-1:" in _graphsearch_published_text(
            graphsearch_handler)
        graphsearch_handler._handle_graphsearch("panel")
        assert "Panel in Graph retrieval" in _graphsearch_published_text(
            graphsearch_handler)

    def test_bad_grammar_is_published(self, graphsearch_handler, agent):
        graphsearch_handler._handle_graphsearch("dance party")
        assert USAGE in _graphsearch_published_text(graphsearch_handler)


class TestChatScreenRoutingGraphRetrieval:
    def test_graphsearch_routes_as_system_command(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import MainChatScreen

        class _FakeLog:
            def __init__(self):
                self.lines = []

            def write(self, *args, **kwargs):
                self.lines.append(" ".join(str(a) for a in args))

        calls = []
        monkeypatch.setattr(
            chat_screen.SecureAPI, "publish_system_command",
            staticmethod(lambda cmd, args: calls.append((cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        screen.handle_command(
            "/graphsearch node node-1", _FakeLog())
        assert calls == [("/graphsearch", "node node-1")]
