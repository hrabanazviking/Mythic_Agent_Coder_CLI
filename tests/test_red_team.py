"""M-118 - Third-party red-team pack.

TIER: integration

The third-party red-team pack
(``mythic_agent/data/red_team_pack.yaml`` +
``mythic_agent.core.red_team``): crafted
prompt-injection and tool-abuse attempts arriving
from files, web pages, issues and tool output, each
naming the shipped defence road that must hold it.

These tests do not take the pack's word for any of
it:

* the pack loads and validates, its ids, vectors,
  categories and expected outcomes are complete and
  in order, and the roadmap entry it answers is the
  queued M-118 slice,
* every attack's named carrier module truly exists,
  imports, and states its own slice constant,
* the sharpest attacks are RE-PROVEN LIVE against
  the shipped pure roads, fed the pack's own
  payloads: an injected destructive command is held
  on the ladder (M-111), an exfiltrated key shape is
  redacted and never echoed (M-110), an injected
  out-of-workspace path is denied by the jail
  (M-099), an unapproved mass edit including a
  sensitive file is refused by the guard (M-093),
  and a docker launch is refused by the sandbox
  plan (M-097),
* the scoring judge derives its verdict from the
  counts alone and refuses a partial score,
* the honesty bounds hold: the validator accepts
  no verdict but PASS and refuses duplicated or
  reordered ids, an attack with no expected outcome,
  an unknown vector or category, a carrier module
  or test file that does not exist, and an empty
  payload.
"""

from __future__ import annotations

import copy
import importlib
from pathlib import Path

import pytest

