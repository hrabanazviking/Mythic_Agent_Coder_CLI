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
