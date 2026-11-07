"""M-114 Remote and SSH work - pure-layer tests.

TIER: integration

The pure layer is remote work as data: a target
on another machine (its address, user, port and
the workspace root the project lives under
there) with ONE connection description (SSH,
authenticating by agent, key file or password),
and a work plan of remote commands held as argv
word lists - never a shell string, the M-103
rule - plus file operations against the remote
root. A mechanical judge validates a plan
against its target: an unknown target, a step
outside the remote root, or a file operation
that would copy a file back to this machine all
refuse plainly, because files and commands stay
on that machine. Nothing here opens a
connection or runs a command.
"""

import pytest

from mythic_agent.core.remote_work import (
    AUTH_METHODS,
    AUTH_PHRASES,
    CONNECTION_KINDS,
    CONNECTION_PHRASES,
    DEFAULT_PORT,
    FILE_OP_KINDS,
    FILE_OP_PHRASES,
    PLAIN_EXPLANATION,
    REMOTE_WORK_SLICE,
    USAGE,
    Command,
    Connection,
    FileOp,
    Host,
    Plan,
    RemoteCommand,
    RemoteConnection,
    RemoteFileOp,
    RemoteHost,
    RemoteTarget,
    RemoteWorkPlan,
    RemoteWorkRegistry,
    Target,
    WorkPlan,
    build_command,
    build_connection,
    build_file_op,
    build_target,
    build_work_plan,
    format_plan,
    format_plans,
    format_record,
    format_remote_record,
    format_remote_screen,
    format_target,
    format_targets,
    format_work_plan,
    judge_work_plan,
    normalize_address,
    normalize_auth_method,
    normalize_connection_kind,
    normalize_file_op_kind,
    normalize_plan_id,
    normalize_port,
    normalize_target_id,
    normalize_user,
    normalize_workspace_root,
    parse_remote_args,
    plain_words,
    remote_work_record,
    validate_command,
    validate_connection,
    validate_file_op,
    validate_step,
    validate_target,
    validate_work_plan,
)


def _target(**overrides):
    base = {"target_id": "mimir", "address": "mimir.local",
            "user": "volmarr", "workspace_root": "/home/volmarr/proj"}
    base.update(overrides)
    return build_target(base)


def _steps():
    return [
        {"argv": ["git", "status", "--short"], "cwd": "src"},
        {"kind": "read", "path": "src/app.py"},
        {"kind": "list", "path": "/home/volmarr/proj"},
    ]


# -- constants and word readings ---------------------------------------


def test_constants_and_usage():
    assert REMOTE_WORK_SLICE == "M-114"
    assert CONNECTION_KINDS == ("ssh",)
    assert set(CONNECTION_PHRASES) == set(CONNECTION_KINDS)
    assert AUTH_METHODS == ("agent", "key", "password")
    assert set(AUTH_PHRASES) == set(AUTH_METHODS)
    assert FILE_OP_KINDS == ("read", "write", "edit", "list")
    assert set(FILE_OP_PHRASES) == set(FILE_OP_KINDS)
    assert DEFAULT_PORT == 22
    assert USAGE.startswith("Usage: /remote")
    assert "ONE connection" in PLAIN_EXPLANATION
    assert "stay on that machine" in PLAIN_EXPLANATION
    assert Connection is RemoteConnection
    assert Target is RemoteTarget
    assert RemoteHost is RemoteTarget
    assert Host is RemoteTarget
    assert Command is RemoteCommand
    assert FileOp is RemoteFileOp
    assert WorkPlan is RemoteWorkPlan
    assert Plan is RemoteWorkPlan
    assert format_plan is format_work_plan
    assert format_record is format_remote_record


