"""M-138 Crew replay - pure-layer tests.

TIER: integration

The pure layer is a crew run's hand-offs read
back as a replay, as data: a replay book of
journal steps (one per hand-off of the run -
the M-126 hand-off itself, composed by import
from the comms layer, at its journal position),
the shipped example replay book held in a data
file, a loader that reads a replay book from
any file, decision traces whose account is
derived from the steps that led to the
decision, records shaped as session news, and
a registry. Nothing here reads a live journal,
re-runs a step, calls a model or spawns an
agent: a step naming a position other than
its place in the book is refused, and a stored
trace disagreeing with the account derived
from its steps is refused.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.crew_members import load_casting
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.crew_replay import (
    CREW_REPLAY_RESOURCE,
    CREW_REPLAY_SCHEMA,
    CREW_REPLAY_SLICE,
    PLAIN_EXPLANATION,
    USAGE,
    DecisionTrace,
    ReplayBook,
    ReplayRegistry,
    ReplayStep,
    book_record,
    build_book,
    build_step,
    build_trace,
    derive_trace,
    format_replay_screen,
    format_step,
    format_steps,
    format_trace,
    load_crew_replay,
    load_crew_replay_file,
    parse_replay_args,
    plain_words,
    step_record,
    trace_plain_words,
    trace_record,
    validate_book,
    validate_step,
    validate_trace,
)

ROOT = Path(__file__).resolve().parents[1]


def _handoff(**kwargs):
    kwargs.setdefault("sender", "cartographer")
    kwargs.setdefault("recipient", "architect")
    kwargs.setdefault("kind", "findings")
    kwargs.setdefault("slice_id", "M-138")
    kwargs.setdefault("title", "Run traffic mapped")
    kwargs.setdefault(
        "body",
        "The finished run's hand-offs sit in the journal "
        "in order.")
    return kwargs


def _step(**kwargs):
    kwargs.setdefault("step_id", "step-map")
    kwargs.setdefault("position", 1)
    kwargs.setdefault("handoff", _handoff())
    return ReplayStep(**kwargs)


def _steps():
    return [
        _step(),
        ReplayStep(
            step_id="step-diff", position=2,
            handoff=_handoff(
                sender="architect", recipient="forge_worker",
                kind="diff", title="Replay shape diff",
                body="crew_replay derives the replay.")),
        ReplayStep(
            step_id="step-ask", position=3,
            handoff=_handoff(
                sender="forge_worker", recipient="human",
                kind="question", title="Replay kept whole",
                body="Show every hand-off, or only the chain?")),
        ReplayStep(
            step_id="step-decision", position=4,
            handoff=_handoff(
                sender="auditor", recipient="scribe",
                title="Decision - replay derived, never stored",
                body="The replay is derived from the journal.")),
        ReplayStep(
            step_id="step-note", position=5,
            handoff=_handoff(
                sender="scribe", recipient="skald",
                slice_id="M-137", title="Earlier seat note",
                body="A note from the earlier slice.")),
    ]


def _book_data():
    return {
        "schema": CREW_REPLAY_SCHEMA, "slice": CREW_REPLAY_SLICE,
        "guide": {"title": "A replay book"},
        "steps": [
            {"step_id": s.step_id, "position": s.position,
             "handoff": {
                 "sender": s.sender, "recipient": s.recipient,
                 "kind": s.kind, "slice_id": s.slice_id,
                 "title": s.title,
                 "body": s.handoff.body}}
            for s in _steps()],
        "traces": [
            {"trace_id": "trace-replay-decision",
             "decision_step": "step-decision"},
        ]}


def _write_replay(tmp_path, data):
    path = tmp_path / "replay.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_constants_and_usage():
    assert CREW_REPLAY_SLICE == "M-138"
    assert CREW_REPLAY_RESOURCE == "crew_replay.yaml"
    assert CREW_REPLAY_SCHEMA == "mythic.crew_replay/1"
    assert USAGE.startswith("Usage: /replay")
    assert "derived from the journal" in PLAIN_EXPLANATION
    assert "auditable" in PLAIN_EXPLANATION
    assert "reads no live" in PLAIN_EXPLANATION


def test_shipped_example_book_shape():
    book = load_crew_replay()
    assert book.title == "Crew replay at the M-137 slice boundary"
    assert len(book.steps) == 5
    assert book.step_ids() == (
        "step-map", "step-diff", "step-ask",
        "step-decision", "step-note")
    assert [s.position for s in book.steps] == [1, 2, 3, 4, 5]
    first = book.step_at(1)
    assert first.sender == "cartographer"
    assert first.recipient == "architect"
    assert first.kind == "findings"
    ask = book.step_for("step-ask")
    assert ask.recipient == "human"
    assert ask.kind == "question"
    note = book.step_for("step-note")
    assert note.slice_id == "M-137"
    trace = book.trace_for("trace-replay-decision")
    assert trace.decision_step == "step-decision"
    assert trace.member == "auditor"
    assert trace.slice_id == "M-138"
    assert trace.steps == (1, 2, 3, 4)
    assert trace.account == (
        "Step 1: cartographer handed findings "
        "'Run traffic mapped' to architect (M-138).",
        "Step 2: architect handed diff "
        "'Replay shape diff' to forge_worker (M-138).",
        "Step 3: forge_worker handed question "
        "'Replay kept whole' to human (M-138).",
        "Step 4: auditor handed findings "
        "'Decision - replay derived, never stored' "
        "to scribe (M-138).",
        "The decision 'Decision - replay derived, "
        "never stored' was handed by auditor at "
        "step 4; it rests on 4 hand-offs in "
        "journal order.")


def test_example_steps_hold_shipped_casting_members():
    casting_ids = [m.member_id for m in load_casting().members]
    for step in load_crew_replay().steps:
        # The run's members are the shipped M-121
        # casting itself - a replay walks the
        # house crew's own traffic, addressed by
        # the M-121 layer's own ids.
        assert step.sender in casting_ids
        assert step.recipient == "human" \
            or step.recipient in casting_ids


def test_step_validation_and_alias_spellings():
    step = validate_step({
        "id": "step-map", "seq": 1,
        "hand_off": {
            "from_member": "cartographer",
            "to_member": "architect", "handoff_kind": "findings",
            "slice": "M-138", "title": "Run traffic mapped",
            "text": "The journal holds the run."}})
    assert step.step_id == "step-map"
    assert step.position == 1
    assert step.sender == "cartographer"
    assert step.slice_id == "M-138"
    assert build_step(step) is step
    with pytest.raises(ValueError):
        validate_step({
            "position": 1, "seq": 2, "handoff": _handoff()})
    with pytest.raises(ValueError):
        validate_step({
            "position": 1, "handoff": _handoff(),
            "entry": _handoff(title="Another title")})


def test_step_refusals():
    base = {"position": 1, "handoff": _handoff()}
    with pytest.raises(ValueError):
        validate_step({**base, "surprise": True})
    for bad_position in (0, -1, True, "1", 1.5, None):
        with pytest.raises(ValueError):
            validate_step({**base, "position": bad_position})
    # The hand-off's own law refuses through the
    # comms layer itself, composed by import.
    with pytest.raises(ValueError):
        validate_step({**base, "handoff": _handoff(sender="human")})
    with pytest.raises(ValueError):
        validate_step({**base, "handoff": _handoff(kind="rumour")})
    with pytest.raises(ValueError):
        validate_step({
            **base, "handoff": _handoff(sender="two words")})
    with pytest.raises(ValueError):
        validate_step({
            **base, "handoff": {**_handoff(), "cc": "skald"}})
    no_handoff = dict(base)
    del no_handoff["handoff"]
    with pytest.raises(ValueError):
        validate_step(no_handoff)
    no_position = dict(base)
    del no_position["position"]
    with pytest.raises(ValueError):
        validate_step(no_position)
    with pytest.raises(ValueError):
        validate_step("not a mapping")


def test_trace_derivation_is_deterministic():
    steps = _steps()
    first = derive_trace(steps, "step-decision")
    second = derive_trace(steps, 4)
    third = derive_trace(steps, steps[3])
    assert first == second == third
    assert first.member == "auditor"
    assert first.slice_id == "M-138"
    # The M-137 note at step 5 is no part of the
    # M-138 decision: the trace holds the
    # decision's own slice, in journal order.
    assert first.steps == (1, 2, 3, 4)
    assert "cartographer" in first.account[0]
    assert "human" in first.account[2]
    assert "rests on 4 hand-offs" in first.account[-1]
    opening = derive_trace(steps, "step-map")
    assert opening.steps == (1,)
    assert "rests on 1 hand-offs" in opening.account[-1]
    with pytest.raises(KeyError):
        derive_trace(steps, "step-missing")
    with pytest.raises(KeyError):
        derive_trace(steps, 9)


def test_stored_trace_must_agree_with_its_steps():
    steps = _steps()
    derived = derive_trace(steps, "step-decision")
    filled = validate_trace(
        {"decision_step": "step-decision"}, steps)
    assert filled.account == derived.account
    assert filled.steps == derived.steps
    with pytest.raises(ValueError):
        validate_trace({
            "decision_step": "step-decision",
            "account": ["The lead just decided."]}, steps)
    with pytest.raises(ValueError):
        validate_trace({
            "decision_step": "step-decision",
            "steps": [1, 4]}, steps)
    with pytest.raises(ValueError):
        validate_trace({
            "decision_step": "step-decision",
            "member": "scribe"}, steps)
    with pytest.raises(ValueError):
        validate_trace({"decision_step": "step-decision"})
    with pytest.raises(ValueError):
        validate_trace({
            "decision_step": "step-decision", "bogus": 1}, steps)
    with pytest.raises(ValueError):
        DecisionTrace(
            decision_step="step-decision", member="auditor",
            slice_id="M-138", steps=(4, 2),
            account=["Out of order."])
    built = build_trace(derive_trace(steps, "step-decision"))
    assert built == derived


def test_book_validation_and_shared_view():
    book = validate_book(_book_data())
    assert isinstance(book, ReplayBook)
    assert book.title == "A replay book"
    assert book.step_for("step-ask").recipient == "human"
    assert book.step_at(4).sender == "auditor"
    assert [s.step_id for s in book.steps_for("scribe")] == [
        "step-decision", "step-note"]
    assert [s.step_id for s in book.steps_for("human")] == [
        "step-ask"]
    assert book.trace_for(
        "trace-replay-decision").member == "auditor"
    with pytest.raises(KeyError):
        book.step_for("step-missing")
    with pytest.raises(KeyError):
        book.step_at(9)
    with pytest.raises(KeyError):
        book.trace_for("no-such-trace")
    assert build_book(book) is book
    from_fields = build_book(title="T", steps=[_step()])
    assert from_fields.step_ids() == ("step-map",)


def test_book_refusals():
    data = _book_data()
    data["steps"][1]["position"] = 3
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    data["steps"][0], data["steps"][1] = (
        data["steps"][1], data["steps"][0])
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    twin = dict(data["steps"][1])
    twin["step_id"] = "step-map"
    data["steps"][1] = twin
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    data["traces"] = [{"trace_id": "stray",
                       "decision_step": "step-missing"}]
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    data["traces"][0]["account"] = ["Invented."]
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    data["schema"] = "mythic.something_else/1"
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    data["surprise"] = True
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    del data["steps"]
    with pytest.raises(ValidationError):
        validate_book(data)
    with pytest.raises(ValidationError):
        validate_book("not a mapping")
    with pytest.raises(ValidationError):
        load_crew_replay(_book_data())


def test_file_loader_round_trip_and_missing_file(tmp_path):
    path = _write_replay(tmp_path, _book_data())
    book = load_crew_replay_file(path)
    assert book.title == "A replay book"
    assert book.step_ids() == (
        "step-map", "step-diff", "step-ask",
        "step-decision", "step-note")
    with pytest.raises(FileNotFoundError):
        load_crew_replay_file(tmp_path / "missing.yaml")
    bad = _write_replay(tmp_path, {"schema": "nope"})
    with pytest.raises(ValidationError):
        load_crew_replay_file(bad)


def test_registry_hold_and_trace():
    registry = ReplayRegistry(load_crew_replay())
    assert [s.step_id for s in registry.list_steps()] == [
        "step-map", "step-diff", "step-ask",
        "step-decision", "step-note"]
    assert registry.get_step("step-ask").recipient == "human"
    assert registry.step_at(4).step_id == "step-decision"
    derived = registry.trace_for("step-decision")
    assert derived == derive_trace(
        registry.list_steps(), "step-decision")
    held_book = registry.book()
    assert held_book.title == "Crew replay at the M-137 slice boundary"
    assert held_book.traces == ()
    with pytest.raises(KeyError):
        registry.get_step("step-missing")
    with pytest.raises(KeyError):
        registry.step_at(9)


def test_registry_auto_ids_and_refusals():
    registry = ReplayRegistry()
    step = registry.register_step({
        "position": 1, "handoff": _handoff()})
    assert step.step_id == "replay-1"
    second = registry.register_step(ReplayStep(
        position=2,
        handoff=_handoff(
            sender="architect", recipient="forge_worker",
            kind="diff", title="Replay shape diff",
            body="crew_replay derives the replay.")))
    assert second.step_id == "replay-2"
    # A step joins only at the next journal
    # position - the held order is the order.
    with pytest.raises(ValueError):
        registry.register_step({
            "position": 4, "handoff": _handoff()})
    with pytest.raises(ValueError):
        registry.register_step(_step())
    with pytest.raises(ValueError):
        ReplayRegistry().book()
    titled = ReplayRegistry(load_crew_replay())
    with pytest.raises(ValueError):
        titled.register_book(validate_book(_book_data()))


def test_records_are_session_news():
    book = load_crew_replay()
    step = book.step_for("step-decision")
    record = step_record(step)
    assert record["type"] == "crew_replay_step"
    assert record["slice"] == "M-138"
    assert record["news"] is True
    assert "step 4" in record["headline"].lower()
    assert record["position"] == 4
    assert record["handoff"]["sender"] == "auditor"
    assert record["handoff"]["slice"] == "M-126"
    whole = book_record(book)
    assert whole["type"] == "crew_replay_book"
    assert whole["step_count"] == 5
    assert whole["trace_count"] == 1
    assert whole["news"] is True
    trace = book.trace_for("trace-replay-decision")
    trecord = trace_record(trace, book)
    assert trecord["type"] == "crew_replay_trace"
    assert trecord["decision_step"] == "step-decision"
    assert trecord["steps"] == [1, 2, 3, 4]
    assert trecord["account"] == list(trace.account)
    assert trecord["news"] is True


def test_plain_words_and_trace_plain_words():
    book = load_crew_replay()
    step = book.step_for("step-ask")
    words = plain_words(step)
    assert words.startswith("forge_worker handed question")
    assert "journal step 3" in words
    assert "(M-138)" in words
    told = trace_plain_words(book)
    assert "Crew replay at the M-137 slice boundary" in told
    assert "step-decision - decision by auditor" in told
    assert "Run traffic mapped" in told
    single = trace_plain_words(
        book.trace_for("trace-replay-decision"))
    assert "step 4" in single
    with pytest.raises(ValueError):
        trace_plain_words("nope")


def test_formatters_and_screen():
    book = load_crew_replay()
    line = format_step(book.step_for("step-map"))
    assert "1. step-map: cartographer -> architect" in line
    assert "[findings]" in line
    listing = format_steps(book)
    assert "step-note" in listing
    assert "step-decision" in format_steps(book, "scribe")
    assert "step-ask" not in format_steps(book, "scribe") \
        or "step-note" in format_steps(book, "scribe")
    traces = format_trace(book)
    assert "Traces in Crew replay at the M-137 slice boundary:" in traces
    assert "decision by auditor" in traces
    assert "Nothing here." in format_trace(
        ReplayBook(title="T", steps=[_step()]))
    screen = format_replay_screen()
    assert "Crew replay (M-138)" in screen
    assert "Run traffic mapped" in screen
    assert USAGE in screen


def test_parse_replay_args_grammar():
    assert parse_replay_args("") == ("show", None)
    assert parse_replay_args(None) == ("show", None)
    assert parse_replay_args("show") == ("show", None)
    assert parse_replay_args("list") == ("show", None)
    assert parse_replay_args("step step-map") == (
        "step", "step-map")
    assert parse_replay_args("trace step-decision") == (
        "trace", "step-decision")
    for bad in ("step", "trace", "step a b", "dance",
                "show extra", 7):
        with pytest.raises(ValueError):
            parse_replay_args(bad)


def test_no_live_roads_in_pure_layer():
    import mythic_agent.core.crew_replay as module
    source = Path(module.__file__).read_text(encoding="utf-8")
    for banned in ("import subprocess", "import socket", "requests.",
                   "openai", "anthropic", "AgentManager",
                   "mythic_agent.agents", "mythic_agent.ui",
                   "WriteAheadLog", "from .journal import",
                   "def spawn", "def persist", "def execute",
                   "def rerun", "def re_run"):
        assert banned not in source
    record = _step().to_record()
    assert "executed" not in record
    assert "delivered" not in record
    assert record["handoff"]["kind"] == "findings"


def test_trace_for_the_kept_note_is_its_own_chain():
    book = load_crew_replay()
    trace = derive_trace(book, "step-note")
    # The M-137 note is the only M-137 step: its
    # trace is itself alone, and none of the
    # M-138 steps that stand before it in the
    # journal are read into it.
    assert trace.steps == (5,)
    assert trace.member == "scribe"
    assert trace.slice_id == "M-137"
    assert len(trace.account) == 2
    assert "Earlier seat note" in trace.account[0]


def test_positions_are_the_journal_order():
    with pytest.raises(ValueError):
        ReplayBook(title="T", steps=[
            _step(),
            ReplayStep(
                step_id="step-late", position=3,
                handoff=_handoff(title="Skipped a place"))])
    with pytest.raises(ValueError):
        ReplayBook(title="T", steps=[
            ReplayStep(
                step_id="step-second", position=2,
                handoff=_handoff()),
            _step()])
    book = ReplayBook(title="T", steps=_steps())
    assert [s.position for s in book.steps] == [1, 2, 3, 4, 5]
    assert book.traces == ()


def test_format_steps_member_filter_empty():
    book = load_crew_replay()
    assert format_steps(book, "guardian") == (
        "No replay steps are held.")
    auditor_steps = format_steps(book, "auditor")
    assert "step-decision" in auditor_steps
    assert "step-map" not in auditor_steps


# -- agent layer -----------------------------------------------------------
#
# M-138 agent layer: the agent holds a
# ReplayRegistry for the session (session state
# only, no new setting), steps are held by being
# registered - published as their step_record
# session news through the checkpoint road, deduped
# per step id - the report road renders the held
# book (or the shipped example when unheld) through
# the pure formatters, and the /replay surface rides
# both roads on the pure parser + formatters. Status,
# get, step-at and trace reads register and publish
# nothing, answer from the held registry first and
# from the shipped example only while nothing is
# held - a held session never falls back to the
# example. This layer reads no live journal,
# re-executes no step, spawns no agent, persists
# nothing, calls no model and claims no board -
# Part VIII does not exist yet, so the screen is
# where the replay is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _replay_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


class TestCrewReplayAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.crew_replay_status()
        assert status["steps"] == []
        assert status["book"] is None
        assert status["replay"]["title"] == (
            "Crew replay at the M-137 slice boundary")
        assert [s["step_id"] for s in status["replay"]["steps"]] == [
            "step-map", "step-diff", "step-ask",
            "step-decision", "step-note"]
        assert status["book_record"]["type"] == "crew_replay_book"
        assert status["book_record"]["step_count"] == 5
        assert [t["trace_id"] for t in status["traces"]] == [
            "trace-replay-decision"]
        assert status["traces"][0]["steps"] == [1, 2, 3, 4]
        assert "cartographer handed findings" in status["plain_words"][0]
        assert "step-decision - decision by auditor" in \
            status["trace_plain_words"]
        assert "Crew replay (M-138)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert agent._crew_replay_registry() is \
            agent._crew_replay_registry()
        assert agent._crew_replay_store is \
            agent._crew_replay_registry()

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.crew_replay_status()
        step = agent.get_replay_step("step-ask")
        assert step.recipient == "human"
        assert step.kind == "question"
        assert agent.replay_step_at(4).step_id == "step-decision"
        trace = agent.replay_trace("step-decision")
        assert trace.member == "auditor"
        assert trace.steps == (1, 2, 3, 4)
        assert "rests on 4 hand-offs" in trace.account[-1]
        assert agent.replay_trace(5).steps == (5,)
        assert agent.crew_replay().title == (
            "Crew replay at the M-137 slice boundary")
        registry = agent._crew_replay_registry()
        assert registry.list_steps() == ()
        assert _replay_events(store, session_id, "crew_replay_step") == []
        agent.close()

    def test_unheld_get_at_and_trace_raise_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.get_replay_step("no-such-step")
        with pytest.raises(KeyError):
            agent.replay_step_at(9)
        with pytest.raises(KeyError):
            agent.replay_trace("no-such-step")

    def test_status_after_register_shows_the_held_pieces(self, agent):
        agent.register_replay_step(_step())
        status = agent.crew_replay_status()
        assert [s["step_id"] for s in status["steps"]] == ["step-map"]
        assert status["book"]["step_count"] == 1
        # The held book answers now, not the example:
        # steps held one by one stand under a session
        # replay book, and it holds no traces.
        assert status["replay"]["title"] == "Session replay book"
        assert [s["step_id"] for s in status["replay"]["steps"]] == [
            "step-map"]
        assert status["traces"] == []
        assert "Run traffic mapped" in status["screen"]

    def test_held_session_never_falls_back_to_the_example(self, agent):
        agent.register_replay_step(_step())
        with pytest.raises(KeyError):
            agent.get_replay_step("step-diff")
        with pytest.raises(KeyError):
            agent.replay_step_at(2)
        with pytest.raises(KeyError):
            agent.replay_trace("step-decision")
        assert agent.crew_replay().step_ids() == ("step-map",)
        assert agent.get_replay_step("step-map").sender == "cartographer"
        assert agent.replay_trace("step-map").steps == (1,)


class TestCrewReplayAgentRegister:
    def test_register_step_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_replay_step(_step())
        assert outcome["step"]["step_id"] == "step-map"
        assert outcome["record"]["type"] == "crew_replay_step"
        events = _replay_events(store, session_id, "crew_replay_step")
        assert len(events) == 1
        assert events[0]["step_id"] == "step-map"
        # The same record is never published twice.
        agent._publish_crew_replay_record(outcome["record"])
        assert len(_replay_events(
            store, session_id, "crew_replay_step")) == 1
        # Foreign record types are refused on this road.
        from mythic_agent.core.character_voices import (
            load_character_voices,
            profile_record,
        )
        from mythic_agent.core.crew_members import (
            casting_record,
            load_casting,
        )
        from mythic_agent.core.crew_memory import (
            entry_record as _memory_entry_record,
            load_crew_memory,
        )
        from mythic_agent.core.crew_sizing import (
            case_record as _sizing_case_record,
            load_crew_sizing,
        )
        from mythic_agent.core.external_agents import (
            book_record as _external_book_record,
            check_record as _external_check_record,
            check_seat,
            load_external_agents,
            seat_record as _external_seat_record,
        )
        from mythic_agent.core.review_panels import (
            load_review_panel,
            review_record,
        )
        from mythic_agent.core.stand_ups import (
            entry_record as _stand_up_entry_record,
            load_stand_up,
        )
        agent._publish_crew_replay_record(profile_record(
            load_character_voices().profiles[0]))
        agent._publish_crew_replay_record(_sizing_case_record(
            load_crew_sizing().cases[0]))
        agent._publish_crew_replay_record({
            "type": "crew_sizing_recommendation_set"})
        agent._publish_crew_replay_record(_stand_up_entry_record(
            load_stand_up().entries[0]))
        memory = load_crew_memory()
        agent._publish_crew_replay_record(_memory_entry_record(
            memory.entry_for("broken-checkpoint-chain")))
        panel = load_review_panel()
        agent._publish_crew_replay_record(review_record(panel.reviews[0]))
        agent._publish_crew_replay_record(casting_record(
            load_casting().members[0]))
        external = load_external_agents()
        agent._publish_crew_replay_record(_external_seat_record(
            external.seats[0]))
        agent._publish_crew_replay_record(_external_book_record(external))
        agent._publish_crew_replay_record(_external_check_record(
            check_seat(external.seats[0])))
        book = load_crew_replay()
        agent._publish_crew_replay_record(book_record(book))
        agent._publish_crew_replay_record(trace_record(
            book.trace_for("trace-replay-decision"), book))
        for kind in ("character_voice_profile", "crew_sizing_case",
                     "crew_sizing_recommendation_set", "stand_up_entry",
                     "crew_memory_entry", "panel_review", "crew_member",
                     "external_seat", "external_seat_book",
                     "external_seat_check", "crew_replay_book",
                     "crew_replay_trace"):
            assert _replay_events(store, session_id, kind) == []
        assert len(_replay_events(
            store, session_id, "crew_replay_step")) == 1
        agent.close()

    def test_duplicate_step_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_replay_step(_step())
        # The same step again stands at the wrong
        # journal position now, and its id at the
        # next position is a duplicate: both refuse.
        with pytest.raises(ValueError):
            agent.register_replay_step(_step())
        with pytest.raises(ValueError):
            agent.register_replay_step(ReplayStep(
                step_id="step-map", position=2,
                handoff=_handoff(title="Same id again")))
        assert len(_replay_events(
            store, session_id, "crew_replay_step")) == 1
        agent.close()

    def test_out_of_order_step_refuses(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValueError):
            agent.register_replay_step(ReplayStep(
                step_id="step-late", position=3,
                handoff=_handoff(title="Skipped the journal")))
        assert agent._crew_replay_registry().list_steps() == ()
        assert _replay_events(store, session_id, "crew_replay_step") == []
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_replay_book(load_crew_replay())
        assert outcome["count"] == 5
        assert outcome["book"]["step_count"] == 5
        events = _replay_events(store, session_id, "crew_replay_step")
        assert [e["step_id"] for e in events] == [
            "step-map", "step-diff", "step-ask",
            "step-decision", "step-note"]
        assert agent.crew_replay().title == (
            "Crew replay at the M-137 slice boundary")
        assert agent.get_replay_step(
            "step-note").slice_id == "M-137"
        # The registry holds steps, never traces: the
        # decision's trace is derived at call time.
        assert agent.crew_replay().traces == ()
        assert agent.replay_trace("step-decision").steps == (1, 2, 3, 4)
        agent.close()

    def test_register_book_twice_refuses(self, agent):
        agent.register_replay_book(load_crew_replay())
        with pytest.raises(ValueError):
            agent.register_replay_book(load_crew_replay())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_replay_book()
        assert outcome["count"] == 5
        assert outcome["book"]["step_count"] == 5
        events = _replay_events(store, session_id, "crew_replay_step")
        assert [e["step_id"] for e in events] == [
            "step-map", "step-diff", "step-ask",
            "step-decision", "step-note"]
        assert agent.crew_replay().title == (
            "Crew replay at the M-137 slice boundary")
        assert agent.get_replay_step(
            "step-ask").recipient == "human"
        # The recorded book stands whole: its held
        # example trace still answers, and a trace for
        # the kept note derives from its own step.
        assert agent.crew_replay().traces[0].trace_id == (
            "trace-replay-decision")
        assert agent.replay_trace("step-note").steps == (5,)
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_replay_book()
        with pytest.raises(ValueError):
            agent.record_replay_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_replay(tmp_path, _book_data())
        book = load_crew_replay_file(path)
        outcome = agent.record_replay_book(book)
        assert outcome["count"] == 5
        assert agent.crew_replay().title == "A replay book"
        assert agent.get_replay_step(
            "step-decision").sender == "auditor"
        assert agent.replay_trace("step-decision").account[0] == (
            "Step 1: cartographer handed findings "
            "'Run traffic mapped' to architect (M-138).")

    def test_one_by_one_steps_stand_under_a_session_book(
            self, agent):
        agent.register_replay_step(_step())
        # Held one by one, the steps stand under a
        # session replay book composed in the agent
        # layer - never under a recorded book's title.
        assert agent.crew_replay().title == "Session replay book"
        assert agent.replay_trace("step-map").steps == (1,)
        # The journal continues: the next step joins
        # at the next position, under the same book.
        agent.register_replay_step(_steps()[1])
        assert agent.crew_replay().step_ids() == (
            "step-map", "step-diff")
        # A whole book recorded now would restart the
        # journal at position 1: the held order is the
        # journal order, so it refuses - unlike a seat
        # book, a replay cannot restart mid-run.
        with pytest.raises(ValueError):
            agent.record_replay_book()


class TestCrewReplayAgentReport:
    def test_report_renders_the_example_when_unheld(self, agent):
        outcome = agent.report_crew_replay()
        assert outcome["book"]["title"] == (
            "Crew replay at the M-137 slice boundary")
        assert outcome["book"]["step_count"] == 5
        assert "step-map" in outcome["steps_text"]
        assert "step-note" in outcome["steps_text"]
        assert "decision by auditor" in outcome["trace_text"]
        assert "Crew replay (M-138)" in outcome["screen"]
        assert outcome["explanation"] == PLAIN_EXPLANATION

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_replay_step(_step())
        outcome = agent.report_crew_replay()
        assert outcome["book"]["step_count"] == 1
        assert "step-map" in outcome["steps_text"]
        assert "step-note" not in outcome["steps_text"]
        assert "Nothing here." in outcome["trace_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_crew_replay()
        registry = agent._crew_replay_registry()
        assert registry.list_steps() == ()
        assert _replay_events(store, session_id, "crew_replay_step") == []
        agent.close()

    def test_no_live_journal_execute_or_model_road(self, agent):
        # This layer holds the replay as data: it reads
        # no live journal, re-executes no step, spawns
        # no agent, persists nothing and calls no model
        # - and there is no Part VIII board yet.
        assert not hasattr(agent, "generate_crew_replay")
        assert not hasattr(agent, "persist_crew_replay")
        assert not hasattr(agent, "execute_replay")
        assert not hasattr(agent, "rerun_replay")
        assert not hasattr(agent, "spawn_replay")
        assert not hasattr(agent, "read_live_journal")
        assert not hasattr(agent, "crew_replay_board")


class TestCrewReplayTerminalSurface:
    def test_show_step_and_trace(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/replay")
        assert "Crew replay (M-138)" in text
        _, _, text = _slash(agent, "/replay step step-map")
        assert "step-map: cartographer -> architect" in text
        assert "[findings]" in text
        _, _, text = _slash(agent, "/replay trace step-decision")
        assert "decision by auditor" in text
        assert "rests on 4 hand-offs" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert "/replay [show|step <step-id>|trace <step-id>]" in text
        _, _, text = _slash(agent, "/replay dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/replay step missing-step")
        assert "no step in the book" in text


@pytest.fixture()
def replay_handler(agent, monkeypatch):
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


def _replay_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCrewReplayCommand:
    def test_show_is_default(self, replay_handler, agent):
        replay_handler._handle_replay("")
        assert "Crew replay (M-138)" in \
            _replay_published_text(replay_handler)

    def test_step_and_trace(self, replay_handler, agent):
        replay_handler._handle_replay("step step-map")
        assert "cartographer -> architect" in _replay_published_text(
            replay_handler)
        replay_handler._handle_replay("trace step-decision")
        assert "decision by auditor" in _replay_published_text(
            replay_handler)

    def test_bad_grammar_is_published(self, replay_handler, agent):
        replay_handler._handle_replay("dance party")
        assert USAGE in _replay_published_text(replay_handler)


class TestChatScreenRoutingReplay:
    def test_replay_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/replay step step-map", _FakeLog())
        assert calls == [("/replay", "step step-map")]
