"""M-246 Git host parity - pure-layer tests.

TIER: unit

The pure layer holds git hosts as registry entries like
providers, and one parity record per host as data. Parity
standing is DERIVED at call time against the parity walk
(registered, mapped, crafted, evidenced, held): a record
stands held only on a full legal walk resting on held
evidence, and stands open - named in its gaps - on a bare
claim, an illegal step, a short walk, or no evidence at
all. No host is called, no repo is cloned, and nothing is
pushed in this layer.
"""

import pytest

from mythic_agent.core.git_host_parity import (
    BARE_CLAIMS,
    CRAFTS,
    GIT_HOST_SCHEMA,
    HELD_EVIDENCE,
    HOSTS,
    STAGES,
    TRANSITIONS,
    HostEntry,
    ParityRecord,
    derive_standing,
    format_hosts,
    format_parity,
    host_record,
    legal_step,
    load_host_registry,
    load_host_registry_file,
    parity_gaps,
    plain_words,
    validate_host_entry,
    validate_host_registry,
    validate_parity_record,
)
from mythic_agent.core.validation import ValidationError

FULL_WALK = ["registered", "mapped", "crafted",
             "evidenced", "held"]


def held_record(**overrides):
    raw = {
        "host": "gitlab",
        "crafts": ["clone", "branch", "request", "merge"],
        "stages": list(FULL_WALK),
        "claims": ["remote_ref", "request_ref", "parity_ref"],
        "detail": "The GitLab walk, evidenced craft by craft.",
    }
    raw.update(overrides)
    return validate_parity_record(raw)


def test_hosts_are_the_three_named_forges():
    assert HOSTS == ("github", "gitlab", "bitbucket")
    assert GIT_HOST_SCHEMA == "mythic.git_host_parity/1"


def test_stages_and_transitions_form_one_walk():
    assert STAGES == ("registered", "mapped", "crafted",
                      "evidenced", "held")
    assert TRANSITIONS["registered"] == ("mapped",)
    assert TRANSITIONS["held"] == ()
    assert set(TRANSITIONS) == set(STAGES)


def test_crafts_are_the_host_agnostic_git_craft():
    assert CRAFTS == ("clone", "branch", "commit", "push",
                      "request", "issue", "review", "merge")
    assert "remote_ref" in HELD_EVIDENCE
    assert "assertion" in BARE_CLAIMS


def test_shipped_registry_covers_every_host_once():
    registry = load_host_registry()
    assert [h.host for h in registry.hosts] == list(HOSTS)


def test_shipped_registry_names_each_request_word():
    registry = load_host_registry()
    assert registry.for_host("gitlab").request_word == (
        "merge request")
    assert registry.for_host("github").request_word == (
        "pull request")
    assert registry.for_host("bitbucket").request_word == (
        "pull request")


def test_host_entry_refuses_unknown_host_by_name():
    with pytest.raises(ValidationError, match="unknown host"):
        validate_host_entry({
            "host": "sourceforge", "label": "SourceForge",
            "request_word": "pull request",
            "reason": "Not a host this book holds."})


def test_host_entry_refuses_half_written_records():
    with pytest.raises(ValidationError, match="reason"):
        validate_host_entry({
            "host": "github", "label": "GitHub",
            "request_word": "pull request", "reason": "  "})
    with pytest.raises(ValidationError,
                       match="request word"):
        validate_host_entry({
            "host": "github", "label": "GitHub",
            "request_word": "change ask",
            "reason": "A word no host gives the craft."})
    with pytest.raises(ValidationError, match="unknown"):
        validate_host_entry({
            "host": "github", "label": "GitHub",
            "request_word": "pull request",
            "reason": "Fine.", "extra": 1})


def test_registry_refuses_wrong_schema_and_duplicates():
    entry = {"host": "github", "label": "GitHub",
             "request_word": "pull request",
             "reason": "The first host."}
    with pytest.raises(ValidationError, match="schema"):
        validate_host_registry(
            {"schema": "mythic.other/9", "hosts": [entry]})
    with pytest.raises(ValidationError, match="duplicate"):
        validate_host_registry({
            "schema": GIT_HOST_SCHEMA,
            "hosts": [entry, dict(entry)]})


