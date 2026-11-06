"""M-084 — Multi-file change sets.

TIER: integration

Covers the M-084 surface:

* the pure layer (``mythic_agent.core.change_sets``): a
  change set as a named, reviewable unit across files —
  one edit per file, each in an M-071 concrete format,
  each file decided accept / reject on its own, the
  whole set planned in memory through M-071's unchanged
  strict appliers (one stale file refuses the whole set),
  and its test evidence carried as data with the verdict
  computed from the counts,
* the roadmap's own law, proven: rejecting one file
  never kills the rest — the accepted files apply, the
  rejected file's edit never lands; every file must be
  decided (an undecided file refuses the apply and is
  named); rejecting every file is an honest no-change
  outcome; a set with no evidence says so plainly,
* ``Agent``: the gate status, ``set_change_sets``
  journaled as ``change_set_setting_changed`` (a failed
  save restoring the previous value and journaling the
  revert), ``preview_change_set`` and ``apply_change_set``
  — the plan is atomic (a stale second file leaves the
  first file untouched), applied files ride the
  EditJournal road, and the set is journaled as
  ``change_set_applied`` under its name with its
  evidence; the gate off refuses a set apply and says so,
* the surfaces: the terminal ``/changeset`` and the TUI
  ``/changeset`` (system-command road through the
  CommandHandler + chat-screen routing), which share the
  parser and formatters,
* the config contract: ``change_sets`` ships in the
  defaults (True). Its M-009 catalogue entry (S-64) is a
  recorded integration delta for the coordinator — the
  hammer teams do not edit the shared catalogue.
"""

from __future__ import annotations

import pytest

from mythic_agent.core.change_sets import (
    CHANGE_SETS_SLICE,
    DECISIONS,
    PLAIN_EXPLANATION,
    SETTING_KEY,
    apply_change_set,
    attach_evidence,
    decide,
    enabled_from_config,
    format_change_set,
    format_change_sets,
    format_evidence,
    format_setting_change,
    make_edit,
    make_evidence,
    parse_changeset_args,
    set_enabled,
    start_change_set,
)
from mythic_agent.core.sessions import SessionStore

APP = "alpha = 1\nbeta = 2\n"
SEARCH = ("<<<<<<< SEARCH\nalpha = 1\n=======\nalpha = 10\n"
          ">>>>>>> REPLACE")
DIFF = "@@ -2,1 +2,1 @@\n-beta = 2\n+beta = 20"
EVIDENCE = {"command": "pytest tests/test_app.py -q",
            "passed": 12, "failed": 0, "skipped": 1,
            "log_ref": "logs/sample-tests.log"}


def sample_set(name="sample work"):
    return start_change_set(name, [
        make_edit("app.py", "search-replace", SEARCH),
        make_edit("notes.txt", "whole-file", "release notes\n")])


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


class TestBuild:
    def test_slice_and_decisions_constants(self):
        assert CHANGE_SETS_SLICE == "M-084"
        assert SETTING_KEY == "change_sets"
        assert DECISIONS == ("pending", "accept", "reject")
        assert "never kills" in PLAIN_EXPLANATION

    def test_a_set_starts_named_and_all_pending(self):
        change_set = sample_set()
        assert change_set.name == "sample work"
        assert change_set.undecided() == [0, 1]
        assert change_set.counts() == {
            "accepted": 0, "rejected": 0, "pending": 2}
        assert change_set.evidence is None

    def test_a_set_needs_a_name(self):
        with pytest.raises(ValueError, match="needs a name"):
            start_change_set("  ", [make_edit(
                "app.py", "whole-file", "x\n")])
        with pytest.raises(ValueError, match="needs a name"):
            start_change_set(None, [make_edit(
                "app.py", "whole-file", "x\n")])

    def test_a_set_needs_at_least_one_file(self):
        with pytest.raises(ValueError, match="at least one file"):
            start_change_set("empty", [])

    def test_one_file_one_edit(self):
        with pytest.raises(ValueError, match="twice"):
            start_change_set("dup", [
                make_edit("app.py", "whole-file", "x\n"),
                make_edit("app.py", "whole-file", "y\n")])

    def test_make_edit_validates_its_format(self):
        edit = make_edit("app.py", "unified-diff", DIFF)
        assert edit.format_id == "unified-diff"
        with pytest.raises(ValueError, match="architect"):
            make_edit("app.py", "architect", "plan only")
        with pytest.raises(ValueError):
            make_edit("app.py", "no-such-format", "x")
        with pytest.raises(ValueError, match="file path"):
            make_edit(" ", "whole-file", "x\n")
        with pytest.raises(ValueError, match="payload as text"):
            make_edit("app.py", "whole-file", None)

    def test_raw_tuples_are_not_edits(self):
        with pytest.raises(ValueError, match="file edits"):
            start_change_set("raw", [("app.py", "whole-file", "x")])


