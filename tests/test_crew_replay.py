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
