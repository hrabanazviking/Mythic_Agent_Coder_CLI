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
