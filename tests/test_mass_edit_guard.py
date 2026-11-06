"""Tests for M-093: guarded mass edits (pure layer).

TIER: integration
"""

import pytest

from mythic_agent.core import mass_edit_guard as mg


def plan(*entries):
    return [{"path": p, "before": b, "after": a}
            for p, b, a in entries]


SIMPLE = plan(
    ("a.py", "one\ntwo\n", "one\nTWO\n"),
    ("b.py", "x = 1\n", "x = 1\ny = 2\n"),
)


# --- the dry run counts a real diff --------------------

def test_report_counts_files_hunks_and_lines():
    report = mg.build_report(SIMPLE)
    assert len(report.files) == 2
    assert len(report.changed_files) == 2
    assert report.total_hunks == 2
    assert report.total_added == 2
    assert report.total_removed == 1


def test_per_file_counts_are_the_files_own():
    report = mg.build_report(SIMPLE)
    first, second = report.files
    assert (first.path, first.hunks, first.added,
            first.removed) == ("a.py", 1, 1, 1)
    assert (second.path, second.hunks, second.added,
            second.removed) == ("b.py", 1, 1, 0)


def test_empty_plan_refuses():
    with pytest.raises(ValueError, match="at least one"):
        mg.build_report([])


def test_non_mapping_entry_refuses():
    with pytest.raises(ValueError, match="mapping"):
        mg.build_report(["a.py"])


def test_unnamed_file_refuses():
    with pytest.raises(ValueError, match="name its file"):
        mg.build_report(plan(("", "a\n", "b\n")))


def test_duplicate_file_refuses():
    with pytest.raises(ValueError, match="twice"):
        mg.build_report(plan(
            ("a.py", "a\n", "b\n"),
            ("a.py", "a\n", "c\n")))


def test_non_text_proposal_refuses():
    with pytest.raises(ValueError, match="texts"):
        mg.build_report(
            [{"path": "a.py", "before": None,
              "after": "b\n"}])


def test_dot_slash_path_is_cleaned():
    report = mg.build_report(
        plan(("./a.py", "a\n", "b\n")))
    assert report.files[0].path == "a.py"


# --- unchanged files are not edits ----------------------

def test_unchanged_file_is_listed_not_counted():
    report = mg.build_report(plan(
        ("a.py", "same\n", "same\n"),
        ("b.py", "x\n", "y\n")))
    assert len(report.files) == 2
    assert len(report.changed_files) == 1
    assert report.files[0].changed is False
    assert report.files[0].risks == ("no change",)
    assert report.total_hunks == 1


# --- risks are mechanical -------------------------------

def test_binary_content_is_a_high_risk():
    report = mg.build_report(
        plan(("blob.bin", "a\x00b", "c\x00d")))
    assert "binary content" in report.files[0].risks
    assert report.files[0].high_risk is True


def test_deleting_every_line_is_a_high_risk():
    report = mg.build_report(
        plan(("a.py", "one\ntwo\n", "")))
    assert "deletes every line" in report.files[0].risks
    assert report.files[0].high_risk is True


def test_sensitive_paths_are_high_risks():
    for path in (".env", "keys/id_rsa", "cert.pem",
                 "api.key", "my_secret.txt",
                 ".ssh/config"):
        report = mg.build_report(
            plan((path, "old\n", "new\n")))
        assert "sensitive path" in \
            report.files[0].risks, path


def test_ordinary_path_carries_no_risk():
    report = mg.build_report(SIMPLE)
    assert report.files[0].risks == ()
    assert report.risks == ()


def test_large_file_risk_names_its_size():
    big = "x" * mg.LARGE_FILE_BYTES
    report = mg.build_report(
        plan(("big.txt", big, big + "y")))
    assert any(r.startswith("large file (")
               for r in report.files[0].risks)


def test_many_hunks_risk_is_counted():
    before = "\n".join(f"line {i}" for i in range(120))
    after_lines = [f"line {i}" for i in range(120)]
    for i in range(0, 120, 10):
        after_lines[i] = f"changed {i}"
    report = mg.build_report(plan(
        ("wide.py", before + "\n",
         "\n".join(after_lines) + "\n")))
    assert report.files[0].hunks >= mg.MANY_HUNKS
    assert any(r.startswith("many hunks (")
               for r in report.files[0].risks)


# --- mass is counted, approval binds exactly ------------

def test_two_changed_files_require_approval():
    assert mg.build_report(SIMPLE).requires_approval \
        is True


def test_single_ordinary_file_needs_no_approval():
    report = mg.build_report(
        plan(("a.py", "a\n", "b\n")))
    assert report.requires_approval is False
    mg.require_approval(report, None)


