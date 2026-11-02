"""M-071 — Edit-format plurality.

TIER: integration

Covers the M-071 surface:

* the pure layer (``mythic_agent.core.edit_formats``): the
  four formats as data (whole-file, unified-diff,
  search-and-replace, architect) and the five task kinds;
  the ``edit_format`` setting as config data ('auto' by
  default, a pinned format honoured exactly, a malformed
  stored value raises); model strength from M-027
  capability truth (reasoning known-true is strong,
  tool_calling known-true is standard, unlisted is
  unknown — never guessed); the auto choice per task and
  per strength (unknown strength always gets the safest
  whole-file; creating a file is always whole-file, even
  under a pinned format, and the override is named);
  the architect/editor split (the architect plans per-file
  intents and never edits — no step's format is architect;
  the editor picks a concrete format per file),
* the appliers: whole-file; unified-diff applied strictly
  (exact context, stated positions, no fuzz — a stale hunk
  refuses and changes nothing; malformed counts refuse;
  a creation diff works); Aider-style SEARCH/REPLACE
  blocks (each search matches exactly once — zero and
  several both refuse; an empty SEARCH only creates into
  an empty file); the dispatcher (architect is not a
  payload format and refuses saying why),
* ``Agent`` changes: ``set_edit_format`` journaled as
  ``edit_format_setting_changed``, saved, a failed save
  restoring the previous setting and journaling the
  revert; ``choose_edit_format`` journaling the choice as
  ``edit_format_chosen`` with its reason (the roadmap's
  "the choice is journaled"); ``apply_edit_format``
  applying through the pure layer and writing through
  the existing EditJournal road,
* the surfaces: the terminal ``/editformat`` and the TUI
  ``/editformat`` (system-command road through the
  CommandHandler + chat-screen routing), which share the
  parser and formatters,
* the config contract: ``edit_format`` ships in the
  defaults ('auto') and is catalogued (M-009, S-60).
"""

from __future__ import annotations

import pytest

from mythic_agent.core.edit_formats import (
    EDIT_FORMATS_SLICE,
    FORMAT_IDS,
    PLAIN_EXPLANATION,
    SETTING_VALUES,
    STRENGTHS,
    TASK_KIND_IDS,
    apply_edit,
    apply_search_replace,
    apply_unified_diff,
    apply_whole_file,
    choose_format,
    format_choice,
    format_edit_formats,
    format_setting_change,
    get_format,
    get_task_kind,
    list_formats,
    list_task_kinds,
    model_strength,
    parse_editformat_args,
    plan_split,
    set_setting,
    setting_from_config,
)
from mythic_agent.core.model_capabilities import load_capabilities
from mythic_agent.core.sessions import SessionStore

STRONG = "deepseek-reasoner"   # M-027: reasoning known-true
STANDARD = "gpt-4o"            # M-027: tool_calling known-true
UNKNOWN = "no-such-model"      # unlisted: all-unknown


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


# ----------------------------------------------------------------------
# The formats and task kinds, as data
# ----------------------------------------------------------------------

class TestData:
    def test_slice_and_ids(self):
        assert EDIT_FORMATS_SLICE == "M-071"
        assert FORMAT_IDS == ("whole-file", "unified-diff",
                              "search-replace", "architect")
        assert TASK_KIND_IDS == ("new-file", "rewrite", "small-fix",
                                 "multi-site", "complex")
        assert SETTING_VALUES == ("auto",) + FORMAT_IDS
        assert STRENGTHS == ("unknown", "standard", "strong")

    def test_only_architect_is_not_appliable(self):
        for fmt in list_formats():
            assert fmt.appliable is (fmt.id != "architect")
            assert fmt.plain
            assert fmt.strength_floor in STRENGTHS

    def test_strength_floors_match_the_auto_law(self):
        floors = {f.id: f.strength_floor for f in list_formats()}
        assert floors["whole-file"] == "unknown"
        assert floors["search-replace"] == "standard"
        assert floors["unified-diff"] == "strong"

    def test_unknown_names_raise_plainly(self):
        with pytest.raises(ValueError, match="unknown edit format"):
            get_format("telepathy")
        with pytest.raises(ValueError, match="unknown edit task kind"):
            get_task_kind("telepathy")
        assert get_format("whole-file").title == "Whole-file"
        assert [k.id for k in list_task_kinds()] == list(TASK_KIND_IDS)


# ----------------------------------------------------------------------
# The setting, as data
# ----------------------------------------------------------------------

