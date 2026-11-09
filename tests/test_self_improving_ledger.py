"""M-155 The Self-Improving ledger - pure-layer tests.

TIER: integration

The pure layer is the learning loop as data: candidate
memories captured after significant work (a durable
lesson or a reusable pattern), each carried with its
provenance whole (the work learned in, the context
learned in, the evidence stood on), standing as
candidates until an explicit promotion decision by
the human or a named standing rule promotes them -
never silently - composed by import from the shipped
project memory map (M-150), the shipped session
memory (M-153), the shipped cross-project memory
(M-154) and the shipped method charter's
Self-Improving Forge tenet, with a ledger panel
derived from the whole book in settled order, the
shipped example book held in a data file, and a
loader that reads a book from any file. A candidate
stands as a standing memory only through a promoted
decision, provenance whole. Nothing here calls a
model, writes any project's files or updates any
live memory: capturing or deciding changes nothing
but data.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.project_memory_map import (
    build_entry as build_map_entry,
    load_project_memory_map,
)
from mythic_agent.core.session_memory import load_session_memory
from mythic_agent.core.cross_project_memory import (
    load_cross_project_memory,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.self_improving_ledger import (
    CANDIDATE_KINDS,
    PLAIN_EXPLANATION,
    PROMOTION_STATES,
    SELF_IMPROVING_RESOURCE,
    SELF_IMPROVING_SCHEMA,
    SELF_IMPROVING_SLICE,
    SELF_IMPROVING_TENET,
    USAGE,
    CandidateMemory,
    LedgerPanel,
    LedgerPanelRow,
    PromotionDecision,
    PromotionStateCount,
    SelfImprovingBook,
    SelfImprovingRegistry,
    book_record,
    build_book,
    build_candidate,
    build_decision,
    build_panel,
    build_row,
    candidate_from_map_entry,
    candidate_record,
    candidates_from_cross_project,
    candidates_from_memory_map,
    candidates_from_session_memory,
    decision_record,
    derive_panel,
    format_candidate,
    format_candidates,
    format_decisions,
    format_panel,
    format_self_improving_screen,
    format_standing,
    load_self_improving_ledger,
    load_self_improving_ledger_file,
    normalize_candidate_kind,
    normalize_promotion_state,
    panel_plain_words,
    panel_record,
    parse_self_improving_args,
    plain_words,
    self_improving_directives,
    standing_memories,
    validate_book,
    validate_candidate,
    validate_decision,
    validate_panel,
    validate_row,
)

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = (
    "Self-improving ledger at the M-154 slice boundary")


def _candidate(**overrides):
    fields = {
        "candidate_id": "candidate-test",
        "kind": "lesson",
        "title": "A candidate lesson",
        "detail": "The lesson itself, in plain words.",
        "source_work": "work-alpha",
        "context": "Learned while fixing the alpha test suite.",
        "evidence": "The alpha suite's failure log of the day.",
        "source": "test source",
        "ref": "alpha/core/thing.py",
    }
    fields.update(overrides)
    return build_candidate(fields)


def _decision(**overrides):
    fields = {
        "decision_id": "decision-test",
        "candidate_id": "candidate-test",
        "state": "candidate",
        "note": "Standing until the human's word.",
    }
    fields.update(overrides)
    return build_decision(fields)


def _stored_candidate(candidate):
    record = candidate.to_record()
    record.pop("type")
    record.pop("slice")
    return record


def _stored_decision(decision):
    record = decision.to_record()
    record.pop("type")
    record.pop("slice")
    return record


def _stored_panel(panel):
    record = panel.to_record()
    record.pop("type")
    record.pop("slice")
    for row in record["rows"]:
        row.pop("type")
        row.pop("slice")
    return record


def _book(candidates=None, decisions=None, **overrides):
    fields = {
        "title": "A test self-improving book",
        "candidates": [_stored_candidate(item) for item in (
            candidates if candidates is not None else [_candidate()])],
        "decisions": [_stored_decision(item) for item in (
            decisions if decisions is not None else [_decision()])],
    }
    fields.update(overrides)
    return build_book(fields)


def _shipped_raw():
    path = ROOT / "mythic_agent" / "data" / "self_improving_ledger.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_constants_and_usage():
    assert SELF_IMPROVING_SLICE == "M-155"
    assert SELF_IMPROVING_SCHEMA == "mythic.self_improving_ledger/1"
    assert SELF_IMPROVING_RESOURCE == "self_improving_ledger.yaml"
    assert SELF_IMPROVING_TENET == "self-improving-forge"
    assert CANDIDATE_KINDS == ("lesson", "pattern")
    assert PROMOTION_STATES == (
        "candidate", "promoted", "declined", "quarantined")
    assert "provenance" in PLAIN_EXPLANATION
    assert "never promoted silently" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /ledger")
    assert "candidate <candidate-id>" in USAGE


def test_shipped_example_shape():
    book = load_self_improving_ledger()
    assert isinstance(book, SelfImprovingBook)
    assert book.title == EXAMPLE_TITLE
    assert book.candidate_ids() == (
        "candidate-commit-before-answer", "candidate-reap-at-bank",
        "candidate-bank-incrementally")
    assert book.decision_ids() == (
        "decision-reap-promoted", "decision-bank-declined")
    assert book.total_candidates == 3
    assert book.total_decisions == 2
    first = book.candidates[0]
    # The first candidate stands with its provenance whole:
    # learned in the Samtal gatekeeper work, in a named
    # context, on evidence.
    assert first.source_work == "samtal-gatekeeper"
    assert first.kind == "lesson"
    assert "Gatekeeper" in first.context
    assert first.evidence
    assert first.ref == "samtal-mvp/server.py"
    assert len(book.panels) == 1


def test_shipped_panel_is_pinned_and_derived():
    book = load_self_improving_ledger()
    panel = book.panel_for("panel-m154-boundary")
    derived = derive_panel(book)
    assert validate_panel(panel, book) == panel
    assert panel.rows == derived.rows
    assert [row.candidate_id for row in panel.rows] == [
        "candidate-reap-at-bank", "candidate-commit-before-answer",
        "candidate-bank-incrementally"]
    assert [row.state for row in panel.rows] == [
        "promoted", "candidate", "declined"]
    assert panel.total_items == 3
    assert panel.total_promoted == 1
    assert panel.total_candidate == 1
    assert panel.total_declined == 1
    assert panel.total_quarantined == 0
    assert panel.account[0] == (
        "The ledger panel holds 3 candidates: promoted 1, "
        "candidate 1, declined 1, quarantined 0.")


def test_candidate_validation_and_aliases():
    candidate = build_candidate({
        "id": "candidate-alias", "type_of_memory": "durable-lesson",
        "name": "An aliased candidate", "body": "The body stands.",
        "work": "work-alpha",
        "learned_in": "A context.", "proof": "Some evidence.",
        "source": "a source", "path": "alpha/x.py"})
    assert candidate.candidate_id == "candidate-alias"
    assert candidate.kind == "lesson"
    assert candidate.title == "An aliased candidate"
    assert candidate.detail == "The body stands."
    assert candidate.source_work == "work-alpha"
    assert candidate.context == "A context."
    assert candidate.evidence == "Some evidence."
    assert candidate.ref == "alpha/x.py"
    assert normalize_candidate_kind("Reusable-Pattern") == "pattern"
    with pytest.raises(ValueError):
        normalize_candidate_kind("habit")
    with pytest.raises(ValueError):
        build_candidate({
            "kind": "lesson", "title": "Two titles",
            "name": "A different title", "detail": "D.",
            "source_work": "work-alpha", "context": "C.",
            "evidence": "E.", "source": "S", "ref": "a/b.py"})


def test_candidate_composes_the_shipped_map_entry():
    entry = build_map_entry({
        "entry_id": "map-test-trap", "section": "gotcha",
        "title": "A library trap",
        "detail": "The trap itself, in plain words.",
        "source": "the map", "ref": "alpha/lib.py"})
    candidate = candidate_from_map_entry(
        entry, kind="lesson", source_work="work-alpha",
        context="Learned the day the trap fired.",
        evidence="The trap's own traceback.")
    assert isinstance(candidate, CandidateMemory)
    assert candidate.candidate_id == "map-test-trap"
    assert candidate.kind == "lesson"
    assert candidate.title == "A library trap"
    assert candidate.detail == entry.detail
    assert candidate.source == entry.source
    assert candidate.ref == entry.ref
    assert candidate.source_work == "work-alpha"


def test_candidate_without_provenance_refuses():
    entry = build_map_entry({
        "entry_id": "map-lonely", "section": "gotcha",
        "title": "A fact at home", "detail": "It stays home.",
        "source": "the map", "ref": "alpha/lib.py"})
    # A bare entry names no kind or provenance: it is not captured.
    with pytest.raises(TypeError):
        candidate_from_map_entry(entry)
    with pytest.raises(ValueError):
        validate_candidate(entry, kind="lesson", source_work="work-alpha")
    record = _stored_candidate(_candidate())
    record.pop("evidence")
    with pytest.raises(ValueError):
        build_candidate(record)
    record = _stored_candidate(_candidate())
    record.pop("context")
    with pytest.raises(ValueError):
        build_candidate(record)
    record = _stored_candidate(_candidate())
    record.pop("source_work")
    with pytest.raises(ValueError):
        build_candidate(record)
    record = _stored_candidate(_candidate())
    record.pop("kind")
    with pytest.raises(ValueError):
        build_candidate(record)


def test_candidate_refusals():
    with pytest.raises(ValueError):
        build_candidate(_stored_candidate(_candidate()), bogus="x")
    with pytest.raises(ValueError):
        _candidate(kind="habit")
    with pytest.raises(ValueError):
        _candidate(source_work="two words")
    with pytest.raises(ValueError):
        _candidate(detail="")
    with pytest.raises(ValueError):
        _candidate(ref="has a space.py")


def test_decision_states_aliases_and_decider_law():
    assert normalize_promotion_state("candidate") == "candidate"
    assert normalize_promotion_state("Pending") == "candidate"
    assert normalize_promotion_state("approved") == "promoted"
    assert normalize_promotion_state("REJECTED") == "declined"
    assert normalize_promotion_state("held") == "quarantined"
    with pytest.raises(ValueError):
        normalize_promotion_state("smuggled")
    decision = build_decision(
        _candidate(), state="approved", decided_by="human",
        note="The human promoted it.")
    assert decision.candidate_id == "candidate-test"
    assert decision.state == "promoted"
    assert decision.decided_by == "human"
    aliased = build_decision({
        "id": "decision-alias", "candidate": "candidate-test",
        "status": "held", "authority": "standing-rule:evidence-first",
        "detail": "Held apart until its evidence is judged again."})
    assert aliased.state == "quarantined"
    assert aliased.decided_by == "standing-rule:evidence-first"
    assert aliased.note == (
        "Held apart until its evidence is judged again.")
    # A decided state naming no decider refuses: promotion
    # is explicit, never silent.
    with pytest.raises(ValueError):
        build_decision({
            "candidate_id": "candidate-test", "state": "promoted",
            "note": "Promoted by nobody, somehow."})
    # A candidate standing as a candidate names no decider:
    # no word has been given yet.
    with pytest.raises(ValueError):
        build_decision({
            "candidate_id": "candidate-test", "state": "candidate",
            "decided_by": "human", "note": "Decided already?"})
    waiting = build_decision({
        "candidate_id": "candidate-test", "state": "pending",
        "note": "Awaiting its word."})
    assert waiting.state == "candidate"
    assert waiting.decided_by is None


def test_decision_refusals():
    with pytest.raises(ValueError):
        build_decision(_stored_decision(_decision()), bogus="x")
    with pytest.raises(ValueError):
        _decision(state="smuggled")
    record = _stored_decision(_decision())
    record.pop("note")
    with pytest.raises(ValueError):
        build_decision(record)
    with pytest.raises(ValueError):
        build_decision(_candidate(candidate_id=None),
                       state="candidate", note="No id to name.")


def test_book_judges_decisions_against_candidates():
    # A decision naming a candidate the book does not hold.
    with pytest.raises(ValueError):
        _book(decisions=[_decision(candidate_id="candidate-missing")])
    # Two decisions standing on one candidate.
    with pytest.raises(ValueError):
        _book(decisions=[_decision(), _decision(decision_id="decision-two")])
    # A duplicated candidate id, and one fact named twice
    # by one work, both refuse.
    with pytest.raises(ValueError):
        _book(candidates=[_candidate(), _candidate(
            title="Another title", ref="alpha/other.py")],
            decisions=[])
    with pytest.raises(ValueError):
        _book(candidates=[_candidate(), _candidate(
            candidate_id="candidate-two", ref="alpha/other.py")],
            decisions=[])
    # Totals that are not the records' own counts refuse.
    with pytest.raises(ValueError):
        _book(total_candidates=7)


def test_book_lookups():
    book = _book()
    assert book.candidate_for("candidate-test").title == (
        "A candidate lesson")
    assert book.decision_for("decision-test").state == "candidate"
    with pytest.raises(KeyError):
        book.candidate_for("candidate-nope")
    with pytest.raises(KeyError):
        book.decision_for("decision-nope")
    with pytest.raises(KeyError):
        book.panel_for("panel-nope")


def test_panel_is_derived_in_settled_order():
    candidates = [
        _candidate(candidate_id="candidate-zed", title="Zed's lesson",
                   source_work="work-zed"),
        _candidate(candidate_id="candidate-alpha", title="Alpha's pattern",
                   kind="pattern", source_work="work-alpha"),
        _candidate(candidate_id="candidate-mid", title="Mid's lesson",
                   source_work="work-mid"),
        _candidate(candidate_id="candidate-gone", title="Gone's lesson",
                   source_work="work-gone"),
    ]
    decisions = [
        _decision(decision_id="decision-q", candidate_id="candidate-gone",
                  state="quarantined", decided_by="human",
                  note="Held apart."),
        _decision(decision_id="decision-d", candidate_id="candidate-mid",
                  state="declined", decided_by="human",
                  note="The word was no."),
        _decision(decision_id="decision-p", candidate_id="candidate-alpha",
                  state="promoted",
                  decided_by="standing-rule:patterns-stand",
                  note="Promoted under the standing rule."),
    ]
    book = _book(candidates=candidates, decisions=decisions)
    panel = derive_panel(book)
    assert [row.state for row in panel.rows] == [
        "promoted", "candidate", "declined", "quarantined"]
    assert [row.candidate_id for row in panel.rows] == [
        "candidate-alpha", "candidate-zed", "candidate-mid",
        "candidate-gone"]
    assert panel.total_items == 4
    assert panel.state_counts == tuple(
        PromotionStateCount(state=state, items=1)
        for state in ("promoted", "candidate", "declined", "quarantined"))
    row = panel.row_for("candidate-alpha")
    assert row.source_work == "work-alpha"
    assert row.kind == "pattern"
    with pytest.raises(KeyError):
        panel.row_for("candidate-nope")


def test_panel_judgement_against_its_book():
    book = _book()
    panel = derive_panel(book)
    assert validate_panel(_stored_panel(panel), book) == panel
    tampered = _stored_panel(panel)
    tampered["rows"][0]["title"] = "A softened title"
    with pytest.raises(ValueError):
        validate_panel(tampered, book)
    tampered = _stored_panel(panel)
    tampered["rows"][0]["source_work"] = "work-zed"
    with pytest.raises(ValueError):
        validate_panel(tampered, book)
    # A stored row claiming a promotion no decision gave refuses:
    # the candidate still stands as a candidate.
    tampered = _stored_panel(panel)
    tampered["rows"][0]["state"] = "promoted"
    with pytest.raises(ValueError):
        validate_panel(tampered, book)


def test_panel_construction_refusals():
    candidates = [
        _candidate(),
        _candidate(candidate_id="candidate-two", title="Second lesson",
                   source_work="work-beta", ref="beta/x.py"),
    ]
    decisions = [
        _decision(decision_id="decision-two", candidate_id="candidate-two",
                  state="promoted", decided_by="human", note="Promoted."),
    ]
    book = _book(candidates=candidates, decisions=decisions)
    panel = derive_panel(book)
    rows = list(panel.rows)
    with pytest.raises(ValueError):
        LedgerPanel(
            rows=list(reversed(rows)), total_items=2,
            total_promoted=1, total_candidate=1, total_declined=0,
            total_quarantined=0, state_counts=panel.state_counts,
            account=panel.account)
    with pytest.raises(ValueError):
        LedgerPanel(
            rows=rows, total_items=3,
            total_promoted=1, total_candidate=1, total_declined=0,
            total_quarantined=0, state_counts=panel.state_counts,
            account=panel.account)
    with pytest.raises(ValueError):
        build_panel({
            "rows": [_stored_panel(panel)["rows"][0]],
            "total_items": 1, "total_promoted": 1,
            "total_candidate": 0, "total_declined": 0,
            "total_quarantined": 0,
            "state_counts": [{"state": "promoted", "items": 1}]})


def test_panel_row_judged_against_its_candidate_and_decision():
    candidate = _candidate()
    decision = _decision()
    row = build_row({
        "state": "candidate", "candidate_id": "candidate-test",
        "kind": "lesson", "title": candidate.title,
        "detail": candidate.detail, "source_work": "work-alpha"},
        candidate, decision)
    assert isinstance(row, LedgerPanelRow)
    with pytest.raises(ValueError):
        validate_row({
            "state": "promoted", "candidate_id": "candidate-test",
            "kind": "lesson", "title": candidate.title,
            "detail": candidate.detail, "source_work": "work-alpha"},
            candidate, decision)


def test_candidates_from_the_shipped_map():
    map_book = load_project_memory_map()
    candidates = candidates_from_memory_map(
        map_book, kind="lesson", source_work="mythic-coder-campaign",
        context="The campaign's own memory map, read whole.",
        evidence="The shipped map book itself.")
    assert len(candidates) == len(map_book.entries)
    assert [item.candidate_id for item in candidates] == [
        entry.entry_id for entry in map_book.entries]
    assert all(
        item.source_work == "mythic-coder-campaign" for item in candidates)
    assert {item.title for item in candidates} == {
        entry.title for entry in map_book.entries}
    # Capture promotes nothing: every candidate stands as a candidate.
    book = _book(candidates=list(candidates), decisions=[])
    assert standing_memories(book) == ()
    assert derive_panel(book).total_candidate == len(map_book.entries)


def test_candidates_from_session_memory():
    memory_book = load_session_memory()
    candidates = candidates_from_session_memory(
        memory_book, kind="lesson", source_work="mythic-coder-campaign",
        context="Facts a session carried across its days.",
        evidence="The shipped session-memory book itself.")
    assert [item.candidate_id for item in candidates] == [
        "note-connected-code", "note-reap-at-bank",
        "note-campaign-home"]
    assert all(
        item.context == "Facts a session carried across its days."
        for item in candidates)


def test_candidates_from_cross_project_memory():
    cross_book = load_cross_project_memory()
    candidates = candidates_from_cross_project(cross_book)
    # The shared lessons' own provenance stands in: their
    # source projects, contexts and evidence, kind lesson.
    assert [item.candidate_id for item in candidates] == [
        "lesson-commit-before-answer", "lesson-reap-at-bank",
        "lesson-bank-incrementally"]
    assert [item.source_work for item in candidates] == [
        lesson.source_project for lesson in cross_book.lessons]
    assert all(item.kind == "lesson" for item in candidates)
    assert candidates[0].context == cross_book.lessons[0].context
    assert candidates[0].evidence == cross_book.lessons[0].evidence
    named = candidates_from_cross_project(
        cross_book, kind="pattern", source_work="learning-loop")
    assert all(item.kind == "pattern" for item in named)
    assert all(item.source_work == "learning-loop" for item in named)


def test_charter_directives_are_composed_by_import():
    directives = self_improving_directives()
    assert directives[0] == (
        "After significant work, capture the durable "
        "lessons it taught.")
    assert any("pattern repeats" in item for item in directives)
    assert len(directives) == 4


def test_standing_memories_only_through_promotion():
    book = load_self_improving_ledger()
    # The promoted candidate stands, provenance whole.
    standing = standing_memories(book)
    assert [item.candidate_id for item in standing] == [
        "candidate-reap-at-bank"]
    assert standing[0].source_work == "mythic-coder-campaign"
    assert standing[0].evidence
    # The undecided candidate and the declined candidate
    # stand nowhere: no silent promotion either way.
    fresh = _book(candidates=[_candidate()], decisions=[])
    assert standing_memories(fresh) == ()
    decided = _book(decisions=[_decision(
        state="promoted", decided_by="human", note="Promoted.")])
    assert [item.candidate_id for item in standing_memories(decided)] == [
        "candidate-test"]


def test_book_validation_refusals():
    raw = _shipped_raw()
    with pytest.raises(ValidationError):
        validate_book({**raw, "schema": "mythic.other/9"})
    with pytest.raises(ValidationError):
        validate_book({**raw, "bogus": 1})
    broken = {**raw, "candidates": []}
    with pytest.raises(ValidationError):
        validate_book(broken)
    broken = {**raw, "guide": {"title": "T", "bogus": 1}}
    with pytest.raises(ValidationError):
        validate_book(broken)
    # A stored panel that disagrees with its book refuses.
    import copy
    broken = copy.deepcopy(raw)
    broken["panels"][0]["rows"][0]["title"] = "A rewritten lesson"
    with pytest.raises(ValidationError):
        validate_book(broken)
    # The example check holds the shipped file to its pins.
    with pytest.raises(ValidationError):
        validate_book(
            {**raw, "guide": {"title": "Another title"}},
            require_example=True)


def test_load_self_improving_ledger_file_roundtrip(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "self_improving_ledger.yaml").read_text(encoding="utf-8")
    path = tmp_path / "self_improving_ledger.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_self_improving_ledger_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.candidate_ids()[0] == "candidate-commit-before-answer"
    with pytest.raises(FileNotFoundError):
        load_self_improving_ledger_file(tmp_path / "missing.yaml")


def test_registry_holds_candidates_and_decisions_one_by_one():
    registry = SelfImprovingRegistry()
    candidate = registry.register_candidate({
        "kind": "lesson", "title": "Held lesson",
        "detail": "Held one by one.",
        "source_work": "work-alpha",
        "context": "A registry test.", "evidence": "This test.",
        "source": "test", "ref": "alpha/x.py"})
    assert candidate.candidate_id == "candidate-1"
    # Capture alone promotes nothing.
    assert registry.standing_memories() == ()
    with pytest.raises(ValueError):
        registry.register_decision({
            "candidate_id": "candidate-missing",
            "state": "promoted", "decided_by": "human",
            "note": "No candidate stands there."})
    with pytest.raises(ValueError):
        registry.register_decision({
            "candidate_id": "candidate-1", "state": "promoted",
            "note": "Promoted by nobody."})
    decision = registry.register_decision({
        "candidate_id": "candidate-1",
        "state": "promoted", "decided_by": "human",
        "note": "The human promoted it."})
    assert decision.decision_id == "decision-1"
    with pytest.raises(ValueError):
        registry.register_decision({
            "candidate_id": "candidate-1", "state": "declined",
            "decided_by": "human", "note": "Twice on one candidate."})
    assert [item.candidate_id for item in registry.list_candidates()] == [
        "candidate-1"]
    panel = registry.panel()
    assert panel.total_items == 1
    assert panel.total_promoted == 1
    assert [item.candidate_id for item in registry.standing_memories()] == [
        "candidate-1"]
    with pytest.raises(KeyError):
        registry.get_candidate("candidate-nope")


def test_registry_register_book_titles():
    registry = SelfImprovingRegistry()
    registry.register_book(load_self_improving_ledger())
    assert registry.book().title == EXAMPLE_TITLE
    with pytest.raises(ValueError):
        registry.register_book(load_self_improving_ledger())
    other = SelfImprovingRegistry()
    other.register_candidate(_candidate())
    with pytest.raises(ValueError):
        other.register_book(_book(title="Another title"))


def test_records_and_plain_words():
    candidate = _candidate()
    candidate_news = candidate_record(candidate)
    assert candidate_news["type"] == "self_improving_candidate"
    assert candidate_news["news"] is True
    assert "work-alpha" in candidate_news["headline"]
    decision_news = decision_record(_decision(
        state="promoted", decided_by="human", note="Promoted."))
    assert decision_news["type"] == "self_improving_decision"
    assert "human" in decision_news["headline"]
    book = _book()
    panel_news = panel_record(derive_panel(book), book)
    assert panel_news["type"] == "self_improving_panel"
    book_news = book_record(book)
    assert book_news["type"] == "self_improving_book"
    assert book_news["candidate_count"] == 1
    assert book_news["decision_count"] == 1
    words = plain_words(candidate)
    assert "learned in work-alpha" in words
    assert "The alpha suite's failure log" in words
    told = panel_plain_words(book)
    assert "A test self-improving book" in told
    assert "candidate-test: candidate" in told


def test_formatters_and_screen():
    book = load_self_improving_ledger()
    assert "candidate-reap-at-bank" in format_candidate(
        book.candidate_for("candidate-reap-at-bank"))
    assert "learned in samtal-gatekeeper" in format_candidate(
        book.candidate_for("candidate-commit-before-answer"))
    assert "candidate-bank-incrementally" in format_candidates(book)
    decisions_text = format_decisions(book)
    assert "decision-reap-promoted" in decisions_text
    assert "standing-rule:reap-at-bank" in decisions_text
    standing_text = format_standing(book)
    assert "candidate-reap-at-bank" in standing_text
    assert "mythic-coder-campaign" in standing_text
    empty = _book(candidates=[_candidate()], decisions=[])
    assert format_standing(empty) == "No candidates stand promoted yet."
    panel_text = format_panel(book)
    assert "Ledger panel in Self-improving ledger" in panel_text
    screen = format_self_improving_screen()
    assert "Self-Improving Ledger (M-155)" in screen
    assert "candidate-commit-before-answer" in screen
    assert USAGE in screen


def test_parse_self_improving_args_grammar():
    assert parse_self_improving_args("") == ("show", None)
    assert parse_self_improving_args("show") == ("show", None)
    assert parse_self_improving_args("list") == ("show", None)
    assert parse_self_improving_args(
        "candidate candidate-test") == ("candidate", "candidate-test")
    assert parse_self_improving_args("decisions") == ("decisions", None)
    assert parse_self_improving_args("standing") == ("standing", None)
    assert parse_self_improving_args("panel") == ("panel", None)
    for bad in ("dance", "candidate", "standing now",
                "candidate two words", "decisions now"):
        with pytest.raises(ValueError):
            parse_self_improving_args(bad)


def test_honest_boundary_module_imports_no_live_roads():
    source = (ROOT / "mythic_agent" / "core"
              / "self_improving_ledger.py").read_text(encoding="utf-8")
    # The pure layer composes the shipped project
    # memory map, session memory, cross-project memory
    # and method charter by import, and imports no
    # agent, ui or terminal code: capturing or deciding
    # can call no model, write no project's files and
    # promote nothing silently.
    assert "from .project_memory_map import" in source
    assert "from .session_memory import" in source
    assert "from .cross_project_memory import" in source
    assert "from .method_charter import" in source
    assert "from ..agents" not in source
    assert "from ..ui" not in source
    assert "from ..terminal" not in source
    assert "import agents" not in source


# -- agent layer -----------------------------------------------------------
#
# M-155 agent layer: the agent holds a
# SelfImprovingRegistry for the session (session state
# only, no new setting), candidates and decisions are
# held by being registered - published as their
# candidate_record / decision_record session news with
# the derived panel_record, through the checkpoint
# road, deduped per shape - the report road renders
# the held book (or the shipped example when unheld)
# through the pure formatters, a capture road reads
# the session's project memory map book onto candidates
# and holds them (promoting nothing), and the /ledger
# surface rides both roads on the pure parser +
# formatters. Status, get, panel and standing reads
# register and publish nothing, answer from the held
# registry first and from the shipped example only
# while nothing is held - a held session never falls
# back to the example. The panel derives at call time
# from the whole book, never held. This layer calls no
# model, writes no project files and updates no live
# memory, and there is no Part VIII board yet, so the
# screen is where the ledger is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _ledger_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_ledger_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "self_improving_ledger.yaml").read_text(encoding="utf-8")
    path = tmp_path / "self_improving_ledger.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestSelfImprovingAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.self_improving_status()
        assert status["candidates"] == []
        assert status["decisions"] == []
        assert status["book"] is None
        assert status["ledger"]["title"] == EXAMPLE_TITLE
        assert len(status["ledger"]["candidates"]) == 3
        assert status["panel"]["total_items"] == 3
        assert status["panel"]["total_promoted"] == 1
        assert status["panels"][0]["panel_id"] == (
            "panel-m154-boundary")
        assert status["book_record"]["candidate_count"] == 3
        assert "Self-Improving Ledger (M-155)" in (
            status["screen"])
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._self_improving_registry()
        assert agent._self_improving_registry() is first
        assert agent._self_improving_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.self_improving_status()
        agent.get_self_improving_candidate("candidate-reap-at-bank")
        agent.get_self_improving_decision("decision-reap-promoted")
        agent.self_improving_panel()
        agent.standing_self_improving_memories()
        agent.report_self_improving_ledger()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("self_improving")] == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_self_improving_candidate("candidate-nope")
        with pytest.raises(KeyError):
            agent.get_self_improving_decision("decision-nope")

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_self_improving_candidate(_candidate())
        status = agent.self_improving_status()
        assert [item["candidate_id"] for item in status["candidates"]] == [
            "candidate-test"]
        assert status["book"]["title"] == (
            "Self-improving ledger")

    def test_held_session_never_falls_back_to_the_example(
            self, agent):
        agent.register_self_improving_candidate(_candidate())
        with pytest.raises(KeyError):
            agent.get_self_improving_candidate("candidate-reap-at-bank")
        candidate = agent.get_self_improving_candidate("candidate-test")
        assert candidate.title == "A candidate lesson"
        assert agent.self_improving_book().title == (
            "Self-improving ledger")


class TestSelfImprovingAgentHolding:
    def test_register_candidate_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_self_improving_candidate(_candidate())
        assert outcome["candidate"]["candidate_id"] == "candidate-test"
        assert outcome["candidate_news"]["type"] == (
            "self_improving_candidate")
        events = _ledger_events(
            store, session_id, "self_improving_candidate")
        assert len(events) == 1
        assert events[0]["candidate_id"] == "candidate-test"
        agent._publish_self_improving_record(
            outcome["candidate_news"])
        assert len(_ledger_events(
            store, session_id, "self_improving_candidate")) == 1
        agent._publish_self_improving_record(
            {"type": "mentions_mention", "mention_id": "mention-x"})
        agent._publish_self_improving_record(
            book_record(load_self_improving_ledger()))
        for kind in ("mentions_mention", "self_improving_book"):
            assert _ledger_events(store, session_id, kind) == []
        # Capture alone promoted nothing.
        assert agent.standing_self_improving_memories() == ()
        agent.close()

    def test_duplicate_candidate_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_self_improving_candidate(_candidate())
        with pytest.raises(ValueError):
            agent.register_self_improving_candidate(_candidate())
        assert len(_ledger_events(
            store, session_id, "self_improving_candidate")) == 1
        agent.close()

    def test_register_decision_holds_and_publishes_decision_and_panel(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_self_improving_candidate(_candidate())
        outcome = agent.register_self_improving_decision(_decision(
            decision_id=None, state="promoted", decided_by="human",
            note="The human promoted it."))
        assert outcome["decision"]["state"] == "promoted"
        assert outcome["panel_record"]["type"] == (
            "self_improving_panel")
        decisions = _ledger_events(
            store, session_id, "self_improving_decision")
        assert len(decisions) == 1
        panels = _ledger_events(
            store, session_id, "self_improving_panel")
        assert len(panels) == 1
        assert panels[0]["total_items"] == 1
        standing = agent.standing_self_improving_memories()
        assert [item.candidate_id for item in standing] == [
            "candidate-test"]
        assert standing[0].source_work == "work-alpha"
        agent.close()

    def test_decision_refusals_hold_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValueError):
            agent.register_self_improving_decision(_decision())
        agent.register_self_improving_candidate(_candidate())
        with pytest.raises(ValueError):
            agent.register_self_improving_decision({
                "candidate_id": "candidate-test", "state": "promoted",
                "note": "Promoted by nobody."})
        assert _ledger_events(
            store, session_id, "self_improving_decision") == []
        agent.close()

    def test_capture_memory_map_candidates_composes_the_map(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        map_book = load_project_memory_map()
        outcome = agent.capture_memory_map_candidates(
            kind="lesson", source_work="mythic-coder-campaign",
            context="The coder campaign's own map, read whole.",
            evidence="The shipped project memory map book.")
        assert outcome["count"] == len(map_book.entries)
        assert len(_ledger_events(
            store, session_id, "self_improving_candidate")) == len(
                map_book.entries)
        # Every captured candidate stands as a candidate:
        # capture promoted nothing, silently or otherwise.
        book = agent.self_improving_book()
        assert agent.standing_self_improving_memories() == ()
        assert agent.self_improving_panel().total_candidate == len(
            map_book.entries)
        assert {item.source_work for item in book.candidates} == {
            "mythic-coder-campaign"}
        with pytest.raises(ValueError):
            agent.capture_memory_map_candidates(
                kind="lesson", source_work="mythic-coder-campaign",
                context="Again.", evidence="Again.")
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent):
        book = _book()
        outcome = agent.register_self_improving_book(book)
        assert outcome["count"] == 1
        assert outcome["decision_count"] == 1
        assert [item["type"] for item in outcome["candidates_news"]] == [
            "self_improving_candidate"]
        assert [item["type"] for item in outcome["decisions_news"]] == [
            "self_improving_decision"]
        assert agent.self_improving_book().title == (
            "A test self-improving book")

    def test_register_book_twice_refuses(self, agent):
        agent.register_self_improving_book(
            load_self_improving_ledger())
        with pytest.raises(ValueError):
            agent.register_self_improving_book(
                load_self_improving_ledger())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_self_improving_book()
        assert outcome["count"] == 3
        assert outcome["decision_count"] == 2
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_ledger_events(
            store, session_id, "self_improving_candidate")) == 3
        assert len(_ledger_events(
            store, session_id, "self_improving_decision")) == 2
        assert agent.self_improving_book().panels[0].panel_id == (
            "panel-m154-boundary")
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_self_improving_book()
        with pytest.raises(ValueError):
            agent.record_self_improving_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_ledger_book(tmp_path)
        book = load_self_improving_ledger_file(path)
        outcome = agent.record_self_improving_book(book)
        assert outcome["count"] == 3
        assert agent.get_self_improving_candidate(
            "candidate-reap-at-bank").title == (
                "Verify copies are reaped at bank")

    def test_report_renders_the_example_when_unheld(self, agent):
        report = agent.report_self_improving_ledger()
        assert report["book"]["candidate_count"] == 3
        assert "candidate-reap-at-bank" in report["candidates_text"]
        assert "Ledger panel in Self-improving" in (
            report["panel_text"])

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_self_improving_candidate(_candidate())
        report = agent.report_self_improving_ledger()
        assert report["book"]["title"] == (
            "Self-improving ledger")
        assert "candidate-reap-at-bank" not in report["candidates_text"]
        assert "candidate-test" in report["candidates_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_self_improving_ledger()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("self_improving")] == []
        agent.close()

    def test_no_live_write_or_persist_road(
            self, agent, tmp_path):
        # This layer holds candidates and decisions as
        # data: it calls no model, writes no project
        # files, updates no live memory and persists
        # nothing - and there is no Part VIII board yet.
        # Holding, recording or capturing changes no
        # workspace file and no live context.
        assert not hasattr(agent, "apply_self_improving_ledger")
        assert not hasattr(agent, "edit_self_improving_ledger")
        assert not hasattr(agent, "persist_self_improving_ledger")
        assert not hasattr(agent, "promote_self_improving_candidate")
        assert not hasattr(agent, "self_improving_board")
        (tmp_path / "alpha.py").write_text(
            "def greet(name):\n    return name\n", encoding="utf-8")
        before = {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")}
        from mythic_agent.agents.context import ContextBuilder
        builder = ContextBuilder(max_tokens=4000)
        builder.add_system("You are the coder.")
        builder.add_turn("user", "Build the slice.")
        built_before = builder.build()
        agent.register_self_improving_candidate(_candidate())
        agent.record_self_improving_book()
        assert builder.build() == built_before
        assert {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")} == before


class TestSelfImprovingTerminalSurface:
    def test_show_candidate_decisions_standing_panel(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/ledger")
        assert "Self-Improving Ledger (M-155)" in text
        _, _, text = _slash(
            agent, "/ledger candidate candidate-reap-at-bank")
        assert "Verify copies are reaped at bank" in text
        _, _, text = _slash(agent, "/ledger decisions")
        assert "decision-reap-promoted" in text
        _, _, text = _slash(agent, "/ledger standing")
        assert "candidate-reap-at-bank" in text
        _, _, text = _slash(agent, "/ledger panel")
        assert "Ledger panel in Self-improving" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/ledger [show|candidate <candidate-id>"
                "|decisions|standing|panel]") in text
        _, _, text = _slash(agent, "/ledger dance party")
        assert text == USAGE
        _, _, text = _slash(
            agent, "/ledger candidate candidate-nope")
        assert "no candidate in the book" in text


@pytest.fixture()
def ledger_handler(agent, monkeypatch):
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


def _ledger_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestSelfImprovingCommand:
    def test_show_is_default(self, ledger_handler, agent):
        ledger_handler._handle_ledger("")
        assert "Self-Improving Ledger (M-155)" in (
            _ledger_published_text(ledger_handler))

    def test_candidate_decisions_standing_panel(
            self, ledger_handler, agent):
        ledger_handler._handle_ledger(
            "candidate candidate-reap-at-bank")
        assert "Verify copies are reaped at bank" in (
            _ledger_published_text(ledger_handler))
        ledger_handler._handle_ledger("decisions")
        assert "decision-reap-promoted" in (
            _ledger_published_text(ledger_handler))
        ledger_handler._handle_ledger("standing")
        assert "candidate-reap-at-bank" in (
            _ledger_published_text(ledger_handler))
        ledger_handler._handle_ledger("panel")
        assert "Ledger panel in Self-improving" in (
            _ledger_published_text(ledger_handler))

    def test_bad_grammar_is_published(self, ledger_handler, agent):
        ledger_handler._handle_ledger("dance party")
        assert USAGE in _ledger_published_text(ledger_handler)


class TestChatScreenRoutingSelfImproving:
    def test_ledger_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command(
            "/ledger candidate candidate-reap-at-bank",
            _FakeLog())
        assert calls == [(
            "/ledger", "candidate candidate-reap-at-bank")]
