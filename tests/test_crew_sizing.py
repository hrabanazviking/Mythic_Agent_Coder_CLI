"""M-135 Crew sizing honesty - pure-layer tests.

TIER: integration

The pure layer is the crew-size recommendation
as data: a sizing book of task shapes (one task
per case - its title, the task in plain words,
the member who would lead it, the office the
work fits, how many independent pieces it splits
into, and whether it is tightly coupled or
loose), the shipped example sizing book held in
a data file, a loader that reads a sizing book
from any file, the recommended size derived from
the shape alone - tightly coupled work takes one
pair of hands, loose work one pair per piece, up
to six - records shaped as session news, and a
registry. Nothing here spawns, sizes or models a
crew, and no model is called: the recommendation
is derived, never stored, and a stored
recommendation that disagrees with the derived
one is refused.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.crew_members import load_casting
from mythic_agent.core.offices import formal_office_ids
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.crew_sizing import (
    COUPLING_KINDS,
    CREW_SIZING_RESOURCE,
    CREW_SIZING_SCHEMA,
    CREW_SIZING_SLICE,
    MAX_CREW_SIZE,
    PLAIN_EXPLANATION,
    SIZE_KINDS,
    USAGE,
    SizingBook,
    SizingRecommendation,
    SizingRegistry,
    TaskShape,
    book_record,
    build_book,
    build_recommendation,
    build_shape,
    case_record,
    derive_recommendation,
    format_crew_sizing_screen,
    format_recommendation,
    format_shape,
    format_shapes,
    format_size_kinds,
    load_crew_sizing,
    load_crew_sizing_file,
    normalize_coupling,
    normalize_size_kind,
    parse_crew_size_args,
    plain_words,
    recommendation_plain_words,
    recommendation_record,
    size_kind_for,
    validate_book,
    validate_recommendation,
    validate_shape,
)

ROOT = Path(__file__).resolve().parents[1]


def _shape(**kwargs):
    kwargs.setdefault("case_id", "a-task")
    kwargs.setdefault("lead", "auditor")
    kwargs.setdefault("office", "auditor")
    kwargs.setdefault("title", "A task")
    kwargs.setdefault("detail", "The task stands so.")
    kwargs.setdefault("independent_pieces", 3)
    kwargs.setdefault("coupling", "loose")
    return TaskShape(**kwargs)


def _book_data():
    return {
        "schema": CREW_SIZING_SCHEMA, "slice": CREW_SIZING_SLICE,
        "guide": {"title": "A sizing book"},
        "cases": [
            {"case_id": "solo-task", "lead": "forge_worker",
             "office": "forge_worker", "title": "Solo task",
             "detail": "It leans on itself.", "independent_pieces": 5,
             "coupling": "tight"},
            {"case_id": "pair-task", "lead": "scribe",
             "office": "scribe", "title": "Pair task",
             "detail": "It splits in two.", "independent_pieces": 2,
             "coupling": "loose"},
            {"case_id": "crew-task", "lead": "auditor",
             "office": "auditor", "title": "Crew task",
             "detail": "It splits in three.", "independent_pieces": 3,
             "coupling": "loose"},
            {"case_id": "wide-task", "lead": "cartographer",
             "office": "cartographer", "title": "Wide task",
             "detail": "It splits widely.", "independent_pieces": 8,
             "coupling": "loose"},
        ]}


def _write_sizing(tmp_path, data):
    path = tmp_path / "sizing.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_constants_and_usage():
    assert CREW_SIZING_SLICE == "M-135"
    assert CREW_SIZING_RESOURCE == "crew_sizing.yaml"
    assert CREW_SIZING_SCHEMA == "mythic.crew_sizing/1"
    assert MAX_CREW_SIZE == 6
    assert COUPLING_KINDS == ("tight", "loose")
    assert SIZE_KINDS == ("solo", "pair", "crew", "full_crew")
    assert USAGE.startswith("Usage: /crewsize")
    assert "one pair of hands beats six" in PLAIN_EXPLANATION
    assert "spawns no crew" in PLAIN_EXPLANATION


def test_shipped_example_book_shape():
    book = load_crew_sizing()
    assert book.title == "Crew sizing at the M-134 slice boundary"
    assert len(book.cases) == 4
    sizes = {c.case_id: c.recommended_size() for c in book.cases}
    assert sizes == {
        "tangled-single-file-fix": 1,
        "docs-and-tests-split": 2,
        "four-independent-slices": 4,
        "wide-census-sweep": 6}
    assert [c.case_id for c in book.cases_for("solo")] == [
        "tangled-single-file-fix"]
    assert [c.case_id for c in book.cases_for("pair")] == [
        "docs-and-tests-split"]
    assert [c.case_id for c in book.cases_for("crew")] == [
        "four-independent-slices"]
    assert [c.case_id for c in book.cases_for("full-crew")] == [
        "wide-census-sweep"]
    recs = book.recommendations()
    assert [r.kind for r in recs] == [
        "solo", "pair", "crew", "full_crew"]


def test_example_members_and_offices_are_the_shipped_casting():
    casting = load_casting()
    ids = [member.member_id for member in casting.members]
    for case in load_crew_sizing().cases:
        assert case.lead in ids
        assert case.office in formal_office_ids()


def test_derivation_is_deterministic():
    shape = _shape()
    first = derive_recommendation(shape)
    assert derive_recommendation(shape) == first
    assert first.recommended_size == 3
    assert first.kind == "crew"
    assert "3 pairs of hands" in first.reason
    assert size_kind_for(1) == "solo"
    assert size_kind_for(2) == "pair"
    assert size_kind_for(4) == "crew"
    assert size_kind_for(6) == "full_crew"


def test_one_pair_of_hands_beats_six_for_tight_work():
    shape = _shape(independent_pieces=6, coupling="tight")
    rec = derive_recommendation(shape)
    assert rec.recommended_size == 1
    assert rec.kind == "solo"
    assert "One pair of hands beats six" in rec.reason
    solo = load_crew_sizing().case_for("tangled-single-file-fix")
    assert solo.independent_pieces == 6
    assert derive_recommendation(solo).recommended_size == 1


def test_loose_work_is_capped_at_six():
    rec = derive_recommendation(_shape(independent_pieces=99))
    assert rec.recommended_size == MAX_CREW_SIZE
    assert rec.kind == "full_crew"
    assert "six pairs of hands is the honest crew" in rec.reason
    one = derive_recommendation(_shape(independent_pieces=1))
    assert one.recommended_size == 1
    assert one.kind == "solo"
    assert "does not split" in one.reason


def test_stored_recommendation_must_agree_with_the_derived_one():
    shape = _shape()
    derived = derive_recommendation(shape)
    stored = {"case_id": "a-task", "size": 3, "band": "crew"}
    assert validate_recommendation(stored, shape) == derived
    assert build_recommendation(derived) is derived
    with pytest.raises(ValueError):
        validate_recommendation({"case_id": "a-task", "size": 6}, shape)
    with pytest.raises(ValueError):
        validate_recommendation(
            {"case_id": "a-task", "size": 3, "band": "solo"}, shape)
    with pytest.raises(ValueError):
        validate_shape({"lead": "auditor", "office": "auditor",
                        "title": "T", "detail": "So.", "pieces": 3,
                        "coupling": "loose", "recommended_size": 2})
    ok = validate_shape({"lead": "auditor", "office": "auditor",
                         "title": "T", "detail": "So.", "pieces": 3,
                         "coupling": "loose", "crew_size": 3})
    assert ok.recommended_size() == 3


def test_recommendation_band_must_match_its_size():
    with pytest.raises(ValueError):
        SizingRecommendation(
            case_id="x-task", title="T", recommended_size=1,
            kind="crew", reason="So.")
    rec = SizingRecommendation(
        case_id="x-task", title="T", recommended_size=2,
        kind="pair", reason="So.")
    assert rec.kind == "pair"
    with pytest.raises(ValueError):
        validate_recommendation({"size": 2, "bogus": 1}, _shape())
    with pytest.raises(ValueError):
        derive_recommendation(_shape(case_id=None))


def test_normalize_coupling_readings_and_refusals():
    assert normalize_coupling("Tight") == "tight"
    assert normalize_coupling("tightly-coupled") == "tight"
    assert normalize_coupling("single-head") == "tight"
    assert normalize_coupling("LOOSE") == "loose"
    assert normalize_coupling("Independent") == "loose"
    assert normalize_coupling("splittable") == "loose"
    with pytest.raises(ValueError):
        normalize_coupling("medium")
    with pytest.raises(ValueError):
        normalize_coupling("")
    with pytest.raises(ValueError):
        normalize_coupling(None)


def test_normalize_size_kind_readings_and_refusals():
    assert normalize_size_kind("Solo") == "solo"
    assert normalize_size_kind("one") == "solo"
    assert normalize_size_kind("Two") == "pair"
    assert normalize_size_kind("small-crew") == "crew"
    assert normalize_size_kind("full-crew") == "full_crew"
    assert normalize_size_kind("Maximum") == "full_crew"
    with pytest.raises(ValueError):
        normalize_size_kind("army")
    with pytest.raises(ValueError):
        normalize_size_kind(3)


def test_shape_validation_and_two_spellings_refusal():
    shape = validate_shape(
        {"member": "guardian", "lead_office": "auditor",
         "name": "Words", "body": "It stands so.",
         "chunks": 2, "tightness": "Independent"})
    assert shape.lead == "guardian"
    assert shape.office == "auditor"
    assert shape.title == "Words"
    assert shape.independent_pieces == 2
    assert shape.coupling == "loose"
    with pytest.raises(ValueError):
        validate_shape({"lead": "guardian", "office": "auditor",
                        "title": "One", "name": "Two", "detail": "So.",
                        "pieces": 1, "coupling": "loose"})
    with pytest.raises(ValueError):
        validate_shape({"lead": "guardian", "office": "auditor",
                        "title": "T", "detail": "So.", "pieces": 1,
                        "coupling": "loose", "bogus": 1})
    with pytest.raises(ValueError):
        validate_shape({"lead": "guardian", "office": "auditor",
                        "title": "T", "pieces": 1, "coupling": "loose"})
    assert build_shape(lead="scribe", office="scribe", title="Built",
                       detail="So.", independent_pieces=1,
                       coupling="tight").recommended_size() == 1
    assert plain_words(_shape()).startswith("auditor - A task (loose, 3")


def test_shape_refusals():
    with pytest.raises(ValueError):
        _shape(detail="  ")
    with pytest.raises(ValueError):
        _shape(title="")
    with pytest.raises(ValueError):
        _shape(lead="two words")
    with pytest.raises(ValueError):
        _shape(office="polymath")
    with pytest.raises(ValueError):
        _shape(office="wizard")
    with pytest.raises(ValueError):
        _shape(independent_pieces=0)
    with pytest.raises(ValueError):
        _shape(independent_pieces="three")
    with pytest.raises(ValueError):
        _shape(independent_pieces=True)
    with pytest.raises(ValueError):
        _shape(coupling="medium")


def test_book_validation_and_shared_view():
    book = validate_book(_book_data())
    assert book.title == "A sizing book"
    assert [c.case_id for c in book.cases] == [
        "solo-task", "pair-task", "crew-task", "wide-task"]
    assert book.case_for("wide-task").recommended_size() == 6
    assert [c.case_id for c in book.cases_for("solo")] == ["solo-task"]
    assert build_book(book) is book
    with pytest.raises(KeyError):
        book.case_for("missing")


def test_book_refusals():
    data = _book_data()
    data["schema"] = "mythic.other/1"
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    data["bogus"] = 1
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    data["cases"][1]["case_id"] = "solo-task"
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    del data["cases"]
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    del data["guide"]["title"]
    with pytest.raises(ValidationError):
        validate_book(data)
    with pytest.raises(ValueError):
        SizingBook(title="T", cases=(
            _shape(case_id="x-task"),
            _shape(case_id="x-task", title="Other")))


def test_file_loader_round_trip_and_missing_file(tmp_path):
    path = _write_sizing(tmp_path, _book_data())
    book = load_crew_sizing_file(path)
    assert book.title == "A sizing book"
    assert book.case_for("pair-task").lead == "scribe"
    with pytest.raises(FileNotFoundError):
        load_crew_sizing_file(tmp_path / "nope.yaml")


def test_registry_hold_and_recommendations():
    registry = SizingRegistry()
    registry.register_book(validate_book(_book_data()))
    assert registry.get_case("solo-task").lead == "forge_worker"
    assert [c.case_id for c in registry.list_cases()] == [
        "solo-task", "pair-task", "crew-task", "wide-task"]
    assert registry.recommendation_for("wide-task").recommended_size == 6
    assert [r.kind for r in registry.recommendations()] == [
        "solo", "pair", "crew", "full_crew"]
    assert [c.case_id for c in registry.cases_for("pair")] == ["pair-task"]
    assert registry.book().title == "A sizing book"
    with pytest.raises(KeyError):
        registry.get_case("missing")


def test_registry_auto_ids_and_refusals():
    registry = SizingRegistry(SizingBook(title="T"))
    first = registry.register_case(_shape(case_id=None))
    assert first.case_id == "case-1"
    second = registry.register_case(
        _shape(case_id=None, title="Second", coupling="tight"))
    assert second.case_id == "case-2"
    assert registry.recommendation_for("case-2").kind == "solo"
    with pytest.raises(ValueError):
        registry.register_case(_shape(case_id="case-1"))
    with pytest.raises(ValueError):
        registry.register_book(validate_book(_book_data()))
    with pytest.raises(ValueError):
        SizingRegistry().book()
    fresh = SizingRegistry(load_crew_sizing())
    assert len(fresh.recommendations()) == 4
    with pytest.raises(ValueError):
        fresh.register_book(load_crew_sizing())


def test_records_are_session_news():
    case = case_record(_shape())
    assert case["type"] == "crew_sizing_case"
    assert case["slice"] == "M-135"
    assert case["news"] is True
    assert "auditor" in case["headline"]
    book = book_record(load_crew_sizing())
    assert book["type"] == "crew_sizing_book"
    assert book["case_count"] == 4
    rec = recommendation_record(derive_recommendation(_shape()))
    assert rec["type"] == "crew_sizing_recommendation"
    assert rec["recommended_size"] == 3
    assert "3 pairs of hands" in rec["headline"]
    solo = recommendation_record(
        derive_recommendation(load_crew_sizing().cases[0]))
    assert "one pair of hands" in solo["headline"]
    assert "beats six" in solo["headline"]
    with pytest.raises(ValueError):
        recommendation_record(
            {"case_id": "a-task", "size": 6}, _shape())


def test_recommendation_plain_words_cover_all_four_bands():
    words = recommendation_plain_words(load_crew_sizing())
    assert "Untangle one shared file" in words
    assert "one pair of hands (solo)" in words
    assert "One pair of hands beats six" in words
    assert "Write the guide while its tests are drafted" in words
    assert "Build four slices that share no files" in words
    assert "Sweep the whole tree for a census" in words
    assert "6 pairs of hands (full-crew)" in words
    empty = recommendation_plain_words(SizingBook(title="T"))
    assert empty == "T"
    bare = recommendation_plain_words(
        derive_recommendation(_shape(coupling="tight")))
    assert "beats six" in bare


def test_formatters_and_screen():
    book = load_crew_sizing()
    assert "forge_worker / tangled-single-file-fix [solo" in format_shape(
        book.case_for("tangled-single-file-fix"))
    assert "wide-census-sweep" in format_shapes(book)
    assert "wide-census-sweep" not in format_shapes(book, "solo")
    rec_text = format_recommendation(book)
    assert "Sizing for Crew sizing at the M-134 slice boundary:" in rec_text
    assert "solo (1):" in rec_text
    assert "full-crew (6):" in rec_text
    assert format_size_kinds() == (
        "Size kinds: solo, pair, crew, full-crew")
    screen = format_crew_sizing_screen(book)
    assert "Crew sizing honesty (M-135)" in screen
    assert USAGE in screen
    assert format_shapes(SizingBook(
        title="T")) == "No task shapes stand sized."


def test_parse_crew_size_args_grammar():
    assert parse_crew_size_args("") == ("show", None)
    assert parse_crew_size_args("show") == ("show", None)
    assert parse_crew_size_args("recommend tangled-single-file-fix") == (
        "recommend", "tangled-single-file-fix")
    assert parse_crew_size_args("case docs-and-tests-split") == (
        "case", "docs-and-tests-split")
    assert parse_crew_size_args("solo") == ("band", "solo")
    assert parse_crew_size_args("Full-Crew") == ("band", "full_crew")
    assert parse_crew_size_args("crew") == ("band", "crew")
    assert parse_crew_size_args("kinds") == ("kinds", None)
    with pytest.raises(ValueError):
        parse_crew_size_args("recommend")
    with pytest.raises(ValueError):
        parse_crew_size_args("bogus words here")
    with pytest.raises(ValueError):
        parse_crew_size_args(42)


def test_no_live_roads_in_pure_layer():
    import mythic_agent.core.crew_sizing as module
    source = Path(module.__file__).read_text(encoding="utf-8")
    for banned in ("import subprocess", "requests.", "openai",
                   "anthropic", "AgentManager", "def spawn",
                   "def persist", "def schedule"):
        assert banned not in source
    record = _shape().to_record()
    assert "recommended_size" not in record
    assert "kind" not in record
