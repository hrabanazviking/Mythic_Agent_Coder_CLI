"""M-079 — README and licence guardians.

TIER: integration

Covers the M-079 surface:

* the pure layer (``mythic_agent.core.file_guardians``):
  the guarded names judged from the basename at any depth
  (README / README.<anything>; LICENSE, LICENCE, COPYING,
  NOTICE with any extension or suffix), the stub measure,
  and the verdict matrix — a README is never overwritten
  and licence files are never touched, without the user's
  explicit word; in-place README edits, README creation,
  and stub overwrites are allowed,
* the edit layer itself (``EditJournal``): the refusal
  lives in the journal's write, so the direct journal
  roads (write / replace / anchored range / anchored
  search) all refuse or allow by the same verdict, and a
  refusal changes nothing — no file movement, and the
  edit stays undoable only when it truly happened,
* ``Agent``: every apply road classified by the operation
  it truly is (M-071 formats, M-072 anchored, M-073 repair
  — a guardian refusal is re-raised, never packet-ized —
  M-074 hunk review), the explicit-word status and
  ``set_guardian_word`` journaled as
  ``guardian_word_changed`` (a failed save restoring the
  previous value and journaling the revert),
* the tool roads: write_file / replace_file_content carry
  the agent's word into the journal and surface refusals,
* the surfaces: the terminal ``/guardians`` and the TUI
  ``/guardians`` (system-command road through the
  CommandHandler + chat-screen routing), which share the
  parser and formatters,
* the config contract: ``guardian_explicit_word`` ships
  in the defaults (False — the word is never presumed);
  its M-009 catalogue entry is a recorded inventory
  delta for the coordinator (wave discipline), not an
  in-worktree edit.

All fixtures live in throwaway tmp dirs — no README or
licence file in the real tree is ever a test fixture.
"""

from __future__ import annotations

import pytest

from mythic_agent.core.file_guardians import (
    GUARDED_KINDS,
    GUARDIANS_SLICE,
    OPERATIONS,
    PLAIN_EXPLANATION,
    SETTING_KEY,
    GuardianRefusal,
    explicit_from_config,
    format_guard_check,
    format_guardians,
    format_setting_change,
    guard_kind,
    guard_or_raise,
    is_stub_readme,
    judge,
    parse_guardians_args,
    set_explicit_word,
)
from mythic_agent.core.sessions import SessionStore

REAL_README = (
    "# Longhouse Notes\n\n"
    "First section with real words the user wrote and kept.\n"
    "Second section with more history and hard-won detail.\n"
    "Third section keeps the build steps and their reasons.\n"
    "Fourth section records the decisions and their whys.\n"
    "Fifth section is not a stub by any honest measure.\n")
STUB_README = "# New Project\n\nTODO: write this.\n"
LICENCE_TEXT = "MIT License\n\nPermission is hereby granted.\n"
CODE = "alpha = 1\nbeta = 2\ngamma = 3\ndelta = 4\nepsilon = 5\n"


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


class TestGuardKind:
    def test_slice_and_kinds_constants(self):
        assert GUARDIANS_SLICE == "M-079"
        assert SETTING_KEY == "guardian_explicit_word"
        assert GUARDED_KINDS == ("readme", "licence")
        assert OPERATIONS == ("create", "overwrite",
                              "inplace", "delete")
        assert "refuses to overwrite a README" in PLAIN_EXPLANATION

    @pytest.mark.parametrize("path", [
        "README", "README.md", "readme.txt", "ReadMe.RST",
        "docs/README.md", "a/b/c/README.markdown"])
    def test_readme_names_at_any_depth(self, path):
        assert guard_kind(path) == "readme"

    @pytest.mark.parametrize("path", [
        "LICENSE", "LICENCE", "LICENSE.md", "LICENCE.txt",
        "LICENSE-MIT", "LICENSE_APACHE", "COPYING",
        "COPYING.LESSER", "NOTICE", "NOTICE.md",
        "vendor/LICENSE"])
    def test_licence_names_and_spellings(self, path):
        assert guard_kind(path) == "licence"

    @pytest.mark.parametrize("path", [
        "src/app.py", "README2.md", "MYREADME.md",
        "docs/guide.md", "NOTICES.md", "LICENSES/MIT.txt",
        "CHANGELOG.md"])
    def test_unguarded_names(self, path):
        assert guard_kind(path) is None


