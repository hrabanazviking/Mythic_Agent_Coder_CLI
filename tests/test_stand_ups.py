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
