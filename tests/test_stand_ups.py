"""M-134 Stand-ups - pure-layer tests.

TIER: integration

The pure layer is the coordinator's progress
digest as data: a stand-up report of progress
entries (one item of work per entry - its title,
the item in plain words, the member who holds it,
and the state it stands in: done, doing, blocked
or needs-you) under a title and a boundary, the
shipped example stand-up held in a data file, a
loader that reads a stand-up from any file, the
digest derived from the entries alone into its
four sections, records shaped as session news,
and a registry. Nothing here is scheduled, sent,
posted or persisted, and no model is called: the
digest is derived, never stored, and a stored
digest that disagrees with the derived one is
refused.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.crew_members import load_casting
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.stand_ups import (
    PLAIN_EXPLANATION,
    STAND_UP_RESOURCE,
    STAND_UP_SCHEMA,
    STAND_UP_SLICE,
    STATUS_KINDS,
    USAGE,
    ProgressEntry,
    StandUpDigest,
    StandUpRegistry,
    StandUpReport,
    build_digest,
    build_entry,
    build_report,
    digest_plain_words,
    digest_record,
    digest_stand_up,
    entry_record,
    format_digest,
    format_entries,
    format_entry,
    format_stand_up_screen,
    format_status_kinds,
    load_stand_up,
    load_stand_up_file,
    normalize_status,
    parse_stand_up_args,
    plain_words,
    report_record,
    validate_digest,
    validate_entry,
    validate_report,
)

ROOT = Path(__file__).resolve().parents[1]


def _entry(**kwargs):
    kwargs.setdefault("entry_id", "an-item")
    kwargs.setdefault("member", "auditor")
    kwargs.setdefault("title", "An item")
    kwargs.setdefault("detail", "The item stands so.")
    kwargs.setdefault("status", "doing")
    return ProgressEntry(**kwargs)


def _report_data():
    return {
        "schema": STAND_UP_SCHEMA, "slice": STAND_UP_SLICE,
        "report": {"title": "A stand-up", "boundary": "M-100"},
        "entries": [
            {"entry_id": "done-item", "member": "scribe",
             "title": "Done item", "detail": "It is finished.",
             "status": "done"},
            {"entry_id": "doing-item", "member": "auditor",
             "title": "Doing item", "detail": "It is under way.",
             "status": "doing"},
            {"entry_id": "held-item", "member": "guardian",
             "title": "Held item", "detail": "It waits on a fix.",
             "status": "blocked"},
            {"entry_id": "word-item", "member": "cartographer",
             "title": "Word item", "detail": "It needs a decision.",
             "status": "needs_you"},
        ]}


def _write_stand_up(tmp_path, data):
    path = tmp_path / "stand_up.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_constants_and_usage():
    assert STAND_UP_SLICE == "M-134"
    assert STAND_UP_RESOURCE == "stand_ups.yaml"
    assert STAND_UP_SCHEMA == "mythic.stand_ups/1"
    assert STATUS_KINDS == ("done", "doing", "blocked", "needs_you")
    assert USAGE.startswith("Usage: /standup")
    assert "needs-you" in PLAIN_EXPLANATION
    assert "schedules nothing" in PLAIN_EXPLANATION


def test_shipped_example_stand_up_shape():
    report = load_stand_up()
    assert report.boundary == "M-133"
    assert report.title == "Stand-up at the M-133 slice boundary"
    assert len(report.entries) == 5
    digest = digest_stand_up(report)
    assert digest.done == ("m-133-memory-banked", "m-132-panels-banked")
    assert digest.doing == ("m-134-stand-ups-building",)
    assert digest.blocked == ("full-suite-portaudio-held",)
    assert digest.needs_you == ("hall-posting-needs-word",)
    assert digest.counts() == {
        "done": 2, "doing": 1, "blocked": 1, "needs_you": 1}
    assert digest.total() == 5


def test_example_members_are_the_shipped_casting():
    casting = load_casting()
    ids = [member.member_id for member in casting.members]
    for entry in load_stand_up().entries:
        assert entry.member in ids


def test_digest_groups_by_state_in_report_order():
    report = StandUpReport(title="T", boundary="M-1", entries=(
        _entry(entry_id="b-item", status="blocked"),
        _entry(entry_id="a-item", status="done"),
        _entry(entry_id="c-item", status="done"),
        _entry(entry_id="d-item", status="needs_you"),
    ))
    digest = digest_stand_up(report)
    assert digest.done == ("a-item", "c-item")
    assert digest.doing == ()
    assert digest.blocked == ("b-item",)
    assert digest.needs_you == ("d-item",)
    assert digest_stand_up(report) == digest
    assert report.entries_for("Finished")[0].entry_id == "a-item"


def test_digest_refuses_an_id_less_entry():
    report = StandUpReport(title="T", boundary="M-1", entries=(
        _entry(entry_id=None),))
    with pytest.raises(ValueError):
        digest_stand_up(report)


def test_needs_you_is_its_own_section_never_blocked():
    report = load_stand_up()
    digest = digest_stand_up(report)
    assert "hall-posting-needs-word" in digest.needs_you
    assert "hall-posting-needs-word" not in digest.blocked


def test_stored_digest_must_agree_with_the_derived_one():
    report = validate_report(_report_data())
    derived = digest_stand_up(report)
    stored = {
        "title": derived.title, "boundary": derived.boundary,
        "done": list(derived.done), "doing": list(derived.doing),
        "blocked": list(derived.blocked),
        "needs-you": list(derived.needs_you)}
    assert validate_digest(stored, report) == derived
    assert build_digest(derived) is derived
    stored["done"] = []
    with pytest.raises(ValueError):
        validate_digest(stored, report)
    data = _report_data()
    data["digest"] = {
        "title": "A stand-up", "boundary": "M-100",
        "done": ["doing-item"], "doing": [], "blocked": [],
        "needs_you": []}
    with pytest.raises(ValidationError):
        validate_report(data)
    data = _report_data()
    good = digest_stand_up(validate_report(_report_data()))
    data["digest"] = {
        "title": good.title, "boundary": good.boundary,
        "done": list(good.done), "doing": list(good.doing),
        "blocked": list(good.blocked), "needs_you": list(good.needs_you)}
    assert validate_report(data).boundary == "M-100"


def test_digest_names_one_entry_in_two_sections_refuses():
    with pytest.raises(ValueError):
        StandUpDigest(title="T", boundary="M-1",
                      done=("x-item",), blocked=("x-item",))
    with pytest.raises(ValueError):
        validate_digest({"title": "T", "boundary": "M-1", "bogus": []})
    with pytest.raises(ValueError):
        validate_digest({"boundary": "M-1"})


def test_normalize_status_readings_and_refusals():
    assert normalize_status("Finished") == "done"
    assert normalize_status("BANKED") == "done"
    assert normalize_status("in-progress") == "doing"
    assert normalize_status("Working") == "doing"
    assert normalize_status("stuck") == "blocked"
    assert normalize_status("Held") == "blocked"
    assert normalize_status("needs-you") == "needs_you"
    assert normalize_status("Needs_Human") == "needs_you"
    assert normalize_status("decision") == "needs_you"
    with pytest.raises(ValueError):
        normalize_status("maybe")
    with pytest.raises(ValueError):
        normalize_status("")
    with pytest.raises(ValueError):
        normalize_status(None)


def test_entry_validation_and_two_spellings_refusal():
    entry = validate_entry(
        {"member_id": "guardian", "name": "Words",
         "body": "It stands so.", "state": "Finished"})
    assert entry.member == "guardian"
    assert entry.title == "Words"
    assert entry.detail == "It stands so."
    assert entry.status == "done"
    with pytest.raises(ValueError):
        validate_entry({"member": "guardian", "title": "One",
                        "name": "Two", "detail": "So.",
                        "status": "done"})
    with pytest.raises(ValueError):
        validate_entry({"member": "guardian", "title": "T",
                        "detail": "So.", "status": "done", "bogus": 1})
    with pytest.raises(ValueError):
        validate_entry({"member": "guardian", "title": "T",
                        "status": "done"})
    with pytest.raises(ValueError):
        _entry(detail="  ")
    with pytest.raises(ValueError):
        _entry(member="two words")
    with pytest.raises(ValueError):
        _entry(status="pending")
    assert build_entry(member="scribe", title="Built", detail="So.",
                       status="blocked").status == "blocked"
    assert plain_words(_entry()).startswith("auditor - An item (doing):")


def test_report_validation_and_shared_view():
    report = validate_report(_report_data())
    assert report.boundary == "M-100"
    assert [e.entry_id for e in report.entries] == [
        "done-item", "doing-item", "held-item", "word-item"]
    assert report.entry_for("held-item").status == "blocked"
    assert report.entries_for("needs-you")[0].entry_id == "word-item"
    assert build_report(report) is report
    with pytest.raises(KeyError):
        report.entry_for("missing")


def test_report_refusals():
    data = _report_data()
    data["schema"] = "mythic.other/1"
    with pytest.raises(ValidationError):
        validate_report(data)
    data = _report_data()
    data["bogus"] = 1
    with pytest.raises(ValidationError):
        validate_report(data)
    data = _report_data()
    data["entries"][1]["entry_id"] = "done-item"
    with pytest.raises(ValidationError):
        validate_report(data)
    data = _report_data()
    del data["entries"]
    with pytest.raises(ValidationError):
        validate_report(data)
    data = _report_data()
    del data["report"]["boundary"]
    with pytest.raises(ValidationError):
        validate_report(data)
    with pytest.raises(ValueError):
        StandUpReport(title="T", boundary="M-1", entries=(
            _entry(entry_id="x"), _entry(entry_id="x", title="Other")))


def test_file_loader_round_trip_and_missing_file(tmp_path):
    path = _write_stand_up(tmp_path, _report_data())
    report = load_stand_up_file(path)
    assert report.boundary == "M-100"
    assert report.entry_for("word-item").member == "cartographer"
    with pytest.raises(FileNotFoundError):
        load_stand_up_file(tmp_path / "nope.yaml")


def test_registry_hold_and_digest():
    registry = StandUpRegistry()
    registry.register_report(validate_report(_report_data()))
    assert registry.get_entry("done-item").member == "scribe"
    assert [e.entry_id for e in registry.list_entries()] == [
        "done-item", "doing-item", "held-item", "word-item"]
    assert registry.digest().needs_you == ("word-item",)
    assert [e.entry_id for e in registry.entries_for("blocked")] == [
        "held-item"]
    assert registry.report().title == "A stand-up"
    with pytest.raises(KeyError):
        registry.get_entry("missing")


def test_registry_auto_ids_and_refusals():
    registry = StandUpRegistry(StandUpReport(title="T", boundary="M-1"))
    first = registry.register_entry(_entry(entry_id=None))
    assert first.entry_id == "entry-1"
    second = registry.register_entry(
        _entry(entry_id=None, title="Second", status="done"))
    assert second.entry_id == "entry-2"
    assert registry.digest().done == ("entry-2",)
    with pytest.raises(ValueError):
        registry.register_entry(_entry(entry_id="entry-1"))
    with pytest.raises(ValueError):
        registry.register_report(validate_report(_report_data()))
    with pytest.raises(ValueError):
        StandUpRegistry().report()
    fresh = StandUpRegistry(load_stand_up())
    assert fresh.digest().total() == 5
    with pytest.raises(ValueError):
        fresh.register_report(load_stand_up())


def test_records_are_session_news():
    entry = entry_record(_entry())
    assert entry["type"] == "stand_up_entry"
    assert entry["slice"] == "M-134"
    assert entry["news"] is True
    assert "auditor" in entry["headline"]
    report = report_record(load_stand_up())
    assert report["type"] == "stand_up_report"
    assert report["entry_count"] == 5
    assert "M-133" in report["headline"]
    digest = digest_record(digest_stand_up(load_stand_up()))
    assert digest["type"] == "stand_up_digest"
    assert digest["counts"] == {
        "done": 2, "doing": 1, "blocked": 1, "needs_you": 1}
    assert "2 done" in digest["headline"]
    assert "1 needs-you" in digest["headline"]
    with pytest.raises(ValueError):
        digest_record({"title": "T", "boundary": "M-133", "done": []},
                      load_stand_up())


def test_digest_plain_words_cover_all_four_sections():
    words = digest_plain_words(load_stand_up())
    assert "done: M-133 crew memory banked" in words
    assert "doing: M-134 stand-ups pure layer being built." in words
    assert "blocked: Full suite held" in words
    assert "needs-you: Posting stand-ups to the hall" in words
    empty = digest_plain_words(StandUpReport(title="T", boundary="M-9"))
    assert "done: nothing." in empty
    assert "needs-you: nothing." in empty
    bare = digest_plain_words(digest_stand_up(load_stand_up()))
    assert "done: m-133-memory-banked" in bare


def test_formatters_and_screen():
    report = load_stand_up()
    assert "scribe / m-133-memory-banked [done]" in format_entry(
        report.entry_for("m-133-memory-banked"))
    assert "hall-posting-needs-word" in format_entries(report)
    assert "word-item" not in format_entries(
        validate_report(_report_data()), "done")
    digest_text = format_digest(report)
    assert "Digest at M-133: 5 item(s)" in digest_text
    assert "needs-you (1):" in digest_text
    assert format_status_kinds() == (
        "Status kinds: done, doing, blocked, needs-you")
    screen = format_stand_up_screen(report)
    assert "Stand-ups (M-134)" in screen
    assert USAGE in screen
    assert format_entries(StandUpReport(
        title="T", boundary="M-9")) == "No items stand reported."


def test_parse_stand_up_args_grammar():
    assert parse_stand_up_args("") == ("show", None)
    assert parse_stand_up_args("show") == ("show", None)
    assert parse_stand_up_args("digest") == ("digest", None)
    assert parse_stand_up_args("done") == ("section", "done")
    assert parse_stand_up_args("Blocked") == ("section", "blocked")
    assert parse_stand_up_args("needs-you") == ("section", "needs_you")
    assert parse_stand_up_args("needs_you") == ("section", "needs_you")
    assert parse_stand_up_args("entry m-133-memory-banked") == (
        "entry", "m-133-memory-banked")
    assert parse_stand_up_args("kinds") == ("kinds", None)
    with pytest.raises(ValueError):
        parse_stand_up_args("entry")
    with pytest.raises(ValueError):
        parse_stand_up_args("bogus words here")
    with pytest.raises(ValueError):
        parse_stand_up_args(42)


def test_no_live_roads_in_pure_layer():
    import mythic_agent.core.stand_ups as module
    source = Path(module.__file__).read_text(encoding="utf-8")
    for banned in ("import subprocess", "requests.", "openai",
                   "anthropic", "AgentManager", "def spawn",
                   "def persist", "def schedule"):
        assert banned not in source
    record = _entry().to_record()
    assert "digest" not in record and "sections" not in record

# -- agent layer -----------------------------------------------------------
#
# M-134 agent layer: the agent holds a
# StandUpRegistry for the session (session state
# only, no new setting), entries are held by
# being registered - published as their
# entry_record session news through the checkpoint
# road, deduped per entry id - the whole report's
# digest is published as ONE digest_record session
# event, deduped per whole digest shape, and the
# /standup surface rides both roads on the pure
# parser + formatters. Status, get, digest and
# stand-up reads register and publish nothing,
# answer from the held registry first and from
# the shipped example only while nothing is held
# - a held session never falls back to the
# example. This layer schedules nothing, sends
# nothing, posts nothing, persists nothing, calls
# no model and claims no board - Part VIII does
# not exist yet, so the screen is where the
# digest is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _stand_up_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


class TestStandUpAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.stand_up_status()
        assert status["entries"] == []
        assert status["report"] is None
        assert status["stand_up"]["title"] == (
            "Stand-up at the M-133 slice boundary")
        assert status["stand_up"]["boundary"] == "M-133"
        assert len(status["stand_up"]["entries"]) == 5
        assert status["report_record"]["type"] == "stand_up_report"
        assert status["report_record"]["entry_count"] == 5
        assert status["digest"]["counts"] == {
            "done": 2, "doing": 1, "blocked": 1, "needs_you": 1}
        assert status["digest_record"]["type"] == "stand_up_digest"
        assert "Stand-ups (M-134)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert agent._stand_up_registry() is             agent._stand_up_registry()
        assert agent._stand_up_store is             agent._stand_up_registry()

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.stand_up_status()
        entry = agent.get_stand_up_entry("m-133-memory-banked")
        assert entry.member == "scribe"
        digest = agent.stand_up_digest()
        assert digest.done == (
            "m-133-memory-banked", "m-132-panels-banked")
        assert digest.needs_you == ("hall-posting-needs-word",)
        assert agent.stand_up().boundary == "M-133"
        registry = agent._stand_up_registry()
        assert registry.list_entries() == ()
        for kind in ("stand_up_entry", "stand_up_digest"):
            assert _stand_up_events(store, session_id, kind) == []
        agent.close()

    def test_unheld_get_raises_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.get_stand_up_entry("entry-1")
        with pytest.raises(KeyError):
            agent.get_stand_up_entry("no-such-entry")

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_stand_up_entry(_entry())
        status = agent.stand_up_status()
        assert [e["entry_id"] for e in status["entries"]] == ["an-item"]
        assert status["report"]["entry_count"] == 1
        # The held stand-up answers now, not the example:
        # the session stand-up is the held entries alone.
        assert [e["entry_id"] for e in status["stand_up"]["entries"]] == [
            "an-item"]
        assert status["digest"]["counts"] == {
            "done": 0, "doing": 1, "blocked": 0, "needs_you": 0}
        assert "An item" in status["screen"]

    def test_held_session_never_falls_back_to_the_example(
            self, agent):
        agent.register_stand_up_entry(_entry())
        with pytest.raises(KeyError):
            agent.get_stand_up_entry("m-133-memory-banked")
        assert [e.entry_id for e in agent.stand_up().entries] == [
            "an-item"]
        assert agent.stand_up_digest().doing == ("an-item",)
        assert agent.stand_up_digest().done == ()


class TestStandUpAgentRegister:
    def test_register_entry_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_stand_up_entry(_entry())
        assert outcome["entry"]["entry_id"] == "an-item"
        assert outcome["record"]["type"] == "stand_up_entry"
        events = _stand_up_events(store, session_id, "stand_up_entry")
        assert len(events) == 1
        assert events[0]["entry_id"] == "an-item"
        # The same record is never published twice.
        agent._publish_stand_up_record(outcome["record"])
        assert len(_stand_up_events(
            store, session_id, "stand_up_entry")) == 1
        # Foreign record types are refused on this road.
        from mythic_agent.core.crew_members import (
            casting_record,
            load_casting,
        )
        from mythic_agent.core.crew_memory import (
            entry_record as _memory_entry_record,
            load_crew_memory,
            notebook_record,
        )
        from mythic_agent.core.review_panels import (
            load_review_panel,
            review_record,
        )
        memory = load_crew_memory()
        agent._publish_stand_up_record(_memory_entry_record(
            memory.entry_for("broken-checkpoint-chain")))
        agent._publish_stand_up_record(notebook_record(
            memory.notebook_for("auditor")))
        panel = load_review_panel()
        agent._publish_stand_up_record(review_record(panel.reviews[0]))
        agent._publish_stand_up_record(casting_record(
            load_casting().members[0]))
        for kind in ("crew_memory_entry", "member_notebook",
                     "panel_review", "crew_member"):
            assert _stand_up_events(store, session_id, kind) == []
        assert len(_stand_up_events(
            store, session_id, "stand_up_entry")) == 1
        agent.close()

    def test_duplicate_id_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_stand_up_entry(_entry())
        with pytest.raises(ValueError):
            agent.register_stand_up_entry(
                _entry(title="Another item"))
        assert len(_stand_up_events(
            store, session_id, "stand_up_entry")) == 1
        agent.close()

    def test_record_report_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_stand_up_report()
        assert outcome["count"] == 5
        assert outcome["report"]["entry_count"] == 5
        events = _stand_up_events(store, session_id, "stand_up_entry")
        assert [e["entry_id"] for e in events] == [
            "m-133-memory-banked", "m-134-stand-ups-building",
            "m-132-panels-banked", "full-suite-portaudio-held",
            "hall-posting-needs-word"]
        assert agent.stand_up().boundary == "M-133"
        assert agent.get_stand_up_entry(
            "hall-posting-needs-word").status == "needs_you"
        agent.close()

    def test_record_same_report_twice_refuses(self, agent):
        agent.record_stand_up_report()
        with pytest.raises(ValueError):
            agent.record_stand_up_report()

    def test_report_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_stand_up(tmp_path, _report_data())
        report = load_stand_up_file(path)
        outcome = agent.record_stand_up_report(report)
        assert outcome["count"] == 4
        assert agent.get_stand_up_entry(
            "word-item").member == "cartographer"
        assert agent.stand_up_digest().needs_you == ("word-item",)


class TestStandUpAgentReport:
    def test_digest_report_publishes_one_digest_event_and_dedups(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.record_stand_up_report()
        outcome = agent.report_stand_up()
        assert outcome["record"]["type"] == "stand_up_digest"
        assert outcome["entry_count"] == 5
        assert outcome["digest"]["counts"] == {
            "done": 2, "doing": 1, "blocked": 1, "needs_you": 1}
        events = _stand_up_events(store, session_id, "stand_up_digest")
        # ONE digest event holds the whole digest.
        assert len(events) == 1
        assert events[0]["entry_count"] == 5
        # Reporting again on the same digest publishes
        # nothing new.
        agent.report_stand_up()
        assert len(_stand_up_events(
            store, session_id, "stand_up_digest")) == 1
        agent.close()

    def test_changed_digest_announces_again(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_stand_up_entry(_entry())
        outcome = agent.report_stand_up()
        assert outcome["entry_count"] == 1
        assert len(_stand_up_events(
            store, session_id, "stand_up_digest")) == 1
        # A newly held entry changes the digest: the new
        # digest announces as the new digest it is.
        agent.register_stand_up_entry(_entry(
            entry_id="b-item", title="B item", status="done"))
        outcome = agent.report_stand_up()
        assert outcome["entry_count"] == 2
        events = _stand_up_events(store, session_id, "stand_up_digest")
        assert len(events) == 2
        assert events[1]["counts"]["done"] == 1
        agent.close()

    def test_no_schedule_send_post_persist_or_model_road(self, agent):
        # This layer holds the stand-up as data: it
        # schedules nothing, sends nothing, posts
        # nothing, persists nothing and calls no model
        # - and there is no Part VIII board yet.
        assert not hasattr(agent, "schedule_stand_up")
        assert not hasattr(agent, "send_stand_up")
        assert not hasattr(agent, "post_stand_up")
        assert not hasattr(agent, "persist_stand_up")
        assert not hasattr(agent, "stand_up_board")


class TestStandUpTerminalSurface:
    def test_show_digest_sections_entry_and_kinds(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/standup")
        assert "Stand-ups (M-134)" in text
        _, _, text = _slash(agent, "/standup digest")
        assert "Digest at M-133: 5 item(s)" in text
        _, _, text = _slash(agent, "/standup done")
        assert "m-133-memory-banked" in text
        assert "hall-posting-needs-word" not in text
        _, _, text = _slash(agent, "/standup needs-you")
        assert "hall-posting-needs-word" in text
        _, _, text = _slash(agent, "/standup entry m-133-memory-banked")
        assert "m-133-memory-banked" in text
        _, _, text = _slash(agent, "/standup kinds")
        assert text == "Status kinds: done, doing, blocked, needs-you"

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/standup [show|digest|done|doing|blocked|"
                "needs-you|entry <entry-id>|kinds]") in text
        _, _, text = _slash(agent, "/standup dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/standup entry missing-entry")
        assert "no entry in the stand-up" in text


@pytest.fixture()
def standup_handler(agent, monkeypatch):
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


def _standup_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestStandUpCommand:
    def test_show_is_default(self, standup_handler, agent):
        standup_handler._handle_standup("")
        assert "Stand-ups (M-134)" in \
            _standup_published_text(standup_handler)

    def test_digest_section_entry_and_kinds(
            self, standup_handler, agent):
        standup_handler._handle_standup("digest")
        assert "Digest at M-133" in \
            _standup_published_text(standup_handler)
        standup_handler._handle_standup("blocked")
        assert "full-suite-portaudio-held" in \
            _standup_published_text(standup_handler)
        standup_handler._handle_standup("entry hall-posting-needs-word")
        assert "hall-posting-needs-word" in \
            _standup_published_text(standup_handler)
        standup_handler._handle_standup("kinds")
        assert "needs-you" in \
            _standup_published_text(standup_handler)

    def test_bad_grammar_is_published(self, standup_handler, agent):
        standup_handler._handle_standup("dance party")
        assert USAGE in _standup_published_text(standup_handler)


class TestChatScreenRoutingStandUp:
    def test_standup_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/standup kinds", _FakeLog())
        assert calls == [("/standup", "kinds")]
