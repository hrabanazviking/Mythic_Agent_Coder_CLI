"""M-245 Aesir deepening — pure-layer tests.

TIER: unit

The pure layer holds Aesir's honest capability reports,
the per-role selection book, and the derived router ask
as data. A report may narrow Aesir's documented v1
ceiling, never widen it; a selection names a real crew
office or refuses by name; an ask is granted only what
the report grants, names the resident model only, and
is not shaped at all for an unselected office or an
unreachable server. No session is opened, no model is
called, and no server is probed in this layer.
"""

import pytest

from mythic_agent.core.aesir_deepening import (
    AESIR_SCHEMA,
    CAPABILITY_CEILING,
    NEEDS,
    AesirAsk,
    AesirCapabilityReport,
    SelectionBook,
    format_ask,
    format_report,
    format_selections,
    load_selection_book,
    load_selection_book_file,
    plain_words,
    selection_record,
    shape_ask,
    validate_report,
    validate_selection,
    validate_selection_book,
)
from mythic_agent.core.role_routing import office_ids
from mythic_agent.core.validation import ValidationError

LIVE_REPORT = {
    "streaming": True,
    "tool_calling": False,
    "vision": False,
    "json_mode": False,
    "embeddings": False,
    "resident_models": 1,
    "catalog_is_readiness": False,
    "reachable": True,
    "backend": "cpu",
    "profile": "default",
    "context": 8192,
    "model": "zen-4b",
    "model_digest": "sha256:abc",
}


def live_report(**overrides):
    raw = dict(LIVE_REPORT)
    raw.update(overrides)
    return validate_report(raw)


def test_ceiling_is_aesirs_documented_v1_shape():
    assert CAPABILITY_CEILING == {
        "streaming": True, "tool_calling": False,
        "vision": False, "json_mode": False,
        "embeddings": False, "resident_models": 1}


def test_report_holds_live_fields_whole():
    report = live_report()
    assert isinstance(report, AesirCapabilityReport)
    assert report.model == "zen-4b"
    assert report.context == 8192
    assert report.record()["backend"] == "cpu"


def test_report_missing_live_fields_stay_unknown():
    report = validate_report({"reachable": False})
    assert report.backend is None
    assert report.model is None
    assert report.streaming is True


def test_report_may_narrow_but_never_widen():
    narrowed = live_report(streaming=False)
    assert narrowed.streaming is False
    for key in ("tool_calling", "vision", "json_mode",
                "embeddings"):
        with pytest.raises(ValidationError, match=key):
            live_report(**{key: True})


def test_report_refuses_extra_resident_models():
    with pytest.raises(ValidationError,
                       match="resident_models"):
        live_report(resident_models=2)


def test_report_refuses_catalog_as_readiness():
    with pytest.raises(ValidationError,
                       match="catalog_is_readiness"):
        live_report(catalog_is_readiness=True)


def test_report_refuses_unknown_keys_and_bad_shapes():
    with pytest.raises(ValidationError, match="unknown"):
        live_report(surprise=True)
    with pytest.raises(ValidationError, match="streaming"):
        live_report(streaming="yes")
    with pytest.raises(ValidationError):
        validate_report(["not", "a", "mapping"])


def test_shipped_book_covers_every_office_once():
    book = load_selection_book()
    assert isinstance(book, SelectionBook)
    offices = [s.office for s in book.selections]
    assert sorted(offices) == sorted(office_ids())
    assert len(offices) == len(set(offices))


def test_shipped_book_tool_offices_not_selected():
    book = load_selection_book()
    for office in ("auditor", "forge_worker", "guardian"):
        assert book.for_office(office).selected is False
    for office in ("primary", "scribe", "skald"):
        assert book.for_office(office).selected is True


def test_selection_refuses_unknown_office_by_name():
    with pytest.raises(ValidationError, match="wizard"):
        validate_selection({
            "office": "wizard", "selected": True,
            "reason": "because", "capability": "none"})
    book = load_selection_book()
    with pytest.raises(ValidationError, match="wizard"):
        book.for_office("wizard")


def test_selection_refuses_half_written_records():
    with pytest.raises(ValidationError, match="reason"):
        validate_selection({
            "office": "scribe", "selected": True,
            "reason": "  ", "capability": "streaming"})
    with pytest.raises(ValidationError,
                       match="capability"):
        validate_selection({
            "office": "scribe", "selected": True,
            "reason": "words", "capability": "flight"})


def test_book_refuses_wrong_schema_and_duplicates():
    with pytest.raises(ValidationError, match="schema"):
        validate_selection_book({"schema": "other/9",
                                 "selections": []})
    row = {"office": "scribe", "selected": True,
           "reason": "words", "capability": "streaming"}
    with pytest.raises(ValidationError, match="duplicate"):
        validate_selection_book({
            "schema": AESIR_SCHEMA,
            "selections": [row, dict(row)]})


def test_book_loads_from_any_file(tmp_path):
    path = tmp_path / "book.yaml"
    path.write_text(
        "schema: mythic.aesir_deepening/1\n"
        "selections:\n"
        "- office: scribe\n  selected: true\n"
        "  capability: streaming\n  reason: words\n",
        encoding="utf-8")
    book = load_selection_book_file(path)
    assert book.for_office("scribe").selected is True


def test_selection_record_is_plain_data():
    book = load_selection_book()
    record = selection_record(book, "scribe")
    assert record["office"] == "scribe"
    assert record["selected"] is True


def test_ask_grants_only_what_the_report_grants():
    book = load_selection_book()
    ask = shape_ask(book, live_report(), "scribe",
                    needs=("streaming", "tool_calling"))
    assert isinstance(ask, AesirAsk)
    assert ask.shaped is True
    assert ask.road == "aesir"
    assert ask.granted == ("streaming",)
    assert ask.refused == ("tool_calling",)
    assert ask.model == "zen-4b"


def test_ask_reshapes_json_mode_to_boolean_subset():
    book = load_selection_book()
    ask = shape_ask(book, live_report(), "skald",
                    needs=("json_mode",))
    assert "json_mode" in ask.refused
    assert "structured_boolean" in ask.granted


def test_ask_names_only_the_resident_model():
    book = load_selection_book()
    ask = shape_ask(book, live_report(), "scribe",
                    model="some-other-model")
    assert ask.model is None
    assert "model:some-other-model" in ask.refused
    ask = shape_ask(book, live_report(), "scribe",
                    model="zen-4b")
    assert ask.model == "zen-4b"


def test_ask_not_shaped_for_unselected_office():
    book = load_selection_book()
    ask = shape_ask(book, live_report(), "auditor",
                    needs=("streaming",))
    assert ask.shaped is False
    assert ask.road == "session_default"
    assert ask.granted == ()


def test_ask_not_shaped_when_aesir_is_silent():
    book = load_selection_book()
    report = validate_report({"reachable": False})
    ask = shape_ask(book, report, "scribe",
                    needs=("streaming",))
    assert ask.shaped is False
    assert ask.road == "session_default"


def test_ask_refuses_unknown_needs_by_name():
    book = load_selection_book()
    with pytest.raises(ValidationError, match="flight"):
        shape_ask(book, live_report(), "scribe",
                  needs=("flight",))
    assert "flight" not in NEEDS


def test_formatters_speak_plainly():
    book = load_selection_book()
    report = live_report()
    assert "zen-4b" in format_report(report)
    assert "scribe" in format_selections(book)
    ask = shape_ask(book, report, "scribe",
                    needs=("streaming",))
    assert "scribe" in format_ask(ask)
    assert "Aesir" in plain_words()
