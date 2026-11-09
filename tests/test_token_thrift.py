"""M-160 Token thrift - pure-layer tests.

TIER: integration

The pure layer is the thrift record itself, held as
data: one read, load or edit taken by a thrift road
(diff-first reading, map-first loading, hash-anchored
edits), carried with its provenance whole (what was
read, loaded or edited, the road used, the reference
it stands under, the baseline tokens the plain road
would have cost against the actual tokens it cost,
who recorded it, the day, and where it was read
from), composed by import from the shipped holdings
it measures (the cost court, M-140, the context
budget, M-147, pinning and protection, M-159, and the
compaction glass-box, M-151), each judged by its own
layer's validation, a thrift panel derived from the
whole book in settled order - thrift is a reported
virtue - a thrift cost line derived for the panel's
totals through the shared rate table (the line
`mythic costs` reports), the shipped example book
held in a data file, and a loader that reads a book
from any file. One thing is counted once per road in
a book. Nothing here reads any live file, edits any
code, calls a model, intercepts any live read or
writes any project's files: holding a record declares
a measured saving, and that is the whole road.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.compaction_glassbox import (
    load_compaction_glassbox,
)
from mythic_agent.core.context_budget import (
    build_item as build_context_item,
    load_context_budget,
)
from mythic_agent.core.cost_court import (
    build_entry as build_cost_entry,
    load_cost_court,
)
from mythic_agent.core.pinning_protection import (
    load_pinning_protection,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.token_thrift import (
    TOKEN_THRIFT_RESOURCE,
    TOKEN_THRIFT_SCHEMA,
    TOKEN_THRIFT_SLICE,
    THRIFT_ROADS,
    PLAIN_EXPLANATION,
    USAGE,
    ThriftBook,
    ThriftCostLine,
    ThriftPanel,
    ThriftPanelRow,
    ThriftRecord,
    ThriftRegistry,
    ThriftRoadCount,
    book_record,
    build_book,
    build_cost_line,
    build_panel,
    build_record,
    build_row,
    cost_line_plain_words,
    cost_line_record,
    derive_cost_line,
    derive_panel,
    format_cost_line,
    format_panel,
    format_thrift_record,
    format_thrift_records,
    format_token_thrift_screen,
    inspect_thrift_source,
    load_token_thrift,
    load_token_thrift_file,
    normalize_thrift_road,
    panel_plain_words,
    panel_record,
    parse_thrift_args,
    plain_words,
    thrift_from_compaction_record,
    thrift_from_context_item,
    thrift_from_cost_entry,
    thrift_from_pin,
    thrift_record,
    thrift_records_from_context,
    thrift_refs,
    total_saved,
    validate_book,
    validate_cost_line,
    validate_panel,
    validate_record,
    validate_row,
)

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Token thrift at the M-159 slice boundary"

BY = "Volmarr"
ON = "2026-11-08"


def _record(**overrides):
    fields = {
        "record_id": "thrift-test",
        "subject": "the test file, read diff-first",
        "road": "diff-first",
        "ref": "file-test",
        "baseline_tokens": 1000,
        "actual_tokens": 250,
        "recorded_by": BY,
        "recorded_on": ON,
        "source": "test source",
    }
    fields.update(overrides)
    return build_record(fields)


def _stored_record(record):
    stored = record.to_record()
    stored.pop("type")
    stored.pop("slice")
    stored.pop("tokens_saved")
    stored.pop("savings_percent")
    return stored


def _stored_panel(panel):
    stored = panel.to_record()
    stored.pop("type")
    stored.pop("slice")
    for row in stored["rows"]:
        row.pop("type")
        row.pop("slice")
    return stored


def _stored_line(line):
    stored = line.to_record()
    stored.pop("type")
    stored.pop("slice")
    return stored


def _book(records=None, **overrides):
    fields = {
        "title": "A test thrift book",
        "records": [_stored_record(item) for item in (
            records if records is not None else [_record()])],
    }
    fields.update(overrides)
    return build_book(fields)


def _shipped_raw():
    path = ROOT / "mythic_agent" / "data" / "token_thrift.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_constants_and_usage():
    assert TOKEN_THRIFT_SLICE == "M-160"
    assert TOKEN_THRIFT_SCHEMA == "mythic.token_thrift/1"
    assert TOKEN_THRIFT_RESOURCE == "token_thrift.yaml"
    assert THRIFT_ROADS == (
        "diff-first", "map-first", "hash-anchored")
    assert "reported virtue" in PLAIN_EXPLANATION
    assert "reads no files itself" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /thrift")
    assert "record <record-id>" in USAGE


def test_roadmap_boundary_is_derived_from_the_shipped_roadmap():
    road = load_roadmap()
    ids = [item.id for item in road.slices]
    assert "M-160" in ids
    mine = road.slices[ids.index("M-160")]
    assert mine.title == "Token thrift"
    assert mine.part == 7
    assert "diff-first" in mine.summary
    assert "mythic" in mine.summary
    for earlier in road.slices[:ids.index("M-160")]:
        assert earlier.status == "done", earlier.id


def test_shipped_example_shape():
    book = load_token_thrift()
    assert isinstance(book, ThriftBook)
    assert book.title == EXAMPLE_TITLE
    assert book.record_ids() == (
        "thrift-diff-pinning", "thrift-map-context",
        "thrift-hash-edit", "thrift-diff-tests")
    assert book.total_records == 4
    first = book.records[0]
    assert first.subject == (
        "mythic_agent/core/pinning_protection.py, "
        "read diff-first")
    assert first.road == "diff-first"
    assert first.tokens_saved == 16300
    assert first.recorded_by == "Volmarr"
    assert first.recorded_on == "2026-11-08"
    assert len(book.panels) == 1


def test_shipped_panel_is_pinned_and_derived():
    book = load_token_thrift()
    panel = book.panel_for("panel-m159-boundary")
    derived = derive_panel(book)
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert [row.record_id for row in panel.rows] == [
        "thrift-diff-pinning", "thrift-diff-tests",
        "thrift-map-context", "thrift-hash-edit"]
    assert panel.total_records == 4
    assert panel.total_baseline == 38400
    assert panel.total_actual == 6940
    assert panel.total_saved == 31460


def test_normalizers_and_aliases():
    assert normalize_thrift_road("Diff") == "diff-first"
    assert normalize_thrift_road("READING") == "diff-first"
    assert normalize_thrift_road("map") == "map-first"
    assert normalize_thrift_road("Loading") == "map-first"
    assert normalize_thrift_road("hash") == "hash-anchored"
    assert normalize_thrift_road("ANCHOR") == "hash-anchored"
    assert normalize_thrift_road("edits") == "hash-anchored"
    with pytest.raises(ValueError):
        normalize_thrift_road("whole-file")


def test_record_validation_and_alias_spellings():
    record = _record()
    assert isinstance(record, ThriftRecord)
    assert record.tokens_saved == 750
    assert record.savings_percent == 75.0
    aliased = build_record({
        "what": "the aliased load", "road": "map",
        "reference": "map-x", "baseline": 800,
        "actual": 200, "by": "Volmarr",
        "day": "2026-11-08", "source": "the map"})
    assert aliased.subject == "the aliased load"
    assert aliased.road == "map-first"
    assert aliased.ref == "map-x"
    assert aliased.recorded_by == "Volmarr"
    with pytest.raises(ValueError):
        build_record({"subject": "the bare read"})
    with pytest.raises(ValueError):
        _record(recorded_on="08/11/2026")
    with pytest.raises(ValueError):
        _record(recorded_on="2026-13-01")
    with pytest.raises(ValueError):
        _record(road="whole-file")
    # A stored saving refuses: the saving is derived.
    stored = _stored_record(_record())
    stored["tokens_saved"] = 750
    with pytest.raises(ValueError, match="unknown thrift-record keys"):
        build_record(stored)


def test_record_refuses_missing_provenance():
    fields = _stored_record(_record())
    fields.pop("recorded_by")
    with pytest.raises(ValueError, match="missing its"):
        build_record(fields)
    fields = _stored_record(_record())
    fields.pop("source")
    with pytest.raises(ValueError, match="missing its"):
        build_record(fields)
    fields = _stored_record(_record())
    fields["bogus"] = "nope"
    with pytest.raises(ValueError, match="unknown thrift-record keys"):
        build_record(fields)


def test_record_refuses_unmeasured_or_negative_thrift():
    with pytest.raises(ValueError, match="baseline"):
        _record(baseline_tokens=0)
    with pytest.raises(ValueError, match="must not exceed"):
        _record(actual_tokens=1001)
    # Spending exactly the baseline is measured and
    # stands: it saves nothing, and says so.
    even = _record(actual_tokens=1000)
    assert even.tokens_saved == 0


def test_book_refuses_duplicate_record_and_duplicate_thing():
    with pytest.raises(ValueError, match="already exists"):
        _book([_record(), _record(subject="another subject")])
    # One thing is counted once per road in a book,
    # under any second record id or subject.
    with pytest.raises(ValueError, match="counted once"):
        _book([_record(), _record(record_id="thrift-copy")])
    # The same reference by another road is another
    # measure, and the same road on another reference
    # is another measure: both stand.
    book = _book([_record(), _record(
        record_id="thrift-map", subject="the test map load",
        road="map-first"),
        _record(record_id="thrift-other", subject="the other read",
                ref="file-other")])
    assert book.total_records == 3


def test_record_for_ref_in_book():
    book = load_token_thrift()
    record = book.record_for_ref("maps", "map-session-context")
    assert record.record_id == "thrift-map-context"
    assert isinstance(book.record_for("thrift-diff-pinning"), ThriftRecord)
    with pytest.raises(KeyError):
        book.record_for_ref("diff-first", "file-nope")
    with pytest.raises(KeyError):
        book.record_for("thrift-nope")


def test_composition_from_cost_entry():
    entry = build_cost_entry({
        "entry_id": "run-thrift-1", "member": "cartographer",
        "slice_id": "M-160", "model": "gpt-4o",
        "input_tokens": 300, "output_tokens": 100})
    record = thrift_from_cost_entry(
        entry, road="diff-first", baseline_tokens=2000,
        recorded_by=BY, recorded_on=ON)
    assert record.ref == "run-thrift-1"
    assert record.actual_tokens == 400
    assert record.tokens_saved == 1600
    assert record.subject == "cost-court run run-thrift-1"
    # Only the id and the measure cross: the entry's
    # own words stand in no record this road builds.
    blob = str(record.to_record())
    assert "cartographer" not in blob
    assert "gpt-4o" not in blob
    shipped = [e for e in load_cost_court().entries if e.entry_id]
    assert shipped
    record = thrift_from_cost_entry(
        shipped[0], road="map-first", baseline_tokens=100000,
        recorded_by=BY, recorded_on=ON)
    assert record.ref == shipped[0].entry_id
    assert record.actual_tokens == (
        shipped[0].input_tokens + shipped[0].output_tokens)


def test_composition_from_context_item():
    item = build_context_item({
        "item_id": "ctx-map-x", "kind": "map_section",
        "title": "A map title of its own",
        "source": "workspace", "reason": "It is loaded.",
        "tokens": 120})
    record = thrift_from_context_item(
        item, baseline_tokens=1200, recorded_by=BY, recorded_on=ON)
    assert record.road == "map-first"
    assert record.ref == "ctx-map-x"
    assert record.actual_tokens == 120
    assert "A map title of its own" not in str(record.to_record())
    panel = load_context_budget()
    first = [i for i in panel.items if i.item_id][0]
    record = thrift_from_context_item(
        first, baseline_tokens=first.tokens + 500,
        recorded_by=BY, recorded_on=ON)
    assert record.ref == first.item_id
    assert record.tokens_saved == 500


def test_composition_from_pin():
    book = load_pinning_protection()
    pin = book.pins[0]
    record = thrift_from_pin(
        pin, road="diff-first", baseline_tokens=900,
        actual_tokens=90, recorded_by=BY, recorded_on=ON)
    assert record.ref == pin.ref
    assert record.subject == f"pinned {pin.kind} {pin.ref}"
    blob = str(record.to_record())
    assert pin.subject not in blob
    assert pin.why not in blob


def test_composition_from_compaction_record():
    book = load_compaction_glassbox()
    source_record = book.records[0]
    record = thrift_from_compaction_record(
        source_record, road="hash-anchored", baseline_tokens=5000,
        actual_tokens=400, recorded_by=BY, recorded_on=ON)
    assert record.ref == source_record.record_id
    assert record.subject == (
        f"compaction record {source_record.record_id}")
    blob = str(record.to_record())
    assert source_record.title not in blob
    assert source_record.summary not in blob
    for piece in source_record.replaced:
        assert piece not in blob


def test_composition_requires_the_baseline_and_recorder():
    item = build_context_item({
        "item_id": "ctx-x", "kind": "note",
        "title": "A note title", "source": "session",
        "reason": "It is carried.", "tokens": 5})
    with pytest.raises(ValueError, match="baseline"):
        thrift_from_context_item(
            item, baseline_tokens=None, recorded_by=BY, recorded_on=ON)
    with pytest.raises(ValueError, match="who recorded it"):
        thrift_from_context_item(
            item, baseline_tokens=100, recorded_by=None, recorded_on=ON)
    with pytest.raises(ValueError, match="missing its"):
        validate_record({"road": "diff-first", "ref": "file-x"})


def test_plural_composition_road_from_context():
    panel = load_context_budget()
    items = [i for i in panel.items if i.item_id]
    assert items
    baselines = {i.item_id: i.tokens * 4 for i in items}
    records = thrift_records_from_context(
        panel, baselines=baselines, recorded_by=BY, recorded_on=ON)
    assert len(records) == len(items)
    assert {r.road for r in records} == {"map-first"}
    assert all(r.tokens_saved == r.actual_tokens * 3 for r in records)
    blob = str([r.to_record() for r in records])
    for item in items:
        assert item.title not in blob
    short = dict(baselines)
    short.pop(items[0].item_id)
    with pytest.raises(ValueError, match="no baseline is named"):
        thrift_records_from_context(
            panel, baselines=short, recorded_by=BY, recorded_on=ON)


def test_inspection_road():
    item = build_context_item({
        "item_id": "ctx-seen", "kind": "file",
        "title": "A file title", "source": "workspace",
        "reason": "It is read.", "tokens": 42})
    seen = inspect_thrift_source(item)
    assert seen == {"ref": "ctx-seen", "actual_tokens": 42}
    entry = build_cost_entry({
        "entry_id": "run-seen", "member": "cartographer",
        "slice_id": "M-160", "model": "gpt-4o",
        "input_tokens": 10, "output_tokens": 2})
    seen = inspect_thrift_source(entry)
    assert seen == {"ref": "run-seen", "actual_tokens": 12}
    pin = load_pinning_protection().pins[0]
    seen = inspect_thrift_source(pin)
    assert seen == {"ref": pin.ref, "actual_tokens": None}
    seen = inspect_thrift_source(load_compaction_glassbox().records[0])
    assert seen == {
        "ref": "compact-pruner-boundary", "actual_tokens": None}
    with pytest.raises(ValueError):
        inspect_thrift_source(object())


def test_book_validation_refusals():
    raw = _shipped_raw()
    raw["schema"] = "mythic.other/1"
    with pytest.raises(ValidationError):
        validate_book(raw)
    raw = _shipped_raw()
    raw["panels"][0]["total_saved"] = 9
    with pytest.raises(ValidationError):
        validate_book(raw)
    raw = _shipped_raw()
    raw["records"][1]["ref"] = "file-pinning-protection"
    with pytest.raises(ValidationError):
        validate_book(raw)
    raw = _shipped_raw()
    raw["guide"]["title"] = "A different title"
    with pytest.raises(ValidationError):
        validate_book(raw, require_example=True)


def test_load_token_thrift_file_roundtrip(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "token_thrift.yaml").read_text(encoding="utf-8")
    path = tmp_path / "token_thrift.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_token_thrift_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.record_ids()[0] == "thrift-diff-pinning"
    with pytest.raises(FileNotFoundError):
        load_token_thrift_file(tmp_path / "nope.yaml")


def test_registry_holds_records_one_by_one():
    registry = ThriftRegistry()
    held = registry.register_record({
        "subject": "the held read", "road": "diff-first",
        "ref": "file-held", "baseline_tokens": 500,
        "actual_tokens": 50, "recorded_by": BY,
        "recorded_on": ON, "source": "test"})
    assert held.record_id == "thrift-1"
    second = registry.register_record(_record())
    assert second.record_id == "thrift-test"
    assert registry.latest_record().record_id == "thrift-test"
    assert [r.record_id for r in registry.list_records()] == [
        "thrift-1", "thrift-test"]
    with pytest.raises(ValueError, match="counted once"):
        registry.register_record(_record(record_id="thrift-copy"))
    with pytest.raises(ValueError):
        registry.register_record(_record())
    with pytest.raises(KeyError):
        registry.get_record("thrift-nope")
    assert registry.record_for_ref(
        "diff-first", "file-test").record_id == "thrift-test"
    named = ThriftRegistry()
    named.register_book(_book())
    assert named.book().title == "A test thrift book"
    assert named.panel().total_records == 1
    assert named.cost_line().tokens_saved == 750
    with pytest.raises(ValueError):
        named.register_book(_book(title="Another title"))


def test_panel_row_judged_against_its_record():
    record = _record()
    panel = derive_panel(_book([record]))
    row = panel.rows[0]
    assert isinstance(row, ThriftPanelRow)
    assert validate_row(row, record) == row
    bad = build_row({
        "record_id": "thrift-test", "subject": "another subject",
        "road": "diff-first", "ref": "file-test",
        "baseline_tokens": 1000, "actual_tokens": 250,
        "tokens_saved": 750, "recorded_by": BY, "recorded_on": ON})
    with pytest.raises(ValueError, match="disagrees"):
        validate_row(bad, record)
    # A row whose saving is not its measures'
    # difference refuses at construction.
    with pytest.raises(ValueError, match="derived"):
        build_row({
            "record_id": "thrift-test", "subject": "the test read",
            "road": "diff-first", "ref": "file-test",
            "baseline_tokens": 1000, "actual_tokens": 250,
            "tokens_saved": 700, "recorded_by": BY,
            "recorded_on": ON})
    counts = panel.road_counts
    assert counts == (ThriftRoadCount(
        road="diff-first", records=1, saved_tokens=750),)


def test_panel_validation_refusals():
    book = _book()
    panel = derive_panel(book)
    stored = _stored_panel(panel)
    assert validate_panel(stored, book) == panel
    bad = _stored_panel(panel)
    bad["total_saved"] = 9
    with pytest.raises(ValueError):
        validate_panel(bad)
    bad = _stored_panel(panel)
    bad["account"] = ["A different account."]
    with pytest.raises(ValueError, match="disagrees"):
        validate_panel(bad, book)
    built = build_panel(_stored_panel(panel))
    assert built == panel
    # Panel order is settled by road first: a
    # diff-first record held second still stands
    # before a hash-anchored record held first.
    mixed = _book([_record(
        record_id="thrift-hash", subject="the held edit",
        road="hash-anchored", ref="edit-test"), _record()])
    panel = derive_panel(mixed)
    assert [row.record_id for row in panel.rows] == [
        "thrift-test", "thrift-hash"]


def test_cost_line_is_derived_and_priced_by_the_shared_table():
    book = load_token_thrift()
    line = derive_cost_line(book)
    assert isinstance(line, ThriftCostLine)
    assert line.model == "gpt-4o"
    assert line.baseline_tokens == 38400
    assert line.actual_tokens == 6940
    assert line.tokens_saved == 31460
    # The shared table prices gpt-4o input at $2.50
    # per million tokens: the line is that arithmetic.
    assert line.baseline_cost_usd == 0.096
    assert line.actual_cost_usd == 0.01735
    assert line.saved_cost_usd == 0.07865
    assert line.priced is True
    # A model the table does not know prices at zero
    # and says so - no price is invented.
    unknown = derive_cost_line(book, "no-such-model-xyz")
    assert unknown.priced is False
    assert unknown.saved_cost_usd == 0.0
    assert unknown.tokens_saved == 31460


def test_cost_line_validation_refusals():
    book = load_token_thrift()
    line = derive_cost_line(book)
    stored = _stored_line(line)
    assert validate_cost_line(stored, book) == line
    assert build_cost_line(_stored_line(line)) == line
    bad = _stored_line(line)
    bad["tokens_saved"] = 9
    bad["actual_tokens"] = 38391
    with pytest.raises(ValueError):
        validate_cost_line(bad)
    bad = _stored_line(line)
    bad["saved_cost_usd"] = 0.5
    with pytest.raises(ValueError):
        validate_cost_line(bad)
    bad = _stored_line(line)
    bad["baseline_tokens"] = 100
    bad["actual_tokens"] = 25
    bad["tokens_saved"] = 75
    bad["baseline_cost_usd"] = 0.00025
    bad["actual_cost_usd"] = 0.000063
    bad["saved_cost_usd"] = 0.000187
    # Internally priced, but not this book's line.
    with pytest.raises(ValueError, match="disagrees"):
        validate_cost_line(bad, book)


def test_records_and_plain_words():
    record = _record()
    news = thrift_record(record)
    assert news["type"] == "token_thrift_record"
    assert news["news"] is True
    assert "750 tokens" in news["headline"]
    assert set(news) == {
        "type", "slice", "record_id", "subject", "road", "ref",
        "baseline_tokens", "actual_tokens", "tokens_saved",
        "savings_percent", "recorded_by", "recorded_on",
        "source", "news", "headline"}
    words = plain_words(record)
    assert "the test file" in words and "file-test" in words
    book = load_token_thrift()
    panel_news = panel_record(derive_panel(book), book)
    assert panel_news["headline"].startswith(
        "Thrift panel: 4 records")
    line_news = cost_line_record(derive_cost_line(book), book)
    assert line_news["type"] == "token_thrift_cost_line"
    assert "31460 tokens saved" in line_news["headline"]
    book_news = book_record(book)
    assert book_news["record_count"] == 4
    told = panel_plain_words(book)
    assert "thrift-map-context" in told
    assert "Every saving is measured" in told
    line_words = cost_line_plain_words(book)
    assert "31460 tokens saved" in line_words
    assert "shared rate table" in line_words


def test_formatters_and_screen():
    book = load_token_thrift()
    text = format_thrift_record(book.records[0])
    assert "thrift-diff-pinning" in text
    assert "file-pinning-protection" in text
    assert "reads no file and edits no code" in text
    assert "thrift-map-context" in format_thrift_records(book)
    maps = format_thrift_records(book, "maps")
    assert "thrift-map-context" in maps
    assert "thrift-diff-pinning" not in maps
    panel_text = format_panel(book)
    assert "Thrift panel in Token thrift" in panel_text
    line_text = format_cost_line(book)
    assert "Thrift cost line in Token thrift" in line_text
    assert "31460 tokens saved" in line_text
    screen = format_token_thrift_screen()
    assert "Token Thrift (M-160)" in screen
    assert USAGE in screen


def test_parse_thrift_args_grammar():
    assert parse_thrift_args("") == ("show", None)
    assert parse_thrift_args("show") == ("show", None)
    assert parse_thrift_args("list") == ("show", None)
    assert parse_thrift_args("record thrift-test") == (
        "record", "thrift-test")
    assert parse_thrift_args("road maps") == ("road", "map-first")
    assert parse_thrift_args("road diff-first") == (
        "road", "diff-first")
    assert parse_thrift_args("panel") == ("panel", None)
    assert parse_thrift_args("costs") == ("costs", None)
    for bad in ("dance", "record", "record a b", "road",
                "road whole-file", 5):
        with pytest.raises(ValueError):
            parse_thrift_args(bad)


def test_visible_surface_thrift_refs_and_total_saved():
    book = load_token_thrift()
    assert thrift_refs(book) == (
        ("diff-first", "file-pinning-protection"),
        ("diff-first", "file-pinning-tests"),
        ("map-first", "map-session-context"),
        ("hash-anchored", "edit-pins-wiring"))
    assert total_saved(book) == 31460
    assert total_saved(_book()) == 750


def test_honest_boundary_module_imports_no_live_roads():
    source = (ROOT / "mythic_agent" / "core"
              / "token_thrift.py").read_text(encoding="utf-8")
    assert "from .cost_court import" in source
    assert "from .costs import" in source
    assert "from .context_budget import" in source
    assert "from .pinning_protection import" in source
    assert "from .compaction_glassbox import" in source
    assert "from ..agents" not in source
    assert "from ..ui" not in source
    assert "from ..terminal" not in source
    assert "import agents" not in source


def test_registry_constructor_and_titleless_book_refusal():
    registry = ThriftRegistry(load_token_thrift())
    assert registry.book().title == EXAMPLE_TITLE
    assert registry.panel().total_records == 4
    assert registry.cost_line().tokens_saved == 31460
    bare = ThriftRegistry()
    bare.register_record(_record())
    with pytest.raises(ValueError, match="no thrift book is held"):
        bare.book()
    # The panel still derives from what stands held,
    # title or no title: derivation needs no book.
    assert bare.panel().total_records == 1
    assert isinstance(derive_panel(load_token_thrift()), ThriftPanel)
    direct = validate_record(_stored_record(_record()))
    assert direct == _record()


# -- agent layer -----------------------------------------------------------
#
# M-160 agent layer: the agent holds a ThriftRegistry
# for the session (session state only, no new setting),
# records are held by being registered - published as
# their thrift_record session news with the derived
# panel_record and cost_line_record, through the
# checkpoint road, deduped per shape - the report road
# renders the held book (or the shipped example when
# unheld) through the pure formatters, a thrift road
# reads the session's context-budget panel onto thrift
# records and holds them (mutating no live context),
# and the /thrift surface rides both roads on the pure
# parser + formatters. Status, get, panel, cost-line
# and report reads register and publish nothing, answer
# from the held registry first and from the shipped
# example only while nothing is held - a held session
# never falls back to the example. The panel and the
# cost line derive at call time from the whole book,
# never held. This layer calls no model, reads no live
# file, edits no code and persists nothing beyond the
# session journal news, and there is no Part VIII board
# yet, so the screen is where the book is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _thrift_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_thrift_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "token_thrift.yaml").read_text(encoding="utf-8")
    path = tmp_path / "token_thrift.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestThriftAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.token_thrift_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["thrifting"]["title"] == EXAMPLE_TITLE
        assert len(status["thrifting"]["records"]) == 4
        assert status["panel"]["total_saved"] == 31460
        assert status["panels"][0]["panel_id"] == "panel-m159-boundary"
        assert status["book_record"]["record_count"] == 4
        assert status["cost_line"]["tokens_saved"] == 31460
        assert status["cost_line"]["saved_cost_usd"] == 0.07865
        assert "Token Thrift (M-160)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._token_thrift_registry()
        assert agent._token_thrift_registry() is first
        assert agent._token_thrift_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.token_thrift_status()
        agent.get_thrift_record("thrift-diff-pinning")
        agent.token_thrift_panel()
        agent.token_thrift_cost_line()
        agent.report_token_thrift()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("token_thrift")] == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_thrift_record("thrift-nope")

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_thrift_record(_record())
        status = agent.token_thrift_status()
        assert [item["record_id"] for item in status["records"]] == [
            "thrift-test"]
        assert status["book"]["title"] == "Token thrift"
        assert status["cost_line"]["tokens_saved"] == 750

    def test_held_session_never_falls_back_to_the_example(
            self, agent):
        agent.register_thrift_record(_record())
        with pytest.raises(KeyError):
            agent.get_thrift_record("thrift-diff-pinning")
        record = agent.get_thrift_record("thrift-test")
        assert record.subject == "the test file, read diff-first"
        assert agent.token_thrift_book().title == "Token thrift"


class TestThriftAgentHolding:
    def test_register_record_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_thrift_record(_record())
        assert outcome["record"]["record_id"] == "thrift-test"
        assert outcome["record_news"]["type"] == "token_thrift_record"
        events = _thrift_events(
            store, session_id, "token_thrift_record")
        assert len(events) == 1
        assert events[0]["record_id"] == "thrift-test"
        agent._publish_thrift_record(outcome["record_news"])
        assert len(_thrift_events(
            store, session_id, "token_thrift_record")) == 1
        agent._publish_thrift_record(
            {"type": "mentions_mention", "mention_id": "mention-x"})
        agent._publish_thrift_record(
            book_record(load_token_thrift()))
        for kind in ("mentions_mention", "token_thrift_book"):
            assert _thrift_events(store, session_id, kind) == []
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_thrift_record(_record())
        with pytest.raises(ValueError):
            agent.register_thrift_record(_record())
        with pytest.raises(ValueError):
            agent.register_thrift_record(_record(record_id="thrift-copy"))
        assert len(_thrift_events(
            store, session_id, "token_thrift_record")) == 1
        agent.close()

    def test_thrift_from_session_context_carries_ids_only(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        panel = agent.context_budget_panel()
        items = [i for i in panel.items if i.item_id]
        expected = len(items)
        baselines = {i.item_id: i.tokens * 4 for i in items}
        outcome = agent.thrift_from_session_context(
            baselines=baselines, recorded_by="Volmarr",
            recorded_on="2026-11-08")
        assert outcome["count"] == expected
        assert outcome["total_saved"] == sum(
            i.tokens * 3 for i in items)
        events = _thrift_events(
            store, session_id, "token_thrift_record")
        assert len(events) == expected
        assert len(_thrift_events(
            store, session_id, "token_thrift_panel")) == 1
        assert len(_thrift_events(
            store, session_id, "token_thrift_cost_line")) == 1
        blob = str(events) + str(outcome["records"])
        for item in items:
            assert item.title not in blob
            assert item.reason not in blob
        # Counting mutated no live context: the
        # session's context panel stands whole.
        assert agent.context_budget_panel().items == panel.items
        assert agent.token_thrift_panel().total_records == expected
        with pytest.raises(ValueError):
            agent.thrift_from_session_context(
                baselines=baselines, recorded_by="Volmarr",
                recorded_on="2026-11-08")
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent):
        book = _book()
        outcome = agent.register_thrift_book(book)
        assert outcome["count"] == 1
        assert [item["type"] for item in outcome["records_news"]] == [
            "token_thrift_record"]
        assert agent.token_thrift_book().title == "A test thrift book"

    def test_register_book_twice_refuses(self, agent):
        agent.register_thrift_book(load_token_thrift())
        with pytest.raises(ValueError):
            agent.register_thrift_book(load_token_thrift())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_thrift_book()
        assert outcome["count"] == 4
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_thrift_events(
            store, session_id, "token_thrift_record")) == 4
        assert agent.token_thrift_book().panels[0].panel_id == (
            "panel-m159-boundary")
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_thrift_book()
        with pytest.raises(ValueError):
            agent.record_thrift_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_thrift_book(tmp_path)
        book = load_token_thrift_file(path)
        outcome = agent.record_thrift_book(book)
        assert outcome["count"] == 4
        assert agent.get_thrift_record(
            "thrift-diff-pinning").road == "diff-first"

    def test_report_renders_the_example_when_unheld(self, agent):
        report = agent.report_token_thrift()
        assert report["book"]["record_count"] == 4
        assert "thrift-diff-pinning" in report["records_text"]
        assert "Thrift panel in Token thrift" in report["panel_text"]
        assert "31460 tokens saved" in report["cost_line_text"]

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_thrift_record(_record())
        report = agent.report_token_thrift()
        assert report["book"]["title"] == "Token thrift"
        assert "thrift-diff-pinning" not in report["records_text"]
        assert "thrift-test" in report["records_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_token_thrift()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("token_thrift")] == []
        agent.close()

    def test_no_live_read_edit_or_persist_road(
            self, agent, tmp_path):
        # This layer holds thrift as data: it calls no
        # model, reads no live file, edits no code,
        # intercepts no live read and persists nothing
        # - and there is no Part VIII board yet.
        # Holding, recording or counting changes no
        # workspace file and no built context.
        assert not hasattr(agent, "apply_token_thrift")
        assert not hasattr(agent, "intercept_token_thrift")
        assert not hasattr(agent, "persist_token_thrift")
        assert not hasattr(agent, "token_thrift_board")
        (tmp_path / "alpha.py").write_text(
            "def greet(name):\n    return name\n", encoding="utf-8")
        before = {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")}
        from mythic_agent.agents.context import ContextBuilder
        builder = ContextBuilder(max_tokens=4000)
        builder.add_system("You are the coder.")
        builder.add_turn("user", "Build the slice.")
        built_before = builder.build()
        agent.register_thrift_record(_record())
        agent.record_thrift_book()
        panel = agent.context_budget_panel()
        agent.thrift_from_session_context(
            baselines={i.item_id: i.tokens * 2
                       for i in panel.items if i.item_id},
            recorded_by="Volmarr", recorded_on="2026-11-08",
            road="diff-first")
        assert builder.build() == built_before
        assert {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")} == before


class TestThriftTerminalSurface:
    def test_show_record_road_panel_costs(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/thrift")
        assert "Token Thrift (M-160)" in text
        _, _, text = _slash(agent, "/thrift record thrift-diff-pinning")
        assert "file-pinning-protection" in text
        _, _, text = _slash(agent, "/thrift road maps")
        assert "thrift-map-context" in text
        assert "thrift-diff-pinning" not in text
        _, _, text = _slash(agent, "/thrift panel")
        assert "Thrift panel in Token thrift" in text
        _, _, text = _slash(agent, "/thrift costs")
        assert "31460 tokens saved" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/thrift [show|record <record-id>"
                "|road <road>|panel|costs]") in text
        _, _, text = _slash(agent, "/thrift dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/thrift record thrift-nope")
        assert "no thrift record in the book" in text


@pytest.fixture()
def thrift_handler(agent, monkeypatch):
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


def _thrift_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestThriftCommand:
    def test_show_is_default(self, thrift_handler, agent):
        thrift_handler._handle_thrift("")
        assert "Token Thrift (M-160)" in (
            _thrift_published_text(thrift_handler))

    def test_record_road_panel_costs(self, thrift_handler, agent):
        thrift_handler._handle_thrift("record thrift-diff-pinning")
        assert "file-pinning-protection" in (
            _thrift_published_text(thrift_handler))
        thrift_handler._handle_thrift("road maps")
        assert "thrift-map-context" in (
            _thrift_published_text(thrift_handler))
        thrift_handler._handle_thrift("panel")
        assert "Thrift panel in Token thrift" in (
            _thrift_published_text(thrift_handler))
        thrift_handler._handle_thrift("costs")
        assert "31460 tokens saved" in (
            _thrift_published_text(thrift_handler))

    def test_bad_grammar_is_published(self, thrift_handler, agent):
        thrift_handler._handle_thrift("dance party")
        assert USAGE in _thrift_published_text(thrift_handler)


class TestChatScreenRoutingThrift:
    def test_thrift_routes_as_system_command(self, monkeypatch):
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
            "/thrift record thrift-diff-pinning", _FakeLog())
        assert calls == [("/thrift", "record thrift-diff-pinning")]
