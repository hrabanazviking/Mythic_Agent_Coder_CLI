"""M-144 Crew interrupts with grace - pure-layer tests.

TIER: integration

The pure layer is the graceful pauses as data: a
crew interrupt book of interrupt records (one
pause of one member, the whole crew, or one
slice, named in plain words, naming the worktree,
journal and pause-point readings it rests on),
the shipped example interrupt book held in a data
file, a loader that reads an interrupt book from
any file, per-pause consistency reports whose
checks, consistency and account are derived from
the pause's readings, the interrupt index whose
rows, totals and account are derived from the
whole book, records shaped as session news, and a
registry. Nothing here pauses a member, halts a
crew, signals a process, touches a worktree,
writes a journal or persists anything: a stored
report disagreeing with the report derived from
its own interrupt is refused, and a stored index
disagreeing with the index derived from its book
is refused. Consistency is derived from the held
readings, never stored loose: a stored consistency
key on a record refuses as an unknown key.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.validation import ValidationError
from mythic_agent.core.crew_interrupts import (
    PLAIN_EXPLANATION,
    CREW_INTERRUPTS_RESOURCE,
    CREW_INTERRUPTS_SCHEMA,
    CREW_INTERRUPTS_SLICE,
    JOURNAL_STATES,
    PAUSE_POINTS,
    SCOPES,
    USAGE,
    WORKTREE_STATES,
    ConsistencyReport,
    CrewInterrupt,
    CrewInterruptBook,
    InterruptIndex,
    InterruptRegistry,
    book_record,
    build_book,
    build_index,
    build_interrupt,
    build_report,
    derive_index,
    derive_report,
    format_crew_interrupts_screen,
    format_index,
    format_interrupt,
    format_interrupts,
    format_report,
    index_plain_words,
    index_record,
    interrupt_record,
    load_crew_interrupts,
    load_crew_interrupts_file,
    parse_crew_interrupts_args,
    plain_words,
    report_plain_words,
    report_record,
    validate_book,
    validate_index,
    validate_interrupt,
    validate_report,
)

ROOT = Path(__file__).resolve().parents[1]


def _pause(**kwargs):
    kwargs.setdefault("interrupt_id", "int-auditor-rest")
    kwargs.setdefault("scope", "member")
    kwargs.setdefault("title", "Pause the Auditor")
    kwargs.setdefault(
        "detail", "The Auditor rests at the end of a review pass.")
    kwargs.setdefault("member", "auditor")
    kwargs.setdefault("worktree", "clean")
    kwargs.setdefault("journal", "flushed")
    kwargs.setdefault("point", "resting")
    return CrewInterrupt(**kwargs)


def _pauses():
    return [
        _pause(),
        CrewInterrupt(
            interrupt_id="int-crew-rest", scope="crew",
            title="Pause the whole crew",
            detail="The whole crew rests at a slice boundary.",
            worktree="checkpointed", journal="flushed", point="resting"),
        CrewInterrupt(
            interrupt_id="int-slice-m143", scope="slice",
            title="Pause slice M-143",
            detail="The M-143 work rests where it banked.",
            slice_id="M-143",
            worktree="clean", journal="flushed", point="resting"),
        CrewInterrupt(
            interrupt_id="int-forge-worker-mid-edit", scope="member",
            title="Pause the Forge Worker mid-edit",
            detail="Caught mid-edit, tree dirty, journal pending.",
            member="forge_worker",
            worktree="dirty", journal="pending", point="mid_edit"),
    ]


def _report_mapping(report):
    mapping = {
        "interrupt_id": report.interrupt_id,
        "scope": report.scope,
        "checks": list(report.checks),
        "consistent": report.consistent,
        "account": list(report.account)}
    if report.member is not None:
        mapping["member"] = report.member
    if report.slice_id is not None:
        mapping["slice_id"] = report.slice_id
    return mapping


def test_constants_and_usage():
    assert CREW_INTERRUPTS_SLICE == "M-144"
    assert CREW_INTERRUPTS_SCHEMA == "mythic.crew_interrupts/1"
    assert CREW_INTERRUPTS_RESOURCE == "crew_interrupts.yaml"
    assert SCOPES == ("member", "crew", "slice")
    assert WORKTREE_STATES == ("clean", "checkpointed", "dirty")
    assert JOURNAL_STATES == ("flushed", "pending")
    assert PAUSE_POINTS == ("resting", "mid_edit")
    assert "worktree and journal consistent" in PLAIN_EXPLANATION
    assert "data only" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /interrupts")
    assert "/interrupts interrupt <interrupt-id>" in USAGE
    assert "/interrupts slice <slice-id>" in USAGE
    assert "/interrupts index" in USAGE


def test_shipped_example_shape():
    book = load_crew_interrupts()
    assert book.title == "Crew interrupt book at the M-143 slice boundary"
    assert book.interrupt_ids() == (
        "int-auditor-rest", "int-crew-rest",
        "int-slice-m143", "int-forge-worker-mid-edit")
    assert book.scopes() == ("member", "crew", "slice", "member")
    assert tuple(e.consistent for e in book.entries) == (
        True, True, True, False)
    assert tuple(e.status for e in book.entries) == (
        "consistent", "consistent", "consistent", "inconsistent")
    assert book.entries[0].target == "auditor"
    assert book.entries[1].target == "crew"
    assert book.entries[2].target == "M-143"
    assert book.interrupt_for("int-crew-rest").worktree == "checkpointed"
    assert [e.interrupt_id for e in book.interrupts_for_member("auditor")] == [
        "int-auditor-rest"]
    assert [e.interrupt_id for e in book.interrupts_for_slice("M-143")] == [
        "int-slice-m143"]
    assert [e.interrupt_id for e in book.interrupts_with_scope("crew")] == [
        "int-crew-rest"]
    with pytest.raises(KeyError):
        book.interrupt_for("int-nope")


def test_shipped_index():
    book = load_crew_interrupts()
    index = book.index_for("index-m143-boundary")
    assert tuple(r.scope for r in index.rows) == (
        "member", "crew", "slice", "member")
    assert index.total_interrupts == 4
    assert index.total_consistent == 3
    assert index.total_inconsistent == 1
    derived = derive_index(book.entries)
    assert derived.rows == index.rows
    assert derived.account == index.account
    first = derive_report(book.entries[0])
    assert first.checks == (
        "worktree clean: consistent",
        "journal flushed: consistent",
        "pause at a resting point: consistent")
    assert first.account[0] == (
        "Pausing member auditor leaves its worktree "
        "and journal consistent.")


def test_record_validation_and_aliases():
    record = validate_interrupt({
        "id": "int-auditor-rest", "kind": "member",
        "headline": "Pause the Auditor",
        "reason": "The Auditor rests at the end of a review pass.",
        "member_id": "auditor", "worktree_state": "clean",
        "journal_state": "flushed", "resting_point": "resting"})
    assert record == _pause(
        detail="The Auditor rests at the end of a review pass.")
    assert validate_interrupt(_pause()) is not None
    crew = validate_interrupt({
        "scope": "crew", "title": "Pause the whole crew",
        "detail": "The whole crew rests.",
        "worktree": "checkpointed", "journal": "flushed",
        "point": "resting"})
    assert crew.target == "crew"
    assert crew.consistent is True


def test_two_spellings_refusals():
    base = {
        "scope": "member", "title": "Pause the Auditor",
        "detail": "The Auditor rests.", "member": "auditor",
        "worktree": "clean", "journal": "flushed", "point": "resting"}
    with pytest.raises(ValueError):
        validate_interrupt(dict(base, kind="crew"))
    with pytest.raises(ValueError):
        validate_interrupt(dict(base, headline="A different title"))
    with pytest.raises(ValueError):
        validate_interrupt(dict(base, worktree_state="dirty"))
    with pytest.raises(ValueError):
        validate_interrupt(dict(base, slice="M-143", slice_id="M-144"))


def test_unknown_key_refusals():
    base = {
        "scope": "member", "title": "Pause the Auditor",
        "detail": "The Auditor rests.", "member": "auditor",
        "worktree": "clean", "journal": "flushed", "point": "resting"}
    for key in ("consistent", "consistency", "status", "graceful",
                "checks", "account", "surprise"):
        with pytest.raises(ValueError):
            validate_interrupt(dict(base, **{key: True}))


def test_scope_target_stand_together():
    with pytest.raises(ValueError):
        CrewInterrupt(
            scope="member", title="No member named",
            detail="A member pause with no member.",
            worktree="clean", journal="flushed", point="resting")
    with pytest.raises(ValueError):
        _pause(slice_id="M-143")
    with pytest.raises(ValueError):
        CrewInterrupt(
            scope="crew", title="Crew plus member",
            detail="A crew pause naming a member.",
            member="auditor",
            worktree="clean", journal="flushed", point="resting")
    with pytest.raises(ValueError):
        CrewInterrupt(
            scope="slice", title="Slice plus member",
            detail="A slice pause naming a member.",
            member="auditor", slice_id="M-143",
            worktree="clean", journal="flushed", point="resting")
    with pytest.raises(ValueError):
        CrewInterrupt(
            scope="slice", title="No slice named",
            detail="A slice pause with no slice.",
            worktree="clean", journal="flushed", point="resting")


def test_malformed_records():
    with pytest.raises(ValueError):
        _pause(scope="team")
    with pytest.raises(ValueError):
        _pause(worktree="messy")
    with pytest.raises(ValueError):
        _pause(journal="written")
    with pytest.raises(ValueError):
        _pause(point="later")
    with pytest.raises(ValueError):
        _pause(title="")
    with pytest.raises(ValueError):
        _pause(member="not a member!")
    with pytest.raises(ValueError):
        CrewInterrupt(
            scope="slice", title="Bad slice", detail="No such slice.",
            slice_id="M-999",
            worktree="clean", journal="flushed", point="resting")
    with pytest.raises(ValueError):
        validate_interrupt({"scope": "member", "title": "Missing detail"})


def test_consistency_derivation():
    assert _pause().consistent is True
    assert _pause(worktree="checkpointed").consistent is True
    dirty = _pause(worktree="dirty")
    assert dirty.consistent is False
    assert dirty.checks[0] == "worktree dirty: not consistent"
    pending = _pause(journal="pending")
    assert pending.consistent is False
    assert pending.checks[1] == "journal pending: not consistent"
    mid_edit = _pause(point="mid_edit")
    assert mid_edit.consistent is False
    assert mid_edit.checks[2] == "pause taken mid-edit: not consistent"
    record = _pause().to_record()
    assert record["consistent"] is True
    assert record["status"] == "consistent"
    assert record["target"] == "auditor"


def test_report_derivation():
    report = derive_report(_pause())
    assert report.interrupt_id == "int-auditor-rest"
    assert report.scope == "member"
    assert report.member == "auditor"
    assert report.consistent is True
    bad = derive_report(_pauses()[3])
    assert bad.consistent is False
    assert "does not yet leave" in bad.account[0]
    assert "worktree dirty: not consistent" in bad.account[1]


def test_stored_report_judged():
    report = derive_report(_pause())
    stored = _report_mapping(report)
    assert validate_report(stored, _pause()) == report
    bad = dict(stored, consistent=False, checks=[
        "worktree dirty: not consistent",
        "journal flushed: consistent",
        "pause at a resting point: consistent"])
    with pytest.raises(ValueError):
        validate_report(bad, _pause())
    bad_account = dict(stored, account=["A different account altogether."])
    with pytest.raises(ValueError):
        validate_report(bad_account, _pause())


def test_accountless_report_refusal():
    with pytest.raises(ValueError):
        validate_report({
            "scope": "member", "member": "auditor",
            "checks": ["worktree clean: consistent",
                       "journal flushed: consistent",
                       "pause at a resting point: consistent"],
            "consistent": True})


def test_report_consistency_must_match_its_checks():
    with pytest.raises(ValueError):
        ConsistencyReport(
            scope="member", member="auditor",
            checks=["worktree dirty: not consistent",
                    "journal flushed: consistent",
                    "pause at a resting point: consistent"],
            consistent=True,
            account=["A claimed consistency its checks deny."])
    with pytest.raises(ValueError):
        ConsistencyReport(
            scope="member", member="auditor",
            checks=["worktree clean: consistent"],
            consistent=True,
            account=["Too few checks."])


def test_index_derivation():
    index = derive_index(_pauses())
    assert index.total_interrupts == 4
    assert index.total_consistent == 3
    assert index.total_inconsistent == 1
    assert index.row_for("int-crew-rest").consistent is True
    assert index.row_for("int-forge-worker-mid-edit").consistent is False
    with pytest.raises(KeyError):
        index.row_for("int-nope")
    with pytest.raises(ValueError):
        derive_index([])


def test_stored_index_judged():
    index = derive_index(_pauses())
    stored = {
        "index_id": index.index_id,
        "rows": [_report_mapping(r) for r in index.rows],
        "total_interrupts": index.total_interrupts,
        "total_consistent": index.total_consistent,
        "total_inconsistent": index.total_inconsistent,
        "account": list(index.account)}
    assert validate_index(stored, _pauses()).rows == index.rows
    bad = dict(stored, total_consistent=99)
    with pytest.raises(ValueError):
        validate_index(bad, _pauses())
    with pytest.raises(ValueError):
        InterruptIndex(
            rows=index.rows, total_interrupts=4, total_consistent=2,
            total_inconsistent=2, account=index.account)


def test_duplicate_refusals():
    with pytest.raises(ValueError):
        CrewInterruptBook(title="A book", entries=[_pause(), _pause()])
    book = load_crew_interrupts()
    with pytest.raises(ValueError):
        CrewInterruptBook(
            title="A book", entries=[_pause()],
            indexes=[book.indexes[0], book.indexes[0]])


def test_book_index_disagreement_refuses():
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data"
         / "crew_interrupts.yaml").read_text())
    raw["indexes"][0]["total_consistent"] = 99
    raw["indexes"][0]["total_inconsistent"] = -95
    with pytest.raises(ValidationError):
        validate_book(raw)


def test_file_loader_round_trip_and_missing(tmp_path):
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data"
         / "crew_interrupts.yaml").read_text())
    path = tmp_path / "interrupts.yaml"
    path.write_text(yaml.safe_dump(raw))
    book = load_crew_interrupts_file(path)
    assert book.interrupt_ids() == (
        "int-auditor-rest", "int-crew-rest",
        "int-slice-m143", "int-forge-worker-mid-edit")
    with pytest.raises(FileNotFoundError):
        load_crew_interrupts_file(tmp_path / "nope.yaml")


def test_registry_auto_ids_and_duplicates():
    registry = InterruptRegistry()
    first = registry.register_interrupt({
        "scope": "member", "title": "Pause the Auditor",
        "detail": "The Auditor rests.", "member": "auditor",
        "worktree": "clean", "journal": "flushed", "point": "resting"})
    assert first.interrupt_id == "interrupt-1"
    second = registry.register_interrupt({
        "scope": "crew", "title": "Pause the whole crew",
        "detail": "The whole crew rests.",
        "worktree": "checkpointed", "journal": "flushed",
        "point": "resting"})
    assert second.interrupt_id == "interrupt-2"
    with pytest.raises(ValueError):
        registry.register_interrupt(first)
    assert registry.get_interrupt("interrupt-1").member == "auditor"
    assert registry.report_for("interrupt-2").consistent is True
    assert registry.index().total_interrupts == 2
    assert registry.index().total_consistent == 2


def test_registry_book_title_clash():
    registry = InterruptRegistry()
    registry.register_book(load_crew_interrupts())
    other = CrewInterruptBook(
        title="Another book entirely",
        entries=[CrewInterrupt(
            interrupt_id="int-solo-rest", scope="member",
            title="Pause the Polymath", detail="The Polymath rests.",
            member="polymath",
            worktree="clean", journal="flushed", point="resting")])
    with pytest.raises(ValueError):
        registry.register_book(other)
    assert registry.book().title == (
        "Crew interrupt book at the M-143 slice boundary")


def test_session_news_records():
    record = interrupt_record(_pause())
    assert record["type"] == "crew_interrupt"
    assert record["slice"] == "M-144"
    assert record["news"] is True
    assert "leaves its worktree and journal consistent" in record["headline"]
    assert record["consistent"] is True
    bad = interrupt_record(_pauses()[3])
    assert "does not yet leave" in bad["headline"]
    report = report_record(derive_report(_pause()), _pause())
    assert report["type"] == "crew_interrupt_consistency"
    assert report["slice"] == "M-144"
    assert report["news"] is True
    index = index_record(derive_index(_pauses()), _pauses())
    assert index["type"] == "crew_interrupt_index"
    assert index["news"] is True
    book = book_record(load_crew_interrupts())
    assert book["type"] == "crew_interrupt_book"
    assert book["interrupt_count"] == 4


def test_plain_words():
    text = plain_words(_pause())
    assert text.startswith("Pause the Auditor - pausing member auditor:")
    assert "leaves its worktree and journal consistent" in text
    bad_text = plain_words(_pauses()[3])
    assert "does not yet leave" in bad_text
    assert "mid-edit" in bad_text
    report_text = report_plain_words(load_crew_interrupts())
    assert "Pausing member auditor - consistent" in report_text
    assert "Pausing member forge_worker - not yet consistent" in report_text
    index_text = index_plain_words(load_crew_interrupts())
    assert "Interrupt index:" in index_text
    assert "3 leave the worktree and journal consistent" in index_text


def test_formatters_and_screen():
    line = format_interrupt(_pause())
    assert line.startswith("int-auditor-rest: member - Pause the Auditor")
    assert "pausing member auditor: consistent" in line
    book = load_crew_interrupts()
    all_lines = format_interrupts(book)
    assert "int-crew-rest" in all_lines
    filtered = format_interrupts(book, member="auditor")
    assert "int-auditor-rest" in filtered
    assert "int-crew-rest" not in filtered
    by_scope = format_interrupts(book, scope="slice")
    assert "int-slice-m143" in by_scope
    assert "int-auditor-rest" not in by_scope
    report_text = format_report(book)
    assert "Consistency reports in Crew interrupt book" in report_text
    index_text = format_index(book)
    assert "Interrupt index:" in index_text
    screen = format_crew_interrupts_screen()
    assert "Crew interrupts (M-144)" in screen
    assert USAGE in screen


def test_parser_grammar():
    assert parse_crew_interrupts_args("") == ("show", None)
    assert parse_crew_interrupts_args("show") == ("show", None)
    assert parse_crew_interrupts_args("list") == ("show", None)
    assert parse_crew_interrupts_args("interrupt int-auditor-rest") == (
        "interrupt", "int-auditor-rest")
    assert parse_crew_interrupts_args("member auditor") == (
        "member", "auditor")
    assert parse_crew_interrupts_args("slice M-143") == ("slice", "M-143")
    assert parse_crew_interrupts_args("report int-crew-rest") == (
        "report", "int-crew-rest")
    assert parse_crew_interrupts_args("index") == ("index", None)
    with pytest.raises(ValueError):
        parse_crew_interrupts_args("pause auditor")
    with pytest.raises(ValueError):
        parse_crew_interrupts_args("interrupt")
    with pytest.raises(ValueError):
        parse_crew_interrupts_args("slice banana")
    with pytest.raises(ValueError):
        parse_crew_interrupts_args("index now")


def test_builders_from_field_words():
    record = build_interrupt({
        "scope": "member", "title": "Pause the Auditor",
        "detail": "The Auditor rests.", "member": "auditor",
        "worktree": "clean", "journal": "flushed", "point": "resting"})
    assert record.consistent is True
    report = build_report(
        scope="member", member="auditor",
        checks=["worktree clean: consistent",
                "journal flushed: consistent",
                "pause at a resting point: consistent"],
        consistent=True,
        account=["Pausing member auditor leaves its worktree "
                 "and journal consistent."])
    assert report.scope == "member"
    index = build_index(
        rows=[derive_report(record)], total_interrupts=1,
        total_consistent=1, total_inconsistent=0,
        account=["The book holds 1 crew interrupt(s)."])
    assert index.total_interrupts == 1
    book = build_book(title="A small book", entries=[record])
    assert isinstance(book, CrewInterruptBook)
    assert book.entries[0] is record
