"""Tests for M-069 — Intelligence cache.

TIER: unit

Parse/graph/LSP results cached per file hash: entries live
under the workspace's ``.mythic/intelligence-cache/``, keyed
by kind + workspace-relative path + the file's SHA-256
content hash + producer name. The slice's heart is
invalidation honesty — a lookup recomputes the file's
current hash, so a changed file evicts its stale entry and
misses; a stale result is never served. The parse producer
is the M-043 foundation's own parse and the graph producer
is M-046's per-file extraction, cross-checked live; LSP
payloads are stored/looked up only, their producer being
the live server road.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mythic_agent.tools import intelligence_cache as surface
from mythic_agent.tools.intelligence_cache import (
    CACHE_KINDS,
    INTELLIGENCE_CACHE_SLICE,
    MAX_PRODUCER_FILE_BYTES,
    PLAIN_EXPLANATION,
    PRODUCERS,
    USAGE,
    IntelligenceCache,
    cache_dir_for,
    entry_key,
    format_intelligence_cache_report,
    intelligence_cache_report,
    parse_intelcache_args,
    sha256_hex,
)

SOURCE_V1 = "import os\n\n\ndef alpha(x):\n    return x + 1\n"
SOURCE_V2 = ("import os\n\n\ndef alpha(x):\n    return x + 1\n\n\n"
             "def beta(y):\n    return y * 2\n")


def _workspace(tmp_path: Path) -> Path:
    (tmp_path / "mod.py").write_text(SOURCE_V1, encoding="utf-8")
    return tmp_path


def _cache(tmp_path: Path) -> IntelligenceCache:
    return IntelligenceCache(tmp_path)


# -- keys + kinds -----------------------------------------------------------

def test_hash_and_key_are_deterministic():
    assert sha256_hex(b"abc") == sha256_hex(b"abc")
    assert sha256_hex(b"abc") != sha256_hex(b"abd")
    key = entry_key("parse", "mod.py", "h" * 64, PRODUCERS["parse"])
    assert key == entry_key("parse", "mod.py", "h" * 64,
                            PRODUCERS["parse"])
    assert key != entry_key("graph", "mod.py", "h" * 64,
                            PRODUCERS["parse"])
    assert key != entry_key("parse", "mod.py", "h" * 64, "other/9")
    assert INTELLIGENCE_CACHE_SLICE == "M-069"
    assert CACHE_KINDS == ("parse", "graph", "lsp")
    assert set(PRODUCERS) == set(CACHE_KINDS)


def test_cache_dir_lives_under_workspace_mythic(tmp_path: Path):
    assert cache_dir_for(tmp_path) == (
        tmp_path.resolve() / ".mythic" / "intelligence-cache")


def test_unknown_kind_refused(tmp_path: Path):
    cache = _cache(_workspace(tmp_path))
    with pytest.raises(ValueError, match="unknown cache kind"):
        cache.put("mod.py", "embeddings", {})
    with pytest.raises(ValueError, match="unknown cache kind"):
        cache.get("mod.py", "embeddings")


def test_non_mapping_payload_refused(tmp_path: Path):
    cache = _cache(_workspace(tmp_path))
    with pytest.raises(ValueError, match="mappings"):
        cache.put("mod.py", "parse", ["not", "a", "dict"])  # type: ignore[arg-type]


def test_outside_workspace_refused(tmp_path: Path):
    cache = _cache(_workspace(tmp_path))
    with pytest.raises(ValueError, match="outside the workspace"):
        cache.put("../elsewhere.py", "parse", {})
    with pytest.raises(ValueError, match="outside the workspace"):
        cache.get("/etc/passwd", "parse")


# -- put / get honesty --------------------------------------------------------

def test_put_get_roundtrip_every_kind(tmp_path: Path):
    cache = _cache(_workspace(tmp_path))
    for kind in CACHE_KINDS:
        info = cache.put("mod.py", kind, {"kind_was": kind})
        assert info.kind == kind and info.path == "mod.py"
        assert info.file_hash == sha256_hex(SOURCE_V1.encode())
        assert info.producer == PRODUCERS[kind]
        assert cache.get("mod.py", kind) == {"kind_was": kind}
    stats = cache.stats()
    assert stats["entries"] == 3
    assert stats["per_kind"] == {"parse": 1, "graph": 1, "lsp": 1}
    assert cache.kind_counts() == stats["per_kind"]
    assert stats["hits"] == 3 and stats["misses"] == 0


def test_missing_entry_is_a_plain_miss(tmp_path: Path):
    cache = _cache(_workspace(tmp_path))
    assert cache.get("mod.py", "parse") is None
    stats = cache.stats()
    assert stats["misses"] == 1 and stats["stale_evictions"] == 0


def test_changed_file_never_serves_stale(tmp_path: Path):
    root = _workspace(tmp_path)
    cache = _cache(root)
    cache.put("mod.py", "parse", {"definitions": ["alpha"]})
    (root / "mod.py").write_text(SOURCE_V2, encoding="utf-8")
    assert cache.get("mod.py", "parse") is None
    stats = cache.stats()
    assert stats["stale_evictions"] == 1 and stats["misses"] == 1
    assert stats["entries"] == 0  # the stale entry was evicted
    # And the fresh content caches + serves under its new hash.
    cache.put("mod.py", "parse", {"definitions": ["alpha", "beta"]})
    assert cache.get("mod.py", "parse") == {
        "definitions": ["alpha", "beta"]}


def test_missing_file_misses_and_evicts(tmp_path: Path):
    root = _workspace(tmp_path)
    cache = _cache(root)
    cache.put("mod.py", "graph", {"definitions": []})
    (root / "mod.py").unlink()
    assert cache.get("mod.py", "graph") is None
    assert cache.stats()["entries"] == 0


def test_corrupt_entry_is_a_miss_and_is_evicted(tmp_path: Path):
    root = _workspace(tmp_path)
    cache = _cache(root)
    info = cache.put("mod.py", "parse", {"ok": True})
    key = entry_key("parse", "mod.py", info.file_hash, info.producer)
    (cache.cache_dir / f"{key}.json").write_text(
        "{ not json", encoding="utf-8")
    assert cache.get("mod.py", "parse") is None
    assert cache.stats()["entries"] == 0


def test_producer_mismatch_misses_without_evicting(tmp_path: Path):
    cache = _cache(_workspace(tmp_path))
    cache.put("mod.py", "lsp", {"diagnostics": []},
              producer="m049-lsp/1")
    assert cache.get("mod.py", "lsp", producer="other/9") is None
    # The other producer's entry is not stale — it stays, and
    # its own producer still hits.
    assert cache.stats()["entries"] == 1
    assert cache.stats()["stale_evictions"] == 0
    assert cache.get("mod.py", "lsp") == {"diagnostics": []}


def test_stats_persist_across_instances(tmp_path: Path):
    root = _workspace(tmp_path)
    cache = _cache(root)
    cache.put("mod.py", "parse", {"ok": True})
    assert cache.get("mod.py", "parse") == {"ok": True}
    fresh = IntelligenceCache(root, create=False)
    assert fresh.stats()["hits"] == 1


def test_check_states_follow_the_file(tmp_path: Path):
    root = _workspace(tmp_path)
    cache = _cache(root)
    state = cache.check("mod.py")
    assert state.path == "mod.py"
    assert state.file_hash == sha256_hex(SOURCE_V1.encode())
    assert state.states == {k: "absent" for k in CACHE_KINDS}
    assert state.hit_ready_kinds() == ()
    cache.put("mod.py", "parse", {"ok": True})
    state = cache.check("mod.py")
    assert state.state_for("parse") == "hit-ready"
    assert state.hit_ready_kinds() == ("parse",)
    (root / "mod.py").write_text(SOURCE_V2, encoding="utf-8")
    state = cache.check("mod.py")
    assert state.state_for("parse") == "stale"


def test_get_or_compute_computes_once(tmp_path: Path):
    cache = _cache(_workspace(tmp_path))
    calls = []

    def compute():
        calls.append(1)
        return {"computed": len(calls)}

    payload, hit = cache.get_or_compute("mod.py", "parse", compute)
    assert (payload, hit) == ({"computed": 1}, False)
    payload, hit = cache.get_or_compute("mod.py", "parse", compute)
    assert (payload, hit) == ({"computed": 1}, True)
    assert len(calls) == 1


def test_clear_removes_entries_and_reports(tmp_path: Path):
    cache = _cache(_workspace(tmp_path))
    cache.put("mod.py", "parse", {"ok": True})
    cache.put("mod.py", "graph", {"ok": True})
    assert cache.clear() == 2
    assert cache.stats()["entries"] == 0
    assert cache.clear() == 0


# -- live producers -------------------------------------------------------------

def test_cached_parse_matches_the_live_foundation(tmp_path: Path):
    root = _workspace(tmp_path)
    cache = _cache(root)
    from mythic_agent.core.tree_sitter_foundation import parse_source
    live = parse_source("python", SOURCE_V1)
    payload, hit = cache.cached_parse("mod.py")
    assert hit is False
    assert payload["language"] == live.language
    assert payload["backend"] == live.backend
    assert payload["has_error"] == live.has_error
    assert [d["name"] for d in payload["definitions"]] == [
        d.name for d in live.definitions]
    payload2, hit2 = cache.cached_parse("mod.py")
    assert hit2 is True and payload2 == payload


def test_cached_parse_hit_never_reruns_the_producer(
        tmp_path: Path, monkeypatch):
    root = _workspace(tmp_path)
    cache = _cache(root)
    payload, hit = cache.cached_parse("mod.py")
    assert hit is False

    def _boom(*args, **kwargs):
        raise AssertionError("producer re-ran on a cache hit")

    monkeypatch.setattr(
        "mythic_agent.core.tree_sitter_foundation.parse_source", _boom)
    payload2, hit2 = cache.cached_parse("mod.py")
    assert hit2 is True and payload2 == payload


def test_cached_graph_matches_the_live_extraction(tmp_path: Path):
    root = _workspace(tmp_path)
    cache = _cache(root)
    from mythic_agent.context.symbol_graph import extract_file_graph
    live = extract_file_graph("mod.py", "python", SOURCE_V1).record()
    payload, hit = cache.cached_graph("mod.py")
    assert hit is False
    assert json.loads(json.dumps(payload)) == json.loads(
        json.dumps(live))
    _payload2, hit2 = cache.cached_graph("mod.py")
    assert hit2 is True


def test_changed_file_recomputes_fresh_results(tmp_path: Path):
    root = _workspace(tmp_path)
    cache = _cache(root)
    payload, _hit = cache.cached_parse("mod.py")
    assert [d["name"] for d in payload["definitions"]] == ["alpha"]
    (root / "mod.py").write_text(SOURCE_V2, encoding="utf-8")
    payload, hit = cache.cached_parse("mod.py")
    assert hit is False
    assert [d["name"] for d in payload["definitions"]] == [
        "alpha", "beta"]
    assert cache.stats()["stale_evictions"] == 1


def test_producer_refuses_oversized_and_uncatalogued(tmp_path: Path):
    root = _workspace(tmp_path)
    big = root / "big.py"
    big.write_text("x = 1\n" * (MAX_PRODUCER_FILE_BYTES // 6 + 10),
                   encoding="utf-8")
    cache = _cache(root)
    with pytest.raises(ValueError, match="producer cap"):
        cache.cached_parse("big.py")
    (root / "notes.txt").write_text("hello\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no catalogued language"):
        cache.cached_parse("notes.txt")


def test_grammarless_language_is_never_invented(tmp_path: Path):
    root = _workspace(tmp_path)
    (root / "song.mojo").write_text("fn main():\n    pass\n",
                                    encoding="utf-8")
    cache = _cache(root)
    from mythic_agent.core.tree_sitter_foundation import (
        ParseUnavailableError)
    with pytest.raises(ParseUnavailableError):
        cache.cached_parse("song.mojo")


# -- warm ---------------------------------------------------------------------

def test_warm_fills_then_hits_and_never_writes_sources(
        tmp_path: Path):
    root = _workspace(tmp_path)
    (root / "other.py").write_text("def gamma():\n    return 3\n",
                                   encoding="utf-8")
    (root / "readme.md").write_text("# hi\n", encoding="utf-8")
    (root / "song.mojo").write_text("fn main():\n    pass\n",
                                    encoding="utf-8")
    hidden = root / ".hidden"
    hidden.mkdir()
    (hidden / "secret.py").write_text("def hidden():\n    pass\n",
                                      encoding="utf-8")
    before = {p.name: p.read_text(encoding="utf-8")
              for p in root.glob("*.py")}
    cache = _cache(root)
    warm = cache.warm()
    assert warm.files_seen == 3  # mod.py, other.py, song.mojo
    assert warm.parse_filled == 2 and warm.graph_filled == 2
    assert warm.filled() == 4 and warm.hits == 0
    skipped_paths = {p for p, _r in warm.skipped}
    assert skipped_paths == {"song.mojo"}  # grammar-less, named
    assert cache.stats()["entries"] == 4
    warm2 = cache.warm()
    assert warm2.filled() == 0 and warm2.hits == 4
    after = {p.name: p.read_text(encoding="utf-8")
             for p in root.glob("*.py")}
    assert after == before  # warming never writes a source file


def test_warm_cap_is_named(tmp_path: Path):
    root = _workspace(tmp_path)
    (root / "other.py").write_text("def gamma():\n    return 3\n",
                                   encoding="utf-8")
    cache = _cache(root)
    warm = cache.warm(max_files=1)
    assert warm.files_seen == 1 and warm.capped is True
    with pytest.raises(ValueError, match="max_files"):
        cache.warm(max_files=0)


# -- the report surface ---------------------------------------------------------

def test_report_show_file_warm_clear(tmp_path: Path):
    root = _workspace(tmp_path)
    report = intelligence_cache_report(root)
    assert report.kind == "show" and report.status == "ok"
    assert report.totals() == (0, 0)
    assert report.per_kind() == {k: 0 for k in CACHE_KINDS}
    assert not (root / ".mythic").exists()  # show creates nothing
    report = intelligence_cache_report(root, "warm")
    assert report.warm_result is not None
    assert report.warm_result.files_seen == 1
    assert report.totals()[0] == 2
    report = intelligence_cache_report(root, "file", target="mod.py")
    assert report.file_state is not None
    assert report.file_state.state_for("parse") == "hit-ready"
    assert report.file_state.state_for("lsp") == "absent"
    report = intelligence_cache_report(root, "clear")
    assert report.cleared == 2 and report.totals() == (0, 0)
    with pytest.raises(ValueError, match="unknown mode"):
        intelligence_cache_report(root, "bogus")
    with pytest.raises(ValueError, match="needs its file"):
        intelligence_cache_report(root, "file")


def test_report_disabled_reads_and_writes_nothing(tmp_path: Path):
    root = _workspace(tmp_path)
    report = intelligence_cache_report(root, enabled=False)
    assert report.status == "disabled" and report.entries == []
    assert surface.enabled_from_config({}) is True
    assert surface.enabled_from_config(
        {"intelligence_cache": False}) is False
    assert surface.enabled_from_config(None) is True
    assert not (root / ".mythic").exists()


def test_parse_intelcache_args():
    assert parse_intelcache_args("") == {"action": "show"}
    assert parse_intelcache_args("show") == {"action": "show"}
    assert parse_intelcache_args("warm") == {"action": "warm"}
    assert parse_intelcache_args("clear") == {"action": "clear"}
    assert parse_intelcache_args("mod.py") == {
        "action": "file", "target": "mod.py"}
    with pytest.raises(ValueError):
        parse_intelcache_args("a.py b.py")


def test_format_and_render_use_the_reports_own_values(tmp_path: Path):
    root = _workspace(tmp_path)
    intelligence_cache_report(root, "warm")
    report = intelligence_cache_report(root)
    text = format_intelligence_cache_report(
        {"report": report.record(),
         "plain_explanation": PLAIN_EXPLANATION})
    assert "Intelligence cache (M-069)" in text
    assert "parse: 1" in text and "graph: 1" in text
    page = surface.render_markdown(report)
    n_entries, n_bytes = report.totals()
    assert f"**{n_entries} entr" in page
    assert f"**{n_bytes} bytes**" in page
    assert "`mod.py`" in page
    assert USAGE.startswith("Usage")


# -- surfaces -------------------------------------------------------------------

def _bare_agent(root: Path, config=None):
    from mythic_agent.agents.llm import Agent

    agent = Agent.__new__(Agent)
    agent.project_root = root
    agent.config = config or {}
    agent._session_store = None
    agent.session_id = None
    return agent


def test_agent_surfaces(tmp_path: Path):
    root = _workspace(tmp_path)
    agent = _bare_agent(root)
    status = agent.intelligence_cache("warm")
    assert status["report"]["kind"] == "warm"
    assert status["plain_explanation"] == PLAIN_EXPLANATION
    status = agent.intelligence_cache()
    assert status["report"]["stats"]["entries"] == 2
    status = agent.intelligence_cache("file", target="mod.py")
    assert status["report"]["file_state"]["states"]["parse"] == (
        "hit-ready")


def test_agent_respects_the_config_switch(tmp_path: Path):
    agent = _bare_agent(tmp_path, {"intelligence_cache": False})
    status = agent.intelligence_cache()
    assert status["report"]["status"] == "disabled"
    assert status["report"]["entries"] == []


def test_terminal_road(tmp_path: Path):
    from mythic_agent.terminal import _slash

    root = _workspace(tmp_path)
    agent = _bare_agent(root)
    handled, _, text = _slash(agent, "/intelcache warm")
    assert handled and "Intelligence cache (M-069)" in text
    handled, _, text = _slash(agent, "/intelcache mod.py")
    assert handled and "hit-ready" in text
    handled, _, text = _slash(agent, "/intelcache a.py b.py")
    assert handled and "Usage" in text


def test_tui_road(tmp_path: Path, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY

    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    agent = _bare_agent(_workspace(tmp_path))
    AGENT_REGISTRY["Primary"] = agent
    try:
        handler = CommandHandler.__new__(CommandHandler)
        handler._handle_intelcache("warm")
        handler._handle_intelcache("mod.py")
        handler._handle_intelcache("a.py b.py")
    finally:
        AGENT_REGISTRY.pop("Primary", None)
    text = "\n".join(kwargs.get("text", "")
                     for _event, kwargs in published)
    assert "Intelligence cache (M-069)" in text
    assert "hit-ready" in text
    assert "Usage" in text


def test_setting_lives_in_defaults_and_catalogue():
    import yaml

    root = Path(__file__).resolve().parents[1]
    defaults = yaml.safe_load(
        (root / "mythic_agent/data/config_defaults.yaml").read_text(
            encoding="utf-8"))
    assert defaults["intelligence_cache"] is True
    catalogue = yaml.safe_load(
        (root / "mythic_agent/data/config_catalog.yaml").read_text(
            encoding="utf-8"))
    entries = [s for s in catalogue["settings"]
               if s["name"] == "intelligence_cache"]
    assert len(entries) == 1
    assert entries[0]["id"] == "S-59"


def test_config_catalogue_carries_the_setting():
    from mythic_agent.core.config_catalog import load_catalog

    catalog = load_catalog()
    entry = [s for s in catalog.settings
             if s.name == "intelligence_cache"]
    assert len(entry) == 1
    assert entry[0].id == "S-59"


def test_gap_audit_has_no_m069_row_recorded():
    # Checked at build time (the house pattern): no census
    # gap row is owned by M-069, so no module_kind flip
    # exists to make for this slice.
    import yaml

    root = Path(__file__).resolve().parents[1]
    audit = yaml.safe_load(
        (root / "mythic_agent/data/gap_audit.yaml").read_text(
            encoding="utf-8"))
    assert [r for r in audit["rows"] if r["slice"] == "M-069"] == []
