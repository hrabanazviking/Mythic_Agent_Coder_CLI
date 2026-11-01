"""M-045 — Map in the TUI.

TIER: integration

Part III (Code Intelligence): M-044's repo map made visible —
browse it, pin files, see why the coder thinks a file
matters; the ranking is explainable.

These tests do not take the view's word for any of it:

* the view never re-ranks: its ranks, scores, and reasons
  are the M-044 map's own, carried verbatim (checked entry
  by entry against a map built directly),
* pinning is presentation: a pinned file is shown first but
  keeps its true rank and score, gains exactly one added
  reason (the pin reason), and its M-044 reasons are intact,
* a pin naming a file the build left out is explained in
  place — omitted over the budget, skipped with the build's
  own reason, or absent — never presented as an entry,
* one file's detail is its full account (rank, score
  arithmetic, definitions, references, reasons), resolvable
  by exact path or a unique name, with ambiguity refused,
* pins are a validated config setting (catalogued per
  M-009): malformed stored pins raise, a duplicate pin and
  an unpin of an unpinned file are refused plainly, and the
  agent's pin change is journal-shaped and save-guarded,
* the surfaces share one parser + formatters: the terminal
  ``/map`` road, the TUI system-command road, and the chat
  screen's routing all speak the same grammar.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mythic_agent.context.repo_map import build_repo_map
from mythic_agent.context.repo_map_view import (
    MAP_VIEW_SLICE,
    PINS_KEY,
    PLAIN_EXPLANATION,
    build_map_view,
    format_map_change,
    format_map_detail,
    format_map_pins,
    format_map_view,
    normalize_pin_path,
    parse_map_args,
    pin_file,
    pins_from_config,
    resolve_detail,
    unpin_file,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _ws(tmp_path):
    root = tmp_path / "ws"
    root.mkdir()
    (root / "core.py").write_text(
        "class Engine:\n"
        "    def start(self):\n"
        "        return 'on'\n"
        "\n"
        "def build_engine():\n"
        "    return Engine()\n")
    (root / "app.py").write_text(
        "def main():\n"
        "    engine = build_engine()\n"
        "    return engine.start()\n")
    (root / "lonely.py").write_text(
        "def unused_helper():\n"
        "    return 42\n")
    return root


# ---------------------------------------------------------------------------
# Pin paths and the stored pins
# ---------------------------------------------------------------------------

class TestPinPaths:
    def test_slice_and_key(self):
        assert MAP_VIEW_SLICE == "M-045"
        assert PINS_KEY == "repo_map_pins"
        assert "never changes a file's rank or score" in PLAIN_EXPLANATION

    def test_normalize_accepts_map_spelling(self):
        assert normalize_pin_path("core.py") == "core.py"
        assert normalize_pin_path(" pkg/mod.py ") == "pkg/mod.py"
        assert normalize_pin_path("./pkg/mod.py") == "pkg/mod.py"

    @pytest.mark.parametrize("bad", [
        "", "   ", "/abs/path.py", "../escape.py", "pkg/../../escape.py",
        "pkg\\mod.py", "C:/drive.py", None, 42,
    ])
    def test_normalize_refuses_unmappable_paths(self, bad):
        with pytest.raises(ValueError):
            normalize_pin_path(bad)

    def test_pins_absent_means_none(self):
        assert pins_from_config({}) == ()
        assert pins_from_config({PINS_KEY: []}) == ()

    def test_pins_round_trip_in_order(self):
        config = {PINS_KEY: ["b.py", "a.py"]}
        assert pins_from_config(config) == ("b.py", "a.py")

    @pytest.mark.parametrize("bad", [
        "core.py",                # not a list
        ["core.py", "core.py"],   # duplicate
        [""],                     # blank
        ["../escape.py"],         # escape
        [42],                     # not a path
    ])
    def test_malformed_stored_pins_raise(self, bad):
        with pytest.raises(ValueError):
            pins_from_config({PINS_KEY: bad})


class TestPinChanges:
    def test_pin_appends_without_mutating(self):
        config = {PINS_KEY: ["a.py"]}
        stored, change = pin_file(config, "b.py")
        assert stored == ["a.py", "b.py"]
        assert config[PINS_KEY] == ["a.py"]
        assert change.kind == "pinned" and change.path == "b.py"
        assert change.event() == {
            "type": "repo_map_pins_changed", "action": "pinned",
            "path": "b.py", "from": ["a.py"], "to": ["a.py", "b.py"]}
        record = change.record("sess-1", True)
        assert record["to"] == ["a.py", "b.py"]
        assert record["session_id"] == "sess-1"
        assert record["journaled"] is True

    def test_pin_duplicate_is_refused(self):
        with pytest.raises(ValueError, match="already pinned"):
            pin_file({PINS_KEY: ["a.py"]}, "a.py")

    def test_unpin_removes(self):
        stored, change = unpin_file({PINS_KEY: ["a.py", "b.py"]}, "a.py")
        assert stored == ["b.py"]
        assert change.kind == "unpinned"

    def test_unpin_unpinned_is_refused(self):
        with pytest.raises(ValueError, match="not pinned"):
            unpin_file({PINS_KEY: []}, "a.py")


# ---------------------------------------------------------------------------
# The view — never a second ranking
# ---------------------------------------------------------------------------

class TestView:
    def test_ranks_scores_reasons_are_the_maps_own(self, tmp_path):
        repo_map = build_repo_map(_ws(tmp_path), budget_tokens=10_000)
        view = build_map_view(repo_map, ())
        assert [e.path for e in view.entries] == [
            e.path for e in repo_map.entries]
        for view_entry, entry in zip(view.entries, repo_map.entries):
            assert view_entry.rank == repo_map.entries.index(entry) + 1
            assert view_entry.entry.score == entry.score
            assert view_entry.entry.pagerank == entry.pagerank
            assert view_entry.reasons == entry.reasons
            assert view_entry.pinned is False
        assert view.unmapped_pins == ()

    def test_pinned_first_with_true_rank_and_score(self, tmp_path):
        repo_map = build_repo_map(_ws(tmp_path), budget_tokens=10_000)
        last = repo_map.entries[-1]
        view = build_map_view(repo_map, (last.path,))
        first = view.entries[0]
        assert first.path == last.path and first.pinned is True
        assert first.rank == len(repo_map.entries)
        assert first.entry.score == last.score
        assert first.entry.pagerank == last.pagerank
        # The map's own reasons intact, exactly one reason added.
        assert first.reasons[:-1] == last.reasons
        assert "pinned by you" in first.reasons[-1]
        assert "rank and score" in first.reasons[-1]
        # The rest keep rank order among themselves.
        rest = [e.path for e in view.entries[1:]]
        assert rest == [e.path for e in repo_map.entries[:-1]]

    def test_unmapped_pin_omitted_over_budget(self, tmp_path):
        repo_map = build_repo_map(_ws(tmp_path), budget_tokens=1)
        assert repo_map.entries == ()
        assert set(repo_map.omitted) == {"core.py", "app.py", "lonely.py"}
        view = build_map_view(repo_map, ("core.py",))
        assert len(view.unmapped_pins) == 1
        unmapped = view.unmapped_pins[0]
        assert unmapped.path == "core.py" and unmapped.state == "omitted"
        assert "budget" in unmapped.reason

    def test_unmapped_pin_skipped_with_build_reason(self, tmp_path):
        root = _ws(tmp_path)
        (root / "spell.mojo").write_text("fn main():\n    pass\n")
        repo_map = build_repo_map(root, budget_tokens=10_000)
        assert [s.path for s in repo_map.skipped] == ["spell.mojo"]
        view = build_map_view(repo_map, ("spell.mojo",))
        unmapped = view.unmapped_pins[0]
        assert unmapped.state == "skipped"
        assert repo_map.skipped[0].reason in unmapped.reason

    def test_unmapped_pin_absent(self, tmp_path):
        repo_map = build_repo_map(_ws(tmp_path), budget_tokens=10_000)
        view = build_map_view(repo_map, ("ghost.py",))
        unmapped = view.unmapped_pins[0]
        assert unmapped.state == "absent"
        assert "no such mappable file" in unmapped.reason

    def test_view_record_shape(self, tmp_path):
        repo_map = build_repo_map(_ws(tmp_path), budget_tokens=10_000)
        record = build_map_view(repo_map, ("core.py",)).record()
        assert record["slice"] == "M-045"
        assert record["pins"] == ["core.py"]
        assert record["entries"][0]["pinned"] is True
        assert record["entries"][0]["rank"] >= 1


# ---------------------------------------------------------------------------
# One file's detail
# ---------------------------------------------------------------------------

class TestDetail:
    def test_mapped_detail_is_the_full_account(self, tmp_path):
        repo_map = build_repo_map(_ws(tmp_path), budget_tokens=10_000)
        detail = resolve_detail(repo_map, (), "core.py")
        assert detail.state == "mapped"
        assert detail.entry.path == "core.py"
        assert {d.name for d in detail.entry.entry.definitions} >= {
            "Engine", "build_engine"}
        assert "app.py" in detail.entry.entry.references_in

    def test_detail_resolves_a_unique_name(self, tmp_path):
        root = _ws(tmp_path)
        sub = root / "pkg"
        sub.mkdir()
        (sub / "widget.py").write_text("def widget():\n    return 1\n")
        repo_map = build_repo_map(root, budget_tokens=10_000)
        detail = resolve_detail(repo_map, (), "widget.py")
        assert detail.state == "mapped"
        assert detail.path == "pkg/widget.py"

    def test_detail_ambiguous_name_is_refused(self, tmp_path):
        root = _ws(tmp_path)
        for name in ("a", "b"):
            sub = root / name
            sub.mkdir()
            (sub / "util.py").write_text(
                f"def util_{name}():\n    return 1\n")
        repo_map = build_repo_map(root, budget_tokens=10_000)
        with pytest.raises(ValueError, match="more than one file"):
            resolve_detail(repo_map, (), "util.py")

    def test_detail_omitted_skipped_absent(self, tmp_path):
        root = _ws(tmp_path)
        (root / "spell.mojo").write_text("fn main():\n    pass\n")
        full = build_repo_map(root, budget_tokens=10_000)
        assert resolve_detail(full, (), "spell.mojo").state == "skipped"
        assert resolve_detail(full, (), "ghost.py").state == "absent"
        tiny = build_repo_map(root, budget_tokens=1)
        detail = resolve_detail(tiny, (), "core.py")
        assert detail.state == "omitted"
        assert detail.entry is None

    def test_detail_for_a_pin_carries_the_pin(self, tmp_path):
        repo_map = build_repo_map(_ws(tmp_path), budget_tokens=10_000)
        detail = resolve_detail(repo_map, ("lonely.py",), "lonely.py")
        assert detail.state == "mapped"
        assert detail.entry.pinned is True


# ---------------------------------------------------------------------------
# Parser + formatters
# ---------------------------------------------------------------------------

class TestSurfaceText:
    def test_parser_grammar(self):
        assert parse_map_args("") == {
            "action": "list", "query": "", "path": None}
        assert parse_map_args(None) == {
            "action": "list", "query": "", "path": None}
        assert parse_map_args("fix the parser") == {
            "action": "list", "query": "fix the parser", "path": None}
        assert parse_map_args("show core.py") == {
            "action": "detail", "query": "", "path": "core.py"}
        assert parse_map_args("pin core.py")["action"] == "pin"
        assert parse_map_args("unpin core.py")["action"] == "unpin"
        assert parse_map_args("pins")["action"] == "pins"

    @pytest.mark.parametrize("bad", [
        "show", "pin", "unpin", "pins please", "show a b.py",
    ])
    def test_parser_usage_errors(self, bad):
        with pytest.raises(ValueError, match="Usage: /map"):
            parse_map_args(bad)

    def test_parser_non_text_is_refused(self):
        with pytest.raises(ValueError, match="must be text"):
            parse_map_args(42)

    def test_format_view_carries_reasons_and_pins(self, tmp_path):
        repo_map = build_repo_map(_ws(tmp_path), budget_tokens=10_000)
        status = {"view": build_map_view(repo_map, ("core.py",)).record()}
        text = format_map_view(status)
        assert "Repo map (M-045)" in text
        assert "core.py [pinned]" in text
        assert "PageRank" in text
        assert PLAIN_EXPLANATION in text

    def test_format_detail_carries_the_account(self, tmp_path):
        repo_map = build_repo_map(_ws(tmp_path), budget_tokens=10_000)
        detail = resolve_detail(repo_map, (), "core.py")
        text = format_map_detail({"detail": detail.record()})
        assert "rank #" in text
        assert "class Engine:" in text
        assert "Referenced by: app.py" in text
        assert "Why the coder thinks it matters:" in text

    def test_format_detail_unmapped_is_plain(self, tmp_path):
        repo_map = build_repo_map(_ws(tmp_path), budget_tokens=10_000)
        detail = resolve_detail(repo_map, (), "ghost.py")
        text = format_map_detail({"detail": detail.record()})
        assert "ghost.py — absent" in text

    def test_format_pins_and_change(self):
        assert "No files are pinned" in format_map_pins({"pins": []})
        text = format_map_pins({"pins": ["core.py"]})
        assert "core.py" in text and PLAIN_EXPLANATION in text
        pinned = format_map_change({
            "kind": "pinned", "path": "core.py", "session_id": None})
        assert pinned.startswith("Pinned core.py")
        unpinned = format_map_change({
            "kind": "unpinned", "path": "core.py", "session_id": "s-1"})
        assert unpinned.startswith("Unpinned core.py")
        assert "session s-1" in unpinned


# ---------------------------------------------------------------------------
# The catalogue contract (M-009): the pins setting is catalogued
# ---------------------------------------------------------------------------

class TestCatalogue:
    def test_pins_setting_in_defaults_and_catalogue(self):
        import yaml

        defaults = yaml.safe_load(
            (REPO_ROOT / "mythic_agent/data/config_defaults.yaml")
            .read_text(encoding="utf-8"))
        assert defaults[PINS_KEY] == []
        from mythic_agent.core.config_catalog import load_catalog
        assert PINS_KEY in load_catalog().setting_names()


# ---------------------------------------------------------------------------
# The agent
# ---------------------------------------------------------------------------

def _seed_agent_workspace(agent):
    root = Path(agent.project_root)
    (root / "core.py").write_text(
        "class Engine:\n"
        "    def start(self):\n"
        "        return 'on'\n"
        "\n"
        "def build_engine():\n"
        "    return Engine()\n")
    (root / "app.py").write_text(
        "def main():\n"
        "    engine = build_engine()\n"
        "    return engine.start()\n")
    return root


class TestAgent:
    def test_status_matches_the_pure_layer(self, agent):
        _seed_agent_workspace(agent)
        status = agent.repo_map_status()
        repo_map = build_repo_map(agent.project_root)
        view = build_map_view(repo_map, ())
        assert status["view"]["entries"] == view.record()["entries"]
        assert status["plain_explanation"] == PLAIN_EXPLANATION

    def test_detail_and_pins(self, agent):
        _seed_agent_workspace(agent)
        detail = agent.repo_map_detail("core.py")
        assert detail["detail"]["state"] == "mapped"
        assert detail["detail"]["entry"]["path"] == "core.py"
        assert agent.repo_map_pins()["pins"] == []

    def test_pin_unpin_round_trip(self, agent):
        _seed_agent_workspace(agent)
        record = agent.pin_repo_map_file("app.py")
        assert record["kind"] == "pinned"
        assert agent.config[PINS_KEY] == ["app.py"]
        assert agent.repo_map_pins()["pins"] == ["app.py"]
        status = agent.repo_map_status()
        assert status["view"]["entries"][0]["path"] == "app.py"
        assert status["view"]["entries"][0]["pinned"] is True
        record = agent.unpin_repo_map_file("app.py")
        assert record["kind"] == "unpinned"
        assert agent.repo_map_pins()["pins"] == []

    def test_pin_missing_file_is_refused(self, agent):
        _seed_agent_workspace(agent)
        with pytest.raises(ValueError, match="no such file"):
            agent.pin_repo_map_file("ghost.py")
        assert agent.repo_map_pins()["pins"] == []

    def test_pin_duplicate_is_refused(self, agent):
        _seed_agent_workspace(agent)
        agent.pin_repo_map_file("core.py")
        with pytest.raises(ValueError, match="already pinned"):
            agent.pin_repo_map_file("core.py")


# ---------------------------------------------------------------------------
# Surfaces — terminal + TUI command road + chat screen routing
# ---------------------------------------------------------------------------

class TestTerminalSurface:
    def test_browse_show_pin_flow(self, agent):
        from mythic_agent.terminal import _slash

        _seed_agent_workspace(agent)
        _, _, text = _slash(agent, "/map")
        assert "Repo map (M-045)" in text
        assert "core.py" in text
        _, _, text = _slash(agent, "/map show core.py")
        assert "rank #" in text
        _, _, text = _slash(agent, "/map pin app.py")
        assert text.startswith("Pinned app.py")
        _, _, text = _slash(agent, "/map pins")
        assert "app.py" in text
        _, _, text = _slash(agent, "/map unpin app.py")
        assert text.startswith("Unpinned app.py")

    def test_usage_error_is_plain(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/map show")
        assert text.startswith("Usage: /map")


@pytest.fixture()
def handler(agent, monkeypatch):
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


def _published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestMapCommand:
    def test_browse_and_detail(self, handler, agent):
        _seed_agent_workspace(agent)
        handler._handle_map("")
        text = _published_text(handler)
        assert "Repo map (M-045)" in text
        handler.published.clear()
        handler._handle_map("show core.py")
        assert "rank #" in _published_text(handler)

    def test_pin_flow(self, handler, agent):
        _seed_agent_workspace(agent)
        handler._handle_map("pin app.py")
        assert "Pinned app.py" in _published_text(handler)
        assert agent.repo_map_pins()["pins"] == ["app.py"]


class TestChatScreenRouting:
    def test_map_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/map show core.py", _FakeLog())
        assert calls == [("/map", "show core.py")]