def test_registry_loads_from_any_file(tmp_path):
    path = tmp_path / "hosts.yaml"
    path.write_text(
        "schema: mythic.git_host_parity/1\n"
        "hosts:\n"
        "- host: github\n"
        "  label: GitHub\n"
        "  request_word: pull request\n"
        "  reason: Loaded from a plain file.\n",
        encoding="utf-8")
    registry = load_host_registry_file(path)
    assert registry.for_host("github").label == "GitHub"


def test_host_record_is_plain_data():
    registry = load_host_registry()
    record = host_record(registry, "gitlab")
    assert record["host"] == "gitlab"
    assert record["label"] == "GitLab"
    entry = registry.for_host("github")
    assert isinstance(entry, HostEntry)
    assert entry.record()["request_word"] == "pull request"
    with pytest.raises(ValidationError, match="unknown host"):
        host_record(registry, "codeberg")


def test_parity_record_holds_walk_whole():
    record = held_record()
    assert isinstance(record, ParityRecord)
    assert record.stage == "held"
    assert record.record()["stages"] == FULL_WALK
    assert record.record()["claims"] == [
        "remote_ref", "request_ref", "parity_ref"]


def test_parity_refuses_unknown_craft_by_name():
    with pytest.raises(ValidationError, match="craft"):
        held_record(crafts=["teleport"])


def test_parity_refuses_unknown_stage_and_claim():
    with pytest.raises(ValidationError, match="stage"):
        held_record(stages=["registered", "teleported"])
    with pytest.raises(ValidationError, match="claim"):
        held_record(claims=["vibes"])
    with pytest.raises(ValidationError, match="detail"):
        held_record(detail=" ")


def test_legal_steps_follow_the_walk():
    assert legal_step("registered", "mapped")
    assert legal_step("evidenced", "held")
    assert not legal_step("registered", "held")
    assert not legal_step("held", "mapped")
    assert not legal_step("nowhere", "mapped")


def test_standing_held_only_on_full_walk_with_evidence():
    standing = derive_standing(held_record())
    assert standing.standing == "held"
    assert standing.gaps == ()
    assert standing.stage == "held"
    assert standing.record()["host"] == "gitlab"


def test_standing_open_when_walk_stops_early():
    standing = derive_standing(held_record(
        stages=["registered", "mapped", "crafted"]))
    assert standing.standing == "open"
    assert any("not held" in gap for gap in standing.gaps)


def test_standing_open_on_illegal_step():
    gaps = parity_gaps(held_record(
        stages=["registered", "crafted", "evidenced",
                "held"]))
    assert any("not in the parity walk" in gap
               for gap in gaps)
    gaps = parity_gaps(held_record(
        stages=["mapped", "crafted", "evidenced", "held"]))
    assert any("walk opens at" in gap for gap in gaps)


def test_standing_open_on_bare_claims():
    standing = derive_standing(held_record(
        claims=["remote_ref", "assertion"]))
    assert standing.standing == "open"
    assert any("bare claims" in gap
               for gap in standing.gaps)


def test_standing_open_when_held_without_evidence():
    standing = derive_standing(held_record(claims=[]))
    assert standing.standing == "open"
    assert any("no held evidence" in gap
               for gap in standing.gaps)


def test_standing_open_with_no_craft_named():
    standing = derive_standing(held_record(crafts=[]))
    assert standing.standing == "open"
    assert any("no git craft" in gap for gap in standing.gaps)
    empty = derive_standing(held_record(stages=[], claims=[],
                                        crafts=[]))
    assert any("not begun" in gap for gap in empty.gaps)


def test_plain_words_and_formatters_speak_plainly():
    words = plain_words()
    assert "host-agnostic" in words
    assert "registry entries like providers" in words
    assert "ever claimed without held evidence" in words
    registry = load_host_registry()
    block = format_hosts(registry)
    assert "GitHub" in block and "GitLab" in block
    assert "Bitbucket" in block and "merge request" in block
    text = format_parity(held_record())
    assert "gitlab: parity held" in text
    open_text = format_parity(held_record(
        stages=["registered"], claims=["memory"]))
    assert "parity open" in open_text
    assert "gap:" in open_text
