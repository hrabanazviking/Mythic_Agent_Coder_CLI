"""M-082 — PR craft.

TIER: integration

Covers the M-082 surface:

* the pure layer (``mythic_agent.core.pr_craft``): a pull
  request fetched as data through one injectable gh runner
  seam, its review comments fetched and turned into tasks
  (one task per comment, place and author carried; a
  wordless review honestly makes no task), and the three
  draft kinds — PR, review (approve / comment / request
  changes, line notes riding in the review body), reply,
* the roadmap's own law, proven: a review pass posts only
  at the user's word — every post road (create, review,
  reply) refuses a draft with no recorded word BEFORE the
  runner is touched (the fake runner records zero calls),
  an armed draft posts through the runner with the built
  gh argv, and no record ever carries the word's text,
* ``Agent``: the gate status, ``set_pr_craft`` journaled
  as ``pr_craft_setting_changed`` (a failed save restoring
  the previous value and journaling the revert), fetches
  journaled, drafts prepared with nothing sent, posts
  journaled and gated, the gate off refusing fetches and
  posts and saying so,
* the surfaces: the terminal ``/prcraft`` and the TUI
  ``/prcraft`` (system-command road through the
  CommandHandler + chat-screen routing), which share the
  parser and formatters,
* the config contract: ``pr_craft`` ships in the defaults
  (True). Its M-009 catalogue entry (S-64) is a recorded
  integration delta for the coordinator — the parallel
  teams do not edit the shared catalogue.

No test in this file makes a live GitHub call: every road
runs over a fake runner that records its argv.
"""

from __future__ import annotations

import json

import pytest

from mythic_agent.core.pr_craft import (
    PLAIN_EXPLANATION,
    PR_CRAFT_SLICE,
    SETTING_KEY,
    VERDICTS,
    arm_pr_draft,
    arm_reply_draft,
    arm_review_draft,
    comments_to_tasks,
    enabled_from_config,
    fetch_pull_request,
    fetch_review_comments,
    format_pr_craft,
    format_pull_request,
    format_setting_change,
    format_tasks,
    parse_prcraft_args,
    parse_pull_request,
    parse_review_comments,
    post_pr,
    post_reply,
    post_review,
    prepare_pr,
    prepare_reply,
    prepare_review,
    set_enabled,
)
from mythic_agent.core.sessions import SessionStore

PR_PAYLOAD = {
    "number": 7, "title": "Add the forge bellows",
    "body": "Bellows for the forge.",
    "baseRefName": "main", "headRefName": "feature/bellows",
    "state": "OPEN", "isDraft": False,
    "url": "https://example.invalid/pr/7",
    "author": {"login": "volmarr"},
    "comments": [
        {"id": "c1", "author": {"login": "reviewer-a"},
         "body": "The handle needs a guard.",
         "path": "forge/bellows.py", "line": 42,
         "url": "https://example.invalid/pr/7#c1"},
        {"id": "c2", "author": {"login": "reviewer-b"},
         "body": "Overall shape looks right.",
         "url": "https://example.invalid/pr/7#c2"},
    ],
    "reviews": [
        {"id": "r1", "author": {"login": "reviewer-a"},
         "body": "Close — one guard short of ready.",
         "state": "CHANGES_REQUESTED"},
        {"id": "r2", "author": {"login": "reviewer-b"},
         "body": "", "state": "APPROVED"},
    ],
}

CREATED_PAYLOAD = {
    "number": 8, "url": "https://example.invalid/pr/8",
    "title": "Add the forge bellows", "state": "OPEN"}


class FakeRunner:
    """A fake gh road: records argv, answers canned data."""

    def __init__(self):
        self.calls = []

    def __call__(self, args):
        self.calls.append(list(args))
        if list(args[:2]) == ["pr", "view"]:
            return json.dumps(PR_PAYLOAD)
        if list(args[:2]) == ["pr", "create"]:
            return json.dumps(CREATED_PAYLOAD)
        return ""


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


