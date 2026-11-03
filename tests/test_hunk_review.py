"""M-074 — Hunk-level review.

TIER: integration

Covers the M-074 surface:

* the pure layer (``mythic_agent.core.hunk_review``): a
  unified diff split into reviewable hunks as data (each
  hunk's stated counts proven against its body at split
  time), per-hunk decisions (accept / reject / edit),
  an edited hunk re-judged at edit time (its old side —
  context and removed lines — may never change; only its
  new side may), and the accepted subset applied through
  the unchanged M-071 strict applier,
* the roadmap's own law, proven: rejecting one hunk never
  kills the rest — the accepted hunks apply, the rejected
  hunk's change never lands; every hunk must be decided
  (a pending hunk refuses the apply and is named); a stale
  accepted hunk refuses and changes nothing; rejecting
  every hunk is an honest no-change outcome,
* ``Agent``: the gate status, ``set_hunk_review`` journaled
  as ``hunk_review_setting_changed`` (a failed save
  restoring the previous value and journaling the revert),
  ``split_for_review`` and ``apply_hunk_review`` — applied
  hunks ride the EditJournal road and the review is
  journaled as ``hunk_review_applied`` with its counts;
  the gate off refuses a reviewed apply and says so,
* the surfaces: the terminal ``/hunkreview`` and the TUI
  ``/hunkreview`` (system-command road through the
  CommandHandler + chat-screen routing), which share the
  parser and formatters,
* the config contract: ``hunk_review`` ships in the
  defaults (True) and is catalogued (M-009, S-63).
"""

from __future__ import annotations

import pytest

from mythic_agent.core.hunk_review import (
    DECISIONS,
    HUNK_REVIEW_SLICE,
    PLAIN_EXPLANATION,
    SETTING_KEY,
    apply_review,
    decide,
    edit_hunk,
    enabled_from_config,
    format_hunk_review,
    format_review,
    format_setting_change,
    parse_hunkreview_args,
    set_enabled,
    split_diff,
    start_review,
)
from mythic_agent.core.sessions import SessionStore

SOURCE = "alpha = 1\nbeta = 2\ngamma = 3\ndelta = 4\nepsilon = 5\n"
DIFF = (
    "@@ -1,2 +1,2 @@\n alpha = 1\n-beta = 2\n+beta = 20\n"
    "@@ -4,2 +4,2 @@\n delta = 4\n-epsilon = 5\n+epsilon = 50")
EDITED_BODY = [" delta = 4", "-epsilon = 5", "+epsilon = 55"]


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


class TestSplit:
    def test_slice_and_decisions_constants(self):
        assert HUNK_REVIEW_SLICE == "M-074"
        assert SETTING_KEY == "hunk_review"
        assert DECISIONS == ("pending", "accept", "reject", "edit")
        assert "never kills" in PLAIN_EXPLANATION

    def test_split_into_hunks_as_data(self):
        hunks = split_diff(DIFF)
        assert len(hunks) == 2
        assert hunks[0].old_start == 1 and hunks[0].old_count == 2
        assert hunks[0].old_side == ["alpha = 1", "beta = 2"]
        assert hunks[0].new_side == ["alpha = 1", "beta = 20"]
        assert hunks[1].header() == "@@ -4,2 +4,2 @@"
        assert hunks[1].to_diff().splitlines()[0] == "@@ -4,2 +4,2 @@"

    def test_split_skips_file_headers(self):
        payload = "--- a/app.py\n+++ b/app.py\n" + DIFF
        assert len(split_diff(payload)) == 2

    def test_split_refuses_a_malformed_diff(self):
        with pytest.raises(ValueError, match="not a unified diff"):
            split_diff("this is not a diff")
        with pytest.raises(ValueError, match="no diff hunk"):
            split_diff("")
        with pytest.raises(ValueError, match="counts do not match"):
            split_diff("@@ -1,3 +1,3 @@\n alpha = 1\n-beta = 2")

    def test_a_review_starts_all_pending(self):
        review = start_review(DIFF)
        assert review.undecided() == [0, 1]
        assert review.counts() == {"accepted": 0, "rejected": 0,
                                    "edited": 0, "pending": 2}