class TestStub:
    def test_stub_measure(self):
        assert is_stub_readme("") is True
        assert is_stub_readme("  \n \n") is True
        assert is_stub_readme(STUB_README) is True
        assert is_stub_readme(REAL_README) is False
        assert is_stub_readme("one line only\n") is True
        six = "\n".join(f"line {i}" for i in range(6))
        assert is_stub_readme(six) is False
        assert is_stub_readme("x" * 201 + "\n") is False

    def test_stub_requires_text(self):
        with pytest.raises(ValueError, match="must be text"):
            is_stub_readme(None)


class TestJudge:
    def test_readme_overwrite_refused(self):
        verdict = judge("README.md", "overwrite",
                        current_text=REAL_README)
        assert verdict.allowed is False
        assert verdict.kind == "readme"
        assert "never overwritten" in verdict.reason

    def test_readme_overwrite_without_text_refused(self):
        # No text to prove the stub exception with: refused.
        assert judge("docs/README.md", "overwrite").allowed is False

    def test_readme_stub_overwrite_allowed(self):
        verdict = judge("README.md", "overwrite",
                        current_text=STUB_README)
        assert verdict.allowed is True
        assert "stub" in verdict.reason

    def test_readme_inplace_and_create_allowed(self):
        assert judge("README.md", "inplace",
                     current_text=REAL_README).allowed is True
        assert judge("README.md", "create").allowed is True

    def test_readme_delete_refused(self):
        assert judge("README.md", "delete",
                     current_text=REAL_README).allowed is False

    @pytest.mark.parametrize("operation", list(OPERATIONS))
    def test_licence_every_touch_refused(self, operation):
        verdict = judge("LICENSE", operation,
                        current_text=LICENCE_TEXT)
        assert verdict.allowed is False
        assert "not touched" in verdict.reason

    @pytest.mark.parametrize("operation", list(OPERATIONS))
    def test_licence_stub_exception_never_extends(self, operation):
        assert judge("LICENSE", operation,
                     current_text="tiny\n").allowed is False

    @pytest.mark.parametrize("operation", list(OPERATIONS))
    def test_explicit_word_allows_everything_guarded(self, operation):
        for path in ("README.md", "LICENSE-MIT"):
            verdict = judge(path, operation, explicit_word=True,
                            current_text=REAL_README)
            assert verdict.allowed is True
        # Where the word is what lifts the guard, it is named.
        for path in ("LICENSE-MIT",):
            verdict = judge(path, operation, explicit_word=True,
                            current_text=REAL_README)
            assert "explicit word" in verdict.reason
        verdict = judge("README.md", "overwrite", explicit_word=True,
                        current_text=REAL_README)
        assert "explicit word" in verdict.reason

    def test_unguarded_always_allowed(self):
        for operation in OPERATIONS:
            assert judge("src/app.py", operation).allowed is True

    def test_judge_validates_its_inputs(self):
        with pytest.raises(ValueError, match="guardian judges"):
            judge("README.md", "frob")
        with pytest.raises(ValueError, match="given or not given"):
            judge("README.md", "inplace", explicit_word="yes")

    def test_refusal_text_names_file_guard_and_word(self):
        verdict = judge("docs/README.md", "overwrite",
                        current_text=REAL_README)
        text = verdict.refusal_text()
        assert "docs/README.md" in text
        assert "nothing was changed" in text
        assert "/guardians word on" in text
        assert "guardian_explicit_word" in text

    def test_guard_or_raise(self):
        verdict = guard_or_raise("src/app.py", "overwrite")
        assert verdict.allowed is True
        with pytest.raises(GuardianRefusal) as caught:
            guard_or_raise("LICENSE", "inplace")
        assert isinstance(caught.value, ValueError)
        assert caught.value.verdict.kind == "licence"

    def test_verdict_event_and_record(self):
        verdict = judge("README.md", "inplace")
        event = verdict.event()
        assert event["type"] == "guardian_judged"
        assert event["allowed"] is True
        record = verdict.record(None, False)
        assert record["journaled"] is False
        assert record["reason"] == verdict.reason


