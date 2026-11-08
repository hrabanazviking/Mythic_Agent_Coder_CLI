"""M-145 Crew on schedule - pure-layer tests.

TIER: integration

The pure layer is the crew-on-schedule attachments
as data: a crew schedule book of attachment
records (one formation attached to one Part V
scheduled job, the job held whole as M-105 data -
what it runs, when it runs, whether it is enabled
and its approval posture), the shipped example
attachment book held in a data file, a loader that
reads a schedule book from any file, per-attachment
reports whose checks, standing, action and account
are derived from the attachment's job, the
attachment index whose rows, totals and account
are derived from the whole book, records shaped as
session news, and a registry. Nothing here starts
a timer, runs a job, summons a crew, spawns an
agent or persists anything: a stored report
disagreeing with the report derived from its own
attachment is refused, and a stored index
disagreeing with the index derived from its book
is refused. Standing is derived from the held
job, never stored loose: a stored standing key on
a record refuses as an unknown key.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.validation import ValidationError
from mythic_agent.core.crew_schedules import (
    PLAIN_EXPLANATION,
    CREW_SCHEDULES_RESOURCE,
    CREW_SCHEDULES_SCHEMA,
    CREW_SCHEDULES_SLICE,
    STANDINGS,
    USAGE,
    AttachmentIndex,
    AttachmentReport,
    CrewAttachment,
    CrewScheduleBook,
    CrewScheduleRegistry,
    attachment_record,
    book_record,
    build_attachment,
    build_book,
    build_index,
    build_report,
    derive_index,
    derive_report,
    format_attachment,
    format_attachments,
    format_crew_schedules_screen,
    format_index,
    format_report,
    index_plain_words,
    index_record,
    load_crew_schedules,
    load_crew_schedules_file,
    parse_crew_schedules_args,
    plain_words,
    report_plain_words,
    report_record,
    validate_book,
    validate_index,
    validate_attachment,
    validate_report,
)

ROOT = Path(__file__).resolve().parents[1]


def _job(**kwargs):
    job = {
        "job_id": "dawn-auditor-sweep",
        "label": "Auditor sweep over yesterday's commits",
        "argv": ["git", "log", "--since=yesterday", "--oneline"],
        "schedule": {"kind": "daily", "time": "06:00"},
        "enabled": True,
        "approval": "unattended"}
    job.update(kwargs)
    return job


def _attachment(**kwargs):
    kwargs.setdefault("attachment_id", "att-dawn-auditor-sweep")
    kwargs.setdefault("template", "review_panel")
    kwargs.setdefault("template_id", "tpl-review-panel")
    kwargs.setdefault("title", "Dawn Auditor sweep")
    kwargs.setdefault(
        "detail", "At dawn the Review Panel sweeps yesterday's commits.")
    kwargs.setdefault("job", _job())
    return CrewAttachment(**kwargs)


def _attachments():
    return [
        _attachment(),
        CrewAttachment(
            attachment_id="att-weekly-full-six", template="full_six",
            template_id="tpl-full-six", title="Weekly Full Six review",
            detail="Once a week the Full Six stands over the tests.",
            job=_job(
                job_id="weekly-full-six", label="Full Six weekly review",
                argv=["python", "-m", "pytest", "-q"],
                schedule={"kind": "weekly", "weekday": "monday",
                          "time": "09:00"},
                approval="needs_approval")),
        CrewAttachment(
            attachment_id="att-research-swarm-watch",
            template="research_swarm", template_id="tpl-research-swarm",
            title="Research Swarm upstream watch",
            detail="Every twelve hours the Swarm reads upstream.",
            job=_job(
                job_id="research-swarm-watch", label="Upstream watch",
                argv=["git", "log", "--oneline", "-20"],
                schedule={"kind": "interval", "every_hours": 12,
                          "anchor": "2026-01-01T00:00:00"})),
        CrewAttachment(
            attachment_id="att-weekend-duo-paused", template="duo",
            template_id="tpl-duo", title="Weekend Duo sweep (paused)",
            detail="The Duo would sweep the weekend diff on Saturday.",
            job=_job(
                job_id="weekend-duo-sweep", label="Duo weekend sweep",
                argv=["git", "diff", "--stat"],
                schedule={"kind": "weekly", "weekday": "saturday",
                          "time": "08:00"},
                enabled=False)),
    ]


def _report_mapping(report):
    mapping = {
        "attachment_id": report.attachment_id,
        "template": report.template,
        "job_id": report.job_id,
        "schedule_text": report.schedule_text,
        "checks": list(report.checks),
        "standing": report.standing,
        "action": report.action,
        "account": list(report.account)}
    if report.template_id is not None:
        mapping["template_id"] = report.template_id
    return mapping


def test_constants_and_usage():
    assert CREW_SCHEDULES_SLICE == "M-145"
    assert CREW_SCHEDULES_SCHEMA == "mythic.crew_schedules/1"
    assert CREW_SCHEDULES_RESOURCE == "crew_schedules.yaml"
    assert STANDINGS == ("armed", "waiting_for_approval", "disabled")
    assert "formations can be attached" in PLAIN_EXPLANATION
    assert "data" in PLAIN_EXPLANATION and "only" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /crewschedules")
    assert "/crewschedules attachment <attachment-id>" in USAGE
    assert "/crewschedules job <job-id>" in USAGE
    assert "/crewschedules index" in USAGE


def test_shipped_example_shape():
    book = load_crew_schedules()
    assert isinstance(book, CrewScheduleBook)
    assert book.title == "Crew schedule book at the M-144 slice boundary"
    assert book.attachment_ids() == (
        "att-dawn-auditor-sweep", "att-weekly-full-six",
        "att-research-swarm-watch", "att-weekend-duo-paused")
    assert book.template_words() == (
        "review_panel", "full_six", "research_swarm", "duo")
    assert book.job_ids() == (
        "dawn-auditor-sweep", "weekly-full-six",
        "research-swarm-watch", "weekend-duo-sweep")
    assert book.standings() == (
        "armed", "waiting_for_approval", "armed", "disabled")
    assert [e.action for e in book.entries] == [
        "run", "await_approval", "run", "none"]
    first = book.entries[0]
    assert first.template == "review_panel"
    assert first.job.argv == (
        "git", "log", "--since=yesterday", "--oneline")
    assert first.schedule_text == "daily at 06:00"
    assert book.attachment_for(
        "att-weekly-full-six").job.requires_approval is True
    assert book.attachment_for_job(
        "research-swarm-watch").template == "research_swarm"
    assert [e.attachment_id for e in
            book.attachments_for_template("duo")] == [
        "att-weekend-duo-paused"]
    assert [e.attachment_id for e in
            book.attachments_with_standing("armed")] == [
        "att-dawn-auditor-sweep", "att-research-swarm-watch"]
    with pytest.raises(KeyError):
        book.attachment_for("att-nope")
    with pytest.raises(KeyError):
        book.attachment_for_job("nope")


def test_shipped_index():
    book = load_crew_schedules()
    assert [i.index_id for i in book.indexes] == ["index-m144-boundary"]
    index = book.index_for("index-m144-boundary")
    assert isinstance(index, AttachmentIndex)
    assert [r.template for r in index.rows] == [
        "review_panel", "full_six", "research_swarm", "duo"]
    assert index.total_attachments == 4
    assert index.total_armed == 2
    assert index.total_waiting == 1
    assert index.total_disabled == 1
    assert index.total_templates == 4
    derived = derive_index(book.entries)
    assert derived.rows == index.rows
    assert derived.account == index.account
    first = derive_report(book.entries[0])
    assert first.checks == (
        "formation review_panel: attached by name",
        "schedule daily at 06:00: stated",
        "approval unattended: runs when its moment comes")
    assert first.account[0] == (
        "Formation review_panel is attached to scheduled job "
        "dawn-auditor-sweep: daily at 06:00, running when its "
        "moment comes.")
    assert index.row_for("att-weekly-full-six").standing == (
        "waiting_for_approval")


def test_record_validation_and_aliases():
    record = validate_attachment({
        "id": "att-dawn-auditor-sweep", "formation": "review_panel",
        "headline": "Dawn Auditor sweep",
        "description": "At dawn the Panel sweeps the commits.",
        "scheduled_job": _job()})
    assert isinstance(record, CrewAttachment)
    assert record.attachment_id == "att-dawn-auditor-sweep"
    assert record.template == "review_panel"
    assert record.job_id == "dawn-auditor-sweep"
    assert record.standing == "armed" and record.action == "run"
    record = record.to_record()
    assert record["type"] == "crew_schedule_attachment"
    assert record["slice"] == "M-145"
    assert record["job"]["type"] == "scheduled_job"
    assert record["schedule_text"] == "daily at 06:00"


def test_two_spellings_refusals():
    with pytest.raises(ValueError):
        validate_attachment({
            "template": "duo", "formation": "full_six",
            "title": "T", "detail": "D", "job": _job()})
    with pytest.raises(ValueError):
        validate_attachment({
            "template": "duo", "title": "T", "headline": "Other",
            "detail": "D", "job": _job()})
    with pytest.raises(ValueError):
        validate_attachment({
            "template": "duo", "title": "T", "detail": "D",
            "job": _job(), "scheduled_job": _job(job_id="other-job")})


def test_unknown_key_refusals():
    base = {"template": "duo", "title": "T", "detail": "D", "job": _job()}
    for key in ("standing", "status", "action", "schedule_text",
                "armed", "members", "size"):
        with pytest.raises(ValueError):
            validate_attachment({**base, key: "armed"})
    with pytest.raises(ValueError):
        validate_attachment({**base, "bogus": 1})


def test_one_job_one_formation():
    entries = _attachments()
    clash = CrewAttachment(
        attachment_id="att-other", template="duo", title="Other",
        detail="A second formation on the dawn job.",
        job=_job())
    with pytest.raises(ValueError):
        CrewScheduleBook(title="Clash", entries=[entries[0], clash])
    registry = CrewScheduleRegistry()
    registry.register_attachment(entries[0])
    with pytest.raises(ValueError):
        registry.register_attachment(clash)


def test_malformed_records():
    with pytest.raises(ValueError):
        validate_attachment({
            "template": "not a word!", "title": "T", "detail": "D",
            "job": _job()})
    with pytest.raises(ValueError):
        validate_attachment({
            "template": "duo", "title": "", "detail": "D", "job": _job()})
    with pytest.raises(ValueError):
        validate_attachment({"template": "duo", "title": "T", "detail": "D"})
    unnamed = _job()
    del unnamed["job_id"]
    with pytest.raises(ValueError):
        validate_attachment({
            "template": "duo", "title": "T", "detail": "D", "job": unnamed})
    with pytest.raises(ValueError):
        validate_attachment({
            "template": "duo", "title": "T", "detail": "D",
            "job": _job(argv="git log --since=yesterday")})
    with pytest.raises(ValueError):
        validate_attachment({
            "template": "duo", "title": "T", "detail": "D",
            "job": _job(schedule={"kind": "daily", "time": "dawn"})})
    with pytest.raises(ValueError):
        validate_attachment({
            "template": "duo", "title": "T", "detail": "D",
            "job": _job(bogus=1)})
    with pytest.raises(ValueError):
        validate_attachment("not a mapping")


def test_standing_derivation():
    assert _attachment().standing == "armed"
    assert _attachment().action == "run"
    waiting = _attachment(job=_job(approval="needs_approval"))
    assert waiting.standing == "waiting_for_approval"
    assert waiting.action == "await_approval"
    disabled = _attachment(job=_job(enabled=False))
    assert disabled.standing == "disabled"
    assert disabled.action == "none"
    disabled_waiting = _attachment(
        job=_job(enabled=False, approval="needs_approval"))
    assert disabled_waiting.standing == "disabled"
    assert disabled_waiting.checks[2] == "job disabled: does not run"


def test_report_derivation():
    report = derive_report(_attachment())
    assert isinstance(report, AttachmentReport)
    assert report.template == "review_panel"
    assert report.job_id == "dawn-auditor-sweep"
    assert report.standing == "armed" and report.armed is True
    assert report.account[1] == (
        "The attachment keeps the scheduled job's own approval "
        "line: unattended work runs when due, exactly as live "
        "work would.")
    waiting = derive_report(_attachments()[1])
    assert waiting.standing == "waiting_for_approval"
    assert "never run unattended" in waiting.account[1]
    disabled = derive_report(_attachments()[3])
    assert disabled.standing == "disabled"
    assert disabled.checks[2] == "job disabled: does not run"
    assert disabled.to_record()["type"] == "crew_schedule_report"


def test_stored_report_judged():
    attachment = _attachment()
    report = derive_report(attachment)
    assert validate_report(_report_mapping(report), attachment) == report
    bad = _report_mapping(report)
    bad["standing"] = "disabled"
    bad["action"] = "none"
    bad["checks"] = [
        "formation review_panel: attached by name",
        "schedule daily at 06:00: stated", "job disabled: does not run"]
    with pytest.raises(ValueError):
        validate_report(bad, attachment)
    bad = _report_mapping(report)
    bad["account"] = ["A different account."]
    with pytest.raises(ValueError):
        validate_report(bad, attachment)


def test_accountless_report_refusal():
    mapping = _report_mapping(derive_report(_attachment()))
    del mapping["account"]
    with pytest.raises(ValueError):
        validate_report(mapping)


def test_report_action_must_match_its_standing():
    with pytest.raises(ValueError):
        AttachmentReport(
            template="duo", job_id="weekend-duo-sweep",
            schedule_text="weekly on saturday at 08:00",
            checks=["formation duo: attached by name",
                    "schedule weekly on saturday at 08:00: stated",
                    "job disabled: does not run"],
            standing="disabled", action="run",
            account=["An account."])
    with pytest.raises(ValueError):
        AttachmentReport(
            template="duo", job_id="weekend-duo-sweep",
            schedule_text="weekly on saturday at 08:00",
            checks=["formation duo: attached by name",
                    "schedule weekly on saturday at 08:00: stated",
                    "approval unattended: runs when its moment comes"],
            standing="disabled", action="none",
            account=["An account."])
    with pytest.raises(ValueError):
        AttachmentReport(
            template="duo", job_id="weekend-duo-sweep",
            schedule_text="weekly on saturday at 08:00",
            checks=["formation duo: attached by name"],
            standing="disabled", action="none",
            account=["An account."])
    with pytest.raises(ValueError):
        AttachmentReport(
            template="duo", job_id="weekend-duo-sweep",
            schedule_text="weekly on saturday at 08:00",
            checks=["formation full_six: attached by name",
                    "schedule weekly on saturday at 08:00: stated",
                    "job disabled: does not run"],
            standing="disabled", action="none",
            account=["An account."])


def test_index_derivation():
    entries = _attachments()
    index = derive_index(entries)
    assert index.total_attachments == 4
    assert index.total_armed == 2
    assert index.total_waiting == 1
    assert index.total_disabled == 1
    assert index.total_templates == 4
    assert index.row_for("att-dawn-auditor-sweep").template == "review_panel"
    with pytest.raises(KeyError):
        index.row_for("att-nope")
    pair = derive_index([entries[0], CrewAttachment(
        attachment_id="att-dawn-duo", template="review_panel",
        title="Dawn Panel again", detail="The Panel on another job.",
        job=_job(job_id="another-dawn-job"))])
    assert pair.total_attachments == 2
    assert pair.total_templates == 1
    with pytest.raises(ValueError):
        derive_index([])


def test_stored_index_judged():
    entries = _attachments()
    index = derive_index(entries)
    mapping = {
        "rows": [_report_mapping(r) for r in index.rows],
        "total_attachments": 4, "total_armed": 2, "total_waiting": 1,
        "total_disabled": 1, "total_templates": 4,
        "account": list(index.account)}
    assert validate_index(mapping, entries) == index
    bad = dict(mapping, total_armed=3)
    with pytest.raises(ValueError):
        validate_index(bad, entries)
    bad = dict(mapping, account=["A different account."])
    with pytest.raises(ValueError):
        validate_index(bad, entries)
    with pytest.raises(ValueError):
        AttachmentIndex(
            rows=index.rows, total_attachments=4, total_armed=1,
            total_waiting=1, total_disabled=1, total_templates=4,
            account=list(index.account))


def test_duplicate_refusals():
    entries = _attachments()
    with pytest.raises(ValueError):
        CrewScheduleBook(title="Dup", entries=[entries[0], entries[0]])
    index = derive_index(entries[:1])
    first = AttachmentIndex(
        rows=index.rows, total_attachments=1, total_armed=1,
        total_waiting=0, total_disabled=0, total_templates=1,
        account=list(index.account), index_id="index-one")
    with pytest.raises(ValueError):
        CrewScheduleBook(
            title="Dup index", entries=entries[:1],
            indexes=[first, first])


def test_book_index_disagreement_refuses():
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / "crew_schedules.yaml")
        .read_text(encoding="utf-8"))
    raw["indexes"][0]["total_armed"] = 3
    with pytest.raises(ValidationError):
        validate_book(raw)
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / "crew_schedules.yaml")
        .read_text(encoding="utf-8"))
    raw["schema"] = "mythic.other/1"
    with pytest.raises(ValidationError):
        validate_book(raw)


def test_file_loader_round_trip_and_missing(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / "crew_schedules.yaml").read_text(
        encoding="utf-8")
    path = tmp_path / "crew_schedules.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_crew_schedules_file(path)
    assert book.title == "Crew schedule book at the M-144 slice boundary"
    assert book.attachment_ids() == load_crew_schedules().attachment_ids()
    with pytest.raises(FileNotFoundError):
        load_crew_schedules_file(tmp_path / "nope.yaml")


def test_registry_auto_ids_and_duplicates():
    registry = CrewScheduleRegistry()
    first = registry.register_attachment({
        "template": "duo", "title": "One", "detail": "First.",
        "job": _job(job_id="job-one")})
    second = registry.register_attachment({
        "template": "duo", "title": "Two", "detail": "Second.",
        "job": _job(job_id="job-two")})
    assert first.attachment_id == "attachment-1"
    assert second.attachment_id == "attachment-2"
    assert registry.get_for_job("job-two").attachment_id == "attachment-2"
    with pytest.raises(ValueError):
        registry.register_attachment({
            "template": "full_six", "title": "Clash", "detail": "Same job.",
            "job": _job(job_id="job-one")})
    with pytest.raises(KeyError):
        registry.get_attachment("att-nope")
    with pytest.raises(ValueError):
        registry.book()
    registry2 = CrewScheduleRegistry()
    registry2.register_attachment(_attachment())
    with pytest.raises(ValueError):
        registry2.register_attachment(_attachment())
    assert registry2.report_for(
        "att-dawn-auditor-sweep").standing == "armed"
    assert registry2.index().total_attachments == 1
    assert [e.attachment_id for e in registry2.list_attachments()] == [
        "att-dawn-auditor-sweep"]


def test_registry_book_title_clash():
    registry = CrewScheduleRegistry()
    registry.register_book(load_crew_schedules())
    other = CrewScheduleBook(
        title="Another book",
        entries=[CrewAttachment(
            attachment_id="att-x", template="duo", title="X",
            detail="Another book's attachment.", job=_job(job_id="job-x"))])
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_session_news_records():
    attachment = _attachment()
    record = attachment_record(attachment)
    assert record["type"] == "crew_schedule_attachment"
    assert record["news"] is True
    assert "runs when its moment comes" in record["headline"]
    disabled = attachment_record(_attachments()[3])
    assert "disabled" in disabled["headline"]
    report = report_record(derive_report(attachment))
    assert report["type"] == "crew_schedule_report"
    assert "armed to run when due" in report["headline"]
    index = index_record(derive_index(_attachments()))
    assert index["type"] == "crew_schedule_index"
    assert index["total_attachments"] == 4
    book = book_record(load_crew_schedules())
    assert book["type"] == "crew_schedule_book"
    assert book["attachment_count"] == 4
    assert book["index_count"] == 1


def test_plain_words():
    words = plain_words(_attachment())
    assert "Dawn Auditor sweep" in words
    assert "daily at 06:00" in words
    assert "armed to run when due" in words
    book = load_crew_schedules()
    reports = report_plain_words(book)
    assert "Crew schedule book at the M-144 slice boundary" in reports
    assert "Formation full_six on job weekly-full-six" in reports
    index_words = index_plain_words(book)
    assert "Attachment index:" in index_words
    assert "The book holds 4 crew schedule attachment(s)" in index_words


def test_formatters_and_screen():
    book = load_crew_schedules()
    line = format_attachment(book.entries[0])
    assert line.startswith("att-dawn-auditor-sweep: review_panel")
    assert "armed to run when due" in line
    only_duo = format_attachments(book, template="duo")
    assert "att-weekend-duo-paused" in only_duo
    assert "att-dawn-auditor-sweep" not in only_duo
    armed = format_attachments(book, standing="armed")
    assert "att-research-swarm-watch" in armed
    assert "att-weekend-duo-paused" not in armed
    report_text = format_report(book)
    assert "Attachment reports in" in report_text
    assert "Formation review_panel on job dawn-auditor-sweep" in report_text
    index_text = format_index(book)
    assert "Attachment index:" in index_text
    screen = format_crew_schedules_screen(book)
    assert "Crew on schedule (M-145)" in screen
    assert USAGE in screen
    assert "No attachment records are held." in format_attachments(
        book, template="full_six", standing="disabled")


def test_parser_grammar():
    assert parse_crew_schedules_args("") == ("show", None)
    assert parse_crew_schedules_args("show") == ("show", None)
    assert parse_crew_schedules_args("list") == ("show", None)
    assert parse_crew_schedules_args(
        "attachment att-dawn-auditor-sweep") == (
        "attachment", "att-dawn-auditor-sweep")
    assert parse_crew_schedules_args("template review_panel") == (
        "template", "review_panel")
    assert parse_crew_schedules_args("job dawn-auditor-sweep") == (
        "job", "dawn-auditor-sweep")
    assert parse_crew_schedules_args(
        "report att-dawn-auditor-sweep") == (
        "report", "att-dawn-auditor-sweep")
    assert parse_crew_schedules_args("index") == ("index", None)
    for bad in ("dance", "attachment", "job", "index now",
                "template two words", "attachment bad id!"):
        with pytest.raises(ValueError):
            parse_crew_schedules_args(bad)


def test_builders_from_field_words():
    record = build_attachment({
        "template": "duo", "title": "Weekend Duo",
        "detail": "The Duo on the weekend job.",
        "job": _job(job_id="weekend-job", enabled=False)})
    assert record.standing == "disabled"
    report = build_report(
        template="duo", job_id="weekend-job",
        schedule_text="daily at 06:00",
        checks=["formation duo: attached by name",
                "schedule daily at 06:00: stated",
                "job disabled: does not run"],
        standing="disabled", action="none",
        account=["Formation duo is attached to scheduled job "
                 "weekend-job."])
    assert report.template == "duo"
    index = build_index(
        rows=[derive_report(record)], total_attachments=1,
        total_armed=0, total_waiting=0, total_disabled=1,
        total_templates=1,
        account=["The book holds 1 crew schedule attachment(s)."])
    assert index.total_disabled == 1
    book = build_book(title="A small book", entries=[record])
    assert isinstance(book, CrewScheduleBook)
    assert book.entries[0] is record


# -- agent layer -----------------------------------------------------------
#
# M-145 agent layer: the agent holds a
# CrewScheduleRegistry for the session (session
# state only, no new setting), attachment records
# are held by being registered - published as their
# attachment_record session news with their derived
# report_record, and a whole book's derived
# index_record, through the checkpoint road, deduped
# per id - the report road renders the held book (or
# the shipped example when unheld) through the pure
# formatters, and the /crewschedules surface rides
# both roads on the pure parser + formatters. Status,
# get, report, template, job and index reads register
# and publish nothing, answer from the held registry
# first and from the shipped example only while
# nothing is held - a held session never falls back
# to the example. Reports and the index derive at
# call time from the held records, never held. This
# layer starts no timer, runs no job, summons no
# crew, spawns no agent and persists nothing - and
# there is no Part VIII board yet, so the screen is
# where the crew on schedule attachments are visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _schedule_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_schedule_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "crew_schedules.yaml").read_text(encoding="utf-8")
    path = tmp_path / "crew_schedules.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestCrewSchedulesAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.crew_schedules_status()
        assert status["attachments"] == []
        assert status["book"] is None
        assert status["crew_schedules"]["title"] == (
            "Crew schedule book at the M-144 slice boundary")
        assert [e["attachment_id"]
                for e in status["crew_schedules"]["attachments"]] == [
            "att-dawn-auditor-sweep", "att-weekly-full-six",
            "att-research-swarm-watch", "att-weekend-duo-paused"]
        assert status["book_record"]["type"] == "crew_schedule_book"
        assert status["book_record"]["attachment_count"] == 4
        assert status["book_record"]["index_count"] == 1
        assert [r["standing"] for r in status["reports"]] == [
            "armed", "waiting_for_approval", "armed", "disabled"]
        assert [i["index_id"] for i in status["indexes"]] == [
            "index-m144-boundary"]
        assert status["index"]["total_attachments"] == 4
        assert status["index"]["total_armed"] == 2
        assert status["index"]["total_waiting"] == 1
        assert status["index"]["total_disabled"] == 1
        assert status["index"]["total_templates"] == 4
        assert "Dawn Auditor sweep" in status["plain_words"][0]
        assert "Formation review_panel on job dawn-auditor-sweep" in (
            status["report_plain_words"])
        assert "Attachment index:" in status["index_plain_words"]
        assert "Crew on schedule (M-145)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert agent._crew_schedules_registry() is \
            agent._crew_schedules_registry()
        assert agent._crew_schedules_store is \
            agent._crew_schedules_registry()

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.crew_schedules_status()
        attachment = agent.get_crew_schedule("att-dawn-auditor-sweep")
        assert attachment.template == "review_panel"
        assert agent.get_crew_schedule_for_job(
            "weekly-full-six").template == "full_six"
        report = agent.crew_schedule_report("att-weekly-full-six")
        assert report.standing == "waiting_for_approval"
        index = agent.crew_schedule_index()
        assert index.total_attachments == 4
        assert index.total_armed == 2
        assert [e.attachment_id for e in
                agent.crew_schedules_for_template("duo")] == [
            "att-weekend-duo-paused"]
        assert agent.crew_schedules().title == (
            "Crew schedule book at the M-144 slice boundary")
        registry = agent._crew_schedules_registry()
        assert registry.list_attachments() == ()
        for kind in ("crew_schedule_attachment", "crew_schedule_report",
                     "crew_schedule_index"):
            assert _schedule_events(store, session_id, kind) == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_crew_schedule("att-nope")
        with pytest.raises(KeyError):
            agent.get_crew_schedule_for_job("nope")
        with pytest.raises(KeyError):
            agent.crew_schedule_report("att-nope")

    def test_status_after_register_shows_the_held_pieces(self, agent):
        agent.register_crew_schedule(_attachment())
        status = agent.crew_schedules_status()
        assert [e["attachment_id"] for e in status["attachments"]] == [
            "att-dawn-auditor-sweep"]
        assert status["book"]["attachment_count"] == 1
        # The held book answers now, not the example:
        # records held one by one stand under a session
        # crew schedule book, and it holds no indexes -
        # the index stays a derivation.
        assert status["crew_schedules"]["title"] == (
            "Session crew schedule book")
        assert status["indexes"] == []
        assert status["index"]["total_attachments"] == 1
        assert status["index"]["total_armed"] == 1
        assert status["index"]["total_templates"] == 1
        assert "att-dawn-auditor-sweep" in status["screen"]

    def test_held_session_never_falls_back_to_the_example(self, agent):
        agent.register_crew_schedule(_attachment())
        with pytest.raises(KeyError):
            agent.get_crew_schedule("att-weekly-full-six")
        with pytest.raises(KeyError):
            agent.get_crew_schedule_for_job("weekly-full-six")
        with pytest.raises(KeyError):
            agent.crew_schedule_report("att-weekly-full-six")
        assert agent.crew_schedules_for_template("duo") == ()
        assert agent.crew_schedules().attachment_ids() == (
            "att-dawn-auditor-sweep",)
        assert agent.get_crew_schedule(
            "att-dawn-auditor-sweep").template == "review_panel"
        report = agent.crew_schedule_report("att-dawn-auditor-sweep")
        assert report.standing == "armed"
        assert agent.crew_schedule_index().total_attachments == 1


class TestCrewSchedulesAgentRegister:
    def test_register_attachment_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_crew_schedule(_attachment())
        assert outcome["attachment"]["attachment_id"] == (
            "att-dawn-auditor-sweep")
        assert outcome["record"]["type"] == "crew_schedule_attachment"
        assert outcome["report_record"]["type"] == "crew_schedule_report"
        events = _schedule_events(
            store, session_id, "crew_schedule_attachment")
        assert len(events) == 1
        assert events[0]["attachment_id"] == "att-dawn-auditor-sweep"
        reports = _schedule_events(store, session_id, "crew_schedule_report")
        assert len(reports) == 1
        assert reports[0]["attachment_id"] == "att-dawn-auditor-sweep"
        # The same records are never published twice.
        agent._publish_crew_schedules_record(outcome["record"])
        agent._publish_crew_schedules_record(outcome["report_record"])
        assert len(_schedule_events(
            store, session_id, "crew_schedule_attachment")) == 1
        assert len(_schedule_events(
            store, session_id, "crew_schedule_report")) == 1
        # Foreign record types are refused on this road.
        from mythic_agent.core.crew_interrupts import (
            book_record as _interrupt_book_record,
            load_crew_interrupts,
        )
        from mythic_agent.core.dogfood import (
            entry_record as _dogfood_entry_record,
            load_dogfood,
        )
        from mythic_agent.core.solo_mode import (
            capability_record as _solo_capability_record,
            load_solo_mode,
        )
        agent._publish_crew_schedules_record(book_record(
            load_crew_schedules()))
        agent._publish_crew_schedules_record(_interrupt_book_record(
            load_crew_interrupts()))
        agent._publish_crew_schedules_record(_solo_capability_record(
            load_solo_mode().entries[0]))
        agent._publish_crew_schedules_record(_dogfood_entry_record(
            load_dogfood().entries[0]))
        for kind in ("crew_schedule_book", "crew_interrupt_book",
                     "solo_capability", "dogfood_entry"):
            assert _schedule_events(store, session_id, kind) == []
        assert len(_schedule_events(
            store, session_id, "crew_schedule_attachment")) == 1
        agent.close()

    def test_duplicate_attachment_and_job_refuse_and_publish_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_crew_schedule(_attachment())
        with pytest.raises(ValueError):
            agent.register_crew_schedule(_attachment())
        with pytest.raises(ValueError):
            agent.register_crew_schedule(CrewAttachment(
                attachment_id="att-other", template="duo",
                title="Another formation on the dawn job",
                detail="A second formation on one job refuses.",
                job=_job()))
        assert len(_schedule_events(
            store, session_id, "crew_schedule_attachment")) == 1
        agent.close()

    def test_register_attachment_without_id_gets_an_attachment_id(
            self, agent):
        outcome = agent.register_crew_schedule({
            "template": "duo", "title": "Duo on a job",
            "detail": "The Duo stands on this job.",
            "job": _job(job_id="duo-job")})
        assert outcome["attachment"]["attachment_id"] == "attachment-1"
        assert agent.get_crew_schedule(
            "attachment-1").template == "duo"
        assert agent.get_crew_schedule_for_job(
            "duo-job").attachment_id == "attachment-1"

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_crew_schedule_book(load_crew_schedules())
        assert outcome["count"] == 4
        assert outcome["book"]["attachment_count"] == 4
        events = _schedule_events(
            store, session_id, "crew_schedule_attachment")
        assert [e["attachment_id"] for e in events] == [
            "att-dawn-auditor-sweep", "att-weekly-full-six",
            "att-research-swarm-watch", "att-weekend-duo-paused"]
        reports = _schedule_events(store, session_id, "crew_schedule_report")
        assert [e["attachment_id"] for e in reports] == [
            "att-dawn-auditor-sweep", "att-weekly-full-six",
            "att-research-swarm-watch", "att-weekend-duo-paused"]
        indexes = _schedule_events(store, session_id, "crew_schedule_index")
        assert len(indexes) == 1
        assert indexes[0]["total_attachments"] == 4
        assert indexes[0]["total_armed"] == 2
        assert agent.crew_schedules().title == (
            "Crew schedule book at the M-144 slice boundary")
        # The registry holds records, never reports or
        # indexes: both are derived at call time.
        assert agent.crew_schedules().indexes == ()
        assert agent.crew_schedule_report(
            "att-weekly-full-six").standing == "waiting_for_approval"
        assert agent.crew_schedule_index().total_disabled == 1
        agent.close()

    def test_register_book_twice_refuses(self, agent):
        agent.register_crew_schedule_book(load_crew_schedules())
        with pytest.raises(ValueError):
            agent.register_crew_schedule_book(load_crew_schedules())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_crew_schedule_book()
        assert outcome["count"] == 4
        assert outcome["book"]["attachment_count"] == 4
        events = _schedule_events(
            store, session_id, "crew_schedule_attachment")
        assert [e["attachment_id"] for e in events] == [
            "att-dawn-auditor-sweep", "att-weekly-full-six",
            "att-research-swarm-watch", "att-weekend-duo-paused"]
        assert len(_schedule_events(
            store, session_id, "crew_schedule_report")) == 4
        assert len(_schedule_events(
            store, session_id, "crew_schedule_index")) == 1
        assert agent.crew_schedules().title == (
            "Crew schedule book at the M-144 slice boundary")
        # The recorded book stands whole: its held
        # index still answers.
        assert agent.crew_schedules().indexes[0].index_id == (
            "index-m144-boundary")
        assert agent.crew_schedule_index().total_attachments == 4
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_crew_schedule_book()
        with pytest.raises(ValueError):
            agent.record_crew_schedule_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_schedule_book(tmp_path)
        book = load_crew_schedules_file(path)
        outcome = agent.record_crew_schedule_book(book)
        assert outcome["count"] == 4
        assert agent.crew_schedules().title == (
            "Crew schedule book at the M-144 slice boundary")
        assert agent.get_crew_schedule_for_job(
            "weekend-duo-sweep").template == "duo"
        assert agent.crew_schedule_report(
            "att-weekend-duo-paused").standing == "disabled"

    def test_one_by_one_holdings_stand_under_a_session_book(self, agent):
        agent.register_crew_schedule(_attachment())
        # Held one by one, the records stand under a
        # session crew schedule book composed in the
        # agent layer - never under a recorded book
        # title.
        assert agent.crew_schedules().title == (
            "Session crew schedule book")
        agent.register_crew_schedule(_attachments()[3])
        assert [e.attachment_id
                for e in agent.crew_schedules().entries] == [
            "att-dawn-auditor-sweep", "att-weekend-duo-paused"]
        # A whole book recorded now would re-hold the
        # same attachment ids: the registry refuses it,
        # as it refuses any duplicate.
        with pytest.raises(ValueError):
            agent.record_crew_schedule_book()


class TestCrewSchedulesAgentReport:
    def test_report_renders_the_example_when_unheld(self, agent):
        outcome = agent.report_crew_schedules()
        assert outcome["book"]["title"] == (
            "Crew schedule book at the M-144 slice boundary")
        assert outcome["book"]["attachment_count"] == 4
        assert "att-weekend-duo-paused" in outcome["attachments_text"]
        assert "Formation review_panel on job dawn-auditor-sweep" in (
            outcome["report_text"])
        assert "Attachment index:" in outcome["index_text"]
        assert "Crew on schedule (M-145)" in outcome["screen"]
        assert outcome["explanation"] == PLAIN_EXPLANATION

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_crew_schedule(_attachment())
        outcome = agent.report_crew_schedules()
        assert outcome["book"]["attachment_count"] == 1
        assert "att-dawn-auditor-sweep" in outcome["attachments_text"]
        assert "att-weekly-full-six" not in outcome["attachments_text"]
        assert "att-weekly-full-six" not in outcome["report_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_crew_schedules()
        registry = agent._crew_schedules_registry()
        assert registry.list_attachments() == ()
        for kind in ("crew_schedule_attachment", "crew_schedule_report",
                     "crew_schedule_index"):
            assert _schedule_events(store, session_id, kind) == []
        agent.close()

    def test_no_live_run_summon_timer_or_persist_road(self, agent):
        # This layer holds the attachments as data: it
        # starts no timer, runs no job, summons no crew,
        # spawns no agent, persists nothing - and there
        # is no Part VIII board yet.
        assert not hasattr(agent, "run_crew_schedule")
        assert not hasattr(agent, "summon_crew_schedule")
        assert not hasattr(agent, "spawn_crew_schedule")
        assert not hasattr(agent, "start_crew_schedule_timer")
        assert not hasattr(agent, "persist_crew_schedules")
        assert not hasattr(agent, "crew_schedules_board")


class TestCrewSchedulesTerminalSurface:
    def test_show_attachment_template_job_report_and_index(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/crewschedules")
        assert "Crew on schedule (M-145)" in text
        _, _, text = _slash(
            agent, "/crewschedules attachment att-dawn-auditor-sweep")
        assert "att-dawn-auditor-sweep: review_panel - Dawn Auditor sweep" in text
        _, _, text = _slash(agent, "/crewschedules template duo")
        assert "att-weekend-duo-paused" in text
        assert "att-dawn-auditor-sweep" not in text
        _, _, text = _slash(agent, "/crewschedules job weekly-full-six")
        assert "att-weekly-full-six" in text
        _, _, text = _slash(
            agent, "/crewschedules report att-weekly-full-six")
        assert "Formation full_six on job weekly-full-six" in text
        _, _, text = _slash(agent, "/crewschedules index")
        assert "Attachment index:" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/crewschedules [show|attachment <attachment-id>|"
                "template <template>|job <job-id>|"
                "report <attachment-id>|index]") in text
        _, _, text = _slash(agent, "/crewschedules dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/crewschedules attachment att-nope")
        assert "no attachment record in the book" in text


@pytest.fixture()
def schedules_handler(agent, monkeypatch):
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


def _schedules_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCrewSchedulesCommand:
    def test_show_is_default(self, schedules_handler, agent):
        schedules_handler._handle_crewschedules("")
        assert "Crew on schedule (M-145)" in _schedules_published_text(
            schedules_handler)

    def test_attachment_template_job_report_and_index(
            self, schedules_handler, agent):
        schedules_handler._handle_crewschedules(
            "attachment att-dawn-auditor-sweep")
        assert "review_panel" in _schedules_published_text(schedules_handler)
        schedules_handler._handle_crewschedules("template duo")
        assert "att-weekend-duo-paused" in _schedules_published_text(
            schedules_handler)
        schedules_handler._handle_crewschedules("job weekly-full-six")
        assert "att-weekly-full-six" in _schedules_published_text(
            schedules_handler)
        schedules_handler._handle_crewschedules(
            "report att-weekly-full-six")
        assert "Formation full_six on job weekly-full-six" in (
            _schedules_published_text(schedules_handler))
        schedules_handler._handle_crewschedules("index")
        assert "Attachment index:" in _schedules_published_text(
            schedules_handler)

    def test_bad_grammar_is_published(self, schedules_handler, agent):
        schedules_handler._handle_crewschedules("dance party")
        assert USAGE in _schedules_published_text(schedules_handler)


class TestChatScreenRoutingCrewSchedules:
    def test_crewschedules_routes_as_system_command(self, monkeypatch):
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
            "/crewschedules attachment att-dawn-auditor-sweep", _FakeLog())
        assert calls == [("/crewschedules",
                          "attachment att-dawn-auditor-sweep")]
