"""M-139 Failure fostering - pure-layer tests.

TIER: integration

The pure layer is failure fostering as data: a
fostering book of original dealings (the M-125
dealt assignments themselves, composed by import
from the task-dealing layer) and the failure
reports filed against them, the shipped example
fostering book held in a data file, a loader that
reads a fostering book from any file, fostered
re-deals whose account is derived from the
original dealing and its failure report,
escalations whose account is derived from the
two reports of the same failure, records shaped
as session news, and a registry. Nothing here
re-deals a task to a live agent, delivers an
escalation, calls a model or spawns an agent: a
stored re-deal disagreeing with the account
derived from its own parts is refused, and a
stored escalation disagreeing with the account
derived from its reports is refused.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.crew_members import load_casting
from mythic_agent.core.task_dealing import DealtAssignment
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.failure_fostering import (
    FAILURE_FOSTERING_RESOURCE,
    FAILURE_FOSTERING_SCHEMA,
    FAILURE_FOSTERING_SLICE,
    HUMAN_RECIPIENT,
    PLAIN_EXPLANATION,
    USAGE,
    FailureEscalation,
    FailureReport,
    FosterBook,
    FosterRegistry,
    FosteredRedeal,
    book_record,
    build_book,
    build_escalation,
    build_redeal,
    build_report,
    derive_escalation,
    derive_redeal,
    escalation_plain_words,
    escalation_record,
    format_escalation,
    format_fostering_screen,
    format_redeal,
    format_report,
    format_reports,
    load_failure_fostering,
    load_failure_fostering_file,
    parse_fostering_args,
    plain_words,
    redeal_plain_words,
    redeal_record,
    report_record,
    validate_book,
    validate_escalation,
    validate_redeal,
    validate_report,
)

ROOT = Path(__file__).resolve().parents[1]


def _assignment(**kwargs):
    kwargs.setdefault("assignment_id", "assign-m139-forge")
    kwargs.setdefault("member", "forge_worker")
    kwargs.setdefault("office", "forge_worker")
    kwargs.setdefault("slice_id", "M-139")
    kwargs.setdefault("title", "Failure fostering")
    kwargs.setdefault("required_office", "forge_worker")
    kwargs.setdefault("load_after", 1)
    return DealtAssignment(**kwargs)


def _report(**kwargs):
    kwargs.setdefault("report_id", "report-first")
    kwargs.setdefault("member", "forge_worker")
    kwargs.setdefault("slice_id", "M-139")
    kwargs.setdefault("failure_key", "replay-gap")
    kwargs.setdefault("title", "Replay gap found")
    kwargs.setdefault(
        "body",
        "The replay book for the finished run skips "
        "a hand-off, so the closing decision cannot "
        "be shown whole.")
    return FailureReport(**kwargs)


def _reports():
    return [
        _report(),
        _report(
            report_id="report-second",
            title="Replay gap found again",
            body="The same replay gap is still there "
                 "on the second run."),
        FailureReport(
            report_id="report-note", member="scribe",
            slice_id="M-138", failure_key="trace-slip",
            title="Trace slip noted",
            body="One trace statement names the wrong step."),
    ]


def _assignments():
    return [
        _assignment(),
        DealtAssignment(
            assignment_id="assign-m138-scribe", member="scribe",
            office="scribe", slice_id="M-138", title="Crew replay",
            required_office="scribe", load_after=1),
    ]


def _assignment_dict(a):
    return {
        "assignment_id": a.assignment_id, "member": a.member,
        "office": a.office, "slice_id": a.slice_id,
        "title": a.title, "required_office": a.required_office,
        "load_after": a.load_after}


def _report_dict(r):
    return {
        "report_id": r.report_id, "member": r.member,
        "slice_id": r.slice_id, "failure_key": r.failure_key,
        "title": r.title, "body": r.body}


def _book_data():
    redeal = derive_redeal(_assignment(), _report(), "auditor")
    escalation = derive_escalation(_reports(), "report-first")
    return {
        "schema": FAILURE_FOSTERING_SCHEMA,
        "slice": FAILURE_FOSTERING_SLICE,
        "guide": {"title": "A fostering book"},
        "assignments": [_assignment_dict(a) for a in _assignments()],
        "reports": [_report_dict(r) for r in _reports()],
        "redeals": [{
            "redeal_id": "redeal-m139",
            "assignment": _assignment_dict(_assignment()),
            "report": _report_dict(_report()),
            "foster_member": "auditor",
            "account": list(redeal.account)}],
        "escalations": [{
            "escalation_id": "escalation-m139",
            "member": "forge_worker", "slice_id": "M-139",
            "failure_key": "replay-gap",
            "report_ids": list(escalation.report_ids),
            "account": list(escalation.account)}]}


def _write_book(tmp_path, data):
    path = tmp_path / "fostering.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_constants_and_usage():
    assert FAILURE_FOSTERING_SLICE == "M-139"
    assert FAILURE_FOSTERING_RESOURCE == "failure_fostering.yaml"
    assert FAILURE_FOSTERING_SCHEMA == "mythic.failure_fostering/1"
    assert HUMAN_RECIPIENT == "human"
    assert "re-dealt" in PLAIN_EXPLANATION
    assert "data only" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /foster")
    assert "report <report-id>" in USAGE
    assert "escalation <report-id>" in USAGE


def test_shipped_example_book_shape():
    book = load_failure_fostering()
    assert book.title == (
        "Failure fostering at the M-138 slice boundary")
    assert [a.slice_id for a in book.assignments] == ["M-139", "M-138"]
    assert book.report_ids() == (
        "report-first", "report-second", "report-note")
    first, second, note = book.reports
    assert (first.member, first.failure_key) == (
        "forge_worker", "replay-gap")
    assert (second.member, second.failure_key) == (
        "forge_worker", "replay-gap")
    assert (note.member, note.slice_id, note.failure_key) == (
        "scribe", "M-138", "trace-slip")
    redeal = book.redeal_for("redeal-m139")
    assert redeal.member == "forge_worker"
    assert redeal.foster_member == "auditor"
    assert redeal.account == (
        "Slice M-139 'Failure fostering' was dealt "
        "to forge_worker.",
        "forge_worker reported failure 'replay-gap' "
        "on M-139: 'Replay gap found'.",
        "The task is re-dealt to auditor with its "
        "failure report attached.")
    escalation = book.escalation_for("escalation-m139")
    assert escalation.recipient == "human"
    assert escalation.report_ids == ("report-first", "report-second")
    assert escalation.account == (
        "Report 1: forge_worker reported 'Replay gap "
        "found' (replay-gap) on M-139.",
        "Report 2: forge_worker reported 'Replay gap "
        "found again' (replay-gap) on M-139.",
        "The same failure 'replay-gap' on M-139 "
        "happened twice; it escalates to the human "
        "with both reports attached.")
    # The kept note is a different failure: it is
    # no part of the escalation.
    assert "report-note" not in escalation.report_ids


def test_example_members_hold_shipped_casting_members():
    casting = load_casting()
    held = {member.member_id for member in casting.members}
    book = load_failure_fostering()
    for assignment in book.assignments:
        assert assignment.member in held
    for report in book.reports:
        assert report.member in held
    for redeal in book.redeals:
        assert redeal.foster_member in held


def test_report_validation_and_alias_spellings():
    report = validate_report({
        "id": "report-first", "member_id": "forge_worker",
        "slice": "m-139", "failure": "replay-gap",
        "title": "Replay gap found", "text": "A body."})
    assert report.report_id == "report-first"
    assert report.slice_id == "M-139"
    assert report.failure_key == "replay-gap"
    assert report.body == "A body."
    same = build_report(_report_dict(_report()))
    assert same == _report()
    with pytest.raises(ValueError):
        validate_report({
            "member": "forge_worker", "member_id": "scribe",
            "slice_id": "M-139", "failure_key": "replay-gap",
            "title": "T", "body": "B"})
    with pytest.raises(ValueError):
        validate_report({
            "member": "forge_worker", "slice_id": "M-139",
            "failure_key": "replay-gap", "failure": "other-gap",
            "title": "T", "body": "B"})


def test_report_refusals():
    base = _report_dict(_report())
    for bad in (
            {**base, "surprise": 1},
            {**base, "member": "human resources"},
            {**base, "slice_id": "X-139"},
            {**base, "failure_key": "has space"},
            {**base, "title": ""},
            {**base, "body": ""},
            {k: v for k, v in base.items() if k != "body"},
            {k: v for k, v in base.items() if k != "member"},
            "not a mapping"):
        with pytest.raises(ValueError):
            validate_report(bad)


def test_redeal_derivation_is_deterministic():
    one = derive_redeal(_assignment(), _report(), "auditor")
    two = derive_redeal(
        _assignment_dict(_assignment()), _report_dict(_report()),
        "auditor")
    assert one == two
    assert one.member == "forge_worker"
    assert one.slice_id == "M-139"
    assert one.foster_member == "auditor"
    assert one.account[-1] == (
        "The task is re-dealt to auditor with its "
        "failure report attached.")
    # The dealing layer's own spellings ride inside
    # the embedded dealing, read by that layer.
    dealt = derive_redeal(
        {**_assignment_dict(_assignment()), "member_id": "forge_worker"},
        _report(), "scribe")
    assert dealt.foster_member == "scribe"


def test_stored_redeal_must_agree_with_its_parts():
    derived = derive_redeal(_assignment(), _report(), "auditor")
    stored = {
        "redeal_id": "redeal-m139",
        "assignment": _assignment_dict(_assignment()),
        "report": _report_dict(_report()),
        "foster_member": "auditor",
        "account": list(derived.account)}
    assert build_redeal(stored).account == derived.account
    assert validate_redeal(stored).account == derived.account
    assert validate_redeal(
        stored, _assignment(), _report()).foster_member == "auditor"
    tampered = {**stored, "account": ["Invented."] + list(derived.account[1:])}
    with pytest.raises(ValueError):
        validate_redeal(tampered)
    with pytest.raises(ValueError):
        validate_redeal(stored, _assignments()[1])
    with pytest.raises(ValueError):
        validate_redeal(stored, report=_reports()[2])
    with pytest.raises(ValueError):
        validate_redeal({k: v for k, v in stored.items() if k != "account"})
    with pytest.raises(ValueError):
        validate_redeal({**stored, "surprise": 1})


def test_redeal_refusals():
    with pytest.raises(ValueError):
        derive_redeal(_assignment(), _report(), "forge_worker")
    with pytest.raises(ValueError):
        derive_redeal(_assignment(), _reports()[2], "auditor")
    with pytest.raises(ValueError):
        derive_redeal(
            _assignment(),
            _report(member="scribe"), "auditor")
    with pytest.raises(ValueError):
        FosteredRedeal(
            assignment=_assignment(), report=_report(),
            foster_member="forge_worker", account=("A.",))
    with pytest.raises(ValueError):
        build_redeal("not a mapping")


def test_escalation_derivation_is_deterministic():
    one = derive_escalation(_reports(), "report-first")
    two = derive_escalation(_reports(), "report-first", "report-second")
    assert one == two
    assert one.member == "forge_worker"
    assert one.recipient == HUMAN_RECIPIENT
    assert one.report_ids == ("report-first", "report-second")
    assert len(one.account) == 3
    # One report of a failure is not the same
    # failure twice: the kept note never escalates.
    with pytest.raises(ValueError):
        derive_escalation(_reports(), "report-note")
    # Two reports of different failures never
    # escalate together.
    with pytest.raises(ValueError):
        derive_escalation(_reports(), "report-first", "report-note")
    with pytest.raises(KeyError):
        derive_escalation(_reports(), "report-missing")


def test_stored_escalation_must_agree_with_its_reports():
    derived = derive_escalation(_reports(), "report-first")
    stored = {
        "escalation_id": "escalation-m139",
        "member": "forge_worker", "slice_id": "M-139",
        "failure_key": "replay-gap",
        "report_ids": ["report-first", "report-second"],
        "account": list(derived.account)}
    judged = validate_escalation(stored, _reports())
    assert judged.account == derived.account
    assert judged.report_ids == derived.report_ids
    filled = {k: v for k, v in stored.items() if k != "account"}
    assert validate_escalation(filled, _reports()).account == derived.account
    tampered = {**stored, "account": ["Invented."] + list(derived.account[1:])}
    with pytest.raises(ValueError):
        validate_escalation(tampered, _reports())
    with pytest.raises(ValueError):
        validate_escalation(
            {**stored, "report_ids": ["report-first", "report-note"]},
            _reports())
    with pytest.raises(ValueError):
        validate_escalation({**stored, "member": "scribe"}, _reports())
    with pytest.raises(ValueError):
        validate_escalation(filled)
    with pytest.raises(ValueError):
        validate_escalation({**stored, "surprise": 1}, _reports())
    with pytest.raises(ValueError):
        build_escalation({
            "member": "forge_worker", "slice_id": "M-139",
            "failure_key": "replay-gap",
            "report_ids": ["report-first", "report-first"],
            "account": ["A."]})


def test_book_validation_and_shared_view():
    book = validate_book(_book_data())
    assert book.title == "A fostering book"
    assert book.assignment_for("m-139").member == "forge_worker"
    assert book.report_for("report-note").member == "scribe"
    assert [r.report_id for r in book.reports_for("forge_worker")] == [
        "report-first", "report-second"]
    assert book.redeal_for("redeal-m139").foster_member == "auditor"
    assert book.escalation_for("escalation-m139").recipient == "human"
    assert build_book(_book_data()).title == "A fostering book"
    with pytest.raises(KeyError):
        book.report_for("report-missing")
    with pytest.raises(KeyError):
        book.assignment_for("M-140")


def test_book_refusals():
    data = _book_data()
    dup_slice = _book_data()
    dup_slice["assignments"] = data["assignments"] + [data["assignments"][0]]
    with pytest.raises(ValidationError):
        validate_book(dup_slice)
    dup_report = _book_data()
    dup_report["reports"] = data["reports"] + [data["reports"][0]]
    with pytest.raises(ValidationError):
        validate_book(dup_report)
    orphan_redeal = _book_data()
    orphan_redeal["reports"] = data["reports"][1:]
    with pytest.raises(ValidationError):
        validate_book(orphan_redeal)
    orphan_esc = _book_data()
    orphan_esc["escalations"] = [{
        **data["escalations"][0],
        "report_ids": ["report-missing", "report-second"]}]
    with pytest.raises(ValidationError):
        validate_book(orphan_esc)
    tampered = _book_data()
    tampered["redeals"] = [{
        **data["redeals"][0], "account": ["Invented."]}]
    with pytest.raises(ValidationError):
        validate_book(tampered)
    for bad in (
            {**data, "schema": "mythic.other/1"},
            {**data, "surprise": 1},
            {k: v for k, v in data.items() if k != "reports"},
            "not a mapping"):
        with pytest.raises(ValidationError):
            validate_book(bad)
    with pytest.raises(ValidationError):
        validate_book(_book_data(), require_example=True)
    with pytest.raises(ValueError):
        FosterBook(title="T", assignments=[], reports=_reports())


def test_file_loader_round_trip_and_missing_file(tmp_path):
    path = _write_book(tmp_path, _book_data())
    book = load_failure_fostering_file(path)
    assert book.title == "A fostering book"
    assert book.report_ids() == (
        "report-first", "report-second", "report-note")
    with pytest.raises(FileNotFoundError):
        load_failure_fostering_file(tmp_path / "missing.yaml")
    bad = _write_book(tmp_path, {"schema": "nope"})
    with pytest.raises(ValidationError):
        load_failure_fostering_file(bad)


def test_registry_hold_and_derivations():
    registry = FosterRegistry(load_failure_fostering())
    assert [r.report_id for r in registry.list_reports()] == [
        "report-first", "report-second", "report-note"]
    held = registry.book()
    assert held.title == load_failure_fostering().title
    # The registry holds dealings and reports, never
    # re-deals or escalations: both are derived.
    assert held.redeals == ()
    assert held.escalations == ()
    redeal = registry.redeal_for("M-139", "auditor")
    assert redeal.account == load_failure_fostering().redeal_for(
        "redeal-m139").account
    escalation = registry.escalation_for("report-first")
    assert escalation.report_ids == ("report-first", "report-second")
    with pytest.raises(ValueError):
        registry.escalation_for("report-note")
    with pytest.raises(KeyError):
        registry.get_report("report-missing")


def test_registry_auto_ids_and_refusals():
    registry = FosterRegistry()
    registry.register_assignment(_assignment())
    one = registry.register_report({
        "member": "forge_worker", "slice_id": "M-139",
        "failure_key": "replay-gap", "title": "One",
        "body": "First."})
    two = registry.register_report({
        "member": "forge_worker", "slice_id": "M-139",
        "failure_key": "replay-gap", "title": "Two",
        "body": "Second."})
    assert (one.report_id, two.report_id) == (
        "fostering-1", "fostering-2")
    derived = registry.escalation_for("fostering-1")
    assert derived.report_ids == ("fostering-1", "fostering-2")
    with pytest.raises(ValueError):
        registry.register_assignment(_assignment())
    registry.register_report(_report())
    with pytest.raises(ValueError):
        registry.register_report(_report())
    other = FosterRegistry(load_failure_fostering())
    with pytest.raises(ValueError):
        other.register_book(_book_data())


def test_records_are_session_news():
    book = load_failure_fostering()
    record = report_record(book.reports[0])
    assert record["type"] == "failure_report"
    assert record["slice"] == "M-139"
    assert record["news"] is True
    assert "replay-gap" in record["headline"]
    redeal = redeal_record(book.redeals[0])
    assert redeal["type"] == "failure_fostering_redeal"
    assert redeal["news"] is True
    assert "auditor" in redeal["headline"]
    assert redeal["assignment"]["member"] == "forge_worker"
    escalation = escalation_record(book.escalations[0], book)
    assert escalation["type"] == "failure_fostering_escalation"
    assert escalation["recipient"] == "human"
    assert escalation["report_ids"] == ["report-first", "report-second"]
    whole = book_record(book)
    assert whole["type"] == "failure_fostering_book"
    assert whole["report_count"] == 3
    assert whole["redeal_count"] == 1
    assert whole["escalation_count"] == 1


def test_plain_words_and_derived_plain_words():
    book = load_failure_fostering()
    words = plain_words(book.reports[0])
    assert words.startswith("forge_worker reported failure")
    assert "Replay gap found" in words
    redeal_words = redeal_plain_words(book)
    assert book.title in redeal_words
    assert "fostered by auditor" in redeal_words
    single = redeal_plain_words(book.redeals[0])
    assert "re-dealt to auditor" in single
    esc_words = escalation_plain_words(book.escalations[0])
    assert "escalates to the human" in esc_words
    assert "both reports attached" in esc_words


def test_formatters_and_screen():
    book = load_failure_fostering()
    assert format_report(book.reports[0]) == (
        "report-first: forge_worker [replay-gap] "
        "'Replay gap found' (M-139)")
    reports = format_reports(book)
    assert "report-note" in reports
    assert format_reports(book, "guardian") == (
        "No failure reports are held.")
    scribe_reports = format_reports(book, "scribe")
    assert "report-note" in scribe_reports
    assert "report-first" not in scribe_reports
    redeal = format_redeal(book)
    assert "forge_worker -> auditor" in redeal
    single = format_redeal(book.redeals[0])
    assert single.startswith("M-139 - forge_worker")
    escalation = format_escalation(book)
    assert "-> human" in escalation
    screen = format_fostering_screen()
    assert "Failure fostering (M-139)" in screen
    assert "report-first" in screen
    assert USAGE in screen


def test_parse_fostering_args_grammar():
    assert parse_fostering_args("") == ("show", None)
    assert parse_fostering_args(None) == ("show", None)
    assert parse_fostering_args("show") == ("show", None)
    assert parse_fostering_args("list") == ("show", None)
    assert parse_fostering_args("report report-first") == (
        "report", "report-first")
    assert parse_fostering_args("redeal m-139") == (
        "redeal", "M-139")
    assert parse_fostering_args("escalation report-second") == (
        "escalation", "report-second")
    for bad in ("report", "redeal", "escalation", "report a b",
                "redeal X-139", "dance", "show extra", 7):
        with pytest.raises(ValueError):
            parse_fostering_args(bad)


def test_no_live_roads_in_pure_layer():
    import mythic_agent.core.failure_fostering as module
    source = Path(module.__file__).read_text(encoding="utf-8")
    for banned in ("import subprocess", "import socket", "requests.",
                   "openai", "anthropic", "AgentManager",
                   "mythic_agent.agents", "mythic_agent.ui",
                   "WriteAheadLog", "from .journal import",
                   "def spawn", "def persist", "def execute",
                   "def deliver", "def send"):
        assert banned not in source
    record = _report().to_record()
    assert "delivered" not in record
    assert "executed" not in record
    redeal = derive_redeal(_assignment(), _report(), "auditor").to_record()
    assert "delivered" not in redeal
    assert redeal["report"]["failure_key"] == "replay-gap"


# -- agent layer -----------------------------------------------------------
#
# M-139 agent layer: the agent holds a
# FosterRegistry for the session (session state
# only, no new setting), dealings and reports are
# held by being registered - reports published as
# their report_record session news through the
# checkpoint road, deduped per report id - the
# report road renders the held book (or the shipped
# example when unheld) through the pure formatters,
# and the /foster surface rides both roads on the
# pure parser + formatters. Status, get, assignment,
# re-deal and escalation reads register and publish
# nothing, answer from the held registry first and
# from the shipped example only while nothing is
# held - a held session never falls back to the
# example. This layer re-deals no task to a live
# agent, delivers no escalation, spawns no agent,
# persists nothing, calls no model and claims no
# board - Part VIII does not exist yet, so the
# screen is where the fostering is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _fostering_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


class TestFailureFosteringAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.failure_fostering_status()
        assert status["assignments"] == []
        assert status["reports"] == []
        assert status["book"] is None
        assert status["fostering"]["title"] == (
            "Failure fostering at the M-138 slice boundary")
        assert [a["slice_id"] for a in status["fostering"]["assignments"]] == [
            "M-139", "M-138"]
        assert [r["report_id"] for r in status["fostering"]["reports"]] == [
            "report-first", "report-second", "report-note"]
        assert status["book_record"]["type"] == "failure_fostering_book"
        assert status["book_record"]["report_count"] == 3
        assert [r["redeal_id"] for r in status["redeals"]] == ["redeal-m139"]
        assert [e["escalation_id"] for e in status["escalations"]] == [
            "escalation-m139"]
        assert "forge_worker reported failure 'replay-gap'" in \
            status["plain_words"][0]
        assert "fostered by auditor" in status["redeal_plain_words"]
        assert "escalated by forge_worker" in \
            status["escalation_plain_words"]
        assert "Failure fostering (M-139)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert agent._failure_fostering_registry() is \
            agent._failure_fostering_registry()
        assert agent._failure_fostering_store is \
            agent._failure_fostering_registry()

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.failure_fostering_status()
        report = agent.get_failure_report("report-first")
        assert report.member == "forge_worker"
        assert report.failure_key == "replay-gap"
        dealt = agent.get_fostering_assignment("M-139")
        assert dealt.member == "forge_worker"
        assert dealt.assignment_id == "assign-m139-forge"
        redeal = agent.fostering_redeal("M-139", "auditor")
        assert redeal.foster_member == "auditor"
        assert redeal.account[-1] == (
            "The task is re-dealt to auditor with its "
            "failure report attached.")
        escalation = agent.fostering_escalation("report-first")
        assert escalation.report_ids == ("report-first", "report-second")
        assert escalation.recipient == "human"
        assert agent.failure_fostering().title == (
            "Failure fostering at the M-138 slice boundary")
        registry = agent._failure_fostering_registry()
        assert registry.list_assignments() == ()
        assert registry.list_reports() == ()
        assert _fostering_events(store, session_id, "failure_report") == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_failure_report("no-such-report")
        with pytest.raises(KeyError):
            agent.get_fostering_assignment("M-200")
        with pytest.raises(KeyError):
            agent.fostering_redeal("M-200", "auditor")
        with pytest.raises(KeyError):
            agent.fostering_escalation("no-such-report")
        # One report alone never escalates.
        with pytest.raises(ValueError):
            agent.fostering_escalation("report-note")

    def test_status_after_register_shows_the_held_pieces(self, agent):
        agent.register_fostering_assignment(_assignment())
        agent.register_failure_report(_report())
        status = agent.failure_fostering_status()
        assert [a["slice_id"] for a in status["assignments"]] == ["M-139"]
        assert [r["report_id"] for r in status["reports"]] == ["report-first"]
        assert status["book"]["report_count"] == 1
        # The held book answers now, not the example:
        # records held one by one stand under a session
        # fostering book, and it holds no re-deals or
        # escalations - both stay derivations.
        assert status["fostering"]["title"] == "Session fostering book"
        assert status["redeals"] == []
        assert status["escalations"] == []
        assert "report-first" in status["screen"]

    def test_held_session_never_falls_back_to_the_example(self, agent):
        agent.register_fostering_assignment(_assignment())
        agent.register_failure_report(_report())
        with pytest.raises(KeyError):
            agent.get_failure_report("report-second")
        with pytest.raises(KeyError):
            agent.get_fostering_assignment("M-138")
        with pytest.raises(KeyError):
            agent.fostering_redeal("M-138", "auditor")
        # The one held report is the same failure only
        # once: it cannot escalate from held records.
        with pytest.raises(ValueError):
            agent.fostering_escalation("report-first")
        assert agent.failure_fostering().report_ids() == ("report-first",)
        assert agent.get_failure_report("report-first").member == \
            "forge_worker"
        redeal = agent.fostering_redeal("M-139", "auditor")
        assert redeal.report.report_id == "report-first"


class TestFailureFosteringAgentRegister:
    def test_register_report_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_failure_report(_report())
        assert outcome["report"]["report_id"] == "report-first"
        assert outcome["record"]["type"] == "failure_report"
        events = _fostering_events(store, session_id, "failure_report")
        assert len(events) == 1
        assert events[0]["report_id"] == "report-first"
        # The same record is never published twice.
        agent._publish_failure_fostering_record(outcome["record"])
        assert len(_fostering_events(
            store, session_id, "failure_report")) == 1
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
        from mythic_agent.core.crew_replay import (
            book_record as _replay_book_record,
            load_crew_replay,
            step_record as _replay_step_record,
            trace_record as _replay_trace_record,
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
        agent._publish_failure_fostering_record(profile_record(
            load_character_voices().profiles[0]))
        agent._publish_failure_fostering_record(_sizing_case_record(
            load_crew_sizing().cases[0]))
        agent._publish_failure_fostering_record({
            "type": "crew_sizing_recommendation_set"})
        agent._publish_failure_fostering_record(_stand_up_entry_record(
            load_stand_up().entries[0]))
        memory = load_crew_memory()
        agent._publish_failure_fostering_record(_memory_entry_record(
            memory.entry_for("broken-checkpoint-chain")))
        panel = load_review_panel()
        agent._publish_failure_fostering_record(review_record(
            panel.reviews[0]))
        agent._publish_failure_fostering_record(casting_record(
            load_casting().members[0]))
        external = load_external_agents()
        agent._publish_failure_fostering_record(_external_seat_record(
            external.seats[0]))
        agent._publish_failure_fostering_record(
            _external_book_record(external))
        agent._publish_failure_fostering_record(_external_check_record(
            check_seat(external.seats[0])))
        replay = load_crew_replay()
        agent._publish_failure_fostering_record(_replay_step_record(
            replay.steps[0]))
        agent._publish_failure_fostering_record(
            _replay_book_record(replay))
        agent._publish_failure_fostering_record(_replay_trace_record(
            replay.trace_for("trace-replay-decision"), replay))
        book = load_failure_fostering()
        agent._publish_failure_fostering_record(book_record(book))
        agent._publish_failure_fostering_record(redeal_record(
            book.redeals[0]))
        agent._publish_failure_fostering_record(escalation_record(
            book.escalations[0], list(book.reports)))
        for kind in ("character_voice_profile", "crew_sizing_case",
                     "crew_sizing_recommendation_set", "stand_up_entry",
                     "crew_memory_entry", "panel_review", "crew_member",
                     "external_seat", "external_seat_book",
                     "external_seat_check", "crew_replay_step",
                     "crew_replay_book", "crew_replay_trace",
                     "failure_fostering_book",
                     "failure_fostering_redeal",
                     "failure_fostering_escalation"):
            assert _fostering_events(store, session_id, kind) == []
        assert len(_fostering_events(
            store, session_id, "failure_report")) == 1
        agent.close()

    def test_duplicate_holdings_refuse_and_publish_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_fostering_assignment(_assignment())
        agent.register_failure_report(_report())
        with pytest.raises(ValueError):
            agent.register_fostering_assignment(_assignment())
        with pytest.raises(ValueError):
            agent.register_failure_report(_report())
        assert len(_fostering_events(
            store, session_id, "failure_report")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_fostering_book(load_failure_fostering())
        assert outcome["count"] == 3
        assert outcome["book"]["report_count"] == 3
        events = _fostering_events(store, session_id, "failure_report")
        assert [e["report_id"] for e in events] == [
            "report-first", "report-second", "report-note"]
        assert agent.failure_fostering().title == (
            "Failure fostering at the M-138 slice boundary")
        assert agent.get_failure_report("report-note").member == "scribe"
        # The registry holds dealings and reports, never
        # re-deals or escalations: both are derived at
        # call time from the held records.
        assert agent.failure_fostering().redeals == ()
        assert agent.fostering_redeal(
            "M-139", "auditor").foster_member == "auditor"
        assert agent.fostering_escalation(
            "report-first").report_ids == (
                "report-first", "report-second")
        agent.close()

    def test_register_book_twice_refuses(self, agent):
        agent.register_fostering_book(load_failure_fostering())
        with pytest.raises(ValueError):
            agent.register_fostering_book(load_failure_fostering())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_fostering_book()
        assert outcome["count"] == 3
        assert outcome["book"]["report_count"] == 3
        events = _fostering_events(store, session_id, "failure_report")
        assert [e["report_id"] for e in events] == [
            "report-first", "report-second", "report-note"]
        assert agent.failure_fostering().title == (
            "Failure fostering at the M-138 slice boundary")
        assert agent.get_fostering_assignment("M-138").member == "scribe"
        # The recorded book stands whole: its held
        # re-deal and escalation still answer.
        assert agent.failure_fostering().redeals[0].redeal_id == \
            "redeal-m139"
        assert agent.failure_fostering().escalations[0].escalation_id == \
            "escalation-m139"
        assert agent.fostering_escalation(
            "report-second").report_ids == (
                "report-first", "report-second")
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_fostering_book()
        with pytest.raises(ValueError):
            agent.record_fostering_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_book(tmp_path, _book_data())
        book = load_failure_fostering_file(path)
        outcome = agent.record_fostering_book(book)
        assert outcome["count"] == 3
        assert agent.failure_fostering().title == "A fostering book"
        assert agent.get_failure_report("report-note").failure_key == \
            "trace-slip"
        assert agent.fostering_redeal(
            "M-139", "auditor").account[0].startswith("Slice M-139")

    def test_one_by_one_holdings_stand_under_a_session_book(
            self, agent):
        agent.register_fostering_assignment(_assignment())
        agent.register_failure_report(_report())
        # Held one by one, the records stand under a
        # session fostering book composed in the agent
        # layer - never under a recorded book's title.
        assert agent.failure_fostering().title == \
            "Session fostering book"
        agent.register_fostering_assignment(_assignments()[1])
        agent.register_failure_report(_reports()[2])
        assert [a.slice_id for a in
                agent.failure_fostering().assignments] == [
                    "M-139", "M-138"]
        # A whole book recorded now would re-hold the
        # same slices and report ids: the registry
        # refuses it, as it refuses any duplicate.
        with pytest.raises(ValueError):
            agent.record_fostering_book()

    def test_partial_holding_answers_without_a_whole_book(
            self, agent):
        agent.register_failure_report(_report())
        # Only one side of the book stands held, so no
        # whole book can stand - and none is claimed.
        assert agent.failure_fostering() is None
        status = agent.failure_fostering_status()
        assert status["book"] is None
        assert status["fostering"]["title"] is None
        assert [r["report_id"] for r in status["reports"]] == [
            "report-first"]
        assert "report-first" in status["screen"]
        assert agent.get_failure_report("report-first").member == \
            "forge_worker"
        outcome = agent.report_failure_fostering()
        assert outcome["book"] is None
        assert "report-first" in outcome["reports_text"]


class TestFailureFosteringAgentReport:
    def test_report_renders_the_example_when_unheld(self, agent):
        outcome = agent.report_failure_fostering()
        assert outcome["book"]["title"] == (
            "Failure fostering at the M-138 slice boundary")
        assert outcome["book"]["report_count"] == 3
        assert "report-first" in outcome["reports_text"]
        assert "report-note" in outcome["reports_text"]
        assert "auditor" in outcome["redeal_text"]
        assert "replay-gap" in outcome["escalation_text"]
        assert "Failure fostering (M-139)" in outcome["screen"]
        assert outcome["explanation"] == PLAIN_EXPLANATION

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_fostering_assignment(_assignment())
        agent.register_failure_report(_report())
        outcome = agent.report_failure_fostering()
        assert outcome["book"]["report_count"] == 1
        assert "report-first" in outcome["reports_text"]
        assert "report-note" not in outcome["reports_text"]
        assert "Nothing here." in outcome["redeal_text"]
        assert "Nothing here." in outcome["escalation_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_failure_fostering()
        registry = agent._failure_fostering_registry()
        assert registry.list_assignments() == ()
        assert registry.list_reports() == ()
        assert _fostering_events(store, session_id, "failure_report") == []
        agent.close()

    def test_no_live_redeal_deliver_or_model_road(self, agent):
        # This layer holds the fostering as data: it
        # re-deals no task to a live agent, delivers no
        # escalation, spawns no agent, persists nothing
        # and calls no model - and there is no Part
        # VIII board yet.
        assert not hasattr(agent, "generate_failure_fostering")
        assert not hasattr(agent, "persist_failure_fostering")
        assert not hasattr(agent, "deliver_failure_escalation")
        assert not hasattr(agent, "redeal_live_task")
        assert not hasattr(agent, "spawn_fostering")
        assert not hasattr(agent, "read_live_crew")
        assert not hasattr(agent, "failure_fostering_board")


class TestFailureFosteringTerminalSurface:
    def test_show_report_redeal_and_escalation(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/foster")
        assert "Failure fostering (M-139)" in text
        _, _, text = _slash(agent, "/foster report report-first")
        assert "report-first: forge_worker" in text
        assert "[replay-gap]" in text
        _, _, text = _slash(agent, "/foster redeal M-139")
        assert "M-139 - forge_worker -> auditor" in text
        _, _, text = _slash(agent, "/foster escalation report-first")
        assert "replay-gap on M-139" in text
        assert "escalates to the human" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/foster [show|report <report-id>|redeal <slice-id>|"
                "escalation <report-id>]") in text
        _, _, text = _slash(agent, "/foster dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/foster report missing-report")
        assert "no report in the book" in text


@pytest.fixture()
def foster_handler(agent, monkeypatch):
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


def _foster_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestFailureFosteringCommand:
    def test_show_is_default(self, foster_handler, agent):
        foster_handler._handle_foster("")
        assert "Failure fostering (M-139)" in \
            _foster_published_text(foster_handler)

    def test_report_redeal_and_escalation(self, foster_handler, agent):
        foster_handler._handle_foster("report report-first")
        assert "forge_worker" in _foster_published_text(foster_handler)
        foster_handler._handle_foster("redeal M-139")
        assert "forge_worker -> auditor" in \
            _foster_published_text(foster_handler)
        foster_handler._handle_foster("escalation report-first")
        assert "replay-gap on M-139" in \
            _foster_published_text(foster_handler)

    def test_bad_grammar_is_published(self, foster_handler, agent):
        foster_handler._handle_foster("dance party")
        assert USAGE in _foster_published_text(foster_handler)


class TestChatScreenRoutingFoster:
    def test_foster_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/foster report report-first", _FakeLog())
        assert calls == [("/foster", "report report-first")]