class TestSetting:
    def test_absent_means_auto(self):
        assert setting_from_config({}) == "auto"

    def test_stored_values_read_back(self):
        for value in SETTING_VALUES:
            assert setting_from_config({"edit_format": value}) == value

    def test_malformed_stored_setting_raises(self):
        with pytest.raises(ValueError, match="edit_format must be one of"):
            setting_from_config({"edit_format": "sideways"})

    def test_set_setting_is_pure_and_records_the_change(self):
        config = {"edit_format": "auto"}
        value, change = set_setting(config, "unified-diff")
        assert value == "unified-diff"
        assert config == {"edit_format": "auto"}
        assert change.event() == {"type": "edit_format_setting_changed",
                                  "from": "auto", "to": "unified-diff"}
        assert change.record("s" * 32, True)["to"] == "unified-diff"

    def test_set_setting_refuses_no_change_and_bad_value(self):
        with pytest.raises(ValueError, match="already auto"):
            set_setting({}, "auto")
        with pytest.raises(ValueError, match="must be one of"):
            set_setting({}, "sideways")


# ----------------------------------------------------------------------
# Strength is M-027 truth
# ----------------------------------------------------------------------

class TestStrength:
    def test_named_models(self):
        assert model_strength(STRONG) == "strong"
        assert model_strength(STANDARD) == "standard"
        assert model_strength(UNKNOWN) == "unknown"
        assert model_strength(None) == "unknown"
        assert model_strength("") == "unknown"

    def test_every_shipped_model_matches_its_record(self):
        caps = load_capabilities()
        for record in caps.records:
            expected = ("strong" if record.reasoning is True else
                        "standard" if record.tool_calling is True else
                        "unknown")
            assert model_strength(record.model, caps) == expected


# ----------------------------------------------------------------------
# The choice: per task, per strength, pinned honoured
# ----------------------------------------------------------------------

class TestChoice:
    @pytest.mark.parametrize("model,expected", [
        (STRONG, "search-replace"), (STANDARD, "search-replace"),
        (UNKNOWN, "whole-file")])
    def test_small_fix(self, model, expected):
        choice = choose_format("small-fix", model=model)
        assert choice.format_id == expected
        assert choice.split is False
        assert choice.reason

    @pytest.mark.parametrize("model,expected", [
        (STRONG, "unified-diff"), (STANDARD, "search-replace"),
        (UNKNOWN, "whole-file")])
    def test_multi_site(self, model, expected):
        assert choose_format("multi-site", model=model).format_id == expected

    @pytest.mark.parametrize("model", [STRONG, STANDARD, UNKNOWN])
    def test_new_file_and_rewrite_are_always_whole_file(self, model):
        assert choose_format("new-file", model=model).format_id == "whole-file"
        assert choose_format("rewrite", model=model).format_id == "whole-file"

    @pytest.mark.parametrize("model", [STRONG, STANDARD, UNKNOWN])
    def test_complex_always_splits(self, model):
        choice = choose_format("complex", model=model)
        assert choice.format_id == "architect"
        assert choice.split is True

    def test_choice_event_is_the_journal_shape(self):
        choice = choose_format("small-fix", model=STRONG)
        event = choice.event()
        assert event["type"] == "edit_format_chosen"
        assert event["format"] == "search-replace"
        assert event["strength"] == "strong"
        assert event["reason"] == choice.reason

    def test_pinned_format_is_honoured_exactly(self):
        config = {"edit_format": "unified-diff"}
        choice = choose_format("small-fix", model=UNKNOWN, config=config)
        assert choice.format_id == "unified-diff"
        assert "pins unified-diff" in choice.reason

    def test_pinned_architect_splits(self):
        config = {"edit_format": "architect"}
        choice = choose_format("small-fix", model=STRONG, config=config)
        assert choice.format_id == "architect"
        assert choice.split is True

    def test_new_file_overrides_a_pin_and_names_it(self):
        for pinned in ("unified-diff", "search-replace", "architect"):
            config = {"edit_format": pinned}
            choice = choose_format("new-file", model=STRONG, config=config)
            assert choice.format_id == "whole-file"
            assert choice.split is False
            assert pinned in choice.reason
            assert "always written whole" in choice.reason

    def test_unknown_task_kind_raises(self):
        with pytest.raises(ValueError, match="unknown edit task kind"):
            choose_format("telepathy", model=STRONG)


# ----------------------------------------------------------------------
# The architect/editor split
# ----------------------------------------------------------------------