def test_vocabulary_word_readings():
    assert normalize_connection_kind("SSH") == "ssh"
    assert normalize_connection_kind("openssh") == "ssh"
    assert normalize_auth_method("ssh-agent") == "agent"
    assert normalize_auth_method("key_file") == "key"
    assert normalize_auth_method("pass") == "password"
    assert normalize_file_op_kind("ls") == "list"
    assert normalize_file_op_kind("View") == "read"
    assert normalize_file_op_kind("modify") == "edit"
    for bad in ("telnet", "ftp"):
        with pytest.raises(ValueError):
            normalize_connection_kind(bad)
    with pytest.raises(ValueError):
        normalize_auth_method("fingerprint")
    with pytest.raises(ValueError):
        normalize_file_op_kind("download")
    with pytest.raises(ValueError):
        normalize_file_op_kind("copy")
    with pytest.raises(ValueError):
        normalize_file_op_kind(None)


def test_id_address_user_and_port_readings():
    assert normalize_target_id("My Mimir") == "my-mimir"
    assert normalize_target_id("purplelongship") == "purplelongship"
    assert normalize_plan_id("plan-1") == "plan-1"
    assert normalize_plan_id("Plan.2_x") == "Plan.2_x"
    assert normalize_address("mimir.local") == "mimir.local"
    assert normalize_address("192.168.1.20") == "192.168.1.20"
    assert normalize_user("volmarr") == "volmarr"
    assert normalize_port(22) == 22
    assert normalize_port("2222") == 2222
    with pytest.raises(ValueError):
        normalize_target_id("bad target!")
    with pytest.raises(ValueError):
        normalize_plan_id("two words")
    with pytest.raises(ValueError):
        normalize_address("bad host")
    with pytest.raises(ValueError):
        normalize_address("mimir.local:22")
    with pytest.raises(ValueError):
        normalize_address("-bad-")
    with pytest.raises(ValueError):
        normalize_user("1root")
    with pytest.raises(ValueError):
        normalize_user("bad user")
    with pytest.raises(ValueError):
        normalize_port(0)
    with pytest.raises(ValueError):
        normalize_port(65536)
    with pytest.raises(ValueError):
        normalize_port(True)
    with pytest.raises(ValueError):
        normalize_port("ssh")


def test_workspace_root_readings():
    assert normalize_workspace_root("/home/volmarr/proj") == \
        "/home/volmarr/proj"
    assert normalize_workspace_root("/") == "/"
    with pytest.raises(ValueError):
        normalize_workspace_root("home/volmarr/proj")
    with pytest.raises(ValueError):
        normalize_workspace_root("/home/../etc")
    with pytest.raises(ValueError):
        normalize_workspace_root("/home/proj/")
    with pytest.raises(ValueError):
        normalize_workspace_root("")


# -- the connection ------------------------------------------------------


def test_connection_defaults_and_key_rule():
    default = RemoteConnection()
    assert default.kind == "ssh"
    assert default.auth == "agent"
    assert default.identity_file is None
    keyed = build_connection(
        {"auth": "key", "identity_file": "~/.ssh/id_ed25519"})
    assert keyed.auth == "key"
    assert keyed.identity_file == "~/.ssh/id_ed25519"
    with pytest.raises(ValueError):
        RemoteConnection(auth="key")
    with pytest.raises(ValueError):
        RemoteConnection(auth="agent", identity_file="k")
    with pytest.raises(ValueError):
        validate_connection({"kind": "telnet"})
    with pytest.raises(ValueError):
        validate_connection({"auth": "agent", "bogus": 1})
    with pytest.raises(ValueError):
        validate_connection(
            {"auth": "agent", "auth_method": "key"})


# -- the target ------------------------------------------------------------


def test_target_defaults_and_record():
    target = _target()
    assert target.port == 22
    assert target.label == "mimir"
    assert target.connection_line == "volmarr@mimir.local:22"
    assert target.display_label == "mimir (mimir)"
    record = target.to_record()
    assert record["type"] == "remote_target"
    assert record["slice"] == "M-114"
    assert record["workspace_root"] == "/home/volmarr/proj"
    assert record["connection"] == {
        "kind": "ssh", "auth": "agent", "identity_file": None}


