"""M-096 Remembered approvals with scope - pure-layer tests.

TIER: integration

Scopes are exact in all three parts (command + args
pattern + path), nothing is remembered silently,
the list is the whole truth in one screen, and
revocation names the id the screen shows.
"""

import pytest

from mythic_agent.core.remembered_approvals import (
    PLAIN_EXPLANATION,
    SETTING_KEY,
    approval_change_record,
    args_match,
    find_match,
    format_remembered_approval,
    format_remembered_approvals,
    matches,
    normalize_path,
    parse_remember_args,
    remember_approval,
    revoke_approval,
    scope_fingerprint,
    stored_approvals,
    validate_record,
    validate_scope,
)

SPEC = {"command": "git", "args_pattern": ["status"], "path": "/home/u/proj"}
WILD = {"command": "git", "args_pattern": ["*"], "path": "/home/u/proj"}
OTHER = {"command": "pytest", "args_pattern": ["-q"], "path": "/home/u/proj"}


def remembered(*specs):
    out = []
    for spec in specs:
        out = remember_approval(out, spec, explicit=True)
    return out


# -- scope validation ---------------------------------------------------


def test_scope_validates_and_normalizes_path():
    scope = validate_scope(
        {"command": " git ", "args_pattern": ["status"], "path": "./proj/"}
    )
    assert scope.command == "git"
    assert scope.args_pattern == ("status",)
    assert scope.path == "proj"


def test_normalize_path_spellings():
    assert normalize_path("/a/b/") == "/a/b"
    assert normalize_path("a\\b") == "a/b"
    assert normalize_path("/") == "/"
    with pytest.raises(ValueError):
        normalize_path("  ")


def test_scope_refuses_wildcard_command():
    with pytest.raises(ValueError):
        validate_scope({"command": "*", "args_pattern": [], "path": "/p"})
    with pytest.raises(ValueError):
        validate_scope({"command": "gi?", "args_pattern": [], "path": "/p"})


def test_scope_refuses_command_with_spaces():
    with pytest.raises(ValueError):
        validate_scope(
            {"command": "git status", "args_pattern": [], "path": "/p"}
        )


def test_scope_refuses_unknown_and_missing_keys():
    with pytest.raises(ValueError):
        validate_scope(
            {"command": "git", "args_pattern": [], "path": "/p", "x": 1}
        )
    with pytest.raises(ValueError):
        validate_scope({"command": "git", "args_pattern": []})


def test_scope_refuses_bad_args_pattern():
    with pytest.raises(ValueError):
        validate_scope({"command": "git", "args_pattern": "status", "path": "/p"})
    with pytest.raises(ValueError):
        validate_scope({"command": "git", "args_pattern": [""], "path": "/p"})
    with pytest.raises(ValueError):
        validate_scope({"command": "git", "args_pattern": [3], "path": "/p"})


def test_empty_args_pattern_is_valid():
    scope = validate_scope({"command": "pwd", "args_pattern": [], "path": "/p"})
    assert scope.args_pattern == ()


def test_fingerprint_is_stable_and_scope_bound():
    a = validate_scope(SPEC)
    b = validate_scope(dict(SPEC))
    c = validate_scope(OTHER)
    assert scope_fingerprint(a) == scope_fingerprint(b)
    assert scope_fingerprint(a) != scope_fingerprint(c)
    assert len(scope_fingerprint(a)) == 64


# -- exact matching -------------------------------------------------------


def test_args_match_exact_and_wildcard():
    assert args_match(("status",), ["status"]) is True
    assert args_match(("*",), ["status"]) is True
    assert args_match(("*", "*"), ["a", "b"]) is True
    assert args_match(("status",), ["log"]) is False
    assert args_match(("*",), ["a", "b"]) is False
    assert args_match((), []) is True
    assert args_match((), ["x"]) is False


def test_matches_needs_all_three_parts_exact():
    (approval,) = remembered(SPEC)
    assert matches(approval, "git", ["status"], "/home/u/proj") is True
    assert matches(approval, "git", ["status"], "/home/u/proj/") is True
    assert matches(approval, "git", ["log"], "/home/u/proj") is False
    assert matches(approval, "git", ["status", "-s"], "/home/u/proj") is False
    assert matches(approval, "hg", ["status"], "/home/u/proj") is False
    assert matches(approval, "git", ["status"], "/home/u/other") is False
    # no prefix / substring broadening
    assert matches(approval, "git", ["stat"], "/home/u/proj") is False
    assert matches(approval, "git", ["status"], "/home/u/proj/sub") is False


def test_find_match_none_and_hit():
    approvals = remembered(SPEC, OTHER)
    assert find_match(approvals, "git", ["status"], "/home/u/proj").command == "git"
    assert find_match(approvals, "git", ["push"], "/home/u/proj") is None
    assert find_match([], "git", ["status"], "/home/u/proj") is None