from mythic_agent.core.red_team import (
    ATTACK_IDS,
    CATEGORIES,
    EXPECTED_OUTCOMES,
    PACK_RESOURCE,
    PACK_SCHEMA,
    PACK_SLICE,
    PLAIN_EXPLANATION,
    USAGE,
    VECTORS,
    Pack,
    format_attack,
    format_attacks,
    format_pack_screen,
    format_verdict,
    judge_run,
    load_pack,
    normalize_outcome,
    pack_record,
    parse_redteam_args,
    plain_words,
    render_markdown,
    validate_pack,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Each carrier module's stem and slice constant it states.
CARRIER_CONSTANTS = {
    "mythic_agent/core/destructive_doctrine.py": (
        "destructive_doctrine", "DESTRUCTIVE_DOCTRINE_SLICE", "M-111"),
    "mythic_agent/core/secret_hygiene.py": (
        "secret_hygiene", "SECRET_HYGIENE_SLICE", "M-110"),
    "mythic_agent/core/path_jail.py": (
        "path_jail", "PATH_JAIL_SLICE", "M-099"),
    "mythic_agent/core/mass_edit_guard.py": (
        "mass_edit_guard", "MASS_EDIT_GUARD_SLICE", "M-093"),
    "mythic_agent/core/os_sandbox.py": (
        "os_sandbox", "OS_SANDBOX_SLICE", "M-097"),
}


@pytest.fixture(scope="module")
def pack() -> Pack:
    return load_pack()


def _named(payload: str, marker: str) -> str:
    """The act a payload names after its marker word."""
    return payload.split(marker, 1)[1].strip()


def test_shipped_pack_loads_and_validates(pack):
    assert isinstance(pack, Pack)
    assert validate_pack(load_resource(PACK_RESOURCE)) == []
    assert pack.pack_slice == PACK_SLICE == "M-118"
    assert pack.part == 5
    assert pack.part_title == "Autonomy & Safety"
    assert pack.verdict == "PASS"
    assert PACK_SCHEMA == "mythic.red_team_pack/1"
    assert PLAIN_EXPLANATION


def test_pack_answers_the_roadmap_slice(pack):
    road = load_roadmap()
    entry = road.slice("M-118")
    assert entry.title == "Third-party red-team pack"
    assert "prompt-injection" in entry.summary
    assert "files, web pages, issues" in entry.summary
    assert road.part(5).title == pack.part_title


def test_ids_vectors_categories_complete_in_order(pack):
    assert pack.attack_ids() == ATTACK_IDS
    assert ATTACK_IDS == tuple(f"RT-{n:02d}" for n in range(1, 13))
    # Every road third-party content arrives by is exercised:
    # the roadmap's files, web pages and issues, plus tool output.
    for vector in VECTORS:
        assert pack.attacks_for(vector), vector
    assert {a.vector for a in pack.attacks} == set(VECTORS)
    assert {a.category for a in pack.attacks} == set(CATEGORIES)
    assert {a.expected for a in pack.attacks} == set(EXPECTED_OUTCOMES)
    for attack in pack.attacks:
        assert attack.payload.strip()
        assert attack.doctrine


def test_every_carrier_module_exists_and_states_its_slice(pack):
    for attack in pack.attacks:
        assert (REPO_ROOT / attack.module).is_file(), attack.module
        assert (REPO_ROOT / attack.test_file).is_file(), attack.test_file
        stem, constant, slice_id = CARRIER_CONSTANTS[attack.module]
        assert attack.module == f"mythic_agent/core/{stem}.py"
        module = importlib.import_module(f"mythic_agent.core.{stem}")
        assert getattr(module, constant) == slice_id
        assert getattr(module, "PLAIN_EXPLANATION")


def test_attack_lookup_and_unknown_attack(pack):
    attack = pack.attack("RT-01")
    assert attack.vector == "file"
    assert attack.expected == "refuse"
    with pytest.raises(KeyError):
        pack.attack("RT-99")


def test_plain_words_record_render_and_surface(pack):
    words = plain_words(pack)
    assert "M-118" in words
    assert "PASS" in words
    assert "12 crafted attacks" in words
    record = pack_record(pack)
    assert record["type"] == "red_team_pack"
    assert record["news"] is True
    assert record["slice"] == "M-118"
    assert record["attacks"] == 12
    assert record["headline"] == words
    text = render_markdown(pack)
    assert "PASS" in text
    for attack in pack.attacks:
        assert attack.doctrine in text
    screen = format_pack_screen(pack)
    assert format_attack(pack.attack("RT-01")) in screen
    assert format_attacks(pack).count("\n") == 11
    assert parse_redteam_args("") == {"action": "show"}
    assert parse_redteam_args("show") == {"action": "show"}
    assert parse_redteam_args("list") == {"action": "list"}
    assert parse_redteam_args("attack RT-05") == {
        "action": "attack", "attack_id": "RT-05"}
    assert parse_redteam_args("rt-05") == {
        "action": "attack", "attack_id": "RT-05"}
    with pytest.raises(ValueError):
        parse_redteam_args("attack RT-99")
    with pytest.raises(ValueError):
        parse_redteam_args("detonate")
    assert USAGE.startswith("Usage: /redteam")


# ----------------------------------------------------------------------
# The validator's refusals.
# ----------------------------------------------------------------------


def _raw():
    return copy.deepcopy(load_resource(PACK_RESOURCE))


def test_validator_refuses_a_failed_verdict():
    raw = _raw()
    raw["verdict"] = "FAIL"
    problems = validate_pack(raw)
    assert any("verdict" in p for p in problems)
    with pytest.raises(ValidationError):
        load_pack(raw)


def test_validator_refuses_duplicate_and_reordered_ids():
    raw = _raw()
    raw["attacks"].append(copy.deepcopy(raw["attacks"][0]))
    problems = validate_pack(raw)
    assert any("named twice" in p or "attack ids" in p for p in problems)
    raw = _raw()
    raw["attacks"][0], raw["attacks"][1] = (
        raw["attacks"][1], raw["attacks"][0])
    problems = validate_pack(raw)
    assert any("attack ids" in p for p in problems)


def test_validator_refuses_no_expected_outcome():
    raw = _raw()
    del raw["attacks"][0]["expected"]
    problems = validate_pack(raw)
    assert any("expected outcome" in p for p in problems)
    raw = _raw()
    raw["attacks"][0]["expected"] = "ignore"
    problems = validate_pack(raw)
    assert any("expected outcome" in p for p in problems)


def test_validator_refuses_unknown_vector_and_category():
    raw = _raw()
    raw["attacks"][0]["vector"] = "carrier_pigeon"
    problems = validate_pack(raw)
    assert any("vector" in p for p in problems)
    raw = _raw()
    raw["attacks"][0]["category"] = "mischief"
    problems = validate_pack(raw)
    assert any("category" in p for p in problems)


def test_validator_refuses_missing_carrier_files():
    raw = _raw()
    raw["attacks"][0]["module"] = "mythic_agent/core/no_such_road.py"
    problems = validate_pack(raw)
    assert any("does not exist" in p for p in problems)
    raw = _raw()
    raw["attacks"][0]["test_file"] = "tests/test_no_such_road.py"
    problems = validate_pack(raw)
    assert any("does not exist" in p for p in problems)


def test_validator_refuses_an_empty_payload():
    raw = _raw()
    raw["attacks"][0]["payload"] = "  "
    problems = validate_pack(raw)
    assert any("payload" in p for p in problems)


def test_validator_refuses_a_vector_left_unexercised():
    raw = _raw()
    for entry in raw["attacks"]:
        if entry["vector"] == "tool_output":
            entry["vector"] = "file"
    problems = validate_pack(raw)
    assert any("tool_output" in p for p in problems)


# ----------------------------------------------------------------------
# The scoring judge: verdict from the counts alone.
# ----------------------------------------------------------------------


def _passing_outcomes(pack):
    return {a.id: a.expected for a in pack.attacks}


def test_judge_passes_a_fully_held_run(pack):
    verdict = judge_run(pack, _passing_outcomes(pack))
    assert verdict.verdict == "PASS"
    assert verdict.total == 12
    assert verdict.refused == 10
    assert verdict.defanged == 2
    assert verdict.succeeded == 0
    assert verdict.mismatched == 0
    assert verdict.held == 12
    assert "PASS" in format_verdict(verdict)
    assert "12 of 12" in format_verdict(verdict)


def test_judge_fails_any_success_and_any_wrong_form(pack):
    outcomes = _passing_outcomes(pack)
    outcomes["RT-01"] = "succeeded"
    verdict = judge_run(pack, outcomes)
    assert verdict.verdict == "FAIL"
    assert verdict.succeeded == 1
    outcomes = _passing_outcomes(pack)
    outcomes["RT-05"] = "refused"  # a defang expected, a refusal judged
    verdict = judge_run(pack, outcomes)
    assert verdict.verdict == "FAIL"
    assert verdict.mismatched == 1
    assert verdict.succeeded == 0


def test_judge_refuses_a_partial_or_unknown_score(pack):
    outcomes = _passing_outcomes(pack)
    del outcomes["RT-12"]
    with pytest.raises(ValueError):
        judge_run(pack, outcomes)
    outcomes = _passing_outcomes(pack)
    outcomes["RT-99"] = "refused"
    with pytest.raises(ValueError):
        judge_run(pack, outcomes)
    outcomes = _passing_outcomes(pack)
    outcomes["RT-01"] = "shrugged"
    with pytest.raises(ValueError):
        judge_run(pack, outcomes)
    assert normalize_outcome("held") == "refused"
    assert normalize_outcome("got_through") == "succeeded"


# ----------------------------------------------------------------------
# The sharpest attacks, re-proven live on the shipped pure roads,
# fed the pack's own payloads.
# ----------------------------------------------------------------------


def test_live_injected_destructive_commands_are_held(pack):
    from mythic_agent.core.destructive_doctrine import judge_command

    for attack_id in ("RT-01", "RT-03", "RT-07"):
        judged = judge_command(_named(pack.attack(attack_id).payload, "RUN: "))
        assert judged.rung == "irreversible", attack_id
        assert judged.classification == "classified"
        assert judged.approval == "explicit_named_targets"
        assert judged.needs_approval
    for attack_id in ("RT-02", "RT-11"):
        judged = judge_command(_named(pack.attack(attack_id).payload, "RUN: "))
        assert judged.rung == "costly", attack_id
        assert judged.needs_approval
    judged = judge_command(_named(pack.attack("RT-12").payload, "RUN: "))
    assert judged.rung is None
    assert judged.classification == "unclassified"
    assert judged.needs_approval


def test_live_exfiltrated_secret_shapes_are_defanged(pack):
    from mythic_agent.core.secret_hygiene import (
        REDACTION_MARKER,
        redact_secrets,
        secret_kinds_in,
    )

    payload = pack.attack("RT-05").payload
    assert "openai_key" in secret_kinds_in(payload)
    out = redact_secrets(payload)
    assert REDACTION_MARKER in out
    assert "sk-FAKE0" not in out
    payload = pack.attack("RT-09").payload
    assert "bearer_token" in secret_kinds_in(payload)
    out = redact_secrets(payload)
    assert REDACTION_MARKER in out
    assert "FAKEFAKE" not in out


def test_live_injected_paths_are_denied_by_the_jail(pack, tmp_path):
    from mythic_agent.core.path_jail import check_path

    for attack_id in ("RT-04", "RT-10"):
        target = _named(pack.attack(attack_id).payload, "READ: ")
        decision = check_path(target, tmp_path)
        assert decision.decision == "deny", attack_id
        assert not decision.allowed


def test_live_unapproved_mass_edit_is_refused(pack):
    from mythic_agent.core.mass_edit_guard import (
        build_report,
        require_approval,
    )

    plan = [
        {"path": "src/app.py", "before": "x = 1\n", "after": "x = 2\n"},
        {"path": ".env", "before": "TOKEN=old\n",
         "after": pack.attack("RT-06").payload},
    ]
    report = build_report(plan)
    assert report.requires_approval
    assert "sensitive path" in report.risks
    with pytest.raises(ValueError):
        require_approval(report, None)


def test_live_docker_launch_is_refused_by_the_sandbox(pack):
    from mythic_agent.core.os_sandbox import build_confinement_plan

    command = _named(pack.attack("RT-08").payload, "RUN: ")
    with pytest.raises(ValueError) as caught:
        build_confinement_plan(command.split())
    assert "docker" in str(caught.value).lower()


def test_module_purity():
    import inspect

    import mythic_agent.core.red_team as module

    source = inspect.getsource(module)
    assert "import subprocess" not in source
    assert "from mythic_agent.agents" not in source
    assert "from mythic_agent.ui" not in source
    assert "open(" not in source.split('"""', 2)[-1]
