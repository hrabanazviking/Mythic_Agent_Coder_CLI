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

# -- agent layer -----------------------------------------------------------
#
# M-142 agent layer: the agent holds a
# SoloRegistry for the session (session state
# only, no new setting), capability records are
# held by being registered - published as their
# capability_record session news through the
# checkpoint road, deduped per capability id - the
# report road renders the held book (or the shipped
# example when unheld) through the pure formatters,
# and the /solo surface rides both roads on the
# pure parser + formatters. Status, get, report
# and ledger reads register and publish nothing,
# answer from the held registry first and from the
# shipped example only while nothing is held - a
# held session never falls back to the example.
# Reports and the parity ledger derive at call
# time from the held records, never held. This
# layer disables no crew, spawns no agent, runs no
# agent, calls no model and persists nothing - and
# there is no Part VIII board yet, so the screen is
# where the solo mode is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _solo_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _book_dict(**overrides):
    data = {
        "schema": SOLO_MODE_SCHEMA,
        "guide": {"title": "A small solo mode book"},
        "entries": [_cap_dict(c) for c in _caps()],
    }
    data.update(overrides)
    return data


def _write_solo_book(tmp_path, data):
    path = tmp_path / "solo_mode.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


class TestSoloModeAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.solo_mode_status()
        assert status["capabilities"] == []
        assert status["book"] is None
        assert status["solo_mode"]["title"] == (
            "Solo mode book at the M-141 slice boundary")
        assert [c["capability_id"] for c in status["solo_mode"]["capabilities"]] == [
            "cap-planning", "cap-editing", "cap-testing",
            "cap-reviewing", "cap-remembering", "cap-costing",
            "cap-shipping", "cap-judging"]
        assert status["book_record"]["type"] == "solo_book"
        assert status["book_record"]["capability_count"] == 8
        assert status["book_record"]["ledger_count"] == 1
        assert [r["member"] for r in status["reports"]] == [
            "architect", "forge_worker", "auditor", "scribe"]
        assert [r["amplifications"] for r in status["reports"]] == [1, 2, 2, 2]
        assert [led["ledger_id"] for led in status["ledgers"]] == [
            "ledger-m141-boundary"]
        assert status["ledger"]["total_capabilities"] == 8
        assert status["ledger"]["total_amplified"] == 7
        assert status["ledger"]["total_plain"] == 1
        assert "planning -" in status["plain_words"][0]
        assert "architect - 1 amplification(s)" in status["report_plain_words"]
        assert "Parity ledger:" in status["ledger_plain_words"]
        assert "Solo mode dignity (M-142)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert agent._solo_mode_registry() is agent._solo_mode_registry()
        assert agent._solo_mode_store is agent._solo_mode_registry()

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.solo_mode_status()
        cap = agent.get_solo_capability("cap-editing")
        assert cap.amplifier == "forge_worker"
        report = agent.solo_mode_report("auditor")
        assert report.amplifications == 2
        assert agent.solo_mode_report("architect").amplifications == 1
        ledger = agent.parity_ledger()
        assert ledger.total_capabilities == 8
        assert ledger.total_amplified == 7
        assert agent.solo_mode().title == (
            "Solo mode book at the M-141 slice boundary")
        registry = agent._solo_mode_registry()
        assert registry.list_capabilities() == ()
        assert _solo_events(store, session_id, "solo_capability") == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_solo_capability("no-such-capability")
        with pytest.raises(KeyError):
            agent.solo_mode_report("guardian")

    def test_status_after_register_shows_the_held_pieces(self, agent):
        agent.register_solo_capability(_cap())
        status = agent.solo_mode_status()
        assert [c["capability_id"] for c in status["capabilities"]] == [
            "cap-editing"]
        assert status["book"]["capability_count"] == 1
        # The held book answers now, not the example:
        # records held one by one stand under a session
        # solo mode book, and it holds no ledgers - the
        # ledger stays a derivation.
        assert status["solo_mode"]["title"] == "Session solo mode book"
        assert status["ledgers"] == []
        assert status["ledger"]["total_capabilities"] == 1
        assert status["ledger"]["total_amplified"] == 1
        assert "cap-editing" in status["screen"]

    def test_held_session_never_falls_back_to_the_example(self, agent):
        agent.register_solo_capability(_cap())
        with pytest.raises(KeyError):
            agent.get_solo_capability("cap-planning")
        with pytest.raises(KeyError):
            agent.solo_mode_report("scribe")
        assert agent.solo_mode().capability_ids() == ("cap-editing",)
        assert agent.get_solo_capability(
            "cap-editing").amplifier == "forge_worker"
        report = agent.solo_mode_report("forge_worker")
        assert report.amplifications == 1
        assert agent.parity_ledger().total_capabilities == 1