class TestWordAndSurface:
    def test_word_defaults_not_given_and_validates(self):
        assert explicit_from_config({}) is False
        assert explicit_from_config(None) is False
        assert explicit_from_config(
            {"guardian_explicit_word": True}) is True
        with pytest.raises(ValueError, match="true or false"):
            explicit_from_config({"guardian_explicit_word": "yes"})

    def test_set_explicit_word(self):
        value, change = set_explicit_word({}, True)
        assert value is True and change.before is False
        assert change.event()["type"] == "guardian_word_changed"
        with pytest.raises(ValueError, match="already not given"):
            set_explicit_word({}, False)
        with pytest.raises(ValueError, match="given or not given"):
            set_explicit_word({}, "on")

    def test_parse_args(self):
        assert parse_guardians_args("") == {"action": "show"}
        assert parse_guardians_args("word on") == {
            "action": "setting", "enabled": True}
        assert parse_guardians_args("word off") == {
            "action": "setting", "enabled": False}
        assert parse_guardians_args("check docs/LICENSE") == {
            "action": "check", "path": "docs/LICENSE"}
        with pytest.raises(ValueError, match="Usage"):
            parse_guardians_args("sideways")
        with pytest.raises(ValueError, match="Usage"):
            parse_guardians_args("check")

    def test_format_setting_change(self):
        record = {"from": False, "to": True}
        assert format_setting_change(record) == (
            "Guardian explicit word: not given -> given.")

    def test_format_guard_check(self):
        text = format_guard_check({}, "LICENSE-MIT")
        assert "Guard: licence" in text
        assert text.count("REFUSED") == 4
        text = format_guard_check({}, "src/app.py")
        assert "Guard: none" in text
        assert "REFUSED" not in text
        text = format_guard_check(
            {"guardian_explicit_word": True}, "README.md")
        assert "REFUSED" not in text

    def test_format_guardians_shows_the_worked_examples(self):
        text = format_guardians({})
        assert "README and licence guardians (M-079)" in text
        assert "Explicit word: not given" in text
        assert "docs/guide/README.rst: readme" in text
        assert "LICENSE-MIT: licence" in text
        assert "src/app.py: unguarded" in text
        assert "REFUSED" in text and "in place: allowed" in text
        assert "Usage: /guardians" in text