class TestFetch:
    def test_slice_constants(self):
        assert PR_CRAFT_SLICE == "M-082"
        assert SETTING_KEY == "pr_craft"
        assert VERDICTS == ("approve", "comment", "request_changes")
        assert "posts only" in PLAIN_EXPLANATION
        assert "your word" in PLAIN_EXPLANATION

    def test_fetch_pr_as_data(self):
        runner = FakeRunner()
        pr = fetch_pull_request(runner, 7)
        assert runner.calls[0][:3] == ["pr", "view", "7"]
        assert pr.number == 7 and pr.title == "Add the forge bellows"
        assert pr.base == "main" and pr.head == "feature/bellows"
        assert pr.author == "volmarr" and pr.draft is False

    def test_parse_pr_from_a_string_author(self):
        payload = dict(PR_PAYLOAD, author="someone")
        pr = parse_pull_request(json.dumps(payload))
        assert pr.author == "someone"

    def test_fetch_refuses_a_bad_number_and_bad_json(self):
        runner = FakeRunner()
        with pytest.raises(ValueError, match="positive integer"):
            fetch_pull_request(runner, 0)
        assert runner.calls == []
        with pytest.raises(ValueError, match="not JSON"):
            parse_pull_request("this is not json")

    def test_comments_become_tasks_one_per_comment(self):
        runner = FakeRunner()
        comments = fetch_review_comments(runner, 7)
        tasks = comments_to_tasks(comments)
        # 2 comments + 1 review with words; the wordless
        # approval honestly makes no task.
        assert len(tasks) == 3
        first = tasks[0]
        assert first["task_id"] == "pr-7-comment-c1"
        assert first["state"] == "queued"
        assert first["kind"] == "review_comment"
        assert first["author"] == "reviewer-a"
        assert first["path"] == "forge/bellows.py"
        assert first["line"] == 42
        assert first["body"] == "The handle needs a guard."
        assert tasks[2]["comment_kind"] == "review"
        assert tasks[2]["pr_number"] == 7

    def test_parse_comments_directly(self):
        comments = parse_review_comments(json.dumps(PR_PAYLOAD), 7)
        assert [c.comment_id for c in comments] == ["c1", "c2", "r1"]


class TestDraftsAndGate:
    def test_prepare_pr_validates(self):
        draft = prepare_pr("T", "B", "main", "feat")
        assert draft.armed is False and draft.draft is False
        with pytest.raises(ValueError, match="title"):
            prepare_pr("  ", "B", "main", "feat")
        with pytest.raises(ValueError, match="base"):
            prepare_pr("T", "B", "", "feat")
        with pytest.raises(ValueError, match="head"):
            prepare_pr("T", "B", "main", " ")

    def test_unarmed_pr_post_refuses_before_the_runner(self):
        runner = FakeRunner()
        with pytest.raises(ValueError, match="user's word"):
            post_pr(runner, prepare_pr("T", "B", "main", "feat"))
        assert runner.calls == []

    def test_armed_pr_post_creates_through_the_runner(self):
        runner = FakeRunner()
        draft = arm_pr_draft(
            prepare_pr("Add the forge bellows", "Bellows.",
                       "main", "feature/bellows", draft=True),
            "open it")
        posted = post_pr(runner, draft)
        assert posted["number"] == 8
        args = runner.calls[0]
        assert args[:2] == ["pr", "create"]
        assert "--draft" in args and "feature/bellows" in args

    def test_arm_refuses_an_empty_word(self):
        with pytest.raises(ValueError, match="no word was given"):
            arm_pr_draft(prepare_pr("T", "B", "main", "feat"), "  ")
        with pytest.raises(ValueError, match="no word was given"):
            arm_review_draft(prepare_review(7, "approve", ""), "")
        with pytest.raises(ValueError, match="no word was given"):
            arm_reply_draft(prepare_reply(7, "c1", "Thanks."), None)

    def test_prepare_review_validates(self):
        with pytest.raises(ValueError, match="verdict"):
            prepare_review(7, "maybe", "words")
        with pytest.raises(ValueError, match="needs words"):
            prepare_review(7, "request_changes", "")
        with pytest.raises(ValueError, match="needs words"):
            prepare_review(7, "comment", "  ")
        approve = prepare_review(7, "approve", "")
        assert approve.verdict == "approve"
        with pytest.raises(ValueError, match="positive line"):
            prepare_review(7, "comment", "words",
                           notes=[("a.py", 0, "note")])
        with pytest.raises(ValueError, match="file and words"):
            prepare_review(7, "comment", "words",
                           notes=[("", 3, "note")])

    def test_line_notes_ride_in_the_review_body(self):
        draft = prepare_review(
            7, "request_changes", "One guard short.",
            notes=[("forge/bellows.py", 42, "Add a guard.")])
        body = draft.review_body()
        assert body.startswith("One guard short.")
        assert "forge/bellows.py:42" in body
        assert "Add a guard." in body

    def test_unarmed_review_post_refuses_before_the_runner(self):
        runner = FakeRunner()
        draft = prepare_review(7, "approve", "")
        with pytest.raises(ValueError, match="posts only"):
            post_review(runner, draft)
        assert runner.calls == []

    def test_armed_review_posts_with_the_verdict_flag(self):
        runner = FakeRunner()
        draft = arm_review_draft(
            prepare_review(7, "request_changes", "One guard short.",
                           notes=[("forge/bellows.py", 42, "Guard.")]),
            "post it")
        post_review(runner, draft)
        args = runner.calls[0]
        assert args[:3] == ["pr", "review", "7"]
        assert "--request-changes" in args
        body = args[args.index("--body") + 1]
        assert "forge/bellows.py:42" in body

    def test_armed_approve_without_words_posts_no_body(self):
        runner = FakeRunner()
        post_review(runner, arm_review_draft(
            prepare_review(7, "approve", ""), "yes"))
        assert runner.calls[0] == ["pr", "review", "7", "--approve"]

    def test_reply_draft_and_gate(self):
        runner = FakeRunner()
        with pytest.raises(ValueError, match="comment it answers"):
            prepare_reply(7, "", "Thanks.")
        with pytest.raises(ValueError, match="needs words"):
            prepare_reply(7, "c1", "")
        draft = prepare_reply(7, "c1", "Guard added — thank you.")
        with pytest.raises(ValueError, match="posts only"):
            post_reply(runner, draft)
        assert runner.calls == []
        post_reply(runner, arm_reply_draft(draft, "answer it"))
        assert runner.calls[0][:3] == ["pr", "comment", "7"]

    def test_records_never_carry_the_word(self):
        draft = arm_review_draft(
            prepare_review(7, "comment", "Words."), "post it")
        record = draft.post_record(None, False)
        assert record["armed"] is True
        assert "post it" not in json.dumps(record)
        assert "post it" not in json.dumps(draft.record(None, False))