class TestDecisions:
    def test_decide_returns_a_new_review(self):
        review = start_review(DIFF)
        decided = decide(review, 0, "accept")
        assert review.decision(0) == "pending"
        assert decided.decision(0) == "accept"

    def test_decide_refuses_edit_and_pending_and_unknown(self):
        review = start_review(DIFF)
        with pytest.raises(ValueError, match="edited body"):
            decide(review, 0, "edit")
        with pytest.raises(ValueError, match="accept or reject"):
            decide(review, 0, "pending")
        with pytest.raises(ValueError, match="accept or reject"):
            decide(review, 0, "maybe")
        with pytest.raises(ValueError, match="no hunk"):
            decide(review, 7, "accept")

    def test_redeciding_clears_an_edit(self):
        review = edit_hunk(start_review(DIFF), 1, EDITED_BODY)
        assert review.decision(1) == "edit"
        review = decide(review, 1, "reject")
        assert review.decision(1) == "reject"
        assert review.hunk(1).new_side == ["delta = 4", "epsilon = 50"]


class TestEdit:
    def test_edit_changes_the_new_side_only(self):
        review = edit_hunk(start_review(DIFF), 1, EDITED_BODY)
        hunk = review.hunk(1)
        assert hunk.new_side == ["delta = 4", "epsilon = 55"]
        assert hunk.old_side == ["delta = 4", "epsilon = 5"]

    def test_edit_may_add_lines_and_counts_are_recomputed(self):
        body = [" delta = 4", "-epsilon = 5", "+epsilon = 55",
                "+zeta = 6"]
        review = edit_hunk(start_review(DIFF), 1, body)
        assert review.hunk(1).new_count == 3
        assert review.hunk(1).old_count == 2

    def test_edit_as_a_text_body(self):
        review = edit_hunk(start_review(DIFF), 1,
                           " delta = 4\n-epsilon = 5\n+epsilon = 55\n")
        assert review.hunk(1).new_side[-1] == "epsilon = 55"

    def test_edit_refuses_to_change_what_the_hunk_matches(self):
        with pytest.raises(ValueError, match="never what it matches"):
            edit_hunk(start_review(DIFF), 1,
                      [" delta = 4", "-epsilon = 99", "+epsilon = 55"])
        with pytest.raises(ValueError, match="never what it matches"):
            edit_hunk(start_review(DIFF), 1,
                      [" delta = 4!", "-epsilon = 5", "+epsilon = 55"])

    def test_edit_refuses_a_malformed_body(self):
        with pytest.raises(ValueError, match="not a diff body line"):
            edit_hunk(start_review(DIFF), 1, ["epsilon = 55"])
        with pytest.raises(ValueError, match="at least one line"):
            edit_hunk(start_review(DIFF), 1, [])