def test_find_match_prefers_fewest_wildcards():
    approvals = remembered(WILD, SPEC)
    hit = find_match(approvals, "git", ["status"], "/home/u/proj")
    assert hit.args_pattern == ("status",)
    hit2 = find_match(approvals, "git", ["log"], "/home/u/proj")
    assert hit2.args_pattern == ("*",)


# -- remembering: never silently -----------------------------------------


def test_remember_requires_explicit_true():
    with pytest.raises(ValueError):
        remember_approval([], SPEC)
    with pytest.raises(ValueError):
        remember_approval([], SPEC, explicit=False)
    with pytest.raises(ValueError):
        remember_approval([], SPEC, explicit="yes")
    out = remember_approval([], SPEC, explicit=True)
    assert len(out) == 1 and out[0].command == "git"


def test_remember_duplicate_refuses():
    approvals = remembered(SPEC)
    with pytest.raises(ValueError):
        remember_approval(approvals, SPEC, explicit=True)
    # same scope in a different path spelling is still a duplicate
    with pytest.raises(ValueError):
        remember_approval(
            approvals,
            {"command": "git", "args_pattern": ["status"], "path": "/home/u/proj/"},
            explicit=True,
        )


def test_remember_does_not_mutate_the_old_list():
    before = remembered(SPEC)
    after = remember_approval(before, OTHER, explicit=True)
    assert len(before) == 1 and len(after) == 2


# -- stored list ------------------------------------------------------------


def test_stored_absent_is_empty():
    assert stored_approvals({}) == []
    assert stored_approvals({SETTING_KEY: []}) == []


def test_stored_round_trip():
    approvals = remembered(SPEC, OTHER)
    config = {SETTING_KEY: [a.scope.to_record() for a in approvals]}
    back = stored_approvals(config)
    assert [a.id for a in back] == [a.id for a in approvals]


def test_stored_malformed_raises():
    with pytest.raises(ValueError):
        stored_approvals({SETTING_KEY: "git status"})
    with pytest.raises(ValueError):
        stored_approvals({SETTING_KEY: [{"command": "git"}]})
    with pytest.raises(ValueError):
        stored_approvals({SETTING_KEY: [dict(SPEC), dict(SPEC)]})
    with pytest.raises(ValueError):
        stored_approvals({SETTING_KEY: [dict(SPEC, extra=1)]})


def test_record_id_must_agree_with_scope():
    (approval,) = remembered(SPEC)
    record = approval.to_record()
    assert validate_record(record).id == approval.id
    bad = dict(record, id="0" * 64)
    with pytest.raises(ValueError):
        validate_record(bad)
    with pytest.raises(ValueError):
        validate_record(dict(record, type="something_else"))


# -- revocation -------------------------------------------------------------


def test_revoke_by_full_id_and_unique_prefix():
    approvals = remembered(SPEC, OTHER)
    target = approvals[0]
    out = revoke_approval(approvals, target.id)
    assert [a.id for a in out] == [approvals[1].id]
    out2 = revoke_approval(approvals, target.id[:8])
    assert [a.id for a in out2] == [approvals[1].id]
    assert len(approvals) == 2  # old list untouched


def test_revoke_unknown_and_short_refuse():
    approvals = remembered(SPEC)
    with pytest.raises(ValueError):
        revoke_approval(approvals, "zzzzzz")
    with pytest.raises(ValueError):
        revoke_approval(approvals, approvals[0].id[:5])
    with pytest.raises(ValueError):
        revoke_approval(approvals, "")


# -- listing + records + grammar -------------------------------------------


def test_listing_empty_and_full():
    assert "No remembered approvals" in format_remembered_approvals([])
    approvals = remembered(SPEC, OTHER)
    text = format_remembered_approvals(approvals)
    assert "Remembered approvals (2):" in text
    assert "git status in /home/u/proj" in text
    assert "pytest -q in /home/u/proj" in text
    for a in approvals:
        assert a.id[:12] in text


def test_format_one_line_and_no_args():
    (approval,) = remembered({"command": "pwd", "args_pattern": [], "path": "/p"})
    line = format_remembered_approval(approval)
    assert line.startswith("pwd (no args) in /p [")


def test_change_record_shape():
    (approval,) = remembered(SPEC)
    record = approval_change_record("remembered", approval, total=1)
    assert record["type"] == "remembered_approval"
    assert record["action"] == "remembered"
    assert record["total"] == 1
    assert record["id"] == approval.id
    with pytest.raises(ValueError):
        approval_change_record("forgot", approval, total=0)


def test_parse_remember_args():
    assert parse_remember_args("") == {"action": "list"}
    assert parse_remember_args("list") == {"action": "list"}
    assert parse_remember_args("show") == {"action": "list"}
    assert parse_remember_args("clear") == {"action": "clear"}
    assert parse_remember_args("forget abc123") == {
        "action": "forget",
        "id": "abc123",
    }
    with pytest.raises(ValueError):
        parse_remember_args("forget")
    with pytest.raises(ValueError):
        parse_remember_args("always git")


def test_plain_explanation_names_the_rules():
    assert "exact scope" in PLAIN_EXPLANATION
    assert "revoked" in PLAIN_EXPLANATION