class TestSoloModeAgentRegister:
    def test_register_capability_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_solo_capability(_cap())
        assert outcome["capability"]["capability_id"] == "cap-editing"
        assert outcome["record"]["type"] == "solo_capability"
        events = _solo_events(store, session_id, "solo_capability")
        assert len(events) == 1
        assert events[0]["capability_id"] == "cap-editing"
        # The same record is never published twice.
        agent._publish_solo_mode_record(outcome["record"])
        assert len(_solo_events(
            store, session_id, "solo_capability")) == 1
        # Foreign record types are refused on this road.
        from mythic_agent.core.character_voices import (
            load_character_voices,
            profile_record,
        )
        from mythic_agent.core.cost_court import (
            entry_record as _court_entry_record,
            load_cost_court,
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
            load_crew_replay,
            step_record as _replay_step_record,
        )
        from mythic_agent.core.crew_sizing import (
            case_record as _sizing_case_record,
            load_crew_sizing,
        )
        from mythic_agent.core.dogfood import (
            entry_record as _dogfood_entry_record,
            load_dogfood,
        )
        from mythic_agent.core.external_agents import (
            load_external_agents,
            seat_record as _external_seat_record,
        )
        from mythic_agent.core.failure_fostering import (
            load_failure_fostering,
            report_record as _foster_report_record,
        )
        from mythic_agent.core.review_panels import (
            load_review_panel,
            review_record,
        )
        from mythic_agent.core.stand_ups import (
            entry_record as _stand_up_entry_record,
            load_stand_up,
        )
        caps = _caps()
        agent._publish_solo_mode_record(report_record(
            derive_report(caps, "auditor"), caps))
        agent._publish_solo_mode_record(ledger_record(
            derive_ledger(caps), caps))
        agent._publish_solo_mode_record(book_record(load_solo_mode()))
        agent._publish_solo_mode_record(_dogfood_entry_record(
            load_dogfood().entries[0]))
        agent._publish_solo_mode_record(_court_entry_record(
            load_cost_court().entries[0]))
        agent._publish_solo_mode_record(_foster_report_record(
            load_failure_fostering().reports[0]))
        agent._publish_solo_mode_record(_replay_step_record(
            load_crew_replay().steps[0]))
        agent._publish_solo_mode_record(profile_record(
            load_character_voices().profiles[0]))
        agent._publish_solo_mode_record(_sizing_case_record(
            load_crew_sizing().cases[0]))
        agent._publish_solo_mode_record(_stand_up_entry_record(
            load_stand_up().entries[0]))
        memory = load_crew_memory()
        agent._publish_solo_mode_record(_memory_entry_record(
            memory.entry_for("broken-checkpoint-chain")))
        panel = load_review_panel()
        agent._publish_solo_mode_record(review_record(panel.reviews[0]))
        agent._publish_solo_mode_record(casting_record(
            load_casting().members[0]))
        agent._publish_solo_mode_record(_external_seat_record(
            load_external_agents().seats[0]))
        for kind in ("solo_amplification_report", "solo_parity_ledger",
                     "solo_book", "dogfood_entry", "cost_court_entry",
                     "failure_report", "crew_replay_step",
                     "character_voice_profile", "crew_sizing_case",
                     "stand_up_entry", "crew_memory_entry",
                     "panel_review", "crew_member", "external_seat"):
            assert _solo_events(store, session_id, kind) == []
        assert len(_solo_events(
            store, session_id, "solo_capability")) == 1
        agent.close()

    def test_duplicate_capability_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_solo_capability(_cap())
        with pytest.raises(ValueError):
            agent.register_solo_capability(_cap())
        assert len(_solo_events(
            store, session_id, "solo_capability")) == 1
        agent.close()

    def test_register_capability_without_id_gets_a_solo_id(self, agent):
        outcome = agent.register_solo_capability({
            "capability": "editing", "title": "Edit the code",
            "detail": "Writing and changing the code itself.",
            "amplifier": "forge_worker",
            "gain": "More hands on the tools at once."})
        assert outcome["capability"]["capability_id"] == "solo-1"
        assert agent.get_solo_capability("solo-1").capability == "editing"

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_solo_book(load_solo_mode())
        assert outcome["count"] == 8
        assert outcome["book"]["capability_count"] == 8
        events = _solo_events(store, session_id, "solo_capability")
        assert [e["capability_id"] for e in events] == [
            "cap-planning", "cap-editing", "cap-testing",
            "cap-reviewing", "cap-remembering", "cap-costing",
            "cap-shipping", "cap-judging"]
        assert agent.solo_mode().title == (
            "Solo mode book at the M-141 slice boundary")
        assert agent.get_solo_capability(
            "cap-judging").amplifier is None
        # The registry holds records, never reports or
        # ledgers: both are derived at call time.
        assert agent.solo_mode().ledgers == ()
        assert agent.solo_mode_report("auditor").amplifications == 2
        assert agent.solo_mode_report("architect").amplifications == 1
        assert agent.parity_ledger().total_capabilities == 8
        agent.close()

    def test_register_book_twice_refuses(self, agent):
        agent.register_solo_book(load_solo_mode())
        with pytest.raises(ValueError):
            agent.register_solo_book(load_solo_mode())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_solo_book()
        assert outcome["count"] == 8
        assert outcome["book"]["capability_count"] == 8
        events = _solo_events(store, session_id, "solo_capability")
        assert [e["capability_id"] for e in events] == [
            "cap-planning", "cap-editing", "cap-testing",
            "cap-reviewing", "cap-remembering", "cap-costing",
            "cap-shipping", "cap-judging"]
        assert agent.solo_mode().title == (
            "Solo mode book at the M-141 slice boundary")
        # The recorded book stands whole: its held
        # ledger still answers.
        assert agent.solo_mode().ledgers[0].ledger_id == (
            "ledger-m141-boundary")
        assert agent.parity_ledger().total_capabilities == 8
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_solo_book()
        with pytest.raises(ValueError):
            agent.record_solo_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_solo_book(tmp_path, _book_dict())
        book = load_solo_mode_file(path)
        outcome = agent.record_solo_book(book)
        assert outcome["count"] == 4
        assert agent.solo_mode().title == "A small solo mode book"
        assert agent.get_solo_capability(
            "cap-judging").amplifier is None
        assert agent.solo_mode_report("auditor").amplifications == 2

    def test_one_by_one_holdings_stand_under_a_session_book(self, agent):
        agent.register_solo_capability(_cap())
        # Held one by one, the records stand under a
        # session solo mode book composed in the agent
        # layer - never under a recorded book title.
        assert agent.solo_mode().title == "Session solo mode book"
        agent.register_solo_capability(_caps()[1])
        assert [c.capability_id for c in agent.solo_mode().entries] == [
            "cap-editing", "cap-testing"]
        # A whole book recorded now would re-hold the
        # same capability ids: the registry refuses it,
        # as it refuses any duplicate.
        with pytest.raises(ValueError):
            agent.record_solo_book()

