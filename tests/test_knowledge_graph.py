"""Tests for mythic_agent.knowledge.graph (Slice 41)."""

import json
from pathlib import Path

import pytest

from mythic_agent.knowledge.graph import (
    KnowledgeGraph,
    build_graph_from_index,
    build_graph_from_project,
)


@pytest.fixture()
def graph() -> KnowledgeGraph:
    g = KnowledgeGraph()
    g.add_entity("app", "module")
    g.add_entity("app.run", "function", docstring="Run the app.")
    g.add_entity("app.Engine", "class")
    g.add_relation("app", "app.run", "contains")
    g.add_relation("app", "app.Engine", "contains")
    g.add_relation("app.Engine", "app.Engine.start", "defines")
    g.add_relation("app.run", "app.Engine.start", "calls")
    return g


def test_add_entity_and_query(graph: KnowledgeGraph):
    q = graph.query("app.run")
    assert q["entity"] == "app.run"
    assert q["type"] == "function"
    assert "Run the app." in q["summary"]
    assert "app.Engine.start" in q["relations"]["calls"]


def test_query_groups_incoming_and_outgoing(graph: KnowledgeGraph):
    q = graph.query("app.Engine.start")
    assert q["relations"]["incoming:defines"] == ["app.Engine"]
    assert q["relations"]["incoming:calls"] == ["app.run"]


def test_query_unknown_entity_raises(graph: KnowledgeGraph):
    with pytest.raises(KeyError):
        graph.query("nope")


def test_query_related_two_hop(graph: KnowledgeGraph):
    q = graph.query("app")
    assert "app.Engine.start" in q["related"]


def test_entities_of_type_and_neighbors(graph: KnowledgeGraph):
    assert graph.entities_of_type("module") == ["app"]
    assert sorted(graph.neighbors("app", "contains")) == ["app.Engine", "app.run"]
    assert len(graph) == 4


def test_add_relation_creates_unknown_entities():
    g = KnowledgeGraph()
    g.add_relation("a", "b", "links")
    assert g.entity("a")["type"] == "unknown"
    assert g.entity("b")["type"] == "unknown"


def test_no_duplicate_relations(graph: KnowledgeGraph):
    graph.add_relation("app", "app.run", "contains")
    q = graph.query("app.run")
    assert q["relations"]["incoming:contains"] == ["app"]


def test_explain_and_architecture_summary(graph: KnowledgeGraph):
    text = graph.explain("app.run")
    assert "app.run" in text and "function" in text
    summary = graph.architecture_summary()
    assert "1 modules" in summary
    assert "- app" in summary


def test_save_and_load_roundtrip(graph: KnowledgeGraph, tmp_path: Path):
    path = graph.save(tmp_path / "kg" / "graph.json")
    assert path.exists()
    data = json.loads(path.read_text())
    assert "app.run" in data["entities"]
    loaded = KnowledgeGraph.load(path)
    assert loaded.query("app.run")["type"] == "function"
    assert loaded.query("app")["relations"]["contains"] == ["app.Engine", "app.run"]


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    (tmp_path / "alpha.py").write_text(
        "import beta\n\n"
        "class Engine:\n"
        '    """The engine."""\n'
        "    def start(self):\n"
        '        """Start it."""\n'
        "        return beta.helper()\n"
    )
    (tmp_path / "beta.py").write_text(
        "def helper():\n"
        '    """Help."""\n'
        "    return 42\n"
    )
    return tmp_path


def test_build_graph_from_project(project: Path):
    g = build_graph_from_project(project)
    assert "alpha" in g.entities_of_type("module")
    assert "beta" in g.entities_of_type("module")
    q = g.query("alpha.Engine")
    assert q["type"] == "class"
    assert "alpha.Engine.start" in q["relations"]["defines"]


def test_build_graph_call_edges(project: Path):
    g = build_graph_from_project(project)
    q = g.query("alpha.Engine.start")
    assert "beta.helper" in q["relations"]["calls"]


def test_build_graph_import_edges(project: Path):
    g = build_graph_from_project(project)
    q = g.query("alpha")
    assert "alpha.beta" in q["relations"]["imports"]


def test_build_graph_from_index_none():
    g = build_graph_from_index(None)
    assert len(g) == 0
