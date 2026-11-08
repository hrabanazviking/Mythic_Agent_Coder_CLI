"""M-132 Review panels - pure-layer tests.

TIER: integration

The pure layer is the review panel as data: one
change put to two reviewers riding different
models (a change - the change under review, named
and summarised; a review - one reviewer's
verdict, the provider and model they rode, their
notes and the concerns they name), the shipped
example panel held in a data file, a loader that
reads a panel from any file, the outcome derived
mechanically from the two verdicts alone - agreed
when they match, a disagreement naming both
positions when they differ, awaiting while fewer
than two reviews are held - an outcome record
shaped as session news, and a registry. Nothing
here runs a review, calls a model, executes a
change, spawns a crew or claims a Part VIII
board: the panel is data only, and the reviews
arrive through later roads.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.crew_members import load_casting
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.review_panels import (
    OUTCOME_KINDS,
    PANEL_RESOURCE,
    PANEL_SCHEMA,
    PANEL_SLICE,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_KINDS,
    PanelChange,
    PanelOutcome,
    PanelReview,
    ReviewPanel,
    ReviewPanelRegistry,
    build_change,
    build_outcome,
    build_review,
    change_record,
    format_outcome,
    format_panel_screen,
    format_review,
    format_reviews,
    format_verdict_kinds,
    load_review_panel,
    load_review_panel_file,
    normalize_model,
    normalize_outcome,
    normalize_provider,
    normalize_verdict,
    outcome_of_panel,
    outcome_plain_words,
    outcome_record,
    parse_panel_args,
    plain_words,
    review_record,
    validate_change,
    validate_outcome,
    validate_panel,
    validate_review,
)

ROOT = Path(__file__).resolve().parents[1]


def _change(**kwargs):
    kwargs.setdefault("title", "A later change")
    kwargs.setdefault("summary", "It changes one road honestly.")
    return PanelChange(**kwargs)


def _review(**kwargs):
    kwargs.setdefault("reviewer", "auditor")
    kwargs.setdefault("provider", "anthropic")
    kwargs.setdefault("model", "claude-sonnet-4-5")
    kwargs.setdefault("verdict", "approve")
    kwargs.setdefault("notes", "It reads clean.")
    return PanelReview(**kwargs)


def _panel_data():
    return {
        "schema": PANEL_SCHEMA, "slice": PANEL_SLICE,
        "change": {"title": "A later change",
                   "summary": "It changes one road honestly."},
        "reviews": [
            {"reviewer": "auditor", "provider": "anthropic",
             "model": "claude-sonnet-4-5", "verdict": "approve",
             "notes": "It reads clean."},
        ]}


def _write_panel(tmp_path, data):
    path = tmp_path / "panel.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


# ---------------------------------------------------------------------
# Constants, the shipped example, and its reviewers.
# ---------------------------------------------------------------------


def test_constants_and_usage():
    assert PANEL_SLICE == "M-132"
    assert PANEL_RESOURCE == "review_panels.yaml"
    assert PANEL_SCHEMA == "mythic.review_panels/1"
    assert VERDICT_KINDS == ("approve", "request_changes", "reject")
    assert OUTCOME_KINDS == ("agreed", "disagreement", "awaiting")
    assert USAGE.startswith("Usage: /panel")
    assert "surfaced, not averaged away" in PLAIN_EXPLANATION
    assert "board" in PLAIN_EXPLANATION


def test_shipped_example_panel_shape():
    panel = load_review_panel()
    assert panel.change.title == "Session-branching restore guard"
    assert [r.reviewer for r in panel.reviews] == [
        "auditor", "guardian"]
    assert [r.model for r in panel.reviews] == [
        "claude-sonnet-4-5", "llama3.1"]
    assert [r.verdict for r in panel.reviews] == [
        "approve", "request_changes"]
    assert panel.is_complete()
    assert panel.disagrees()


def test_example_reviewers_are_the_shipped_casting():
    casting = load_casting()
    ids = [member.member_id for member in casting.members]
    for review in load_review_panel().reviews:
        assert review.reviewer in ids


def test_example_outcome_is_a_surfaced_disagreement():
    outcome = outcome_of_panel(load_review_panel())
    assert outcome.outcome == "disagreement"
    assert outcome.complete is True
    assert outcome.verdict == ""
    assert outcome.reviewers == ("auditor", "guardian")
    assert outcome.verdicts == ("approve", "request_changes")
    words = outcome_plain_words(outcome)
    assert "auditor holds approve" in words
    assert "guardian holds request_changes" in words
    assert "surfaced, not averaged" in words


# ---------------------------------------------------------------------
# Normalizers and piece validation.
# ---------------------------------------------------------------------


def test_normalize_verdict_readings_and_refusals():
    assert normalize_verdict("Approved") == "approve"
    assert normalize_verdict("pass") == "approve"
    assert normalize_verdict("request-changes") == "request_changes"
    assert normalize_verdict("block") == "request_changes"
    assert normalize_verdict("veto") == "reject"
    with pytest.raises(ValueError):
        normalize_verdict("shrug")
    with pytest.raises(ValueError):
        normalize_verdict("")


def test_normalize_outcome_and_roads():
    assert normalize_outcome("Consensus") == "agreed"
    assert normalize_outcome("dispute") == "disagreement"
    assert normalize_outcome("pending") == "awaiting"
    assert normalize_provider("Anthropic") == "anthropic"
    assert normalize_model("llama3.1") == "llama3.1"
    with pytest.raises(ValueError):
        normalize_outcome("split")
    with pytest.raises(ValueError):
        normalize_model("two words")


def test_change_validation_and_two_spellings_refusal():
    change = validate_change(
        {"name": "Words", "description": "It does a thing."})
    assert change.title == "Words"
    assert change.summary == "It does a thing."
    with pytest.raises(ValueError):
        validate_change({"title": "One", "name": "Two",
                         "summary": "It does a thing."})
    with pytest.raises(ValueError):
        validate_change({"title": "Words", "summary": "Sum.",
                         "bogus": 1})
    with pytest.raises(ValueError):
        validate_change({"summary": "No title."})
    assert build_change(title="Built", summary="Sum.").title == "Built"
    assert plain_words(_change()).startswith("Change under review:")


def test_review_validation_and_concern_rules():
    review = validate_review(
        {"member_id": "guardian", "provider": "ollama",
         "model": "llama3.1", "decision": "changes",
         "note": "Grow it first.", "concern": "no road back"})
    assert review.reviewer == "guardian"
    assert review.verdict == "request_changes"
    assert review.concerns == ("no road back",)
    assert build_review(reviewer="scribe", provider="openai",
                        model="gpt-5", verdict="reject",
                        notes="No.").reviewer == "scribe"
    with pytest.raises(ValueError):
        _review(concerns=["same", "same"])
    with pytest.raises(ValueError):
        validate_review({"reviewer": "scribe", "provider": "openai",
                         "model": "gpt-5", "verdict": "approve",
                         "notes": "Fine.", "note": "Other."})
    with pytest.raises(ValueError):
        validate_review({"reviewer": "scribe", "provider": "openai",
                         "model": "gpt-5", "verdict": "meh",
                         "notes": "Fine."})


# ---------------------------------------------------------------------
# Whole-panel validation and the outcome judge.
# ---------------------------------------------------------------------


def test_panel_validation_and_awaiting_outcome():
    panel = validate_panel(_panel_data())
    assert not panel.is_complete()
    assert not panel.disagrees()
    outcome = outcome_of_panel(panel)
    assert outcome.outcome == "awaiting"
    assert outcome.complete is False
    assert outcome.verdict == ""
    assert outcome.reviewers == ("auditor",)
    assert "Awaiting a second review" in outcome_plain_words(outcome)


def test_panel_refusals():
    data = _panel_data()
    data["schema"] = "mythic.other/1"
    with pytest.raises(ValidationError):
        validate_panel(data)
    data = _panel_data()
    data["reviews"].append(
        {"reviewer": "auditor", "provider": "ollama",
         "model": "llama3.1", "verdict": "reject",
         "notes": "Again."})
    with pytest.raises(ValidationError):
        validate_panel(data)
    data = _panel_data()
    data["reviews"].append(
        {"reviewer": "guardian", "provider": "ollama",
         "model": "claude-sonnet-4-5", "verdict": "reject",
         "notes": "Same model."})
    with pytest.raises(ValidationError):
        validate_panel(data)
    data = _panel_data()
    data["reviews"].append(
        {"reviewer": "guardian", "provider": "ollama",
         "model": "llama3.1", "verdict": "reject",
         "notes": "No."})
    data["reviews"].append(
        {"reviewer": "scribe", "provider": "openai",
         "model": "gpt-5", "verdict": "approve",
         "notes": "Third."})
    with pytest.raises(ValidationError):
        validate_panel(data)
    data = _panel_data()
    data["bogus"] = 1
    with pytest.raises(ValidationError):
        validate_panel(data)


def test_agreed_outcome_names_the_shared_verdict():
    data = _panel_data()
    data["reviews"].append(
        {"reviewer": "guardian", "provider": "ollama",
         "model": "llama3.1", "verdict": "approved",
         "notes": "Also clean."})
    panel = validate_panel(data)
    outcome = outcome_of_panel(panel)
    assert outcome.outcome == "agreed"
    assert outcome.verdict == "approve"
    assert outcome.complete is True
    assert "Agreed (approve)" in outcome_plain_words(outcome)
    assert validate_outcome(outcome, panel) == outcome


def test_stored_outcome_disagreement_refuses():
    panel = validate_panel(_panel_data())
    outcome = outcome_of_panel(panel)
    stored = {"title": "A later change", "outcome": "awaiting",
              "verdict": "", "reviewers": ["guardian"],
              "verdicts": ["reject"], "complete": False}
    with pytest.raises(ValueError):
        validate_outcome(stored, panel)
    with pytest.raises(ValueError):
        PanelOutcome(
            title="A later change", outcome="agreed", verdict="approve",
            reviewers=("auditor", "guardian"),
            verdicts=("approve", "reject"), complete=True)
    with pytest.raises(ValueError):
        PanelOutcome(
            title="A later change", outcome="disagreement",
            verdict="approve", reviewers=("auditor", "guardian"),
            verdicts=("approve", "reject"), complete=True)
    built = build_outcome(
        {"title": "A later change", "outcome": "awaiting",
         "verdict": "", "reviewers": (), "verdicts": (),
         "complete": False})
    assert "No reviews" in outcome_plain_words(built)


def test_panel_file_loader_round_trip(tmp_path):
    data = _panel_data()
    data["reviews"].append(
        {"reviewer": "guardian", "provider": "ollama",
         "model": "llama3.1", "verdict": "reject",
         "notes": "Not this way.", "concerns": ["breaks the chain"]})
    panel = load_review_panel_file(_write_panel(tmp_path, data))
    assert panel.disagrees()
    assert panel.review_for("guardian").concerns == (
        "breaks the chain",)
    with pytest.raises(KeyError):
        panel.review_for("scribe")
    with pytest.raises(FileNotFoundError):
        load_review_panel_file(tmp_path / "missing.yaml")


# ---------------------------------------------------------------------
# The registry: pieces held in order, refusals kept.
# ---------------------------------------------------------------------


def test_registry_holds_pieces_and_derives():
    registry = ReviewPanelRegistry()
    change = registry.hold_change(_change())
    assert change.change_id == "change-1"
    with pytest.raises(ValueError):
        registry.hold_change(_change())
    first = registry.register_review(_review())
    assert first.review_id == "review-1"
    second = registry.register_review(_review(
        reviewer="guardian", provider="ollama", model="llama3.1",
        verdict="reject", notes="Not this way."))
    assert second.review_id == "review-2"
    assert registry.get_review("review-1") == first
    with pytest.raises(KeyError):
        registry.get_review("review-9")
    assert registry.reviews_for("guardian") == (second,)
    assert registry.list_reviews() == (first, second)
    panel = registry.panel()
    assert panel.is_complete()
    assert registry.outcome().outcome == "disagreement"


def test_registry_refusals():
    registry = ReviewPanelRegistry(_change())
    registry.register_review(_review())
    with pytest.raises(ValueError):
        registry.register_review(_review(provider="ollama",
                                         model="llama3.1"))
    with pytest.raises(ValueError):
        registry.register_review(_review(reviewer="guardian",
                                         provider="ollama"))
    registry.register_review(_review(
        reviewer="guardian", provider="ollama", model="llama3.1",
        verdict="approve", notes="Clean too."))
    with pytest.raises(ValueError):
        registry.register_review(_review(
            reviewer="scribe", provider="openai", model="gpt-5",
            verdict="approve", notes="Third."))
    empty = ReviewPanelRegistry()
    with pytest.raises(KeyError):
        empty.panel()


def test_registry_register_panel_round_trip():
    registry = ReviewPanelRegistry()
    panel = registry.register_panel(load_review_panel())
    assert panel.disagrees()
    assert registry.outcome().outcome == "disagreement"


# ---------------------------------------------------------------------
# Records, screens and the shared grammar.
# ---------------------------------------------------------------------


def test_records_carry_slice_and_headlines():
    change = change_record(_change())
    assert change["type"] == "panel_change"
    assert change["slice"] == "M-132"
    assert change["news"] is True
    assert "put to a review panel" in change["headline"]
    review = review_record(_review())
    assert review["type"] == "panel_review"
    assert "auditor reviews the change" in review["headline"]
    assert "claude-sonnet-4-5" in review["headline"]
    outcome = outcome_record(outcome_of_panel(load_review_panel()))
    assert outcome["type"] == "panel_outcome"
    assert "disagrees" in outcome["headline"]
    assert "surfaced, not averaged" in outcome["headline"]


def test_formatters_and_screen():
    line = format_review(_review(concerns=["one worry"]))
    assert line.startswith("auditor (anthropic/claude-sonnet-4-5):")
    assert "concerns: one worry" in line
    reviews = format_reviews()
    assert "auditor" in reviews and "guardian" in reviews
    outcome = format_outcome()
    assert outcome.splitlines()[0].startswith("Disagreement on")
    assert format_verdict_kinds() == (
        "Verdict kinds: approve, request_changes, reject")
    screen = format_panel_screen()
    assert screen.startswith("Review panels (M-132)")
    assert "Session-branching restore guard" in screen
    assert USAGE in screen
    awaiting = ReviewPanel(change=_change(), reviews=(_review(),))
    assert "One review still to come." in format_reviews(awaiting)


def test_parse_panel_args_grammar():
    assert parse_panel_args("") == ("show", None)
    assert parse_panel_args(None) == ("show", None)
    assert parse_panel_args("show") == ("show", None)
    assert parse_panel_args("reviews") == ("show", None)
    assert parse_panel_args("show guardian") == ("show", "guardian")
    assert parse_panel_args("guardian") == ("show", "guardian")
    assert parse_panel_args("outcome") == ("outcome", None)
    assert parse_panel_args("verdicts") == ("verdicts", None)
    assert parse_panel_args("kinds") == ("kinds", None)
    with pytest.raises(ValueError):
        parse_panel_args("show guardian extra")
    with pytest.raises(ValueError):
        parse_panel_args("two words here")
    with pytest.raises(ValueError):
        parse_panel_args(42)


def test_no_live_roads_in_the_pure_layer():
    import mythic_agent.core.review_panels as panels
    for road in ("run_panel", "spawn_panel", "call_model",
                 "run_review", "execute_change", "panel_board"):
        assert not hasattr(panels, road)
    assert (ROOT / "mythic_agent" / "data" / PANEL_RESOURCE).exists()


# -- agent layer -----------------------------------------------------------
#
# M-132 agent layer: the agent holds a
# ReviewPanelRegistry for the session (session
# state only, no new setting), a panel is recorded
# by being registered - published as its
# change_record / review_record session news
# through the checkpoint road, deduped per piece
# id - the outcome is published as ONE
# outcome_record session event, deduped per
# outcome, and the /panel surface rides both
# roads on the pure parser + formatters. Status,
# find, panel and outcome reads register and
# publish nothing. This layer runs no review,
# calls no model, executes no change, spawns no
# crew and claims no board - Part VIII does not
# exist yet, so the screen is where the outcome
# is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _panel_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


class TestPanelAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.panel_status()
        assert status["change"] is None
        assert status["reviews"] == []
        assert status["panel"]["change"]["title"] == \
            "Session-branching restore guard"
        assert len(status["panel"]["reviews"]) == 2
        assert status["outcome"]["type"] == "panel_outcome"
        assert status["outcome"]["outcome"] == "disagreement"
        assert status["outcome"]["complete"] is True
        assert "Review panels (M-132)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert agent._review_panel_registry() is \
            agent._review_panel_registry()
        assert agent._review_panel_store is \
            agent._review_panel_registry()

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.panel_status()
        found = agent.find_panel_reviews("auditor")
        assert [r.reviewer for r in found] == ["auditor"]
        assert agent.review_panel().change.title == \
            "Session-branching restore guard"
        outcome = agent.panel_outcome()
        assert outcome.outcome == "disagreement"
        assert outcome.complete is True
        registry = agent._review_panel_registry()
        assert registry.list_reviews() == ()
        for kind in ("panel_change", "panel_review",
                     "panel_outcome"):
            assert _panel_events(store, session_id, kind) == []
        agent.close()

    def test_unheld_pieces_raise_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.get_panel_review("review-1")

    def test_find_reviewer_without_a_review_raises_keyerror(
            self, agent):
        with pytest.raises(KeyError):
            agent.find_panel_reviews("scribe")

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.hold_panel_change(_change())
        agent.register_panel_review(_review())
        status = agent.panel_status()
        assert status["change"]["title"] == "A later change"
        assert [r["reviewer"] for r in status["reviews"]] == [
            "auditor"]
        # One review is held, so the outcome is still
        # awaiting its second review - the status
        # says so plainly.
        assert status["outcome"]["outcome"] == "awaiting"
        assert status["outcome"]["complete"] is False
        assert "One review still to come." in status["screen"]
        assert len(status["panel"]["reviews"]) == 2


class TestPanelAgentRegister:
    def test_hold_change_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.hold_panel_change(_change())
        assert outcome["change"]["change_id"] == "change-1"
        assert outcome["record"]["type"] == "panel_change"
        events = _panel_events(store, session_id, "panel_change")
        assert len(events) == 1
        assert events[0]["title"] == "A later change"
        # The same record is never published twice.
        agent._publish_panel_record(outcome["record"])
        assert len(_panel_events(
            store, session_id, "panel_change")) == 1
        # A foreign record type is refused on this road.
        agent._publish_panel_record(outcome_record(
            outcome_of_panel(load_review_panel())))
        assert _panel_events(store, session_id, "panel_outcome") \
            == []
        agent.close()

    def test_register_review_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.hold_panel_change(_change())
        outcome = agent.register_panel_review(_review())
        assert outcome["review"]["review_id"] == "review-1"
        assert outcome["record"]["type"] == "panel_review"
        assert len(_panel_events(
            store, session_id, "panel_change")) == 1
        assert len(_panel_events(
            store, session_id, "panel_review")) == 1
        agent._publish_panel_record(outcome["record"])
        assert len(_panel_events(
            store, session_id, "panel_review")) == 1
        agent.close()

    def test_second_change_refuses(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.hold_panel_change(_change())
        with pytest.raises(ValueError):
            agent.hold_panel_change(_change(title="Another"))
        assert len(_panel_events(
            store, session_id, "panel_change")) == 1
        agent.close()

    def test_same_reviewer_twice_refuses_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.hold_panel_change(_change())
        agent.register_panel_review(_review())
        with pytest.raises(ValueError):
            agent.register_panel_review(_review(
                provider="openai", model="gpt-5",
                verdict="reject", notes="Second reading."))
        assert len(_panel_events(
            store, session_id, "panel_review")) == 1
        agent.close()

    def test_record_panel_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_review_panel()
        assert outcome["count"] == 3
        assert outcome["change"]["title"] == \
            "Session-branching restore guard"
        assert len(outcome["reviews"]) == 2
        assert len(_panel_events(
            store, session_id, "panel_change")) == 1
        assert len(_panel_events(
            store, session_id, "panel_review")) == 2
        assert agent.review_panel().change.title == \
            "Session-branching restore guard"
        agent.close()

    def test_record_same_panel_twice_refuses(self, agent):
        agent.record_review_panel()
        with pytest.raises(ValueError):
            agent.record_review_panel()

    def test_panel_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_panel(tmp_path, _panel_data())
        panel = load_review_panel_file(path)
        outcome = agent.record_review_panel(panel)
        assert outcome["count"] == 2
        assert agent.review_panel().change.title == \
            "A later change"
        assert agent.panel_outcome().outcome == "awaiting"
        assert agent.panel_outcome().reviewers == ("auditor",)

    def test_find_prefers_the_held_pieces(self, agent):
        agent.hold_panel_change(_change())
        agent.register_panel_review(_review())
        found = agent.find_panel_reviews("auditor")
        assert [r.notes for r in found] == ["It reads clean."]
        # The held pieces answer now: the example's
        # guardian review no longer answers.
        with pytest.raises(KeyError):
            agent.find_panel_reviews("guardian")


class TestPanelAgentOutcome:
    def test_outcome_report_publishes_one_outcome_event(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.record_review_panel()
        outcome = agent.report_panel_outcome()
        assert outcome["complete"] is True
        assert outcome["record"]["type"] == "panel_outcome"
        assert outcome["outcome"]["outcome"] == "disagreement"
        assert "Disagreement on" in outcome["screen"]
        outcomes = _panel_events(
            store, session_id, "panel_outcome")
        # ONE outcome event holds the whole outcome.
        assert len(outcomes) == 1
        assert outcomes[0]["complete"] is True
        # Reporting again on the same reviews publishes
        # nothing new.
        agent.report_panel_outcome()
        assert len(_panel_events(
            store, session_id, "panel_outcome")) == 1
        agent.close()

    def test_grown_outcome_announces_as_the_new_outcome(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.hold_panel_change(_change())
        agent.register_panel_review(_review())
        outcome = agent.report_panel_outcome()
        assert outcome["outcome"]["outcome"] == "awaiting"
        assert outcome["complete"] is False
        assert len(_panel_events(
            store, session_id, "panel_outcome")) == 1
        # A newly held review grows the outcome: the
        # new outcome announces as the new outcome
        # it is.
        agent.register_panel_review(_review(
            reviewer="guardian", provider="ollama",
            model="llama3.1", verdict="request_changes",
            notes="Name the next step."))
        outcome = agent.report_panel_outcome()
        assert outcome["outcome"]["outcome"] == "disagreement"
        assert outcome["complete"] is True
        assert len(_panel_events(
            store, session_id, "panel_outcome")) == 2
        agent.close()

    def test_no_review_or_execution_road_for_panel(self, agent):
        # This layer holds the panel as data: it runs
        # no review, calls no model, executes no
        # change, spawns no crew and builds no board
        # - Part VIII does not exist yet, and the
        # live review is a later road, not this
        # slice.
        assert not hasattr(agent, "run_review_panel")
        assert not hasattr(agent, "execute_panel_change")
        assert not hasattr(agent, "spawn_review_panel")
        assert not hasattr(agent, "panel_board")


class TestPanelTerminalSurface:
    def test_show_outcome_verdicts_and_kinds(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/panel")
        assert "Review panels (M-132)" in text
        _, _, text = _slash(agent, "/panel show auditor")
        assert "auditor (anthropic/claude-sonnet-4-5): approve" \
            in text
        _, _, text = _slash(agent, "/panel outcome")
        assert "Disagreement on" in text
        _, _, text = _slash(agent, "/panel verdicts")
        assert "- auditor: approve" in text
        assert "- guardian: request_changes" in text
        _, _, text = _slash(agent, "/panel kinds")
        assert text == \
            "Verdict kinds: approve, request_changes, reject"

    def test_bare_reviewer_shows_theirs(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/panel guardian")
        assert "guardian (ollama/llama3.1): request_changes" \
            in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert "/panel [show|show <reviewer>|outcome|verdicts|kinds]" \
            in text
        # A bare word parses as a reviewer id (member
        # ids are slugs, not a fixed list), so an
        # unknown reviewer answers with the find
        # road's KeyError; two stray words are a
        # usage error.
        _, _, text = _slash(agent, "/panel dance")
        assert "no review from the reviewer" in text
        _, _, text = _slash(agent, "/panel dance party")
        assert text == USAGE


@pytest.fixture()
def panel_handler(agent, monkeypatch):
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


def _panel_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestPanelCommand:
    def test_show_is_default(self, panel_handler, agent):
        panel_handler._handle_panel("")
        assert "Review panels (M-132)" in \
            _panel_published_text(panel_handler)

    def test_show_one_outcome_verdicts_and_kinds(
            self, panel_handler, agent):
        panel_handler._handle_panel("show auditor")
        assert "auditor (anthropic/claude-sonnet-4-5): approve" \
            in _panel_published_text(panel_handler)
        panel_handler._handle_panel("outcome")
        assert "Disagreement on" in \
            _panel_published_text(panel_handler)
        panel_handler._handle_panel("verdicts")
        assert "- guardian: request_changes" in \
            _panel_published_text(panel_handler)
        panel_handler._handle_panel("kinds")
        assert "Verdict kinds:" in \
            _panel_published_text(panel_handler)

    def test_bad_grammar_is_published(self, panel_handler, agent):
        panel_handler._handle_panel("dance party")
        assert USAGE in _panel_published_text(panel_handler)


class TestChatScreenRoutingPanel:
    def test_panel_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/panel kinds", _FakeLog())
        assert calls == [("/panel", "kinds")]