class TestJournalRoads:
    """The refusal lives in EditJournal.write itself."""

    def journal(self, tmp_path, **kwargs):
        from mythic_agent.core.edits import EditJournal
        return EditJournal(tmp_path, **kwargs)

    def seed(self, tmp_path, name, text):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def test_write_overwrite_of_readme_refused(self, agent, tmp_path):
        target = self.seed(tmp_path, "README.md", REAL_README)
        with pytest.raises(GuardianRefusal, match="never overwritten"):
            self.journal(tmp_path).write("README.md", "# Replaced\n")
        assert target.read_text(encoding="utf-8") == REAL_README

    def test_write_create_readme_and_code_allowed(self, agent, tmp_path):
        journal = self.journal(tmp_path)
        journal.write("README.md", REAL_README)
        journal.write("app.py", CODE)
        journal.write("app.py", CODE.replace("beta = 2", "beta = 20"))
        assert "beta = 20" in (tmp_path / "app.py").read_text(
            encoding="utf-8")

    def test_write_stub_readme_overwrite_allowed(self, agent, tmp_path):
        self.seed(tmp_path, "README.md", STUB_README)
        self.journal(tmp_path).write("README.md", REAL_README)
        assert (tmp_path / "README.md").read_text(
            encoding="utf-8") == REAL_README

    def test_write_no_change_is_not_a_touch(self, agent, tmp_path):
        target = self.seed(tmp_path, "LICENSE", LICENCE_TEXT)
        self.journal(tmp_path).write("LICENSE", LICENCE_TEXT)
        assert target.read_text(encoding="utf-8") == LICENCE_TEXT

    def test_write_licence_refused_create_and_overwrite(
            self, agent, tmp_path):
        journal = self.journal(tmp_path)
        with pytest.raises(GuardianRefusal, match="not touched"):
            journal.write("LICENSE", LICENCE_TEXT)
        assert not (tmp_path / "LICENSE").exists()
        self.seed(tmp_path, "LICENSE", LICENCE_TEXT)
        with pytest.raises(GuardianRefusal):
            journal.write("LICENSE", "Other licence.\n")

    def test_explicit_word_in_journal_allows(self, agent, tmp_path):
        self.seed(tmp_path, "README.md", REAL_README)
        self.seed(tmp_path, "LICENSE", LICENCE_TEXT)
        journal = self.journal(tmp_path, explicit_word=True)
        journal.write("README.md", "# Given word.\n")
        journal.write("LICENSE", "Other licence.\n")
        assert "Given word" in (tmp_path / "README.md").read_text(
            encoding="utf-8")

    def test_per_call_word_wins(self, agent, tmp_path):
        self.seed(tmp_path, "LICENSE", LICENCE_TEXT)
        self.journal(tmp_path).write(
            "LICENSE", "Other licence.\n", explicit_word=True)
        assert "Other" in (tmp_path / "LICENSE").read_text(
            encoding="utf-8")

    def test_replace_is_inplace_for_readme_refused_for_licence(
            self, agent, tmp_path):
        readme = self.seed(tmp_path, "README.md", REAL_README)
        licence = self.seed(tmp_path, "NOTICE.md", LICENCE_TEXT)
        journal = self.journal(tmp_path)
        journal.replace("README.md", "First section",
                        "Opening section")
        assert "Opening section" in readme.read_text(encoding="utf-8")
        with pytest.raises(GuardianRefusal):
            journal.replace("NOTICE.md", "MIT License", "Other")
        assert licence.read_text(encoding="utf-8") == LICENCE_TEXT

    def test_anchored_partial_readme_full_refused(self, agent, tmp_path):
        from mythic_agent.core.hash_anchored import range_anchor
        target = self.seed(tmp_path, "README.md", REAL_README)
        journal = self.journal(tmp_path)
        lines = len(REAL_README.splitlines())
        anchor = range_anchor(REAL_README, 3, 3).hash
        journal.write_anchored_range(
            "README.md", 3, 3, anchor, "A replaced third line.")
        assert "replaced third line" in target.read_text(
            encoding="utf-8")
        whole = range_anchor(
            target.read_text(encoding="utf-8"), 1, lines).hash
        with pytest.raises(GuardianRefusal, match="never overwritten"):
            journal.write_anchored_range(
                "README.md", 1, lines, whole, "# All new.\n")

    def test_anchored_search_whole_file_is_overwrite(
            self, agent, tmp_path):
        from mythic_agent.core.hash_anchored import range_anchor
        target = self.seed(tmp_path, "README.md", REAL_README)
        journal = self.journal(tmp_path)
        lines = len(REAL_README.splitlines())
        anchor = range_anchor(REAL_README, 1, lines).hash
        with pytest.raises(GuardianRefusal):
            journal.write_anchored_search(
                "README.md", REAL_README.rstrip("\n"), anchor,
                "# All new.\n")
        part = range_anchor(REAL_README, 3, 3).hash
        journal.write_anchored_search(
            "README.md", REAL_README.splitlines()[2], part,
            "A replaced third line.")
        assert "replaced third line" in target.read_text(
            encoding="utf-8")

    def test_refused_write_journals_nothing_to_undo(
            self, agent, tmp_path):
        self.seed(tmp_path, "README.md", REAL_README)
        journal = self.journal(tmp_path)
        with pytest.raises(GuardianRefusal):
            journal.write("README.md", "# Replaced\n")
        assert journal.undo() == (
            "No agent edit to undo in this workspace.")