def test_target_validate_and_build_aliases():
    target = validate_target({
        "id": "PurpleLongship", "host": "ship.local",
        "username": "volmarr", "root": "/srv/code",
        "port": "2200", "title": "the laptop",
        "connection": {"type": "openssh", "method": "password"}})
    assert target.target_id == "purplelongship"
    assert target.address == "ship.local"
    assert target.port == 2200
    assert target.label == "the laptop"
    assert target.connection.auth == "password"
    assert build_target(target) is target
    with pytest.raises(ValueError):
        validate_target({"target_id": "x", "address": "a.local"})
    with pytest.raises(ValueError):
        validate_target({
            "target_id": "x", "id": "y", "address": "a.local",
            "user": "u", "root": "/r"})
    with pytest.raises(ValueError):
        validate_target({
            "target_id": "x", "address": "a.local", "user": "u",
            "root": "/r", "bogus": 1})
    with pytest.raises(ValueError):
        _target(workspace_root="relative/root")


# -- the steps -------------------------------------------------------------


def test_command_step_is_argv_data_never_a_shell_string():
    command = build_command(["pytest", "-q"], cwd="tests")
    assert command.argv == ("pytest", "-q")
    assert command.command_text == "pytest -q"
    assert command.display_label == "pytest -q"
    assert validate_command({"command": ["ls"], "name": "list"}).label == "list"
    with pytest.raises(ValueError):
        build_command("pytest -q")
    with pytest.raises(ValueError):
        validate_command({"argv": "rm -rf /"})
    with pytest.raises(ValueError):
        build_command([])
    with pytest.raises(ValueError):
        build_command(["ls", " "])
    with pytest.raises(ValueError):
        build_command(["ls", 7])
    with pytest.raises(ValueError):
        validate_command({"cwd": "src"})
    with pytest.raises(ValueError):
        validate_command({"argv": ["ls"], "bogus": 1})


def test_file_op_step_validation():
    op = build_file_op("read", "src/app.py")
    assert op.kind == "read"
    assert op.local_copy is False
    assert op.display_label == "read src/app.py"
    assert validate_file_op(
        {"op": "ls", "file": "src"}).kind == "list"
    with pytest.raises(ValueError):
        build_file_op("download", "src/app.py")
    with pytest.raises(ValueError):
        build_file_op("read", "../secret")
    with pytest.raises(ValueError):
        build_file_op("read", "")
    with pytest.raises(ValueError):
        build_file_op("read", "src/app.py", local_copy="yes")
    with pytest.raises(ValueError):
        validate_file_op({"kind": "read"})
    with pytest.raises(ValueError):
        validate_file_op({"kind": "read", "path": "a", "bogus": 1})


def test_validate_step_dispatch_and_ambiguity():
    assert isinstance(validate_step({"argv": ["ls"]}), RemoteCommand)
    assert isinstance(
        validate_step({"kind": "edit", "path": "a.py"}), RemoteFileOp)
    step = build_command(["ls"])
    assert validate_step(step) is step
    with pytest.raises(ValueError):
        validate_step({"argv": ["ls"], "kind": "read", "path": "a"})
    with pytest.raises(ValueError):
        validate_step({"nothing": True})
    with pytest.raises(ValueError):
        validate_step(42)


# -- the work plan ----------------------------------------------------------


