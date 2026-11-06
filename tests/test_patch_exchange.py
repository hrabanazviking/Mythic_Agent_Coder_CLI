"""Tests for M-089: patch export/import (pure layer).

TIER: integration
"""

import pytest

from mythic_agent.core import patch_exchange as pe
from mythic_agent.core.change_sets import (
    attach_evidence,
    decide,
    make_edit,
    make_evidence,
    start_change_set,
)


def _set(name="hand-off fix", evidence=True, reject_second=False):
    edits = [make_edit("src/app.py", "whole-file", "x = 2\n"),
             make_edit("src/new.py", "whole-file", "y = 3\n")]
    result = start_change_set(name, edits)
    result = decide(result, 0, "accept")
    result = decide(result, 1, "reject" if reject_second else "accept")
    if evidence:
        result = attach_evidence(result, make_evidence(
            "pytest -q", 12, 0, 1, "logs/run.log"))
    return result


def test_export_starts_with_magic_and_header():
    text = pe.export_patch(_set())
    lines = text.splitlines()
    assert lines[0] == pe.MAGIC
    assert '"patch_header"' in lines[1]
    assert '"slice":"M-089"' in lines[1]


def test_round_trip_recovers_name_files_and_evidence():
    patch = pe.parse_patch(pe.export_patch(_set()))
    assert patch.name == "hand-off fix"
    assert [e.path for e in patch.edits] == ["src/app.py", "src/new.py"]
    assert patch.edits[0].payload == "x = 2\n"
    assert patch.evidence["verdict"] == "passed"
    assert patch.evidence["passed"] == 12
    assert patch.record()["slice"] == "M-089"


def test_round_trip_change_set_is_fully_accepted():
    patch = pe.parse_patch(pe.export_patch(_set()))
    rebuilt = patch.change_set()
    assert rebuilt.undecided() == []
    assert rebuilt.counts() == {"accepted": 2, "rejected": 0,
                                 "pending": 0}
    assert rebuilt.evidence.command == "pytest -q"


def test_pending_file_refuses_export_and_is_named():
    result = start_change_set("half", [make_edit(
        "src/app.py", "whole-file", "x = 2\n")])
    with pytest.raises(ValueError, match="not decided"):
        pe.export_patch(result)


def test_all_rejected_refuses_export():
    result = start_change_set("no", [make_edit(
        "src/app.py", "whole-file", "x = 2\n")])
    result = decide(result, 0, "reject")
    with pytest.raises(ValueError, match="every"):
        pe.export_patch(result)


def test_rejected_file_is_named_but_carries_no_payload():
    text = pe.export_patch(_set(reject_second=True))
    patch = pe.parse_patch(text)
    assert patch.rejected == ("src/new.py",)
    assert [e.path for e in patch.edits] == ["src/app.py"]
    assert "y = 3" not in text


def test_no_evidence_is_recorded_as_none():
    patch = pe.parse_patch(pe.export_patch(_set(evidence=False)))
    assert patch.evidence is None
    assert "none attached" in pe.format_patch(patch)


def test_failed_evidence_verdict_travels():
    result = _set(evidence=False)
    result = attach_evidence(result, make_evidence("pytest -q", 3, 2))
    patch = pe.parse_patch(pe.export_patch(result))
    assert patch.evidence["verdict"] == "failed"


def test_tampered_header_refuses():
    text = pe.export_patch(_set())
    bad = text.replace("hand-off fix", "hand-off fox", 1)
    with pytest.raises(ValueError, match="checksum"):
        pe.parse_patch(bad)


def test_tampered_payload_refuses_on_anchor():
    text = pe.export_patch(_set())
    bad = text.replace("x = 2", "x = 9", 1)
    with pytest.raises(ValueError, match="anchor"):
        pe.parse_patch(bad)


def test_wrong_magic_refuses():
    with pytest.raises(ValueError, match="not a patch file"):
        pe.parse_patch("SOMETHING ELSE\n{}")


def test_trailing_bytes_refuse():
    text = pe.export_patch(_set()) + "smuggled\n"
    with pytest.raises(ValueError, match="after its last section"):
        pe.parse_patch(text)


