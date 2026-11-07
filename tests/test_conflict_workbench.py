"""M-081 — Conflict workbench.

TIER: integration

Covers the M-081 surface:

* the pure layer (``mythic_agent.core.conflict_workbench``):
  conflict markers parsed into regions as data (two-way
  and diff3 forms), intent summaries derived mechanically
  from real commit data and real diff counts (never
  invented — a deleted side, a missing base and a missing
  commit each stated plainly), per-region decisions
  (ours / theirs / both / edit), an edit judged at edit
  time (marker-carrying text refuses), and a resolution
  that refuses while any place is pending and refuses
  any resolved text still carrying a marker,
* real conflicts manufactured in throwaway git repos —
  a merge conflict and a rebase conflict — proven:
  detection names the operation, the conflicted file,
  its regions, and both sides' intent summarised from
  the actual commits (subjects + line counts against
  the base),
* ``Agent``: the gate status, ``set_conflict_workbench``
  journaled (save failure restores + journals the
  revert), ``conflict_workbench_view`` over a real
  conflict, and ``resolve_conflict`` — the resolution
  rides the EditJournal road, is staged, is verified
  against the real index (the file leaves the unmerged
  list), and is journaled as
  ``conflict_resolution_applied``; the gate off refuses,
* the surfaces: terminal ``/conflicts`` and the TUI
  ``/conflicts`` sharing one parser and formatters,
* the config contract: ``conflict_workbench`` ships in
  the defaults (True). Its M-009 catalogue entry is a
  recorded integration delta (see TEAM_LOG.md) — the
  catalogue is a shared inventory surface the campaign
  coordinator regenerates at banking.
"""

from __future__ import annotations

import subprocess

import pytest

from mythic_agent.core.conflict_workbench import (
    CHOICES,
    CONFLICT_SLICE,
    PLAIN_EXPLANATION,
    SETTING_KEY,
    ConflictFile,
    Workbench,
    apply_resolution,
    decide_resolution,
    detect_workbench,
    edit_resolution,
    enabled_from_config,
    format_conflict_workbench,
    format_setting_change,
    format_workbench,
    parse_conflict_regions,
    parse_conflicts_args,
    set_enabled,
    start_resolution,
    summarise_side,
)
from mythic_agent.core.sessions import SessionStore

CONFLICTED = (
    "title = 'Guide'\n<<<<<<< HEAD\nprice = 10\n=======\n"
    "price = 12\n>>>>>>> pricing\nend = True\n")
BASE = "title = 'Guide'\nprice = 9\nend = True\n"


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, check=True).stdout


