"""M-077 — Undo grown up.

TIER: integration

Covers the M-077 surface:

* the pure layer (``mythic_agent.core.undo_timeline``):
  workspace snapshots judged complete or incomplete with
  reasons, command footprints built from a before/after
  snapshot pair (created / changed / deleted files, each
  labelled certain or best-effort by the footprint's
  completeness and backups), the three strands merged
  into one timeline newest-first, and the walk judgement
  (only the newest entry undoes; a buried entry refuses
  and names the entry that blocks it),
* the durable store: footprints recorded with their
  backed-up before-contents, command undo all-or-nothing
  (a file changed since the command refuses the whole
  undo and changes nothing; a file too large to back up
  refuses rather than faking a restore), edits registered
  on the shared timeline at write time through the
  EditJournal hook,
* the checkpoint seam: entries and restores read through
  the CheckpointTimelineSource protocol only — a fake
  source proves the road, checkpoint entries default to
  the honest certainty ``unknown``, a source that does
  not speak the seam raises, and with no source wired
  the strand is reported DEPENDS-ON-M-075, never faked,
* ``Agent``: the gate status and ``set_undo_timeline``
  journaled as ``undo_timeline_setting_changed`` (a
  failed save restoring the previous value and
  journaling the revert), ``undo_newest`` / ``undo_kind``
  walking edits and commands as one timeline, the gate
  off refusing timeline undos and saying so,
* the tool road: a ``run_command`` through execute_tool
  records its footprint, and ``/undo command`` puts its
  files back; recording never alters the command result,
* the surfaces: the terminal ``/undo`` and the TUI
  ``/undo`` (system-command road through the
  CommandHandler), which share the parser and
  formatters — bare ``/undo`` keeps its original
  last-edit meaning when the newest entry is an edit,
* the config contract: ``undo_timeline`` ships in the
  defaults (True). Its M-009 catalogue entry (S-64) is a
  recorded integration delta in TEAM_LOG.md — the
  catalogue is a shared inventory surface the wave does
  not edit per-team.
"""

from __future__ import annotations

import pytest

from mythic_agent.core.edits import EditJournal
from mythic_agent.core.sessions import SessionStore
from mythic_agent.core.undo_timeline import (
    CERTAINTIES,
    CHECKPOINT_SOURCE_ATTR,
    KINDS,
    SETTING_KEY,
    UNDO_TIMELINE_SLICE,
    PLAIN_EXPLANATION,
    CheckpointTimelineSource,
    TimelineEntry,
    UndoStore,
    build_footprint,
    build_timeline,
    checkpoint_entries_from_source,
    enabled_from_config,
    format_setting_change,
    format_timeline,
    format_undo_outcome,
    format_undo_timeline,
    judge_walk,
    parse_undo_args,
    set_enabled,
    take_snapshot,
)


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


def _entry(kind, ref_id, seq, certainty="certain", label=None):
    return TimelineEntry(
        kind=kind, ref_id=ref_id, label=label or ref_id,
        detail="detail", seq=seq, certainty=certainty)


class FakeCheckpointSource:
    """A checkpoint source speaking only the seam."""

    def __init__(self):
        self.restored = []
        self.entries = [
            {"id": "cp-1", "name": "before the auth rework"},
            {"id": "cp-2", "label": "after the auth rework",
             "certainty": "certain"},
        ]

    def list_checkpoint_entries(self):
        return list(self.entries)

    def restore_checkpoint(self, checkpoint_id):
        self.restored.append(checkpoint_id)
        return f"Restored checkpoint {checkpoint_id} (fake seam)."


class TestConstants:
    def test_slice_kinds_and_certainties(self):
        assert UNDO_TIMELINE_SLICE == "M-077"
        assert SETTING_KEY == "undo_timeline"
        assert KINDS == ("edit", "command", "checkpoint")
        assert CERTAINTIES == ("certain", "best-effort", "unknown")
        assert "one timeline" in PLAIN_EXPLANATION
        assert "best-effort" in PLAIN_EXPLANATION
        assert CHECKPOINT_SOURCE_ATTR == "checkpoint_timeline_source"