def test_truncated_payload_refuses():
    text = pe.export_patch(_set())
    with pytest.raises(ValueError):
        pe.parse_patch(text[:len(text) - 8])


def test_payload_with_header_like_lines_round_trips():
    tricky = 'MYTHIC-PATCH/1\n{"path": "fake"}\nreal = 1\n'
    result = start_change_set("tricky", [make_edit(
        "src/t.py", "whole-file", tricky)])
    result = decide(result, 0, "accept")
    patch = pe.parse_patch(pe.export_patch(result))
    assert patch.edits[0].payload == tricky


def test_payload_without_trailing_newline_round_trips():
    result = start_change_set("nonl", [make_edit(
        "src/t.py", "whole-file", "no newline at end")])
    result = decide(result, 0, "accept")
    patch = pe.parse_patch(pe.export_patch(result))
    assert patch.edits[0].payload == "no newline at end"


def test_unicode_payload_round_trips():
    result = start_change_set("uni", [make_edit(
        "src/t.py", "whole-file", "rune = 'ᚱ'\n")])
    result = decide(result, 0, "accept")
    patch = pe.parse_patch(pe.export_patch(result))
    assert patch.edits[0].payload == "rune = 'ᚱ'\n"


def test_import_plans_against_receiving_tree():
    text = pe.export_patch(_set())
    planned, outcome = pe.import_patch(
        text, {"src/app.py": "x = 1\n", "src/new.py": None})
    assert planned == {"src/app.py": "x = 2\n", "src/new.py": "y = 3\n"}
    assert outcome.applied == 2


def test_import_refuses_whole_set_on_one_stale_file():
    edits = [make_edit("src/a.py", "search-replace",
                       "<<<<<<< SEARCH\nold = 1\n=======\n"
                       "old = 2\n>>>>>>> REPLACE"),
             make_edit("src/b.py", "whole-file", "b = 2\n")]
    result = start_change_set("strict", edits)
    result = decide(decide(result, 0, "accept"), 1, "accept")
    text = pe.export_patch(result)
    with pytest.raises(ValueError, match="whole"):
        pe.import_patch(text, {"src/a.py": "changed = 9\n",
                               "src/b.py": "b = 1\n"})


def test_setting_gate_reads_config():
    assert pe.enabled_from_config({}) is True
    assert pe.enabled_from_config({"patch_exchange": False}) is False
    with pytest.raises(ValueError, match="true or false"):
        pe.enabled_from_config({"patch_exchange": "yes"})


def test_set_enabled_validates_and_records():
    enabled, change = pe.set_enabled({}, False)
    assert enabled is False
    assert change.event() == {"type": "patch_exchange_setting_changed",
                              "from": True, "to": False}
    with pytest.raises(ValueError, match="already on"):
        pe.set_enabled({}, True)
    with pytest.raises(ValueError, match="on or off"):
        pe.set_enabled({}, "off")


def test_parse_args_grammar():
    assert pe.parse_patch_args("") == {"action": "show"}
    assert pe.parse_patch_args("on") == {"action": "on"}
    assert pe.parse_patch_args("off") == {"action": "off"}
    assert pe.parse_patch_args("export my set name") == {
        "action": "export", "name": "my set name"}
    assert pe.parse_patch_args("import /tmp/a.patch") == {
        "action": "import", "ref": "/tmp/a.patch"}
    with pytest.raises(ValueError, match="usage"):
        pe.parse_patch_args("frobnicate")


def test_format_patch_names_rejected_and_evidence():
    patch = pe.parse_patch(pe.export_patch(
        _set(reject_second=True)))
    shown = pe.format_patch(patch)
    assert "src/new.py" in shown
    assert "rejected in review" in shown
    assert "passed" in shown


def test_format_patch_exchange_show_surface():
    shown = pe.format_patch_exchange({})
    assert "M-089" in shown
    assert "Setting: on (patch_exchange)" in shown
    assert "Plans whole on the receiving tree" in shown
    assert pe.format_patch_exchange(
        {"patch_exchange": False}).splitlines()[2] == \
        "Setting: off (patch_exchange)."


def test_format_setting_change():
    assert pe.format_setting_change({"to": True}) == \
        "Patch exchange is now on."
    assert pe.format_setting_change({"to": False}) == \
        "Patch exchange is now off."
