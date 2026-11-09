"""M-174 Approval Cards Perfected - pure-layer tests.

TIER: integration

The pure layer is the approval card, held as
data: exactly one decision - the operation
verbatim, the target and the consequence each
named as their own line, the full context carried
on the card, and the act itself as a command, its
arguments and its project path, with its
provenance whole (the day it was recorded, who
recorded it, its source and the session it was
recorded in). The remembered scope a card offers
is derived from the card's own act through the
shipped M-096 scope road, the alarm level is
derived from the destructive flag alone, and the
keyboard and mouse paths are read off one held
tuple, exactly equal. A card composed from a
command is judged by the shipped M-111 doctrine,
and a card composed from a shipped M-116 moment
only when its judge reads it complete. The answer
to a card is held as its own decision record, and
the panel and the verdict are derived from the
held cards and their answers. The shipped example
book is held in a data file, and a loader reads a
book from any file. Nothing here runs an
operation, executes an approval, saves a
remembered approval, renders a live UI, sends,
posts, schedules, calls a model or persists
anything: a card held here is a question, never
the act it asks about.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.approval_cards import (
    ALARM_LEVELS,
    ANSWERS,
    ANSWER_WORDS,
    APPROVAL_CARDS_RESOURCE,
    APPROVAL_CARDS_SCHEMA,
    APPROVAL_CARDS_SLICE,
    DECISION_ACTS,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_WORDS,
    AnswerCount,
    ApprovalCard,
    ApprovalCardRegistry,
    ApprovalCardsBook,
    ApprovalPanel,
    ApprovalVerdict,
    CardDecision,
    alarm_of,
    book_record,
    build_book,
    build_card,
    build_decision,
    build_panel,
    build_row,
    build_verdict,
    card_from_command,
    card_from_moment,
    card_record,
    cards_with_alarm,
    decision_plain_words,
    decision_record,
    derive_panel,
    derive_verdict,
    effective_answers,
    format_approval_cards_screen,
    format_book,
    format_card,
    format_decision,
    format_panel,
    format_verdict,
    inspect_operation_source,
    line_of,
    load_approval_cards,
    load_approval_cards_file,
    normalize_alarm,
    normalize_answer,
    panel_plain_words,
    panel_record,
    parse_approval_cards_args,
    paths_of,
    plain_words,
    scope_line_of,
    scope_of,
    total_cards,
    validate_card,
    validate_decision,
    validate_panel,
    validate_row,
    validate_verdict,
    verdict_plain_words,
    verdict_record,
)
from mythic_agent.core.approval_moments import build_moment
from mythic_agent.core.remembered_approvals import (
    scope_fingerprint,
    validate_scope,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Approval Cards at the M-173 slice boundary"

BY = "the coordinator"
HAND = "the jarl"
ON = "2026-11-09"
PROJECT = "/home/volmarr/mythic-hammer"


def _card(**overrides):
    fields = {
        "card_id": "card-test",
        "decision": "Allow the test act",
        "operation": "python -m pytest tests/test_thing.py -q",
        "target": "tests/test_thing.py",
        "consequence": "The tests run; no shipped file changes.",
        "context": ["A test card standing for the tests."],
        "command": "python",
        "args": ["-m", "pytest", "tests/test_thing.py", "-q"],
        "path": PROJECT,
        "destructive": False,
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_card(fields)


def _stored_card(card):
    stored = card.to_record()
    for key in ("type", "slice", "line", "alarm", "scope",
                "scope_id", "scope_line", "keyboard", "mouse"):
        stored.pop(key)
    return stored


def _decision(**overrides):
    fields = {
        "decision_id": "dec-test",
        "seq": 1,
        "card_id": "card-test",
        "answer": "allow",
        "detail": "allowed by hand for the tests.",
        "recorded_on": ON,
        "actor": HAND,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_decision(fields)


def _stored_decision(decision):
    stored = decision.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    return stored


def _book(cards=None, decisions=(), **overrides):
    fields = {
        "title": "A test approval book",
        "cards": [_stored_card(item) for item in (
            cards if cards is not None else [_card()])],
        "decisions": [_stored_decision(item) for item in decisions],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(
        cards=[
            _card(),
            _card(card_id="card-second",
                  decision="Allow the second act"),
            _card(card_id="card-danger",
                  decision="Allow the dangerous act",
                  operation="rm -rf /tmp/scratch-tree",
                  target="/tmp/scratch-tree",
                  consequence="The tree is deleted for good.",
                  command="rm", args=["-rf", "/tmp/scratch-tree"],
                  destructive=True),
        ],
        decisions=[
            _decision(),
            _decision(decision_id="dec-second", seq=2,
                      card_id="card-second", answer="remember",
                      detail="remembered by hand for the tests."),
        ])


# ---------------------------------------------------------------------
# The shipped example book, the roadmap and the charter.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_approval_cards()
    assert book.title == EXAMPLE_TITLE
    assert book.card_ids() == (
        "card-test-run", "card-commit-m174",
        "card-push-roadmap", "card-remove-team99")
    first = book.cards[0]
    assert first.decision == "Allow the slice-board test run"
    assert first.alarm == "calm"
    assert book.decision_ids() == (
        "dec-remember-tests", "dec-allow-commit")
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m173-boundary"
    assert panel.as_of == "2026-11-09"
    assert tuple(row.card_id for row in panel.rows) == book.card_ids()
    derived = derive_panel(book)
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_cards == derived.total_cards == 4
    assert (panel.total_allowed, panel.total_rejected,
            panel.total_remembered, panel.total_awaiting) == (1, 0, 1, 2)
    assert (panel.total_destructive, panel.total_alarmed) == (1, 1)
    assert derive_verdict(book).verdict == "alarmed"
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / APPROVAL_CARDS_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == APPROVAL_CARDS_SCHEMA
    assert raw["slice"] == "M-174"


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-174")]
    assert slice_.title == "Approval cards perfected"
    assert slice_.part == 8
    assert "one decision per card" in slice_.summary
    assert "remembered-scope offered precisely" in slice_.summary
    assert "keyboard" in slice_.summary
    assert APPROVAL_CARDS_SLICE == "M-174"


def test_charter_s04_names_m174():
    charter = load_charter()
    screen = charter.screen("command_approval")
    assert screen.id == "S-04"
    assert screen.verdict == "repair"
    assert "M-174" in screen.owning_slices
    assert screen.judgement("K-03").standing == "fails"
    assert screen.judgement("K-02").standing == "strains"
    assert screen.judgement("L-05").standing == "strains"
    assert "name the target and the consequence" in screen.direction
    assert "remembered approval" in screen.direction
    assert "keyboard and mouse exactly equal" in screen.direction
    assert "destructive operations" in screen.direction


def test_closed_vocabularies():
    assert ANSWERS == ("allow", "reject", "remember")
    assert ANSWER_WORDS == (
        "allow", "reject", "remember", "awaiting")
    assert DECISION_ACTS == ("allow", "reject", "remember")
    assert ALARM_LEVELS == ("calm", "alarm")
    assert VERDICT_WORDS == ("complete", "waiting", "alarmed")
    assert normalize_answer("approve") == "allow"
    assert normalize_answer("deny") == "reject"
    assert normalize_answer("always") == "remember"
    assert normalize_alarm("routine") == "calm"
    assert normalize_alarm("destructive") == "alarm"
    with pytest.raises(ValueError):
        normalize_answer("whenever")
    with pytest.raises(ValueError):
        normalize_alarm("whenever")
    assert "one decision per card" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /approvalcards")


# ---------------------------------------------------------------------
# The card: judged whole, its scope and alarm derived.
# ---------------------------------------------------------------------


def test_card_record_round_trips():
    card = _card()
    assert build_card(_stored_card(card)) == card
    record = card.to_record()
    assert record["line"] == "Allow the test act - calm"
    assert record["type"] == "approval_card"
    assert record["target"] == "tests/test_thing.py"
    assert record["consequence"] == (
        "The tests run; no shipped file changes.")
    assert card.line == line_of(card)
    assert card.alarm == alarm_of(card)


def test_card_provenance_is_whole_and_required():
    card = _card()
    assert card.actor == BY
    assert card.origin_session == "session-test"
    for missing in ("card_id", "decision", "operation", "target",
                    "consequence", "context", "command", "args",
                    "path", "destructive", "recorded_on", "actor",
                    "source", "origin_session"):
        fields = _stored_card(card)
        fields.pop(missing)
        with pytest.raises(ValueError):
            build_card(fields)
    with pytest.raises(ValueError):
        _card(context=[])


def test_card_refuses_unknown_keys_split_spellings_and_derived_keys():
    for derived_key, value in (
            ("line", "Allow the test act - calm"),
            ("alarm", "calm"),
            ("scope", {"command": "python"}),
            ("keyboard", ["allow"]),
            ("mouse", ["allow"]),
            ("decisions", ["one", "two"])):
        fields = _stored_card(_card())
        fields[derived_key] = value
        with pytest.raises(ValueError):
            build_card(fields)
    fields = _stored_card(_card())
    fields["question"] = "A second, different question"
    with pytest.raises(ValueError):
        build_card(fields)
    fields = _stored_card(_card())
    fields["surprise"] = "x"
    with pytest.raises(ValueError):
        build_card(fields)
    with pytest.raises(ValueError):
        _card(command="py thon")
    with pytest.raises(ValueError):
        _card(command="py*thon")


def test_card_alias_spellings_read_onto_the_fields():
    card = build_card({
        "id": "card-alias", "question": "Allow the alias act",
        "command_text": "git status",
        "target": "the working tree",
        "effect": "The tree's standing is shown.",
        "context": ["An alias-spelled card for the tests."],
        "command": "git", "arguments": ["status"],
        "project": PROJECT, "destructive": False,
        "day": ON, "by": BY, "source": "alias source",
        "session": "session-alias"})
    assert card.decision == "Allow the alias act"
    assert card.operation == "git status"
    assert card.consequence == "The tree's standing is shown."
    assert card.args == ("status",)
    assert card.path == PROJECT


def test_line_and_alarm_are_derived():
    assert line_of(_card()) == "Allow the test act - calm"
    assert alarm_of(_card()) == "calm"
    dangerous = _card(destructive=True)
    assert alarm_of(dangerous) == "alarm"
    assert line_of(dangerous) == "Allow the test act - alarm"
    assert normalize_alarm(alarm_of(dangerous)) == "alarm"


def test_scope_is_derived_exactly_from_the_act():
    card = _card()
    scope = scope_of(card)
    shipped = validate_scope({
        "command": "python",
        "args_pattern": ["-m", "pytest", "tests/test_thing.py", "-q"],
        "path": PROJECT})
    assert scope == shipped
    record = card.to_record()
    assert record["scope_id"] == scope_fingerprint(shipped)
    assert record["scope_line"] == (
        "always allow python -m pytest tests/test_thing.py -q "
        f"in {PROJECT}")
    assert scope_line_of(card) == record["scope_line"]
    bare = _card(command="pwd", args=[], operation="pwd")
    assert scope_line_of(bare) == f"always allow pwd in {PROJECT}"


def test_keyboard_and_mouse_paths_are_exactly_equal():
    for card in (_card(), _card(destructive=True)):
        paths = paths_of(card)
        assert paths["keyboard"] == paths["mouse"]
        assert paths["keyboard"] == DECISION_ACTS == ANSWERS
        record = card.to_record()
        assert record["keyboard"] == record["mouse"]


# ---------------------------------------------------------------------
# Composition: the doctrine and the moment, by import.
# ---------------------------------------------------------------------


def test_card_from_command_judges_the_doctrine():
    danger = card_from_command(
        "rm -rf /tmp/scratch-tree",
        card_id="card-rm", decision="Allow removing the tree",
        consequence="The tree is deleted for good.",
        context=["A composed card for the tests."], path=PROJECT)
    assert danger.destructive is True
    assert danger.alarm == "alarm"
    assert danger.target == "/tmp/scratch-tree"
    assert danger.command == "rm"
    assert danger.args == ("-rf", "/tmp/scratch-tree")
    costly = card_from_command(
        "git push origin HEAD",
        card_id="card-push", decision="Allow the push",
        target="origin HEAD",
        consequence="The branch leaves this machine.",
        context=["A composed card for the tests."], path=PROJECT)
    assert costly.destructive is False
    assert costly.alarm == "calm"
    with pytest.raises(ValueError):
        card_from_command(
            "rm -rf /tmp/scratch-tree",
            card_id="card-rm2", decision="Allow removing the tree",
            consequence="The tree is deleted for good.",
            context=["A composed card for the tests."],
            path=PROJECT, destructive=False)
    with pytest.raises(ValueError):
        card_from_command(
            "pwd",
            card_id="card-pwd", decision="Allow printing the path",
            consequence="The path is printed.",
            context=["A composed card for the tests."], path=PROJECT)


def test_card_from_moment_requires_a_complete_moment():
    moment = build_moment(
        what="Allow the test run?",
        where="tests/test_thing.py",
        what_it_does="Runs the thing tests.",
        choices=[
            {"key": "approve", "label": "Allow",
             "effect": "The tests run."},
            {"key": "deny", "label": "Reject",
             "effect": "Nothing runs."}])
    card = card_from_moment(
        moment, card_id="card-moment", command="python",
        args=("-m", "pytest"), path=PROJECT)
    assert card.decision == "Allow the test run?"
    assert card.target == "tests/test_thing.py"
    assert card.consequence == "Runs the thing tests."
    assert card.operation == "python -m pytest"
    incomplete = build_moment(
        what="Allow the test run?", where="",
        what_it_does="Runs the thing tests.",
        choices=[
            {"key": "approve", "label": "Allow",
             "effect": "The tests run."}])
    with pytest.raises(ValueError):
        card_from_moment(
            incomplete, card_id="card-bad", command="python",
            path=PROJECT)


def test_inspect_operation_source_names_what_a_piece_is():
    found = inspect_operation_source(
        {"operation": "rm -rf /tmp/scratch-tree"})
    assert found["alarm"] == "alarm"
    assert found["destructive"] is True
    assert found["rung"] == "irreversible"
    calm = inspect_operation_source({"operation": "pwd"})
    assert calm["alarm"] == "calm"
    assert inspect_operation_source({"words": "x"})["alarm"] is None
    assert inspect_operation_source("nope")["alarm"] is None


# ---------------------------------------------------------------------
# The decision record: one answer, judged whole, standing once.
# ---------------------------------------------------------------------


def test_decision_is_judged_whole():
    decision = _decision(answer="approve")
    assert decision.answer == "allow"
    assert build_decision(_stored_decision(_decision())) == _decision()
    with pytest.raises(ValueError):
        _decision(answer="whenever")
    fields = _stored_decision(_decision())
    fields["scope"] = {"command": "python"}
    with pytest.raises(ValueError):
        build_decision(fields)
    fields = _stored_decision(_decision())
    fields.pop("detail")
    with pytest.raises(ValueError):
        build_decision(fields)


def test_effective_answers_answer_a_card_once():
    cards = [_card(), _card(card_id="card-second",
                            decision="Allow the second act")]
    answers = effective_answers(cards, [_decision()])
    assert answers["card-test"].answer == "allow"
    assert "card-second" not in answers
    with pytest.raises(ValueError):
        effective_answers(cards, [
            _decision(),
            _decision(decision_id="dec-two", seq=2, answer="reject")])
    with pytest.raises(ValueError):
        effective_answers(cards, [
            _decision(card_id="card-ghost")])
    with pytest.raises(ValueError):
        _book(decisions=[
            _decision(),
            _decision(decision_id="dec-two", seq=2, answer="reject")])


# ---------------------------------------------------------------------
# The panel and the verdict: derived, never chosen.
# ---------------------------------------------------------------------


def test_panel_is_derived_from_the_whole_book():
    book = _mixed_book()
    panel = derive_panel(book)
    assert panel.total_cards == 3
    assert (panel.total_allowed, panel.total_rejected,
            panel.total_remembered, panel.total_awaiting) == (1, 0, 1, 1)
    assert (panel.total_destructive, panel.total_alarmed) == (1, 1)
    assert [row.card_id for row in panel.rows] == [
        "card-test", "card-second", "card-danger"]
    assert panel.rows[0].answer == "allow"
    assert panel.rows[1].answer == "remember"
    assert panel.rows[2].answer == "awaiting"
    assert panel.rows[2].alarm == "alarm"
    assert panel.rows[2].line == "Allow the dangerous act - alarm"
    assert {c.answer: c.items for c in panel.answer_counts} == {
        "allow": 1, "remember": 1, "awaiting": 1}
    assert AnswerCount(answer="allow", items=1).to_record() == {
        "answer": "allow", "items": 1}


def test_panel_refuses_a_stored_panel_that_disagrees():
    book = _mixed_book()
    stored = derive_panel(book).to_record()
    stored.pop("type")
    stored.pop("slice")
    stored["total_awaiting"] = 3
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    stored = derive_panel(book).to_record()
    stored.pop("type")
    stored.pop("slice")
    stored["rows"][0]["alarm"] = "alarm"
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    panel = build_panel(derive_panel(book).to_record(), book)
    assert panel.total_cards == 3


def test_row_is_judged_against_its_card():
    card = _card()
    row = build_row(card=card)
    assert row.line == "Allow the test act - calm"
    assert row.answer == "awaiting"
    assert validate_row(row.to_record(), card) == row
    answered = build_row(card=card, decision=_decision())
    assert answered.answer == "allow"
    bad = row.to_record()
    bad["line"] = "a chosen line"
    with pytest.raises(ValueError):
        validate_row(bad, card)
    bad = row.to_record()
    bad["alarm"] = "alarm"
    with pytest.raises(ValueError):
        validate_row(bad, card)


def test_verdict_bands_and_the_alarmed_example():
    book = load_approval_cards()
    verdict = derive_verdict(book)
    assert verdict.verdict == "alarmed"
    assert verdict.total_alarmed == 1
    done = _book(decisions=[_decision()])
    assert derive_verdict(done).verdict == "complete"
    waiting = _book()
    assert derive_verdict(waiting).verdict == "waiting"
    mixed = derive_verdict(_mixed_book())
    assert mixed.verdict == "alarmed"
    assert build_verdict(mixed.to_record(), _mixed_book()) == mixed
    with pytest.raises(ValueError):
        ApprovalVerdict(
            total_cards=1, total_destructive=0, total_alarmed=0,
            total_allowed=1, total_rejected=0, total_remembered=0,
            total_awaiting=0, earliest_on=ON, latest_on=ON,
            verdict="waiting")
    with pytest.raises(ValueError):
        validate_verdict(mixed.to_record(), _book())


# ---------------------------------------------------------------------
# The book, the file loader and the registry.
# ---------------------------------------------------------------------


def test_book_laws_one_card_per_id_and_decisions_in_order():
    with pytest.raises(ValueError):
        _book(cards=[_card(), _card(decision="Another question")])
    with pytest.raises(ValueError):
        _book(decisions=[
            _decision(), _decision(decision_id="dec-two")])
    with pytest.raises(ValueError):
        _book(decisions=[
            _decision(),
            _decision(seq=2, card_id="card-test", answer="reject")])
    book = _mixed_book()
    assert book.card_for("card-second").decision == (
        "Allow the second act")
    assert book.decision_for("dec-second").answer == "remember"
    assert book.answer_for("card-test").answer == "allow"
    assert book.answer_for("card-danger") is None
    with pytest.raises(KeyError):
        book.card_for("card-nope")
    with pytest.raises(KeyError):
        book.decision_for("dec-nope")
    assert total_cards(book) == 3
    assert [c.card_id for c in cards_with_alarm(book, "alarm")] == [
        "card-danger"]
    assert [c.card_id for c in cards_with_alarm(
        book, "destructive")] == ["card-danger"]


def test_book_file_loader_reads_any_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "approval_cards.yaml").read_text(encoding="utf-8")
    path = tmp_path / "approval_cards.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_approval_cards_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_cards(book) == 4


def test_registry_holds_cards_and_decisions_one_by_one():
    registry = ApprovalCardRegistry()
    registry.register_card(_card())
    registry.register_card(_card(
        card_id="card-second", decision="Allow the second act"))
    held = registry.register_decision(_decision(decision_id=None))
    assert held.decision_id == "dec-1"
    assert registry.answer_for("card-test").answer == "allow"
    assert registry.answer_for("card-second") is None
    assert registry.latest_decision().decision_id == "dec-1"
    assert registry.book().title == "Approval Cards"
    assert registry.panel().total_cards == 2
    assert registry.verdict().verdict == "waiting"
    with pytest.raises(ValueError):
        registry.register_card(_card(decision="Another question"))
    with pytest.raises(ValueError):
        registry.register_decision(_decision(
            decision_id="dec-two", seq=2))
    with pytest.raises(ValueError):
        registry.register_decision(_decision(
            decision_id="dec-ghost", seq=2, card_id="card-ghost"))
    assert [d.decision_id for d in registry.list_decisions()] == ["dec-1"]
    with pytest.raises(KeyError):
        registry.get_card("card-nope")


def test_registry_register_book_and_refusals():
    registry = ApprovalCardRegistry()
    book = registry.register_book(_mixed_book())
    assert total_cards(book) == 3
    assert registry.title() == "A test approval book"
    with pytest.raises(ValueError):
        registry.register_book(_book())
    other = ApprovalCardRegistry(_book())
    assert other.get_card("card-test").card_id == "card-test"
    assert isinstance(other.book(), ApprovalCardsBook)
    assert isinstance(other.panel(), ApprovalPanel)
    assert isinstance(other.verdict(), ApprovalVerdict)
    assert isinstance(_card(), ApprovalCard)
    assert isinstance(_decision(), CardDecision)


# ---------------------------------------------------------------------
# News, plain words, formatters and the grammar.
# ---------------------------------------------------------------------


def test_news_records_carry_headlines():
    card = _card()
    news = card_record(card)
    assert news["news"] is True
    assert news["type"] == "approval_card"
    assert "Allow the test act - calm" in news["headline"]
    assert "target: tests/test_thing.py" in news["headline"]
    decision_news = decision_record(_decision())
    assert decision_news["type"] == "approval_card_decision"
    assert "allow" in decision_news["headline"]
    panel_news = panel_record(derive_panel(_mixed_book()))
    assert "Approval cards panel" in panel_news["headline"]
    verdict_news = verdict_record(derive_verdict(_mixed_book()))
    assert "alarmed" in verdict_news["headline"]
    book_news = book_record(_mixed_book())
    assert book_news["card_count"] == 3
    assert book_news["decision_count"] == 2


def test_formatters_and_screen():
    book = load_approval_cards()
    text = format_card(book.card_for("card-remove-team99"))
    assert "Target: /home/volmarr/mythic-hammer/team-99" in text
    assert "Consequence: The worktree and everything in it" in text
    assert "Remembered scope: always allow rm -rf" in text
    assert "Keyboard: allow/reject/remember" in text
    assert "Mouse: allow/reject/remember (exactly equal)" in text
    assert "Alarm: alarm" in text
    decision_text = format_decision(book.decision_for("dec-allow-commit"))
    assert "dec-allow-commit: allow card-commit-m174" in decision_text
    listed = format_book(book)
    assert "card-test-run: Allow the slice-board test run - calm" in listed
    alarmed = format_book(book, alarm="alarm")
    assert "card-remove-team99" in alarmed
    assert "card-test-run" not in alarmed
    assert "Panel in Approval Cards at the M-173 slice boundary" in (
        format_panel(book))
    assert format_verdict(book).startswith(
        "Verdict in Approval Cards over")
    assert "alarmed" in format_verdict(book)
    screen = format_approval_cards_screen()
    assert "Approval Cards (M-174)" in screen
    assert "1 stand alarmed" in screen
    assert "stands alarmed" in plain_words(
        book.card_for("card-remove-team99"))
    assert "card's own" in decision_plain_words(
        book.decision_for("dec-remember-tests"))
    assert "Cards, in held order" in panel_plain_words(book)
    assert "alarmed" in verdict_plain_words(book)


def test_parse_approval_cards_args_grammar():
    assert parse_approval_cards_args("") == ("show", None)
    assert parse_approval_cards_args(None) == ("show", None)
    assert parse_approval_cards_args("show") == ("show", None)
    assert parse_approval_cards_args("list") == ("show", None)
    assert parse_approval_cards_args("card card-test-run") == (
        "card", "card-test-run")
    assert parse_approval_cards_args("decision dec-allow-commit") == (
        "decision", "dec-allow-commit")
    assert parse_approval_cards_args("panel") == ("panel", None)
    assert parse_approval_cards_args("verdict") == ("verdict", None)
    for bad in ("card", "decision", "panel now", "dance", 42):
        with pytest.raises(ValueError):
            parse_approval_cards_args(bad)


def test_pure_layer_imports_no_agent_or_ui():
    text = (ROOT / "mythic_agent" / "core"
            / "approval_cards.py").read_text(encoding="utf-8")
    assert "mythic_agent.agents" not in text
    assert "import textual" not in text
    assert "from ..agents" not in text


# -- agent layer -----------------------------------------------------------
#
# M-174 agent layer: the agent holds an
# ApprovalCardRegistry for the session (session
# state only, no new setting), cards and decision
# records are held by being registered - each
# judged whole, and each decision judged against
# the held cards, before it is held - published
# as their card_record / decision_record session
# news through the checkpoint road, deduped per
# shape - a card composed from a command by import
# takes its destructive standing from the shipped
# doctrine's ladder, and a card composed from a
# shipped moment by import only from a moment its
# judge reads complete, the deciding road composes
# one decision record at the held book's next
# sequence and publishes the derived panel and
# verdict news with it, whole-book register and
# record roads hold a book judged whole first, the
# report road renders the held book (or the
# shipped example when unheld) through the pure
# formatters, and the /approvalcards surface rides
# both roads on the pure parser + formatters.
# Status, get, alarm, panel, verdict and report
# reads register and publish nothing, answer from
# the held registry first and from the shipped
# example only while nothing is held - a held card
# never falls back to the example. The panel and
# the verdict derive at call time from the whole
# book, never held. This layer sends nothing,
# posts nothing, schedules nothing, calls no model,
# persists nothing beyond the session journal news,
# executes no approval, saves no remembered
# approval and renders no live UI - a card held
# here is a question, never the act it asks about,
# and a remember answer names only the card's own
# derived scope, which the shipped M-096 road
# alone may hold.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _card_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "approval_cards.yaml").read_text(encoding="utf-8")
    path = tmp_path / "approval_cards.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestApprovalCardsAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.approval_cards_status()
        assert status["cards"] == []
        assert status["decisions"] == []
        assert status["book"] is None
        assert status["approval_cards"]["title"] == EXAMPLE_TITLE
        assert len(status["approval_cards"]["cards"]) == 4
        assert len(status["approval_cards"]["decisions"]) == 2
        assert status["panel"]["total_cards"] == 4
        assert status["panel"]["total_alarmed"] == 1
        assert status["panels"][0]["panel_id"] == "panel-m173-boundary"
        assert status["book_record"]["card_count"] == 4
        assert status["book_record"]["decision_count"] == 2
        assert status["verdict"]["verdict"] == "alarmed"
        assert "Allow removing the team-99 worktree - alarm" in (
            status["plain_words"])
        assert "stands alarmed" in status["plain_words"]
        assert "Approval Cards (M-174)" in status["screen"]
        assert "1 stand alarmed" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._approval_cards_registry()
        assert agent._approval_cards_registry() is first
        assert agent._approval_cards_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.approval_cards_status()
        assert agent.get_approval_card(
            "card-remove-team99").alarm == "alarm"
        assert agent.get_approval_decision(
            "dec-allow-commit").answer == "allow"
        assert [c.card_id for c in agent.approval_cards_with_alarm(
            "alarm")] == ["card-remove-team99"]
        assert [c.card_id for c in agent.approval_cards_with_alarm(
            "calm")] == [
                "card-test-run", "card-commit-m174", "card-push-roadmap"]
        agent.approval_cards_panel()
        agent.approval_cards_verdict()
        agent.report_approval_cards()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("approval_card")] == []
        with pytest.raises(KeyError):
            agent.get_approval_card("card-nope")
        with pytest.raises(KeyError):
            agent.get_approval_decision("dec-nope")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_approval_card(_card())
        status = agent.approval_cards_status()
        assert [item["card_id"] for item in status["cards"]] == [
            "card-test"]
        assert status["book"]["title"] == "Approval Cards"
        assert status["panel"]["total_cards"] == 1
        assert status["panel"]["total_awaiting"] == 1
        assert status["verdict"]["verdict"] == "waiting"

    def test_held_card_never_falls_back_to_the_example(
            self, agent):
        agent.register_approval_card(_card())
        with pytest.raises(KeyError):
            agent.get_approval_card("card-test-run")
        with pytest.raises(KeyError):
            agent.get_approval_decision("dec-allow-commit")
        card = agent.get_approval_card("card-test")
        assert card.decision == "Allow the test act"
        assert agent.approval_cards_book().title == "Approval Cards"


class TestApprovalCardsAgentHolding:
    def test_register_card_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_approval_card(_card())
        assert outcome["card"]["card_id"] == "card-test"
        assert outcome["record_news"]["news"] is True
        assert outcome["record_news"]["type"] == "approval_card"
        assert "card-test" in outcome["screen"]
        agent.register_approval_card(_card(
            card_id="card-second", decision="Allow the second act"))
        events = _card_events(store, session_id, "approval_card")
        assert len(events) == 2
        agent._publish_approval_card_record(card_record(_card()))
        agent._publish_approval_card_record(
            {"type": "slice_board_card", "news": True})
        events = _card_events(store, session_id, "approval_card")
        assert len(events) == 2
        agent.close()

    def test_duplicate_card_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_approval_card(_card())
        with pytest.raises(ValueError):
            agent.register_approval_card(_card())
        with pytest.raises(ValueError):
            agent.register_approval_card(
                _card(decision="Another question"))
        events = _card_events(store, session_id, "approval_card")
        assert len(events) == 1
        agent.close()

    def test_composed_cards_hold_by_import(self, agent):
        danger = card_from_command(
            "rm -rf /tmp/scratch-tree",
            card_id="card-rm", decision="Allow removing the tree",
            consequence="The tree is deleted for good.",
            context=["A composed card for the tests."], path=PROJECT)
        assert danger.destructive is True
        outcome = agent.register_approval_card(danger)
        assert outcome["card"]["alarm"] == "alarm"
        moment = build_moment(
            what="Allow the test run?", where="tests/test_thing.py",
            what_it_does="Runs the thing tests.",
            choices=[
                {"key": "approve", "label": "Allow",
                 "effect": "The tests run."},
                {"key": "deny", "label": "Reject",
                 "effect": "Nothing runs."}])
        composed = card_from_moment(
            moment, card_id="card-moment", command="python",
            args=("-m", "pytest"), path=PROJECT)
        agent.register_approval_card(composed)
        assert [c.card_id for c in agent.approval_cards_with_alarm(
            "alarm")] == ["card-rm"]
        assert agent.get_approval_card(
            "card-moment").target == "tests/test_thing.py"

    def test_register_decision_is_judged_against_its_cards(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_approval_card(_card())
        agent.register_approval_card(_card(
            card_id="card-second", decision="Allow the second act"))
        outcome = agent.register_approval_decision(_decision())
        assert outcome["decision"]["decision_id"] == "dec-test"
        assert outcome["record_news"]["type"] == (
            "approval_card_decision")
        assert agent.approval_cards_book().answer_for(
            "card-test").answer == "allow"
        with pytest.raises(ValueError):
            agent.register_approval_decision(_decision(
                decision_id="dec-two", seq=2, answer="reject"))
        with pytest.raises(ValueError):
            agent.register_approval_decision(_decision(
                decision_id="dec-ghost", seq=2, card_id="card-ghost"))
        assert [d.decision_id for d in
                agent._approval_cards_registry().list_decisions()] == [
                    "dec-test"]
        events = _card_events(
            store, session_id, "approval_card_decision")
        assert len(events) == 1
        agent.close()

    def test_decide_road_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_approval_card(_card())
        agent.register_approval_card(_card(
            card_id="card-second", decision="Allow the second act"))
        outcome = agent.decide_approval_card(
            "allow", card_id="card-test",
            detail="allowed by hand for the tests.")
        assert outcome["answer"] == "allow"
        assert outcome["decision"]["seq"] == 1
        assert outcome["decision"]["decision_id"] == "dec-1"
        assert outcome["record_news"]["type"] == (
            "approval_card_decision")
        assert outcome["panel_record"]["type"] == (
            "approval_cards_panel")
        assert outcome["verdict_record"]["type"] == (
            "approval_cards_verdict")
        second = agent.decide_approval_card(
            "remember", card_id="card-second",
            detail="remembered by hand for the tests.")
        assert second["decision"]["seq"] == 2
        assert agent.approval_cards_verdict().verdict == "complete"
        assert len(_card_events(
            store, session_id, "approval_card_decision")) == 2
        assert len(_card_events(
            store, session_id, "approval_cards_panel")) == 1
        assert len(_card_events(
            store, session_id, "approval_cards_verdict")) == 2
        agent.close()

    def test_decide_road_refuses_a_second_answer(self, agent):
        agent.register_approval_card(_card())
        agent.decide_approval_card(
            "reject", card_id="card-test",
            detail="rejected by hand for the tests.")
        with pytest.raises(ValueError):
            agent.decide_approval_card(
                "allow", card_id="card-test",
                detail="a card is answered once.")
        with pytest.raises(ValueError):
            agent.decide_approval_card(
                "allow", card_id="card-ghost",
                detail="no such card stands held.")
        assert [d.answer for d in
                agent._approval_cards_registry().list_decisions()] == [
                    "reject"]
        assert agent.approval_cards_verdict().verdict == "complete"

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_approval_cards_book(_mixed_book())
        assert outcome["count"] == 3
        assert [c["card_id"] for c in outcome["cards"]] == [
            "card-test", "card-second", "card-danger"]
        assert [r["type"] for r in outcome["records_news"]] == [
            "approval_card", "approval_card",
            "approval_card", "approval_card_decision",
            "approval_card_decision"]
        events = _card_events(store, session_id, "approval_card")
        assert [e["card_id"] for e in events] == [
            "card-test", "card-second", "card-danger"]
        assert len(_card_events(
            store, session_id, "approval_cards_panel")) == 1
        assert agent.approval_cards_book().title == (
            "A test approval book")
        with pytest.raises(ValueError):
            agent.register_approval_cards_book(_mixed_book())
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_approval_cards_book()
        assert outcome["count"] == 4
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_card_events(
            store, session_id, "approval_card")) == 4
        assert len(_card_events(
            store, session_id, "approval_card_decision")) == 2
        status = agent.approval_cards_status()
        assert status["panels"][0]["panel_id"] == "panel-m173-boundary"
        with pytest.raises(ValueError):
            agent.record_approval_cards_book()
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_book_file(tmp_path)
        book = load_approval_cards_file(path)
        outcome = agent.record_approval_cards_book(book)
        assert outcome["count"] == 4
        assert agent.approval_cards_book().title == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_approval_cards()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert len(report["cards"]) == 4
        assert report["verdict"]["verdict"] == "alarmed"
        assert "card-remove-team99: Allow removing" in (
            report["book_text"])
        agent.register_approval_card(_card())
        report = agent.report_approval_cards()
        assert [c["card_id"] for c in report["cards"]] == ["card-test"]
        assert "card-test: Allow the test act - calm" in (
            report["book_text"])
        assert report["verdict"]["verdict"] == "waiting"

    def test_holding_and_deciding_execute_nothing(self, agent):
        from mythic_agent.core.remembered_approvals import (
            stored_approvals)
        for name in (
                "run_approval_card", "execute_approval_card",
                "execute_approval", "save_remembered_approval",
                "remember_approval_card", "bank_approval_cards",
                "persist_approval_cards", "send_approval_cards",
                "schedule_approval_cards", "render_approval_card_ui",
                "delete_approval_card"):
            assert not hasattr(agent, name), name
        agent.register_approval_card(_card())
        agent.decide_approval_card(
            "remember", card_id="card-test",
            detail="remembered by hand for the tests.")
        assert agent.approval_cards_book().answer_for(
            "card-test").answer == "remember"
        # The remember answer is held as data on this
        # layer's book alone: the shipped M-096
        # remembered-approvals setting stays empty.
        assert stored_approvals(agent.config) == []
        assert agent.config.get("remembered_approvals") is None


class TestApprovalCardsTerminalSurface:
    def test_show_card_decision_panel_verdict(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/approvalcards")
        assert "Approval Cards (M-174)" in text
        _, _, text = _slash(agent, "/approvalcards card card-remove-team99")
        assert "Target: /home/volmarr/mythic-hammer/team-99" in text
        assert "Alarm: alarm" in text
        _, _, text = _slash(agent, "/approvalcards card card-test-run")
        assert "Remembered scope: always allow python" in text
        assert "Keyboard: allow/reject/remember" in text
        _, _, text = _slash(
            agent, "/approvalcards decision dec-allow-commit")
        assert "allow card-commit-m174" in text
        _, _, text = _slash(agent, "/approvalcards panel")
        assert "Panel in Approval Cards at the M-173 slice boundary" in (
            text)
        _, _, text = _slash(agent, "/approvalcards verdict")
        assert "alarmed" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/approvalcards [show|card <card-id>"
                "|decision <decision-id>|panel|verdict]") in text
        _, _, text = _slash(agent, "/approvalcards dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/approvalcards card card-nope")
        assert "no card named" in text


@pytest.fixture()
def cards_handler(agent, monkeypatch):
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


def _cards_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestApprovalCardsCommand:
    def test_show_is_default(self, cards_handler, agent):
        cards_handler._handle_approvalcards("")
        assert "Approval Cards (M-174)" in (
            _cards_published_text(cards_handler))

    def test_card_decision_panel_verdict(
            self, cards_handler, agent):
        cards_handler._handle_approvalcards("card card-remove-team99")
        assert "Target: /home/volmarr/mythic-hammer/team-99" in (
            _cards_published_text(cards_handler))
        cards_handler._handle_approvalcards("decision dec-remember-tests")
        assert "remember card-test-run" in (
            _cards_published_text(cards_handler))
        cards_handler._handle_approvalcards("panel")
        assert "Panel in Approval Cards" in (
            _cards_published_text(cards_handler))
        cards_handler._handle_approvalcards("verdict")
        assert "alarmed" in _cards_published_text(cards_handler)

    def test_bad_grammar_is_published(
            self, cards_handler, agent):
        cards_handler._handle_approvalcards("dance party")
        assert USAGE in _cards_published_text(cards_handler)
        cards_handler._handle_approvalcards("card card-nope")
        assert "no card named" in _cards_published_text(
            cards_handler)


class TestChatScreenRoutingApprovalCards:
    def test_approvalcards_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/approvalcards panel", _FakeLog())
        assert calls == [("/approvalcards", "panel")]

    def test_chat_screen_help_and_usage_name_the_cards(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/approvalcards[/green] - show approval cards perfected (M-174)" in (
            text)
        assert ('"/approvalcards": "Usage: /approvalcards | '
                '/approvalcards card <card-id>') in text
