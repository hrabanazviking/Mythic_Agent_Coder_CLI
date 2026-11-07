"""Tests for M-087: large-file and binary care.

TIER: integration
"""

import pytest

from mythic_agent.core import large_file_care as lfc


def test_empty_bytes_are_small_text():
    record = lfc.classify_bytes("src/empty.py", b"")
    assert record.is_binary is False
    assert record.size_class == "small"
    assert record.edit_mode == "whole_file"
    assert record.size_bytes == 0


def test_small_text_uses_whole_file_road():
    record = lfc.classify_text("src/app.py", "x = 1\n")
    assert record.edit_mode == "whole_file"
    assert "whole-file" in record.explanation
    assert str(lfc.WHOLE_FILE_LIMIT_BYTES) in record.explanation


def test_boundary_exactly_at_limit_is_whole_file():
    record = lfc.classify_bytes("a.txt", b"x" * lfc.WHOLE_FILE_LIMIT_BYTES)
    assert record.size_class == "small"
    assert record.edit_mode == "whole_file"


def test_one_byte_over_limit_uses_anchored_chunks():
    record = lfc.classify_bytes(
        "a.txt", b"x" * (lfc.WHOLE_FILE_LIMIT_BYTES + 1))
    assert record.size_class == "large"
    assert record.edit_mode == "anchored_chunks"
    assert "anchored chunks" in record.explanation


def test_large_mark_is_named_at_a_million_bytes():
    record = lfc.classify_bytes("a.txt", b"x" * lfc.LARGE_FILE_BYTES)
    assert record.size_class == "large"
    assert "large-file mark" in record.explanation


def test_nul_byte_classifies_binary_with_offset():
    record = lfc.classify_bytes("img/x.bin", b"abc\x00def")
    assert record.is_binary is True
    assert record.edit_mode == "refused"
    assert "offset 3" in record.binary_reason
    assert record.record()["slice"] == "M-087"


def test_invalid_utf8_classifies_binary():
    record = lfc.classify_bytes("img/x.bin", b"\xff\xfe\xfa")
    assert record.is_binary is True
    assert "not valid UTF-8" in record.binary_reason


def test_detect_binary_returns_none_for_text():
    assert lfc.detect_binary("héllo\n".encode("utf-8")) is None


def test_classify_rejects_non_bytes():
    with pytest.raises(ValueError):
        lfc.classify_bytes("a.txt", "text not bytes")


@pytest.mark.parametrize("bad", ["/abs/x.py", "../x.py", "a//b.py", ""])
def test_classify_refuses_dirty_paths(bad):
    with pytest.raises(ValueError):
        lfc.classify_text(bad, "x = 1\n")


def test_split_chunks_empty_text_has_none():
    assert lfc.split_chunks("") == []


def test_split_chunks_are_line_bound_and_contiguous():
    text = "line\n" * 60_000
    chunks = lfc.split_chunks(text)
    assert len(chunks) > 1
    assert chunks[0].start_line == 1
    for prev, nxt in zip(chunks, chunks[1:]):
        assert nxt.start_line == prev.end_line + 1
        assert nxt.index == prev.index + 1
    assert chunks[-1].end_line == 60_000
    assert "".join(c.text for c in chunks) == text
    for chunk in chunks:
        assert chunk.anchor == lfc.chunk_anchor(chunk.text)
        assert chunk.text.endswith("\n")


def test_single_long_line_forms_its_own_chunk():
    long_line = "x" * (lfc.CHUNK_TARGET_BYTES * 2) + "\n"
    chunks = lfc.split_chunks(long_line + "next\n")
    assert chunks[0].text == long_line
    assert chunks[0].start_line == 1 and chunks[0].end_line == 1


def test_apply_chunk_edit_replaces_only_that_chunk():
    text = "line\n" * 60_000
    chunks = lfc.split_chunks(text)
    target = chunks[1]
    edited = lfc.apply_chunk_edit(text, 1, target.anchor, "CHANGED\n")
    assert edited.startswith(chunks[0].text)
    assert "CHANGED\n" in edited
    assert edited.count("line\n") == 60_000 - (
        target.end_line - target.start_line + 1)


def test_apply_chunk_edit_accepts_short_anchor():
    text = "line\n" * 60_000
    chunks = lfc.split_chunks(text)
    edited = lfc.apply_chunk_edit(
        text, 0, chunks[0].anchor[:lfc.SHORT_HASH_LEN], "A\n")
    assert edited.startswith("A\n")