class TestDecisions:
    def test_decide_returns_a_new_set(self):
        change_set = sample_set()
        decided = decide(change_set, 0, "accept")
        assert change_set.decision(0) == "pending"
        assert decided.decision(0) == "accept"

    def test_decide_refuses_pending_unknown_and_bad_index(self):
        change_set = sample_set()
        with pytest.raises(ValueError, match="accept or reject"):
            decide(change_set, 0, "pending")
        with pytest.raises(ValueError, match="accept or reject"):
            decide(change_set, 0, "maybe")
        with pytest.raises(ValueError, match="no file"):
            decide(change_set, 7, "accept")

    def test_redeciding_replaces(self):
        change_set = decide(sample_set(), 0, "accept")
        change_set = decide(change_set, 0, "reject")
        assert change_set.decision(0) == "reject"


class TestEvidence:
    def test_verdict_is_computed_from_the_counts(self):
        passed = make_evidence("pytest -q", 12, 0, 1, "log.txt")
        assert passed.verdict == "passed"
        assert passed.total == 13
        assert make_evidence("pytest -q", 3, 2).verdict == "failed"
        assert make_evidence("pytest -q", 0, 0).verdict == \
            "no tests ran"

    def test_evidence_record_carries_everything(self):
        record = make_evidence(**EVIDENCE).record()
        assert record["command"] == EVIDENCE["command"]
        assert record["passed"] == 12 and record["failed"] == 0
        assert record["skipped"] == 1 and record["total"] == 13
        assert record["log_ref"] == "logs/sample-tests.log"
        assert record["verdict"] == "passed"

    def test_evidence_counts_must_be_honest_numbers(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            make_evidence("pytest -q", -1, 0)
        with pytest.raises(ValueError, match="whole number"):
            make_evidence("pytest -q", True, 0)
        with pytest.raises(ValueError, match="whole number"):
            make_evidence("pytest -q", "12", 0)
        with pytest.raises(ValueError, match="command that ran"):
            make_evidence(" ", 1, 0)

    def test_attach_returns_a_new_set_with_evidence(self):
        change_set = sample_set()
        attached = attach_evidence(
            change_set, make_evidence(**EVIDENCE))
        assert change_set.evidence is None
        assert attached.evidence.verdict == "passed"
        with pytest.raises(ValueError, match="evidence road"):
            attach_evidence(change_set, {"passed": 1})

    def test_absent_evidence_says_so_plainly(self):
        assert format_evidence(None) == \
            "Test evidence: none attached."
        text = format_evidence(make_evidence(**EVIDENCE))
        assert "passed" in text and "logs/sample-tests.log" in text


class TestApply:
    CURRENTS = {"app.py": APP, "notes.txt": None}

    def test_accept_all_applies_every_file(self):
        change_set = decide(decide(sample_set(), 0, "accept"),
                            1, "accept")
        new_texts, outcome = apply_change_set(
            change_set, self.CURRENTS)
        assert new_texts["app.py"].splitlines()[0] == "alpha = 10"
        assert new_texts["notes.txt"] == "release notes\n"
        assert outcome.applied == 2 and outcome.rejected == 0
        assert outcome.units == 2
        assert outcome.changed_files == 2 and outcome.changed is True

    def test_rejecting_one_file_never_kills_the_rest(self):
        change_set = decide(decide(sample_set(), 0, "accept"),
                            1, "reject")
        new_texts, outcome = apply_change_set(
            change_set, self.CURRENTS)
        assert "app.py" in new_texts
        assert "notes.txt" not in new_texts
        assert outcome.applied == 1 and outcome.rejected == 1

    def test_rejecting_everything_is_an_honest_no_change(self):
        change_set = decide(decide(sample_set(), 0, "reject"),
                            1, "reject")
        new_texts, outcome = apply_change_set(
            change_set, self.CURRENTS)
        assert new_texts == {}
        assert outcome.applied == 0 and outcome.rejected == 2
        assert outcome.changed is False

    def test_an_undecided_file_refuses_and_is_named(self):
        change_set = decide(sample_set(), 0, "accept")
        with pytest.raises(ValueError, match="notes.txt"):
            apply_change_set(change_set, self.CURRENTS)

    def test_one_stale_file_refuses_the_whole_set(self):
        change_set = start_change_set("two diffs", [
            make_edit("app.py", "unified-diff", DIFF),
            make_edit("other.py", "unified-diff", DIFF)])
        change_set = decide(decide(change_set, 0, "accept"),
                            1, "accept")
        currents = {"app.py": APP, "other.py": "gamma = 3\n"}
        with pytest.raises(ValueError, match="whole change set"):
            apply_change_set(change_set, currents)

    def test_a_rejected_stale_file_is_never_judged(self):
        change_set = start_change_set("one good one stale", [
            make_edit("app.py", "unified-diff", DIFF),
            make_edit("other.py", "unified-diff", DIFF)])
        change_set = decide(decide(change_set, 0, "accept"),
                            1, "reject")
        new_texts, outcome = apply_change_set(
            change_set, {"app.py": APP, "other.py": "gamma = 3\n"})
        assert new_texts["app.py"].splitlines()[1] == "beta = 20"
        assert outcome.rejected == 1

    def test_an_unchanged_accepted_file_is_not_counted_changed(self):
        change_set = start_change_set("no-op write", [
            make_edit("app.py", "whole-file", APP)])
        change_set = decide(change_set, 0, "accept")
        new_texts, outcome = apply_change_set(
            change_set, {"app.py": APP})
        assert outcome.applied == 1 and outcome.changed_files == 0
        assert outcome.changed is False

    def test_event_and_record_carry_name_counts_and_evidence(self):
        change_set = attach_evidence(
            decide(decide(sample_set(), 0, "accept"), 1, "reject"),
            make_evidence(**EVIDENCE))
        event = change_set.event()
        assert event["type"] == "change_set_applied"
        assert event["name"] == "sample work"
        assert event["accepted"] == 1 and event["rejected"] == 1
        assert event["evidence"]["verdict"] == "passed"
        record = change_set.record(None, False)
        assert record["journaled"] is False


class TestGateAndSurface:
    def test_gate_defaults_on_and_validates(self):
        assert enabled_from_config({}) is True
        assert enabled_from_config({"change_sets": False}) is False
        with pytest.raises(ValueError, match="true or false"):
            enabled_from_config({"change_sets": "yes"})

    def test_set_enabled(self):
        value, change = set_enabled({}, False)
        assert value is False and change.before is True
        with pytest.raises(ValueError, match="already on"):
            set_enabled({}, True)
        with pytest.raises(ValueError, match="on or off"):
            set_enabled({}, "off")

    def test_parse_args(self):
        assert parse_changeset_args("") == {"action": "show"}
        assert parse_changeset_args("on") == {
            "action": "setting", "enabled": True}
        assert parse_changeset_args("off") == {
            "action": "setting", "enabled": False}
        with pytest.raises(ValueError, match="Usage"):
            parse_changeset_args("sideways")

    def test_format_change_set_lists_files_decisions_evidence(self):
        text = format_change_set(sample_set())
        assert "app.py" in text and "notes.txt" in text
        assert "2 undecided" in text
        assert "Test evidence: none attached." in text
        attached = attach_evidence(
            sample_set(), make_evidence(**EVIDENCE))
        assert "verdict" not in format_change_set(attached)
        assert "passed" in format_change_set(attached)

    def test_format_change_sets_shows_the_worked_example(self):
        text = format_change_sets({})
        assert "Multi-file change sets (M-084)" in text
        assert "rejecting one file" in text
        assert "notes.txt was never created" in text
        assert "Setting: on (change_sets)" in text
        assert "Usage: /changeset" in text

    def test_format_setting_change(self):
        record = {"from": True, "to": False}
        assert format_setting_change(record) == \
            "Change sets: on -> off."


class TestAgentGate:
    def test_status(self, agent):
        status = agent.change_set_status()
        assert status["enabled"] is True
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_set_without_session(self, agent):
        record = agent.set_change_sets(False)
        assert record["journaled"] is False
        assert agent.config["change_sets"] is False
        with pytest.raises(ValueError, match="already off"):
            agent.set_change_sets(False)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_change_sets(False)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "change_set_setting_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_change_sets(False)
        assert agent.config.get("change_sets") is not False
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["change_set_setting_changed",
                              "change_set_setting_reverted"]
        agent.close()


class TestAgentApply:
    EDITS = [("app.py", "search-replace", SEARCH),
             ("notes.txt", "whole-file", "release notes\n")]

    def _seed(self, tmp_path):
        (tmp_path / "app.py").write_text(APP, encoding="utf-8")

    def test_preview_validates_and_writes_nothing(
            self, agent, tmp_path):
        self._seed(tmp_path)
        shown = agent.preview_change_set("sample work", self.EDITS)
        assert shown["name"] == "sample work"
        assert [f["path"] for f in shown["files"]] == \
            ["app.py", "notes.txt"]
        assert shown["evidence"] is None
        assert not (tmp_path / "notes.txt").exists()
        with pytest.raises(ValueError, match="architect"):
            agent.preview_change_set(
                "bad", [("app.py", "architect", "plan")])

    def test_apply_writes_every_accepted_file(
            self, agent, tmp_path):
        self._seed(tmp_path)
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.apply_change_set(
            "sample work", self.EDITS,
            [(0, "accept"), (1, "accept")], evidence=EVIDENCE)
        app_text = (tmp_path / "app.py").read_text(encoding="utf-8")
        assert app_text.splitlines()[0] == "alpha = 10"
        assert (tmp_path / "notes.txt").read_text(
            encoding="utf-8") == "release notes\n"
        assert record["applied"] == 2 and record["rejected"] == 0
        assert record["changed"] is True
        assert record["evidence"]["verdict"] == "passed"
        events = store.export(session_id)["events"]
        applied = [e for e in events
                   if e["type"] == "change_set_applied"]
        assert applied and applied[-1]["name"] == "sample work"
        assert applied[-1]["evidence"]["passed"] == 12
        from mythic_agent.core.edits import EditJournal
        assert "notes.txt" in EditJournal(tmp_path).undo()
        agent.close()

    def test_a_rejected_file_never_lands(self, agent, tmp_path):
        self._seed(tmp_path)
        record = agent.apply_change_set(
            "partial", self.EDITS, [(0, "accept"), (1, "reject")])
        assert (tmp_path / "app.py").read_text(
            encoding="utf-8").splitlines()[0] == "alpha = 10"
        assert not (tmp_path / "notes.txt").exists()
        assert record["applied"] == 1 and record["rejected"] == 1

    def test_all_rejected_writes_nothing(self, agent, tmp_path):
        self._seed(tmp_path)
        record = agent.apply_change_set(
            "nothing", self.EDITS, [(0, "reject"), (1, "reject")])
        assert (tmp_path / "app.py").read_text(
            encoding="utf-8") == APP
        assert not (tmp_path / "notes.txt").exists()
        assert record["applied"] == 0 and record["changed"] is False
        assert record["evidence"] is None

    def test_an_undecided_file_refuses_and_writes_nothing(
            self, agent, tmp_path):
        self._seed(tmp_path)
        with pytest.raises(ValueError, match="not decided"):
            agent.apply_change_set(
                "half", self.EDITS, [(0, "accept")])
        assert (tmp_path / "app.py").read_text(
            encoding="utf-8") == APP
        assert not (tmp_path / "notes.txt").exists()

    def test_a_stale_second_file_leaves_the_first_untouched(
            self, agent, tmp_path):
        self._seed(tmp_path)
        (tmp_path / "other.py").write_text(
            "gamma = 3\n", encoding="utf-8")
        edits = [("app.py", "unified-diff", DIFF),
                 ("other.py", "unified-diff", DIFF)]
        with pytest.raises(ValueError, match="whole change set"):
            agent.apply_change_set(
                "atomic", edits, [(0, "accept"), (1, "accept")])
        assert (tmp_path / "app.py").read_text(
            encoding="utf-8") == APP
        assert (tmp_path / "other.py").read_text(
            encoding="utf-8") == "gamma = 3\n"

    def test_gate_off_refuses_and_says_so(self, agent, tmp_path):
        self._seed(tmp_path)
        agent.set_change_sets(False)
        with pytest.raises(ValueError, match="change sets are off"):
            agent.apply_change_set(
                "gated", self.EDITS, [(0, "accept"), (1, "reject")])
        assert (tmp_path / "app.py").read_text(
            encoding="utf-8") == APP


class TestTerminalSurface:
    def test_show_and_set(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/changeset")
        assert "Multi-file change sets (M-084)" in text
        _, _, text = _slash(agent, "/changeset off")
        assert "on -> off" in text
        assert agent.config["change_sets"] is False
        _, _, text = _slash(agent, "/changeset on")
        assert "off -> on" in text

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/changeset sideways")
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


class TestChangesetCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_changeset("")
        assert "Multi-file change sets (M-084)" in \
            _published_text(handler)

    def test_set_via_the_handler(self, handler, agent):
        handler._handle_changeset("off")
        assert "on -> off" in _published_text(handler)
        assert agent.config["change_sets"] is False

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_changeset("sideways")
        assert "Usage" in _published_text(handler)


class TestChatScreenRouting:
    def test_changeset_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/changeset off", _FakeLog())
        assert calls == [("/changeset", "off")]


class TestConfigContract:
    def test_defaults_ship_on(self):
        import yaml
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        defaults = yaml.safe_load(
            (root / "mythic_agent/data/config_defaults.yaml")
            .read_text(encoding="utf-8"))
        assert defaults["change_sets"] is True