class TestSnapshotsAndFootprints:
    def test_snapshot_of_a_small_tree_is_complete(self, tmp_path):
        (tmp_path / "a.txt").write_text("alpha", encoding="utf-8")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "b.txt").write_text("beta", encoding="utf-8")
        snap = take_snapshot(tmp_path)
        assert snap.complete is True
        assert set(snap.hashes) == {"a.txt", "sub/b.txt"}
        assert snap.contents["a.txt"] == b"alpha"

    def test_snapshot_ignores_git_internals(self, tmp_path):
        git = tmp_path / ".git"
        git.mkdir()
        (git / "HEAD").write_text("ref", encoding="utf-8")
        (tmp_path / "a.txt").write_text("alpha", encoding="utf-8")
        snap = take_snapshot(tmp_path)
        assert set(snap.hashes) == {"a.txt"}

    def test_footprint_judges_created_changed_deleted(
            self, tmp_path):
        (tmp_path / "keep.txt").write_text("same", encoding="utf-8")
        (tmp_path / "change.txt").write_text("old", encoding="utf-8")
        (tmp_path / "gone.txt").write_text("bye", encoding="utf-8")
        before = take_snapshot(tmp_path)
        (tmp_path / "change.txt").write_text("new", encoding="utf-8")
        (tmp_path / "gone.txt").unlink()
        (tmp_path / "born.txt").write_text("hi", encoding="utf-8")
        after = take_snapshot(tmp_path)
        footprint = build_footprint("do things", before, after)
        kinds = {c.path: c.kind for c in footprint.changes}
        assert kinds == {"change.txt": "changed",
                         "gone.txt": "deleted",
                         "born.txt": "created"}
        assert footprint.certainty == "certain"
        assert footprint.complete is True

    def test_a_command_that_changes_nothing_is_certain(
            self, tmp_path):
        (tmp_path / "a.txt").write_text("alpha", encoding="utf-8")
        before = take_snapshot(tmp_path)
        footprint = build_footprint("true", before,
                                    take_snapshot(tmp_path))
        assert footprint.changes == ()
        assert footprint.certainty == "certain"

    def test_an_unbacked_up_file_makes_it_best_effort(
            self, tmp_path, monkeypatch):
        import mythic_agent.core.undo_timeline as undo_module

        (tmp_path / "big.txt").write_text("x" * 64,
                                          encoding="utf-8")
        monkeypatch.setattr(undo_module, "MAX_BACKUP_BYTES", 8)
        before = take_snapshot(tmp_path)
        (tmp_path / "big.txt").write_text("y" * 64,
                                          encoding="utf-8")
        after = take_snapshot(tmp_path)
        footprint = build_footprint("rewrite big", before, after)
        assert footprint.certainty == "best-effort"
        assert any("too large" in reason
                   for reason in footprint.reasons)

    def test_footprint_event_carries_the_label(self, tmp_path):
        before = take_snapshot(tmp_path)
        (tmp_path / "a.txt").write_text("alpha", encoding="utf-8")
        footprint = build_footprint("touch a", before,
                                    take_snapshot(tmp_path))
        event = footprint.event()
        assert event["type"] == "command_footprint_recorded"
        assert event["files"] == 1
        assert event["certainty"] == "certain"


class TestTimelineWalk:
    def test_build_timeline_orders_newest_first(self):
        entries = build_timeline([
            _entry("edit", "1", seq=1),
            _entry("command", "2", seq=3, certainty="best-effort"),
            _entry("checkpoint", "3", seq=2, certainty="unknown"),
        ])
        assert [e.kind for e in entries] == [
            "command", "checkpoint", "edit"]

    def test_build_timeline_refuses_unknown_kinds(self):
        with pytest.raises(ValueError, match="timeline entry"):
            build_timeline([_entry("widget", "1", seq=1)])
        with pytest.raises(ValueError, match="certainty"):
            build_timeline([
                _entry("edit", "1", seq=1, certainty="maybe")])

    def test_judge_walk_allows_only_the_newest(self):
        entries = build_timeline([
            _entry("edit", "1", seq=1, label="app.py"),
            _entry("command", "2", seq=2, label="make"),
        ])
        judge_walk(entries, entries[0])
        with pytest.raises(ValueError, match="must be undone first"):
            judge_walk(entries, entries[1])

    def test_judge_walk_names_the_blocker(self):
        entries = build_timeline([
            _entry("edit", "1", seq=1, label="app.py"),
            _entry("command", "2", seq=2, label="make all"),
        ])
        with pytest.raises(ValueError, match="make all"):
            judge_walk(entries, entries[1])


