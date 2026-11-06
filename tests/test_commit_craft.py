"""M-080 — Commit craft.

TIER: integration

Covers the M-080 surface:

* the pure layer (``mythic_agent.core.commit_craft``):
  a multi-file working diff split into its files with
  every hunk judged by the M-074 hunk layer, the files
  grouped by concern (code / tests / docs / config),
  and each group's message drafted from its own actual
  diff (verb, names, and counts all read off the diff),
* the house rules as pure judgements, proven: any
  force spelling, force refspec, or deletion refspec
  refuses; a diverged remote refuses (never
  force-push); an up-to-date remote is an honest
  no-send; ls-remote verification proves a move and
  refuses an unmoved or wrong remote,
* the M-078 seam: the auto-commit trigger is reported
  honestly as not yet available (DEPENDS-ON-M-078),
* ``Agent``: the gate status, ``set_commit_craft``
  journaled as ``commit_craft_setting_changed`` (a
  failed save restoring the previous value and
  journaling the revert), ``plan_commit_split``,
  ``commit_craft_group`` — one concern committed at a
  time in a throwaway repo, the rest left in the
  working tree — and ``push_with_house_rules`` against
  a local file:// remote only: fetch + remote-diff
  first, a landed push verified by ls-remote, a
  diverged remote refused with the remote untouched,
* the surfaces: the terminal ``/commitcraft`` and the
  TUI ``/commitcraft`` (system-command road through
  the CommandHandler + chat-screen routing), which
  share the parser and formatters,
* the config contract: ``commit_craft`` ships in the
  defaults (True). Its M-009 catalogue entry (S-64) is
  a pending inventory delta recorded in TEAM_LOG.md —
  the catalogue is a shared surface the coordinator
  regenerates at integration.

Every git test runs in a throwaway repo under
tmp_path; every push test uses a local bare repo as
its remote. The real origin is never touched.
"""

from __future__ import annotations

import subprocess

import pytest

from mythic_agent.core.commit_craft import (
    AUTO_COMMIT_SLICE,
    COMMIT_CRAFT_SLICE,
    CONCERNS,
    PLAIN_EXPLANATION,
    SETTING_KEY,
    auto_commit_trigger,
    classify_concern,
    collect_working_diff,
    draft_message,
    draft_subject,
    enabled_from_config,
    format_commit_craft,
    format_commit_record,
    format_plan,
    format_push_record,
    format_setting_change,
    judge_push,
    parse_commitcraft_args,
    plan_commits,
    set_enabled,
    split_files,
    validate_push_args,
    verify_remote_moved,
)
from mythic_agent.core.sessions import SessionStore

DIFF = (
    "diff --git a/app.py b/app.py\n"
    "--- a/app.py\n"
    "+++ b/app.py\n"
    "@@ -1,2 +1,2 @@\n"
    " alpha = 1\n"
    "-beta = 2\n"
    "+beta = 20\n"
    "diff --git a/tests/test_app.py b/tests/test_app.py\n"
    "--- a/tests/test_app.py\n"
    "+++ b/tests/test_app.py\n"
    "@@ -1,1 +1,1 @@\n"
    "-assert beta == 2\n"
    "+assert beta == 20\n"
    "diff --git a/NOTES.md b/NOTES.md\n"
    "--- a/NOTES.md\n"
    "+++ b/NOTES.md\n"
    "@@ -1,1 +1,1 @@\n"
    "-beta is 2\n"
    "+beta is 20")

NEW_FILE_DIFF = (
    "diff --git a/fresh.py b/fresh.py\n"
    "new file mode 100644\n"
    "--- /dev/null\n"
    "+++ b/fresh.py\n"
    "@@ -0,0 +1,2 @@\n"
    "+one = 1\n"
    "+two = 2")