class TestSettingAndSurface:
    def test_enabled_from_config(self):
        assert enabled_from_config({}) is True
        assert enabled_from_config({"pr_craft": False}) is False
        with pytest.raises(ValueError, match="true or false"):
            enabled_from_config({"pr_craft": "yes"})

    def test_set_enabled(self):
        value, change = set_enabled({}, False)
        assert value is False and change.before is True
        with pytest.raises(ValueError, match="already on"):
            set_enabled({}, True)
        with pytest.raises(ValueError, match="on or off"):
            set_enabled({}, "off")

    def test_parse_args(self):
        assert parse_prcraft_args("") == {"action": "show"}
        assert parse_prcraft_args("on") == {
            "action": "setting", "enabled": True}
        assert parse_prcraft_args("off") == {
            "action": "setting", "enabled": False}
        assert parse_prcraft_args("tasks 7") == {
            "action": "tasks", "number": 7}
        with pytest.raises(ValueError, match="Usage"):
            parse_prcraft_args("tasks zero")
        with pytest.raises(ValueError, match="Usage"):
            parse_prcraft_args("sideways")
        with pytest.raises(ValueError, match="positive integer"):
            parse_prcraft_args("tasks 0")

    def test_format_pull_request_and_tasks(self):
        pr = parse_pull_request(json.dumps(PR_PAYLOAD))
        text = format_pull_request(pr)
        assert "PR #7" in text and "feature/bellows -> main" in text
        tasks = comments_to_tasks(
            parse_review_comments(json.dumps(PR_PAYLOAD), 7))
        text = format_tasks(tasks)
        assert "3 comment(s)" in text
        assert "forge/bellows.py:42" in text
        assert format_tasks([]).startswith("No review comments")

    def test_format_pr_craft_shows_the_worked_example(self):
        text = format_pr_craft({})
        assert "PR craft (M-082)" in text
        assert "Setting: on (pr_craft)" in text
        assert "posts only at your word" in text
        assert "refuses" in text and "nothing was sent" in text
        assert "PR #8" in text
        assert "Usage: /prcraft" in text

    def test_format_setting_change(self):
        record = {"from": True, "to": False}
        assert format_setting_change(record) == "PR craft: on -> off."


class TestAgentGate:
    def test_status(self, agent):
        status = agent.pr_craft_status()
        assert status["enabled"] is True
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_set_without_session(self, agent):
        record = agent.set_pr_craft(False)
        assert record["journaled"] is False
        assert agent.config["pr_craft"] is False
        with pytest.raises(ValueError, match="already off"):
            agent.set_pr_craft(False)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_pr_craft(False)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "pr_craft_setting_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_pr_craft(False)
        assert agent.config.get("pr_craft") is not False
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["pr_craft_setting_changed",
                              "pr_craft_setting_reverted"]
        agent.close()