class TestCheckpointSeam:
    def test_a_fake_source_speaks_the_protocol(self):
        source = FakeCheckpointSource()
        assert isinstance(source, CheckpointTimelineSource)
        entries = checkpoint_entries_from_source(source)
        assert entries[0] == {"id": "cp-1",
                              "label": "before the auth rework",
                              "certainty": "unknown"}
        assert entries[1]["certainty"] == "certain"

    def test_no_source_is_an_empty_strand(self):
        assert checkpoint_entries_from_source(None) == []

    def test_a_source_off_the_seam_raises(self):
        with pytest.raises(ValueError, match="checkpoint source"):
            checkpoint_entries_from_source(object())

    def test_an_entry_without_an_id_raises(self):
        class Bad:
            def list_checkpoint_entries(self):
                return [{"name": "nameless"}]

            def restore_checkpoint(self, checkpoint_id):
                return ""

        with pytest.raises(ValueError, match="no usable id"):
            checkpoint_entries_from_source(Bad())


class TestGate:
    def test_gate_defaults_on_and_validates(self):
        assert enabled_from_config({}) is True
        assert enabled_from_config({"undo_timeline": False}) is False
        with pytest.raises(ValueError, match="true or false"):
            enabled_from_config({"undo_timeline": "yes"})

    def test_set_enabled(self):
        value, change = set_enabled({}, False)
        assert value is False
        assert change.before is True and change.after is False
        assert change.event()["type"] == \
            "undo_timeline_setting_changed"
        with pytest.raises(ValueError, match="already on"):
            set_enabled({}, True)
        with pytest.raises(ValueError, match="on or off"):
            set_enabled({}, "off")


class TestStore:
    def _record(self, tmp_path, command="do things"):
        (tmp_path / "change.txt").write_text("old",
                                             encoding="utf-8")
        before = take_snapshot(tmp_path)
        (tmp_path / "change.txt").write_text("new",
                                             encoding="utf-8")
        (tmp_path / "born.txt").write_text("hi", encoding="utf-8")
        after = take_snapshot(tmp_path)
        footprint = build_footprint(command, before, after)
        store = UndoStore(tmp_path)
        command_id = store.record_footprint(footprint, before)
        return store, command_id

    def test_record_and_undo_a_footprint(self, tmp_path):
        store, command_id = self._record(tmp_path)
        records = store.footprints()
        assert records[0]["certainty"] == "certain"
        assert records[0]["files"] == 2
        outcome = store.undo_footprint(command_id)
        assert outcome.restored == 1 and outcome.deleted == 1
        assert outcome.certainty == "certain"
        assert (tmp_path / "change.txt").read_text(
            encoding="utf-8") == "old"
        assert not (tmp_path / "born.txt").exists()
        assert store.footprints() == []

    def test_undo_recreates_a_deleted_file(self, tmp_path):
        (tmp_path / "gone.txt").write_text("bye", encoding="utf-8")
        before = take_snapshot(tmp_path)
        (tmp_path / "gone.txt").unlink()
        footprint = build_footprint(
            "rm gone", before, take_snapshot(tmp_path))
        store = UndoStore(tmp_path)
        command_id = store.record_footprint(footprint, before)
        outcome = store.undo_footprint(command_id)
        assert outcome.recreated == 1
        assert (tmp_path / "gone.txt").read_text(
            encoding="utf-8") == "bye"

    def test_a_file_changed_since_refuses_the_whole_undo(
            self, tmp_path):
        store, command_id = self._record(tmp_path)
        (tmp_path / "born.txt").write_text("user work",
                                           encoding="utf-8")
        with pytest.raises(ValueError, match="changed after"):
            store.undo_footprint(command_id)
        # nothing was touched: the other file keeps the
        # command's change, and the footprint stays recorded
        assert (tmp_path / "change.txt").read_text(
            encoding="utf-8") == "new"
        assert len(store.footprints()) == 1

    def test_an_unbacked_up_file_refuses_rather_than_fakes(
            self, tmp_path, monkeypatch):
        import mythic_agent.core.undo_timeline as undo_module

        (tmp_path / "big.txt").write_text("x" * 64,
                                          encoding="utf-8")
        monkeypatch.setattr(undo_module, "MAX_BACKUP_BYTES", 8)
        before = take_snapshot(tmp_path)
        (tmp_path / "big.txt").write_text("y" * 64,
                                          encoding="utf-8")
        footprint = build_footprint(
            "rewrite big", before, take_snapshot(tmp_path))
        store = UndoStore(tmp_path)
        command_id = store.record_footprint(footprint, before)
        with pytest.raises(ValueError, match="not backed up"):
            store.undo_footprint(command_id)
        assert (tmp_path / "big.txt").read_text(
            encoding="utf-8") == "y" * 64

    def test_an_unknown_footprint_refuses(self, tmp_path):
        with pytest.raises(ValueError, match="no recorded"):
            UndoStore(tmp_path).undo_footprint(99)

    def test_an_empty_footprint_undoes_as_a_certain_no_change(
            self, tmp_path):
        before = take_snapshot(tmp_path)
        footprint = build_footprint("true", before,
                                    take_snapshot(tmp_path))
        store = UndoStore(tmp_path)
        command_id = store.record_footprint(footprint, before)
        outcome = store.undo_footprint(command_id)
        assert outcome.changed is False
        assert outcome.certainty == "certain"

    def test_edits_register_on_the_timeline_at_write_time(
            self, agent, tmp_path):
        journal = EditJournal(tmp_path)
        journal.write("app.py", "alpha = 1\n")
        journal.write("app.py", "alpha = 2\n")
        entries = UndoStore(tmp_path).timeline(journal.entries())
        assert [e.kind for e in entries] == ["edit", "edit"]
        assert entries[0].label == "app.py"
        assert entries[0].seq > entries[1].seq

    def test_timeline_merges_all_three_strands(
            self, agent, tmp_path):
        journal = EditJournal(tmp_path)
        journal.write("app.py", "alpha = 1\n")
        store, _ = self._record(tmp_path)
        checkpoints = checkpoint_entries_from_source(
            FakeCheckpointSource())
        entries = store.timeline(journal.entries(), checkpoints)
        kinds = [e.kind for e in entries]
        assert kinds[0] == "checkpoint"
        assert set(kinds) == {"edit", "command", "checkpoint"}
        by_label = {e.label: e for e in entries
                    if e.kind == "checkpoint"}
        assert by_label["before the auth rework"].certainty == \
            "unknown"
        assert by_label["after the auth rework"].certainty == \
            "certain"