def test_work_plan_shape_and_counts():
    plan = build_work_plan(name="fix", target_id="Mimir", steps=_steps())
    assert plan.target_id == "mimir"
    assert len(plan.steps) == 3
    assert len(plan.command_steps) == 1
    assert len(plan.file_steps) == 2
    assert plan.stays_on_remote is True
    record = plan.to_record()
    assert record["command_count"] == 1
    assert record["file_op_count"] == 2
    assert record["steps"][0]["argv"] == ["git", "status", "--short"]
    assert validate_work_plan(plan) is plan
    assert validate_work_plan({
        "plan": "fix", "target": "mimir", "work": _steps()}).name == "fix"
    with pytest.raises(ValueError):
        build_work_plan(name="fix", target_id="mimir", steps=[])
    with pytest.raises(ValueError):
        build_work_plan(name="fix", target_id="mimir", steps="run ls")
    with pytest.raises(ValueError):
        validate_work_plan({"name": "x", "target_id": "mimir"})
    with pytest.raises(ValueError):
        validate_work_plan({
            "name": "x", "target_id": "mimir", "steps": _steps(),
            "bogus": 1})


# -- the judge ----------------------------------------------------------------


def test_judge_accepts_a_plan_that_stays_inside_the_root():
    target = _target()
    plan = build_work_plan(name="fix", target_id="mimir", steps=_steps())
    assert judge_work_plan(plan, target) is plan
    absolute = build_work_plan(name="fix", target_id="mimir", steps=[
        {"argv": ["ls"], "cwd": "/home/volmarr/proj/src"},
        {"kind": "write", "path": "/home/volmarr/proj/new.py"}])
    assert judge_work_plan(absolute, target) is absolute


def test_judge_refuses_unknown_and_mismatched_targets():
    plan = build_work_plan(name="fix", target_id="mimir", steps=_steps())
    other = _target(target_id="ship", address="ship.local")
    with pytest.raises(ValueError, match="one target"):
        judge_work_plan(plan, other)
    registry = RemoteWorkRegistry()
    registry.register_target(_target(
        target_id="ship", address="ship.local"))
    with pytest.raises(ValueError, match="unknown target"):
        judge_work_plan(plan, registry)
    empty = RemoteWorkRegistry()
    with pytest.raises(ValueError, match="holds no targets"):
        judge_work_plan(plan, empty)


def test_judge_refuses_a_local_copy_plainly():
    plan = build_work_plan(name="fetch", target_id="mimir", steps=[
        {"kind": "read", "path": "src/app.py", "local_copy": True}])
    assert plan.stays_on_remote is False
    with pytest.raises(ValueError, match="files stay on"):
        judge_work_plan(plan, _target())


def test_judge_refuses_steps_outside_the_remote_root():
    target = _target()
    outside_file = build_work_plan(name="peek", target_id="mimir", steps=[
        {"kind": "read", "path": "/etc/passwd"}])
    with pytest.raises(ValueError, match="outside the remote workspace root"):
        judge_work_plan(outside_file, target)
    outside_cwd = build_work_plan(name="peek", target_id="mimir", steps=[
        {"argv": ["ls"], "cwd": "/etc"}])
    with pytest.raises(ValueError, match="outside the remote workspace root"):
        judge_work_plan(outside_cwd, target)
    sibling = build_work_plan(name="peek", target_id="mimir", steps=[
        {"kind": "read", "path": "/home/volmarr/project/app.py"}])
    with pytest.raises(ValueError, match="outside the remote workspace root"):
        judge_work_plan(sibling, target)


def test_judge_never_sees_a_shell_string():
    with pytest.raises(ValueError, match="not a shell string"):
        build_work_plan(name="x", target_id="mimir", steps=[
            {"argv": "ls -la"}])


# -- plain words and the news record ------------------------------------------


def test_plain_words_and_record_state_stays_on_remote_honestly():
    plan = build_work_plan(name="fix", target_id="mimir", steps=_steps())
    words = plain_words(plan)
    assert "mimir" in words
    assert "1 commands and 2 file operations" in words
    assert "stays on that machine" in words
    record = remote_work_record(plan)
    assert record["type"] == "remote_work_plan"
    assert record["news"] is True
    assert record["slice"] == "M-114"
    assert record["plan_id"] is None
    assert record["stays_on_remote"] is True
    assert record["headline"] == words
    copying = build_work_plan(name="fetch", target_id="mimir", steps=[
        {"kind": "read", "path": "a.py", "local_copy": True}])
    bad_words = plain_words(copying)
    assert "would copy a file back" in bad_words
    assert "refuses as named" in bad_words
    with pytest.raises(ValueError):
        plain_words("not a plan")
    with pytest.raises(ValueError):
        remote_work_record(None)


