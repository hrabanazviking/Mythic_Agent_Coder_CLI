"""M-124 Parallel worktrees - pure-layer tests.

TIER: integration

The pure layer is the worktree discipline as data:
one assignment per crew member (member, office,
slice, branch, worktree path) validated as data,
a plan holding assignments under the house law
(never two writers in one tree; a member, a branch
or a path twice refuses; the coordinator holds no
assignment), the shipped example plan (the M-121
casting dealt one worktree each) held in a data
file, a loader that reads a plan from any file,
the coordinator merge plan derived in slice order,
a worktree record shaped as session news, and a
registry. Nothing here runs git, creates a
worktree, spawns an agent or runs a model.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.crew_members import load_casting, member_offices
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.worktrees import (
    PLAIN_EXPLANATION,
    USAGE,
    WORKTREES_RESOURCE,
    WORKTREES_SCHEMA,
    WORKTREES_SLICE,
    MergeStep,
    WorktreeAssignment,
    WorktreePlan,
    WorktreeRegistry,
    build_assignment,
    format_assignment,
    format_assignments,
    format_merge_plan,
    format_worktrees_screen,
    load_worktree_plan,
    load_worktree_plan_file,
    merge_plan_for,
    normalize_branch,
    normalize_slice_id,
    normalize_worktree_path,
    parse_worktrees_args,
    plain_words,
    suggest_branch,
    suggest_path,
    validate_assignment,
    validate_merge_steps,
    validate_plan,
    worktree_record,
)

ROOT = Path(__file__).resolve().parents[1]


def _assignment(**kwargs):
    kwargs.setdefault("member", "architect")
    kwargs.setdefault("office", "architect")
    kwargs.setdefault("slice_id", "M-125")
    kwargs.setdefault("branch", "crew/architect/m-125")
    kwargs.setdefault("path", "worktrees/architect")
    return WorktreeAssignment(**kwargs)


def _plan_data():
    return {
        "schema": WORKTREES_SCHEMA, "slice": WORKTREES_SLICE,
        "coordinator": "coordinator",
        "assignments": [
            {"member": "forge_worker", "office": "forge_worker",
             "slice_id": "M-128", "branch": "crew/forge_worker/m-128",
             "path": "worktrees/forge_worker"},
            {"member": "architect", "office": "architect",
             "slice_id": "M-125", "branch": "crew/architect/m-125",
             "path": "worktrees/architect"},
        ]}


def _plan():
    return WorktreePlan(
        assignments=[
            _assignment(member="forge_worker", office="forge_worker",
                        slice_id="M-128",
                        branch="crew/forge_worker/m-128",
                        path="worktrees/forge_worker"),
            _assignment(),
        ],
        coordinator="coordinator")


# -- constants and word readings --------------------------------------------


def test_constants_and_usage():
    assert WORKTREES_SLICE == "M-124"
    assert WORKTREES_SCHEMA == "mythic.worktrees/1"
    assert WORKTREES_RESOURCE == "worktrees.yaml"
    assert USAGE.startswith("Usage: /worktrees")
    assert "merges" in USAGE and "plan" in USAGE
    assert "never two writers in one tree" in PLAIN_EXPLANATION
    assert "coordinator" in PLAIN_EXPLANATION


def test_slice_readings():
    assert normalize_slice_id("M-124") == "M-124"
    assert normalize_slice_id("m-7") == "M-007"
    assert normalize_slice_id(" M-272 ") == "M-272"
    for bad in ("M-000", "M-273", "124", "M124", "M-12a", "", None, 124):
        with pytest.raises(ValueError):
            normalize_slice_id(bad)


def test_branch_readings():
    assert normalize_branch("crew/architect/m-125") == "crew/architect/m-125"
    assert normalize_branch("main") == "main"
    assert normalize_branch("fix/a.b-c_d") == "fix/a.b-c_d"
    for bad in ("", " crew//x", "a//b", "/lead", "trail/", ".dot/x",
                "a/../b", "a..b", "has space", "end.lock/x", "x/y.lock",
                "HEAD", "trail.", None, 4):
        with pytest.raises(ValueError):
            normalize_branch(bad)


def test_path_readings():
    assert normalize_worktree_path("worktrees/architect") == \
        "worktrees/architect"
    assert normalize_worktree_path("team-01") == "team-01"
    for bad in ("", "/abs/path", "a/../b", "../up", "a/./b", ".git/x",
                "a/.git", "a//b", "trail/", "back\\slash", "has space",
                None, 4):
        with pytest.raises(ValueError):
            normalize_worktree_path(bad)


def test_suggestions_are_valid_and_conventional():
    assert suggest_path("architect") == "worktrees/architect"
    assert suggest_branch("architect", "M-125") == "crew/architect/m-125"
    assert normalize_branch(suggest_branch("forge_worker", "m-9")) == \
        "crew/forge_worker/m-009"
    assert normalize_worktree_path(suggest_path("skald")) == \
        "worktrees/skald"


# -- the shipped example plan: the casting, one tree each -------------------


def test_shipped_plan_loads_as_the_casting():
    plan = load_worktree_plan()
    assert isinstance(plan, WorktreePlan)
    casting = load_casting()
    assert [a.member for a in plan.assignments] == \
        [m.member_id for m in casting.members]
    assert plan.coordinator == "coordinator"
    assert plan.plan_note
    assert "EXAMPLE PLAN" in plan.plan_note
    assert "never two writers in one tree" in plan.plan_note
    rebuilt = {"schema": WORKTREES_SCHEMA, "slice": WORKTREES_SLICE,
               "coordinator": plan.coordinator,
               "assignments": [{
                   "member": a.member, "office": a.office,
                   "slice_id": a.slice_id, "branch": a.branch,
                   "path": a.path} for a in plan.assignments]}
    assert validate_plan(rebuilt, require_example=True) == []


def test_shipped_plan_holds_the_house_law():
    plan = load_worktree_plan()
    casting = {m.member_id: m for m in load_casting().members}
    members = [a.member for a in plan.assignments]
    branches = [a.branch for a in plan.assignments]
    paths = [a.path for a in plan.assignments]
    slices = [a.slice_id for a in plan.assignments]
    assert len(set(members)) == len(members) == 8
    assert len(set(branches)) == len(branches)
    assert len(set(paths)) == len(paths)
    assert len(set(slices)) == len(slices)
    assert plan.coordinator not in members
    for assignment in plan.assignments:
        assert assignment.office == casting[assignment.member].office
        assert assignment.office in member_offices()
        assert assignment.branch == suggest_branch(
            assignment.member, assignment.slice_id)
        assert assignment.path == suggest_path(assignment.member)


def test_shipped_merge_plan_is_slice_order_by_coordinator():
    plan = load_worktree_plan()
    steps = merge_plan_for(plan)
    assert [s.slice_id for s in steps] == \
        [f"M-{n:03d}" for n in range(124, 132)]
    assert [s.order for s in steps] == list(range(1, 9))
    assert all(s.merger == "coordinator" for s in steps)
    assert validate_merge_steps(plan, steps) == []
    assert plan.merge_plan() == steps


# -- the assignment ----------------------------------------------------------


def test_assignment_construction_and_record():
    assignment = _assignment()
    assert assignment.member == "architect"
    assert assignment.assignment_id is None
    record = assignment.to_record()
    assert record["type"] == "worktree_assignment"
    assert record["slice"] == "M-124"
    assert record["member"] == "architect"
    assert record["office"] == "architect"
    assert record["slice_id"] == "M-125"
    assert record["branch"] == "crew/architect/m-125"
    assert record["path"] == "worktrees/architect"


def test_assignment_validator_refusals():
    for kwargs in (
            {"office": "primary"}, {"office": "captain"},
            {"member": ""}, {"member": "has space"},
            {"slice_id": "M-999"}, {"slice_id": "soon"},
            {"branch": "a//b"}, {"branch": "x.lock"},
            {"path": "/abs"}, {"path": "a/../b"}, {"path": ".git"}):
        with pytest.raises(ValueError):
            _assignment(**kwargs)


def test_assignment_mapping_aliases_and_refusals():
    built = validate_assignment({
        "member_id": "scribe", "office": "scribe", "slice": "M-129",
        "branch": "crew/scribe/m-129", "worktree_path": "worktrees/scribe",
        "id": "wave-1"})
    assert built.member == "scribe"
    assert built.slice_id == "M-129"
    assert built.path == "worktrees/scribe"
    assert built.assignment_id == "wave-1"
    assert build_assignment(built) is built
    with pytest.raises(ValueError):
        validate_assignment({
            "member": "scribe", "member_id": "skald", "office": "scribe",
            "slice_id": "M-129", "branch": "crew/scribe/m-129",
            "path": "worktrees/scribe"})
    with pytest.raises(ValueError):
        validate_assignment({
            "member": "scribe", "office": "scribe", "slice_id": "M-129",
            "branch": "crew/scribe/m-129", "path": "worktrees/scribe",
            "surprise": True})
    with pytest.raises(ValueError):
        validate_assignment({"member": "scribe", "office": "scribe"})
    with pytest.raises(ValueError):
        validate_assignment("not a mapping")


# -- the plan and the house law ----------------------------------------------


def test_plan_construction_holds_collisions():
    assert validate_plan(_plan_data()) == []
    plan = _plan()
    assert plan.get("architect").slice_id == "M-125"
    with pytest.raises(KeyError):
        plan.get("scribe")
    dup_member = _plan_data()
    dup_member["assignments"].append(
        {"member": "architect", "office": "architect",
         "slice_id": "M-126", "branch": "crew/architect/m-126",
         "path": "worktrees/architect-2"})
    assert any("two assignments" in p for p in validate_plan(dup_member))
    dup_branch = _plan_data()
    dup_branch["assignments"].append(
        {"member": "scribe", "office": "scribe", "slice_id": "M-129",
         "branch": "crew/architect/m-125", "path": "worktrees/scribe"})
    assert any("assigned twice" in p for p in validate_plan(dup_branch))
    dup_path = _plan_data()
    dup_path["assignments"].append(
        {"member": "scribe", "office": "scribe", "slice_id": "M-129",
         "branch": "crew/scribe/m-129", "path": "worktrees/architect"})
    assert any("two writers in one tree" in p
               for p in validate_plan(dup_path))
    with pytest.raises(ValueError):
        WorktreePlan(
            assignments=[_assignment(), _assignment(
                slice_id="M-126", branch="crew/architect/m-126",
                path="worktrees/architect-2")],
            coordinator="coordinator")


def test_plan_coordinator_holds_no_assignment():
    data = _plan_data()
    data["coordinator"] = "architect"
    problems = validate_plan(data)
    assert any("coordinator" in p and "merges" in p for p in problems)
    with pytest.raises(ValidationError):
        load_worktree_plan(data)


def test_plan_refusals():
    for mutate in (
            lambda d: d.update(schema="mythic.other/1"),
            lambda d: d.update(slice="M-999"),
            lambda d: d.update(assignments=[]),
            lambda d: d.update(surprise=True),
            lambda d: d.pop("coordinator"),
            lambda d: d.update(coordinator="has space")):
        data = _plan_data()
        mutate(data)
        assert validate_plan(data) != []
        with pytest.raises(ValidationError):
            load_worktree_plan(data)
    assert validate_plan("not a mapping") != []
    example = _plan_data()
    assert validate_plan(example, require_example=True) != []


# -- the merge plan ------------------------------------------------------------


def test_merge_plan_derives_slice_order_from_shuffled_plan():
    plan = _plan()  # file order: M-128 first, then M-125
    steps = merge_plan_for(plan)
    assert [s.slice_id for s in steps] == ["M-125", "M-128"]
    assert steps[0].member == "architect"
    assert steps[0].order == 1 and steps[1].order == 2
    assert all(s.merger == plan.coordinator for s in steps)
    assert validate_merge_steps(plan, steps) == []


def test_merge_steps_coordinator_only_refusal():
    plan = _plan()
    steps = list(merge_plan_for(plan))
    foreign = MergeStep(
        order=steps[0].order, slice_id=steps[0].slice_id,
        member=steps[0].member, branch=steps[0].branch,
        path=steps[0].path, merger="architect")
    problems = validate_merge_steps(plan, [foreign] + steps[1:])
    assert any("only the coordinator" in p for p in problems)
    assert validate_merge_steps(plan, steps[1:]) != []
    assert validate_merge_steps(plan, list(reversed(steps))) != []
    assert validate_merge_steps(plan, "not steps") != []
    assert validate_merge_steps("not a plan", steps) != []
    with pytest.raises(ValueError):
        MergeStep(order=0, slice_id="M-125", member="architect",
                  branch="crew/architect/m-125",
                  path="worktrees/architect", merger="coordinator")
    with pytest.raises(ValueError):
        merge_plan_for("not a plan")


# -- plan files on disk --------------------------------------------------------


def _write_plan(tmp_path, data):
    target = tmp_path / "wave_plan.yaml"
    target.write_text(yaml.safe_dump(data), encoding="utf-8")
    return target


def test_plan_file_roundtrip(tmp_path):
    target = _write_plan(tmp_path, _plan_data())
    plan = load_worktree_plan_file(target)
    assert [a.member for a in plan.assignments] == \
        ["forge_worker", "architect"]
    assert plan.coordinator == "coordinator"


def test_plan_file_single_assignment_and_refusals(tmp_path):
    single = {"schema": WORKTREES_SCHEMA, "slice": WORKTREES_SLICE,
              "coordinator": "coordinator",
              "assignments": [{
                  "member": "skald", "office": "skald",
                  "slice_id": "M-130", "branch": "crew/skald/m-130",
                  "path": "worktrees/skald"}]}
    plan = load_worktree_plan_file(_write_plan(tmp_path, single))
    assert len(plan.assignments) == 1
    bad = _plan_data()
    bad["assignments"][0]["path"] = "/etc/passwd"
    with pytest.raises(ValidationError):
        load_worktree_plan_file(_write_plan(tmp_path, bad))
    with pytest.raises(FileNotFoundError):
        load_worktree_plan_file(tmp_path / "missing.yaml")
    malformed = tmp_path / "broken.yaml"
    malformed.write_text("schema: [unclosed\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_worktree_plan_file(malformed)


# -- the registry ---------------------------------------------------------------


def test_registry_holds_the_house_law():
    registry = WorktreeRegistry()
    first = registry.register(_assignment())
    assert first.assignment_id == "worktree-1"
    second = registry.register(_assignment(
        member="scribe", office="scribe", slice_id="M-129",
        branch="crew/scribe/m-129", path="worktrees/scribe"))
    assert second.assignment_id == "worktree-2"
    assert registry.get("worktree-1") is first
    assert registry.by_member("scribe") is second
    assert registry.by_branch("crew/scribe/m-129") is second
    assert registry.by_path("worktrees/architect") is first
    assert [a.member for a in registry.list_assignments()] == \
        ["architect", "scribe"]
    assert [a.member for a in registry.list_assignments("scribe")] == \
        ["scribe"]
    with pytest.raises(KeyError):
        registry.get("worktree-99")
    with pytest.raises(KeyError):
        registry.by_member("skald")
    with pytest.raises(ValueError):
        registry.register(_assignment(
            slice_id="M-126", branch="crew/architect/m-126",
            path="worktrees/other"))
    with pytest.raises(ValueError):
        registry.register(_assignment(
            member="auditor", office="auditor", slice_id="M-126",
            branch="crew/scribe/m-129", path="worktrees/auditor"))
    with pytest.raises(ValueError):
        registry.register(_assignment(
            member="auditor", office="auditor", slice_id="M-126",
            branch="crew/auditor/m-126", path="worktrees/scribe"))
    with pytest.raises(ValueError):
        registry.register(_assignment(
            assignment_id="worktree-1", member="auditor",
            office="auditor", slice_id="M-126",
            branch="crew/auditor/m-126", path="worktrees/auditor"))


def test_registry_register_plan_and_supplied_id_skipping():
    registry = WorktreeRegistry()
    held = registry.register(_assignment(
        assignment_id="worktree-1", member="skald", office="skald",
        slice_id="M-130", branch="crew/skald/m-130",
        path="worktrees/skald"))
    assert held.assignment_id == "worktree-1"
    minted = registry.register(_assignment())
    assert minted.assignment_id == "worktree-2"
    plan_registry = WorktreeRegistry()
    registered = plan_registry.register_plan(load_worktree_plan())
    assert len(registered) == 8
    assert [a.assignment_id for a in registered] == \
        [f"worktree-{n}" for n in range(1, 9)]
    with pytest.raises(ValueError):
        plan_registry.register_plan(load_worktree_plan())
    with pytest.raises(ValueError):
        plan_registry.register_plan("not a plan")


# -- news, words, formatters, parser --------------------------------------------


def test_record_and_plain_words():
    record = worktree_record(_assignment())
    assert record["news"] is True
    assert record["type"] == "worktree_assignment"
    assert "architect" in record["headline"]
    assert "only writer in that tree" in record["headline"]
    words = plain_words(_assignment())
    assert "M-125" in words and "crew/architect/m-125" in words
    assert "worktrees/architect" in words


def test_formatters():
    assert format_assignments() == \
        "Worktree assignments: none. No crew member holds a tree."
    assert format_assignments([]) == format_assignments()
    plan = _plan()
    text = format_assignments(plan)
    assert text.startswith("Worktree assignments: 2 held.")
    assert "architect" in text and "forge_worker" in text
    assert format_assignment(_assignment()).startswith("  architect:")
    screen = format_worktrees_screen(plan)
    assert "Parallel worktrees (M-124)" in screen
    assert PLAIN_EXPLANATION in screen and USAGE in screen
    merges = format_merge_plan(plan)
    assert "coordinator (coordinator) only" in merges
    assert merges.index("M-125") < merges.index("M-128")
    with pytest.raises(ValueError):
        format_assignments("not assignments")
    with pytest.raises(ValueError):
        format_merge_plan("not a plan")


def test_parser():
    assert parse_worktrees_args("") == ("show", None)
    assert parse_worktrees_args(None) == ("show", None)
    assert parse_worktrees_args("show") == ("show", None)
    assert parse_worktrees_args("list") == ("show", None)
    assert parse_worktrees_args("show architect") == ("show", "architect")
    assert parse_worktrees_args("architect") == ("show", "architect")
    assert parse_worktrees_args("plan") == ("plan", None)
    assert parse_worktrees_args("merges") == ("merges", None)
    for bad in ("show", "plan now", "merges please", "show a b",
                "dance party", 4):
        if bad == "show":
            continue
        with pytest.raises(ValueError):
            parse_worktrees_args(bad)


def test_module_purity():
    source = (ROOT / "mythic_agent" / "core" / "worktrees.py").read_text(
        encoding="utf-8")
    for banned in ("agents.llm", "terminal", "command_handler",
                   "subprocess", "os.system"):
        assert banned not in source
    assert "from .crew_members import" in source
    assert "normalize_member_id" in source
    assert "normalize_office" in source
