"""M-125 Task dealing - pure-layer tests.

TIER: integration

The pure layer is the dealing as data: a plan of
tasks (slice, title, the office its work fits)
validated as data, the dealing derived mechanically
from the plan, the shipped M-121 casting and the
crew's current load - office fit first, then least
load, casting order breaking ties - the shipped
example plan (the next ten roadmap slices) held in
a data file, a loader that reads a plan from any
file, the human's re-deal as data, a dealing record
shaped as session news, and a registry. Nothing
here starts a crew, spawns an agent, runs a model
or runs git, and no Part VIII board is claimed:
the dealing is visible on this slice's own screen.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.crew_members import load_casting, member_offices
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.task_dealing import (
    DEALING_RESOURCE,
    DEALING_SCHEMA,
    DEALING_SLICE,
    PLAIN_EXPLANATION,
    USAGE,
    Dealing,
    DealingPlan,
    DealingTask,
    DealtAssignment,
    TaskDealingRegistry,
    build_assignment,
    build_task,
    deal_tasks,
    dealing_record,
    format_assignment,
    format_assignments,
    format_dealing_screen,
    format_loads,
    format_tasks,
    load_dealing_plan,
    load_dealing_plan_file,
    member_loads,
    normalize_slice_id,
    parse_dealing_args,
    plain_words,
    redeal_dealing,
    validate_assignment,
    validate_dealing,
    validate_plan,
    validate_task,
)

ROOT = Path(__file__).resolve().parents[1]


def _casting():
    return load_casting().members


def _task(**kwargs):
    kwargs.setdefault("slice_id", "M-125")
    kwargs.setdefault("title", "Task dealing")
    kwargs.setdefault("office", "forge_worker")
    return DealingTask(**kwargs)


def _assignment(**kwargs):
    kwargs.setdefault("member", "forge_worker")
    kwargs.setdefault("office", "forge_worker")
    kwargs.setdefault("slice_id", "M-125")
    kwargs.setdefault("title", "Task dealing")
    kwargs.setdefault("required_office", "forge_worker")
    kwargs.setdefault("load_after", 1)
    return DealtAssignment(**kwargs)


def _plan_data():
    return {
        "schema": DEALING_SCHEMA, "slice": DEALING_SLICE,
        "dealer": "coordinator",
        "tasks": [
            {"slice_id": "M-128", "title": "Merge discipline",
             "office": "forge_worker"},
            {"slice_id": "M-125", "title": "Task dealing",
             "office": "forge_worker"},
        ]}


def _write_plan(tmp_path, data):
    path = tmp_path / "plan.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


# -- constants and word readings --------------------------------------------


def test_constants_and_usage():
    assert DEALING_SLICE == "M-125"
    assert DEALING_SCHEMA == "mythic.task_dealing/1"
    assert DEALING_RESOURCE == "task_dealing.yaml"
    assert USAGE.startswith("Usage: /dealing")
    assert "plan" in USAGE and "loads" in USAGE
    assert "office fit and current load" in PLAIN_EXPLANATION
    assert "no Part VIII board" in PLAIN_EXPLANATION


def test_slice_readings_come_from_the_worktrees_layer():
    assert normalize_slice_id("m-7") == "M-007"
    assert normalize_slice_id(" M-272 ") == "M-272"
    for bad in ("M-000", "M-273", "125", "", None, 125):
        with pytest.raises(ValueError):
            normalize_slice_id(bad)


def test_task_construction_and_record():
    task = _task()
    assert task.slice_id == "M-125"
    record = task.to_record()
    assert record["type"] == "dealing_task"
    assert record["slice"] == "M-125"
    assert record["office"] == "forge_worker"
    # Offices read as the M-121 layer reads them.
    assert _task(office="Forge-Worker").office == "forge_worker"
    with pytest.raises(ValueError):
        _task(office="primary")
    with pytest.raises(ValueError):
        _task(office="wizard")
    with pytest.raises(ValueError):
        _task(title="  ")
    with pytest.raises(ValueError):
        _task(title="Bad\ttitle")


def test_task_validator_aliases_and_refusals():
    task = validate_task(
        {"slice": "m-126", "title": "Crew comms",
         "required_office": "scribe"})
    assert task.slice_id == "M-126" and task.office == "scribe"
    assert build_task(task) is task
    assert build_task(slice_id="M-126", title="Crew comms",
                      office="scribe") == task
    with pytest.raises(ValueError):
        validate_task({"slice_id": "M-126", "slice": "M-127",
                       "title": "Crew comms", "office": "scribe"})
    with pytest.raises(ValueError):
        validate_task({"slice_id": "M-126", "title": "Crew comms"})
    with pytest.raises(ValueError):
        validate_task({"slice_id": "M-126", "title": "Crew comms",
                       "office": "scribe", "surprise": 1})
    with pytest.raises(ValueError):
        validate_task("not a task")


def test_assignment_construction_fit_and_record():
    assignment = _assignment()
    assert assignment.fit is True
    record = assignment.to_record()
    assert record["type"] == "task_dealing"
    assert record["fit"] is True and record["load_after"] == 1
    off = _assignment(member="scribe", office="scribe")
    assert off.fit is False
    with pytest.raises(ValueError):
        _assignment(load_after=-1)
    with pytest.raises(ValueError):
        _assignment(load_after=True)
    with pytest.raises(ValueError):
        _assignment(member="bad member")


def test_assignment_validator_aliases_and_refusals():
    assignment = validate_assignment(
        {"member_id": "scribe", "office": "scribe",
         "slice": "M-126", "title": "Crew comms",
         "required_office": "forge_worker", "load": 2,
         "id": "dealing-9"})
    assert assignment.member == "scribe"
    assert assignment.assignment_id == "dealing-9"
    assert assignment.load_after == 2
    assert build_assignment(assignment) is assignment
    with pytest.raises(ValueError):
        validate_assignment(
            {"member": "scribe", "member_id": "auditor",
             "office": "scribe", "slice_id": "M-126",
             "title": "Crew comms",
             "required_office": "forge_worker", "load_after": 1})
    with pytest.raises(ValueError):
        validate_assignment(
            {"member": "scribe", "office": "scribe",
             "slice_id": "M-126", "title": "Crew comms",
             "required_office": "forge_worker",
             "load_after": 1, "surprise": 1})
    with pytest.raises(ValueError):
        validate_assignment({"member": "scribe"})


# -- the shipped example plan -----------------------------------------------


def test_shipped_plan_loads_as_the_example():
    plan = load_dealing_plan()
    assert plan.dealer == "coordinator"
    assert [t.slice_id for t in plan.tasks] == \
        [f"M-{n:03d}" for n in range(125, 135)]
    assert plan.get("M-130").title == "The Auditor's veto"
    assert plan.get("m-127").office == "guardian"
    with pytest.raises(KeyError):
        plan.get("M-140")
    assert validate_plan(
        yaml.safe_load(
            (ROOT / "mythic_agent" / "data" / DEALING_RESOURCE)
            .read_text(encoding="utf-8")),
        require_example=True) == []


def test_shipped_example_check_refuses_drift():
    data = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / DEALING_RESOURCE)
        .read_text(encoding="utf-8"))
    data["tasks"][0]["office"] = "scribe"
    problems = validate_plan(data, require_example=True)
    assert any("exactly the ten tasks" in p for p in problems)
    # The same file is a well-formed plan without the check.
    assert validate_plan(data) == []


def test_shipped_dealing_deals_every_task_on_fit():
    plan = load_dealing_plan()
    dealing = deal_tasks(plan, _casting())
    assert dealing.undealt == ()
    assert [a.slice_id for a in dealing.assignments] == \
        [t.slice_id for t in plan.tasks]
    assert all(a.fit for a in dealing.assignments)
    by_member = {}
    for assignment in dealing.assignments:
        member = next(
            m for m in _casting()
            if m.member_id == assignment.member)
        assert assignment.office == member.office
        by_member.setdefault(assignment.member, []).append(
            assignment.slice_id)
    assert by_member["forge_worker"] == ["M-125", "M-128"]
    assert by_member["auditor"] == ["M-130", "M-132"]
    assert by_member["scribe"] == ["M-126", "M-133"]
    assert dealing.loads() == {
        "forge_worker": 2, "scribe": 2, "guardian": 1,
        "polymath": 1, "auditor": 2, "cartographer": 1,
        "skald": 1}
    assert validate_dealing(plan, dealing, _casting()) == []


# -- the mechanical dealing ---------------------------------------------------


def test_dealing_prefers_fit_then_least_load_then_crew_order():
    members = [
        {"member": "first", "office": "forge_worker"},
        {"member": "second", "office": "forge_worker"},
        {"member": "third", "office": "scribe"},
    ]
    tasks = [_task(), _task(slice_id="M-128",
                            title="Merge discipline")]
    # Equal fit, equal load: crew order deals both in turn
    # as the first member's load grows.
    dealing = deal_tasks(tasks, members)
    assert [a.member for a in dealing.assignments] == \
        ["first", "second"]
    assert [a.load_after for a in dealing.assignments] == [1, 1]
    # A starting load moves the deal to the less loaded fit.
    dealing = deal_tasks(tasks[:1], members, loads={"first": 3})
    assert dealing.assignments[0].member == "second"
    assert dealing.assignments[0].load_after == 1
    assert dealing.base_loads == (("first", 3),)
    # Fit beats load: an unfitted member never wins while a
    # fitted one can take the slice, however loaded.
    dealing = deal_tasks(tasks[:1], members, loads={"first": 9,
                                                    "second": 9})
    assert dealing.assignments[0].member == "first"
    assert dealing.assignments[0].fit is True


def test_dealing_without_a_fitted_member_deals_off_fit_by_load():
    members = [
        {"member": "busy", "office": "scribe"},
        {"member": "idle", "office": "auditor"},
    ]
    dealing = deal_tasks([_task()], members, loads={"busy": 2})
    assignment = dealing.assignments[0]
    assert assignment.member == "idle"
    assert assignment.fit is False
    assert assignment.required_office == "forge_worker"


def test_dealing_with_an_empty_crew_leaves_tasks_undealt():
    dealing = deal_tasks([_task()], [])
    assert dealing.assignments == ()
    assert [t.slice_id for t in dealing.undealt] == ["M-125"]


def test_dealing_refusals():
    with pytest.raises(ValueError):
        deal_tasks([_task(), _task()], _casting())
    with pytest.raises(ValueError):
        deal_tasks([_task()], [{"member": "x", "office": "scribe"},
                               {"member": "x", "office": "auditor"}])
    with pytest.raises(ValueError):
        deal_tasks([_task()], _casting(), loads={"nobody": 1})
    with pytest.raises(ValueError):
        deal_tasks([_task()], _casting(), loads={"scribe": -1})
    with pytest.raises(ValueError):
        deal_tasks("not tasks", _casting())


def test_member_loads_counts_the_whole_crew():
    dealing = deal_tasks(load_dealing_plan(), _casting())
    loads = member_loads(_casting(), dealing)
    assert loads["forge_worker"] == 2
    assert loads["architect"] == 0
    assert set(loads) == {m.member_id for m in _casting()}
    # Held worktree assignments are a starting load: one
    # per member, passed in as counts.
    loads = member_loads(
        _casting(), dealing,
        loads={m.member_id: 1 for m in _casting()})
    assert loads["forge_worker"] == 3
    assert loads["architect"] == 1
    assert {m.office for m in _casting()} == set(member_offices())


def test_validate_dealing_names_problems():
    plan = load_dealing_plan()
    dealing = deal_tasks(plan, _casting())
    moved = redeal_dealing(dealing, "M-125", "scribe", _casting())
    assert validate_dealing(plan, moved, _casting()) == []
    broken = Dealing(assignments=dealing.assignments[1:],
                     undealt=())
    problems = validate_dealing(plan, broken, _casting())
    assert any("M-125" in p for p in problems)
    wrong_office = Dealing(assignments=(
        DealtAssignment(
            member="scribe", office="auditor", slice_id="M-126",
            title="Crew comms", required_office="scribe",
            load_after=1),), undealt=())
    problems = validate_dealing(plan, wrong_office, _casting())
    assert any("cast office" in p for p in problems)


def test_redeal_moves_one_slice_and_recomputes_loads():
    plan = load_dealing_plan()
    dealing = deal_tasks(plan, _casting())
    moved = redeal_dealing(dealing, "M-125", "scribe", _casting())
    assignment = moved.get("M-125")
    assert assignment.member == "scribe"
    assert assignment.office == "scribe"
    assert assignment.fit is False
    # Loads recomputed in assignment order from no base.
    assert moved.get("M-126").load_after == 2
    assert moved.get("M-128").load_after == 1
    # The original dealing is untouched (frozen, derived).
    assert dealing.get("M-125").member == "forge_worker"
    with pytest.raises(ValueError):
        redeal_dealing(dealing, "M-125", "nobody", _casting())
    with pytest.raises(KeyError):
        redeal_dealing(dealing, "M-140", "scribe", _casting())


# -- plans on disk ------------------------------------------------------------


def test_plan_construction_and_refusals():
    plan = DealingPlan(tasks=[_task()], dealer="coordinator")
    assert plan.tasks[0].slice_id == "M-125"
    with pytest.raises(ValueError):
        DealingPlan(tasks=[], dealer="coordinator")
    with pytest.raises(ValueError):
        DealingPlan(tasks=[_task(), _task()], dealer="coordinator")
    with pytest.raises(ValueError):
        DealingPlan(tasks=[_task()], dealer="bad dealer")


def test_plan_file_roundtrip(tmp_path):
    path = _write_plan(tmp_path, _plan_data())
    plan = load_dealing_plan_file(path)
    assert [t.slice_id for t in plan.tasks] == ["M-128", "M-125"]
    dealing = deal_tasks(plan, _casting())
    assert [a.member for a in dealing.assignments] == \
        ["forge_worker", "forge_worker"]
    assert dealing.assignments[1].load_after == 2


def test_plan_file_refusals(tmp_path):
    data = _plan_data()
    data["schema"] = "mythic.other/9"
    assert validate_plan(data) != []
    with pytest.raises(ValidationError):
        load_dealing_plan_file(_write_plan(tmp_path, data))
    data = _plan_data()
    data["tasks"].append(dict(data["tasks"][0]))
    with pytest.raises(ValidationError):
        load_dealing_plan_file(_write_plan(tmp_path, data))
    with pytest.raises(FileNotFoundError):
        load_dealing_plan_file(tmp_path / "missing.yaml")
    assert validate_plan("not a plan") != []
    assert validate_plan({}) != []


# -- the registry -------------------------------------------------------------


def test_registry_holds_and_counts():
    registry = TaskDealingRegistry()
    dealing = deal_tasks(load_dealing_plan(), _casting())
    held = registry.register_dealing(dealing)
    assert [a.assignment_id for a in held] == \
        [f"dealing-{n}" for n in range(1, 11)]
    assert registry.by_slice("M-130").member == "auditor"
    assert [a.slice_id for a in registry.by_member("scribe")] == \
        ["M-126", "M-133"]
    assert registry.loads() == {
        "forge_worker": 2, "scribe": 2, "guardian": 1,
        "polymath": 1, "auditor": 2, "cartographer": 1,
        "skald": 1}
    assert registry.get("dealing-3").slice_id == "M-127"
    with pytest.raises(KeyError):
        registry.by_slice("M-140")
    with pytest.raises(KeyError):
        registry.get("dealing-99")


def test_registry_refuses_a_slice_dealt_twice():
    registry = TaskDealingRegistry()
    registry.register(_assignment())
    with pytest.raises(ValueError):
        registry.register(_assignment(member="scribe",
                                      office="scribe"))
    supplied = registry.register(_assignment(
        assignment_id="dealing-9", slice_id="M-126",
        title="Crew comms", required_office="scribe",
        member="scribe", office="scribe"))
    assert supplied.assignment_id == "dealing-9"
    with pytest.raises(ValueError):
        registry.register(_assignment(
            assignment_id="dealing-9", slice_id="M-127",
            title="Cycle and deadlock detection grown",
            required_office="guardian", member="guardian",
            office="guardian"))
    fresh = registry.register(_assignment(
        slice_id="M-127", title="Cycle and deadlock detection grown",
        required_office="guardian", member="guardian",
        office="guardian"))
    # dealing-1 was auto-issued first, so the fresh id is next.
    assert fresh.assignment_id == "dealing-2"


def test_registry_redeal_moves_in_place():
    registry = TaskDealingRegistry()
    registry.register_dealing(
        deal_tasks(load_dealing_plan(), _casting()))
    moved = registry.redeal("M-125", "scribe", "scribe")
    assert moved.member == "scribe" and moved.office == "scribe"
    assert moved.assignment_id == "dealing-1"
    assert registry.by_slice("M-126").load_after == 2
    assert registry.loads()["forge_worker"] == 1
    assert registry.loads()["scribe"] == 3
    with pytest.raises(KeyError):
        registry.redeal("M-140", "scribe", "scribe")


# -- news, words and surfaces ---------------------------------------------------


def test_record_and_plain_words():
    record = dealing_record(_assignment())
    assert record["type"] == "task_dealing"
    assert record["news"] is True
    assert "M-125" in record["headline"]
    words = plain_words(_assignment())
    assert "forge worker" in words and "office fit" in words
    off = plain_words(_assignment(member="scribe", office="scribe"))
    assert "off the fitted office" in off


def test_formatters():
    dealing = deal_tasks(load_dealing_plan(), _casting())
    text = format_assignments(dealing)
    assert text.startswith("Dealt assignments: 10 dealt.")
    assert "M-125" in format_assignment(dealing.assignments[0])
    assert format_assignments() == \
        "Dealt assignments: none. No slice is dealt."
    loads = format_loads(dealing)
    assert loads.startswith("Crew load:")
    assert "forge_worker 2" in loads
    assert format_loads() == \
        "Crew load: none. No member holds a dealt slice."
    screen = format_dealing_screen()
    assert "Task dealing (M-125)" in screen
    assert "Dealt assignments: 10 dealt." in screen
    assert "no Part VIII board" in screen
    assert USAGE in screen
    held_screen = format_dealing_screen(dealing)
    assert "M-134" in held_screen
    tasks_text = format_tasks(load_dealing_plan())
    assert tasks_text.startswith("Dealing plan: 10 tasks.")
    assert "M-130: The Auditor's veto - fits auditor." in tasks_text
    assert format_tasks([]) == "Dealing plan: no tasks."


def test_parser():
    assert parse_dealing_args("") == ("show", None)
    assert parse_dealing_args(None) == ("show", None)
    assert parse_dealing_args("show") == ("show", None)
    assert parse_dealing_args("list") == ("show", None)
    assert parse_dealing_args("show scribe") == ("show", "scribe")
    assert parse_dealing_args("scribe") == ("show", "scribe")
    assert parse_dealing_args("plan") == ("plan", None)
    assert parse_dealing_args("loads") == ("loads", None)
    for bad in ("show a b", "plan now", "loads please", "a b", 42):
        with pytest.raises(ValueError):
            parse_dealing_args(bad)


def test_module_purity():
    source = (ROOT / "mythic_agent" / "core" / "task_dealing.py") \
        .read_text(encoding="utf-8")
    for banned in ("agents.llm", "terminal", "command_handler",
                   "subprocess", "os.system"):
        assert banned not in source
    assert "from .crew_members import" in source
    assert "normalize_member_id" in source
    assert "normalize_office" in source
    assert "from .worktrees import" in source
    assert "normalize_slice_id" in source