def make_repo(root):
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "test@example.com")
    git(root, "config", "user.name", "Workbench Tester")
    (root / "guide.py").write_text(BASE, encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-m", "Base guide")


def merge_conflict(root):
    """A real merge conflict: main says 10, pricing says 12."""
    make_repo(root)
    git(root, "checkout", "-b", "pricing")
    (root / "guide.py").write_text(
        BASE.replace("price = 9", "price = 12"), encoding="utf-8")
    git(root, "commit", "-am", "Raise the guide price")
    git(root, "checkout", "main")
    (root / "guide.py").write_text(
        BASE.replace("price = 9", "price = 10"), encoding="utf-8")
    git(root, "commit", "-am", "Set the guide price")
    result = subprocess.run(
        ["git", "-C", str(root), "merge", "pricing"],
        capture_output=True, text=True)
    assert result.returncode != 0
    return root


def rebase_conflict(root):
    """A real rebase conflict: the branch is replayed onto main."""
    make_repo(root)
    git(root, "checkout", "-b", "pricing")
    (root / "guide.py").write_text(
        BASE.replace("price = 9", "price = 12"), encoding="utf-8")
    git(root, "commit", "-am", "Raise the guide price")
    git(root, "checkout", "main")
    (root / "guide.py").write_text(
        BASE.replace("price = 9", "price = 10"), encoding="utf-8")
    git(root, "commit", "-am", "Set the guide price")
    git(root, "checkout", "pricing")
    result = subprocess.run(
        ["git", "-C", str(root), "rebase", "main"],
        capture_output=True, text=True)
    assert result.returncode != 0
    return root


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


def sample_file():
    return ConflictFile(
        path="guide.py", regions=parse_conflict_regions(CONFLICTED),
        ours_intent="ours summary", theirs_intent="theirs summary",
        content=CONFLICTED)


class TestParse:
    def test_constants(self):
        assert CONFLICT_SLICE == "M-081"
        assert SETTING_KEY == "conflict_workbench"
        assert CHOICES == ("pending", "ours", "theirs", "both", "edit")
        assert "never invented" in PLAIN_EXPLANATION

    def test_regions_as_data(self):
        regions = parse_conflict_regions(CONFLICTED)
        assert len(regions) == 1
        assert regions[0].ours == ("price = 10",)
        assert regions[0].theirs == ("price = 12",)
        assert regions[0].ours_label == "HEAD"
        assert regions[0].theirs_label == "pricing"

    def test_diff3_base_section(self):
        text = ("a\n<<<<<<< HEAD\nx\n||||||| base\nb\n=======\n"
                "y\n>>>>>>> other\nz\n")
        regions = parse_conflict_regions(text)
        assert regions[0].base == ("b",)
        assert regions[0].ours == ("x",) and regions[0].theirs == ("y",)

    def test_no_markers_no_regions_and_unterminated_raises(self):
        assert parse_conflict_regions("plain\ntext\n") == ()
        with pytest.raises(ValueError, match="never closes"):
            parse_conflict_regions("<<<<<<< HEAD\nx\n")


class TestIntent:
    def test_summary_is_the_commit_and_the_counts(self):
        summary = summarise_side(
            "ours", ("aaaaaaa1", "Set the guide price", "Volmarr"),
            "price = 9\n", "price = 10\n")
        assert "aaaaaaa" in summary
        assert "'Set the guide price'" in summary
        assert "by Volmarr" in summary
        assert "+1 -1" in summary

    def test_deleted_side_missing_base_missing_commit_stated(self):
        assert "deleted the file" in summarise_side(
            "theirs", ("bbbbbbb2", "Drop it", "Volmarr"),
            "x\n", None)
        assert "no common base" in summarise_side(
            "ours", ("aaaaaaa1", "Add it", "Volmarr"), None, "x\n")
        assert "no commit recorded" in summarise_side(
            "ours", None, "x\n", "y\n")


class TestResolution:
    def test_each_choice_resolves(self):
        cf = sample_file()
        for choice, expected in (("ours", "price = 10"),
                                 ("theirs", "price = 12")):
            res = decide_resolution(start_resolution(cf), 0, choice)
            text, outcome = apply_resolution(CONFLICTED, res)
            assert expected in text and outcome.changed is True
        res = decide_resolution(start_resolution(cf), 0, "both")
        text, _ = apply_resolution(CONFLICTED, res)
        assert "price = 10" in text and "price = 12" in text

    def test_edit_resolves_with_edited_text(self):
        res = edit_resolution(start_resolution(sample_file()), 0,
                              ["price = 11"])
        text, outcome = apply_resolution(CONFLICTED, res)
        assert "price = 11" in text and outcome.applied == 1

    def test_pending_refuses_and_is_named(self):
        with pytest.raises(ValueError, match="not decided"):
            apply_resolution(CONFLICTED, start_resolution(sample_file()))

    def test_edit_carrying_a_marker_refuses_at_edit_time(self):
        with pytest.raises(ValueError, match="conflict marker"):
            edit_resolution(start_resolution(sample_file()), 0,
                            ["<<<<<<< HEAD", "price = 11"])

    def test_decide_refuses_edit_pending_and_unknown(self):
        res = start_resolution(sample_file())
        with pytest.raises(ValueError, match="edited text"):
            decide_resolution(res, 0, "edit")
        with pytest.raises(ValueError, match="ours, theirs, or both"):
            decide_resolution(res, 0, "pending")
        with pytest.raises(ValueError, match="no conflicted place"):
            decide_resolution(res, 5, "ours")

    def test_redeciding_clears_an_edit(self):
        res = edit_resolution(start_resolution(sample_file()), 0,
                              ["price = 11"])
        res = decide_resolution(res, 0, "ours")
        text, _ = apply_resolution(CONFLICTED, res)
        assert "price = 10" in text

    def test_counts_and_event(self):
        res = decide_resolution(start_resolution(sample_file()), 0, "theirs")
        assert res.counts()["theirs"] == 1
        event = res.event()
        assert event["type"] == "conflict_resolution_applied"
        assert event["path"] == "guide.py"


class TestDetectRealRepos:
    def test_merge_conflict_detected_with_real_intent(self, tmp_path):
        root = merge_conflict(tmp_path / "repo")
        workbench = detect_workbench(root)
        assert workbench.operation == "merge"
        assert [f.path for f in workbench.files] == ["guide.py"]
        cf = workbench.files[0]
        assert cf.region_count == 1
        assert cf.regions[0].ours == ("price = 10",)
        assert cf.regions[0].theirs == ("price = 12",)
        # Intent comes from the actual commits on each side.
        assert "'Set the guide price'" in cf.ours_intent
        assert "'Raise the guide price'" in cf.theirs_intent
        assert "+1 -1" in cf.ours_intent and "+1 -1" in cf.theirs_intent
        assert "Workbench Tester" in cf.ours_intent

    def test_rebase_conflict_detected(self, tmp_path):
        root = rebase_conflict(tmp_path / "repo")
        workbench = detect_workbench(root)
        assert workbench.operation == "rebase"
        assert [f.path for f in workbench.files] == ["guide.py"]
        assert workbench.files[0].region_count == 1

    def test_clean_repo_and_non_repo_are_honest(self, tmp_path):
        make_repo(tmp_path / "clean")
        workbench = detect_workbench(tmp_path / "clean")
        assert workbench.files == ()
        assert detect_workbench(tmp_path / "nope").operation == \
            "not-a-repository"
        assert "No conflicts" in format_workbench(workbench)


class TestGateAndSurface:
    def test_gate_defaults_on_and_validates(self):
        assert enabled_from_config({}) is True
        assert enabled_from_config({"conflict_workbench": False}) is False
        with pytest.raises(ValueError, match="true or false"):
            enabled_from_config({"conflict_workbench": "yes"})

    def test_set_enabled(self):
        value, change = set_enabled({}, False)
        assert value is False and change.before is True
        with pytest.raises(ValueError, match="already on"):
            set_enabled({}, True)
        with pytest.raises(ValueError, match="on or off"):
            set_enabled({}, "off")

    def test_parse_args(self):
        assert parse_conflicts_args("") == {"action": "show"}
        assert parse_conflicts_args("on") == {
            "action": "setting", "enabled": True}
        assert parse_conflicts_args("off") == {
            "action": "setting", "enabled": False}
        with pytest.raises(ValueError, match="Usage"):
            parse_conflicts_args("sideways")

    def test_format_workbench_lists_intent_and_regions(self):
        text = format_workbench(Workbench(
            operation="merge", files=(sample_file(),)))
        assert "guide.py" in text and "ours summary" in text
        assert "theirs summary" in text and "price = 10" in text

    def test_format_conflict_workbench_worked_example(self):
        text = format_conflict_workbench({})
        assert "Conflict workbench (M-081)" in text
        assert "Setting: on (conflict_workbench)" in text
        assert "'Set the guide price'" in text
        assert "price = 12" in text and "price = 11" in text
        assert "Usage: /conflicts" in text

    def test_format_setting_change(self):
        assert format_setting_change({"from": True, "to": False}) == \
            "Conflict workbench: on -> off."


class TestAgentGate:
    def test_status(self, agent):
        status = agent.conflict_workbench_status()
        assert status["enabled"] is True
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_set_without_session(self, agent):
        record = agent.set_conflict_workbench(False)
        assert record["journaled"] is False
        assert agent.config["conflict_workbench"] is False
        with pytest.raises(ValueError, match="already off"):
            agent.set_conflict_workbench(False)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_conflict_workbench(False)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "conflict_workbench_setting_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_conflict_workbench(False)
        assert agent.config.get("conflict_workbench") is not False
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["conflict_workbench_setting_changed",
                              "conflict_workbench_setting_reverted"]
        agent.close()


@pytest.fixture()
def conflict_agent(agent, tmp_path, monkeypatch):
    """An agent whose workspace is a real merge-conflicted repo."""
    root = merge_conflict(tmp_path / "repo")
    monkeypatch.setattr(agent, "project_root", root)
    return agent, root


class TestAgentResolve:
    def test_view_shows_the_real_conflict(self, conflict_agent):
        agent, _root = conflict_agent
        view = agent.conflict_workbench_view()
        assert view["operation"] == "merge"
        assert view["conflicted"] is True
        assert view["files"][0]["path"] == "guide.py"
        assert "'Set the guide price'" in view["files"][0]["ours_intent"]
        assert "'Raise the guide price'" in \
            view["files"][0]["theirs_intent"]

    def test_resolve_theirs_journals_stages_and_verifies(
            self, conflict_agent, tmp_path):
        agent, root = conflict_agent
        store = store_for(root)
        session_id = agent.attach_session(store)
        record = agent.resolve_conflict("guide.py", [(0, "theirs")])
        text = (root / "guide.py").read_text(encoding="utf-8")
        assert "price = 12" in text and "<<<<<<<" not in text
        assert record["applied"] == 1 and record["verified"] is True
        # Tested against the real index: no longer unmerged, and
        # the resolution is staged.
        assert git(root, "diff", "--name-only", "--diff-filter=U") == ""
        assert "guide.py" in git(root, "diff", "--cached", "--name-only")
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "conflict_resolution_applied" in types
        from mythic_agent.core.edits import EditJournal
        assert "guide.py" in EditJournal(root).undo()
        agent.close()

    def test_resolve_with_an_edit(self, conflict_agent):
        agent, root = conflict_agent
        record = agent.resolve_conflict(
            "guide.py", [(0, "edit", ["price = 11"])])
        assert "price = 11" in (root / "guide.py").read_text(
            encoding="utf-8")
        assert record["verified"] is True

    def test_pending_refuses_and_writes_nothing(self, conflict_agent):
        agent, root = conflict_agent
        before = (root / "guide.py").read_text(encoding="utf-8")
        with pytest.raises(ValueError, match="not decided"):
            agent.resolve_conflict("guide.py", [])
        assert (root / "guide.py").read_text(encoding="utf-8") == before

    def test_unconflicted_file_refuses(self, conflict_agent):
        agent, _root = conflict_agent
        with pytest.raises(ValueError, match="not a conflicted file"):
            agent.resolve_conflict("other.py", [(0, "ours")])

    def test_gate_off_refuses_and_says_so(self, conflict_agent):
        agent, root = conflict_agent
        agent.set_conflict_workbench(False)
        with pytest.raises(ValueError, match="conflict workbench is off"):
            agent.resolve_conflict("guide.py", [(0, "ours")])
        assert "<<<<<<<" in (root / "guide.py").read_text(
            encoding="utf-8")


class TestTerminalSurface:
    def test_show_and_set(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/conflicts")
        assert "Conflict workbench (M-081)" in text
        _, _, text = _slash(agent, "/conflicts off")
        assert "on -> off" in text
        assert agent.config["conflict_workbench"] is False
        _, _, text = _slash(agent, "/conflicts on")
        assert "off -> on" in text

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/conflicts sideways")
        assert "Usage" in text


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


class TestConflictsCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_conflicts("")
        assert "Conflict workbench (M-081)" in _published_text(handler)

    def test_set_via_the_handler(self, handler, agent):
        handler._handle_conflicts("off")
        assert "on -> off" in _published_text(handler)
        assert agent.config["conflict_workbench"] is False

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_conflicts("sideways")
        assert "Usage" in _published_text(handler)


class TestChatScreenRouting:
    def test_conflicts_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/conflicts off", _FakeLog())
        assert calls == [("/conflicts", "off")]


class TestConfigContract:
    def test_defaults_ship_on(self):
        import yaml
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        defaults = yaml.safe_load(
            (root / "mythic_agent/data/config_defaults.yaml")
            .read_text(encoding="utf-8"))
        assert defaults["conflict_workbench"] is True