DELETED_FILE_DIFF = (
    "diff --git a/old.py b/old.py\n"
    "deleted file mode 100644\n"
    "--- a/old.py\n"
    "+++ /dev/null\n"
    "@@ -1,1 +0,0 @@\n"
    "-gone = 1")


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True, capture_output=True, text=True).stdout.strip()


def make_repo(repo):
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "craft@example.com")
    git(repo, "config", "user.name", "Commit Craft Test")
    return repo


def seed_repo(repo):
    make_repo(repo)
    (repo / "app.py").write_text(
        "alpha = 1\nbeta = 2\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_app.py").write_text(
        "assert beta == 2\n", encoding="utf-8")
    (repo / "NOTES.md").write_text("beta is 2\n", encoding="utf-8")
    # The agent fixture keeps its session state under state/;
    # a real repo would ignore it, and the split must not see it.
    (repo / ".gitignore").write_text("state/\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "seed")
    return repo


def dirty_repo(repo):
    seed_repo(repo)
    (repo / "app.py").write_text(
        "alpha = 1\nbeta = 20\n", encoding="utf-8")
    (repo / "tests" / "test_app.py").write_text(
        "assert beta == 20\n", encoding="utf-8")
    (repo / "NOTES.md").write_text("beta is 20\n", encoding="utf-8")
    return repo


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


class TestClassify:
    def test_constants(self):
        assert COMMIT_CRAFT_SLICE == "M-080"
        assert SETTING_KEY == "commit_craft"
        assert AUTO_COMMIT_SLICE == "M-078"
        assert CONCERNS == ("code", "tests", "docs", "config")
        assert "never force-push" in PLAIN_EXPLANATION

    def test_classify_concern(self):
        assert classify_concern("mythic_agent/core/x.py") == "code"
        assert classify_concern("tests/test_x.py") == "tests"
        assert classify_concern("src/test_utils.py") == "tests"
        assert classify_concern("pkg/util_test.py") == "tests"
        assert classify_concern("docs/GUIDE.md") == "docs"
        assert classify_concern("README.md") == "docs"
        assert classify_concern("LICENSE") == "docs"
        assert classify_concern("mythic_agent/data/x.yaml") == "config"
        assert classify_concern("pyproject.toml") == "config"
        assert classify_concern("settings.json") == "config"


class TestSplitFiles:
    def test_split_into_files_with_judged_hunks(self):
        files = split_files(DIFF)
        assert [f.path for f in files] == [
            "app.py", "tests/test_app.py", "NOTES.md"]
        assert len(files[0].hunks) == 1
        assert files[0].added == 1 and files[0].removed == 1
        assert files[0].hunks[0].new_side == ["alpha = 1", "beta = 20"]

    def test_bare_header_diff_also_splits(self):
        files = split_files(
            "--- a/app.py\n+++ b/app.py\n"
            "@@ -1,1 +1,1 @@\n-old\n+new")
        assert len(files) == 1 and files[0].path == "app.py"

    def test_new_and_deleted_files(self):
        new = split_files(NEW_FILE_DIFF)[0]
        assert new.is_new and new.added == 2 and new.removed == 0
        gone = split_files(DELETED_FILE_DIFF)[0]
        assert gone.is_deleted and gone.removed == 1

    def test_binary_file_carries_no_hunks(self):
        files = split_files(
            "diff --git a/logo.png b/logo.png\n"
            "Binary files a/logo.png and b/logo.png differ")
        assert files[0].binary is True and files[0].hunks == ()

    def test_a_malformed_hunk_refuses_the_split(self):
        with pytest.raises(ValueError, match="counts do not match"):
            split_files(
                "diff --git a/app.py b/app.py\n"
                "--- a/app.py\n+++ b/app.py\n"
                "@@ -1,3 +1,3 @@\n alpha = 1\n-beta = 2")

    def test_not_a_diff_refuses(self):
        with pytest.raises(ValueError, match="not a unified diff"):
            split_files("just some prose")


class TestPlanAndDraft:
    def test_plan_groups_by_concern_in_order(self):
        plan = plan_commits(DIFF)
        assert [g.concern for g in plan.groups] == [
            "code", "tests", "docs"]
        record = plan.record()
        assert record["files"] == 3
        assert record["added"] == 3 and record["removed"] == 3

    def test_untracked_files_join_as_new(self):
        plan = plan_commits(DIFF, untracked=(("fresh.py", 12),))
        code = plan.group("code")
        assert [f.path for f in code.files] == ["app.py", "fresh.py"]
        fresh = code.files[1]
        assert fresh.is_new and fresh.added == 12

    def test_an_empty_change_refuses_the_plan(self):
        with pytest.raises(ValueError, match="nothing to commit"):
            plan_commits("")

    def test_a_missing_group_is_named(self):
        plan = plan_commits(DIFF)
        with pytest.raises(ValueError, match="no 'config' group"):
            plan.group("config")

    def test_draft_subject_verbs_come_from_the_diff(self):
        plan = plan_commits(DIFF)
        assert draft_subject(plan.group("code")) == \
            "Update code: app.py"
        new_plan = plan_commits(NEW_FILE_DIFF)
        assert draft_subject(new_plan.group("code")) == \
            "Add code: fresh.py"
        gone_plan = plan_commits(DELETED_FILE_DIFF)
        assert draft_subject(gone_plan.group("code")) == \
            "Remove code: old.py"

    def test_draft_subject_counts_the_rest(self):
        payload = "".join(
            f"diff --git a/f{i}.py b/f{i}.py\n"
            f"--- a/f{i}.py\n+++ b/f{i}.py\n"
            f"@@ -1,1 +1,1 @@\n-x = {i}\n+x = {i}0\n"
            for i in range(5))
        subject = draft_subject(plan_commits(payload).group("code"))
        assert subject == "Update code: f0.py, f1.py, f2.py, and 2 more"

    def test_draft_message_carries_the_diff_evidence(self):
        message = draft_message(plan_commits(DIFF).group("tests"))
        lines = message.splitlines()
        assert lines[0] == "Update tests: test_app.py"
        assert "- tests/test_app.py (+1 -1)" in lines
        assert "M-080" in lines[-1]
        new_message = draft_message(
            plan_commits(NEW_FILE_DIFF).group("code"))
        assert "(new)" in new_message


class TestPushDiscipline:
    def test_the_house_push_args_pass(self):
        validate_push_args(
            ["push", "origin", "HEAD:refs/heads/main"])

    @pytest.mark.parametrize("bad", [
        "--force", "--force-with-lease", "--force-if-includes",
        "-f", "--mirror", "--delete",
    ])
    def test_force_spellings_refuse(self, bad):
        with pytest.raises(ValueError, match="never force-push|not a push"):
            validate_push_args(["push", "origin", bad])

    def test_a_force_refspec_refuses(self):
        with pytest.raises(ValueError, match="never force-push"):
            validate_push_args(
                ["push", "origin", "+HEAD:refs/heads/main"])

    def test_a_deletion_refspec_refuses(self):
        with pytest.raises(ValueError, match="deletion refspec"):
            validate_push_args(
                ["push", "origin", ":refs/heads/main"])

    def test_judge_push(self):
        assert judge_push("", None, False).kind == "no-local-head"
        up = judge_push("aaa", "aaa", True)
        assert up.kind == "up-to-date" and up.allowed is False
        new = judge_push("aaa", None, False)
        assert new.kind == "new-branch" and new.allowed is True
        ff = judge_push("bbb", "aaa", True)
        assert ff.kind == "fast-forward" and ff.allowed is True
        diverged = judge_push("bbb", "ccc", False)
        assert diverged.kind == "diverged"
        assert diverged.allowed is False
        assert "never force-push" in diverged.reason

    def test_verify_remote_moved(self):
        moved = verify_remote_moved("aaa", "bbb", "bbb")
        assert moved.verified is True and moved.kind == "moved"
        wrong = verify_remote_moved("aaa", "ccc", "bbb")
        assert wrong.verified is False and wrong.kind == "not-landed"
        still = verify_remote_moved("bbb", "bbb", "bbb")
        assert still.verified is False and still.kind == "unchanged"

    def test_the_m078_seam_is_honest(self):
        trigger = auto_commit_trigger()
        assert trigger["slice"] == "M-078"
        assert trigger["available"] is False
        assert "never commits on its own" in trigger["note"]


class TestGateAndSurface:
    def test_gate_defaults_on_and_validates(self):
        assert enabled_from_config({}) is True
        assert enabled_from_config({"commit_craft": False}) is False
        with pytest.raises(ValueError, match="true or false"):
            enabled_from_config({"commit_craft": "yes"})

    def test_set_enabled(self):
        value, change = set_enabled({}, False)
        assert value is False and change.before is True
        with pytest.raises(ValueError, match="already on"):
            set_enabled({}, True)
        with pytest.raises(ValueError, match="on or off"):
            set_enabled({}, "off")

    def test_parse_args(self):
        assert parse_commitcraft_args("") == {"action": "show"}
        assert parse_commitcraft_args("on") == {
            "action": "setting", "enabled": True}
        assert parse_commitcraft_args("off") == {
            "action": "setting", "enabled": False}
        assert parse_commitcraft_args("plan") == {"action": "plan"}
        assert parse_commitcraft_args("push") == {"action": "push"}
        assert parse_commitcraft_args("commit tests") == {
            "action": "commit", "concern": "tests"}
        with pytest.raises(ValueError, match="one of"):
            parse_commitcraft_args("commit sideways")
        with pytest.raises(ValueError, match="Usage"):
            parse_commitcraft_args("sideways")

    def test_format_plan_lists_every_group(self):
        text = format_plan(plan_commits(DIFF).record())
        assert "[code] Update code: app.py" in text
        assert "[tests] Update tests: test_app.py" in text
        assert "[docs] Update docs: NOTES.md" in text

    def test_format_commit_craft_shows_the_worked_example(self):
        text = format_commit_craft({})
        assert "Commit craft (M-080)" in text
        assert "splits into 3 commits by concern" in text
        assert "never force-push" in text
        assert "Setting: on (commit_craft)" in text
        assert "Usage: /commitcraft" in text

    def test_format_setting_change(self):
        record = {"from": True, "to": False}
        assert format_setting_change(record) == \
            "Commit craft: on -> off."

    def test_format_commit_and_push_records(self):
        commit = {"concern": "code", "sha": "a" * 40,
                  "subject": "Update code: app.py",
                  "files": ["app.py"], "added": 1, "removed": 1}
        assert "Update code: app.py" in format_commit_record(commit)
        landed = {"pushed": True, "remote": "origin",
                  "branch": "main", "before": "a" * 40,
                  "after": "b" * 40, "verdict": {"reason": "x"}}
        assert "verified by ls-remote" in format_push_record(landed)
        unsent = {"pushed": False, "remote": "origin",
                  "branch": "main", "before": None, "after": None,
                  "verdict": {"reason": "nothing to push"}}
        assert "not sent" in format_push_record(unsent)


class TestCollector:
    def test_a_non_repo_refuses(self, tmp_path):
        with pytest.raises(ValueError, match="not a git repository"):
            collect_working_diff(tmp_path)

    def test_collects_a_diff_and_untracked(self, tmp_path):
        repo = dirty_repo(tmp_path / "work")
        (repo / "fresh.py").write_text(
            "one = 1\ntwo = 2\n", encoding="utf-8")
        diff_text, untracked, _warnings = collect_working_diff(repo)
        files = split_files(diff_text)
        assert {f.path for f in files} == {
            "app.py", "tests/test_app.py", "NOTES.md"}
        assert untracked == (("fresh.py", 2),)


class TestAgentGate:
    def test_status(self, agent):
        status = agent.commit_craft_status()
        assert status["enabled"] is True
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["auto_commit_trigger"]["available"] is False

    def test_set_without_session(self, agent):
        record = agent.set_commit_craft(False)
        assert record["journaled"] is False
        assert agent.config["commit_craft"] is False
        with pytest.raises(ValueError, match="already off"):
            agent.set_commit_craft(False)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_commit_craft(False)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "commit_craft_setting_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_commit_craft(False)
        assert agent.config.get("commit_craft") is not False
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["commit_craft_setting_changed",
                              "commit_craft_setting_reverted"]
        agent.close()


class TestAgentCommit:
    def test_plan_commit_split(self, agent, tmp_path):
        dirty_repo(tmp_path)
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.plan_commit_split()
        assert record["concerns"] == ["code", "tests", "docs"]
        assert record["files"] == 3
        code = record["groups"][0]
        assert code["draft_subject"] == "Update code: app.py"
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "commit_craft_planned" in types
        agent.close()

    def test_commit_one_group_leaves_the_rest(self, agent, tmp_path):
        dirty_repo(tmp_path)
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.commit_craft_group("code")
        assert record["subject"] == "Update code: app.py"
        assert git(tmp_path, "log", "-1", "--format=%s") == \
            "Update code: app.py"
        assert git(tmp_path, "show", "--name-only",
                   "--format=", "HEAD") == "app.py"
        status = git(tmp_path, "status", "--porcelain")
        assert "tests/test_app.py" in status
        assert "NOTES.md" in status
        assert "app.py" not in status.split("tests/")[0]
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "commit_craft_committed" in types
        agent.close()

    def test_groups_commit_in_turns(self, agent, tmp_path):
        dirty_repo(tmp_path)
        agent.commit_craft_group("tests")
        agent.commit_craft_group("docs")
        agent.commit_craft_group("code")
        assert git(tmp_path, "status", "--porcelain") == ""
        subjects = git(tmp_path, "log", "--format=%s", "-3")
        assert subjects.splitlines() == [
            "Update code: app.py", "Update docs: NOTES.md",
            "Update tests: test_app.py"]

    def test_commit_with_a_given_message(self, agent, tmp_path):
        dirty_repo(tmp_path)
        record = agent.commit_craft_group("code", message="my words")
        assert record["subject"] == "my words"
        assert git(tmp_path, "log", "-1", "--format=%s") == "my words"

    def test_a_clean_tree_refuses_the_plan(self, agent, tmp_path):
        seed_repo(tmp_path)
        with pytest.raises(ValueError, match="nothing to commit"):
            agent.plan_commit_split()

    def test_gate_off_refuses_a_commit(self, agent, tmp_path):
        dirty_repo(tmp_path)
        agent.set_commit_craft(False)
        with pytest.raises(ValueError, match="commit craft is off"):
            agent.commit_craft_group("code")
        assert git(tmp_path, "log", "-1", "--format=%s") == "seed"


class TestAgentPush:
    def _repo_with_remote(self, agent, tmp_path):
        bare = tmp_path / "origin.git"
        bare.mkdir()
        git(bare, "init", "--bare", "-b", "main")
        dirty_repo(tmp_path)
        git(tmp_path, "remote", "add", "origin", str(bare))
        agent.commit_craft_group("code")
        return bare

    def test_first_push_creates_and_verifies(self, agent, tmp_path):
        bare = self._repo_with_remote(agent, tmp_path)
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.push_with_house_rules()
        head = git(tmp_path, "rev-parse", "HEAD")
        assert record["pushed"] is True
        assert record["before"] is None
        assert record["after"] == head
        assert record["verify"]["verified"] is True
        assert git(bare, "rev-parse", "refs/heads/main") == head
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "commit_craft_pushed" in types
        agent.close()

    def test_an_up_to_date_push_is_an_honest_no_send(
            self, agent, tmp_path):
        self._repo_with_remote(agent, tmp_path)
        agent.push_with_house_rules()
        record = agent.push_with_house_rules()
        assert record["pushed"] is False
        assert record["verdict"]["kind"] == "up-to-date"

    def test_a_second_push_moves_the_remote(self, agent, tmp_path):
        bare = self._repo_with_remote(agent, tmp_path)
        first = agent.push_with_house_rules()
        agent.commit_craft_group("tests")
        record = agent.push_with_house_rules()
        assert record["pushed"] is True
        assert record["before"] == first["after"]
        assert record["after"] != record["before"]
        assert record["remote_diff_stat"] != ""
        assert git(bare, "rev-parse", "refs/heads/main") == \
            record["after"]

    def test_a_diverged_remote_refuses_and_is_untouched(
            self, agent, tmp_path):
        bare = self._repo_with_remote(agent, tmp_path)
        agent.push_with_house_rules()
        other = tmp_path / "other"
        subprocess.run(
            ["git", "clone", str(bare), str(other)],
            check=True, capture_output=True, text=True)
        git(other, "config", "user.email", "other@example.com")
        git(other, "config", "user.name", "Other")
        (other / "other.py").write_text("x = 1\n", encoding="utf-8")
        git(other, "add", ".")
        git(other, "commit", "-m", "other work")
        git(other, "push", "origin", "main")
        remote_head = git(bare, "rev-parse", "refs/heads/main")
        agent.commit_craft_group("tests")
        with pytest.raises(ValueError, match="never force-push"):
            agent.push_with_house_rules()
        assert git(bare, "rev-parse", "refs/heads/main") == remote_head

    def test_gate_off_refuses_a_push(self, agent, tmp_path):
        self._repo_with_remote(agent, tmp_path)
        agent.set_commit_craft(False)
        with pytest.raises(ValueError, match="commit craft is off"):
            agent.push_with_house_rules()


class TestTerminalSurface:
    def test_show_and_set(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/commitcraft")
        assert "Commit craft (M-080)" in text
        _, _, text = _slash(agent, "/commitcraft off")
        assert "on -> off" in text
        assert agent.config["commit_craft"] is False
        _, _, text = _slash(agent, "/commitcraft on")
        assert "off -> on" in text

    def test_plan_and_commit_via_the_terminal(self, agent, tmp_path):
        from mythic_agent.terminal import _slash

        dirty_repo(tmp_path)
        _, _, text = _slash(agent, "/commitcraft plan")
        assert "[code] Update code: app.py" in text
        _, _, text = _slash(agent, "/commitcraft commit code")
        assert "Committed [code]" in text
        assert git(tmp_path, "log", "-1", "--format=%s") == \
            "Update code: app.py"

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/commitcraft sideways")
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


class TestCommitCraftCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_commitcraft("")
        assert "Commit craft (M-080)" in _published_text(handler)

    def test_set_via_the_handler(self, handler, agent):
        handler._handle_commitcraft("off")
        assert "on -> off" in _published_text(handler)
        assert agent.config["commit_craft"] is False

    def test_plan_via_the_handler(self, handler, agent, tmp_path):
        dirty_repo(tmp_path)
        handler._handle_commitcraft("plan")
        assert "[tests] Update tests: test_app.py" in \
            _published_text(handler)

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_commitcraft("sideways")
        assert "Usage" in _published_text(handler)


class TestChatScreenRouting:
    def test_commitcraft_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/commitcraft off", _FakeLog())
        assert calls == [("/commitcraft", "off")]


class TestConfigContract:
    def test_defaults_ship_on(self):
        import yaml
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        defaults = yaml.safe_load(
            (root / "mythic_agent/data/config_defaults.yaml")
            .read_text(encoding="utf-8"))
        assert defaults["commit_craft"] is True