class TestSplit:
    FILES = [("app.py", "targeted", "fix the paging off-by-one"),
             ("util.py", "multi-site", "rename the helper everywhere"),
             ("new_mod.py", "create", "hold the new helper"),
             ("old.py", "rewrite", "rewrite the parser")]

    def test_editor_picks_per_file_for_a_strong_model(self):
        split = plan_split(self.FILES, model=STRONG)
        by_path = {s.path: s.format_id for s in split.steps}
        assert by_path == {"app.py": "search-replace",
                           "util.py": "unified-diff",
                           "new_mod.py": "whole-file",
                           "old.py": "whole-file"}
        assert split.event()["format"] == "architect"
        assert split.event()["files"] == [f[0] for f in self.FILES]

    def test_editor_picks_the_safest_for_an_unknown_model(self):
        split = plan_split(self.FILES, model=UNKNOWN)
        assert {s.format_id for s in split.steps} == {"whole-file"}

    def test_the_architect_never_edits(self):
        split = plan_split(self.FILES, model=STRONG)
        for step in split.steps:
            assert step.format_id != "architect"
            assert get_format(step.format_id).appliable is True
            assert step.intent  # the architect side is intent only

    def test_split_refusals(self):
        with pytest.raises(ValueError, match="at least one file"):
            plan_split([], model=STRONG)
        with pytest.raises(ValueError, match="twice"):
            plan_split([("a.py", "create", "x"), ("a.py", "create", "y")])
        with pytest.raises(ValueError, match="unknown change kind"):
            plan_split([("a.py", "sideways", "x")])
        with pytest.raises(ValueError, match="needs an intent"):
            plan_split([("a.py", "create", "")])


# ----------------------------------------------------------------------
# The appliers
# ----------------------------------------------------------------------

class TestApplyWholeFile:
    def test_payload_is_the_new_text(self):
        assert apply_whole_file("old\n", "new\n") == ("new\n", 1)
        assert apply_whole_file(None, "created\n") == ("created\n", 1)


SEARCH_PAYLOAD = ("<<<<<<< SEARCH\n"
                  "def alpha(x):\n"
                  "    return x + 1\n"
                  "=======\n"
                  "def alpha(x):\n"
                  "    return x + 2\n"
                  ">>>>>>> REPLACE\n")


class TestApplySearchReplace:
    SOURCE = "import os\n\n\ndef alpha(x):\n    return x + 1\n"

    def test_one_block(self):
        new, units = apply_search_replace(self.SOURCE, SEARCH_PAYLOAD)
        assert units == 1
        assert new == "import os\n\n\ndef alpha(x):\n    return x + 2\n"

    def test_two_blocks_apply_in_order(self):
        payload = (SEARCH_PAYLOAD
                   + "<<<<<<< SEARCH\nimport os\n=======\nimport sys\n"
                     ">>>>>>> REPLACE\n")
        new, units = apply_search_replace(self.SOURCE, payload)
        assert units == 2
        assert new.startswith("import sys\n")
        assert "x + 2" in new

    def test_no_match_refuses(self):
        with pytest.raises(ValueError, match="matched nothing"):
            apply_search_replace(self.SOURCE,
                                 SEARCH_PAYLOAD.replace("x + 1", "x + 9"))

    def test_several_matches_refuse(self):
        source = "same\nsame\n"
        payload = ("<<<<<<< SEARCH\nsame\n=======\nother\n"
                   ">>>>>>> REPLACE\n")
        with pytest.raises(ValueError, match="exactly once"):
            apply_search_replace(source, payload)

    def test_empty_search_creates_only_into_an_empty_file(self):
        payload = ("<<<<<<< SEARCH\n=======\nborn\n>>>>>>> REPLACE\n")
        assert apply_search_replace("", payload) == ("born", 1)
        with pytest.raises(ValueError, match="empty SEARCH"):
            apply_search_replace(self.SOURCE, payload)

    def test_malformed_payloads_refuse(self):
        with pytest.raises(ValueError, match="no SEARCH/REPLACE block"):
            apply_search_replace(self.SOURCE, "")
        with pytest.raises(ValueError, match="missing its"):
            apply_search_replace(self.SOURCE, "<<<<<<< SEARCH\nx\n")
        with pytest.raises(ValueError, match="made of blocks"):
            apply_search_replace(self.SOURCE, "just text\n")


DIFF_ONE = ("--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -2,3 +2,3 @@\n"
            " line2\n"
            "-line3\n"
            "+line three\n"
            " line4\n")