class TestSoloModeAgentReport:
    def test_report_renders_the_example_when_unheld(self, agent):
        outcome = agent.report_solo_mode()
        assert outcome["book"]["title"] == (
            "Solo mode book at the M-141 slice boundary")
        assert outcome["book"]["capability_count"] == 8
        assert "cap-judging" in outcome["capabilities_text"]
        assert "architect - 1 amplification(s)" in outcome["report_text"]
        assert "Parity ledger:" in outcome["ledger_text"]
        assert "Solo mode dignity (M-142)" in outcome["screen"]
        assert outcome["explanation"] == PLAIN_EXPLANATION

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_solo_capability(_cap())
        outcome = agent.report_solo_mode()
        assert outcome["book"]["capability_count"] == 1
        assert "cap-editing" in outcome["capabilities_text"]
        assert "cap-planning" not in outcome["capabilities_text"]
        assert "auditor" not in outcome["report_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_solo_mode()
        registry = agent._solo_mode_registry()
        assert registry.list_capabilities() == ()
        assert _solo_events(store, session_id, "solo_capability") == []
        agent.close()

    def test_no_live_crew_model_or_persist_road(self, agent):
        # This layer holds the solo mode as data: it
        # disables no crew, spawns no agent, runs no
        # agent, calls no model, persists nothing - and
        # there is no Part VIII board yet.
        assert not hasattr(agent, "generate_solo_mode")
        assert not hasattr(agent, "persist_solo_mode")
        assert not hasattr(agent, "spawn_solo_crew")
        assert not hasattr(agent, "disable_solo_crew")
        assert not hasattr(agent, "run_live_crew")
        assert not hasattr(agent, "solo_mode_board")


class TestSoloModeTerminalSurface:
    def test_show_capability_member_report_and_ledger(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/solo")
        assert "Solo mode dignity (M-142)" in text
        _, _, text = _slash(agent, "/solo capability cap-editing")
        assert "cap-editing: editing" in text
        _, _, text = _slash(agent, "/solo member auditor")
        assert "cap-testing" in text
        assert "cap-reviewing" in text
        assert "cap-editing" not in text
        _, _, text = _slash(agent, "/solo report auditor")
        assert "auditor - 2 amplification(s)" in text
        _, _, text = _slash(agent, "/solo ledger")
        assert "Parity ledger:" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/solo [show|capability <capability-id>|member <member-id>|"
                "report <member-id>|ledger]") in text
        _, _, text = _slash(agent, "/solo dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/solo capability missing-cap")
        assert "no capability record in the book" in text

@pytest.fixture()
def solo_handler(agent, monkeypatch):
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


def _solo_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestSoloModeCommand:
    def test_show_is_default(self, solo_handler, agent):
        solo_handler._handle_solo("")
        assert "Solo mode dignity (M-142)" in _solo_published_text(solo_handler)

    def test_capability_member_report_and_ledger(self, solo_handler, agent):
        solo_handler._handle_solo("capability cap-editing")
        assert "forge_worker" in _solo_published_text(solo_handler)
        solo_handler._handle_solo("member scribe")
        assert "cap-remembering" in _solo_published_text(solo_handler)
        solo_handler._handle_solo("report auditor")
        assert "auditor - 2 amplification(s)" in _solo_published_text(solo_handler)
        solo_handler._handle_solo("ledger")
        assert "Parity ledger:" in _solo_published_text(solo_handler)

    def test_bad_grammar_is_published(self, solo_handler, agent):
        solo_handler._handle_solo("dance party")
        assert USAGE in _solo_published_text(solo_handler)


class TestChatScreenRoutingSolo:
    def test_solo_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/solo capability cap-editing", _FakeLog())
        assert calls == [("/solo", "capability cap-editing")]