class TestParserAndFormatters:
    def test_parse_args(self):
        assert parse_undo_args("") == {"action": "next", "count": 1}
        assert parse_undo_args("list") == {"action": "show"}
        assert parse_undo_args("edit") == {
            "action": "kind", "kind": "edit"}
        assert parse_undo_args("command") == {
            "action": "kind", "kind": "command"}
        assert parse_undo_args("checkpoint cp-1") == {
            "action": "checkpoint", "checkpoint_id": "cp-1"}
        assert parse_undo_args("3") == {"action": "next", "count": 3}
        assert parse_undo_args("off") == {
            "action": "setting", "enabled": False}
        with pytest.raises(ValueError, match="Usage"):
            parse_undo_args("sideways")
        with pytest.raises(ValueError, match="Usage"):
            parse_undo_args("checkpoint")
        with pytest.raises(ValueError, match="Usage"):
            parse_undo_args("0")

    def test_format_timeline_labels_certainty(self):
        entries = build_timeline([
            _entry("command", "2", seq=2, certainty="best-effort",
                   label="make all"),
            _entry("edit", "1", seq=1, label="app.py"),
        ])
        text = format_timeline(entries)
        assert "2 entries" in text
        assert "[command] make all" in text
        assert "(undo: best-effort)" in text
        assert format_timeline(()) .startswith(
            "The undo timeline is empty")

    def test_format_undo_timeline_shows_the_seam_state(self):
        text = format_undo_timeline({})
        assert "Undo grown up (M-077)" in text
        assert "Setting: on (undo_timeline)" in text
        assert "DEPENDS-ON-M-075" in text
        wired = format_undo_timeline({}, checkpoint_wired=True)
        assert "wired through the checkpoint seam" in wired
        assert "Usage: /undo" in wired

    def test_format_setting_change(self):
        record = {"from": True, "to": False}
        assert format_setting_change(record) == \
            "Undo timeline: on -> off."

    def test_format_undo_outcome_for_a_command(self):
        record = {"kind": "command", "label": "make",
                  "certainty": "certain", "restored": 1,
                  "deleted": 2, "recreated": 0}
        text = format_undo_outcome(record)
        assert "Undid command 'make' (certain)" in text
        assert "1 file(s) restored" in text