class TestAgentWord:
    def test_status(self, agent):
        status = agent.guardian_status()
        assert status["explicit_word"] is False
        assert status["guarded_kinds"] == ["readme", "licence"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_set_without_session(self, agent):
        record = agent.set_guardian_word(True)
        assert record["journaled"] is False
        assert agent.config["guardian_explicit_word"] is True
        with pytest.raises(ValueError, match="already given"):
            agent.set_guardian_word(True)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_guardian_word(True)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "guardian_word_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_guardian_word(True)
        assert agent.config.get("guardian_explicit_word") is not True
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["guardian_word_changed",
                              "guardian_word_reverted"]
        agent.close()


def _seed(tmp_path, name, text):
    target = tmp_path / name
    target.write_text(text, encoding="utf-8")
    return target


class TestAgentRoads:
    def test_whole_file_format_overwrite_of_readme_refused(
            self, agent, tmp_path):
        target = _seed(tmp_path, "README.md", REAL_README)
        with pytest.raises(GuardianRefusal, match="never overwritten"):
            agent.apply_edit_format(
                "README.md", "whole-file", "# Replaced\n")
        assert target.read_text(encoding="utf-8") == REAL_README

    def test_whole_file_format_creates_readme(self, agent, tmp_path):
        agent.apply_edit_format("README.md", "whole-file", REAL_README)
        assert (tmp_path / "README.md").exists()

    def test_search_replace_format_edits_readme_in_place(
            self, agent, tmp_path):
        target = _seed(tmp_path, "README.md", REAL_README)
        payload = ("<<<<<<< SEARCH\nFirst section with real words "
                   "the user wrote and kept.\n=======\n"
                   "Opening section, edited in place.\n"
                   ">>>>>>> REPLACE")
        record = agent.apply_edit_format(
            "README.md", "search-replace", payload)
        assert record["changed"] is True
        assert "Opening section, edited in place." in target.read_text(
            encoding="utf-8")

    def test_unified_diff_format_edits_readme_in_place(
            self, agent, tmp_path):
        target = _seed(tmp_path, "README.md", REAL_README)
        payload = ("@@ -1,3 +1,3 @@\n # Longhouse Notes\n \n"
                   "-First section with real words the user wrote "
                   "and kept.\n+Opening section, edited in place.")
        agent.apply_edit_format("README.md", "unified-diff", payload)
        assert "edited in place" in target.read_text(encoding="utf-8")

    def test_whole_file_format_licence_refused_even_to_create(
            self, agent, tmp_path):
        with pytest.raises(GuardianRefusal, match="not touched"):
            agent.apply_edit_format("LICENSE", "whole-file",
                                    LICENCE_TEXT)
        assert not (tmp_path / "LICENSE").exists()

    def test_word_given_allows_agent_overwrites(self, agent, tmp_path):
        target = _seed(tmp_path, "README.md", REAL_README)
        licence = _seed(tmp_path, "LICENSE", LICENCE_TEXT)
        agent.set_guardian_word(True)
        agent.apply_edit_format(
            "README.md", "whole-file", "# Replaced by word.\n")
        agent.apply_edit_format(
            "LICENSE", "whole-file", "Other licence.\n")
        assert "by word" in target.read_text(encoding="utf-8")
        assert "Other" in licence.read_text(encoding="utf-8")

    def test_anchored_agent_roads_judged_by_span(self, agent, tmp_path):
        from mythic_agent.core.hash_anchored import range_anchor
        target = _seed(tmp_path, "README.md", REAL_README)
        lines = len(REAL_README.splitlines())
        part = range_anchor(REAL_README, 3, 3).hash
        agent.apply_hash_anchored_range(
            "README.md", 3, 3, part, "A replaced third line.")
        assert "replaced third line" in target.read_text(
            encoding="utf-8")
        current = target.read_text(encoding="utf-8")
        whole = range_anchor(current, 1, lines).hash
        with pytest.raises(GuardianRefusal):
            agent.apply_hash_anchored_range(
                "README.md", 1, lines, whole, "# All new.\n")
        # A one-line anchored search on the README is an
        # in-place edit: allowed, and it lands.
        agent.apply_hash_anchored_search(
            "README.md", current.splitlines()[2],
            range_anchor(current, 3, 3).hash, "A searched line.")
        assert "A searched line." in target.read_text(
            encoding="utf-8")

    def test_anchored_search_on_licence_refused(self, agent, tmp_path):
        from mythic_agent.core.hash_anchored import range_anchor
        _seed(tmp_path, "LICENSE", LICENCE_TEXT)
        anchor = range_anchor(LICENCE_TEXT, 1, 1).hash
        with pytest.raises(GuardianRefusal, match="not touched"):
            agent.apply_hash_anchored_search(
                "LICENSE", "MIT License", anchor, "Other License")

    def test_hunk_review_on_readme_inplace_on_licence_refused(
            self, agent, tmp_path):
        target = _seed(tmp_path, "README.md", REAL_README)
        diff = ("@@ -1,3 +1,3 @@\n # Longhouse Notes\n \n"
                "-First section with real words the user wrote "
                "and kept.\n+Opening section, reviewed in place.")
        record = agent.apply_hunk_review(
            "README.md", diff, [(0, "accept")])
        assert record["applied"] == 1
        assert "reviewed in place" in target.read_text(
            encoding="utf-8")
        licence = _seed(tmp_path, "LICENSE", LICENCE_TEXT)
        ldiff = ("@@ -1,1 +1,1 @@\n-MIT License\n+Other License")
        with pytest.raises(GuardianRefusal):
            agent.apply_hunk_review(
                "LICENSE", ldiff, [(0, "accept")])
        assert licence.read_text(encoding="utf-8") == LICENCE_TEXT

    def test_repair_road_reraises_a_guardian_refusal(
            self, agent, tmp_path):
        target = _seed(tmp_path, "README.md", REAL_README)
        with pytest.raises(GuardianRefusal):
            agent.apply_edit_format_with_repair(
                "README.md", "whole-file", "# Replaced\n")
        assert target.read_text(encoding="utf-8") == REAL_README

    def test_repair_road_still_repairs_a_code_file(
            self, agent, tmp_path):
        target = _seed(tmp_path, "app.py", CODE)
        payload = ("<<<<<<< SEARCH\nbeta = 99\n=======\n"
                   "beta = 20\n>>>>>>> REPLACE")
        record = agent.apply_edit_format_with_repair(
            "app.py", "search-replace", payload)
        assert record["applied"] is False  # packet offered, no retry
        assert target.read_text(encoding="utf-8") == CODE


class TestToolRoads:
    def run_tool(self, name, arguments, agent):
        from mythic_agent.agents.tools import execute_tool
        from mythic_agent.core.policy import ToolPolicy
        return execute_tool(name, arguments, agent.project_root,
                            agent=agent, policy=ToolPolicy("trusted"))

    def test_write_file_overwrite_of_readme_refused(
            self, agent, tmp_path):
        target = _seed(tmp_path, "README.md", REAL_README)
        result = self.run_tool(
            "write_file", {"path": "README.md",
                           "content": "# Replaced\n"}, agent)
        assert "Failed to write file" in result
        assert "Guarded file refused" in result
        assert target.read_text(encoding="utf-8") == REAL_README

    def test_write_file_creates_readme_and_code(self, agent, tmp_path):
        result = self.run_tool(
            "write_file", {"path": "README.md",
                           "content": REAL_README}, agent)
        assert result.startswith("Successfully wrote")
        result = self.run_tool(
            "write_file", {"path": "app.py", "content": CODE}, agent)
        assert result.startswith("Successfully wrote")

    def test_write_file_licence_refused(self, agent, tmp_path):
        result = self.run_tool(
            "write_file", {"path": "LICENSE",
                           "content": LICENCE_TEXT}, agent)
        assert "Guarded file refused" in result
        assert not (tmp_path / "LICENSE").exists()

    def test_replace_file_content_readme_inplace_allowed(
            self, agent, tmp_path):
        target = _seed(tmp_path, "README.md", REAL_README)
        result = self.run_tool(
            "replace_file_content",
            {"path": "README.md", "target_content": "First section",
             "replacement_content": "Opening section"}, agent)
        assert result.startswith("Successfully replaced")
        assert "Opening section" in target.read_text(encoding="utf-8")

    def test_replace_file_content_licence_refused(
            self, agent, tmp_path):
        target = _seed(tmp_path, "LICENSE", LICENCE_TEXT)
        result = self.run_tool(
            "replace_file_content",
            {"path": "LICENSE", "target_content": "MIT License",
             "replacement_content": "Other License"}, agent)
        assert "Failed to replace content" in result
        assert "Guarded file refused" in result
        assert target.read_text(encoding="utf-8") == LICENCE_TEXT

    def test_tool_road_honours_the_agents_word(self, agent, tmp_path):
        target = _seed(tmp_path, "README.md", REAL_README)
        agent.set_guardian_word(True)
        result = self.run_tool(
            "write_file", {"path": "README.md",
                           "content": "# By word.\n"}, agent)
        assert result.startswith("Successfully wrote")
        assert "By word" in target.read_text(encoding="utf-8")


class TestTerminalSurface:
    def test_show_and_set(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/guardians")
        assert "README and licence guardians (M-079)" in text
        _, _, text = _slash(agent, "/guardians word on")
        assert "not given -> given" in text
        assert agent.config["guardian_explicit_word"] is True
        _, _, text = _slash(agent, "/guardians word off")
        assert "given -> not given" in text

    def test_check(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/guardians check LICENSE")
        assert "Guard: licence" in text

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/guardians sideways")
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


class TestGuardiansCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_guardians("")
        assert "README and licence guardians (M-079)" in (
            _published_text(handler))

    def test_set_via_the_handler(self, handler, agent):
        handler._handle_guardians("word on")
        assert "not given -> given" in _published_text(handler)
        assert agent.config["guardian_explicit_word"] is True

    def test_check_via_the_handler(self, handler, agent):
        handler._handle_guardians("check README.md")
        assert "Guard: readme" in _published_text(handler)

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_guardians("sideways")
        assert "Usage" in _published_text(handler)


class TestChatScreenRouting:
    def test_guardians_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/guardians word on", _FakeLog())
        assert calls == [("/guardians", "word on")]


class TestConfigContract:
    def test_defaults_ship_word_not_given(self):
        import yaml
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        defaults = yaml.safe_load(
            (root / "mythic_agent/data/config_defaults.yaml")
            .read_text(encoding="utf-8"))
        assert defaults["guardian_explicit_word"] is False

    def test_catalogue_entry_is_a_recorded_delta(self):
        # Wave discipline: the config catalogue is a shared
        # inventory surface — teams do not edit it in their
        # worktrees (parallel S-number claims would collide).
        # The S-entry for this setting (name, bool, default
        # False, and the full effect text) is recorded as an
        # inventory delta in TEAM_LOG.md for the coordinator
        # to apply at integration; until then the catalogue
        # cross-check in test_config_catalog.py fails on
        # this one uncatalogued default, by design.
        import yaml
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        defaults = yaml.safe_load(
            (root / "mythic_agent/data/config_defaults.yaml")
            .read_text(encoding="utf-8"))
        assert "guardian_explicit_word" in defaults
