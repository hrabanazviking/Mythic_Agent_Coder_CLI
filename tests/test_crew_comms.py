"""M-126 Crew comms - pure-layer tests.

TIER: integration

The pure layer is the crew's traffic as data: a
hand-off (sender, recipient, kind, slice, title,
body) validated as data - the kinds the roadmap
names: findings, diffs, questions - the shipped
example ledger held in a data file, a loader that
reads a ledger from any file, the batch of a
member's questions to the human derived
mechanically from the hand-offs (batched, asked
once, with full context - never piecemeal), a
hand-off record and a batch record shaped as
session news, and a registry. Nothing here spawns
a crew, delivers a message, runs a model or runs
git, and no Part VIII board is claimed: the
hand-offs and the batch are visible on this
slice's own screen.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.crew_members import load_casting
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.crew_comms import (
    COMMS_RESOURCE,
    COMMS_SCHEMA,
    COMMS_SLICE,
    HANDOFF_KINDS,
    HUMAN_RECIPIENT,
    PLAIN_EXPLANATION,
    USAGE,
    CrewCommsRegistry,
    Handoff,
    HandoffLedger,
    HumanQuestionBatch,
    batch_human_questions,
    batch_plain_words,
    batch_record,
    build_handoff,
    format_comms_screen,
    format_handoff,
    format_handoffs,
    format_human_batch,
    format_kinds,
    handoff_record,
    human_questions,
    load_comms_ledger,
    load_comms_ledger_file,
    normalize_kind,
    normalize_recipient,
    normalize_slice_id,
    parse_comms_args,
    plain_words,
    validate_batch,
    validate_handoff,
    validate_ledger,
)

ROOT = Path(__file__).resolve().parents[1]


def _casting():
    return load_casting().members


def _handoff(**kwargs):
    kwargs.setdefault("sender", "forge_worker")
    kwargs.setdefault("recipient", "auditor")
    kwargs.setdefault("kind", "findings")
    kwargs.setdefault("slice_id", "M-126")
    kwargs.setdefault("title", "Comms shape mapped")
    kwargs.setdefault("body", "The crew holds no hand-off record yet.")
    return Handoff(**kwargs)


def _question(**kwargs):
    kwargs.setdefault("sender", "scribe")
    kwargs.setdefault("recipient", "human")
    kwargs.setdefault("kind", "question")
    kwargs.setdefault("slice_id", "M-126")
    kwargs.setdefault("title", "Board or screen first")
    kwargs.setdefault("body", "Board, or this screen until then?")
    return Handoff(**kwargs)


def _ledger_data():
    return {
        "schema": COMMS_SCHEMA, "slice": COMMS_SLICE,
        "keeper": "coordinator",
        "handoffs": [
            {"sender": "scribe", "recipient": "human",
             "kind": "question", "slice_id": "M-126",
             "title": "Board or screen first",
             "body": "Board, or this screen until then?"},
            {"sender": "auditor", "recipient": "scribe",
             "kind": "findings", "slice_id": "M-126",
             "title": "Batching rule checked",
             "body": "The batch asks once, together."},
        ]}


def _write_ledger(tmp_path, data):
    path = tmp_path / "ledger.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


# -- constants and word readings --------------------------------------------


def test_constants_and_usage():
    assert COMMS_SLICE == "M-126"
    assert COMMS_SCHEMA == "mythic.crew_comms/1"
    assert COMMS_RESOURCE == "crew_comms.yaml"
    assert HANDOFF_KINDS == ("findings", "diff", "question")
    assert HUMAN_RECIPIENT == "human"
    assert USAGE.startswith("Usage: /comms")
    assert "ask" in USAGE and "kinds" in USAGE
    assert "batched" in PLAIN_EXPLANATION
    assert "asked once" in PLAIN_EXPLANATION
    assert "no Part VIII board" in PLAIN_EXPLANATION
    assert "delivers no message" in PLAIN_EXPLANATION


def test_kind_and_recipient_readings():
    assert normalize_kind("findings") == "findings"
    assert normalize_kind("Finding") == "findings"
    assert normalize_kind("DIFFS") == "diff"
    assert normalize_kind("questions") == "question"
    for bad in ("memo", "note", "", None, 3):
        with pytest.raises(ValueError):
            normalize_kind(bad)
    assert normalize_recipient("Human") == "human"
    assert normalize_recipient("scribe") == "scribe"
    with pytest.raises(ValueError):
        normalize_recipient("bad member")
    # Slice readings are composed from the M-124 layer.
    assert normalize_slice_id("m-126") == "M-126"
    with pytest.raises(ValueError):
        normalize_slice_id("126")


def test_handoff_construction_and_record():
    handoff = _handoff()
    assert handoff.to_human is False
    assert handoff.is_question is False
    assert handoff.waits_for_human is False
    record = handoff.to_record()
    assert record["type"] == "crew_handoff"
    assert record["slice"] == "M-126"
    assert record["kind"] == "findings"
    assert record["to_human"] is False
    question = _question()
    assert question.to_human is True and question.is_question is True
    assert question.waits_for_human is True
    # A question between members never waits for the human.
    member_question = _question(recipient="auditor")
    assert member_question.is_question is True
    assert member_question.waits_for_human is False
    # A finding for the human is handed, not batched.
    finding = _handoff(recipient="human")
    assert finding.to_human is True
    assert finding.waits_for_human is False
    # Kind and recipient readings are the house readings.
    assert _handoff(kind="Diffs").kind == "diff"
    assert _question(recipient="HUMAN").recipient == "human"


def test_handoff_refusals():
    with pytest.raises(ValueError):
        _handoff(sender="human")
    with pytest.raises(ValueError):
        _handoff(sender="Human")
    with pytest.raises(ValueError):
        _handoff(kind="memo")
    with pytest.raises(ValueError):
        _handoff(slice_id="M-999")
    with pytest.raises(ValueError):
        _handoff(title="  ")
    with pytest.raises(ValueError):
        _handoff(title="Bad\ttitle")
    with pytest.raises(ValueError):
        _handoff(body="  ")
    with pytest.raises(ValueError):
        _handoff(body="x" * 8001)
    with pytest.raises(ValueError):
        _handoff(sender="bad sender")


def test_handoff_validator_aliases_and_refusals():
    handoff = validate_handoff(
        {"from_member": "scribe", "to_member": "human",
         "handoff_kind": "questions", "slice": "m-126",
         "title": "Board or screen first", "text": "Board?",
         "id": "comms-9"})
    assert handoff.sender == "scribe"
    assert handoff.recipient == "human"
    assert handoff.kind == "question"
    assert handoff.slice_id == "M-126"
    assert handoff.body == "Board?"
    assert handoff.handoff_id == "comms-9"
    assert build_handoff(handoff) is handoff
    assert build_handoff(
        sender="scribe", recipient="human", kind="question",
        slice_id="M-126", title="Board or screen first",
        body="Board?") == _question(body="Board?")
    with pytest.raises(ValueError):
        validate_handoff(
            {"sender": "scribe", "from_member": "auditor",
             "recipient": "human", "kind": "question",
             "slice_id": "M-126", "title": "T", "body": "B"})
    with pytest.raises(ValueError):
        validate_handoff(
            {"sender": "scribe", "recipient": "human",
             "kind": "question", "slice_id": "M-126",
             "title": "T", "body": "B", "surprise": 1})
    with pytest.raises(ValueError):
        validate_handoff({"sender": "scribe"})
    with pytest.raises(ValueError):
        validate_handoff("not a hand-off")


# -- the shipped example ledger -----------------------------------------------


def test_shipped_ledger_loads_as_the_example():
    ledger = load_comms_ledger()
    assert ledger.keeper == "coordinator"
    assert len(ledger.handoffs) == 6
    assert [h.kind for h in ledger.handoffs] == [
        "findings", "diff", "question", "question",
        "question", "findings"]
    assert [h.slice_id for h in ledger.by_slice("M-125")] == ["M-125"]
    assert len(ledger.by_slice("m-126")) == 5
    # Every sender and recipient is a shipped member or the human.
    member_ids = {m.member_id for m in _casting()}
    for handoff in ledger.handoffs:
        assert handoff.sender in member_ids
        assert handoff.recipient in member_ids | {"human"}
    assert validate_ledger(
        yaml.safe_load(
            (ROOT / "mythic_agent" / "data" / COMMS_RESOURCE)
            .read_text(encoding="utf-8")),
        require_example=True) == []


def test_shipped_example_check_refuses_drift():
    data = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / COMMS_RESOURCE)
        .read_text(encoding="utf-8"))
    data["handoffs"][0]["kind"] = "question"
    problems = validate_ledger(data, require_example=True)
    assert any("exactly the six hand-offs" in p for p in problems)
    # The same file is a well-formed ledger without the check.
    assert validate_ledger(data) == []
    data = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / COMMS_RESOURCE)
        .read_text(encoding="utf-8"))
    data["handoffs"][2]["recipient"] = "auditor"
    problems = validate_ledger(data, require_example=True)
    assert problems != []


# -- the batching rule ---------------------------------------------------------


def test_batch_gathers_every_human_question_once_in_order():
    ledger = load_comms_ledger()
    questions = human_questions(ledger)
    assert [q.sender for q in questions] == [
        "scribe", "auditor", "guardian"]
    assert all(q.waits_for_human for q in questions)
    batch = batch_human_questions(ledger)
    assert len(batch.questions) == 3
    assert validate_batch(ledger, batch) == []
    # Each question keeps its full context in the batch.
    record = batch_record(batch)
    assert record["type"] == "human_question_batch"
    assert record["count"] == 3
    assert record["news"] is True
    asked = record["questions"]
    assert [q["sender"] for q in asked] == [
        "scribe", "auditor", "guardian"]
    assert all(q["body"] and q["title"] and q["slice_id"]
               for q in asked)
    assert "asked once together" in record["headline"]
    # The batch is ONE record: the questions ride inside
    # it, never as separate records of their own.
    assert record["question_ids"] == [None, None, None]


def test_batch_excludes_member_questions_and_other_kinds():
    source = [
        _question(),
        _question(sender="auditor", recipient="scribe",
                  title="Read the dealing", body="Read it?"),
        _handoff(recipient="human"),
        _handoff(),
    ]
    batch = batch_human_questions(source)
    assert [q.sender for q in batch.questions] == ["scribe"]
    assert validate_batch(source, batch) == []
    empty = batch_human_questions([_handoff()])
    assert empty.questions == ()
    assert batch_plain_words(empty) == \
        "No member question waits for the human."
    assert validate_batch([_handoff()], empty) == []


def test_validate_batch_names_a_piecemeal_or_extra_batch():
    ledger = load_comms_ledger()
    questions = human_questions(ledger)
    piecemeal = HumanQuestionBatch(questions=questions[:1])
    problems = validate_batch(ledger, piecemeal)
    assert any("exactly the source's questions" in p
               for p in problems)
    extra = HumanQuestionBatch(
        questions=questions + (_question(sender="skald"),))
    assert validate_batch(ledger, extra) != []
    assert validate_batch(ledger, "not a batch") != []


def test_batch_construction_refuses_non_human_questions():
    with pytest.raises(ValueError):
        HumanQuestionBatch(questions=[_handoff()])
    with pytest.raises(ValueError):
        HumanQuestionBatch(
            questions=[_question(recipient="auditor")])
    with pytest.raises(ValueError):
        HumanQuestionBatch(questions="not questions")
    batch = HumanQuestionBatch(questions=[_question()])
    record = batch.to_record()
    assert record["count"] == 1
    assert record["questions"][0]["recipient"] == "human"


# -- ledgers on disk ------------------------------------------------------------


def test_ledger_construction_and_refusals():
    ledger = HandoffLedger(handoffs=[_handoff()], keeper="coordinator")
    assert ledger.handoffs[0].slice_id == "M-126"
    with pytest.raises(ValueError):
        HandoffLedger(handoffs=[], keeper="coordinator")
    with pytest.raises(ValueError):
        HandoffLedger(handoffs=[_handoff()], keeper="bad keeper")
    with pytest.raises(ValueError):
        HandoffLedger(handoffs="not hand-offs", keeper="coordinator")


def test_ledger_file_roundtrip(tmp_path):
    path = _write_ledger(tmp_path, _ledger_data())
    ledger = load_comms_ledger_file(path)
    assert ledger.keeper == "coordinator"
    assert [h.kind for h in ledger.handoffs] == [
        "question", "findings"]
    batch = batch_human_questions(ledger)
    assert [q.sender for q in batch.questions] == ["scribe"]


def test_ledger_file_refusals(tmp_path):
    data = _ledger_data()
    data["schema"] = "mythic.other/9"
    assert validate_ledger(data) != []
    with pytest.raises(ValidationError):
        load_comms_ledger_file(_write_ledger(tmp_path, data))
    data = _ledger_data()
    data["handoffs"] = []
    with pytest.raises(ValidationError):
        load_comms_ledger_file(_write_ledger(tmp_path, data))
    with pytest.raises(FileNotFoundError):
        load_comms_ledger_file(tmp_path / "missing.yaml")
    assert validate_ledger("not a ledger") != []
    assert validate_ledger({}) != []


# -- the registry ---------------------------------------------------------------


def test_registry_holds_and_counts():
    registry = CrewCommsRegistry()
    held = registry.register_ledger(load_comms_ledger())
    assert [h.handoff_id for h in held] == \
        [f"comms-{n}" for n in range(1, 7)]
    assert [h.slice_id for h in registry.by_sender("auditor")] == \
        ["M-125", "M-126"]
    assert [h.sender for h in registry.by_recipient("human")] == \
        ["scribe", "auditor", "guardian"]
    assert len(registry.for_member("scribe")) == 2
    assert len(registry.by_slice("M-126")) == 5
    assert registry.get("comms-3").sender == "scribe"
    with pytest.raises(KeyError):
        registry.get("comms-99")
    # The held batch is the one batch of the held questions.
    batch = registry.batch()
    assert [q.sender for q in batch.questions] == [
        "scribe", "auditor", "guardian"]
    assert validate_batch(registry, batch) == []


def test_registry_ids_and_repetition():
    registry = CrewCommsRegistry()
    first = registry.register(_handoff())
    assert first.handoff_id == "comms-1"
    # Hand-offs are messages: the same hand-off handed
    # twice is two hand-offs, never a refusal.
    second = registry.register(_handoff())
    assert second.handoff_id == "comms-2"
    supplied = registry.register(_handoff(handoff_id="comms-9"))
    assert supplied.handoff_id == "comms-9"
    with pytest.raises(ValueError):
        registry.register(_handoff(handoff_id="comms-9"))
    fresh = registry.register(_question())
    assert fresh.handoff_id == "comms-3"
    with pytest.raises(ValueError):
        registry.register_ledger("not a ledger")


# -- news, words and surfaces ---------------------------------------------------


def test_record_and_plain_words():
    record = handoff_record(_handoff())
    assert record["type"] == "crew_handoff"
    assert record["news"] is True
    assert "M-126" in record["headline"]
    words = plain_words(_handoff())
    assert "from forge_worker" in words
    assert "handed to auditor as findings" in words
    question_words = plain_words(_question())
    assert "batched" in question_words
    assert "asked once" in question_words
    batch_words = batch_plain_words(
        batch_human_questions(load_comms_ledger()))
    assert batch_words.startswith("3 questions for the human")
    assert "scribe" in batch_words and "guardian" in batch_words


def test_formatters():
    ledger = load_comms_ledger()
    text = format_handoffs(ledger)
    assert text.startswith("Crew hand-offs: 6 handed.")
    assert "M-126" in format_handoff(ledger.handoffs[0])
    assert format_handoffs() == \
        "Crew hand-offs: none. No hand-off is recorded."
    batch_text = format_human_batch(ledger)
    assert batch_text.startswith(
        "Questions for the human: 3 waiting, asked once "
        "together with full context.")
    # Full context: sender, slice, title and body all ride.
    assert "scribe asks about M-126 (Board or screen first):" \
        in batch_text
    assert "stay on this slice's own screen until then?" \
        in batch_text
    assert "auditor asks about M-125" in batch_text
    assert format_human_batch([_handoff()]) == \
        "Questions for the human: none waiting. Nothing is asked."
    kinds = format_kinds()
    assert "findings" in kinds and "diff" in kinds
    assert "question" in kinds and "batched" in kinds
    screen = format_comms_screen()
    assert "Crew comms (M-126)" in screen
    assert "Crew hand-offs: 6 handed." in screen
    assert "Questions for the human: 3 waiting" in screen
    assert "no Part VIII board" in screen
    assert USAGE in screen
    held_screen = format_comms_screen(ledger)
    assert "Batching rule checked" in held_screen


def test_parser():
    assert parse_comms_args("") == ("show", None)
    assert parse_comms_args(None) == ("show", None)
    assert parse_comms_args("show") == ("show", None)
    assert parse_comms_args("list") == ("show", None)
    assert parse_comms_args("show scribe") == ("show", "scribe")
    assert parse_comms_args("scribe") == ("show", "scribe")
    assert parse_comms_args("show human") == ("show", "human")
    assert parse_comms_args("ask") == ("ask", None)
    assert parse_comms_args("questions") == ("ask", None)
    assert parse_comms_args("batch") == ("ask", None)
    assert parse_comms_args("kinds") == ("kinds", None)
    for bad in ("show a b", "ask now", "kinds please", "a b", 42):
        with pytest.raises(ValueError):
            parse_comms_args(bad)


def test_module_purity():
    source = (ROOT / "mythic_agent" / "core" / "crew_comms.py") \
        .read_text(encoding="utf-8")
    for banned in ("agents.llm", "terminal", "command_handler",
                   "subprocess", "os.system"):
        assert banned not in source
    assert "from .crew_members import" in source
    assert "normalize_member_id" in source
    assert "from .worktrees import" in source
    assert "normalize_slice_id" in source


# -- agent layer -----------------------------------------------------------
#
# M-126 agent layer: the agent holds a
# CrewCommsRegistry for the session (session state
# only, no new setting), a ledger is recorded by
# being registered - published as its handoff_record
# session news through the checkpoint road, deduped
# per hand-off id - the one batched ask is published
# as ONE human_question_batch session event holding
# every waiting question, deduped per batch, and
# the /comms surface rides both roads on the pure
# parser + formatters. Status, find, ledger and
# batch reads register and publish nothing. This
# layer spawns no crew and delivers no message, and
# there is no Part VIII board: the screen is where
# the hand-offs and the batch are visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _comms_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


class TestCrewCommsAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.crew_comms_status()
        assert status["handoffs"] == []
        assert len(status["ledger"]) == 6
        assert status["batch"]["count"] == 3
        assert "Crew hand-offs: 6 handed." in status["screen"]
        assert "Questions for the human: 3 waiting" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert agent._crew_comms_registry() is \
            agent._crew_comms_registry()
        assert agent._crew_comms_store is \
            agent._crew_comms_registry()

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.crew_comms_status()
        found = agent.find_handoffs("scribe")
        assert [h.title for h in found] == [
            "Board or screen first", "Batching rule checked"]
        assert len(agent.find_handoffs("human")) == 3
        assert agent.comms_ledger().keeper == "coordinator"
        batch = agent.human_question_batch()
        assert [q.sender for q in batch.questions] == [
            "scribe", "auditor", "guardian"]
        assert agent._crew_comms_registry().list_handoffs() == ()
        assert _comms_events(store, session_id, "crew_handoff") == []
        assert _comms_events(
            store, session_id, "human_question_batch") == []
        agent.close()

    def test_unheld_handoff_raises_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.get_handoff("comms-1")

    def test_find_unknown_member_raises_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.find_handoffs("nobody")

    def test_status_after_register_shows_the_held_handoff(
            self, agent):
        agent.register_handoff(_handoff())
        status = agent.crew_comms_status()
        assert [h["sender"] for h in status["handoffs"]] == \
            ["forge_worker"]
        assert "Crew hand-offs: 1 handed." in status["screen"]
        assert len(status["ledger"]) == 6


class TestCrewCommsAgentRegister:
    def test_register_holds_and_publishes_once(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_handoff(_handoff())
        assert outcome["handoff"]["sender"] == "forge_worker"
        assert outcome["handoff"]["handoff_id"] == "comms-1"
        assert outcome["record"]["type"] == "crew_handoff"
        assert outcome["record"]["news"] is True
        assert agent.get_handoff("comms-1").recipient == "auditor"
        events = _comms_events(store, session_id, "crew_handoff")
        assert len(events) == 1
        assert events[0]["sender"] == "forge_worker"
        # Deduped per hand-off id: no second event.
        agent._publish_comms_record(outcome["record"])
        assert len(_comms_events(store, session_id, "crew_handoff")) == 1
        # Foreign record types are never published on these roads.
        agent._publish_comms_record(
            {"type": "task_dealing", "handoff_id": "comms-9"})
        agent._publish_comms_record(
            {"type": "crew_member", "handoff_id": "comms-9"})
        agent._publish_comms_record(
            {"type": "office", "handoff_id": "comms-9"})
        agent._publish_comms_record(
            {"type": "worktree_assignment", "handoff_id": "comms-9"})
        agent._publish_batch_record(
            {"type": "crew_handoff", "questions": []})
        agent._publish_batch_record(
            {"type": "task_dealing", "questions": []})
        assert len(_comms_events(store, session_id, "crew_handoff")) == 1
        assert _comms_events(
            store, session_id, "human_question_batch") == []
        agent.close()

    def test_record_ledger_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_comms_ledger()
        assert outcome["count"] == 6
        assert [h["handoff_id"] for h in outcome["handoffs"]] == \
            [f"comms-{n}" for n in range(1, 7)]
        assert agent.get_handoff("comms-3").sender == "scribe"
        status = agent.crew_comms_status()
        assert len(status["handoffs"]) == 6
        batch = agent.human_question_batch()
        assert [q.sender for q in batch.questions] == [
            "scribe", "auditor", "guardian"]
        events = _comms_events(store, session_id, "crew_handoff")
        assert len(events) == 6
        agent.close()

    def test_record_same_ledger_twice_refuses(self, agent):
        agent.record_comms_ledger()
        with pytest.raises(ValueError):
            agent.record_comms_ledger()
        assert len(
            agent._crew_comms_registry().list_handoffs()) == 6

    def test_ledger_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        from mythic_agent.core.crew_comms import load_comms_ledger_file
        outcome = agent.record_comms_ledger(
            load_comms_ledger_file(_write_ledger(tmp_path, _ledger_data())))
        assert outcome["count"] == 2
        assert agent.get_handoff("comms-1").sender == "scribe"
        assert agent.comms_ledger().keeper == "coordinator"
        batch = agent.human_question_batch()
        assert [q.sender for q in batch.questions] == ["scribe"]

    def test_find_prefers_the_held_handoff(self, agent):
        agent.register_handoff(_handoff(sender="auditor",
                                        recipient="scribe"))
        found = agent.find_handoffs("scribe")
        assert [h.title for h in found] == ["Comms shape mapped"]
        # Held session, member holding nothing: KeyError,
        # no silent fall back to the example ledger.
        with pytest.raises(KeyError):
            agent.find_handoffs("guardian")

    def test_ask_publishes_one_batch_event_for_all_questions(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_handoff(_question())
        agent.register_handoff(_question(
            sender="auditor", slice_id="M-125",
            title="Re-deal record kept",
            body="Keep the first dealing beside the new one?"))
        outcome = agent.ask_batched_human_questions()
        assert outcome["count"] == 2
        assert outcome["record"]["type"] == "human_question_batch"
        assert outcome["record"]["count"] == 2
        assert "Questions for the human: 2 waiting" in outcome["screen"]
        events = _comms_events(
            store, session_id, "human_question_batch")
        # ONE event holds both questions: asked once.
        assert len(events) == 1
        assert events[0]["count"] == 2
        assert len(events[0]["questions"]) == 2
        # Asking again while the same questions wait
        # publishes nothing new.
        agent.ask_batched_human_questions()
        assert len(_comms_events(
            store, session_id, "human_question_batch")) == 1
        # A newly held question grows the batch: a new ask.
        agent.register_handoff(_question(
            sender="guardian", title="Largest question batch",
            body="Every waiting question together?"))
        outcome = agent.ask_batched_human_questions()
        assert outcome["count"] == 3
        assert len(_comms_events(
            store, session_id, "human_question_batch")) == 2
        agent.close()

    def test_ask_with_no_questions_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_handoff(_handoff())
        outcome = agent.ask_batched_human_questions()
        assert outcome["count"] == 0
        assert outcome["screen"] == \
            "Questions for the human: none waiting. Nothing is asked."
        assert _comms_events(
            store, session_id, "human_question_batch") == []
        agent.close()

    def test_no_delivery_or_board_road_for_comms(self, agent):
        # This layer holds hand-offs as data: it spawns
        # no crew, delivers no message and builds no
        # board - Part VIII does not exist yet.
        assert not hasattr(agent, "deliver_handoff")
        assert not hasattr(agent, "send_handoff")
        assert not hasattr(agent, "message_member")
        assert not hasattr(agent, "comms_board")


class TestCrewCommsTerminalSurface:
    def test_show_ask_and_kinds(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/comms")
        assert "Crew hand-offs: 6 handed." in text
        _, _, text = _slash(agent, "/comms show scribe")
        assert "Board or screen first" in text
        assert "Batching rule checked" in text
        _, _, text = _slash(agent, "/comms ask")
        assert "Questions for the human: 3 waiting" in text
        assert "stay on this slice's own screen until then?" in text
        _, _, text = _slash(agent, "/comms kinds")
        assert text.startswith("Hand-off kinds:")

    def test_bare_member_shows_theirs(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/comms auditor")
        assert "Re-deal record kept" in text
        assert "Batching rule checked" in text
        _, _, text = _slash(agent, "/comms human")
        assert "Board or screen first" in text
        assert "Largest question batch" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert "/comms [show|show <member>|ask|kinds]" in text
        _, _, text = _slash(agent, "/comms dance")
        assert "no hand-off holds the member" in text
        _, _, text = _slash(agent, "/comms dance party")
        assert text == USAGE


@pytest.fixture()
def comms_handler(agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY
    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _comms_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCrewCommsCommand:
    def test_show_is_default(self, comms_handler, agent):
        comms_handler._handle_comms("")
        assert "Crew hand-offs: 6 handed." in \
            _comms_published_text(comms_handler)

    def test_show_one_ask_and_kinds(self, comms_handler, agent):
        comms_handler._handle_comms("show scribe")
        assert "Board or screen first" in \
            _comms_published_text(comms_handler)
        comms_handler._handle_comms("ask")
        assert "Questions for the human: 3 waiting" in \
            _comms_published_text(comms_handler)
        comms_handler._handle_comms("kinds")
        assert "Hand-off kinds:" in \
            _comms_published_text(comms_handler)

    def test_bad_grammar_is_published(self, comms_handler, agent):
        comms_handler._handle_comms("dance party")
        assert USAGE in _comms_published_text(comms_handler)


class TestChatScreenRoutingComms:
    def test_comms_routes_as_system_command(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import MainChatScreen

        class _FakeLog:
            def __init__(self):
                self.lines = []

            def write(self, *args, **kwargs):
                self.lines.append(" ".join(str(a) for a in args))

        calls = []
        monkeypatch.setattr(
            chat_screen.SecureAPI, "publish_system_command",
            staticmethod(lambda cmd, args: calls.append((cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        screen.handle_command("/comms ask", _FakeLog())
        assert calls == [("/comms", "ask")]