class TestAgentGate:
    def test_status(self, agent):
        status = agent.undo_timeline_status()
        assert status["enabled"] is True
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["checkpoint_wired"] is True  # wired to M-075 at banking
        assert status["entries"] == []

    def test_set_without_session(self, agent):
        record = agent.set_undo_timeline(False)
        assert record["journaled"] is False
        assert agent.config["undo_timeline"] is False
        with pytest.raises(ValueError, match="already off"):
            agent.set_undo_timeline(False)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_undo_timeline(False)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "undo_timeline_setting_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_undo_timeline(False)
        assert agent.config.get("undo_timeline") is not False
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["undo_timeline_setting_changed",
                              "undo_timeline_setting_reverted"]
        agent.close()


class TestAgentWalk:
    def test_bare_undo_of_an_edit_matches_the_legacy_words(
            self, agent, tmp_path):
        journal = EditJournal(tmp_path)
        journal.write("app.py", "alpha = 1\n")
        record = agent.undo_newest()
        assert record["changed"] is True
        assert record["message"].startswith(
            "Restored the last agent edit: app.py")
        assert not (tmp_path / "app.py").exists()

    def test_nothing_to_undo_is_an_honest_message(self, agent):
        record = agent.undo_newest()
        assert record["changed"] is False
        assert "Nothing to undo" in record["message"]

    def test_a_command_over_an_edit_walks_in_order(
            self, agent, tmp_path):
        journal = EditJournal(tmp_path)
        journal.write("app.py", "alpha = 1\n")
        (tmp_path / "made.txt").write_text("v1", encoding="utf-8")
        before = take_snapshot(tmp_path)
        (tmp_path / "made.txt").write_text("v2", encoding="utf-8")
        footprint = build_footprint(
            "rewrite made", before, take_snapshot(tmp_path))
        UndoStore(tmp_path).record_footprint(footprint, before)
        # the edit is buried under the command: kind-undo refuses
        with pytest.raises(ValueError, match="must be undone first"):
            agent.undo_kind("edit")
        # walking from the top undoes the command, then the edit
        record = agent.undo_newest()
        assert record["kind"] == "command"
        assert (tmp_path / "made.txt").read_text(
            encoding="utf-8") == "v1"
        record = agent.undo_newest()
        assert record["kind"] == "edit"
        assert not (tmp_path / "app.py").exists()

    def test_gate_off_refuses_timeline_undos(self, agent, tmp_path):
        EditJournal(tmp_path).write("app.py", "alpha = 1\n")
        agent.set_undo_timeline(False)
        with pytest.raises(ValueError, match="undo timeline is off"):
            agent.undo_newest()
        assert (tmp_path / "app.py").exists()

    def test_checkpoint_restore_through_a_wired_source(
            self, agent, tmp_path):
        source = FakeCheckpointSource()
        agent.checkpoint_timeline_source = source
        status = agent.undo_timeline_status()
        assert status["checkpoint_wired"] is True
        assert [e["kind"] for e in status["entries"]] == [
            "checkpoint", "checkpoint"]
        record = agent.restore_checkpoint_via_seam("cp-1")
        assert record["changed"] is True
        assert source.restored == ["cp-1"]
        assert "fake seam" in record["message"]

    def test_checkpoint_restore_without_a_source_refuses(
            self, agent):
        agent.checkpoint_timeline_source = None  # unwired explicitly
        with pytest.raises(ValueError, match="DEPENDS-ON-M-075"):
            agent.restore_checkpoint_via_seam("cp-1")

    def test_an_unknown_checkpoint_refuses(self, agent):
        agent.checkpoint_timeline_source = FakeCheckpointSource()
        with pytest.raises(ValueError, match="no checkpoint"):
            agent.restore_checkpoint_via_seam("cp-99")


class TestToolRoad:
    def test_run_command_records_a_footprint_and_undo_restores(
            self, agent, tmp_path):
        from mythic_agent.agents.tools import execute_tool

        target = tmp_path / "made.txt"
        target.write_text("v1", encoding="utf-8")
        result = execute_tool(
            "run_command",
            {"command": "printf v2 > made.txt && printf new > born.txt"},
            project_root=tmp_path, agent=agent)
        assert "v2" in target.read_text(encoding="utf-8")
        assert (tmp_path / "born.txt").exists()
        records = UndoStore(tmp_path).footprints()
        assert len(records) == 1
        assert records[0]["files"] == 2
        assert records[0]["certainty"] == "certain"
        record = agent.undo_kind("command")
        assert record["kind"] == "command"
        assert target.read_text(encoding="utf-8") == "v1"
        assert not (tmp_path / "born.txt").exists()
        assert isinstance(result, str) and result

    def test_a_read_only_command_records_an_empty_footprint(
            self, agent, tmp_path):
        from mythic_agent.agents.tools import execute_tool

        (tmp_path / "a.txt").write_text("alpha", encoding="utf-8")
        execute_tool("run_command", {"command": "cat a.txt"},
                     project_root=tmp_path, agent=agent)
        records = UndoStore(tmp_path).footprints()
        assert len(records) == 1
        assert records[0]["files"] == 0
        assert records[0]["certainty"] == "certain"