def test_apply_chunk_edit_stale_anchor_refuses():
    text = "line\n" * 60_000
    chunks = lfc.split_chunks(text)
    with pytest.raises(ValueError) as excinfo:
        lfc.apply_chunk_edit(text, 0, "0" * 64, "A\n")
    assert "anchor mismatch" in str(excinfo.value)
    assert chunks[0].anchor[:12] in str(excinfo.value)


def test_apply_chunk_edit_bad_anchor_form_raises():
    with pytest.raises(ValueError):
        lfc.apply_chunk_edit("x\n", 0, "zz", "A\n")


def test_apply_chunk_edit_index_out_of_range():
    with pytest.raises(ValueError):
        lfc.apply_chunk_edit("x\n", 5, "a" * 12, "A\n")


def test_assess_binary_refused_even_with_gate_off():
    record = lfc.classify_bytes("img/x.bin", b"a\x00b")
    assessment = lfc.assess_edit(record, config={"large_file_care": False})
    assert assessment.allowed is False
    assert assessment.edit_mode == "refused"


def test_assess_large_warns_and_allows_chunks():
    record = lfc.classify_bytes(
        "a.txt", b"x" * (lfc.WHOLE_FILE_LIMIT_BYTES + 1))
    assessment = lfc.assess_edit(record)
    assert assessment.allowed is True
    assert assessment.warns is True
    assert assessment.edit_mode == "anchored_chunks"


def test_assess_large_with_gate_off_refuses_and_says_so():
    record = lfc.classify_bytes(
        "a.txt", b"x" * (lfc.WHOLE_FILE_LIMIT_BYTES + 1))
    assessment = lfc.assess_edit(record, config={"large_file_care": False})
    assert assessment.allowed is False
    assert "large-file care is off" in assessment.warning


def test_assess_small_is_silent():
    record = lfc.classify_text("src/app.py", "x = 1\n")
    assessment = lfc.assess_edit(record)
    assert assessment.allowed is True
    assert assessment.warns is False
    assert assessment.warning is None


def test_enabled_from_config_malformed_raises():
    with pytest.raises(ValueError):
        lfc.enabled_from_config({"large_file_care": "yes"})


def test_set_enabled_change_and_same_state():
    enabled, change = lfc.set_enabled({}, False)
    assert enabled is False
    assert change.before is True and change.after is False
    assert change.event()["type"] == "large_file_care_setting_changed"
    with pytest.raises(ValueError):
        lfc.set_enabled({"large_file_care": False}, False)
    with pytest.raises(ValueError):
        lfc.set_enabled({}, "off")


def test_parse_args_grammar():
    assert lfc.parse_largefile_args("") == {"action": "show"}
    assert lfc.parse_largefile_args("show") == {"action": "show"}
    assert lfc.parse_largefile_args("on") == {"action": "on"}
    assert lfc.parse_largefile_args("off") == {"action": "off"}
    assert lfc.parse_largefile_args("src/app.py") == {
        "action": "check", "path": "src/app.py"}
    with pytest.raises(ValueError):
        lfc.parse_largefile_args("a.py b.py")
    with pytest.raises(ValueError):
        lfc.parse_largefile_args("../x.py")


def test_format_file_care_dict_and_dataclass_agree():
    record = lfc.classify_text("src/app.py", "x = 1\n")
    assert lfc.format_file_care(record) == lfc.format_file_care(
        record.record())


def test_format_chunk_plan_names_anchors():
    chunks = lfc.split_chunks("line\n" * 60_000)
    plan = lfc.format_chunk_plan(chunks)
    assert "anchored chunk" in plan
    assert chunks[0].anchor[:12] in plan


def test_format_show_exercises_all_three_roads():
    shown = lfc.format_large_file_care({})
    assert "Setting: on (large_file_care)" in shown
    assert "whole-file" in shown
    assert "anchored chunks" in shown
    assert "binary" in shown
    assert "/largefile <path>" in shown


def test_format_setting_change_words():
    assert lfc.format_setting_change({"to": False}) == (
        "Large-file care is now off.")


# ---------------------------------------------------------------------
# Agent layer + surfaces (keeper restart tick, 2026-11-06).
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore


def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")


LARGE_TEXT = "line\n" * 60_000


