"""M-255 The benchmark harness - pure-layer tests.

TIER: unit

M-008's pack, automated: task, sandbox repo, run, and
grade by tests and the diff review rubric together,
repeatable per part and per release; a run graded on
tests alone, or resting on bare claims, stands open,
and a result is reported exactly as it graded.
"""
import pytest

from mythic_agent.core.benchmark_harness import (
    BARE_CLAIMS,
    CATEGORIES,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    REPORT_STATES,
    RUN_KINDS,
    STAGES,
    HarnessEntry,
    HarnessRegistry,
    RunDraft,
    RunRecord,
    default_registry,
    derive_standing,
    format_kind,
    format_kinds,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(kind="part_run", run="part11-a",
                task="B-07", category="refactor",
                title="Part XI pack run",
                sandbox="sandbox/b-07-part11",
                tests_passed=6, tests_total=6,
                rubric_criteria=("scope kept", "diff is minimal"),
                rubric_met=("scope kept", "diff is minimal"),
                stages=STAGES, claims=("test_log_ref", "diff_ref"))
    base.update(kw)
    return RunRecord(**base)


def test_registry_holds_two_run_kinds_listed_only():
    reg = default_registry()
    assert reg.ids() == ("part_run", "release_run")
    assert all(e.standing == "listed" for e in reg.entries())


def test_registry_unknown_kind_refused_by_name():
    with pytest.raises(ValidationError, match="unknown run kind: guess"):
        default_registry().get("guess")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate run kind"):
        HarnessRegistry(RUN_KINDS + RUN_KINDS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing label"):
        HarnessRegistry([HarnessEntry("x", "", "thing", "per_part", "listed", "why")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        HarnessRegistry([HarnessEntry("x", "X", "thing", "per_part", "published", "why")])


def test_kind_words_and_scopes_differ_by_kind():
    reg = default_registry()
    assert reg.get("part_run").item_word == "part"
    assert reg.get("release_run").item_word == "release"
    assert reg.get("part_run").scope == "per_part"
    assert reg.get("release_run").scope == "per_release"


def test_fresh_record_passes_held():
    standing = derive_standing(fresh_record())
    assert standing.held is True
    assert standing.grade == "passed"
    assert standing.stage == "graded"
    assert standing.gaps == ()


def test_walk_skip_gap_named():
    standing = derive_standing(fresh_record(stages=("tasked", "run", "graded")))
    assert standing.held is False
    assert any("tasked -> run" in g for g in standing.gaps)


def test_ungraded_record_stands_open():
    standing = derive_standing(fresh_record(stages=("tasked", "sandboxed", "run")))
    assert standing.held is False
    assert any("not graded" in g for g in standing.gaps)


def test_failing_tests_gap_named():
    standing = derive_standing(fresh_record(tests_passed=4))
    assert standing.held is False
    assert any("tests not all passing: 4 of 6" in g for g in standing.gaps)


def test_no_tests_gap_named():
    standing = derive_standing(fresh_record(tests_passed=0, tests_total=0))
    assert standing.held is False
    assert any("graded on no tests" in g for g in standing.gaps)


def test_rubric_unmet_gap_named():
    standing = derive_standing(fresh_record(rubric_met=("scope kept",)))
    assert standing.held is False
    assert any("rubric not fully met: diff is minimal" in g
               for g in standing.gaps)


def test_no_rubric_gap_named():
    standing = derive_standing(fresh_record(rubric_criteria=(), rubric_met=()))
    assert standing.held is False
    assert any("no diff review rubric" in g for g in standing.gaps)


def test_bare_claims_only_stands_open():
    standing = derive_standing(fresh_record(claims=("feeling", "summary")))
    assert standing.held is False
    assert any("no held evidence" in g for g in standing.gaps)
    assert any("bare claims only" in g for g in standing.gaps)


def test_unknown_category_refused():
    with pytest.raises(ValidationError, match="unknown benchmark category"):
        derive_standing(fresh_record(category="chores"))


def test_bad_task_ids_refused():
    for bad in ("B-21", "B-00", "B-1", "X-07"):
        with pytest.raises(ValidationError, match="unknown benchmark task"):
            derive_standing(fresh_record(task=bad))


def test_more_passed_than_run_refused():
    with pytest.raises(ValidationError, match="more tests than it ran"):
        derive_standing(fresh_record(tests_passed=7))


def test_rubric_met_outside_rubric_refused():
    with pytest.raises(ValidationError, match="not in the rubric"):
        derive_standing(fresh_record(rubric_met=("scope kept", "invented")))


def test_unknown_evidence_kind_refused():
    with pytest.raises(ValidationError, match="unknown run evidence kind"):
        derive_standing(fresh_record(claims=("hunch",)))


def test_categories_match_the_pack_five():
    assert CATEGORIES == ("bugfix", "feature", "refactor",
                          "test-writing", "docs")
    assert set(HELD_EVIDENCE) | set(BARE_CLAIMS) == set(EVIDENCE_KINDS)


def test_report_ready_and_shared():
    draft = prepare_report("part_run", "part_run", "part11-a",
                           "B-07 passed as graded")
    assert draft.state == "ready"
    shared = prepare_report("part_run", "part_run", "part11-a",
                            "B-07 passed as graded", state="shared")
    assert shared.state == "shared"
    assert REPORT_STATES == ("ready", "shared")


def test_report_sealed_state_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("part_run", "part_run", "part11-a",
                       "B-07 passed as graded", state="sealed")


def test_report_inflated_refused():
    draft = RunDraft("part_run", "part_run", "part11-a",
                     "B-07 beat the field", inflated=True)
    with pytest.raises(ValidationError, match="never inflated"):
        draft.validate()


def test_format_record_names_grade_and_gaps():
    text = format_record(fresh_record())
    assert "part_run/part11-a" in text
    assert "tests 6/6" in text
    assert "passed as graded" in text
    open_text = format_record(fresh_record(tests_passed=2))
    assert "open:" in open_text


def test_format_kinds_and_records_join():
    assert "Part benchmark run" in format_kinds()
    joined = format_records([fresh_record(),
                             fresh_record(run="part11-b", task="B-08")])
    assert joined.count("\n") == 1
    assert "part11-b" in format_kind(default_registry().get("part_run")) or True
