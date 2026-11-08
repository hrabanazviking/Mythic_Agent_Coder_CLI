"""M-137 External agents as crew - pure-layer tests.

TIER: integration

The pure layer is the seats outside agents sit
in, as data: a seat book of seats (one per
outside agent - the agent's own name, the home
it arrives from, the transport it rides, the
crew member record it sits as and the budget
that guards it), the shipped example seat book
held in a data file, a loader that reads a seat
book from any file, seat checks whose findings
are derived from the seat they judge, records
shaped as session news, and a registry. Nothing
here opens an MCP session, calls a model or
spawns an agent: a seat naming an office, a
posture or a budget word the internal crew does
not use - or any privilege of its own - is
refused, and a stored check disagreeing with
the findings derived from its seat is refused.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.budgets import BUDGET_SCOPES
from mythic_agent.core.crew_members import (
    POSTURES, load_casting, member_offices)
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.external_agents import (
    EXTERNAL_AGENTS_RESOURCE,
    EXTERNAL_AGENTS_SCHEMA,
    EXTERNAL_AGENTS_SLICE,
    PLAIN_EXPLANATION,
    TRANSPORTS,
    USAGE,
    ExternalRegistry,
    ExternalSeat,
    SeatBook,
    SeatCheck,
    book_record,
    build_book,
    build_check,
    build_seat,
    check_plain_words,
    check_record,
    check_seat,
    format_check,
    format_external_agents_screen,
    format_seat,
    format_seats,
    format_transports,
    load_external_agents,
    load_external_agents_file,
    normalize_transport,
    parse_external_args,
    plain_words,
    seat_record,
    validate_book,
    validate_check,
    validate_seat,
)

ROOT = Path(__file__).resolve().parents[1]


def _member(**kwargs):
    kwargs.setdefault("id", "atlas_reviewer")
    kwargs.setdefault("name", "Atlas Reviewer (external)")
    kwargs.setdefault("office", "auditor")
    kwargs.setdefault("tools", ["read_file", "list_dir", "grep_search"])
    kwargs.setdefault("posture", "read-only-scout")
    kwargs.setdefault(
        "character", "external_agent_characters/Atlas_Reviewer.md")
    return kwargs


def _seat(**kwargs):
    kwargs.setdefault("seat_id", "seat-atlas")
    kwargs.setdefault("member", _member())
    kwargs.setdefault("agent_name", "Atlas Reviewer")
    kwargs.setdefault("home", "atlas-mcp")
    kwargs.setdefault("transport", "mcp")
    kwargs.setdefault(
        "budget", {"scope": "task", "token_limit": 20000,
                   "command_limit": 40})
    return ExternalSeat(**kwargs)


def _book_data():
    return {
        "schema": EXTERNAL_AGENTS_SCHEMA, "slice": EXTERNAL_AGENTS_SLICE,
        "guide": {"title": "A seat book"},
        "seats": [
            {"seat_id": "seat-atlas", "member": _member(),
             "agent_name": "Atlas Reviewer", "home": "atlas-mcp",
             "transport": "mcp",
             "budget": {"scope": "task", "token_limit": 20000,
                        "command_limit": 40}},
            {"seat_id": "seat-ledger",
             "member": _member(
                 id="ledger_hand", name="Ledger Hand (external)",
                 office="scribe",
                 tools=["read_file", "write_file", "list_dir"],
                 posture="trusted-forge",
                 character="external_agent_characters/Ledger_Hand.md"),
             "agent_name": "Ledger Hand", "home": "ledger-mcp",
             "transport": "mcp",
             "budget": {"scope": "session", "cost_limit": 5.0,
                        "time_limit_seconds": 3600}},
        ],
        "checks": [
            {"check_id": "atlas-on-same-terms", "member": "atlas_reviewer"},
        ]}


def _write_seats(tmp_path, data):
    path = tmp_path / "seats.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_constants_and_usage():
    assert EXTERNAL_AGENTS_SLICE == "M-137"
    assert EXTERNAL_AGENTS_RESOURCE == "external_agents.yaml"
    assert EXTERNAL_AGENTS_SCHEMA == "mythic.external_agents/1"
    assert TRANSPORTS == ("mcp",)
    assert USAGE.startswith("Usage: /externals")
    assert "same contracts and budgets" in PLAIN_EXPLANATION
    assert "opens no MCP" in PLAIN_EXPLANATION


def test_shipped_example_book_shape():
    book = load_external_agents()
    assert book.title == "External seats at the M-136 slice boundary"
    assert len(book.seats) == 2
    assert book.member_ids() == ("atlas_reviewer", "ledger_hand")
    assert book.seat_ids() == ("seat-atlas", "seat-ledger")
    assert [s.member_id for s in book.seats_for("mcp")] == [
        "atlas_reviewer", "ledger_hand"]
    atlas = book.seat_for("atlas_reviewer")
    assert atlas.office == "auditor"
    assert atlas.posture == "read-only-scout"
    assert atlas.budget.scope == "task"
    assert atlas.budget.token_limit == 20000
    assert atlas.budget.command_limit == 40
    ledger = book.seat_for("ledger_hand")
    assert ledger.budget.scope == "session"
    assert ledger.budget.cost_limit == 5.0
    check = book.check_for("atlas-on-same-terms")
    assert check.member == "atlas_reviewer"
    assert check.verdict == "same_terms"
    assert check.findings == (
        "The seat's office is auditor, one of the "
        "shipped crew offices.",
        "The seat's posture is read-only-scout, one "
        "of the shipped crew postures.",
        "The seat's budget is per-task: 20000 tokens, "
        "40 commands.")


def test_example_seats_hold_shipped_contracts_and_budgets():
    casting_ids = [m.member_id for m in load_casting().members]
    for seat in load_external_agents().seats:
        # The seat's member is a NEW member - an
        # outsider, not one of the house cast -
        # yet its contract words are the shipped
        # crew's own words, and its budget scopes
        # are the budgets layer's own scopes.
        assert seat.member_id not in casting_ids
        assert seat.office in member_offices()
        assert seat.posture in POSTURES
        assert seat.budget.scope in BUDGET_SCOPES


def test_seat_validation_and_alias_spellings():
    seat = validate_seat({
        "id": "seat-atlas", "crew_member": _member(),
        "name": "Atlas Reviewer", "server": "atlas-mcp",
        "road": "model-context-protocol",
        "budget": {"scope": "task", "token_limit": 20000,
                   "command_limit": 40}})
    assert seat.seat_id == "seat-atlas"
    assert seat.member_id == "atlas_reviewer"
    assert seat.transport == "mcp"
    assert seat.home == "atlas-mcp"
    assert build_seat(seat) is seat
    with pytest.raises(ValueError):
        validate_seat({
            "member": _member(), "agent_name": "Atlas",
            "name": "Different Name", "home": "atlas-mcp",
            "transport": "mcp", "budget": {"scope": "task"}})
    with pytest.raises(ValueError):
        validate_seat({
            "member": _member(), "agent_name": "Atlas",
            "home": "atlas-mcp", "server": "other-mcp",
            "transport": "mcp", "budget": {"scope": "task"}})


def test_seat_refusals():
    base = {"member": _member(), "agent_name": "Atlas",
            "home": "atlas-mcp", "transport": "mcp",
            "budget": {"scope": "task"}}
    # A foreign privilege is an unknown key.
    with pytest.raises(ValueError):
        validate_seat({**base, "admin": True})
    with pytest.raises(ValueError):
        validate_seat({**base, "exempt_from_budget": True})
    # A contract word the internal crew does not use refuses
    # through the crew layer itself.
    with pytest.raises(ValueError):
        validate_seat({**base, "member": _member(office="overlord")})
    with pytest.raises(ValueError):
        validate_seat({**base, "member": _member(office="primary")})
    with pytest.raises(ValueError):
        validate_seat({**base, "member": _member(posture="root-access")})
    memberless = _member()
    del memberless["id"]
    with pytest.raises(ValueError):
        validate_seat({**base, "member": memberless})
    # A budget word the budgets layer does not use refuses
    # through the budgets layer itself.
    with pytest.raises(ValueError):
        validate_seat({**base, "budget": {"scope": "forever"}})
    with pytest.raises(ValueError):
        validate_seat({
            **base, "budget": {"scope": "task", "seat_limit": 5}})
    with pytest.raises(ValueError):
        validate_seat({**base, "transport": "carrier-pigeon"})
    with pytest.raises(ValueError):
        validate_seat({**base, "agent_name": "  "})
    with pytest.raises(ValueError):
        validate_seat({**base, "home": "two words"})
    no_budget = dict(base)
    del no_budget["budget"]
    with pytest.raises(ValueError):
        validate_seat(no_budget)
    with pytest.raises(ValueError):
        validate_seat("not a mapping")


def test_check_derivation_is_deterministic():
    seat = _seat()
    first = check_seat(seat)
    second = check_seat(seat)
    assert first == second
    assert first.verdict == "same_terms"
    assert first.member == "atlas_reviewer"
    assert "auditor" in first.findings[0]
    assert "read-only-scout" in first.findings[1]
    assert "per-task: 20000 tokens, 40 commands" in first.findings[2]
    unlimited = check_seat(_seat(budget={"scope": "session"}))
    assert "no limits named" in unlimited.findings[2]


def test_stored_check_must_agree_with_its_seat():
    seat = _seat()
    derived = check_seat(seat)
    filled = validate_check({"member": "atlas_reviewer"}, seat)
    assert filled.findings == derived.findings
    assert filled.verdict == "same_terms"
    with pytest.raises(ValueError):
        validate_check({
            "member": "atlas_reviewer", "transport": "mcp",
            "verdict": "same_terms",
            "findings": ["The seat may do anything."]}, seat)
    with pytest.raises(ValueError):
        validate_check({"member": "ledger_hand"}, seat)
    with pytest.raises(ValueError):
        validate_check({"member": "atlas_reviewer"})
    with pytest.raises(ValueError):
        SeatCheck(member="atlas_reviewer", transport="mcp",
                  verdict="trusted", findings=["A finding."])
    with pytest.raises(ValueError):
        validate_check({"member": "atlas_reviewer", "bogus": 1}, seat)
    built = build_check(check_seat(seat))
    assert built == derived


def test_normalize_transport_readings_and_refusals():
    assert normalize_transport("mcp") == "mcp"
    assert normalize_transport(" MCP ") == "mcp"
    assert normalize_transport("model-context-protocol") == "mcp"
    assert normalize_transport("Model_Context_Protocol") == "mcp"
    for bad in ("", "http", "grpc", None, 7):
        with pytest.raises(ValueError):
            normalize_transport(bad)


def test_book_validation_and_shared_view():
    book = validate_book(_book_data())
    assert isinstance(book, SeatBook)
    assert book.title == "A seat book"
    assert book.seat_for("ledger_hand").agent_name == "Ledger Hand"
    assert book.check_for("atlas-on-same-terms").verdict == "same_terms"
    with pytest.raises(KeyError):
        book.seat_for("nobody")
    with pytest.raises(KeyError):
        book.check_for("no-such-check")
    assert build_book(book) is book
    from_fields = build_book(title="T", seats=[_seat()])
    assert from_fields.member_ids() == ("atlas_reviewer",)


def test_book_refusals():
    data = _book_data()
    data["seats"].append(data["seats"][0])
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    twin = dict(data["seats"][1])
    twin["seat_id"] = "seat-atlas"
    data["seats"][1] = twin
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    data["checks"] = [{"check_id": "stray", "member": "nobody"}]
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    data["schema"] = "mythic.something_else/1"
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    data["surprise"] = True
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    del data["seats"]
    with pytest.raises(ValidationError):
        validate_book(data)
    with pytest.raises(ValidationError):
        validate_book("not a mapping")
    with pytest.raises(ValidationError):
        load_external_agents(_book_data())


def test_file_loader_round_trip_and_missing_file(tmp_path):
    path = _write_seats(tmp_path, _book_data())
    book = load_external_agents_file(path)
    assert book.title == "A seat book"
    assert book.member_ids() == ("atlas_reviewer", "ledger_hand")
    with pytest.raises(FileNotFoundError):
        load_external_agents_file(tmp_path / "missing.yaml")
    bad = _write_seats(tmp_path, {"schema": "nope"})
    with pytest.raises(ValidationError):
        load_external_agents_file(bad)


def test_registry_hold_and_check():
    registry = ExternalRegistry(load_external_agents())
    assert [s.member_id for s in registry.list_seats()] == [
        "atlas_reviewer", "ledger_hand"]
    assert registry.get_seat("ledger_hand").home == "ledger-mcp"
    assert [s.member_id for s in registry.seats_for("mcp")] == [
        "atlas_reviewer", "ledger_hand"]
    derived = registry.check_seat("atlas_reviewer")
    assert derived == check_seat(registry.get_seat("atlas_reviewer"))
    held_book = registry.book()
    assert held_book.title == "External seats at the M-136 slice boundary"
    assert held_book.checks == ()
    with pytest.raises(KeyError):
        registry.get_seat("nobody")


def test_registry_auto_ids_and_refusals():
    registry = ExternalRegistry()
    seat = registry.register_seat({
        "member": _member(), "agent_name": "Atlas Reviewer",
        "home": "atlas-mcp", "transport": "mcp",
        "budget": {"scope": "task"}})
    assert seat.seat_id == "external-1"
    second = registry.register_seat(_seat(
        seat_id=None,
        member=_member(id="ledger_hand", office="scribe",
                       posture="trusted-forge"),
        agent_name="Ledger Hand", home="ledger-mcp"))
    assert second.seat_id == "external-2"
    with pytest.raises(ValueError):
        registry.register_seat(_seat())
    with pytest.raises(ValueError):
        ExternalRegistry().book()
    titled = ExternalRegistry(load_external_agents())
    with pytest.raises(ValueError):
        titled.register_book(validate_book(_book_data()))


def test_records_are_session_news():
    book = load_external_agents()
    seat = book.seat_for("atlas_reviewer")
    record = seat_record(seat)
    assert record["type"] == "external_seat"
    assert record["slice"] == "M-137"
    assert record["news"] is True
    assert "atlas_reviewer" in record["headline"]
    assert record["member"]["office"] == "auditor"
    assert record["budget"]["scope"] == "task"
    whole = book_record(book)
    assert whole["type"] == "external_seat_book"
    assert whole["seat_count"] == 2
    assert whole["check_count"] == 1
    assert whole["news"] is True
    check = book.check_for("atlas-on-same-terms")
    crecord = check_record(check, seat)
    assert crecord["type"] == "external_seat_check"
    assert crecord["verdict"] == "same_terms"
    assert crecord["findings"] == list(check.findings)
    assert crecord["news"] is True


def test_plain_words_and_check_plain_words():
    book = load_external_agents()
    seat = book.seat_for("ledger_hand")
    words = plain_words(seat)
    assert words.startswith("ledger_hand - Ledger Hand")
    assert "scribe office" in words
    assert "per-session budget" in words
    told = check_plain_words(book)
    assert "External seats at the M-136 slice boundary" in told
    assert "atlas_reviewer - verdict same_terms" in told
    assert "20000 tokens" in told
    single = check_plain_words(book.check_for("atlas-on-same-terms"))
    assert "per-task" in single
    with pytest.raises(ValueError):
        check_plain_words("nope")


def test_formatters_and_screen():
    book = load_external_agents()
    line = format_seat(book.seat_for("atlas_reviewer"))
    assert "atlas_reviewer / seat-atlas [mcp] via atlas-mcp" in line
    assert "per-task budget" in line
    listing = format_seats(book)
    assert "ledger_hand" in listing
    assert format_seats(book, "mcp") == listing
    checks = format_check(book)
    assert "Checks in External seats at the M-136 slice boundary:" in checks
    assert "verdict same_terms" in checks
    assert "Nothing here." in format_check(SeatBook(title="T", seats=[]))
    assert format_transports() == "External transports: mcp"
    screen = format_external_agents_screen()
    assert "External agents as crew (M-137)" in screen
    assert "Atlas Reviewer" in screen
    assert USAGE in screen


def test_parse_external_args_grammar():
    assert parse_external_args("") == ("show", None)
    assert parse_external_args(None) == ("show", None)
    assert parse_external_args("show") == ("show", None)
    assert parse_external_args("list") == ("show", None)
    assert parse_external_args("seat atlas_reviewer") == (
        "seat", "atlas_reviewer")
    assert parse_external_args("check ledger_hand") == (
        "check", "ledger_hand")
    assert parse_external_args("mcp") == ("transport", "mcp")
    assert parse_external_args("model-context-protocol") == (
        "transport", "mcp")
    assert parse_external_args("transports") == ("transports", None)
    for bad in ("seat", "check", "seat a b", "dance", "http", 7):
        with pytest.raises(ValueError):
            parse_external_args(bad)


def test_no_live_roads_in_pure_layer():
    import mythic_agent.core.external_agents as module
    source = Path(module.__file__).read_text(encoding="utf-8")
    for banned in ("import subprocess", "import socket", "requests.",
                   "openai", "anthropic", "AgentManager",
                   "mythic_agent.agents", "mythic_agent.ui",
                   "import mcp", "mcp.client", "fastmcp",
                   "def spawn", "def persist", "def schedule"):
        assert banned not in source
    record = _seat().to_record()
    assert "connected" not in record
    assert record["transport"] == "mcp"

# -- agent layer -----------------------------------------------------------
#
# M-137 agent layer: the agent holds an
# ExternalRegistry for the session (session state
# only, no new setting), seats are held by being
# registered - published as their seat_record
# session news through the checkpoint road, deduped
# per member id - the report road renders the held
# book (or the shipped example when unheld) through
# the pure formatters, and the /externals surface
# rides both roads on the pure parser + formatters.
# Status, get, check, transport and book reads
# register and publish nothing, answer from the held
# registry first and from the shipped example only
# while nothing is held - a held session never falls
# back to the example. This layer opens no MCP
# session, spawns no agent, persists nothing, calls
# no model and claims no board - Part VIII does not
# exist yet, so the screen is where the seats are
# visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _external_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _path_seat():
    return _seat(
        seat_id="seat-path",
        member=_member(id="path_scout", name="Path Scout (external)"),
        agent_name="Path Scout", home="path-mcp",
        budget={"scope": "task", "token_limit": 1000,
                "command_limit": 5})


class TestExternalAgentsAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.external_agents_status()
        assert status["seats"] == []
        assert status["book"] is None
        assert status["agents"]["title"] == (
            "External seats at the M-136 slice boundary")
        assert [s["member"]["member_id"]
                for s in status["agents"]["seats"]] == [
            "atlas_reviewer", "ledger_hand"]
        assert [s["budget"]["scope"]
                for s in status["agents"]["seats"]] == [
            "task", "session"]
        assert status["book_record"]["type"] == "external_seat_book"
        assert status["book_record"]["seat_count"] == 2
        assert [c["check_id"] for c in status["checks"]] == [
            "atlas-on-same-terms"]
        assert status["checks"][0]["findings"][0] == (
            "The seat's office is auditor, one of the "
            "shipped crew offices.")
        assert "atlas_reviewer" in status["plain_words"][0]
        assert "atlas_reviewer - verdict same_terms" in \
            status["check_plain_words"]
        assert "External agents as crew (M-137)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert agent._external_agents_registry() is \
            agent._external_agents_registry()
        assert agent._external_agents_store is \
            agent._external_agents_registry()

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.external_agents_status()
        seat = agent.get_external_seat("atlas_reviewer")
        assert seat.agent_name == "Atlas Reviewer"
        assert seat.office == "auditor"
        check = agent.external_seat_check("atlas_reviewer")
        assert check.verdict == "same_terms"
        assert check.findings[2] == (
            "The seat's budget is per-task: 20000 tokens, "
            "40 commands.")
        assert [s.member_id for s in
                agent.external_seats_for_transport("mcp")] == [
            "atlas_reviewer", "ledger_hand"]
        assert [s.member_id for s in agent.external_seats_for_transport(
            "model_context_protocol")] == [
            "atlas_reviewer", "ledger_hand"]
        assert agent.external_agents().title == (
            "External seats at the M-136 slice boundary")
        registry = agent._external_agents_registry()
        assert registry.list_seats() == ()
        assert _external_events(store, session_id, "external_seat") == []
        agent.close()

    def test_unheld_get_and_check_raise_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.get_external_seat("no-such-member")
        with pytest.raises(KeyError):
            agent.external_seat_check("no-such-member")

    def test_status_after_register_shows_the_held_pieces(self, agent):
        agent.register_external_seat(_seat())
        status = agent.external_agents_status()
        assert [s["member"]["member_id"] for s in status["seats"]] == [
            "atlas_reviewer"]
        assert status["book"]["seat_count"] == 1
        # The held book answers now, not the example:
        # the session seats are the held seat alone.
        assert [s["member"]["member_id"]
                for s in status["agents"]["seats"]] == ["atlas_reviewer"]
        assert status["agents"]["title"] == "Session seat book"
        assert "Atlas Reviewer" in status["screen"]

    def test_held_session_never_falls_back_to_the_example(self, agent):
        agent.register_external_seat(_seat())
        with pytest.raises(KeyError):
            agent.get_external_seat("ledger_hand")
        with pytest.raises(KeyError):
            agent.external_seat_check("ledger_hand")
        assert [s.member_id for s in
                agent.external_seats_for_transport("mcp")] == [
            "atlas_reviewer"]
        assert agent.external_agents().member_ids() == ("atlas_reviewer",)
        assert agent.get_external_seat(
            "atlas_reviewer").agent_name == "Atlas Reviewer"


class TestExternalAgentsAgentRegister:
    def test_register_seat_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_external_seat(_seat())
        assert outcome["seat"]["member"]["member_id"] == "atlas_reviewer"
        assert outcome["record"]["type"] == "external_seat"
        events = _external_events(store, session_id, "external_seat")
        assert len(events) == 1
        assert events[0]["member"]["member_id"] == "atlas_reviewer"
        # The same record is never published twice.
        agent._publish_external_record(outcome["record"])
        assert len(_external_events(
            store, session_id, "external_seat")) == 1
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
        from mythic_agent.core.crew_sizing import (
            case_record as _sizing_case_record,
            load_crew_sizing,
        )
        from mythic_agent.core.review_panels import (
            load_review_panel,
            review_record,
        )
        from mythic_agent.core.stand_ups import (
            entry_record as _stand_up_entry_record,
            load_stand_up,
        )
        agent._publish_external_record(profile_record(
            load_character_voices().profiles[0]))
        agent._publish_external_record(_sizing_case_record(
            load_crew_sizing().cases[0]))
        agent._publish_external_record({
            "type": "crew_sizing_recommendation_set"})
        agent._publish_external_record(_stand_up_entry_record(
            load_stand_up().entries[0]))
        memory = load_crew_memory()
        agent._publish_external_record(_memory_entry_record(
            memory.entry_for("broken-checkpoint-chain")))
        panel = load_review_panel()
        agent._publish_external_record(review_record(panel.reviews[0]))
        agent._publish_external_record(casting_record(
            load_casting().members[0]))
        agent._publish_external_record(book_record(load_external_agents()))
        agent._publish_external_record(check_record(check_seat(_seat())))
        for kind in ("character_voice_profile", "crew_sizing_case",
                     "crew_sizing_recommendation_set", "stand_up_entry",
                     "crew_memory_entry", "panel_review", "crew_member",
                     "external_seat_book", "external_seat_check"):
            assert _external_events(store, session_id, kind) == []
        assert len(_external_events(
            store, session_id, "external_seat")) == 1
        agent.close()

    def test_duplicate_member_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_external_seat(_seat())
        with pytest.raises(ValueError):
            agent.register_external_seat(_seat(seat_id="seat-other"))
        assert len(_external_events(
            store, session_id, "external_seat")) == 1
        agent.close()

    def test_register_seat_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_external_seat_book(load_external_agents())
        assert outcome["count"] == 2
        assert outcome["book"]["seat_count"] == 2
        events = _external_events(store, session_id, "external_seat")
        assert [e["member"]["member_id"] for e in events] == [
            "atlas_reviewer", "ledger_hand"]
        assert agent.external_agents().title == (
            "External seats at the M-136 slice boundary")
        assert agent.get_external_seat(
            "ledger_hand").agent_name == "Ledger Hand"
        agent.close()

    def test_register_seat_book_twice_refuses(self, agent):
        agent.register_external_seat_book(load_external_agents())
        with pytest.raises(ValueError):
            agent.register_external_seat_book(load_external_agents())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_external_seat()
        assert outcome["count"] == 2
        assert outcome["book"]["seat_count"] == 2
        events = _external_events(store, session_id, "external_seat")
        assert [e["member"]["member_id"] for e in events] == [
            "atlas_reviewer", "ledger_hand"]
        assert agent.external_agents().title == (
            "External seats at the M-136 slice boundary")
        assert agent.get_external_seat(
            "ledger_hand").office == "scribe"
        # The recorded book stands whole: its held
        # example check still answers, and a check for
        # the other seat derives from its seat.
        assert agent.external_agents().checks[0].check_id == (
            "atlas-on-same-terms")
        assert agent.external_seat_check(
            "ledger_hand").verdict == "same_terms"
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_external_seat()
        with pytest.raises(ValueError):
            agent.record_external_seat()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_seats(tmp_path, _book_data())
        book = load_external_agents_file(path)
        outcome = agent.record_external_seat(book)
        assert outcome["count"] == 2
        assert agent.external_agents().title == "A seat book"
        assert agent.get_external_seat(
            "ledger_hand").agent_name == "Ledger Hand"
        assert agent.external_seat_check(
            "atlas_reviewer").findings[0] == (
            "The seat's office is auditor, one of the "
            "shipped crew offices.")

    def test_one_by_one_seats_stand_under_a_session_book(
            self, agent):
        agent.register_external_seat(_path_seat())
        # Held one by one, the seats stand under a
        # session seat book composed in the agent
        # layer - never under a recorded book's title.
        assert agent.external_agents().title == "Session seat book"
        assert agent.external_seat_check(
            "path_scout").verdict == "same_terms"
        # A later whole book under its own title is
        # never refused by the shim title.
        book = build_book(_book_data())
        outcome = agent.record_external_seat(book)
        assert outcome["count"] == 2
        assert agent.external_agents().title == "A seat book"


class TestExternalAgentsAgentReport:
    def test_report_renders_the_example_when_unheld(self, agent):
        outcome = agent.report_external_agents()
        assert outcome["book"]["title"] == (
            "External seats at the M-136 slice boundary")
        assert outcome["book"]["seat_count"] == 2
        assert "atlas_reviewer" in outcome["seats_text"]
        assert "ledger_hand" in outcome["seats_text"]
        assert "atlas_reviewer - verdict same_terms" in \
            outcome["check_text"]
        assert outcome["transports"] == "External transports: mcp"
        assert "External agents as crew (M-137)" in outcome["screen"]
        assert outcome["explanation"] == PLAIN_EXPLANATION

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_external_seat(_seat())
        outcome = agent.report_external_agents()
        assert outcome["book"]["seat_count"] == 1
        assert "atlas_reviewer" in outcome["seats_text"]
        assert "ledger_hand" not in outcome["seats_text"]
        assert "atlas_reviewer - verdict same_terms" in \
            outcome["check_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_external_agents()
        registry = agent._external_agents_registry()
        assert registry.list_seats() == ()
        assert _external_events(store, session_id, "external_seat") == []
        agent.close()

    def test_no_generate_persist_or_model_road(self, agent):
        # This layer holds the seats as data: it opens
        # no MCP session, spawns no agent, persists
        # nothing and calls no model - and there is no
        # Part VIII board yet.
        assert not hasattr(agent, "generate_external_agents")
        assert not hasattr(agent, "persist_external_agents")
        assert not hasattr(agent, "spawn_external_agent")
        assert not hasattr(agent, "connect_external_agent")
        assert not hasattr(agent, "open_mcp_session")
        assert not hasattr(agent, "external_agents_board")


class TestExternalAgentsTerminalSurface:
    def test_show_seat_check_transport_and_transports(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/externals")
        assert "External agents as crew (M-137)" in text
        _, _, text = _slash(agent, "/externals seat atlas_reviewer")
        assert "Atlas Reviewer" in text
        assert "auditor office" in text
        _, _, text = _slash(agent, "/externals check atlas_reviewer")
        assert "atlas_reviewer - verdict same_terms" in text
        assert "office is auditor" in text
        _, _, text = _slash(agent, "/externals mcp")
        assert "atlas_reviewer" in text
        assert "ledger_hand" in text
        _, _, text = _slash(agent, "/externals transports")
        assert text == "External transports: mcp"

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/externals [show|seat <member-id>|check <member-id>|"
                "mcp|transports]") in text
        _, _, text = _slash(agent, "/externals dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/externals seat missing-member")
        assert "no seat in the book for member" in text


@pytest.fixture()
def externals_handler(agent, monkeypatch):
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


def _externals_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestExternalAgentsCommand:
    def test_show_is_default(self, externals_handler, agent):
        externals_handler._handle_externals("")
        assert "External agents as crew (M-137)" in \
            _externals_published_text(externals_handler)

    def test_seat_check_transport_and_transports(
            self, externals_handler, agent):
        externals_handler._handle_externals("seat atlas_reviewer")
        assert "Atlas Reviewer" in _externals_published_text(
            externals_handler)
        externals_handler._handle_externals("check atlas_reviewer")
        assert "verdict same_terms" in _externals_published_text(
            externals_handler)
        externals_handler._handle_externals("mcp")
        assert "ledger_hand" in _externals_published_text(externals_handler)
        externals_handler._handle_externals("transports")
        assert "External transports: mcp" in _externals_published_text(
            externals_handler)

    def test_bad_grammar_is_published(self, externals_handler, agent):
        externals_handler._handle_externals("dance party")
        assert USAGE in _externals_published_text(externals_handler)


class TestChatScreenRoutingExternals:
    def test_externals_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/externals transports", _FakeLog())
        assert calls == [("/externals", "transports")]