class TestApply:
    def test_accept_all_applies_every_hunk(self):
        review = decide(decide(start_review(DIFF), 0, "accept"),
                        1, "accept")
        new_text, outcome = apply_review(SOURCE, review)
        assert "beta = 20" in new_text and "epsilon = 50" in new_text
        assert outcome.applied == 2 and outcome.rejected == 0
        assert outcome.changed is True

    def test_rejecting_one_hunk_never_kills_the_rest(self):
        review = decide(decide(start_review(DIFF), 0, "accept"),
                        1, "reject")
        new_text, outcome = apply_review(SOURCE, review)
        assert "beta = 20" in new_text
        assert "epsilon = 5" in new_text and "epsilon = 50" not in new_text
        assert outcome.applied == 1 and outcome.rejected == 1

    def test_rejecting_the_first_hunk_leaves_the_second_judged(self):
        review = decide(decide(start_review(DIFF), 0, "reject"),
                        1, "accept")
        new_text, outcome = apply_review(SOURCE, review)
        assert "beta = 2" in new_text and "epsilon = 50" in new_text
        assert outcome.applied == 1 and outcome.rejected == 1

    def test_rejecting_everything_is_an_honest_no_change(self):
        review = decide(decide(start_review(DIFF), 0, "reject"),
                        1, "reject")
        new_text, outcome = apply_review(SOURCE, review)
        assert new_text == SOURCE
        assert outcome.applied == 0 and outcome.rejected == 2
        assert outcome.changed is False

    def test_a_pending_hunk_refuses_and_is_named(self):
        review = decide(start_review(DIFF), 0, "accept")
        with pytest.raises(ValueError, match="not decided"):
            apply_review(SOURCE, review)

    def test_an_edited_hunk_applies_its_edited_text(self):
        review = decide(start_review(DIFF), 0, "accept")
        review = edit_hunk(review, 1, EDITED_BODY)
        new_text, outcome = apply_review(SOURCE, review)
        assert "epsilon = 55" in new_text
        assert outcome.applied == 2 and outcome.edited == 1

    def test_a_stale_accepted_hunk_refuses(self):
        changed = SOURCE.replace("beta = 2", "beta = 99")
        review = decide(decide(start_review(DIFF), 0, "accept"),
                        1, "reject")
        with pytest.raises(ValueError, match="does not match"):
            apply_review(changed, review)

    def test_review_event_and_record_carry_the_counts(self):
        review = decide(decide(start_review(DIFF), 0, "accept"),
                        1, "reject")
        event = review.event()
        assert event["type"] == "hunk_review_applied"
        assert event["accepted"] == 1 and event["rejected"] == 1
        record = review.record(None, False)
        assert record["journaled"] is False


class TestGateAndSurface:
    def test_gate_defaults_on_and_validates(self):
        assert enabled_from_config({}) is True
        assert enabled_from_config({"hunk_review": False}) is False
        with pytest.raises(ValueError, match="true or false"):
            enabled_from_config({"hunk_review": "yes"})

    def test_set_enabled(self):
        value, change = set_enabled({}, False)
        assert value is False and change.before is True
        with pytest.raises(ValueError, match="already on"):
            set_enabled({}, True)
        with pytest.raises(ValueError, match="on or off"):
            set_enabled({}, "off")

    def test_parse_args(self):
        assert parse_hunkreview_args("") == {"action": "show"}
        assert parse_hunkreview_args("on") == {
            "action": "setting", "enabled": True}
        assert parse_hunkreview_args("off") == {
            "action": "setting", "enabled": False}
        with pytest.raises(ValueError, match="Usage"):
            parse_hunkreview_args("sideways")

    def test_format_review_lists_every_hunk(self):
        text = format_review(start_review(DIFF))
        assert "hunk 0" in text and "hunk 1" in text
        assert "2 undecided" in text

    def test_format_hunk_review_shows_the_worked_example(self):
        text = format_hunk_review({})
        assert "Hunk-level review (M-074)" in text
        assert "rejecting one hunk never kills the rest" in text
        assert "epsilon = 55" in text
        assert "Setting: on (hunk_review)" in text
        assert "Usage: /hunkreview" in text

    def test_format_setting_change(self):
        record = {"from": True, "to": False}
        assert format_setting_change(record) == "Hunk review: on -> off."


class TestAgentGate:
    def test_status(self, agent):
        status = agent.hunk_review_status()
        assert status["enabled"] is True
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_set_without_session(self, agent):
        record = agent.set_hunk_review(False)
        assert record["journaled"] is False
        assert agent.config["hunk_review"] is False
        with pytest.raises(ValueError, match="already off"):
            agent.set_hunk_review(False)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_hunk_review(False)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "hunk_review_setting_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_hunk_review(False)
        assert agent.config.get("hunk_review") is not False
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["hunk_review_setting_changed",
                              "hunk_review_setting_reverted"]
        agent.close()