# -- the registry ---------------------------------------------------------------


def test_registry_targets_in_order_and_unknown_refusals():
    registry = RemoteWorkRegistry()
    mimir = registry.register_target(_target())
    ship = registry.register_target(_target(
        target_id="ship", address="ship.local", label="the laptop"))
    assert registry.list_targets() == (mimir, ship)
    assert registry.get_target("MIMIR") is mimir
    with pytest.raises(ValueError, match="already held"):
        registry.register_target(_target())
    with pytest.raises(ValueError, match="unknown target"):
        registry.get_target("nope")
    with pytest.raises(ValueError, match="holds no targets"):
        RemoteWorkRegistry().get_target("mimir")


def test_registry_plan_ids_are_deterministic():
    registry = RemoteWorkRegistry()
    registry.register_target(_target())
    first = registry.build_and_register("mimir", "one", _steps())
    second = registry.build_and_register("mimir", "two", _steps())
    assert first.plan_id == "plan-1"
    assert second.plan_id == "plan-2"
    named = registry.register(build_work_plan(
        name="three", target_id="mimir", steps=_steps(),
        plan_id="plan-4"))
    third = registry.build_and_register("mimir", "four", _steps())
    assert named.plan_id == "plan-4"
    assert third.plan_id == "plan-3"
    fourth = registry.build_and_register("mimir", "five", _steps())
    assert fourth.plan_id == "plan-5"
    assert len(registry) == 5
    assert registry.list_plans()[0] is first
    assert registry.record("plan-1")["plan_id"] == "plan-1"
    with pytest.raises(ValueError, match="already exists"):
        registry.register(build_work_plan(
            name="dup", target_id="mimir", steps=_steps(),
            plan_id="plan-1"))
    with pytest.raises(KeyError):
        registry.get("plan-99")
    with pytest.raises(ValueError):
        registry.register("not a plan")


def test_registry_build_and_register_judges_and_holds_nothing_on_refusal():
    registry = RemoteWorkRegistry()
    registry.register_target(_target())
    with pytest.raises(ValueError, match="files stay on"):
        registry.build_and_register("mimir", "fetch", [
            {"kind": "read", "path": "a.py", "local_copy": True}])
    assert len(registry) == 0
    with pytest.raises(ValueError, match="unknown target"):
        registry.build_and_register("nope", "x", _steps())
    assert len(registry) == 0
    held = registry.build_and_register(_target(), "by object", _steps())
    assert held.target_id == "mimir"
    assert len(registry) == 1


# -- formatters and the shared parser --------------------------------------------


def test_formatters_state_connections_and_counts_in_words():
    registry = RemoteWorkRegistry()
    registry.register_target(_target())
    registry.register_target(_target(
        target_id="ship", address="ship.local", label="the laptop",
        connection={"auth": "key", "identity_file": "~/.ssh/ship"}))
    plan = registry.build_and_register("mimir", "fix", _steps())
    target_text = format_target(registry.get_target("ship"))
    assert "the laptop" in target_text
    assert "SSH (one secure shell connection)" in target_text
    assert "a key file" in target_text
    assert "~/.ssh/ship" in target_text
    assert "/home/volmarr/proj" in target_text
    targets_text = format_targets(registry)
    assert targets_text.startswith("Remote work: 2 targets held.")
    assert format_targets().startswith(
        "Remote work: no targets held.")
    plan_text = format_work_plan(plan)
    assert "1 commands, 2 file operations" in plan_text
    assert "files and commands stay on that machine" in plan_text
    assert "git status --short" in plan_text
    assert "read a file on the remote machine" in plan_text
    plans_text = format_plans(registry)
    assert plans_text.startswith("Remote work plans: 1 held.")
    assert format_plans().startswith("Remote work plans: no plans held.")
    record = registry.record("plan-1")
    assert format_remote_record(record) == record["headline"]
    with pytest.raises(ValueError):
        format_remote_record({"type": "other"})
    with pytest.raises(ValueError):
        format_work_plan("not a plan")
    screen = format_remote_screen(registry)
    assert screen.startswith("Remote and SSH work (M-114)")
    assert USAGE in screen
    assert "2 targets held" in screen


