"""M-113 Multi-repo workspaces - pure-layer tests.

TIER: integration

The pure layer is the workspace as data: several
repos held under one session, each a frozen
validated entry carrying its per-repo policy (the
elder policy road's three modes, its target
branch, and whether its changes require review),
and a cross-repo change set built ON the M-084
machinery - one ChangeSet under one name, every
member edit prefixed by its repo, decided file by
file and planned whole, all-or-nothing, so no
repo's part ever applies alone. A repo the
workspace does not hold refuses plainly, and a
read-only repo refuses a change-set member at
build time. Nothing here opens a repo or writes
a file.
"""

import pytest

from mythic_agent.core.multi_repo import (
    MODE_PHRASES,
    MULTI_REPO_SLICE,
    PLAIN_EXPLANATION,
    POLICY_MODES,
    USAGE,
    CrossRepoChangeSet,
    CrossSet,
    MultiRepoRegistry,
    MultiRepoWorkspace,
    Policy,
    Repo,
    RepoEntry,
    RepoPolicy,
    Workspace,
    build_cross_repo_change_set,
    build_policy,
    build_repo,
    build_workspace,
    format_cross_set,
    format_multi_repo_record,
    format_multi_repo_screen,
    format_record,
    format_repo,
    format_repos,
    format_set,
    format_sets,
    multi_repo_record,
    normalize_branch,
    normalize_policy_mode,
    normalize_repo_id,
    normalize_set_id,
    parse_multirepo_args,
    plain_words,
    plan_cross_repo_change_set,
    validate_policy,
    validate_repo,
    validate_workspace,
)


def _workspace():
    return build_workspace(name="session", repos=[
        {"repo_id": "api", "root": "/srv/api", "label": "API repo",
         "policy": {"mode": "trusted", "branch": "main"}},
        {"repo_id": "docs", "root": "/srv/docs", "label": "Docs repo",
         "policy": {"mode": "ask", "branch": "docs-main"}},
        {"repo_id": "frozen", "root": "/srv/frozen",
         "policy": {"mode": "read_only"}},
    ])


def _member(repo_id, path, payload, format_id="whole-file"):
    return {"repo_id": repo_id, "path": path,
            "format_id": format_id, "payload": payload}


_SEARCH = "<<<<<<< SEARCH\nx = 1\n=======\nx = 2\n>>>>>>> REPLACE"


# -- constants and word readings ---------------------------------------


def test_constants_and_usage():
    assert MULTI_REPO_SLICE == "M-113"
    assert POLICY_MODES == ("read_only", "ask", "trusted")
    assert set(MODE_PHRASES) == set(POLICY_MODES)
    assert USAGE.startswith("Usage: /multirepo")
    assert "ONE change set" in PLAIN_EXPLANATION
    assert "reviewed whole" in PLAIN_EXPLANATION or \
        "planned whole" in PLAIN_EXPLANATION
    assert Policy is RepoPolicy
    assert Repo is RepoEntry
    assert Workspace is MultiRepoWorkspace
    assert CrossSet is CrossRepoChangeSet
    assert format_set is format_cross_set
    assert format_record is format_multi_repo_record


def test_mode_word_readings():
    assert normalize_policy_mode("read_only") == "read_only"
    assert normalize_policy_mode("Read-Only") == "read_only"
    assert normalize_policy_mode("readonly") == "read_only"
    assert normalize_policy_mode("ASK") == "ask"
    assert normalize_policy_mode("trust") == "trusted"
    assert normalize_policy_mode("full") == "trusted"
    with pytest.raises(ValueError):
        normalize_policy_mode("yolo")
    with pytest.raises(ValueError):
        normalize_policy_mode(None)
    with pytest.raises(ValueError):
        normalize_policy_mode("")


def test_id_and_branch_readings():
    assert normalize_repo_id("My API") == "my-api"
    assert normalize_repo_id("api_v2") == "api_v2"
    assert normalize_set_id("set-1") == "set-1"
    assert normalize_set_id("Set.2_x") == "Set.2_x"
    assert normalize_branch("feature/new-thing") == "feature/new-thing"
    assert normalize_branch("main") == "main"
    with pytest.raises(ValueError):
        normalize_repo_id("bad repo!")
    with pytest.raises(ValueError):
        normalize_repo_id("")
    with pytest.raises(ValueError):
        normalize_set_id("two words")
    with pytest.raises(ValueError):
        normalize_branch("/main")
    with pytest.raises(ValueError):
        normalize_branch("a//b")
    with pytest.raises(ValueError):
        normalize_branch("")


# -- policies -----------------------------------------------------------