class TestAgentRoads:
    def test_fetch_pull_request(self, agent, tmp_path):
        runner = FakeRunner()
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.fetch_pull_request(7, runner=runner)
        assert record["number"] == 7
        assert record["title"] == "Add the forge bellows"
        assert record["journaled"] is True
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "pr_fetched" in types
        agent.close()

    def test_fetch_review_tasks(self, agent, tmp_path):
        runner = FakeRunner()
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        fetched = agent.fetch_review_tasks(7, runner=runner)
        assert fetched["count"] == 3
        assert fetched["tasks"][0]["task_id"] == "pr-7-comment-c1"
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "pr_review_tasks_fetched" in types
        agent.close()

    def test_prepare_drafts_send_nothing(self, agent):
        runner = FakeRunner()
        record = agent.prepare_pr_draft(
            "Add the forge bellows", "Bellows.", "main",
            "feature/bellows")
        assert record["type"] == "pr_draft_prepared"
        assert record["armed"] is False
        record = agent.prepare_review_draft(
            7, "request_changes", "One guard short.",
            notes=[("forge/bellows.py", 42, "Guard.")])
        assert record["type"] == "pr_review_draft_prepared"
        assert record["notes"] == 1
        record = agent.prepare_reply_draft(7, "c1", "Guard added.")
        assert record["type"] == "pr_reply_draft_prepared"
        assert runner.calls == []

    def test_post_pr_without_the_word_sends_nothing(self, agent):
        runner = FakeRunner()
        with pytest.raises(ValueError, match="user's own word"):
            agent.post_pr_draft("T", "B", "main", "feat",
                                runner=runner)
        assert runner.calls == []

    def test_post_pr_with_the_word(self, agent, tmp_path):
        runner = FakeRunner()
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.post_pr_draft(
            "Add the forge bellows", "Bellows.", "main",
            "feature/bellows", word="open it", runner=runner)
        assert record["type"] == "pr_posted"
        assert record["number"] == 8 and record["armed"] is True
        assert "open it" not in json.dumps(record)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "pr_posted" in types
        agent.close()

    def test_post_review_and_reply_with_the_word(
            self, agent, tmp_path):
        runner = FakeRunner()
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.post_review_draft(
            7, "comment", "Words.", word="post it", runner=runner)
        assert record["type"] == "pr_review_posted"
        record = agent.post_reply_draft(
            7, "c1", "Guard added.", word="answer it",
            runner=runner)
        assert record["type"] == "pr_reply_posted"
        assert [c[:2] for c in runner.calls] == [
            ["pr", "review"], ["pr", "comment"]]
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "pr_review_posted" in types
        assert "pr_reply_posted" in types
        agent.close()

    def test_post_review_without_the_word_sends_nothing(self, agent):
        runner = FakeRunner()
        with pytest.raises(ValueError, match="user's own word"):
            agent.post_review_draft(7, "approve", "", runner=runner)
        with pytest.raises(ValueError, match="user's own word"):
            agent.post_reply_draft(7, "c1", "Thanks.", runner=runner)
        assert runner.calls == []

    def test_gate_off_refuses_fetches_and_posts(self, agent):
        runner = FakeRunner()
        agent.set_pr_craft(False)
        with pytest.raises(ValueError, match="PR craft is off"):
            agent.fetch_pull_request(7, runner=runner)
        with pytest.raises(ValueError, match="PR craft is off"):
            agent.fetch_review_tasks(7, runner=runner)
        with pytest.raises(ValueError, match="PR craft is off"):
            agent.post_review_draft(7, "approve", "", word="yes",
                                    runner=runner)
        assert runner.calls == []


class TestTerminalSurface:
    def test_show_and_set(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/prcraft")
        assert "PR craft (M-082)" in text
        _, _, text = _slash(agent, "/prcraft off")
        assert "on -> off" in text
        assert agent.config["pr_craft"] is False
        _, _, text = _slash(agent, "/prcraft on")
        assert "off -> on" in text

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/prcraft sideways")
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


class TestPrCraftCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_prcraft("")
        assert "PR craft (M-082)" in _published_text(handler)

    def test_set_via_the_handler(self, handler, agent):
        handler._handle_prcraft("off")
        assert "on -> off" in _published_text(handler)
        assert agent.config["pr_craft"] is False

    def test_tasks_via_the_handler(self, handler, agent, monkeypatch):
        monkeypatch.setattr(
            agent, "fetch_review_tasks",
            lambda number, runner=None: {
                "pr_number": number, "count": 1, "journaled": False,
                "tasks": [{"task_id": "pr-7-comment-c1",
                           "state": "queued", "author": "reviewer-a",
                           "path": "forge/bellows.py", "line": 42,
                           "body": "The handle needs a guard."}]})
        handler._handle_prcraft("tasks 7")
        assert "pr-7-comment-c1" in _published_text(handler)

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_prcraft("sideways")
        assert "Usage" in _published_text(handler)


class TestChatScreenRouting:
    def test_prcraft_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/prcraft off", _FakeLog())
        assert calls == [("/prcraft", "off")]


class TestConfigContract:
    def test_defaults_ship_on(self):
        import yaml
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        defaults = yaml.safe_load(
            (root / "mythic_agent/data/config_defaults.yaml")
            .read_text(encoding="utf-8"))
        assert defaults["pr_craft"] is True
