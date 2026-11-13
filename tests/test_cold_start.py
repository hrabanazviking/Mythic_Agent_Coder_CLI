"""M-169 Cold-Start Kindness - pure-layer tests.

TIER: integration

The pure layer is the cold-start record, held as
data: one opening over one project - named by
the project id and the map id alone, the map's
own facts never crossing - carrying its evidence
whole (the map's age in days, its entry count,
the project's file count, how many of those
files the map covers, and the map counted by
area - the shipped map's own sections - each
area naming how many of its entries stand
stale), composed by import from the shipped
holdings it stands over (the project memory map
M-150 and session memory M-153), each judged by
its own layer's validation, ids and counts only
across the seams. The rebuild plan is derived,
never chosen: no map derives a rebuild from
scratch, old, stale or short evidence derives a
background rebuild while the coder works from
the stale-but-usable map, and fresh, whole
evidence derives no rebuild at all - and the
stages stand in derived order, the stalest area
first. A readiness panel is derived from the
whole book (what is usable now beside what is
still rebuilding), a cold-start verdict is
derived for the whole book, progress walks the
derived plan stage by stage in order, the
shipped example book is held in a data file, and
a loader reads a book from any file. Nothing
here starts a thread, rebuilds a live map, opens
a live project, sends, posts, schedules, calls a
model or persists anything: a stage marked done
is marked on the held book alone.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.project_memory_map import (
    MAP_SECTIONS, load_project_memory_map)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.session_memory import load_session_memory
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.cold_start import (
    AREAS,
    COLD_START_RESOURCE,
    COLD_START_SCHEMA,
    COLD_START_SLICE,
    MODES,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_WORDS,
    ColdStartArea,
    ColdStartBook,
    ColdStartPanel,
    ColdStartProgress,
    ColdStartRecord,
    ColdStartRegistry,
    ColdStartVerdict,
    ModeCount,
    book_record,
    build_area,
    build_book,
    build_panel,
    build_progress,
    build_record,
    build_row,
    build_verdict,
    derive_panel,
    derive_progress,
    derive_verdict,
    format_cold_start_screen,
    format_panel,
    format_progress,
    format_record,
    format_records,
    format_verdict,
    inspect_opening_source,
    load_cold_start,
    load_cold_start_file,
    mode_of,
    normalize_mode,
    panel_plain_words,
    panel_record,
    parse_cold_start_args,
    plain_words,
    progress_plain_words,
    progress_record,
    record_for,
    record_from_map_book,
    record_from_map_entry,
    record_from_session_situation,
    record_record,
    record_refs,
    stage_plan_of,
    total_records,
    usable_entries_of,
    validate_area,
    validate_book,
    validate_panel,
    validate_progress,
    validate_record,
    validate_row,
    validate_verdict,
    verdict_plain_words,
    verdict_record,
)

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Cold-Start Kindness at the M-168 slice boundary"

BY = "Volmarr"
ON = "2026-11-09"


def _areas(stale_arch=3, stale_gotcha=2):
    return [
        {"section": "architecture", "entries": 10,
         "stale_entries": stale_arch},
        {"section": "decision", "entries": 5, "stale_entries": 0},
        {"section": "gotcha", "entries": 4,
         "stale_entries": stale_gotcha},
        {"section": "location", "entries": 6, "stale_entries": 0},
    ]


def _record(**overrides):
    fields = {
        "record_id": "record-test",
        "title": "the test project opens cold",
        "project_ref": "proj-test",
        "map_ref": "map-proj-test",
        "map_age_days": 74,
        "map_entries": 25,
        "project_files": 900,
        "covered_files": 800,
        "areas": _areas(),
        "opened_on": ON,
        "opened_by": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_record(fields)


def _fresh_record(**overrides):
    fields = {
        "record_id": "record-fresh", "project_ref": "proj-fresh",
        "map_ref": "map-proj-fresh", "map_age_days": 1,
        "covered_files": 900,
        "areas": _areas(0, 0),
    }
    fields.update(overrides)
    return _record(**fields)


def _scratch_record(**overrides):
    fields = {
        "record_id": "record-scratch", "project_ref": "proj-scratch",
        "map_ref": "map-proj-scratch", "map_age_days": 300,
        "map_entries": 0, "covered_files": 0, "areas": [],
    }
    fields.update(overrides)
    return _record(**fields)


def _stored_record(record):
    stored = record.to_record()
    for key in ("type", "slice", "mode", "stage_plan"):
        stored.pop(key)
    return stored


def _book(records=None, **overrides):
    fields = {
        "title": "A test cold-start book",
        "records": [_stored_record(item) for item in (
            records if records is not None else [_record()])],
    }
    fields.update(overrides)
    return build_book(fields)


# ---------------------------------------------------------------------
# The shipped example book and the roadmap.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_cold_start()
    assert book.title == EXAMPLE_TITLE
    assert book.record_ids() == (
        "opening-mythic-hammer", "opening-old-sagas",
        "opening-fresh-notes")
    first = book.records[0]
    assert first.title == "the mythic hammer campaign home opens cold"
    assert first.project_ref == "mythic-hammer"
    assert mode_of(first) == "background-rebuild"
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m168-boundary"
    assert panel.as_of == "2026-11-09"
    assert tuple(r.record_id for r in panel.rows) == (
        "opening-old-sagas", "opening-mythic-hammer",
        "opening-fresh-notes")
    assert panel == derive_panel(book) or (
        panel.rows == derive_panel(book).rows
        and panel.account == derive_panel(book).account)
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / COLD_START_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == COLD_START_SCHEMA
    assert raw["slice"] == "M-169"


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-169")]
    assert slice_.title == "Cold-start kindness"
    assert "rebuilds its map in the background" in slice_.summary
    assert "already useful" in slice_.summary
    assert COLD_START_SLICE == "M-169"


def test_closed_vocabularies():
    assert MODES == (
        "rebuild-from-scratch", "background-rebuild", "serve-fresh")
    assert VERDICT_WORDS == ("cold", "warming", "kind")
    assert AREAS == MAP_SECTIONS
    assert normalize_mode("scratch") == "rebuild-from-scratch"
    assert normalize_mode("background") == "background-rebuild"
    assert normalize_mode("fresh") == "serve-fresh"
    with pytest.raises(ValueError):
        normalize_mode("whenever")
    assert "background" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /coldstart")


def test_record_record_round_trips():
    record = _record()
    assert build_record(_stored_record(record)) == record
    assert record.to_record()["mode"] == "background-rebuild"
    assert record.to_record()["stage_plan"] == list(stage_plan_of(record))


def test_record_provenance_is_whole_and_required():
    record = _record()
    assert record.opened_by == BY
    assert record.origin_session == "session-test"
    for missing in ("title", "project_ref", "map_ref", "map_age_days",
                    "map_entries", "project_files", "covered_files"):
        fields = _stored_record(record)
        fields.pop(missing)
        with pytest.raises(ValueError):
            build_record(fields)


def test_record_refuses_unknown_keys_and_split_spellings():
    fields = _stored_record(_record())
    fields["mode"] = "background-rebuild"
    with pytest.raises(ValueError):
        build_record(fields)
    fields = _stored_record(_record())
    fields["stage_plan"] = ["serve-stale-map"]
    with pytest.raises(ValueError):
        build_record(fields)
    fields = _stored_record(_record())
    fields["age"] = 99
    with pytest.raises(ValueError):
        build_record(fields)
    fields = _stored_record(_record())
    fields["surprise"] = "x"
    with pytest.raises(ValueError):
        build_record(fields)


def test_record_alias_spellings_read_onto_the_fields():
    record = build_record({
        "name": "an opening named by alias", "project": "proj-alias",
        "map": "map-alias", "age": 5, "entries": 0, "files": 10,
        "covered": 0, "areas": [], "day": ON, "by": BY,
        "source": "alias source", "session": "session-alias",
        "id": "record-alias"})
    assert record.project_ref == "proj-alias"
    assert record.map_entries == 0
    assert mode_of(record) == "rebuild-from-scratch"


def test_plan_is_always_derived():
    assert mode_of(_fresh_record()) == "serve-fresh"
    assert mode_of(_record()) == "background-rebuild"
    assert mode_of(_record(areas=_areas(0, 0))) == "background-rebuild"
    assert mode_of(_record(
        areas=_areas(0, 0), covered_files=900)) == "background-rebuild"
    assert mode_of(_record(
        areas=_areas(0, 0), covered_files=900,
        map_age_days=3)) == "serve-fresh"
    assert mode_of(_scratch_record()) == "rebuild-from-scratch"
    assert stage_plan_of(_fresh_record()) == ("serve-fresh-map",)
    assert stage_plan_of(_scratch_record()) == (
        "rebuild-whole-map", "verify-map")


def test_stage_order_is_stalest_first():
    plan = stage_plan_of(_record())
    assert plan == (
        "serve-stale-map", "rebuild-area:architecture",
        "rebuild-area:gotcha", "verify-map")
    tied = _record(areas=[
        {"section": "gotcha", "entries": 4, "stale_entries": 3},
        {"section": "architecture", "entries": 10, "stale_entries": 3},
        {"section": "decision", "entries": 5, "stale_entries": 0},
        {"section": "location", "entries": 6, "stale_entries": 0}])
    assert stage_plan_of(tied)[1] == "rebuild-area:architecture"
    assert usable_entries_of(_record()) == 20
    assert usable_entries_of(_scratch_record()) == 0


def test_area_evidence_laws():
    with pytest.raises(ValueError):
        _record(areas=_areas()[:-1])
    with pytest.raises(ValueError):
        build_area({"section": "architecture", "entries": 2,
                    "stale_entries": 3})
    with pytest.raises(ValueError):
        _record(covered_files=901)
    with pytest.raises(ValueError):
        _record(areas=[
            {"section": "architecture", "entries": 25,
             "stale_entries": 0},
            {"section": "architecture", "entries": 0,
             "stale_entries": 0}])
    area = validate_area({"area": "gotcha", "count": 4, "stale": 1})
    assert area == ColdStartArea(section="gotcha", entries=4,
                                 stale_entries=1)
    assert area.usable_entries == 3


def test_record_from_map_book_carries_counts_only():
    book = load_project_memory_map()
    record = record_from_map_book(
        book, project_ref="proj-map", map_ref="map-proj-map",
        map_age_days=90, project_files=500, covered_files=400,
        stale={"location": 1}, opened_on=ON, opened_by=BY,
        origin_session="session-test", record_id="record-from-map")
    assert record.map_entries == len(book.entries) == 9
    assert record.area_for("location").entries == 3
    assert record.area_for("location").stale_entries == 1
    assert mode_of(record) == "background-rebuild"
    assert "detail" not in str(record.to_record()["areas"])


def test_record_from_map_entry_carries_id_only():
    entry = load_project_memory_map().entries[0]
    record = record_from_map_entry(
        entry, project_ref="proj-entry", map_ref="map-one-entry",
        map_age_days=40, project_files=50, covered_files=10,
        stale=True, opened_on=ON, opened_by=BY,
        origin_session="session-test", record_id="record-from-entry")
    assert record.map_entries == 1
    assert record.areas[0].section == entry.section
    assert record.total_stale == 1
    assert entry.title not in record.title
    assert entry.detail not in str(record.to_record())


def test_record_from_session_situation_carries_counts_only():
    situation = load_session_memory().situations[0]
    record = record_from_session_situation(
        situation, map_ref="map-carried", map_age_days=60,
        project_files=300, covered_files=200, stale={"gotcha": 1},
        opened_on=ON, opened_by=BY, record_id="record-from-situation")
    assert record.project_ref == situation.session_ref
    assert record.map_entries == len(situation.memory) == 3
    assert record.origin_session == situation.session_ref
    assert mode_of(record) == "background-rebuild"


def test_composition_refuses_stale_for_an_absent_area():
    book = load_project_memory_map()
    with pytest.raises(ValueError):
        record_from_map_book(
            book, project_ref="proj-x", map_ref="map-x",
            map_age_days=1, project_files=10, covered_files=5,
            stale={"decision": 99})
    with pytest.raises(ValueError):
        inspect_opening_source(42)
    with pytest.raises(ValueError):
        inspect_opening_source({"nonsense": True})


def test_inspect_opening_source_judges_by_owning_layer():
    book = load_project_memory_map()
    seen = inspect_opening_source(book)
    assert seen["kind"] == "project-memory-map-book"
    assert seen["map_entries"] == 9
    seen = inspect_opening_source(book.entries[0])
    assert seen["kind"] == "project-memory-map-entry"
    assert seen["entry_id"] == book.entries[0].entry_id
    situation = load_session_memory().situations[0]
    seen = inspect_opening_source(situation)
    assert seen["kind"] == "session-situation"
    assert seen["session_ref"] == situation.session_ref


def test_panel_is_derived_in_panel_order():
    book = _book([_scratch_record(), _record(), _fresh_record()])
    panel = derive_panel(book)
    assert [r.record_id for r in panel.rows] == [
        "record-scratch", "record-test", "record-fresh"]
    assert panel.total_records == 3
    assert (panel.total_cold, panel.total_warming,
            panel.total_fresh) == (1, 1, 1)
    assert panel.distinct_projects == 3
    row = panel.row_for("record-test")
    assert row.mode == "background-rebuild"
    assert row.usable_entries == 20
    assert row.total_stale == 5
    assert row.rebuilding_areas == 2
    assert row.stage_count == 4
    assert row.first_stage == "serve-stale-map"
    assert panel.as_of == ON


def test_panel_refuses_a_stored_panel_that_disagrees():
    book = _book()
    stored = derive_panel(book).to_record()
    stored.pop("type")
    stored.pop("slice")
    stored["rows"] = [
        {k: v for k, v in row.items() if k not in ("type", "slice")}
        for row in stored["rows"]]
    assert validate_panel(stored, book).total_records == 1
    stored["rows"][0]["title"] = "a tampered row title"
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    with pytest.raises(ValueError):
        _book(panels=[derive_panel(book).to_record()])


def test_panel_account_and_mode_counts_are_its_own():
    book = _book([_record(), _fresh_record()])
    panel = derive_panel(book)
    assert panel.mode_counts == (
        ModeCount(mode="background-rebuild", items=1),
        ModeCount(mode="serve-fresh", items=1))
    assert "2 openings" in panel.account[0]
    tampered = derive_panel(book).to_record()
    tampered["account"] = ["a hand-written account"]
    with pytest.raises(ValueError):
        validate_panel(tampered)


def test_row_is_judged_against_its_record():
    record = _record()
    row = derive_panel(_book([record])).rows[0]
    assert validate_row(row, record) == row
    stored = row.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    assert build_row(stored, record) == row
    stored["usable_entries"] = 19
    with pytest.raises(ValueError):
        validate_row(stored, record)
    stored["usable_entries"] = 20
    stored["first_stage"] = "rebuild-area:gotcha"
    with pytest.raises(ValueError):
        validate_row(stored, record)


def test_verdict_bands_and_the_cold_example():
    assert derive_verdict(load_cold_start()).verdict == "cold"
    assert derive_verdict(_book([_fresh_record()])).verdict == "kind"
    assert derive_verdict(_book([_record()])).verdict == "warming"
    assert derive_verdict(_book(
        [_record(), _scratch_record()])).verdict == "cold"
    verdict = derive_verdict(_book([_record(), _fresh_record()]))
    assert verdict.total_records == 2
    assert verdict.distinct_projects == 2
    stored = verdict.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    assert build_verdict(stored, _book(
        [_record(), _fresh_record()])) == verdict
    stored["verdict"] = "kind"
    with pytest.raises(ValueError):
        validate_verdict(stored)
    with pytest.raises(ValueError):
        ColdStartVerdict(
            total_records=1, total_fresh=1, total_warming=0,
            total_cold=0, distinct_projects=1, earliest_on=ON,
            latest_on=ON, verdict="cold")


def test_progress_walks_the_plan_in_order():
    record = _record()
    plan = stage_plan_of(record)
    progress = derive_progress(record)
    assert progress.completed == ()
    assert progress.next_stage == "serve-stale-map"
    assert progress.complete is False
    walked = derive_progress(record, plan[:2])
    assert walked.next_stage == "rebuild-area:gotcha"
    done = derive_progress(record, plan)
    assert done.complete is True
    assert done.next_stage is None
    with pytest.raises(ValueError):
        derive_progress(record, ("verify-map",))
    with pytest.raises(ValueError):
        ColdStartProgress(
            record_id="record-test", stages=plan,
            completed=plan[:1], next_stage="verify-map")


def test_progress_is_judged_against_its_record():
    record = _record()
    progress = derive_progress(record, stage_plan_of(record)[:1])
    stored = progress.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    assert build_progress(stored, record) == progress
    assert validate_progress(progress, record) == progress
    stored["stages"] = ["serve-fresh-map"]
    with pytest.raises(ValueError):
        validate_progress(stored, record)


def test_book_laws_one_opening_per_project():
    book = _book([_record(), _fresh_record()])
    assert total_records(book) == 2
    assert record_refs(book) == (
        ("proj-test", "map-proj-test"),
        ("proj-fresh", "map-proj-fresh"))
    assert record_for(book, "proj-test").record_id == "record-test"
    with pytest.raises(KeyError):
        record_for(book, "proj-nope")
    with pytest.raises(ValueError):
        _book([_record(), _record(record_id="record-two")])
    with pytest.raises(ValueError):
        _book([_record(), _record()])
    with pytest.raises(ValidationError):
        validate_book({"records": []})


def test_book_file_loader_reads_any_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "cold_start.yaml").read_text(encoding="utf-8")
    path = tmp_path / "cold_start.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_cold_start_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.record_ids() == load_cold_start().record_ids()
    bad = tmp_path / "bad.yaml"
    bad.write_text(raw.replace("mythic-hammer", "two words"),
                   encoding="utf-8")
    with pytest.raises(ValidationError):
        load_cold_start_file(bad)


def test_registry_holds_records_one_by_one_and_marks_stages():
    registry = ColdStartRegistry()
    held = registry.register_record(_record(record_id=None))
    assert held.record_id == "record-1"
    registry.register_record(_fresh_record())
    assert [r.record_id for r in registry.list_records()] == [
        "record-1", "record-fresh"]
    assert registry.verdict().verdict == "warming"
    progress = registry.mark_stage("record-1")
    assert progress.completed == ("serve-stale-map",)
    with pytest.raises(ValueError):
        registry.mark_stage("record-1", "verify-map")
    registry.mark_stage("record-1", "rebuild-area:architecture")
    registry.mark_stage("record-1")
    final = registry.mark_stage("record-1")
    assert final.complete is True
    assert registry.is_complete("record-1") is True
    with pytest.raises(ValueError):
        registry.mark_stage("record-1")
    with pytest.raises(KeyError):
        registry.mark_stage("record-nope")


def test_registry_register_book_and_refusals():
    registry = ColdStartRegistry()
    book = _book([_record(), _fresh_record()])
    registry.register_book(book)
    assert registry.book().title == "A test cold-start book"
    assert registry.panel().total_records == 2
    with pytest.raises(ValueError):
        registry.register_record(_record(record_id="record-new"))
    with pytest.raises(ValueError):
        registry.register_book(_book([_scratch_record()], title="Another title"))
    assert registry.latest_record().record_id == "record-fresh"
    assert registry.record_for_project(
        "proj-test").record_id == "record-test"


def test_news_records_carry_headlines():
    record = _record()
    news = record_record(record)
    assert news["news"] is True
    assert "stale-but-usable" in news["headline"]
    assert record_record(_scratch_record())["headline"].find("no map") >= 0
    panel_news = panel_record(derive_panel(_book()))
    assert "Cold-start panel" in panel_news["headline"]
    verdict_news = verdict_record(derive_verdict(_book()))
    assert "warming" in verdict_news["headline"]
    progress_news = progress_record(derive_progress(record))
    assert "next stands serve-stale-map" in progress_news["headline"]
    book_news = book_record(_book())
    assert book_news["record_count"] == 1


def test_formatters_and_screen():
    book = load_cold_start()
    text = format_record(book.records[0])
    assert "opening-mythic-hammer" in text
    assert "background-rebuild" in text
    assert "rebuild-area:architecture" in text
    assert "Panel in Cold-Start Kindness" in format_panel(book)
    assert format_verdict(book).startswith(
        "Verdict in Cold-Start Kindness")
    assert "cold" in format_verdict(book)
    listed = format_records(book, mode="background")
    assert "opening-mythic-hammer" in listed
    assert "opening-old-sagas" not in listed
    progress_text = format_progress(
        derive_progress(book.records[0]))
    assert "serve-stale-map: standing" in progress_text
    screen = format_cold_start_screen()
    assert "Cold-Start Kindness (M-169)" in screen
    assert "opening-fresh-notes" in screen
    assert "mythic hammer" in plain_words(book.records[0])
    assert "Openings, in panel order" in panel_plain_words(book)
    assert "warming" not in verdict_plain_words(book)
    assert "cold" in verdict_plain_words(book)
    assert "next stage stands" in progress_plain_words(
        derive_progress(book.records[0]))


def test_parse_cold_start_args_grammar():
    assert parse_cold_start_args("") == ("show", None)
    assert parse_cold_start_args(None) == ("show", None)
    assert parse_cold_start_args("show") == ("show", None)
    assert parse_cold_start_args("list") == ("show", None)
    assert parse_cold_start_args("record opening-x") == (
        "record", "opening-x")
    assert parse_cold_start_args("project proj-x") == (
        "project", "proj-x")
    assert parse_cold_start_args("panel") == ("panel", None)
    assert parse_cold_start_args("verdict") == ("verdict", None)
    assert parse_cold_start_args("stages") == ("stages", None)
    for bad in ("record", "project two words", "panel now",
                "dance", None.__class__ and 42):
        with pytest.raises(ValueError):
            parse_cold_start_args(bad)


# -- agent layer -----------------------------------------------------------
#
# M-169 agent layer: the agent holds a
# ColdStartRegistry for the session (session state
# only, no new setting), records are held by being
# registered - published as their record_record
# session news through the checkpoint road, deduped
# per shape - the report road renders the held book
# (or the shipped example when unheld) through the
# pure formatters, an opening road raises a record
# over the session's own held project memory map by
# import (its entries counted by area, its own words
# never crossing, the held map never touched), a
# progress road marks ONLY the derived plan's stages
# done, stage by stage in order, on the held book,
# and the /coldstart surface rides both roads on the
# pure parser + formatters. Status, get, panel,
# verdict and report reads register and publish
# nothing, answer from the held registry first and
# from the shipped example only while nothing is
# held - a held record never falls back to the
# example. The panel and the verdict derive at call
# time from the whole book, never held. This layer
# sends nothing, posts nothing, schedules nothing,
# calls no model, persists nothing beyond the
# session journal news, starts no thread, rebuilds
# no live map and opens no live project - a stage
# marked done is marked on the session's own book
# alone, and there is no Part VIII board yet, so
# the screen is where the book is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _cold_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_cold_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "cold_start.yaml").read_text(encoding="utf-8")
    path = tmp_path / "cold_start.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestColdStartAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.cold_start_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["cold_start"]["title"] == EXAMPLE_TITLE
        assert len(status["cold_start"]["records"]) == 3
        assert status["panel"]["total_records"] == 3
        assert status["panel"]["total_warming"] == 1
        assert status["panel"]["total_cold"] == 1
        assert status["panels"][0]["panel_id"] == "panel-m168-boundary"
        assert status["book_record"]["record_count"] == 3
        assert status["verdict"]["verdict"] == "cold"
        assert len(status["progress"]) == 3
        assert "fresh-notes" in status["plain_words"]
        assert "Cold-Start Kindness (M-169)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._cold_start_registry()
        assert agent._cold_start_registry() is first
        assert agent._cold_start_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.cold_start_status()
        agent.get_cold_start_record("opening-mythic-hammer")
        agent.cold_start_for_project("old-sagas")
        agent.cold_start_panel()
        agent.cold_start_verdict()
        agent.report_cold_start()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("cold_start")] == []
        with pytest.raises(KeyError):
            agent.get_cold_start_record("opening-nope")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_cold_start_record(_record())
        status = agent.cold_start_status()
        assert [item["record_id"] for item in status["records"]] == [
            "record-test"]
        assert status["book"]["title"] == "Cold Start"
        assert status["panel"]["total_records"] == 1
        assert status["verdict"]["verdict"] == "warming"

    def test_held_record_never_falls_back_to_the_example(
            self, agent):
        agent.register_cold_start_record(_record())
        with pytest.raises(KeyError):
            agent.get_cold_start_record("opening-mythic-hammer")
        record = agent.get_cold_start_record("record-test")
        assert record.title == "the test project opens cold"
        assert agent.cold_start_for_project(
            "proj-test").record_id == "record-test"
        assert agent.cold_start_book().title == "Cold Start"


class TestColdStartAgentHolding:
    def test_register_record_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_cold_start_record(_record())
        assert outcome["record"]["record_id"] == "record-test"
        assert outcome["record_news"]["news"] is True
        agent.register_cold_start_record(_fresh_record())
        events = _cold_events(store, session_id, "cold_start_record")
        assert len(events) == 2
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_cold_start_record(_record())
        with pytest.raises(ValueError):
            agent.register_cold_start_record(_record())
        with pytest.raises(ValueError):
            agent.register_cold_start_record(
                _record(record_id="record-two"))
        events = _cold_events(store, session_id, "cold_start_record")
        assert len(events) == 1
        agent.close()

    def test_open_road_raises_over_the_held_map_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.open_cold_start_project(
            "proj-opened", map_age_days=90, project_files=500,
            covered_files=400, stale={"location": 2},
            opened_on=ON, opened_by=BY,
            origin_session="session-test", record_id="record-opened")
        assert outcome["mode"] == "background-rebuild"
        assert outcome["record"]["map_entries"] == 9
        assert outcome["stage_plan"][0] == "serve-stale-map"
        assert "rebuild-area:location" in outcome["stage_plan"]
        assert len(_cold_events(
            store, session_id, "cold_start_record")) == 1
        assert len(_cold_events(
            store, session_id, "cold_start_panel")) == 1
        assert len(_cold_events(
            store, session_id, "cold_start_verdict")) == 1
        agent.close()

    def test_open_road_touches_no_held_book(self, agent):
        before = [e.entry_id for e in
                  agent.project_memory_map_book().entries]
        agent.open_cold_start_project(
            "proj-opened", map_age_days=90, project_files=500,
            covered_files=400, stale={"location": 2},
            record_id="record-opened")
        after = [e.entry_id for e in
                 agent.project_memory_map_book().entries]
        assert before == after
        opened = agent.get_cold_start_record("record-opened")
        assert "detail" not in str(opened.to_record()["areas"])

    def test_progress_road_marks_stages_in_derived_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_cold_start_record(_record())
        outcome = agent.record_cold_start_progress("record-test")
        assert outcome["progress"]["completed"] == ["serve-stale-map"]
        assert outcome["complete"] is False
        with pytest.raises(ValueError):
            agent.record_cold_start_progress("record-test", "verify-map")
        agent.record_cold_start_progress(
            "record-test", "rebuild-area:architecture")
        agent.record_cold_start_progress("record-test")
        final = agent.record_cold_start_progress("record-test")
        assert final["complete"] is True
        with pytest.raises(ValueError):
            agent.record_cold_start_progress("record-test")
        events = _cold_events(store, session_id, "cold_start_progress")
        assert len(events) == 4
        agent.close()

    def test_progress_on_an_unheld_record_raises(self, agent):
        with pytest.raises(KeyError):
            agent.record_cold_start_progress("opening-mythic-hammer")

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_cold_start_book(
            _book([_record(), _fresh_record()]))
        assert outcome["count"] == 2
        assert [r["record_id"] for r in outcome["records"]] == [
            "record-test", "record-fresh"]
        events = _cold_events(store, session_id, "cold_start_record")
        assert [e["record_id"] for e in events] == [
            "record-test", "record-fresh"]
        assert len(_cold_events(
            store, session_id, "cold_start_panel")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_cold_start_book()
        assert outcome["count"] == 3
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_cold_events(
            store, session_id, "cold_start_record")) == 3
        with pytest.raises(ValueError):
            agent.record_cold_start_book()
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_cold_book(tmp_path)
        book = load_cold_start_file(path)
        outcome = agent.record_cold_start_book(book)
        assert outcome["count"] == 3
        assert agent.cold_start_book().title == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_cold_start()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert len(report["records"]) == 3
        assert report["verdict"]["verdict"] == "cold"
        agent.register_cold_start_record(_record())
        report = agent.report_cold_start()
        assert [r["record_id"] for r in report["records"]] == [
            "record-test"]
        assert report["progress"][0]["next_stage"] == "serve-stale-map"

    def test_holding_and_progressing_start_no_rebuild(self, agent):
        for name in (
                "rebuild_map", "rebuild_live_map",
                "start_background_rebuild", "spawn_rebuild_thread",
                "open_live_project", "persist_cold_start",
                "cold_start_board", "send_cold_start_record",
                "schedule_cold_start", "sync_cold_start_record",
                "apply_cold_start_plan", "run_cold_start_rebuild"):
            assert not hasattr(agent, name), name
        agent.register_cold_start_record(_record())
        agent.record_cold_start_progress("record-test")
        registry = agent._cold_start_registry()
        assert registry.completed_stages("record-test") == (
            "serve-stale-map",)
        assert [e.entry_id for e in
                agent.project_memory_map_book().entries] != []


class TestColdStartTerminalSurface:
    def test_show_record_project_panel_verdict_stages(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/coldstart")
        assert "Cold-Start Kindness (M-169)" in text
        _, _, text = _slash(
            agent, "/coldstart record opening-mythic-hammer")
        assert "the mythic hammer campaign home opens cold" in text
        _, _, text = _slash(agent, "/coldstart project old-sagas")
        assert "opening-old-sagas" in text
        _, _, text = _slash(agent, "/coldstart panel")
        assert "Panel in Cold-Start Kindness" in text
        _, _, text = _slash(agent, "/coldstart verdict")
        assert "cold" in text
        _, _, text = _slash(agent, "/coldstart stages")
        assert "rebuild-area:architecture" in text
        assert "opening-fresh-notes" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/coldstart [show|record <record-id>"
                "|project <project-ref>|panel|verdict"
                "|stages]") in text
        _, _, text = _slash(agent, "/coldstart dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/coldstart record opening-nope")
        assert "no record named" in text


@pytest.fixture()
def cold_handler(agent, monkeypatch):
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


def _cold_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestColdStartCommand:
    def test_show_is_default(self, cold_handler, agent):
        cold_handler._handle_coldstart("")
        assert "Cold-Start Kindness (M-169)" in (
            _cold_published_text(cold_handler))

    def test_record_project_panel_verdict_stages(
            self, cold_handler, agent):
        cold_handler._handle_coldstart("record opening-mythic-hammer")
        assert "opening-mythic-hammer" in (
            _cold_published_text(cold_handler))
        cold_handler._handle_coldstart("project old-sagas")
        assert "opening-old-sagas" in _cold_published_text(
            cold_handler)
        cold_handler._handle_coldstart("panel")
        assert "Panel in Cold-Start Kindness" in (
            _cold_published_text(cold_handler))
        cold_handler._handle_coldstart("verdict")
        assert "cold" in _cold_published_text(cold_handler)
        cold_handler._handle_coldstart("stages")
        assert "serve-stale-map" in _cold_published_text(cold_handler)

    def test_bad_grammar_is_published(
            self, cold_handler, agent):
        cold_handler._handle_coldstart("dance party")
        assert USAGE in _cold_published_text(cold_handler)
        cold_handler._handle_coldstart("record opening-nope")
        assert "no record named" in _cold_published_text(
            cold_handler)


class TestChatScreenRoutingColdStart:
    def test_coldstart_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/coldstart panel", _FakeLog())
        assert calls == [("/coldstart", "panel")]
