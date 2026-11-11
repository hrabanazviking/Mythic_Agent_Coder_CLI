"""M-217 Templates - pure-layer tests.

TIER: integration

The pure layer is the shapekeeper, held as data: one
record per template, held whole - the slice it
answers for, named by slice id, its title, the
steps it walked in walk order and the evidence
it carries, held by kind. The question walk is
explicit - named, shaped, checked, approved,
issued, with their legal steps held as data -
and a template's standing is derived at call
time: a template that opens anywhere but drafted, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet reached issued stands open,
named in its gaps. A template stands only for
an active slice: a template naming no held
slice, or one that is not active, refuses by
name. The template's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, shelf, trace, order and current
template are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, approved or
issued live. The shipped example book is held
in a data file, and a loader reads a book from
any file. No charter row names this slice: the
M-171 TUI charter binds Part VIII alone, and the
M-005 method charter names the whole of Part IX
as the part that executes it, both pinned live
below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.campaign_templates import (
    EXAMPLE_CHECK,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    CHECKS,
    CLAIM_KINDS,
    TRANSITIONS,
    KIND_STATES,
    CHECK_FIELDS,
    PLAIN_EXPLANATION,
    TEMPLATE_RESOURCE,
    TEMPLATE_RULE,
    TEMPLATE_SCHEMA,
    TEMPLATE_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    TemplateRecord,
    IndexEntry,
    KindRef,
    NoteRecord,
    TemplateBook,
    TemplateIndex,
    TemplatePanel,
    TemplateRegistry,
    TemplateVerdict,
    TemplateView,
    trace_for_template,
    shelf_record,
    book_record,
    build_trace,
    build_book,
    build_template,
    build_kind_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_template,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    template_for_check,
    template_gaps,
    template_order,
    template_record,
    template_green,
    templates_for_kind,
    first_note,
    format_book,
    format_template,
    format_index,
    format_note,
    format_check,
    format_panel,
    format_template_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    kind_record,
    load_template,
    legal_step,
    load_template_file,
    next_check,
    normalize_check,
    normalize_claim_kind,
    normalize_kind_state,
    normalize_stance,
    normalize_view_filter,
    note_for_template,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_template_args,
    green_templates,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_templates,
    validate_book,
    validate_template,
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
EXAMPLE_TITLE = "Campaign templates at the M-217 slice boundary"
EXAMPLE_CHECKS = ["issued", "issued", "issued"]
EXAMPLE_RUN_IDS = (
    "template-held-template", "template-remeasured-template",
    "template-own-template", "template-bare-template",
    "template-leaping-template")
EXAMPLE_TRACE = "drafted > shaped > checked > approved > issued"


def _ref(**overrides):
    fields = {
        "kind_id": "slice-test",
        "seq": 1,
        "title": "A test slice",
        "state": "live",
        "detail": "A test slice reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "template-test",
    }
    fields.update(overrides)
    return build_kind_ref(fields)


def _template(**overrides):
    fields = {
        "template_id": "template-test",
        "seq": 1,
        "kind_id": "slice-test",
        "title": "A test template",
        "checks": ["drafted", "shaped", "checked", "approved", "issued"],
        "claims": [],
        "detail": "A test template held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "template-test",
    }
    fields.update(overrides)
    return build_template(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "template-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "template_id": "template-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "template-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "template_id": "template-test",
        "trace": "drafted > shaped > checked > approved > issued",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "template-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(slices=None, templates=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": TEMPLATE_SCHEMA,
        "slice": "M-217",
        "campaign_templates": {"title": "A test template book"},
        "kinds": [item.to_record() for item in (
            slices if slices is not None else [_ref()])],
        "template_records": [item.to_record() for item in (
            templates if templates is not None else [_template()])],
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
    return _book(templates=[
        _template(),
        _template(template_id="template-hidden", seq=2,
               title="A hidden template", checks=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_template()
    assert book.title == EXAMPLE_TITLE
    assert book.template_ids() == EXAMPLE_RUN_IDS
    assert book.kind_ids() == (
        "kind-m216-hall", "slice-m217-template",
        "kind-m217-templates")
    assert [v.view_id for v in book.views] == [
        "view-templates", "view-issued"]
    assert [m.template_id for m in book.notes] == [
        "template-held-template", "template-bare-template"]
    assert [a.template_id for a in book.traces] == ["template-held-template"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m216-boundary"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.template_ids())
    derived = derive_panel(book, "view-templates")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-templates").verdict == "held"
    assert derive_verdict(book, "view-templates").green_shown == 3
    assert derive_verdict(book, "view-issued").verdict == "issued"
    assert derive_verdict(book, "view-issued").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / TEMPLATE_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == TEMPLATE_SCHEMA
    assert raw["slice"] == "M-217"
    assert "verdict" not in raw
    assert "template_index" not in raw
    assert "shelf" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-217")]
    assert slice_.title == "Campaign templates"
    assert slice_.part == 9
    assert "house shapes (feature build, bug hunt, migration, hardening, docs)" in slice_.summary
    assert "as starting campaign files" in slice_.summary
    assert TEMPLATE_SLICE == "M-217"

def test_charter_rows_do_not_name_m217():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-217" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert CHECK_FIELDS == ("checks", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("issued", "held", "blocked")
    assert KIND_STATES == ("live", "dormant")
    assert CHECKS == ("drafted", "shaped", "checked", "approved", "issued")
    assert HELD_EVIDENCE == ("kind_ref", "shelf_ref", "keeper_record", "issue_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["approved"] == ("drafted", "issued")
    assert TRANSITIONS["issued"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_CHECK == "issued"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_kind_state("LIVE") == "live"
    assert normalize_check("CHECKED") == "checked"
    assert normalize_claim_kind("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_kind_state("blessed")
    with pytest.raises(ValueError):
        normalize_check("polish")
    with pytest.raises(ValueError):
        normalize_claim_kind("weather")
    assert legal_step("checked", "approved") is True
    assert legal_step("shaped", "issued") is False
    assert legal_step("issued", "drafted") is False
    assert next_check("drafted") == "shaped"
    assert next_check("checked") == "approved"
    assert next_check("approved", failed=True) == "drafted"
    assert next_check("approved") == "issued"
    assert next_check("issued") is None
    assert "held as data alone" in TEMPLATE_RULE
    assert "template sequence" in TEMPLATE_RULE
    assert "M-217" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /shapes")

def test_shipped_book_judged_honestly_as_data():
    book = load_template()
    opening = book.template_for("template-held-template")
    assert template_green(opening, book) is True
    assert template_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Template: The held template",
        "Kind: kind-m216-hall",
        "Check: issued",
        "Claims: kind_ref")
    asking = book.template_for("template-bare-template")
    assert template_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert template_green(asking, book) is False
    skipping = book.template_for("template-leaping-template")
    assert template_gaps(skipping, book) == (
        "steps from shaped to issued, which the template sequence "
        "does not allow",)
    assert [g.template_id for g in green_templates(book)] == [
        "template-held-template", "template-remeasured-template", "template-own-template"]
    index = derive_index(book)
    assert [e.check for e in index.entries] == EXAMPLE_CHECKS
    assert index.gaps == ("template-bare-template", "template-leaping-template")
    assert template_for_check(book, EXAMPLE_CHECK).template_id == (
        "template-held-template")
    assert template_for_check(book, "triple resume") is None
    assert transition_breaks(book) == (
        "template-leaping-template: shaped > issued",)
    assert [g.template_id for g in template_order(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "template-held-template") == EXAMPLE_TRACE
    assert trace_current(book, "template-held-template") is True
    assert trace_current(book, "template-remeasured-template") is False
    assert trace_for_template(
        book, "template-held-template").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_template(
        book, "template-held-template", "note").note_id == (
            "note-note-first")
    assert note_for_template(book, "template-nope") is None
    assert current_template(book).template_id == "template-bare-template"
    shelf = shelf_record(book)
    assert shelf["standings"] == [
        {"standing": "complete", "template_records": 3},
        {"standing": "open", "template_records": 2}]
    assert shelf["total"] == 5
    assert shelf["current_template"] == "template-bare-template"
    assert shelf["traces"] == [
        {"template_id": "template-held-template", "trace": "current"},
        {"template_id": "template-remeasured-template", "trace": "unheld"},
        {"template_id": "template-own-template", "trace": "unheld"},
        {"template_id": "template-bare-template", "trace": "unheld"},
        {"template_id": "template-leaping-template", "trace": "unheld"}]
    assert shelf["breaks"] == ["template-leaping-template: shaped > issued"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 230
    assert citizen["next_slice"] == "M-231"
    assert citizen["m217_title"] == "Campaign templates"
    assert citizen["m217_part"] == 9
    assert citizen["m217_status"] == "done"

def test_template_record_round_trips():
    template = _template()
    assert validate_template(template) is template
    rebuilt = build_template(template.to_record())
    assert rebuilt == template
    assert rebuilt.item_id == "template-test"
    assert rebuilt.check == "issued"
    record = template_record(template)
    assert record["type"] == "template_template"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert kind_record(ref)["type"] == "template_slice"
    assert kind_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _template(checks=[])
    assert template_gaps(silent) == (
        "has passed through no step: the template has not started",)
    assert template_green(silent) is False
    walking = _template(checks=["drafted", "shaped"])
    assert template_gaps(walking) == (
        "has not reached issued: the template stands at shaped",)
    assert walking.check == "shaped"
    sideways = _template(checks=["shaped", "checked", "approved", "issued"])
    assert template_gaps(sideways) == (
        "opens at shaped, not at drafted: the template opens "
        "with the reflection",)
    repaired = _template(checks=["drafted", "shaped", "checked", "approved", "drafted", "shaped", "checked", "approved", "issued"])
    assert template_gaps(repaired) == ()
    assert template_green(repaired) is True
    with pytest.raises(ValueError):
        _template(checks=[42])
    with pytest.raises(ValueError):
        _template(checks="inspect as a bare string")
    with pytest.raises(ValueError):
        _template(checks=["drafted", "polish"])
    with pytest.raises(ValueError):
        _template(claims=["weather"])
    with pytest.raises(ValueError):
        _template(claims="kind_ref")
    none_template = _template(checks=None, claims=None)
    assert none_template.checks == ()
    assert none_template.claims == ()

def test_template_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "entries", "coverage", "current_template",
                "shelf", "order"):
        fields = _template().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_template(fields)
    fields = _template().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_template(fields)


def test_template_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _template().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_template(fields)


def test_template_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _template(title="")
    with pytest.raises(ValueError):
        _template(kind_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "drafted > shaped > checked > approved > issued"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_templates_own_fields():
    template = _template(claims=["kind_ref"])
    assert plain_lines(template) == (
        "Template: A test template",
        "Kind: slice-test",
        "Check: issued",
        "Claims: kind_ref")
    segment = segment_of(template)
    assert segment.startswith("template-test: A test template")
    assert "check: 'issued'" in segment
    assert "gaps: none" in segment
    assert plain_words(template).startswith(
        "A test template - from slice-test")

def test_red_templates_stand_named_in_their_gaps():
    asking = _template(claims=["feeling", "kind_ref", "summary"])
    assert template_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert template_green(asking) is False
    skipping = _template(checks=["drafted", "shaped", "issued"])
    assert template_gaps(skipping) == (
        "steps from shaped to issued, which the template sequence "
        "does not allow",)
    book = _book(templates=[
        _template(),
        _template(template_id="template-skipping", seq=2,
             checks=["drafted", "shaped", "issued"]),
    ])
    assert transition_breaks(book) == (
        "template-skipping: shaped > issued",)
    assert current_template(book).template_id == "template-skipping"
    assert [g.template_id for g in template_order(book)] == [
        "template-test", "template-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "template_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "template_note"
    assert record["template_id"] == "template-test"
    assert view_plain_words(view) == "View view-test: shows all templates."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_templates_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.check for e in index.entries] == ["issued"]
    assert index.entries[0] == IndexEntry(
        check="issued",
        template_id="template-test", title="A test template")
    assert index.gaps == ("template-hidden",)
    record = index_record(book)
    assert record["type"] == "template_index"
    assert record["gaps"] == ["template-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "template_book"

def test_check_target_reaches_its_template_and_an_unheld_target_reaches_nothing():
    book = load_template()
    assert template_for_check(book, "issued").template_id == (
        "template-held-template")
    assert template_for_check(book, "") is None
    assert template_for_check(book, None) is None
    assert template_for_check(book, "not held at all") is None
    text = format_check(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_template()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Template note note template-held-template" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").template_id == "template-test"
    assert note_for_template(book, "template-test").note_id == "note-test"
    assert note_for_template(book, "template-test", "praise") is None
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
    row = build_row(None, _template(), book)
    assert row.standing == "complete"
    assert validate_row(row, _template(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_templates():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "template_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "issued"
    empty_book = _book(templates=[_template(checks=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(TemplateVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_readings():
    book = load_template()
    assert [g.template_id for g in shown_templates(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.template_id for g in shown_templates(book, "view-issued")] == [
        "template-held-template", "template-remeasured-template", "template-own-template"]
    assert [g.template_id for g in templates_for_kind(
        book, "slice-m217-template")] == [
            "template-own-template", "template-bare-template",
            "template-leaping-template"]
    assert templates_for_kind(book, "slice-nope") == ()
    assert current_template(_mixed_book()).template_id == "template-hidden"
    assert current_template(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "template-test") == (
        "drafted > shaped > checked > approved > issued")
    assert trace_current(stale, "template-test") is False
    assert shelf_record(stale)["traces"] == [
        {"template_id": "template-test", "trace": "stale"}]

def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(templates=[_template(), _template(seq=2)])
    with pytest.raises(ValueError):
        _book(templates=[_template(), _template(template_id="template-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(templates=[_template(kind_id="slice-nope")])
    with pytest.raises(ValueError):
        _book(slices=[_ref(), _ref(
            kind_id="slice-cold", seq=2, state="dormant")],
            templates=[_template(kind_id="slice-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(kind_id="slice-nope")])
    fields = {
        "schema": TEMPLATE_SCHEMA, "slice": "M-217",
        "campaign_templates": {"title": "A checked book"},
        "slices": [_ref().to_record()],
        "template_records": [_template().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "issued"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_template"] = "template-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_template")
    fields["trace"] = "template-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / TEMPLATE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "campaign_templates.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_template_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.template_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = TemplateRegistry()
    assert registry.title() is None
    registry.register_kind_ref(_ref())
    registry.register_template(_template())
    registry.register_view(_view())
    assert [g.template_id for g in registry.list_templates()] == ["template-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_template("template-test").title == "A test template"
    assert registry.get_slice("slice-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("template-test").template_id == "template-test"
    with pytest.raises(ValueError):
        registry.register_template(_template(seq=9))
    with pytest.raises(ValueError):
        registry.register_template(_template(template_id="template-two"))
    with pytest.raises(KeyError):
        registry.get_template("template-nope")
    assert registry.book().title == "An unheld template book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = TemplateRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test template book"
    assert registry.title() == "A test template book"
    assert len(registry.list_templates()) == 2
    other = TemplateRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    template = _template()
    assert "A test template" in plain_words(template)
    assert panel_plain_words(_mixed_book()).startswith(
        "The template book holds 2 templates")
    assert verdict_plain_words(_mixed_book()) == (
        "The templates stand held: 1 of 2 shown templates stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green templates; red, "
        "named in its gaps: template-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_template(template)
    assert "Template: A test template" in text
    assert "stands complete" in text
    text = format_template(_template(checks=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Template Gate (M-217) - A test template book" in book_text
    assert "template-hidden" in format_book(_mixed_book(), "slice-test")
    assert "Template panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "issued - A test template (template-test)" in index_text
    assert "template-hidden" in index_text
    screen = format_template_screen()
    assert "The Template Gate (M-217)" in screen
    assert "template-bare-template" in screen

def test_parse_args_shelf_and_loader_targets():
    assert parse_template_args("") == ("show", None)
    assert parse_template_args(None) == ("show", None)
    assert parse_template_args("show") == ("show", None)
    assert parse_template_args("template template-test") == (
        "template", "template-test")
    assert parse_template_args("check issued") == (
        "check", "issued")
    assert parse_template_args("kind slice-test") == (
        "kind", "slice-test")
    assert parse_template_args("view view-test") == ("view", "view-test")
    assert parse_template_args("note note-test") == ("note", "note-test")
    assert parse_template_args("index") == ("index", None)
    assert parse_template_args("panel") == ("panel", None)
    assert parse_template_args("verdict") == ("verdict", None)
    for bad in ("dance", "template", "check", "slice", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_template_args(bad)
    shelf = shelf_record()
    assert shelf["type"] == "template_shelf"
    assert shelf["total"] == 5
    assert shelf["current_template"] == "template-bare-template"
    book = load_template({
        "schema": TEMPLATE_SCHEMA, "slice": "M-217",
        "campaign_templates": {"title": "A checked book"},
        "slices": [_ref().to_record()],
        "template_records": [_template().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, TemplateBook)
    assert book.title == "A checked book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_template({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_template({"slice": "M-999"})
    built = build_template(
        template_id="template-kw", seq=3, kind_id="slice-test",
        title="Kw Template", checks=["drafted", "shaped", "checked", "approved", "issued"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="template-test")
    assert built.template_id == "template-kw"
    assert template_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-217 agent layer: the agent holds a template
# book for the session, templates and views are
# published as session news through the
# checkpoint target (journal first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held templates, the shelf is derived from
# the held templates' completeness, the roadmap standing
# is read from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no slice. This layer templates
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_TEMPLATE_EVENT_TYPES = (
    "template_template", "template_slice", "template_view",
    "template_panel", "template_verdict")


def _template_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_shape_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / TEMPLATE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "campaign_templates.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestTemplateAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.shape_status()
        assert status["template_records"] == []
        assert status["slices"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["shape_book"]["title"] == EXAMPLE_TITLE
        assert len(status["shape_book"]["slices"]) == 3
        assert len(status["shape_book"]["template_records"]) == 5
        assert len(status["shape_book"]["views"]) == 2
        assert len(status["shape_book"]["notes"]) == 2
        assert len(status["shape_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m216-boundary"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["check"] for e in status["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert status["index"]["gaps"] == [
            "template-bare-template", "template-leaping-template"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["shelf"]["total"] == 5
        assert status["shelf"]["current_template"] == "template-bare-template"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 230
        assert status["roadmap"]["next_slice"] == "M-231"
        assert status["roadmap"]["m217_title"] == "Campaign templates"
        assert "held as data alone" in status["rule"]
        assert "template-bare-template" in status["plain_words"]
        assert "The Template Gate (M-217)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._shape_registry()
        assert agent._shape_registry() is first
        assert agent._shape_store is first
        for name in ("shape_book", "shape_status", "shape_panel",
                     "shape_verdict", "shape_index", "report_shape"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_shape_registry", "shape_book", "shape_status",
            "get_shape_template", "get_shape_view", "get_shape_note",
            "shape_templates_for_kind", "shape_templates_green",
            "shape_panel", "shape_verdict", "shape_index",
            "register_shape_template", "register_shape_view",
            "view_shape", "register_shape_book",
            "record_shape_book", "report_shape",
            "_publish_shape_record", "_shape_screen",
            "_shape_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.shape_status()
        assert agent.get_shape_template(
            "template-held-template").title == "The held template"
        assert agent.get_shape_view(
            "view-templates").view_filter == "all"
        assert agent.get_shape_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.template_id for d in agent.shape_templates_for_kind(
            "slice-m217-template")] == [
            "template-own-template", "template-bare-template",
            "template-leaping-template"]
        assert [d.template_id for d in agent.shape_templates_green()] == [
            "template-held-template", "template-remeasured-template", "template-own-template"]
        agent.shape_panel()
        agent.shape_verdict()
        agent.shape_index()
        agent.report_shape()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _TEMPLATE_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_shape_template("template-nope")
        with pytest.raises(KeyError):
            agent.get_shape_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_shape_note("note-nope")
        with pytest.raises(ValueError):
            agent.shape_templates_for_kind("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_shape_template(_template())
        status = agent.shape_status()
        assert [d["template_id"] for d in status["template_records"]] == ["template-test"]
        assert status["book"]["title"] == "An unheld template book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["check"] for e in status["index"]["entries"]] == [
            "issued"]
        assert status["first_note"] is None
        assert "template-test" in status["screen"]
    def test_held_template_never_falls_back_to_the_example(
            self, agent):
        agent.register_shape_template(_template())
        with pytest.raises(KeyError):
            agent.get_shape_template("template-held-template")
        with pytest.raises(KeyError):
            agent.get_shape_view("view-templates")
        with pytest.raises(KeyError):
            agent.get_shape_note("note-note-first")
        template = agent.get_shape_template("template-test")
        assert template.title == "A test template"
        assert agent.shape_book().title == (
            "An unheld template book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_shape_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.template_id == "template-held-template"
        status = agent.shape_status()
        assert status["index"]["gaps"] == [
            "template-bare-template", "template-leaping-template"]
        assert status["first_note"]["template_id"] == (
            "template-held-template")
        assert status["first_note"]["stance"] == "note"

class TestTemplateAgentHolding:
    def test_register_template_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_shape_template(_template())
        assert result["template"]["template_id"] == "template-test"
        assert result["record_news"]["type"] == "template_template"
        assert "template-test" in result["screen"]
        events = _template_events(store, session_id, "template_template")
        assert len(events) == 1
        agent.close()

    def test_duplicate_template_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_shape_template(_template())
        with pytest.raises(ValueError):
            agent.register_shape_template(_template(seq=9))
        with pytest.raises(ValueError):
            agent.register_shape_template(_template(template_id="template-two"))
        events = _template_events(store, session_id, "template_template")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_shape_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_template_events(
            store, session_id, "template_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_shape_template(_template())
        result = agent.view_shape("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "template_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "issued"
        assert len(_template_events(
            store, session_id, "template_view")) == 1
        assert len(_template_events(
            store, session_id, "template_panel")) == 1
        assert len(_template_events(
            store, session_id, "template_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_shape_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "template_slice", "template_template", "template_view"]
        assert len(_template_events(
            store, session_id, "template_template")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_shape_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "template_panel"
        assert result["index_record"]["gaps"] == [
            "template-bare-template", "template-leaping-template"]
        with pytest.raises(ValueError):
            agent.record_shape_book()
        assert len(_template_events(
            store, session_id, "template_slice")) == 3
        assert len(_template_events(
            store, session_id, "template_template")) == 5
        assert len(_template_events(
            store, session_id, "template_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_shape_book_file(tmp_path)
        book = load_template_file(path)
        result = agent.record_shape_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_kindrt_renders_example_then_held_book_only(self, agent):
        report = agent.report_shape()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "held"
        assert report["index"]["gaps"] == [
            "template-bare-template", "template-leaping-template"]
        assert "template-held-template" in report["book_text"]
        assert "issued - The held template (template-held-template)" in report["index_text"]
        agent.register_shape_template(_template())
        report = agent.report_shape()
        assert report["book"]["title"] == "An unheld template book"
        assert report["panel"] is None
        assert report["verdict"] is None

class TestTemplateTerminalHeading:
    def test_show_template_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/shapes")
        assert "The Template Gate (M-217)" in text
        _, _, text = _slash(agent, "/shapes template template-held-template")
        assert "Template: The held template" in text
        _, _, text = _slash(
            agent, "/shapes check issued")
        assert "Template: The held template" in text
        _, _, text = _slash(agent, "/shapes check triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/shapes kind slice-m217-template")
        assert "template-bare-template" in text
        assert "template-held-template" not in text
        _, _, text = _slash(agent, "/shapes view view-templates")
        assert "filter all" in text
        _, _, text = _slash(agent, "/shapes note note-note-first")
        assert "Template note note template-held-template" in text
        _, _, text = _slash(agent, "/shapes index")
        assert "Template index" in text
        assert "template-bare-template" in text
        _, _, text = _slash(agent, "/shapes panel")
        assert "Template panel under view view-templates" in text
        _, _, text = _slash(agent, "/shapes verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/shapes [show|template <template-id>"
                "|check <check>|kind <kind-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/shapes dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/shapes template template-nope")
        assert "no template named" in text
@pytest.fixture()
def template_handler(agent, monkeypatch):
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


def _template_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestTemplateCommand:
    def test_show_is_default(self, template_handler, agent):
        template_handler._handle_shape("")
        assert "The Template Gate (M-217)" in (
            _template_published_text(template_handler))

    def test_template_check_slice_view_note_index_panel_verdict(
            self, template_handler, agent):
        template_handler._handle_shape("template template-held-template")
        assert "Template: The held template" in _template_published_text(
            template_handler)
        template_handler._handle_shape(
            "check issued")
        assert "Template: The held template" in _template_published_text(
            template_handler)
        template_handler._handle_shape("kind slice-m217-template")
        assert "template-bare-template" in _template_published_text(
            template_handler)
        template_handler._handle_shape("view view-templates")
        assert "filter all" in _template_published_text(template_handler)
        template_handler._handle_shape("note note-note-first")
        assert "Template note note template-held-template" in (
            _template_published_text(template_handler))
        template_handler._handle_shape("index")
        assert "Template index" in _template_published_text(template_handler)
        template_handler._handle_shape("panel")
        assert "Template panel under view" in _template_published_text(
            template_handler)
        template_handler._handle_shape("verdict")
        assert "held" in _template_published_text(template_handler)
    def test_bad_grammar_is_published(
            self, template_handler, agent):
        template_handler._handle_shape("dance party")
        assert USAGE in _template_published_text(template_handler)
        template_handler._handle_shape("template template-nope")
        assert "no template named" in _template_published_text(
            template_handler)


class TestChatScreenRoutingTemplate:
    def test_onshelf_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/shapes panel", _FakeLog())
        assert calls == [("/shapes", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/shapes[/green] - show the Template gate (M-217)" in (
            text)
        assert ('"/shapes": "Usage: /shapes | '
                '/shapes template <template-id>') in text

class TestTemplateDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.shape_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-templates"
        verdict = agent.shape_verdict()
        assert verdict.verdict == "held"
        found = agent.shape_verdict("view-issued")
        assert found.verdict == "issued"
        assert found.green_shown == 3
        agent.register_shape_template(_template())
        with pytest.raises(ValueError):
            agent.shape_panel()
        with pytest.raises(ValueError):
            agent.shape_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_shape_template(_template(checks=[]))
        result = agent.view_shape("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.shape_index()
        assert [e["check"] for e in result["index"]["entries"]] == (
            EXAMPLE_CHECKS)
        assert result["index"]["gaps"] == [
            "template-bare-template", "template-leaping-template"]
        assert "issued - The held template (template-held-template)" in (
            result["index_text"])
        template = agent.get_shape_template("template-leaping-template")
        assert template_gaps(template, agent.shape_book()) == (
            "steps from shaped to issued, which the template sequence "
            "does not allow",)
        assert template_green(template, agent.shape_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _TEMPLATE_EVENT_TYPES] == []
        agent.close()
