"""M-142 Solo mode dignity - pure-layer tests.

TIER: integration

The pure layer is the solo parity as data: a solo
mode book of capability records (one capability the
single coder holds, named in plain words, with the
member who amplifies it when the crew is on and the
gain that amplification brings - the two standing
together or not at all), the shipped example solo
mode book held in a data file, a loader that reads a
solo mode book from any file, per-member
amplification reports whose counts and account are
derived from the records they report, the parity
ledger whose rows, totals and account are derived
from the whole book, records shaped as session news,
and a registry. Nothing here disables a crew, spawns
an agent, calls a model or persists anything: a
stored report disagreeing with the report derived
from its own records is refused, and a stored ledger
disagreeing with the ledger derived from its book is
refused. Parity is derived from the held records,
never stored loose: a stored crew-only key on a
record refuses as an unknown key.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.validation import ValidationError
from mythic_agent.core.solo_mode import (
    PLAIN_EXPLANATION,
    SOLO_MODE_RESOURCE,
    SOLO_MODE_SCHEMA,
    SOLO_MODE_SLICE,
    USAGE,
    AmplificationReport,
    ParityLedger,
    SoloBook,
    SoloCapability,
    SoloRegistry,
    book_record,
    build_book,
    build_capability,
    build_ledger,
    build_report,
    capability_record,
    derive_ledger,
    derive_report,
    format_capabilities,
    format_capability,
    format_ledger,
    format_report,
    format_solo_mode_screen,
    ledger_plain_words,
    ledger_record,
    load_solo_mode,
    load_solo_mode_file,
    parse_solo_mode_args,
    plain_words,
    report_plain_words,
    report_record,
    validate_book,
    validate_capability,
    validate_ledger,
    validate_report,
)

ROOT = Path(__file__).resolve().parents[1]


def _cap(**kwargs):
    kwargs.setdefault("capability_id", "cap-editing")
    kwargs.setdefault("capability", "editing")
    kwargs.setdefault("title", "Edit the code")
    kwargs.setdefault(
        "detail", "Writing and changing the code itself.")
    kwargs.setdefault("amplifier", "forge_worker")
    kwargs.setdefault("gain", "More hands on the tools at once.")
    return SoloCapability(**kwargs)


def _caps():
    return [
        _cap(),
        SoloCapability(
            capability_id="cap-testing", capability="testing",
            title="Run the tests",
            detail="Running the suite and reading its failures.",
            amplifier="auditor",
            gain="A second reader of the failures."),
        SoloCapability(
            capability_id="cap-reviewing", capability="reviewing",
            title="Review the change",
            detail="Reading the change against the road it serves.",
            amplifier="auditor",
            gain="Eyes that did not write the change."),
        SoloCapability(
            capability_id="cap-judging", capability="judging",
            title="Decide what ships",
            detail="The call itself - what ships and what waits."),
    ]


def test_constants_and_usage():
    assert SOLO_MODE_SLICE == "M-142"
    assert SOLO_MODE_SCHEMA == "mythic.solo_mode/1"
    assert SOLO_MODE_RESOURCE == "solo_mode.yaml"
    assert "never a requirement" in PLAIN_EXPLANATION
    assert "data only" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /solo")
    assert "/solo capability <capability-id>" in USAGE
    assert "/solo ledger" in USAGE


def test_shipped_example_shape():
    book = load_solo_mode()
    assert book.title == "Solo mode book at the M-141 slice boundary"
    assert book.capability_ids() == (
        "cap-planning", "cap-editing", "cap-testing",
        "cap-reviewing", "cap-remembering", "cap-costing",
        "cap-shipping", "cap-judging")
    assert len(book.entries) == 8
    assert len(book.ledgers) == 1
    judging = book.capability_for("cap-judging")
    assert judging.amplifier is None
    assert judging.amplified is False


def test_shipped_example_parity_ledger():
    book = load_solo_mode()
    ledger = book.ledger_for("ledger-m141-boundary")
    assert tuple(r.member for r in ledger.rows) == (
        "architect", "forge_worker", "auditor", "scribe")
    assert ledger.total_capabilities == 8
    assert ledger.total_amplified == 7
    assert ledger.total_plain == 1
    derived = derive_ledger(book.entries)
    assert derived.rows == ledger.rows
    assert derived.account == ledger.account
    assert (derived.total_capabilities, derived.total_amplified,
            derived.total_plain) == (8, 7, 1)
    assert "loses nothing" in ledger.account[0]


def test_capability_alias_spellings():
    cap = validate_capability({
        "id": "cap-x", "name": "editing",
        "headline": "Edit the code",
        "description": "Writing the code itself.",
        "member": "forge_worker",
        "amplification": "More hands at once."})
    assert cap.capability_id == "cap-x"
    assert cap.capability == "editing"
    assert cap.title == "Edit the code"
    assert cap.amplifier == "forge_worker"
    assert cap.gain == "More hands at once."
    assert cap.amplified is True


def test_capability_two_spellings_disagree_refuses():
    with pytest.raises(ValueError):
        validate_capability({
            "capability": "editing", "name": "testing",
            "title": "Edit the code",
            "detail": "Writing the code itself."})
    with pytest.raises(ValueError):
        validate_capability({
            "capability": "editing", "title": "Edit the code",
            "detail": "Writing the code itself.",
            "amplifier": "auditor", "member_id": "scribe",
            "gain": "More hands at once."})


def test_capability_unknown_and_parity_keys_refuse():
    base = {
        "capability": "editing", "title": "Edit the code",
        "detail": "Writing the code itself."}
    for key in ("crew_only", "requires_crew", "solo_holds", "bogus"):
        with pytest.raises(ValueError):
            validate_capability({**base, key: True})


def test_capability_gain_and_amplifier_stand_together():
    with pytest.raises(ValueError):
        _cap(gain=None)
    with pytest.raises(ValueError):
        _cap(amplifier=None)
    plain = _cap(amplifier=None, gain=None)
    assert plain.amplified is False


def test_capability_malformed_refuses():
    with pytest.raises(ValueError):
        _cap(capability="not a word!")
    with pytest.raises(ValueError):
        _cap(title="")
    with pytest.raises(ValueError):
        _cap(detail="   ")
    with pytest.raises(ValueError):
        validate_capability({"capability": "editing", "title": "T"})


def _report_dict(report):
    return {
        "member": report.member,
        "capability_ids": list(report.capability_ids),
        "capabilities": list(report.capabilities),
        "amplifications": report.amplifications,
        "account": list(report.account),
    }


def _ledger_dict(ledger):
    return {
        "rows": [_report_dict(r) for r in ledger.rows],
        "total_capabilities": ledger.total_capabilities,
        "total_amplified": ledger.total_amplified,
        "total_plain": ledger.total_plain,
        "account": list(ledger.account),
    }


def _cap_dict(cap):
    data = {
        "capability_id": cap.capability_id,
        "capability": cap.capability, "title": cap.title,
        "detail": cap.detail,
    }
    if cap.amplifier is not None:
        data["amplifier"] = cap.amplifier
        data["gain"] = cap.gain
    return data


def test_derive_report_reads_records():
    report = derive_report(_caps(), "auditor")
    assert report.capability_ids == ("cap-testing", "cap-reviewing")
    assert report.capabilities == ("testing", "reviewing")
    assert report.amplifications == 2
    assert "amplification" not in report.account[0]
    assert "never a requirement" in report.account[1]
    assert "loses nothing" in report.account[2]
    with pytest.raises(KeyError):
        derive_report(_caps(), "scribe")


def test_stored_report_judged_against_records():
    caps = _caps()
    derived = derive_report(caps, "auditor")
    assert validate_report(_report_dict(derived), caps) == derived
    stored = _report_dict(derived)
    stored["amplifications"] = 1
    stored["capability_ids"] = ["cap-testing"]
    stored["capabilities"] = ["testing"]
    with pytest.raises(ValueError):
        validate_report(stored, caps)


def test_report_no_account_refuses():
    with pytest.raises(ValueError):
        validate_report({
            "member": "auditor", "capability_ids": ["cap-testing"],
            "capabilities": ["testing"], "amplifications": 1})


def test_derive_ledger_counts_the_unamplified():
    ledger = derive_ledger(_caps())
    assert tuple(r.member for r in ledger.rows) == (
        "forge_worker", "auditor")
    assert ledger.total_capabilities == 4
    assert ledger.total_amplified == 3
    assert ledger.total_plain == 1
    assert "Crew is an amplifier, never a requirement." \
        in ledger.account


def test_stored_ledger_judged_against_records():
    caps = _caps()
    derived = derive_ledger(caps)
    assert validate_ledger(_ledger_dict(derived), caps) == derived
    stored = _ledger_dict(derived)
    stored["total_plain"] = 0
    stored["total_capabilities"] = 3
    with pytest.raises(ValueError):
        validate_ledger(stored, caps)
    with pytest.raises(ValueError):
        ParityLedger(
            rows=derived.rows, total_capabilities=4,
            total_amplified=2, total_plain=2,
            account=derived.account)


def test_book_duplicate_capability_id_refuses():
    with pytest.raises(ValueError):
        SoloBook(title="A book", entries=[_cap(), _cap()])


def test_book_ledger_disagreeing_refuses():
    caps = _caps()
    ledger = derive_ledger(caps)
    stored = _ledger_dict(ledger)
    stored["account"] = ["A stored account of its own."]
    data = {
        "schema": SOLO_MODE_SCHEMA,
        "guide": {"title": "A book"},
        "entries": [_cap_dict(c) for c in caps],
        "ledgers": [stored],
    }
    with pytest.raises(ValidationError):
        validate_book(data)


def test_load_solo_mode_file_roundtrip(tmp_path):
    book = load_solo_mode()
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / "solo_mode.yaml")
        .read_text(encoding="utf-8"))
    path = tmp_path / "mine.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    loaded = load_solo_mode_file(path)
    assert loaded.title == book.title
    assert loaded.capability_ids() == book.capability_ids()
    with pytest.raises(FileNotFoundError):
        load_solo_mode_file(tmp_path / "missing.yaml")


def test_registry_auto_ids_and_derivations():
    registry = SoloRegistry()
    first = registry.register_capability({
        "capability": "editing", "title": "Edit the code",
        "detail": "Writing the code itself.",
        "amplifier": "forge_worker",
        "gain": "More hands at once."})
    second = registry.register_capability({
        "capability": "judging", "title": "Decide what ships",
        "detail": "The call itself."})
    assert (first.capability_id, second.capability_id) == (
        "solo-1", "solo-2")
    with pytest.raises(ValueError):
        registry.register_capability(first)
    assert registry.report_for("forge_worker").amplifications == 1
    ledger = registry.ledger()
    assert ledger.total_capabilities == 2
    assert ledger.total_plain == 1


def test_registry_book_title_clash_refuses():
    registry = SoloRegistry(load_solo_mode())
    other = SoloBook(title="Another book", entries=[_cap()])
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_records_are_news_shaped():
    cap = _cap()
    record = capability_record(cap)
    assert record["news"] is True
    assert record["type"] == "solo_capability"
    assert "held by the single coder alone" in record["headline"]
    caps = _caps()
    report = derive_report(caps, "auditor")
    rrec = report_record(report, caps)
    assert rrec["news"] is True
    assert "never a requirement" in rrec["headline"]
    lrec = ledger_record(derive_ledger(caps), caps)
    assert lrec["news"] is True
    assert "none lost with the crew off" in lrec["headline"]
    book = load_solo_mode()
    brec = book_record(book)
    assert brec["capability_count"] == 8
    assert brec["news"] is True


def test_plain_words_forms():
    cap = _cap()
    text = plain_words(cap)
    assert text.startswith("editing - Edit the code:")
    assert "forge_worker amplifies it" in text
    book = load_solo_mode()
    reports = report_plain_words(book)
    assert "architect - 1 amplification(s)" in reports
    ledger = ledger_plain_words(book)
    assert "Parity ledger:" in ledger
    assert "loses nothing" in ledger


def test_formatters_and_screen():
    cap = _cap()
    assert format_capability(cap).startswith("cap-editing: editing")
    book = load_solo_mode()
    lines = format_capabilities(book, member="auditor")
    assert "cap-testing" in lines
    assert "cap-editing" not in lines
    assert "architect - 1 amplification(s)" in format_report(book)
    assert "Parity ledger:" in format_ledger(book)
    screen = format_solo_mode_screen(book)
    assert "Solo mode dignity (M-142)" in screen
    assert USAGE in screen


def test_parse_solo_mode_args():
    assert parse_solo_mode_args("") == ("show", None)
    assert parse_solo_mode_args("show") == ("show", None)
    assert parse_solo_mode_args("capability cap-editing") == (
        "capability", "cap-editing")
    assert parse_solo_mode_args("member auditor") == (
        "member", "auditor")
    assert parse_solo_mode_args("report auditor") == (
        "report", "auditor")
    assert parse_solo_mode_args("ledger") == ("ledger", None)
    for bad in ("bogus", "capability", "ledger now", "member a b"):
        with pytest.raises(ValueError):
            parse_solo_mode_args(bad)


def test_builders_from_field_words():
    cap = build_capability({
        "capability": "editing", "title": "Edit the code",
        "detail": "Writing the code itself."})
    assert isinstance(cap, SoloCapability)
    caps = _caps()
    report = build_report(
        _report_dict(derive_report(caps, "auditor")), caps)
    assert isinstance(report, AmplificationReport)
    ledger = build_ledger(_ledger_dict(derive_ledger(caps)), caps)
    assert isinstance(ledger, ParityLedger)
    book = build_book(load_solo_mode())
    assert isinstance(book, SoloBook)