def test_policy_defaults_and_writable():
    policy = RepoPolicy()
    assert policy.mode == "ask"
    assert policy.branch == "main"
    assert policy.requires_review is True
    assert policy.writable is True
    assert RepoPolicy(mode="read_only").writable is False
    record = policy.to_record()
    assert record["mode"] == "ask" and record["writable"] is True


def test_policy_validate_and_build():
    built = build_policy({"permission": "Read-Only",
                          "target_branch": "release/1",
                          "review": False})
    assert built.mode == "read_only"
    assert built.branch == "release/1"
    assert built.requires_review is False
    assert validate_policy(built) is built
    assert build_policy(built) is built
    assert build_policy(mode="trusted").mode == "trusted"
    assert validate_policy(None) == RepoPolicy()
    with pytest.raises(ValueError):
        validate_policy({"mode": "ask", "bogus": 1})
    with pytest.raises(ValueError):
        validate_policy({"mode": "ask", "permission": "trusted"})
    with pytest.raises(ValueError):
        RepoPolicy(requires_review="yes")
    with pytest.raises(ValueError):
        build_policy("ask")


# -- repos and workspaces ------------------------------------------------


def test_repo_validate_and_build():
    built = build_repo({"id": "API", "path": "/srv/api",
                        "title": "API repo",
                        "policy": {"mode": "trusted"}})
    assert built.repo_id == "api"
    assert built.label == "API repo"
    assert built.policy.mode == "trusted"
    assert validate_repo(built) is built
    plain = build_repo(repo_id="docs", root="/srv/docs")
    assert plain.label == "docs"
    assert plain.policy == RepoPolicy()
    record = plain.to_record()
    assert record["type"] == "multi_repo_repo"
    assert record["slice"] == "M-113"
    with pytest.raises(ValueError):
        validate_repo({"repo_id": "x"})
    with pytest.raises(ValueError):
        validate_repo({"repo_id": "x", "root": "/r", "bogus": 1})
    with pytest.raises(ValueError):
        RepoEntry(repo_id="x", root="  ")


def test_workspace_holds_repos_in_order():
    workspace = _workspace()
    assert workspace.repo_ids == ("api", "docs", "frozen")
    assert workspace.repo_count == 3
    assert workspace.repo_for("API").root == "/srv/api"
    assert workspace.has_repo("docs") is True
    assert workspace.has_repo("nope") is False
    record = workspace.to_record()
    assert record["type"] == "multi_repo_workspace"
    assert record["repo_ids"] == ["api", "docs", "frozen"]
    assert validate_workspace(workspace) is workspace
    assert build_workspace(workspace) is workspace


def test_workspace_unknown_repo_refuses_plainly():
    workspace = _workspace()
    with pytest.raises(ValueError) as excinfo:
        workspace.repo_for("nope")
    assert "unknown repo" in str(excinfo.value)
    assert "api" in str(excinfo.value)


def test_workspace_refuses_duplicates_and_empty():
    with pytest.raises(ValueError):
        build_workspace(name="x", repos=[])
    with pytest.raises(ValueError):
        build_workspace(name="x", repos=[
            {"repo_id": "a", "root": "/1"},
            {"repo_id": "a", "root": "/2"}])
    with pytest.raises(ValueError):
        build_workspace(name="x", repos=[
            {"repo_id": "a", "root": "/1"},
            {"repo_id": "b", "root": "/1"}])
    with pytest.raises(ValueError):
        validate_workspace({"name": "x", "bogus": 1})
    with pytest.raises(ValueError):
        MultiRepoWorkspace(name=" ", repos=[
            {"repo_id": "a", "root": "/1"}])


# -- cross-repo change sets ----------------------------------------------


def test_cross_set_is_one_m084_set_spanning_repos():
    workspace = _workspace()
    cross = build_cross_repo_change_set(workspace, "bump versions", [
        _member("docs", "guide.md", "guide v2\n"),
        _member("api", "app.py", "x = 2\n"),
    ])
    # Spans are named in workspace order, not member order.
    assert cross.repo_ids == ("api", "docs")
    assert [e.path for e in cross.change_set.edits] == [
        "docs/guide.md", "api/app.py"]
    assert cross.change_set.name == "bump versions"
    assert cross.reviewed_whole is False
    assert cross.counts() == {
        "accepted": 0, "rejected": 0, "pending": 2}
    record = cross.to_record()
    assert record["type"] == "multi_repo_change_set"
    assert record["repo_ids"] == ["api", "docs"]
    assert record["reviewed_whole"] is False