class TestApplyUnifiedDiff:
    SOURCE = "line1\nline2\nline3\nline4\nline5\n"

    def test_one_hunk(self):
        new, units = apply_unified_diff(self.SOURCE, DIFF_ONE)
        assert units == 1
        assert new == "line1\nline2\nline three\nline4\nline5\n"

    def test_two_hunks_with_offset(self):
        payload = ("@@ -1,2 +1,3 @@\n"
                   " line1\n"
                   "+inserted\n"
                   " line2\n"
                   "@@ -4,2 +5,2 @@\n"
                   " line4\n"
                   "-line5\n"
                   "+line five\n")
        new, units = apply_unified_diff(self.SOURCE, payload)
        assert units == 2
        assert new == ("line1\ninserted\nline2\nline3\nline4\n"
                       "line five\n")

    def test_creation_diff(self):
        payload = "@@ -0,0 +1,2 @@\n+born\n+here\n"
        new, units = apply_unified_diff("", payload)
        assert units == 1
        assert new == "born\nhere"

    def test_stale_context_refuses_and_changes_nothing(self):
        stale = DIFF_ONE.replace("line3", "other")
        with pytest.raises(ValueError, match="does not match"):
            apply_unified_diff(self.SOURCE, stale)

    def test_malformed_counts_refuse(self):
        bad = "@@ -2,9 +2,3 @@\n line2\n-line3\n+line three\n line4\n"
        with pytest.raises(ValueError, match="counts do not match"):
            apply_unified_diff(self.SOURCE, bad)

    def test_outside_the_file_refuses(self):
        bad = "@@ -99,1 +99,1 @@\n-line99\n+line 99\n"
        with pytest.raises(ValueError, match="outside the file"):
            apply_unified_diff(self.SOURCE, bad)

    def test_no_hunk_refuses(self):
        with pytest.raises(ValueError, match="no diff hunk"):
            apply_unified_diff(self.SOURCE, "--- a/app.py\n+++ b/app.py\n")
        with pytest.raises(ValueError, match="not a unified diff"):
            apply_unified_diff(self.SOURCE, "not a diff at all\n")


class TestApplyEdit:
    def test_dispatches_each_concrete_format(self):
        assert apply_edit("whole-file", "a\n", "b\n") == ("b\n", 1)
        new, _ = apply_edit("search-replace",
                            TestApplySearchReplace.SOURCE, SEARCH_PAYLOAD)
        assert "x + 2" in new
        new, _ = apply_edit("unified-diff",
                            TestApplyUnifiedDiff.SOURCE, DIFF_ONE)
        assert "line three" in new

    def test_architect_is_not_a_payload(self):
        with pytest.raises(ValueError, match="not a payload"):
            apply_edit("architect", "a\n", "b\n")

    def test_none_current_is_an_empty_file(self):
        payload = "@@ -0,0 +1,1 @@\n+born\n"
        assert apply_edit("unified-diff", None, payload) == ("born", 1)


# ----------------------------------------------------------------------
# The /editformat parser + formatters
# ----------------------------------------------------------------------

class TestSurface:
    def test_parse(self):
        assert parse_editformat_args("") == {"action": "show"}
        assert parse_editformat_args("auto") == {
            "action": "setting", "value": "auto"}
        assert parse_editformat_args("unified-diff") == {
            "action": "setting", "value": "unified-diff"}
        assert parse_editformat_args("small-fix") == {
            "action": "choose", "task_kind": "small-fix"}
        with pytest.raises(ValueError, match="Usage"):
            parse_editformat_args("sideways")
        with pytest.raises(ValueError, match="Usage"):
            parse_editformat_args("small-fix please")

    def test_format_choice_and_change(self):
        text = format_choice(choose_format("multi-site", model=STRONG))
        assert "unified-diff" in text and "strong" in text
        change = format_setting_change(
            {"from": "auto", "to": "whole-file"})
        assert change == "Edit format setting: auto -> whole-file."

    def test_show_surface_names_everything(self):
        text = format_edit_formats({"model": STANDARD})
        assert PLAIN_EXPLANATION in text
        for format_id in FORMAT_IDS:
            assert format_id in text
        for kind in TASK_KIND_IDS:
            assert kind in text
        assert "Setting: auto" in text


# ----------------------------------------------------------------------
# Agent: setting journaled, choice journaled, apply rides EditJournal
# ----------------------------------------------------------------------

