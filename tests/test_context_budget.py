"""M-147 Context budget made visible - pure-layer tests.

TIER: integration

The pure layer is the context budget account as
data: a context budget panel book of context item
records (one thing in the context - its kind in
the closed set the shipped context system itself
justifies, its title, its source, the plain-words
reason it is in the context, and its token count)
against one token budget, the shipped example
panel held in a data file, a loader that reads a
panel from any file, a meter whose total, per-kind
subtotals, headroom, over-budget state and usage
are derived from the items, a panel whose rows,
totals and account are derived from the whole
book, a live measurement road through the shipped
TokenEstimator, a road that builds a panel from a
compiled context's blocks, records shaped as
session news, and a registry. Nothing here compiles
a context, assembles a prompt, calls a model or
persists anything: a stored meter disagreeing with
the meter derived from its own items is refused,
and a stored panel disagreeing with the panel
derived from its book is refused. The meter and
the panel are derived from the held items, never
stored loose: a stored total key on an item record
refuses as an unknown key.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.context.budget import TokenEstimator
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.context_budget import (
    PLAIN_EXPLANATION,
    CONTEXT_BUDGET_RESOURCE,
    CONTEXT_BUDGET_SCHEMA,
    CONTEXT_BUDGET_SLICE,
    ITEM_KINDS,
    USAGE,
    ContextBudgetPanel,
    ContextBudgetRegistry,
    ContextItem,
    ContextMeter,
    ContextPanel,
    KindTotal,
    PanelRow,
    book_record,
    build_budget_panel,
    build_item,
    build_meter,
    build_panel,
    derive_meter,
    derive_panel,
    format_context_budget_screen,
    format_item,
    format_items,
    format_meter,
    format_panel,
    item_record,
    load_context_budget,
    load_context_budget_file,
    measure_item,
    measure_panel,
    meter_plain_words,
    meter_record,
    panel_from_compiled,
    panel_plain_words,
    panel_record,
    parse_context_budget_args,
    plain_words,
    validate_book,
    validate_item,
    validate_meter,
    validate_panel,
)

ROOT = Path(__file__).resolve().parents[1]


def _item(**kwargs):
    kwargs.setdefault("item_id", "ctx-file-crew-schedules")
    kwargs.setdefault("kind", "file")
    kwargs.setdefault("title", "crew_schedules.py")
    kwargs.setdefault("source", "mythic_agent/core/crew_schedules.py")
    kwargs.setdefault(
        "reason", "The file under change in this session.")
    kwargs.setdefault("tokens", 1520)
    return ContextItem(**kwargs)


def _items():
    return [
        _item(),
        ContextItem(
            item_id="ctx-system-prompt", kind="system",
            title="System prompt", source="prompts.py",
            reason="The system prompt frames every answer.",
            tokens=640),
        ContextItem(
            item_id="ctx-note-slice", kind="note",
            title="Slice note M-147", source="session notes",
            reason="The keeper's slice note for this slice.",
            tokens=260),
        ContextItem(
            item_id="ctx-file-solo", kind="file",
            title="solo_mode.py", source="mythic_agent/core/solo_mode.py",
            reason="A sibling slice's file, read for its pattern.",
            tokens=480),
    ]


def _meter_mapping(meter):
    return {
        "meter_id": meter.meter_id,
        "budget_tokens": meter.budget_tokens,
        "total_tokens": meter.total_tokens,
        "total_items": meter.total_items,
        "headroom_tokens": meter.headroom_tokens,
        "over_budget": meter.over_budget,
        "usage_percent": meter.usage_percent,
        "kind_totals": [row.to_record() for row in meter.kind_totals],
        "account": list(meter.account)}


def _panel_mapping(panel):
    return {
        "panel_id": panel.panel_id,
        "rows": [row.to_record() for row in panel.rows],
        "budget_tokens": panel.budget_tokens,
        "total_tokens": panel.total_tokens,
        "total_items": panel.total_items,
        "headroom_tokens": panel.headroom_tokens,
        "over_budget": panel.over_budget,
        "account": list(panel.account)}


def test_constants_and_usage():
    assert CONTEXT_BUDGET_SLICE == "M-147"
    assert CONTEXT_BUDGET_SCHEMA == "mythic.context_budget/1"
    assert CONTEXT_BUDGET_RESOURCE == "context_budget.yaml"
    assert ITEM_KINDS == (
        "system", "instruction", "file", "map_section",
        "note", "history", "tool_result")
    assert "live meter" in PLAIN_EXPLANATION
    assert "data" in PLAIN_EXPLANATION and "only" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /contextbudget")
    assert "/contextbudget item <item-id>" in USAGE
    assert "/contextbudget kind <kind>" in USAGE
    assert "/contextbudget meter" in USAGE
    assert "/contextbudget panel" in USAGE


def test_shipped_example_shape():
    book = load_context_budget()
    assert isinstance(book, ContextBudgetPanel)
    assert book.title == "Context budget panel at the M-146 slice boundary"
    assert book.budget_tokens == 8000
    assert book.item_ids() == (
        "ctx-system-prompt", "ctx-instructions",
        "ctx-file-crew-schedules", "ctx-map-crew",
        "ctx-note-slice", "ctx-history-turns",
        "ctx-tool-result-tests")
    assert book.kinds() == ITEM_KINDS
    assert book.total_tokens() == 5660
    first = book.items[0]
    assert first.kind == "system" and first.tokens == 640
    assert book.item_for("ctx-map-crew").kind == "map_section"
    assert [e.item_id for e in book.items_for_kind("file")] == [
        "ctx-file-crew-schedules"]
    with pytest.raises(KeyError):
        book.item_for("ctx-nope")


def test_shipped_meter_and_panel():
    book = load_context_budget()
    assert [m.meter_id for m in book.meters] == ["meter-m146-boundary"]
    meter = book.meter_for("meter-m146-boundary")
    assert isinstance(meter, ContextMeter)
    assert meter.total_tokens == 5660 and meter.total_items == 7
    assert meter.headroom_tokens == 2340
    assert meter.over_budget is False
    assert meter.usage_percent == 70.8
    assert [(row.kind, row.tokens, row.items)
            for row in meter.kind_totals] == [
        ("system", 640, 1), ("instruction", 480, 1),
        ("file", 1520, 1), ("map_section", 720, 1),
        ("note", 260, 1), ("history", 1180, 1),
        ("tool_result", 860, 1)]
    derived = derive_meter(book)
    assert derived.kind_totals == meter.kind_totals
    assert derived.account == meter.account
    assert [p.panel_id for p in book.panels] == ["panel-m146-boundary"]
    panel = book.panel_for("panel-m146-boundary")
    assert isinstance(panel, ContextPanel)
    assert [r.item_id for r in panel.rows] == list(book.item_ids())
    assert panel.row_for("ctx-file-crew-schedules").share_percent == 26.9
    assert derive_panel(book).rows == panel.rows
    assert derive_panel(book).account == panel.account
    with pytest.raises(KeyError):
        panel.row_for("ctx-nope")


def test_record_validation_and_aliases():
    record = validate_item({
        "id": "ctx-file-crew-schedules", "kind": "file",
        "headline": "crew_schedules.py",
        "origin": "mythic_agent/core/crew_schedules.py",
        "why": "The file under change in this session.",
        "token_count": 1520})
    assert isinstance(record, ContextItem)
    assert record.item_id == "ctx-file-crew-schedules"
    assert record.kind == "file" and record.tokens == 1520
    record = record.to_record()
    assert record["type"] == "context_budget_item"
    assert record["slice"] == "M-147"
    assert record["reason"] == "The file under change in this session."


def test_two_spellings_refusals():
    with pytest.raises(ValueError):
        validate_item({
            "kind": "file", "title": "T", "headline": "Other",
            "source": "S", "reason": "R", "tokens": 10})
    with pytest.raises(ValueError):
        validate_item({
            "kind": "file", "title": "T", "source": "S",
            "reason": "R", "tokens": 10, "token_count": 11})
    with pytest.raises(ValueError):
        validate_item({
            "kind": "file", "title": "T", "source": "S",
            "origin": "Elsewhere", "reason": "R", "tokens": 10})


def test_unknown_key_refusals():
    base = {"kind": "file", "title": "T", "source": "S",
            "reason": "R", "tokens": 10}
    for key in ("total", "headroom", "share", "usage",
                "standing", "compiled", "bogus"):
        with pytest.raises(ValueError):
            validate_item({**base, key: 1})
    with pytest.raises(ValueError):
        validate_item({**base, "bogus": 1})


def test_malformed_records():
    with pytest.raises(ValueError):
        validate_item({
            "kind": "banana", "title": "T", "source": "S",
            "reason": "R", "tokens": 10})
    with pytest.raises(ValueError):
        validate_item({
            "kind": "file", "title": "T", "source": "S",
            "reason": "R", "tokens": -1})
    with pytest.raises(ValueError):
        validate_item({
            "kind": "file", "title": "T", "source": "S",
            "reason": "R", "tokens": True})
    with pytest.raises(ValueError):
        validate_item({
            "kind": "file", "title": "", "source": "S",
            "reason": "R", "tokens": 10})
    with pytest.raises(ValueError):
        validate_item({"kind": "file", "title": "T", "source": "S",
                       "tokens": 10})
    with pytest.raises(ValueError):
        validate_item("not a mapping")
    with pytest.raises(ValueError):
        ContextItem(kind="file", title="T", source="S",
                    reason="R", tokens=-5)


def test_meter_derivation():
    meter = derive_meter(_items(), 3000)
    assert meter.total_tokens == 2900 and meter.total_items == 4
    assert meter.headroom_tokens == 100
    assert meter.over_budget is False
    assert meter.usage_percent == 96.7
    assert [(row.kind, row.tokens, row.items)
            for row in meter.kind_totals] == [
        ("file", 2000, 2), ("system", 640, 1), ("note", 260, 1)]
    over = derive_meter(_items(), 2000)
    assert over.over_budget is True
    assert over.headroom_tokens == -900
    assert "over budget by 900" in over.account[0]
    with pytest.raises(ValueError):
        derive_meter([])
    with pytest.raises(ValueError):
        derive_meter(_items())


def test_stored_meter_judged():
    items = _items()
    meter = derive_meter(items, 3000)
    assert validate_meter(_meter_mapping(meter), items) == meter
    bad = _meter_mapping(meter)
    bad["total_tokens"] = 2901
    bad["headroom_tokens"] = 99
    bad["usage_percent"] = 96.7
    bad["kind_totals"] = [
        {"kind": "file", "tokens": 2001, "items": 2},
        {"kind": "system", "tokens": 640, "items": 1},
        {"kind": "note", "tokens": 260, "items": 1}]
    with pytest.raises(ValueError):
        validate_meter(bad, items)
    bad = _meter_mapping(meter)
    bad["account"] = ["A different account."]
    with pytest.raises(ValueError):
        validate_meter(bad, items)


def test_accountless_meter_refusal():
    mapping = _meter_mapping(derive_meter(_items(), 3000))
    del mapping["account"]
    with pytest.raises(ValueError):
        validate_meter(mapping)


def test_meter_internal_inconsistency_refuses():
    meter = derive_meter(_items(), 3000)
    with pytest.raises(ValueError):
        ContextMeter(
            budget_tokens=3000, total_tokens=2900, total_items=4,
            headroom_tokens=50, over_budget=False,
            usage_percent=96.7, kind_totals=meter.kind_totals,
            account=list(meter.account))
    with pytest.raises(ValueError):
        ContextMeter(
            budget_tokens=3000, total_tokens=2900, total_items=4,
            headroom_tokens=100, over_budget=False,
            usage_percent=50.0, kind_totals=meter.kind_totals,
            account=list(meter.account))
    with pytest.raises(ValueError):
        ContextMeter(
            budget_tokens=3000, total_tokens=2900, total_items=4,
            headroom_tokens=100, over_budget=False,
            usage_percent=96.7,
            kind_totals=[KindTotal(kind="file", tokens=2000, items=2)],
            account=list(meter.account))
    with pytest.raises(ValueError):
        ContextMeter(
            budget_tokens=3000, total_tokens=2900, total_items=3,
            headroom_tokens=100, over_budget=False,
            usage_percent=96.7, kind_totals=meter.kind_totals,
            account=list(meter.account))


def test_panel_derivation():
    panel = derive_panel(_items(), 3000)
    assert panel.total_tokens == 2900 and panel.total_items == 4
    assert panel.headroom_tokens == 100 and panel.over_budget is False
    assert [r.item_id for r in panel.rows] == [
        "ctx-file-crew-schedules", "ctx-system-prompt",
        "ctx-note-slice", "ctx-file-solo"]
    assert panel.rows[0].share_percent == 52.4
    assert panel.rows[1].share_percent == 22.1
    assert panel.row_for("ctx-note-slice").kind == "note"
    assert panel.to_record()["type"] == "context_budget_panel"
    with pytest.raises(ValueError):
        derive_panel([])


def test_stored_panel_judged():
    items = _items()
    panel = derive_panel(items, 3000)
    assert validate_panel(_panel_mapping(panel), items) == panel
    bad = _panel_mapping(panel)
    bad["rows"][0]["tokens"] = 1521
    bad["rows"][0]["share_percent"] = 52.4
    bad["total_tokens"] = 2901
    bad["headroom_tokens"] = 99
    with pytest.raises(ValueError):
        validate_panel(bad, items)
    bad = _panel_mapping(panel)
    bad["account"] = ["A different account."]
    with pytest.raises(ValueError):
        validate_panel(bad, items)
    bad = _panel_mapping(panel)
    del bad["account"]
    with pytest.raises(ValueError):
        validate_panel(bad)


def test_panel_internal_inconsistency_refuses():
    panel = derive_panel(_items(), 3000)
    rows = [PanelRow(
        kind=r.kind, title=r.title, source=r.source,
        reason=r.reason, tokens=r.tokens,
        share_percent=r.share_percent, item_id=r.item_id)
        for r in panel.rows]
    rows[0] = PanelRow(
        kind="file", title="crew_schedules.py",
        source="mythic_agent/core/crew_schedules.py",
        reason="The file under change in this session.",
        tokens=1520, share_percent=10.0,
        item_id="ctx-file-crew-schedules")
    with pytest.raises(ValueError):
        ContextPanel(
            rows=rows, budget_tokens=3000, total_tokens=2900,
            total_items=4, headroom_tokens=100, over_budget=False,
            account=list(panel.account))
    with pytest.raises(ValueError):
        ContextPanel(
            rows=panel.rows, budget_tokens=3000, total_tokens=2900,
            total_items=4, headroom_tokens=100, over_budget=True,
            account=list(panel.account))


def test_duplicate_refusals():
    entries = _items()
    with pytest.raises(ValueError):
        ContextBudgetPanel(
            title="Dup", budget_tokens=3000,
            items=[entries[0], entries[0]])
    meter = derive_meter(entries, 3000)
    first = ContextMeter(
        budget_tokens=3000, total_tokens=2900, total_items=4,
        headroom_tokens=100, over_budget=False, usage_percent=96.7,
        kind_totals=meter.kind_totals, account=list(meter.account),
        meter_id="meter-one")
    with pytest.raises(ValueError):
        ContextBudgetPanel(
            title="Dup meter", budget_tokens=3000, items=entries[:1],
            meters=[first, first])
    panel = derive_panel(entries, 3000)
    first_panel = ContextPanel(
        rows=panel.rows, budget_tokens=3000, total_tokens=2900,
        total_items=4, headroom_tokens=100, over_budget=False,
        account=list(panel.account), panel_id="panel-one")
    with pytest.raises(ValueError):
        ContextBudgetPanel(
            title="Dup panel", budget_tokens=3000, items=entries[:1],
            panels=[first_panel, first_panel])


def test_book_disagreement_refuses():
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / "context_budget.yaml")
        .read_text(encoding="utf-8"))
    raw["meters"][0]["total_tokens"] = 5661
    raw["meters"][0]["headroom_tokens"] = 2339
    raw["meters"][0]["kind_totals"][0]["tokens"] = 641
    with pytest.raises(ValidationError):
        validate_book(raw)
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / "context_budget.yaml")
        .read_text(encoding="utf-8"))
    raw["panels"][0]["rows"][0]["reason"] = "A different reason."
    with pytest.raises(ValidationError):
        validate_book(raw)
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / "context_budget.yaml")
        .read_text(encoding="utf-8"))
    raw["schema"] = "mythic.other/1"
    with pytest.raises(ValidationError):
        validate_book(raw)


def test_file_loader_round_trip_and_missing(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / "context_budget.yaml").read_text(
        encoding="utf-8")
    path = tmp_path / "context_budget.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_context_budget_file(path)
    assert book.title == "Context budget panel at the M-146 slice boundary"
    assert book.item_ids() == load_context_budget().item_ids()
    with pytest.raises(FileNotFoundError):
        load_context_budget_file(tmp_path / "nope.yaml")


def test_registry_auto_ids_and_duplicates():
    registry = ContextBudgetRegistry(budget_tokens=3000)
    first = registry.register_item({
        "kind": "file", "title": "One", "source": "a.py",
        "reason": "First.", "tokens": 100})
    second = registry.register_item({
        "kind": "note", "title": "Two", "source": "notes",
        "reason": "Second.", "tokens": 50})
    assert first.item_id == "item-1"
    assert second.item_id == "item-2"
    with pytest.raises(KeyError):
        registry.get_item("ctx-nope")
    registry2 = ContextBudgetRegistry()
    registry2.register_item(_item())
    with pytest.raises(ValueError):
        registry2.register_item(_item())
    with pytest.raises(ValueError):
        registry2.meter()
    registry3 = ContextBudgetRegistry(budget_tokens=3000)
    registry3.register_item(_item())
    assert registry3.meter().total_tokens == 1520
    assert registry3.panel_view().rows[0].item_id == (
        "ctx-file-crew-schedules")
    with pytest.raises(ValueError):
        registry3.set_budget(4000)
    assert registry3.set_budget(3000) == 3000


def test_registry_book_title_and_budget_clash():
    registry = ContextBudgetRegistry()
    registry.register_panel(load_context_budget())
    other = ContextBudgetPanel(
        title="Another panel", budget_tokens=8000,
        items=[ContextItem(
            item_id="ctx-x", kind="note", title="X",
            source="notes", reason="Another panel's item.",
            tokens=10)])
    with pytest.raises(ValueError):
        registry.register_panel(other)
    clash = ContextBudgetPanel(
        title="Context budget panel at the M-146 slice boundary",
        budget_tokens=9000,
        items=[ContextItem(
            item_id="ctx-y", kind="note", title="Y",
            source="notes", reason="A different budget's item.",
            tokens=10)])
    with pytest.raises(ValueError):
        registry.register_panel(clash)
    assert registry.panel().title == (
        "Context budget panel at the M-146 slice boundary")
    # The registry holds items, never meters or panels:
    # both are derived at call time.
    assert registry.panel().meters == ()
    assert registry.panel().panels == ()


def test_session_news_records():
    item = _item()
    record = item_record(item)
    assert record["type"] == "context_budget_item"
    assert record["news"] is True
    assert "holds 1520 tokens" in record["headline"]
    meter = meter_record(derive_meter(_items(), 3000))
    assert meter["type"] == "context_budget_meter"
    assert "2900 of 3000 tokens" in meter["headline"]
    panel = panel_record(derive_panel(_items(), 3000))
    assert panel["type"] == "context_budget_panel"
    assert panel["total_items"] == 4
    book = book_record(load_context_budget())
    assert book["type"] == "context_budget_book"
    assert book["item_count"] == 7
    assert book["total_tokens"] == 5660


def test_plain_words():
    words = plain_words(_item())
    assert "crew_schedules.py" in words
    assert "1520 tokens" in words
    book = load_context_budget()
    meter_words = meter_plain_words(book)
    assert "Context budget panel at the M-146 slice boundary" in meter_words
    assert "5660 of 8000" in meter_words
    panel_words = panel_plain_words(book)
    assert "What's in the context and why:" in panel_words
    assert "Repo map: crew package" in panel_words


def test_formatters_and_screen():
    book = load_context_budget()
    line = format_item(book.items[0])
    assert line.startswith("ctx-system-prompt: system")
    assert "640 tokens" in line
    only_files = format_items(book, kind="file")
    assert "ctx-file-crew-schedules" in only_files
    assert "ctx-system-prompt" not in only_files
    meter_text = format_meter(book)
    assert "Context meter: 5660 of 8000 tokens" in meter_text
    assert "tool_result: 860 tokens" in meter_text
    panel_text = format_panel(book)
    assert "What's in the context and why:" in panel_text
    assert "ctx-map-crew" in panel_text
    screen = format_context_budget_screen(book)
    assert "Context budget made visible (M-147)" in screen
    assert USAGE in screen
    assert "No context items are held." in format_items(
        ContextBudgetPanel(
            title="One kind", budget_tokens=100,
            items=[_item()]), kind="note")


def test_parser_grammar():
    assert parse_context_budget_args("") == ("show", None)
    assert parse_context_budget_args("show") == ("show", None)
    assert parse_context_budget_args("list") == ("show", None)
    assert parse_context_budget_args("item ctx-system-prompt") == (
        "item", "ctx-system-prompt")
    assert parse_context_budget_args("kind map-section") == (
        "kind", "map_section")
    assert parse_context_budget_args("meter") == ("meter", None)
    assert parse_context_budget_args("panel") == ("panel", None)
    for bad in ("dance", "item", "kind", "meter now",
                "kind banana", "item bad id!"):
        with pytest.raises(ValueError):
            parse_context_budget_args(bad)


def test_builders_from_field_words():
    record = build_item({
        "kind": "note", "title": "Weekend note",
        "source": "session notes", "reason": "A held note.",
        "tokens": 42})
    assert record.kind == "note"
    meter = build_meter(
        budget_tokens=3000, total_tokens=2900, total_items=4,
        headroom_tokens=100, over_budget=False, usage_percent=96.7,
        kind_totals=[
            {"kind": "file", "tokens": 2000, "items": 2},
            {"kind": "system", "tokens": 640, "items": 1},
            {"kind": "note", "tokens": 260, "items": 1}],
        account=["The context holds 2900 of 3000 tokens."])
    assert meter.total_tokens == 2900
    panel = build_panel(
        rows=[derive_panel([record], 100).rows[0]],
        budget_tokens=100, total_tokens=42, total_items=1,
        headroom_tokens=58, over_budget=False,
        account=["The panel accounts for 1 item(s)."])
    assert panel.total_items == 1
    book = build_budget_panel(
        title="A small panel", budget_tokens=3000, items=[record])
    assert isinstance(book, ContextBudgetPanel)
    assert book.items[0] is record


def test_measure_item_with_deterministic_estimator():
    estimator = TokenEstimator(prefer_tiktoken=False)
    assert estimator.backend == "heuristic"
    item = measure_item(
        "file", "Measured file", "a.py", "Measured for the panel.",
        "hello world hello world", item_id="ctx-measured",
        estimator=estimator)
    assert item.tokens == 5
    assert measure_item(
        "note", "Empty", "notes", "An empty note.", "",
        estimator=estimator).tokens == 0
    with pytest.raises(ValueError):
        measure_item("file", "T", "S", "R", 42, estimator=estimator)


def test_measure_panel_and_token_refusal():
    estimator = TokenEstimator(prefer_tiktoken=False)
    panel = measure_panel(
        "Measured panel", 100,
        [{"kind": "file", "title": "A", "source": "a.py",
          "reason": "First measured.", "text": "12345678"},
         {"kind": "note", "title": "B", "source": "notes",
          "reason": "Second measured.", "text": "1234"}],
        estimator=estimator)
    assert [e.tokens for e in panel.items] == [2, 1]
    assert derive_meter(panel).total_tokens == 3
    with pytest.raises(ValueError):
        measure_panel(
            "Bad panel", 100,
            [{"kind": "file", "title": "A", "source": "a.py",
              "reason": "Names its own count.", "text": "1234",
              "tokens": 9}],
            estimator=estimator)


def test_panel_from_compiled_with_real_blocks():
    from mythic_agent.context.compiler import (
        CompiledContext,
        ContextBlock,
    )
    compiled = CompiledContext(
        blocks=[
            ContextBlock(
                name="file:a.py", content="x" * 40, priority=5,
                provenance={"source": "explicit-files"}, tokens=10),
            ContextBlock(
                name="repo-map", content="map", priority=1,
                provenance={"source": "repo-map"}, tokens=20),
            ContextBlock(
                name="instructions", content="do", priority=0,
                provenance={"source": "instructions"}, tokens=5)],
        total_tokens=35, budget_tokens=4000)
    panel = panel_from_compiled(compiled)
    assert panel.budget_tokens == 4000
    assert panel.kinds() == ("file", "map_section", "instruction")
    assert panel.item_ids() == (
        "ctx-1-file-a-py", "ctx-2-repo-map", "ctx-3-instructions")
    assert [e.tokens for e in panel.items] == [10, 20, 5]
    assert panel.items[0].source == "explicit-files"
    assert "Mandatory context" in panel.items[2].reason
    assert derive_meter(panel).total_tokens == 35


def test_panel_from_compiled_duck_typed_and_counted():
    estimator = TokenEstimator(prefer_tiktoken=False)
    compiled = {"blocks": [
        {"name": "note-x", "content": "abcd efgh", "tokens": 0,
         "priority": 5, "provenance": {"source": "session-notes"}},
        {"name": "opening", "content": "sys", "tokens": 3,
         "priority": 0, "provenance": {"kind": "system"}}],
        "budget_tokens": 100}
    panel = panel_from_compiled(compiled, estimator=estimator)
    assert panel.kinds() == ("note", "system")
    assert panel.items[0].tokens == 2
    assert panel.items[1].source == "compiled-context"
    bare = panel_from_compiled(
        [{"name": "mystery", "content": "zz", "tokens": 1,
          "priority": 5, "provenance": {"source": "unknown-road"}}],
        budget_tokens=50, estimator=estimator)
    assert bare.items[0].kind == "note"
    with pytest.raises(ValueError):
        panel_from_compiled([{"name": "x", "content": "y"}])
