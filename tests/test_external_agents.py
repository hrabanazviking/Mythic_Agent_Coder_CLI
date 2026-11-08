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