def test_cross_set_refuses_unknown_and_readonly_repos():
    workspace = _workspace()
    with pytest.raises(ValueError) as excinfo:
        build_cross_repo_change_set(workspace, "x", [
            _member("nope", "a.py", "x\n")])
    assert "unknown repo" in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        build_cross_repo_change_set(workspace, "x", [
            _member("frozen", "a.py", "x\n")])
    assert "read-only" in str(excinfo.value)
    assert "frozen" in str(excinfo.value)


def test_cross_set_refuses_bad_members():
    workspace = _workspace()
    with pytest.raises(ValueError):
        build_cross_repo_change_set(workspace, "x", [])
    with pytest.raises(ValueError):
        build_cross_repo_change_set(workspace, "x", [
            _member("api", "a.py", "one\n"),
            _member("api", "a.py", "two\n")])
    with pytest.raises(ValueError):
        build_cross_repo_change_set(workspace, "x", [
            {"repo_id": "api", "path": "a.py"}])
    with pytest.raises(ValueError):
        build_cross_repo_change_set(workspace, "x", [
            {"repo_id": "api", "path": "a.py",
             "format_id": "whole-file", "payload": "x\n",
             "bogus": 1}])
    with pytest.raises(ValueError):
        build_cross_repo_change_set(workspace, "  ", [
            _member("api", "a.py", "x\n")])


def test_cross_set_decide_and_evidence_ride_m084():
    from mythic_agent.core.change_sets import make_evidence
    workspace = _workspace()
    cross = build_cross_repo_change_set(workspace, "bump", [
        _member("api", "app.py", _SEARCH, "search-replace"),
        _member("docs", "guide.md", "guide v2\n"),
    ])
    decided = cross.decide_file(0, "accept").decide_file(1, "reject")
    assert cross.reviewed_whole is False  # the original is a value
    assert decided.reviewed_whole is True
    assert decided.counts() == {
        "accepted": 1, "rejected": 1, "pending": 0}
    with pytest.raises(ValueError):
        cross.decide_file(0, "pending")
    with pytest.raises(ValueError):
        cross.decide_file(9, "accept")
    evidenced = decided.attach(make_evidence(
        "pytest -q", 5, 0, 1, "logs/t.log"))
    record = evidenced.to_record()
    assert record["evidence"]["verdict"] == "passed"
    assert record["evidence"]["total"] == 6


def test_plan_is_whole_or_nothing():
    workspace = _workspace()
    cross = build_cross_repo_change_set(workspace, "bump", [
        _member("api", "app.py", _SEARCH, "search-replace"),
        _member("docs", "guide.md", "guide v2\n"),
    ])
    currents = {"api": {"app.py": "x = 1\n"},
                "docs": {"guide.md": "guide v1\n"}}
    # Undecided: the whole set refuses, for every repo.
    with pytest.raises(ValueError):
        plan_cross_repo_change_set(cross, currents)
    decided = cross.decide_file(0, "accept").decide_file(1, "accept")
    by_repo, outcome = plan_cross_repo_change_set(decided, currents)
    assert by_repo == {"api": {"app.py": "x = 2\n"},
                       "docs": {"guide.md": "guide v2\n"}}
    assert outcome.applied == 2 and outcome.changed_files == 2
    # A stale file in ONE repo refuses the whole set.
    stale = {"api": {"app.py": "x = 99\n"},
             "docs": {"guide.md": "guide v1\n"}}
    with pytest.raises(ValueError):
        plan_cross_repo_change_set(decided, stale)
    # A repo the set spans must be named, never guessed empty.
    with pytest.raises(ValueError):
        plan_cross_repo_change_set(decided, {"api": {"app.py": "x = 1\n"}})


def test_plan_rejected_file_never_lands():
    workspace = _workspace()
    cross = build_cross_repo_change_set(workspace, "bump", [
        _member("api", "app.py", "x = 2\n"),
        _member("docs", "guide.md", "guide v2\n"),
    ]).decide_file(0, "accept").decide_file(1, "reject")
    by_repo, outcome = plan_cross_repo_change_set(cross, {
        "api": {"app.py": "x = 1\n"},
        "docs": {"guide.md": "guide v1\n"}})
    assert by_repo == {"api": {"app.py": "x = 2\n"}}
    assert outcome.rejected == 1


def test_plain_words_and_record_state_review_honestly():
    workspace = _workspace()
    cross = build_cross_repo_change_set(workspace, "bump", [
        _member("api", "app.py", "x = 2\n")])
    words = plain_words(cross)
    assert "not yet reviewed whole" in words
    record = multi_repo_record(cross)
    assert record["type"] == "multi_repo_change_set"
    assert record["news"] is True
    assert record["slice"] == "M-113"
    assert record["headline"] == words
    decided = cross.decide_file(0, "accept")
    assert "reviewed whole as one change set" in plain_words(decided)
    assert format_multi_repo_record(record) == words
    with pytest.raises(ValueError):
        format_multi_repo_record({"type": "other"})