def test_single_high_risk_file_requires_approval():
    report = mg.build_report(
        plan((".env", "old\n", "new\n")))
    assert report.requires_approval is True


def test_fingerprint_is_stable_for_the_same_plan():
    assert mg.build_report(SIMPLE).fingerprint == \
        mg.build_report(SIMPLE).fingerprint


def test_approval_covers_the_report_it_approved():
    report = mg.build_report(SIMPLE)
    approval = mg.approve_report(report)
    assert mg.approval_covers(report, approval) is True
    assert mg.approval_covers(
        report, approval.record()) is True
    mg.require_approval(report, approval)


def test_one_changed_byte_breaks_the_approval():
    report = mg.build_report(SIMPLE)
    approval = mg.approve_report(report)
    tampered = mg.build_report(plan(
        ("a.py", "one\ntwo\n", "one\nTWO!\n"),
        ("b.py", "x = 1\n", "x = 1\ny = 2\n")))
    assert tampered.fingerprint != report.fingerprint
    assert mg.approval_covers(tampered, approval) \
        is False
    with pytest.raises(ValueError,
                       match="needs an approval"):
        mg.require_approval(tampered, approval)


def test_unapproved_and_false_approvals_cover_nothing():
    report = mg.build_report(SIMPLE)
    assert mg.approval_covers(report, None) is False
    assert mg.approval_covers(
        report, {"fingerprint": report.fingerprint,
                 "approved": False}) is False
    assert mg.approval_covers(report, "yes") is False
    with pytest.raises(ValueError):
        mg.require_approval(report, None)


def test_approval_record_names_slice_and_fingerprint():
    report = mg.build_report(SIMPLE)
    record = mg.approve_report(report).record()
    assert record["type"] == "mass_edit_approved"
    assert record["slice"] == "M-093"
    assert record["fingerprint"] == report.fingerprint
    assert record["approved"] is True


# --- the report reads in plain words --------------------

def test_format_report_counts_and_names_risks():
    report = mg.build_report(plan(
        ("a.py", "a\n", "b\n"),
        (".env", "old\n", "new\n")))
    text = mg.format_report(report)
    assert "2 file(s) to change" in text
    assert ".env" in text and "sensitive path" in text
    assert "Approval: required" in text
    assert report.fingerprint[:12] in text


def test_format_report_says_when_no_risks():
    report = mg.build_report(
        plan(("a.py", "a\n", "b\n")))
    text = mg.format_report(report)
    assert "Risks: none" in text
    assert "Approval: not required" in text


def test_record_round_trips_the_totals():
    record = mg.build_report(SIMPLE).record()
    assert record["slice"] == "M-093"
    assert record["changed_files"] == 2
    assert record["total_added"] == 2
    assert record["requires_approval"] is True
    assert len(record["files"]) == 2


# --- the gate setting -----------------------------------

def test_setting_defaults_on_and_reads_stored():
    assert mg.enabled_from_config({}) is True
    assert mg.enabled_from_config(
        {"mass_edit_guard": False}) is False


def test_malformed_setting_raises():
    with pytest.raises(ValueError,
                       match="must be true or false"):
        mg.enabled_from_config({"mass_edit_guard": "yes"})


def test_set_enabled_flips_and_records():
    value, change = mg.set_enabled({}, False)
    assert value is False
    assert change.event() == {
        "type": "mass_edit_guard_setting_changed",
        "from": True, "to": False}
    assert change.record("s1", True)["journaled"] is True


def test_set_enabled_refuses_same_and_non_bool():
    with pytest.raises(ValueError, match="already on"):
        mg.set_enabled({}, True)
    with pytest.raises(ValueError, match="on or off"):
        mg.set_enabled({}, "off")


def test_parse_args_grammar():
    assert mg.parse_mass_edit_args("") == {"action": "show"}
    assert mg.parse_mass_edit_args("show") == \
        {"action": "show"}
    assert mg.parse_mass_edit_args("on") == {"action": "on"}
    assert mg.parse_mass_edit_args("off") == \
        {"action": "off"}
    with pytest.raises(ValueError, match="Usage:"):
        mg.parse_mass_edit_args("apply now")


def test_format_setting_change():
    assert mg.format_setting_change({"to": False}) == \
        "Mass edit guard is now off."


def test_show_surface_exercises_the_report_road():
    text = mg.format_mass_edit_guard({})
    assert "Guarded mass edits (M-093)" in text
    assert "Setting: on (mass_edit_guard)" in text
    assert "notes.txt: no change" in text
    assert "sensitive path" in text
    assert "Approval: required" in text