class TestAgentReview:
    def test_split_for_review(self, agent):
        shown = agent.split_for_review(DIFF)
        assert shown["count"] == 2
        assert shown["hunks"][1]["old_side"] == ["delta = 4",
                                                 "epsilon = 5"]

    def test_accept_and_reject_writes_only_the_accepted(
            self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.apply_hunk_review(
            "app.py", DIFF, [(0, "accept"), (1, "reject")])
        text = target.read_text(encoding="utf-8")
        assert "beta = 20" in text and "epsilon = 5" in text
        assert record["applied"] == 1 and record["rejected"] == 1
        assert record["changed"] is True
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "hunk_review_applied" in types
        from mythic_agent.core.edits import EditJournal
        assert "app.py" in EditJournal(tmp_path).undo()
        agent.close()

    def test_an_edited_hunk_applies_through_the_agent(
            self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        record = agent.apply_hunk_review(
            "app.py", DIFF, [(0, "accept"), (1, "edit", EDITED_BODY)])
        assert "epsilon = 55" in target.read_text(encoding="utf-8")
        assert record["edited"] == 1 and record["applied"] == 2

    def test_all_rejected_writes_nothing(self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        record = agent.apply_hunk_review(
            "app.py", DIFF, [(0, "reject"), (1, "reject")])
        assert target.read_text(encoding="utf-8") == SOURCE
        assert record["applied"] == 0 and record["changed"] is False

    def test_an_undecided_hunk_refuses_and_writes_nothing(
            self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        with pytest.raises(ValueError, match="not decided"):
            agent.apply_hunk_review("app.py", DIFF, [(0, "accept")])
        assert target.read_text(encoding="utf-8") == SOURCE

    def test_gate_off_refuses_and_says_so(self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(SOURCE, encoding="utf-8")
        agent.set_hunk_review(False)
        with pytest.raises(ValueError, match="hunk review is off"):
            agent.apply_hunk_review(
                "app.py", DIFF, [(0, "accept"), (1, "reject")])
        assert target.read_text(encoding="utf-8") == SOURCE

    def test_a_missing_file_refuses(self, agent):
        with pytest.raises(ValueError, match="does not exist"):
            agent.apply_hunk_review(
                "nope.py", DIFF, [(0, "accept"), (1, "reject")])


class TestTerminalSurface:
    def test_show_and_set(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/hunkreview")
        assert "Hunk-level review (M-074)" in text
        _, _, text = _slash(agent, "/hunkreview off")
        assert "on -> off" in text
        assert agent.config["hunk_review"] is False
        _, _, text = _slash(agent, "/hunkreview on")
        assert "off -> on" in text

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/hunkreview sideways")
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


class TestHunkReviewCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_hunkreview("")
        assert "Hunk-level review (M-074)" in _published_text(handler)

    def test_set_via_the_handler(self, handler, agent):
        handler._handle_hunkreview("off")
        assert "on -> off" in _published_text(handler)
        assert agent.config["hunk_review"] is False

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_hunkreview("sideways")
        assert "Usage" in _published_text(handler)


class TestChatScreenRouting:
    def test_hunkreview_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/hunkreview off", _FakeLog())
        assert calls == [("/hunkreview", "off")]


class TestConfigContract:
    def test_defaults_ship_on(self):
        import yaml
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        defaults = yaml.safe_load(
            (root / "mythic_agent/data/config_defaults.yaml")
            .read_text(encoding="utf-8"))
        assert defaults["hunk_review"] is True

    def test_catalogued(self):
        from mythic_agent.core.config_catalog import load_catalog

        catalog = load_catalog()
        entries = {entry.name: entry for entry in catalog.settings}
        assert "hunk_review" in entries
        assert entries["hunk_review"].id == "S-63"