def test_parser_grammar():
    assert parse_remote_args("") == ("show", None)
    assert parse_remote_args(None) == ("show", None)
    assert parse_remote_args("show") == ("show", None)
    assert parse_remote_args("targets") == ("targets", None)
    assert parse_remote_args("Targets") == ("targets", None)
    assert parse_remote_args("show plan-1") == ("show", "plan-1")
    assert parse_remote_args("plan-1") == ("show", "plan-1")
    assert parse_remote_args("Show Plan-3") == ("show", "Plan-3")
    for bad in ("show targets", "targets plan-1", "show plan-1 extra",
                "drop plan-1", "show \"x\""):
        with pytest.raises(ValueError):
            parse_remote_args(bad)
    with pytest.raises(ValueError):
        parse_remote_args(42)


def test_module_is_pure_data_only():
    import pathlib
    source = pathlib.Path(
        "mythic_agent/core/remote_work.py").read_text()
    # Run from the repo root like the suite does; fall back to the
    # module file location when invoked from elsewhere.
    if "Remote and SSH work" not in source:
        import mythic_agent.core.remote_work as module
        source = pathlib.Path(module.__file__).read_text()
    assert "import subprocess" not in source
    assert "import os" not in source
    assert "import sys" not in source
    assert "open(" not in source


def test_target_and_connection_are_frozen_data():
    import dataclasses
    target = _target()
    with pytest.raises(dataclasses.FrozenInstanceError):
        target.port = 2200
    with pytest.raises(dataclasses.FrozenInstanceError):
        target.connection.auth = "key"
    plan = build_work_plan(name="fix", target_id="mimir", steps=_steps())
    with pytest.raises(dataclasses.FrozenInstanceError):
        plan.name = "other"


def test_judge_allows_the_root_itself_and_relative_work():
    target = _target()
    plan = build_work_plan(name="fix", target_id="mimir", steps=[
        {"argv": ["ls"], "cwd": "/home/volmarr/proj"},
        {"argv": ["ls"], "cwd": "deep/nested/dir"},
        {"kind": "edit", "path": "a/b/c.py"}])
    assert judge_work_plan(plan, target) is plan
    root_target = _target(workspace_root="/")
    anywhere = build_work_plan(name="fix", target_id="mimir", steps=[
        {"kind": "read", "path": "/anywhere/at/all.txt"}])
    assert judge_work_plan(anywhere, root_target) is anywhere


def test_format_targets_accepts_lists_and_single_targets():
    text = format_targets([_target()])
    assert text.startswith("Remote work: 1 targets held.")
    single = format_targets(_target())
    assert "mimir" in single
    with pytest.raises(ValueError):
        format_targets(42)


def test_record_carries_every_step_as_data():
    plan = build_work_plan(name="fix", target_id="mimir", steps=_steps())
    record = remote_work_record(plan)
    assert record["steps"][0] == {
        "step": "command", "argv": ["git", "status", "--short"],
        "cwd": "src", "label": ""}
    assert record["steps"][1] == {
        "step": "file_op", "kind": "read", "path": "src/app.py",
        "local_copy": False, "label": ""}
    assert record["steps"][2]["kind"] == "list"