class TestAgentGate:
    def test_status(self, agent):
        status = agent.large_file_care_status()
        assert status["enabled"] is True
        assert status["explanation"] == lfc.PLAIN_EXPLANATION

    def test_set_without_session(self, agent):
        record = agent.set_large_file_care(False)
        assert record["journaled"] is False
        assert agent.config["large_file_care"] is False
        with pytest.raises(ValueError, match="already"):
            agent.set_large_file_care(False)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_large_file_care(False)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "large_file_care_setting_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_large_file_care(False)
        assert agent.config.get("large_file_care") is not False
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["large_file_care_setting_changed",
                              "large_file_care_setting_reverted"]
        agent.close()


class TestAgentCheck:
    def test_check_small_file(self, agent, tmp_path):
        (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
        data = agent.check_large_file("app.py")
        assert data["is_binary"] is False
        assert data["edit_mode"] == "whole_file"
        assert data["assessment"]["allowed"] is True
        assert data["chunks"] == []
        assert data["chunk_plan"] is None

    def test_check_binary_file(self, agent, tmp_path):
        (tmp_path / "x.bin").write_bytes(b"abc\x00def")
        data = agent.check_large_file("x.bin")
        assert data["is_binary"] is True
        assert data["edit_mode"] == "refused"
        assert data["assessment"]["allowed"] is False
        assert "offset 3" in data["binary_reason"]

    def test_check_large_file_returns_chunk_plan(self, agent, tmp_path):
        (tmp_path / "big.txt").write_text(LARGE_TEXT, encoding="utf-8")
        data = agent.check_large_file("big.txt")
        assert data["edit_mode"] == "anchored_chunks"
        assert data["assessment"]["warns"] is True
        assert len(data["chunks"]) > 1
        assert data["chunks"][0]["anchor"] in data["chunk_plan"]

    def test_check_missing_file_refuses(self, agent):
        with pytest.raises(ValueError, match="does not exist"):
            agent.check_large_file("nope.py")


class TestChunkEdit:
    def test_chunk_edit_applies_and_journals(self, agent, tmp_path):
        (tmp_path / "big.txt").write_text(LARGE_TEXT, encoding="utf-8")
        store = store_for(tmp_path)
        session_id = agent.attach_session(store)
        plan = agent.check_large_file("big.txt")
        first = plan["chunks"][0]
        chunks = lfc.split_chunks(LARGE_TEXT)
        data = agent.apply_large_file_chunk_edit(
            "big.txt", 0, chunks[0].anchor, "CHANGED\n")
        assert data["journaled"] is True
        assert data["chunk_index"] == 0
        text = (tmp_path / "big.txt").read_text(encoding="utf-8")
        assert text.startswith("CHANGED\n")
        assert text == "CHANGED\n" + "".join(
            c.text for c in chunks[1:])
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "large_file_chunk_edited" in types
        agent.close()

    def test_chunk_edit_accepts_short_anchor(self, agent, tmp_path):
        (tmp_path / "big.txt").write_text(LARGE_TEXT, encoding="utf-8")
        chunks = lfc.split_chunks(LARGE_TEXT)
        agent.apply_large_file_chunk_edit(
            "big.txt", 1, chunks[1].anchor[:lfc.SHORT_HASH_LEN], "B\n")
        text = (tmp_path / "big.txt").read_text(encoding="utf-8")
        assert text.startswith(chunks[0].text + "B\n")

    def test_chunk_edit_stale_anchor_refuses(self, agent, tmp_path):
        (tmp_path / "big.txt").write_text(LARGE_TEXT, encoding="utf-8")
        with pytest.raises(ValueError, match="anchor mismatch"):
            agent.apply_large_file_chunk_edit(
                "big.txt", 0, "0" * 64, "A\n")
        assert (tmp_path / "big.txt").read_text(
            encoding="utf-8") == LARGE_TEXT

    def test_chunk_edit_gate_off_refuses(self, agent, tmp_path):
        (tmp_path / "big.txt").write_text(LARGE_TEXT, encoding="utf-8")
        chunks = lfc.split_chunks(LARGE_TEXT)
        agent.set_large_file_care(False)
        with pytest.raises(ValueError, match="large-file care is off"):
            agent.apply_large_file_chunk_edit(
                "big.txt", 0, chunks[0].anchor, "A\n")
        assert (tmp_path / "big.txt").read_text(
            encoding="utf-8") == LARGE_TEXT

    def test_chunk_edit_small_file_refuses(self, agent, tmp_path):
        (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
        anchor = lfc.chunk_anchor("x = 1\n")
        with pytest.raises(ValueError, match="whole-file road"):
            agent.apply_large_file_chunk_edit("app.py", 0, anchor, "y\n")
        assert (tmp_path / "app.py").read_text(
            encoding="utf-8") == "x = 1\n"

    def test_chunk_edit_binary_refuses(self, agent, tmp_path):
        (tmp_path / "x.bin").write_bytes(b"a\x00b" * 100_000)
        with pytest.raises(ValueError, match="binary"):
            agent.apply_large_file_chunk_edit(
                "x.bin", 0, "a" * 12, "A\n")


class TestSaveRoad:
    def test_binary_edit_refuses_before_any_byte_moves(
            self, agent, tmp_path):
        (tmp_path / "x.bin").write_bytes(b"abc\x00def")
        with pytest.raises(ValueError, match="binary"):
            agent.apply_edit_format(
                "x.bin", "whole-file", "replacement")
        assert (tmp_path / "x.bin").read_bytes() == b"abc\x00def"

    def test_large_file_edit_warns_and_applies(self, agent, tmp_path):
        (tmp_path / "big.txt").write_text(LARGE_TEXT, encoding="utf-8")
        record = agent.apply_edit_format(
            "big.txt", "whole-file", LARGE_TEXT + "tail\n")
        assert record["large_file_warning"] is not None
        assert "anchored chunks" in record["large_file_warning"]
        assert (tmp_path / "big.txt").read_text(
            encoding="utf-8").endswith("tail\n")

    def test_large_file_edit_gate_off_refuses(self, agent, tmp_path):
        (tmp_path / "big.txt").write_text(LARGE_TEXT, encoding="utf-8")
        agent.set_large_file_care(False)
        with pytest.raises(ValueError, match="large-file care is off"):
            agent.apply_edit_format(
                "big.txt", "whole-file", LARGE_TEXT + "tail\n")
        assert (tmp_path / "big.txt").read_text(
            encoding="utf-8") == LARGE_TEXT

    def test_small_file_edit_has_no_warning(self, agent, tmp_path):
        (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
        record = agent.apply_edit_format(
            "app.py", "search-replace",
            "<<<<<<< SEARCH\nx = 1\n=======\nx = 2\n>>>>>>> REPLACE\n")
        assert record["large_file_warning"] is None


class TestTerminalSurface:
    def test_show_and_set(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/largefile")
        assert "Large-file and binary care (M-087)" in text
        assert "Setting: on (large_file_care)" in text
        _, _, text = _slash(agent, "/largefile off")
        assert "Large-file care is now off." in text
        assert agent.config["large_file_care"] is False
        _, _, text = _slash(agent, "/largefile on")
        assert "Large-file care is now on." in text

    def test_check_via_the_terminal(self, agent, tmp_path):
        from mythic_agent.terminal import _slash

        (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
        _, _, text = _slash(agent, "/largefile app.py")
        assert "whole-file" in text
        (tmp_path / "big.txt").write_text(LARGE_TEXT, encoding="utf-8")
        _, _, text = _slash(agent, "/largefile big.txt")
        assert "anchored chunk" in text
        (tmp_path / "x.bin").write_bytes(b"a\x00b")
        _, _, text = _slash(agent, "/largefile x.bin")
        assert "binary" in text

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/largefile a.py b.py")
        assert "usage" in text


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


class TestLargefileCommand:
    def test_show_is_default(self, handler, agent):
        handler._handle_largefile("")
        assert "Large-file and binary care (M-087)" in _published_text(
            handler)

    def test_set_via_the_handler(self, handler, agent):
        handler._handle_largefile("off")
        assert "Large-file care is now off." in _published_text(handler)
        assert agent.config["large_file_care"] is False

    def test_check_via_the_handler(self, handler, agent, tmp_path):
        (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
        handler._handle_largefile("app.py")
        assert "whole-file" in _published_text(handler)

    def test_usage_error_is_published(self, handler, agent):
        handler._handle_largefile("a.py b.py")
        assert "usage" in _published_text(handler)


class TestChatScreenRouting:
    def test_largefile_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/largefile off", _FakeLog())
        assert calls == [("/largefile", "off")]
