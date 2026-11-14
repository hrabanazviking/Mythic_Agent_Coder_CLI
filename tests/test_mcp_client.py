"""M-233 Cross-app method - pure-layer tests.

TIER: integration

The pure layer is the tracker, held as data: one
record per connection, held whole - the server it
answers for, discovered by server id, its title, the
steps it walked in walk connection and the evidence
it carries, held by server. The question walk is
explicit - discovered, inspected, permitted, connected,
held, with their legal steps held as data -
and a connection's standing is derived at call
time: a connection that opens anywhere but discovered, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet discovered held stands open,
discovered in its gaps. A connection stands only for
an active server: a connection naming no held
server, or one that is not active, refuses by
name. The connection's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, connection and current
connection are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, connected or
held live. The shipped example book is held
in a data file, and a loader reads a book from
any file. No charter row names this server: the
M-171 TUI charter binds Part VIII alone, and the
M-005 method charter names the whole of Part X
as the part that executes it, both pinned live
below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.mcp_client import (
    EXAMPLE_STAGE,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    STAGES,
    CLAIM_KINDS,
    TRANSITIONS,
    SERVER_STATES,
    STAGE_FIELDS,
    PLAIN_EXPLANATION,
    CONNECTION_RESOURCE,
    CONNECTION_RULE,
    CONNECTION_SCHEMA,
    CONNECTION_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    ConnectionRecord,
    IndexConnection,
    ServerRef,
    NoteRecord,
    ConnectionBook,
    ConnectionIndex,
    ConnectionPanel,
    ConnectionRegistry,
    ConnectionVerdict,
    ConnectionView,
    trace_for_connection,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_connection,
    build_server_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_connection,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    connection_for_check,
    connection_gaps,
    connection_connection,
    connection_record,
    connection_green,
    connections_for_server,
    first_note,
    format_book,
    format_connection,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_connection_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    server_record,
    load_connection,
    legal_step,
    load_connection_file,
    next_stage,
    normalize_stage,
    normalize_claim_kind,
    normalize_server_state,
    normalize_stance,
    normalize_view_filter,
    note_for_connection,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_connection_args,
    green_connections,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_connections,
    validate_book,
    validate_connection,
    validate_note,
    validate_panel,
    validate_row,
    validate_verdict,
    validate_view,
    verdict_plain_words,
    verdict_record,
    view_plain_words,
    view_record,
)
from mythic_agent.core.method_charter import (
    load_charter as load_method_charter,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]
ON = "2026-11-11"
BY = "the coordinator"
EXAMPLE_TITLE = "MCP client at the M-233 slice run"
EXAMPLE_STAGES = ["held", "held", "held"]
EXAMPLE_RUN_IDS = (
    "connection-held-connection", "connection-retried-connection",
    "connection-own-connection", "connection-bare-connection",
    "connection-leaping-connection")
EXAMPLE_TRACE = "discovered > inspected > permitted > connected > held"


def _ref(**overrides):
    fields = {
        "server_id": "server-test",
        "seq": 1,
        "title": "A test server",
        "state": "live",
        "detail": "A test server reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "connection-test",
    }
    fields.update(overrides)
    return build_server_ref(fields)


def _connection(**overrides):
    fields = {
        "connection_id": "connection-test",
        "seq": 1,
        "server_id": "server-test",
        "title": "A test connection",
        "stages": ["discovered", "inspected", "permitted", "connected", "held"],
        "claims": [],
        "detail": "A test connection held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "connection-test",
    }
    fields.update(overrides)
    return build_connection(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "connection-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "connection_id": "connection-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "connection-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "connection_id": "connection-test",
        "trace": "discovered > inspected > permitted > connected > held",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "connection-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(servers=None, connections=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": CONNECTION_SCHEMA,
        "server": "M-233",
        "mcp_client": {"title": "A test connection book"},
        "servers": [item.to_record() for item in (
            servers if servers is not None else [_ref()])],
        "connection_records": [item.to_record() for item in (
            connections if connections is not None else [_connection()])],
        "views": [item.to_record() for item in (
            views if views is not None else [_view()])],
        "notes": [item.to_record() for item in (notes or [])],
        "traces": [item.to_record() for item in (
            traces or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(connections=[
        _connection(),
        _connection(connection_id="connection-hidden", seq=2,
               title="A hidden connection", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_connection()
    assert book.title == EXAMPLE_TITLE
    assert book.connection_ids() == EXAMPLE_RUN_IDS
    assert book.server_ids() == (
        "server-filesystem", "server-search",
        "server-remote")
    assert [v.view_id for v in book.views] == [
        "view-connections", "view-held"]
    assert [m.connection_id for m in book.notes] == [
        "connection-held-connection", "connection-bare-connection"]
    assert [a.connection_id for a in book.traces] == ["connection-held-connection"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-filesystem"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.connection_ids())
    derived = derive_panel(book, "view-connections")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-connections").verdict == "held"
    assert derive_verdict(book, "view-connections").green_shown == 3
    assert derive_verdict(book, "view-held").verdict == "held"
    assert derive_verdict(book, "view-held").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / CONNECTION_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == CONNECTION_SCHEMA
    assert raw["server"] == "M-233"
    assert "verdict" not in raw
    assert "connection_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-233")]
    assert slice_.title == "MCP client"
    assert slice_.part == 10
    assert "Mythic *consumes* MCP servers (tools, resources, prompts) with per-server permissions under" in slice_.summary
    assert "the missing half of its MCP face" in slice_.summary
    assert CONNECTION_SLICE == "M-233"

def test_charter_rows_do_not_name_m233():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-233" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert STAGE_FIELDS == ("stages", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("held", "held", "blocked")
    assert SERVER_STATES == ("live", "dormant")
    assert STAGES == ("discovered", "inspected", "permitted", "connected", "held")
    assert HELD_EVIDENCE == ("tools_ref", "resources_ref", "prompts_ref", "manifest_ref", "policy_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["connected"] == ("discovered", "held")
    assert TRANSITIONS["held"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "held"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_server_state("LIVE") == "live"
    assert normalize_stage("PERMITTED") == "permitted"
    assert normalize_claim_kind("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_server_state("blessed")
    with pytest.raises(ValueError):
        normalize_stage("polish")
    with pytest.raises(ValueError):
        normalize_claim_kind("weather")
    assert legal_step("permitted", "connected") is True
    assert legal_step("inspected", "held") is False
    assert legal_step("held", "discovered") is False
    assert next_stage("discovered") == "inspected"
    assert next_stage("permitted") == "connected"
    assert next_stage("connected", failed=True) == "discovered"
    assert next_stage("connected") == "held"
    assert next_stage("held") is None
    assert "held as data alone" in CONNECTION_RULE
    assert "connection sequence" in CONNECTION_RULE
    assert "M-233" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /mcpclient")

def test_shipped_book_judged_honestly_as_data():
    book = load_connection()
    opening = book.connection_for("connection-held-connection")
    assert connection_green(opening, book) is True
    assert connection_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Connection: The held connection",
        "Server: server-filesystem",
        "Stage: held",
        "Claims: tools_ref")
    asking = book.connection_for("connection-bare-connection")
    assert connection_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert connection_green(asking, book) is False
    skipping = book.connection_for("connection-leaping-connection")
    assert connection_gaps(skipping, book) == (
        "steps from inspected to held, which the connection sequence "
        "does not allow",)
    assert [g.connection_id for g in green_connections(book)] == [
        "connection-held-connection", "connection-retried-connection", "connection-own-connection"]
    index = derive_index(book)
    assert [e.stage for e in index.connections] == EXAMPLE_STAGES
    assert index.gaps == ("connection-bare-connection", "connection-leaping-connection")
    assert connection_for_check(book, EXAMPLE_STAGE).connection_id == (
        "connection-held-connection")
    assert connection_for_check(book, "triple connection") is None
    assert transition_breaks(book) == (
        "connection-leaping-connection: inspected > held",)
    assert [g.connection_id for g in connection_connection(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "connection-held-connection") == EXAMPLE_TRACE
    assert trace_current(book, "connection-held-connection") is True
    assert trace_current(book, "connection-retried-connection") is False
    assert trace_for_connection(
        book, "connection-held-connection").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_connection(
        book, "connection-held-connection", "note").note_id == (
            "note-note-first")
    assert note_for_connection(book, "connection-nope") is None
    assert current_connection(book).connection_id == "connection-bare-connection"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "connection_records": 3},
        {"standing": "open", "connection_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_connection"] == "connection-bare-connection"
    assert ledger["traces"] == [
        {"connection_id": "connection-held-connection", "trace": "current"},
        {"connection_id": "connection-retried-connection", "trace": "unheld"},
        {"connection_id": "connection-own-connection", "trace": "unheld"},
        {"connection_id": "connection-bare-connection", "trace": "unheld"},
        {"connection_id": "connection-leaping-connection", "trace": "unheld"}]
    assert ledger["breaks"] == ["connection-leaping-connection: inspected > held"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 268
    assert citizen["next_slice"] == "M-269"
    assert citizen["m233_title"] == "MCP client"
    assert citizen["m233_part"] == 10
    assert citizen["m233_status"] == "done"

def test_connection_record_round_trips():
    connection = _connection()
    assert validate_connection(connection) is connection
    rebuilt = build_connection(connection.to_record())
    assert rebuilt == connection
    assert rebuilt.item_id == "connection-test"
    assert rebuilt.stage == "held"
    record = connection_record(connection)
    assert record["type"] == "connection_connection"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert server_record(ref)["type"] == "connection_run"
    assert server_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _connection(stages=[])
    assert connection_gaps(silent) == (
        "has passed through no step: the connection has not started",)
    assert connection_green(silent) is False
    walking = _connection(stages=["discovered", "inspected"])
    assert connection_gaps(walking) == (
        "has not reached held: the connection stands at inspected",)
    assert walking.stage == "inspected"
    sideways = _connection(stages=["inspected", "permitted", "connected", "held"])
    assert connection_gaps(sideways) == (
        "opens at inspected, not at discovered: the connection opens "
        "with the reflection",)
    repaired = _connection(stages=["discovered", "inspected", "permitted", "connected", "discovered", "inspected", "permitted", "connected", "held"])
    assert connection_gaps(repaired) == ()
    assert connection_green(repaired) is True
    with pytest.raises(ValueError):
        _connection(stages=[42])
    with pytest.raises(ValueError):
        _connection(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _connection(stages=["discovered", "polish"])
    with pytest.raises(ValueError):
        _connection(claims=["weather"])
    with pytest.raises(ValueError):
        _connection(claims="tools_ref")
    none_connection = _connection(stages=None, claims=None)
    assert none_connection.stages == ()
    assert none_connection.claims == ()

def test_policy_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "connections", "coverage", "current_connection",
                "ledger", "connection"):
        fields = _connection().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_connection(fields)
    fields = _connection().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_connection(fields)


def test_policy_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _connection().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_connection(fields)


def test_connection_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _connection(title="")
    with pytest.raises(ValueError):
        _connection(server_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "discovered > inspected > permitted > connected > held"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_connections_own_fields():
    connection = _connection(claims=["tools_ref"])
    assert plain_lines(connection) == (
        "Connection: A test connection",
        "Server: server-test",
        "Stage: held",
        "Claims: tools_ref")
    segment = segment_of(connection)
    assert segment.startswith("connection-test: A test connection")
    assert "stage: 'held'" in segment
    assert "gaps: none" in segment
    assert plain_words(connection).startswith(
        "A test connection - from server-test")

def test_red_connections_stand_named_in_their_gaps():
    asking = _connection(claims=["feeling", "tools_ref", "summary"])
    assert connection_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert connection_green(asking) is False
    skipping = _connection(stages=["discovered", "inspected", "held"])
    assert connection_gaps(skipping) == (
        "steps from inspected to held, which the connection sequence "
        "does not allow",)
    book = _book(connections=[
        _connection(),
        _connection(connection_id="connection-skipping", seq=2,
             stages=["discovered", "inspected", "held"]),
    ])
    assert transition_breaks(book) == (
        "connection-skipping: inspected > held",)
    assert current_connection(book).connection_id == "connection-skipping"
    assert [g.connection_id for g in connection_connection(book)] == [
        "connection-test", "connection-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "connection_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "connection_note"
    assert record["connection_id"] == "connection-test"
    assert view_plain_words(view) == "View view-test: shows all connections."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_connections_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.connections] == ["held"]
    assert index.connections[0] == IndexConnection(
        stage="held",
        connection_id="connection-test", title="A test connection")
    assert index.gaps == ("connection-hidden",)
    record = index_record(book)
    assert record["type"] == "connection_index"
    assert record["gaps"] == ["connection-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "connection_book"

def test_check_target_reaches_its_connection_and_an_unheld_target_reaches_nothing():
    book = load_connection()
    assert connection_for_check(book, "held").connection_id == (
        "connection-held-connection")
    assert connection_for_check(book, "") is None
    assert connection_for_check(book, None) is None
    assert connection_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_connection()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Connection note note connection-held-connection" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").connection_id == "connection-test"
    assert note_for_connection(book, "connection-test").note_id == "note-test"
    assert note_for_connection(book, "connection-test", "praise") is None
    with pytest.raises(KeyError):
        book.note_for("note-nope")
    with pytest.raises(ValueError):
        _book(notes=[_note(), _note(note_id="note-two", seq=2)])


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert panel.panel_id == "panel-view-test"
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 1, "open": 1}
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book) == panel
    row = build_row(None, _connection(), book)
    assert row.standing == "complete"
    assert validate_row(row, _connection(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_connections():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "connection_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "held"
    empty_book = _book(connections=[_connection(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(ConnectionVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_connections():
    book = load_connection()
    assert [g.connection_id for g in shown_connections(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.connection_id for g in shown_connections(book, "view-held")] == [
        "connection-held-connection", "connection-retried-connection", "connection-own-connection"]
    assert [g.connection_id for g in connections_for_server(
        book, "server-search")] == [
            "connection-own-connection", "connection-bare-connection",
            "connection-leaping-connection"]
    assert connections_for_server(book, "server-nope") == ()
    assert current_connection(_mixed_book()).connection_id == "connection-hidden"
    assert current_connection(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "connection-test") == (
        "discovered > inspected > permitted > connected > held")
    assert trace_current(stale, "connection-test") is False
    assert ledger_record(stale)["traces"] == [
        {"connection_id": "connection-test", "trace": "stale"}]

def test_resources_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(connections=[_connection(), _connection(seq=2)])
    with pytest.raises(ValueError):
        _book(connections=[_connection(), _connection(connection_id="connection-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(connections=[_connection(server_id="server-nope")])
    with pytest.raises(ValueError):
        _book(servers=[_ref(), _ref(
            server_id="server-cold", seq=2, state="dormant")],
            connections=[_connection(server_id="server-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(server_id="server-nope")])
    fields = {
        "schema": CONNECTION_SCHEMA, "server": "M-233",
        "mcp_client": {"title": "A permitted book"},
        "servers": [_ref().to_record()],
        "connection_records": [_connection().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "held"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_connection"] = "connection-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_connection")
    fields["trace"] = "connection-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / CONNECTION_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "mcp_client.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_connection_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.connection_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = ConnectionRegistry()
    assert registry.title() is None
    registry.register_server_ref(_ref())
    registry.register_connection(_connection())
    registry.register_view(_view())
    assert [g.connection_id for g in registry.list_connections()] == ["connection-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_connection("connection-test").title == "A test connection"
    assert registry.get_slice("server-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("connection-test").connection_id == "connection-test"
    with pytest.raises(ValueError):
        registry.register_connection(_connection(seq=9))
    with pytest.raises(ValueError):
        registry.register_connection(_connection(connection_id="connection-two"))
    with pytest.raises(KeyError):
        registry.get_connection("connection-nope")
    assert registry.book().title == "An unheld connection book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = ConnectionRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test connection book"
    assert registry.title() == "A test connection book"
    assert len(registry.list_connections()) == 2
    other = ConnectionRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    connection = _connection()
    assert "A test connection" in plain_words(connection)
    assert panel_plain_words(_mixed_book()).startswith(
        "The connection book holds 2 connections")
    assert verdict_plain_words(_mixed_book()) == (
        "The connections stand held: 1 of 2 shown connections stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green connections; red, "
        "discovered in its gaps: connection-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_connection(connection)
    assert "Connection: A test connection" in text
    assert "stands complete" in text
    text = format_connection(_connection(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The MCP Client (M-233) - A test connection book" in book_text
    assert "connection-hidden" in format_book(_mixed_book(), "server-test")
    assert "Connection panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "held - A test connection (connection-test)" in index_text
    assert "connection-hidden" in index_text
    screen = format_connection_screen()
    assert "The MCP Client (M-233)" in screen
    assert "connection-bare-connection" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_connection_args("") == ("show", None)
    assert parse_connection_args(None) == ("show", None)
    assert parse_connection_args("show") == ("show", None)
    assert parse_connection_args("connection connection-test") == (
        "connection", "connection-test")
    assert parse_connection_args("stage held") == (
        "stage", "held")
    assert parse_connection_args("server server-test") == (
        "server", "server-test")
    assert parse_connection_args("view view-test") == ("view", "view-test")
    assert parse_connection_args("note note-test") == ("note", "note-test")
    assert parse_connection_args("index") == ("index", None)
    assert parse_connection_args("panel") == ("panel", None)
    assert parse_connection_args("verdict") == ("verdict", None)
    for bad in ("dance", "connection", "stage", "server", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_connection_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "connection_well"
    assert ledger["total"] == 5
    assert ledger["current_connection"] == "connection-bare-connection"
    book = load_connection({
        "schema": CONNECTION_SCHEMA, "server": "M-233",
        "mcp_client": {"title": "A permitted book"},
        "servers": [_ref().to_record()],
        "connection_records": [_connection().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, ConnectionBook)
    assert book.title == "A permitted book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_connection({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_connection({"server": "M-999"})
    built = build_connection(
        connection_id="connection-kw", seq=3, server_id="server-test",
        title="Kw Connection", stages=["discovered", "inspected", "permitted", "connected", "held"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="connection-test")
    assert built.connection_id == "connection-kw"
    assert connection_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-233 agent layer: the agent holds a connection
# book for the session, connections and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held connections, the ledger is derived from
# the held connections' completeness, the roadmap standing
# is connected from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no server. This layer connections
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_CONNECTION_EVENT_TYPES = (
    "connection_connection", "connection_run", "connection_view",
    "connection_panel", "connection_verdict")


def _connection_events(store, session_id, server):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == server]


def _write_mcpclient_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / CONNECTION_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "mcp_client.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestConnectionAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.mcpclient_status()
        assert status["connection_records"] == []
        assert status["servers"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["mcpclient_book"]["title"] == EXAMPLE_TITLE
        assert len(status["mcpclient_book"]["servers"]) == 3
        assert len(status["mcpclient_book"]["connection_records"]) == 5
        assert len(status["mcpclient_book"]["views"]) == 2
        assert len(status["mcpclient_book"]["notes"]) == 2
        assert len(status["mcpclient_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-filesystem"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["connections"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "connection-bare-connection", "connection-leaping-connection"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_connection"] == "connection-bare-connection"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 268
        assert status["roadmap"]["next_slice"] == "M-269"
        assert status["roadmap"]["m233_title"] == "MCP client"
        assert "held as data alone" in status["rule"]
        assert "connection-bare-connection" in status["plain_words"]
        assert "The MCP Client (M-233)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._mcpclient_registry()
        assert agent._mcpclient_registry() is first
        assert agent._mcpclient_store is first
        for name in ("mcpclient_book", "mcpclient_status", "mcpclient_panel",
                     "mcpclient_verdict", "mcpclient_index", "report_mcpclient"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_mcpclient_registry", "mcpclient_book", "mcpclient_status",
            "get_mcpclient_connection", "get_mcpclient_view", "get_mcpclient_note",
            "connections_for_server", "mcpclient_green",
            "mcpclient_panel", "mcpclient_verdict", "mcpclient_index",
            "register_mcpclient_connection", "register_mcpclient_view",
            "view_mcpclient", "register_mcpclient_book",
            "record_mcpclient_book", "report_mcpclient",
            "_publish_mcpclient_record", "_mcpclient_screen",
            "_mcpclient_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.mcpclient_status()
        assert agent.get_mcpclient_connection(
            "connection-held-connection").title == "The held connection"
        assert agent.get_mcpclient_view(
            "view-connections").view_filter == "all"
        assert agent.get_mcpclient_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.connection_id for d in agent.connections_for_server(
            "server-search")] == [
            "connection-own-connection", "connection-bare-connection",
            "connection-leaping-connection"]
        assert [d.connection_id for d in agent.mcpclient_green()] == [
            "connection-held-connection", "connection-retried-connection", "connection-own-connection"]
        agent.mcpclient_panel()
        agent.mcpclient_verdict()
        agent.mcpclient_index()
        agent.report_mcpclient()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _CONNECTION_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_mcpclient_connection("connection-nope")
        with pytest.raises(KeyError):
            agent.get_mcpclient_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_mcpclient_note("note-nope")
        with pytest.raises(ValueError):
            agent.connections_for_server("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_mcpclient_connection(_connection())
        status = agent.mcpclient_status()
        assert [d["connection_id"] for d in status["connection_records"]] == ["connection-test"]
        assert status["book"]["title"] == "An unheld connection book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["connections"]] == [
            "held"]
        assert status["first_note"] is None
        assert "connection-test" in status["screen"]
    def test_held_connection_never_falls_back_to_the_example(
            self, agent):
        agent.register_mcpclient_connection(_connection())
        with pytest.raises(KeyError):
            agent.get_mcpclient_connection("connection-held-connection")
        with pytest.raises(KeyError):
            agent.get_mcpclient_view("view-connections")
        with pytest.raises(KeyError):
            agent.get_mcpclient_note("note-note-first")
        connection = agent.get_mcpclient_connection("connection-test")
        assert connection.title == "A test connection"
        assert agent.mcpclient_book().title == (
            "An unheld connection book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_mcpclient_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.connection_id == "connection-held-connection"
        status = agent.mcpclient_status()
        assert status["index"]["gaps"] == [
            "connection-bare-connection", "connection-leaping-connection"]
        assert status["first_note"]["connection_id"] == (
            "connection-held-connection")
        assert status["first_note"]["stance"] == "note"

class TestConnectionAgentHolding:
    def test_register_connection_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_mcpclient_connection(_connection())
        assert result["connection"]["connection_id"] == "connection-test"
        assert result["record_news"]["type"] == "connection_connection"
        assert "connection-test" in result["screen"]
        events = _connection_events(store, session_id, "connection_connection")
        assert len(events) == 1
        agent.close()

    def test_duplicate_policy_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_mcpclient_connection(_connection())
        with pytest.raises(ValueError):
            agent.register_mcpclient_connection(_connection(seq=9))
        with pytest.raises(ValueError):
            agent.register_mcpclient_connection(_connection(connection_id="connection-two"))
        events = _connection_events(store, session_id, "connection_connection")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_mcpclient_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_connection_events(
            store, session_id, "connection_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_mcpclient_connection(_connection())
        result = agent.view_mcpclient("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "connection_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "held"
        assert len(_connection_events(
            store, session_id, "connection_view")) == 1
        assert len(_connection_events(
            store, session_id, "connection_panel")) == 1
        assert len(_connection_events(
            store, session_id, "connection_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_connection(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_mcpclient_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "connection_run", "connection_connection", "connection_view"]
        assert len(_connection_events(
            store, session_id, "connection_connection")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_mcpclient_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "connection_panel"
        assert result["index_record"]["gaps"] == [
            "connection-bare-connection", "connection-leaping-connection"]
        with pytest.raises(ValueError):
            agent.record_mcpclient_book()
        assert len(_connection_events(
            store, session_id, "connection_run")) == 3
        assert len(_connection_events(
            store, session_id, "connection_connection")) == 5
        assert len(_connection_events(
            store, session_id, "connection_view")) == 2
        agent.close()

    def test_book_from_a_file_is_linked_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_mcpclient_book_file(tmp_path)
        book = load_connection_file(path)
        result = agent.record_mcpclient_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        connection = agent.report_mcpclient()
        assert connection["book"]["title"] == EXAMPLE_TITLE
        assert connection["verdict"]["verdict"] == "held"
        assert connection["index"]["gaps"] == [
            "connection-bare-connection", "connection-leaping-connection"]
        assert "connection-held-connection" in connection["book_text"]
        assert "held - The held connection (connection-held-connection)" in connection["index_text"]
        agent.register_mcpclient_connection(_connection())
        connection = agent.report_mcpclient()
        assert connection["book"]["title"] == "An unheld connection book"
        assert connection["panel"] is None
        assert connection["verdict"] is None

class TestConnectionTerminalHeading:
    def test_show_connection_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/mcpclient")
        assert "The MCP Client (M-233)" in text
        _, _, text = _slash(agent, "/mcpclient connection connection-held-connection")
        assert "Connection: The held connection" in text
        _, _, text = _slash(
            agent, "/mcpclient stage held")
        assert "Connection: The held connection" in text
        _, _, text = _slash(agent, "/mcpclient stage triple connection")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/mcpclient server server-search")
        assert "connection-bare-connection" in text
        assert "connection-held-connection" not in text
        _, _, text = _slash(agent, "/mcpclient view view-connections")
        assert "filter all" in text
        _, _, text = _slash(agent, "/mcpclient note note-note-first")
        assert "Connection note note connection-held-connection" in text
        _, _, text = _slash(agent, "/mcpclient index")
        assert "Connection index" in text
        assert "connection-bare-connection" in text
        _, _, text = _slash(agent, "/mcpclient panel")
        assert "Connection panel under view view-connections" in text
        _, _, text = _slash(agent, "/mcpclient verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/mcpclient [show|connection <connection-id>"
                "|stage <stage>|server <server-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/mcpclient dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/mcpclient connection connection-nope")
        assert "no connection discovered" in text
@pytest.fixture()
def connection_handler(agent, monkeypatch):
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


def _connection_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestConnectionCommand:
    def test_show_is_default(self, connection_handler, agent):
        connection_handler._handle_mcpclient("")
        assert "The MCP Client (M-233)" in (
            _connection_published_text(connection_handler))

    def test_connection_check_slice_view_note_index_panel_verdict(
            self, connection_handler, agent):
        connection_handler._handle_mcpclient("connection connection-held-connection")
        assert "Connection: The held connection" in _connection_published_text(
            connection_handler)
        connection_handler._handle_mcpclient(
            "stage held")
        assert "Connection: The held connection" in _connection_published_text(
            connection_handler)
        connection_handler._handle_mcpclient("server server-search")
        assert "connection-bare-connection" in _connection_published_text(
            connection_handler)
        connection_handler._handle_mcpclient("view view-connections")
        assert "filter all" in _connection_published_text(connection_handler)
        connection_handler._handle_mcpclient("note note-note-first")
        assert "Connection note note connection-held-connection" in (
            _connection_published_text(connection_handler))
        connection_handler._handle_mcpclient("index")
        assert "Connection index" in _connection_published_text(connection_handler)
        connection_handler._handle_mcpclient("panel")
        assert "Connection panel under view" in _connection_published_text(
            connection_handler)
        connection_handler._handle_mcpclient("verdict")
        assert "held" in _connection_published_text(connection_handler)
    def test_bad_grammar_is_published(
            self, connection_handler, agent):
        connection_handler._handle_mcpclient("dance party")
        assert USAGE in _connection_published_text(connection_handler)
        connection_handler._handle_mcpclient("connection connection-nope")
        assert "no connection discovered" in _connection_published_text(
            connection_handler)


class TestChatScreenRoutingConnection:
    def test_onwell_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/mcpclient panel", _FakeLog())
        assert calls == [("/mcpclient", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/mcpclient[/green] - show the MCP client (M-233)" in (
            text)
        assert ('"/mcpclient": "Usage: /mcpclient | '
                '/mcpclient connection <connection-id>') in text

class TestConnectionDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.mcpclient_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-connections"
        verdict = agent.mcpclient_verdict()
        assert verdict.verdict == "held"
        found = agent.mcpclient_verdict("view-held")
        assert found.verdict == "held"
        assert found.green_shown == 3
        agent.register_mcpclient_connection(_connection())
        with pytest.raises(ValueError):
            agent.mcpclient_panel()
        with pytest.raises(ValueError):
            agent.mcpclient_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_mcpclient_connection(_connection(stages=[]))
        result = agent.view_mcpclient("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.mcpclient_index()
        assert [e["stage"] for e in result["index"]["connections"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "connection-bare-connection", "connection-leaping-connection"]
        assert "held - The held connection (connection-held-connection)" in (
            result["index_text"])
        connection = agent.get_mcpclient_connection("connection-leaping-connection")
        assert connection_gaps(connection, agent.mcpclient_book()) == (
            "steps from inspected to held, which the connection sequence "
            "does not allow",)
        assert connection_green(connection, agent.mcpclient_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _CONNECTION_EVENT_TYPES] == []
        agent.close()