class TestAgentEditFormats:
    def test_status(self, agent):
        status = agent.edit_format_status()
        assert status["setting"] == "auto"
        assert status["model"] == "test-model"
        assert status["strength"] == "unknown"
        assert [f["id"] for f in status["formats"]] == list(FORMAT_IDS)
        assert [t["id"] for t in status["task_kinds"]] == list(TASK_KIND_IDS)

    def test_set_without_session(self, agent):
        record = agent.set_edit_format("unified-diff")
        assert record["journaled"] is False
        assert agent.config["edit_format"] == "unified-diff"
        with pytest.raises(ValueError, match="already unified-diff"):
            agent.set_edit_format("unified-diff")

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_edit_format("whole-file")
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "edit_format_setting_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_edit_format("whole-file")
        assert agent.config.get("edit_format") != "whole-file"
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["edit_format_setting_changed",
                              "edit_format_setting_reverted"]
        agent.close()

    def test_choice_is_journaled_with_its_reason(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        record = agent.choose_edit_format("small-fix")
        assert record["journaled"] is True
        assert record["format"] == "whole-file"  # test-model: unknown
        events = [e for e in store.export(session_id)["events"]
                  if e["type"] == "edit_format_chosen"]
        assert len(events) == 1
        assert events[0]["reason"] == record["reason"]
        agent.close()

    def test_apply_rides_the_edit_journal(self, agent, tmp_path):
        (tmp_path / "app.py").write_text(
            TestApplySearchReplace.SOURCE, encoding="utf-8")
        record = agent.apply_edit_format(
            "app.py", "search-replace", SEARCH_PAYLOAD)
        assert record["units"] == 1
        assert (tmp_path / "app.py").read_text(
            encoding="utf-8").endswith("return x + 2\n")
        # The EditJournal road: the edit is undoable, journal-proven.
        from mythic_agent.core.edits import EditJournal
        message = EditJournal(tmp_path).undo()
        assert "app.py" in message
        assert "x + 1" in (tmp_path / "app.py").read_text(
            encoding="utf-8")

    def test_apply_a_stale_diff_writes_nothing(self, agent, tmp_path):
        target = tmp_path / "app.py"
        target.write_text(TestApplyUnifiedDiff.SOURCE, encoding="utf-8")
        with pytest.raises(ValueError, match="does not match"):
            agent.apply_edit_format(
                "app.py", "unified-diff",
                DIFF_ONE.replace("line3", "other"))
        assert target.read_text(encoding="utf-8") == (
            TestApplyUnifiedDiff.SOURCE)

    def test_apply_creates_a_new_file_whole(self, agent, tmp_path):
        record = agent.apply_edit_format(
            "born.py", "whole-file", "born = True\n")
        assert record["changed"] is True
        assert (tmp_path / "born.py").read_text(
            encoding="utf-8") == "born = True\n"


# ----------------------------------------------------------------------
# Surfaces: terminal + TUI share the parser and formatters
# ----------------------------------------------------------------------

class TestTerminalSurface:
    def test_show_set_and_choose(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/editformat")
        assert "Edit formats (M-071)" in text
        _, _, text = _slash(agent, "/editformat unified-diff")
        assert "auto -> unified-diff" in text
        assert agent.config["edit_format"] == "unified-diff"
        _, _, text = _slash(agent, "/editformat small-fix")
        assert "unified-diff" in text  # the pin is honoured

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/editformat sideways")
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


class TestEditFormatCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_editformat("")
        assert "Edit formats (M-071)" in _published_text(handler)

    def test_set_and_choose_via_the_handler(self, handler, agent):
        handler._handle_editformat("search-replace")
        assert "auto -> search-replace" in _published_text(handler)
        handler._handle_editformat("small-fix")
        assert "search-replace" in _published_text(handler)

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_editformat("sideways")
        assert "Usage" in _published_text(handler)


class TestChatScreenRouting:
    def test_editformat_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/editformat small-fix", _FakeLog())
        assert calls == [("/editformat", "small-fix")]


# ----------------------------------------------------------------------
# The config contract
# ----------------------------------------------------------------------

class TestConfigContract:
    def test_defaults_ship_auto(self):
        import yaml
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        defaults = yaml.safe_load(
            (root / "mythic_agent/data/config_defaults.yaml").read_text(
                encoding="utf-8"))
        assert defaults["edit_format"] == "auto"

    def test_catalogue_carries_the_setting(self):
        from mythic_agent.core.config_catalog import load_catalog

        by_name = {s.name: s for s in load_catalog().settings}
        assert by_name["edit_format"].id == "S-60"
        assert by_name["edit_format"].type == "str"
        assert by_name["edit_format"].default == "auto"

    def test_gap_audit_has_no_m071_row(self):
        # Checked at build time (the house pattern): no census
        # gap row is owned by M-071, so no module_kind flip
        # exists to make for this slice.
        import yaml
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        audit = yaml.safe_load(
            (root / "mythic_agent/data/gap_audit.yaml").read_text(
                encoding="utf-8"))
        assert [r for r in audit["rows"] if r["slice"] == "M-071"] == []