# -- the registry ----------------------------------------------------------


def test_registry_repos_and_workspace():
    registry = MultiRepoRegistry()
    entry = registry.register_repo(
        repo_id="api", root="/srv/api", policy={"mode": "trusted"})
    assert entry.repo_id == "api"
    registry.register_repo({"repo_id": "docs", "root": "/srv/docs"})
    assert [r.repo_id for r in registry.list_repos()] == ["api", "docs"]
    assert registry.get_repo("docs").root == "/srv/docs"
    workspace = registry.workspace("session")
    assert workspace.repo_ids == ("api", "docs")
    with pytest.raises(ValueError):
        registry.register_repo(repo_id="api", root="/elsewhere")
    with pytest.raises(ValueError) as excinfo:
        registry.get_repo("nope")
    assert "unknown repo" in str(excinfo.value)


def test_registry_set_ids_are_deterministic():
    workspace = _workspace()
    registry = MultiRepoRegistry()
    first = registry.build_and_register(workspace, "one", [
        _member("api", "a.py", "x\n")])
    assert first.set_id == "set-1"
    named = registry.register(build_cross_repo_change_set(
        workspace, "two", [_member("api", "b.py", "y\n")]))
    assert named.set_id == "set-2"
    manual = build_cross_repo_change_set(
        workspace, "three", [_member("api", "c.py", "z\n")])
    from dataclasses import replace as _replace
    manual = _replace(manual, set_id="set-4")
    assert registry.register(manual).set_id == "set-4"
    nxt = registry.build_and_register(workspace, "four", [
        _member("api", "d.py", "w\n")])
    assert nxt.set_id == "set-3"  # set-4 was taken; sequence fills first
    with pytest.raises(ValueError):
        registry.register(manual)
    assert [s.set_id for s in registry.list_sets()] == [
        "set-1", "set-2", "set-4", "set-3"]
    assert len(registry) == 4
    assert registry.get("set-1").name == "one"
    assert registry.record("set-1")["type"] == "multi_repo_change_set"
    with pytest.raises(KeyError):
        registry.get("set-99")


# -- formatters and the shared parser --------------------------------------


def test_formatters_state_policies_and_counts_in_words():
    workspace = _workspace()
    assert "read-only (no changes)" in format_repo(
        workspace.repo_for("frozen"))
    repos_text = format_repos(workspace)
    assert repos_text.startswith("Multi-repo workspace: 3 repos held.")
    assert "trusted for changes" in repos_text
    assert "no repos held" in format_repos(None)
    assert "no repos held" in format_repos(MultiRepoRegistry())
    cross = build_cross_repo_change_set(workspace, "bump", [
        _member("api", "app.py", "x = 2\n")])
    registry = MultiRepoRegistry()
    held = registry.register(cross)
    one = format_cross_set(held)
    assert one.startswith("set-1: 'bump' spans api")
    assert "not yet reviewed whole" in one
    assert "Test evidence: none attached." in one
    assert "no sets held" in format_sets(None)
    assert "1 held" in format_sets(registry)
    screen = format_multi_repo_screen(registry)
    assert screen.startswith("Multi-repo workspaces (M-113) - ")
    assert "no repos held" in screen  # this registry holds no repos
    assert USAGE in screen


def test_parser_grammar():
    assert parse_multirepo_args("") == ("show", None)
    assert parse_multirepo_args(None) == ("show", None)
    assert parse_multirepo_args("show") == ("show", None)
    assert parse_multirepo_args("repos") == ("repos", None)
    assert parse_multirepo_args("Repos") == ("repos", None)
    assert parse_multirepo_args("show set-1") == ("show", "set-1")
    assert parse_multirepo_args("set-1") == ("show", "set-1")
    assert parse_multirepo_args("Show Set-3") == ("show", "Set-3")
    for bad in ("show repos", "repos set-1", "show set-1 extra",
                "drop set-1", "show \"x\""):
        with pytest.raises(ValueError):
            parse_multirepo_args(bad)
    with pytest.raises(ValueError):
        parse_multirepo_args(42)


def test_module_is_pure_data_only():
    import pathlib
    source = pathlib.Path(
        "mythic_agent/core/multi_repo.py").read_text()
    # Run from the repo root like the suite does; fall back to the
    # module file location when invoked from elsewhere.
    if "Multi-repo workspaces" not in source:
        import mythic_agent.core.multi_repo as module
        source = pathlib.Path(module.__file__).read_text()
    assert "import subprocess" not in source
    assert "import os" not in source
    assert "import sys" not in source
    assert "open(" not in source