class TestTerminalSurface:
    def test_show_and_set(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/undo list")
        assert "Undo grown up (M-077)" in text
        assert "wired through the checkpoint seam" in text  # M-075 wired at banking
        _, _, text = _slash(agent, "/undo off")
        assert "on -> off" in text
        assert agent.config["undo_timeline"] is False
        _, _, text = _slash(agent, "/undo on")
        assert "off -> on" in text

    def test_bare_undo_undoes_the_newest_edit(self, agent, tmp_path):
        from mythic_agent.terminal import _slash

        EditJournal(tmp_path).write("app.py", "alpha = 1\n")
        _, _, text = _slash(agent, "/undo")
        assert text.startswith("Restored the last agent edit")
        assert not (tmp_path / "app.py").exists()

    def test_bare_undo_with_the_gate_off_keeps_the_legacy_road(
            self, agent, tmp_path):
        from mythic_agent.terminal import _slash

        EditJournal(tmp_path).write("app.py", "alpha = 1\n")
        agent.set_undo_timeline(False)
        _, _, text = _slash(agent, "/undo")
        assert text.startswith("Restored the last agent edit")
        # the timeline forms refuse while the gate is off
        _, _, text = _slash(agent, "/undo command")
        assert "Undo timeline is off" in text

    def test_walk_back_two_entries(self, agent, tmp_path):
        from mythic_agent.terminal import _slash

        journal = EditJournal(tmp_path)
        journal.write("a.py", "a = 1\n")
        journal.write("b.py", "b = 1\n")
        _, _, text = _slash(agent, "/undo 2")
        assert text.count("Restored the last agent edit") == 2
        assert not (tmp_path / "a.py").exists()
        assert not (tmp_path / "b.py").exists()

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/undo sideways")
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


class TestUndoCommand:
    def test_show_is_the_timeline(self, handler, agent):
        handler._handle_undo("list")
        assert "Undo grown up (M-077)" in _published_text(handler)

    def test_bare_undo_undoes_the_newest_edit(
            self, handler, agent, tmp_path):
        EditJournal(tmp_path).write("app.py", "alpha = 1\n")
        handler._handle_undo("")
        assert "Restored the last agent edit" in _published_text(
            handler)
        assert not (tmp_path / "app.py").exists()

    def test_set_via_the_handler(self, handler, agent):
        handler._handle_undo("off")
        assert "on -> off" in _published_text(handler)
        assert agent.config["undo_timeline"] is False

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_undo("sideways")
        assert "Usage" in _published_text(handler)


class TestConfigContract:
    def test_defaults_ship_on(self):
        import yaml
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        defaults = yaml.safe_load(
            (root / "mythic_agent/data/config_defaults.yaml")
            .read_text(encoding="utf-8"))
        assert defaults["undo_timeline"] is True


class TestCheckpointWiringAtBanking:
    """Coordinator wiring proof (M-077 banking): M-075's own
    checkpoints reach the undo timeline through the seam
    adapter the Agent now carries, and a seam restore drives
    M-075's restore road."""

    def test_m075_checkpoint_reaches_timeline_and_restores(
            self, agent, tmp_path):
        # the workspace sits in a subdir, as in M-075 own tests,
        # so the mythic state dir stays outside the tree
        from mythic_agent.agents import llm
        ws = tmp_path / "ws"
        ws.mkdir()
        agent = llm.Agent(project_root=ws)
        (ws / "app.py").write_text("alpha = 1\n")
        agent.take_checkpoint("before")
        status = agent.undo_timeline_status()
        assert status["checkpoint_wired"] is True
        entry = next(e for e in status["entries"]
                     if e["kind"] == "checkpoint")
        assert entry["label"] == "before"
        record = agent.restore_checkpoint_via_seam(entry["ref_id"])
        assert record["changed"] is True
        assert "Restored checkpoint" in record["message"]
        assert (ws / "app.py").read_text() == "alpha = 1\n"
