"""M-184 Onboarding in Five Minutes - pure-layer tests.

TIER: integration

The pure layer is the first run, held as data:
one detection held whole - under its provider,
the named probe that looked for it, and the
outcome that probe honestly returned, found or
absent - the Kista key-keeping offer held as an
offer with its answer, its key never held, and
the walk: one tiny real task, its steps held in
order under the one ordering rule, success
before configuration, always. Detection is
derived from named probes and availability is
never faked: a provider no probe found stands
absent, named in its gaps. A walk demanding
configuration before the first success refuses
by name. The panel is derived for one held view
and the verdict is derived for the whole book
under one view. The shipped example book is held
in a data file, and a loader reads a book from
any file. This layer detects nothing live, keeps
no key, runs no task and configures nothing: it
holds the first run as data and tells it.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.onboarding_five import (
    DETECTION_OUTCOMES,
    OFFER_DECISIONS,
    ONBOARDING_FIVE_RESOURCE,
    ONBOARDING_FIVE_SCHEMA,
    ONBOARDING_FIVE_SLICE,
    PLAIN_EXPLANATION,
    PROBES,
    SUCCESS_BEFORE_CONFIGURATION_RULE,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    WALK_ACTION,
    WALK_PHASES,
    DetectionRecord,
    OfferRecord,
    OnboardingBook,
    OnboardingPanel,
    OnboardingRegistry,
    OnboardingVerdict,
    OnboardingView,
    WalkStep,
    book_record,
    build_book,
    build_detection,
    build_offer,
    build_panel,
    build_row,
    build_step,
    build_verdict,
    build_view,
    derive_panel,
    derive_verdict,
    derive_walk,
    detection_gaps,
    detection_passes,
    detection_plain_words,
    detection_record,
    detections_for_outcome,
    format_book,
    format_detection,
    format_offer,
    format_onboarding_five_screen,
    format_panel,
    format_verdict,
    format_view,
    format_walk,
    inspect_onboarding_source,
    load_onboarding_five,
    load_onboarding_five_file,
    normalize_decision,
    normalize_outcome,
    normalize_phase,
    normalize_probe,
    normalize_view_filter,
    offer_record,
    panel_plain_words,
    panel_record,
    parse_onboarding_args,
    passing_detections,
    plain_lines,
    plain_words,
    segment_of,
    shown_detections,
    step_record,
    total_detections,
    validate_book,
    validate_detection,
    validate_offer,
    validate_panel,
    validate_row,
    validate_step,
    validate_verdict,
    validate_view,
    verdict_plain_words,
    verdict_record,
    view_plain_words,
    view_record,
    walk_plain_words,
    walk_record,
    walk_steps,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]
ON = "2026-11-09"
BY = "the coordinator"
EXAMPLE_TITLE = "Onboarding in five minutes at the M-183 slice boundary"


def _detection(**overrides):
    fields = {
        "detection_id": "det-test",
        "seq": 1,
        "provider": "Ollama",
        "probe": "local door probe",
        "outcome": "found",
        "detail": "A test detection held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_detection(fields)


def _stored_detection(detection):
    return detection.to_record()


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    return view.to_record()


def _step(**overrides):
    fields = {
        "step_id": "step-test",
        "seq": 1,
        "phase": "detect",
        "title": "A test step",
        "detail": "A test walk step held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_step(fields)


def _offer(**overrides):
    fields = {
        "offer_id": "offer-test",
        "seq": 1,
        "provider": "OpenAI",
        "decision": "pending",
        "detail": "A test offer held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_offer(fields)


def _book(detections=None, views=None, steps=None, offers=None,
          **overrides):
    fields = {
        "schema": ONBOARDING_FIVE_SCHEMA,
        "slice": "M-184",
        "guide": {"title": "A test onboarding book"},
        "detections": [_stored_detection(item) for item in (
            detections if detections is not None else [_detection()])],
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "steps": [item.to_record() for item in (steps or [])],
        "offers": [item.to_record() for item in (offers or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(detections=[
        _detection(),
        _detection(detection_id="det-absent", seq=2, provider="Anthropic",
                   probe="environment key probe", outcome="absent"),
    ])


# ---------------------------------------------------------------------
# The shipped example book, the roadmap and the charter.
# ---------------------------------------------------------------------

def test_shipped_book_loads_with_pinned_shape():
    book = load_onboarding_five()
    assert book.title == EXAMPLE_TITLE
    assert book.detection_ids() == (
        "det-ollama-door", "det-openai-env", "det-aesir-door",
        "det-anthropic-env", "det-lmstudio-door",
        "det-openrouter-registry")
    assert [v.view_id for v in book.views] == ["view-all", "view-found"]
    assert [s.phase for s in book.steps] == [
        "detect", "walk", "success", "offer", "configure"]
    assert len(book.offers) == 1
    assert book.offers[0].decision == "declined"
    assert book.offers[0].provider == "OpenAI"
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m183-boundary"
    assert panel.as_of == "2026-11-09"
    assert [row.item_id for row in panel.rows] == list(book.detection_ids())
    derived = derive_panel(book, "view-all")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.outcome: c.items for c in panel.outcome_counts} == {
        "found": 4, "absent": 2}
    assert derive_verdict(book, "view-all").verdict == "strained"
    assert derive_verdict(book, "view-all").passing_shown == 4
    assert derive_verdict(book, "view-found").verdict == "open"
    assert derive_verdict(book, "view-found").passing_shown == 4
    assert derive_walk(book).passes() is True
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / ONBOARDING_FIVE_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == ONBOARDING_FIVE_SCHEMA
    assert raw["slice"] == "M-184"
    assert "verdict" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-184")]
    assert slice_.title == "Onboarding in five minutes"
    assert slice_.part == 8
    assert "detects providers" in slice_.summary
    assert "Kista key-keeping" in slice_.summary
    assert "tiny real task" in slice_.summary
    assert "success before" in slice_.summary
    assert "configuration, always" in slice_.summary
    assert ONBOARDING_FIVE_SLICE == "M-184"


def test_charter_names_m184_on_two_rows():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert owners.count("M-184") == 2
    assert "M-184" in charter.screen("splash").owning_slices
    assert "M-184" in charter.screen("setup_wizard").owning_slices
    direction = " ".join(charter.screen("setup_wizard").direction.split())
    assert "one real success before configuration" in direction
    assert charter.screen("setup_wizard").verdict == "rebuild"


def test_closed_vocabularies():
    assert DETECTION_OUTCOMES == ("found", "absent")
    assert PROBES == (
        "environment key probe", "local door probe",
        "registry probe", "config reference probe")
    assert VIEW_FILTERS == ("all", "found", "absent")
    assert WALK_PHASES == ("detect", "walk", "success", "offer", "configure")
    assert OFFER_DECISIONS == ("accepted", "declined", "pending")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert WALK_ACTION == "walk"
    assert normalize_outcome("FOUND") == "found"
    assert normalize_probe("Local Door Probe") == "local door probe"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_phase("SUCCESS") == "success"
    assert normalize_decision("Declined") == "declined"
    with pytest.raises(ValueError):
        normalize_outcome("maybe")
    with pytest.raises(ValueError):
        normalize_probe("a guess")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_phase("tour")
    with pytest.raises(ValueError):
        normalize_decision("later")
    assert "success before configuration, always" in (
        SUCCESS_BEFORE_CONFIGURATION_RULE)
    assert "M-184" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /onboard")


def test_shipped_book_judged_honestly_as_data():
    book = load_onboarding_five()
    ollama = book.detection_for("det-ollama-door")
    assert detection_passes(ollama) is True
    assert detection_gaps(ollama) == ()
    assert plain_lines(ollama) == (
        "Provider: Ollama",
        "Looked for by: local door probe",
        "What the probe found: found")
    anthropic = book.detection_for("det-anthropic-env")
    assert detection_gaps(anthropic) == ("provider",)
    assert detection_passes(anthropic) is False
    assert [d.detection_id for d in passing_detections(book)] == [
        "det-ollama-door", "det-openai-env", "det-aesir-door",
        "det-lmstudio-door"]
    assert total_detections(book) == 6
    assert segment_of(anthropic) == (
        "det-anthropic-env: Anthropic probed by 'environment key "
        "probe' - outcome: 'absent' - detail: 'No Anthropic key "
        "stands in the environment; the probe names the absence "
        "honestly and invents no availability.' - gaps: provider")
    walk = derive_walk(book)
    assert [s.step_id for s in walk.steps] == [
        "step-detect", "step-walk", "step-success", "step-offer",
        "step-configure"]
    assert walk.success_seq == 3
    assert walk.configure_seq == 5


# ---------------------------------------------------------------------
# The held detection: judged whole, its telling derived.
# ---------------------------------------------------------------------

def test_detection_record_round_trips():
    detection = _detection()
    assert validate_detection(detection) is detection
    rebuilt = build_detection(_stored_detection(detection))
    assert rebuilt == detection
    assert rebuilt.item_id == "det-test"
    record = detection_record(detection)
    assert record["type"] == "onboarding_detection"
    assert record["passes"] is True
    assert record["gaps"] == []


def test_detection_refuses_stored_judgements():
    for key in ("passes", "gaps", "segment", "verdict", "walk",
                "in_order"):
        fields = _stored_detection(_detection())
        fields[key] = "stored"
        with pytest.raises(ValueError):
            build_detection(fields)
    fields = _stored_detection(_detection())
    fields["surprise"] = "stored"
    with pytest.raises(ValueError):
        build_detection(fields)


def test_detection_refuses_to_hold_a_key():
    for key in ("api_key", "key", "secret", "token", "password"):
        fields = _stored_detection(_detection())
        fields[key] = "sk-test"
        with pytest.raises(ValueError) as caught:
            build_detection(fields)
        assert "never held" in str(caught.value)


def test_offer_refuses_to_hold_a_key():
    for key in ("api_key", "key", "secret"):
        fields = _offer().to_record()
        fields[key] = "sk-test"
        with pytest.raises(ValueError) as caught:
            build_offer(fields)
        assert "never held" in str(caught.value)
    offer = _offer(decision="ACCEPTED")
    assert validate_offer(offer) is offer
    assert offer.decision == "accepted"
    assert offer_record(offer)["type"] == "onboarding_offer"


def test_detection_vocabularies_are_closed():
    assert _detection(outcome="ABSENT").outcome == "absent"
    with pytest.raises(ValueError):
        _detection(outcome="guessed")
    with pytest.raises(ValueError):
        _detection(probe="a hunch")
    with pytest.raises(ValueError):
        _detection(provider="   ")
    with pytest.raises(ValueError):
        _detection(seq=0)


def test_plain_telling_derives_from_the_detections_own_fields():
    detection = _detection(
        provider="Test Provider", probe="registry probe",
        outcome="absent",
        detail="The registry names it but no door answers.")
    lines = plain_lines(detection)
    assert lines[0] == "Provider: Test Provider"
    assert lines[1] == "Looked for by: registry probe"
    assert lines[2] == "What the probe found: absent"
    assert plain_words(detection) == detection_plain_words(detection)
    assert "Test Provider" in plain_words(detection)
    assert "no door answers" in plain_words(detection)


def test_absent_detection_stands_named_in_its_gaps():
    detection = _detection(outcome="absent")
    assert detection_gaps(detection) == ("provider",)
    assert detection_passes(detection) is False
    text = format_detection(detection)
    assert "stands absent" in text
    found_text = format_detection(_detection())
    assert "stands found" in found_text


def test_view_step_and_offer_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(_stored_view(view)) == view
    record = view_record(view)
    assert record["type"] == "onboarding_view"
    assert record["view_filter"] == "all"
    assert "shows all detections" in view_plain_words(view)
    assert "filter all" in format_view(view)
    with pytest.raises(ValueError):
        _view(view_filter="some")
    step = _step(phase="WALK")
    assert validate_step(step) is step
    assert step.phase == "walk"
    assert build_step(step.to_record()) == step
    assert step_record(step)["type"] == "onboarding_step"
    offer = _offer()
    assert build_offer(offer.to_record()) == offer
    assert "Kista key-keeping for OpenAI" in format_offer(offer)


def test_walk_is_derived_in_held_order_and_stands_in_order():
    steps = [
        _step(step_id="step-d", seq=1, phase="detect"),
        _step(step_id="step-w", seq=2, phase="walk"),
        _step(step_id="step-s", seq=3, phase="success"),
        _step(step_id="step-c", seq=4, phase="configure"),
    ]
    book = _book(steps=steps)
    assert [s.step_id for s in walk_steps(book)] == [
        "step-d", "step-w", "step-s", "step-c"]
    walk = derive_walk(book)
    assert walk.passes() is True
    assert walk.success_seq == 3
    assert walk.configure_seq == 4
    assert walk_record(book)["passes"] is True
    assert "success before" in walk_plain_words(book)
    assert "[success]" in format_walk(book)
    no_success = _book(steps=[_step(step_id="step-d", seq=1)])
    assert derive_walk(no_success).passes() is False


def test_walk_demanding_configuration_first_refuses_by_name():
    steps = [
        _step(step_id="step-c", seq=1, phase="configure"),
        _step(step_id="step-s", seq=2, phase="success"),
    ]
    with pytest.raises(ValueError) as caught:
        _book(steps=steps)
    assert "success before configuration" in str(caught.value)
    fields = _step().to_record()
    fields["config_first"] = True
    with pytest.raises(ValueError) as caught:
        build_step(fields)
    assert "configuration comes first" in str(caught.value)
    raw = {
        "schema": ONBOARDING_FIVE_SCHEMA, "slice": "M-184",
        "guide": {"title": "A test onboarding book"},
        "detections": [], "views": [], "steps": [], "offers": [],
        "panels": [], "requires_configuration": True,
    }
    with pytest.raises(ValueError) as caught:
        build_book(raw)
    assert "configuration comes first" in str(caught.value)


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert isinstance(panel, OnboardingPanel)
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book).rows == panel.rows
    assert build_row(panel.rows[0], book.detections[0]) == panel.rows[0]
    assert validate_row(panel.rows[0], book.detections[0]) == panel.rows[0]
    tampered = dict(panel.to_record())
    tampered["total_shown"] = 99
    with pytest.raises(ValueError):
        build_panel(tampered, book)
    renamed = dict(panel.to_record())
    renamed["panel_id"] = "panel-renamed"
    assert build_panel(renamed, book).panel_id == "panel-renamed"
    record = panel_record(panel, book)
    assert record["type"] == "onboarding_panel"
    assert record["panel_id"] == panel.panel_id


def test_verdict_is_derived_from_the_shown_detections():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert isinstance(verdict, OnboardingVerdict)
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 2
    assert verdict.passing_shown == 1
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    record = verdict_record(verdict, book)
    assert record["type"] == "onboarding_verdict"
    assert "strained" in verdict_plain_words(book)
    assert "strained" in format_verdict(book)


def test_verdict_open_and_shut_edges():
    whole = _book(detections=[_detection()])
    assert derive_verdict(whole).verdict == "open"
    absent_book = _book(detections=[_detection(outcome="absent")])
    assert derive_verdict(absent_book).verdict == "shut"
    none_shown = _book(
        detections=[_detection(outcome="absent")],
        views=[_view(view_filter="found")])
    verdict = derive_verdict(none_shown)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"


def test_shown_and_outcome_readings():
    book = _mixed_book()
    assert [d.detection_id for d in shown_detections(book)] == [
        "det-test", "det-absent"]
    found_view = _view(view_id="view-f", seq=2, view_filter="found")
    book2 = _book(
        detections=[_detection(), _detection(
            detection_id="det-absent", seq=2, provider="Anthropic",
            probe="environment key probe", outcome="absent")],
        views=[_view(), found_view])
    assert [d.detection_id for d in shown_detections(book2, found_view)] == [
        "det-test"]
    assert [d.detection_id for d in detections_for_outcome(
        book2, "absent")] == ["det-absent"]
    assert [d.detection_id for d in passing_detections(book2)] == [
        "det-test"]
    assert total_detections(book2) == 2
    with pytest.raises(ValueError):
        detections_for_outcome(book2, "maybe")


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(detections=[_detection(), _detection(seq=2)])
    with pytest.raises(ValueError):
        _book(detections=[_detection(), _detection(detection_id="det-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_filter="found")])
    with pytest.raises(ValueError):
        _book(steps=[_step(), _step(phase="walk")])
    with pytest.raises(ValueError):
        _book(offers=[_offer(), _offer(provider="Other")])
    fields = {
        "schema": ONBOARDING_FIVE_SCHEMA, "slice": "M-184",
        "guide": {"title": "A test onboarding book"},
        "detections": [_stored_detection(_detection())],
        "views": [_stored_view(_view())], "steps": [], "offers": [],
        "panels": [], "verdict": "open",
    }
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ONBOARDING_FIVE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "onboarding_five.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_onboarding_five_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_detections(book) == 6


def test_registry_holds_detections_and_views_one_by_one():
    registry = OnboardingRegistry()
    assert registry.list_items() == ()
    held = registry.register_detection(_detection())
    assert held.detection_id == "det-test"
    registry.register_view(_view())
    assert [i.item_id if hasattr(i, "item_id") else i.view_id
            for i in registry.list_items()] == [
        "det-test", "view-test"]
    assert registry.get_detection("det-test").provider == "Ollama"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.book().title == "An unheld onboarding book"
    with pytest.raises(ValueError):
        registry.register_detection(_detection(seq=2))
    with pytest.raises(ValueError):
        registry.register_detection(_detection(detection_id="det-two"))
    with pytest.raises(KeyError):
        registry.get_detection("det-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = OnboardingRegistry()
    book = _mixed_book()
    held = registry.register_book(book)
    assert held.title == "A test onboarding book"
    assert len(registry.list_detections()) == 2
    other = _book(detections=[_detection(
        detection_id="det-x", seq=9, provider="Other")],
        views=[_view(view_id="view-x", seq=9)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_records_are_session_news():
    book = _mixed_book()
    record = book_record(book)
    assert record["type"] == "onboarding_book"
    assert record["title"] == "A test onboarding book"
    assert len(record["detections"]) == 2
    panel = derive_panel(book)
    assert panel_record(panel, book)["rows"][0]["item_id"] == "det-test"
    assert verdict_record(derive_verdict(book), book)["verdict"] == (
        "strained")


def test_plain_words_and_formatters():
    book = _mixed_book()
    assert "Ollama probed by" in format_book(book)
    assert "det-absent" in format_book(book, "absent")
    assert "det-test" not in format_book(book, "absent")
    assert "Onboarding panel under view view-test" in format_panel(book)
    assert panel_plain_words(book).startswith(
        "The onboarding book holds 2 detections")
    screen = format_onboarding_five_screen(book)
    assert "Onboarding in Five Minutes (M-184)" in screen
    assert PLAIN_EXPLANATION in screen
    detection_text = format_detection(book.detections[0])
    assert "Provider: Ollama" in detection_text
    assert "What the probe found: found" in detection_text


def test_parse_args_inspect_and_loader_roads():
    assert parse_onboarding_args("") == ("show", None)
    assert parse_onboarding_args("show") == ("show", None)
    assert parse_onboarding_args(None) == ("show", None)
    assert parse_onboarding_args("detection det-test") == (
        "detection", "det-test")
    assert parse_onboarding_args("walk") == ("walk", None)
    assert parse_onboarding_args("offer offer-test") == (
        "offer", "offer-test")
    assert parse_onboarding_args("view view-test") == (
        "view", "view-test")
    assert parse_onboarding_args("outcome absent") == (
        "outcome", "absent")
    assert parse_onboarding_args("panel") == ("panel", None)
    assert parse_onboarding_args("verdict") == ("verdict", None)
    for bad in ("dance", "detection", "panel now", "walk now",
                "outcome a b"):
        with pytest.raises(ValueError):
            parse_onboarding_args(bad)
    detection = _detection()
    assert inspect_onboarding_source(detection) == {
        "kind": "detection", "detection_id": "det-test"}
    assert inspect_onboarding_source(
        _stored_detection(detection))["kind"] == "detection"
    assert inspect_onboarding_source(
        _stored_view(_view()))["kind"] == "view"
    assert inspect_onboarding_source(
        _step().to_record())["kind"] == "step"
    assert inspect_onboarding_source(
        _offer().to_record())["kind"] == "offer"
    assert inspect_onboarding_source(42)["kind"] == "unknown"
    book = load_onboarding_five({
        "schema": ONBOARDING_FIVE_SCHEMA, "slice": "M-184",
        "guide": {"title": "A judged book"},
        "detections": [_stored_detection(_detection())],
        "views": [_stored_view(_view())], "steps": [], "offers": [],
        "panels": []})
    assert isinstance(book, OnboardingBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_onboarding_five({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_onboarding_five({"slice": "M-999"})
    built = build_detection(
        detection_id="det-kw", seq=3, provider="Kw Provider",
        probe="registry probe", outcome="found",
        detail="Built by fields.", recorded_on=ON, actor=BY,
        source="test source", origin_session="session-test")
    assert built.detection_id == "det-kw"
    assert detection_passes(built) is True


# ---------------------------------------------------------------------
# M-184 agent layer: the agent holds an onboarding
# book for the session, detections and views are
# published as session news through the checkpoint
# road (journal first, deduped per shape), the
# panel and verdict are derived at call time from
# the whole book under a view, never held, and the
# walk is derived at call time from the book's held
# steps under the ordering rule - success before
# configuration, always. This layer calls no model,
# detects nothing live, keeps no key, runs no task,
# configures nothing and persists nothing beyond
# the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _onboarding_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_onboarding_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ONBOARDING_FIVE_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "onboarding_five.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestOnboardingAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.onboarding_five_status()
        assert status["detections"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["onboarding"]["title"] == EXAMPLE_TITLE
        assert len(status["onboarding"]["detections"]) == 6
        assert len(status["onboarding"]["views"]) == 2
        assert len(status["onboarding"]["steps"]) == 5
        assert len(status["onboarding"]["offers"]) == 1
        assert status["panel"]["total_items"] == 6
        assert status["panel"]["total_shown"] == 6
        assert status["panels"][0]["panel_id"] == "panel-m183-boundary"
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["passing_shown"] == 4
        assert status["walk"]["passes"] is True
        assert "success before configuration" in status["rule"]
        assert "OpenRouter" in status["plain_words"]
        assert "Onboarding in Five Minutes (M-184)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._onboarding_five_registry()
        assert agent._onboarding_five_registry() is first
        assert agent._onboarding_five_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.onboarding_five_status()
        assert agent.get_onboarding_detection(
            "det-ollama-door").provider == "Ollama"
        assert agent.get_onboarding_view("view-all").view_filter == "all"
        assert agent.get_onboarding_offer(
            "offer-kista-openai").decision == "declined"
        assert [d.detection_id for d in agent.onboarding_five_with_outcome(
            "absent")] == ["det-anthropic-env", "det-openrouter-registry"]
        assert [d.detection_id for d in agent.onboarding_five_passing()] == [
            "det-ollama-door", "det-openai-env", "det-aesir-door",
            "det-lmstudio-door"]
        agent.onboarding_five_panel()
        agent.onboarding_five_verdict()
        agent.onboarding_five_walk()
        agent.report_onboarding()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("onboarding")] == []
        with pytest.raises(KeyError):
            agent.get_onboarding_detection("det-nope")
        with pytest.raises(KeyError):
            agent.get_onboarding_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_onboarding_offer("offer-nope")
        with pytest.raises(ValueError):
            agent.onboarding_five_with_outcome("maybe")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_onboarding_detection(_detection())
        status = agent.onboarding_five_status()
        assert [d["detection_id"] for d in status["detections"]] == [
            "det-test"]
        assert status["book"]["title"] == "An unheld onboarding book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert status["walk"]["passes"] is False
        assert "det-test" in status["screen"]

    def test_held_detection_never_falls_back_to_the_example(
            self, agent):
        agent.register_onboarding_detection(_detection())
        with pytest.raises(KeyError):
            agent.get_onboarding_detection("det-ollama-door")
        with pytest.raises(KeyError):
            agent.get_onboarding_view("view-all")
        detection = agent.get_onboarding_detection("det-test")
        assert detection.provider == "Ollama"
        assert agent.onboarding_five_book().title == (
            "An unheld onboarding book")

    def test_walk_and_offer_stand_in_the_example(self, agent):
        walk = agent.onboarding_five_walk()
        assert [s.phase for s in walk.steps] == [
            "detect", "walk", "success", "offer", "configure"]
        assert walk.passes() is True
        offer = agent.get_onboarding_offer("offer-kista-openai")
        assert offer.provider == "OpenAI"
        assert offer.decision == "declined"


class TestOnboardingAgentHolding:
    def test_register_detection_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_onboarding_detection(_detection())
        assert result["detection"]["detection_id"] == "det-test"
        assert result["record_news"]["type"] == "onboarding_detection"
        assert "det-test" in result["screen"]
        events = _onboarding_events(
            store, session_id, "onboarding_detection")
        assert len(events) == 1
        agent.close()

    def test_duplicate_detection_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_onboarding_detection(_detection())
        with pytest.raises(ValueError):
            agent.register_onboarding_detection(_detection(seq=9))
        events = _onboarding_events(
            store, session_id, "onboarding_detection")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_onboarding_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_onboarding_events(
            store, session_id, "onboarding_view")) == 1
        agent.close()

    def test_view_road_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_onboarding_detection(_detection())
        result = agent.view_onboarding("found")
        assert result["view"]["view_filter"] == "found"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "onboarding_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_onboarding_events(
            store, session_id, "onboarding_view")) == 1
        assert len(_onboarding_events(
            store, session_id, "onboarding_panel")) == 1
        assert len(_onboarding_events(
            store, session_id, "onboarding_verdict")) == 1
        agent.close()

    def test_view_road_over_an_unshown_filter_is_shut(self, agent):
        agent.register_onboarding_detection(_detection(outcome="absent"))
        result = agent.view_onboarding("found")
        assert result["verdict_record"]["verdict"] == "shut"
        assert result["verdict_record"]["total_shown"] == 0

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_onboarding_book(
            _book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "onboarding_detection", "onboarding_view"]
        assert len(_onboarding_events(
            store, session_id, "onboarding_detection")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_onboarding_book()
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "onboarding_panel"
        assert result["walk_record"]["passes"] is True
        with pytest.raises(ValueError):
            agent.record_onboarding_book()
        assert len(_onboarding_events(
            store, session_id, "onboarding_detection")) == 6
        assert len(_onboarding_events(
            store, session_id, "onboarding_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_onboarding_book_file(tmp_path)
        book = load_onboarding_five_file(path)
        result = agent.record_onboarding_book(book)
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_onboarding()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert "det-ollama-door" in report["book_text"]
        assert "[success]" in report["walk_text"]
        assert "offer-kista-openai" in report["walk_text"]
        agent.register_onboarding_detection(_detection())
        report = agent.report_onboarding()
        assert report["book"]["title"] == "An unheld onboarding book"
        assert report["panel"] is None
        assert report["verdict"] is None


class TestOnboardingTerminalSurface:
    def test_show_detection_walk_offer_view_outcome_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/onboard")
        assert "Onboarding in Five Minutes (M-184)" in text
        _, _, text = _slash(agent, "/onboard detection det-ollama-door")
        assert "Provider: Ollama" in text
        _, _, text = _slash(agent, "/onboard walk")
        assert "[success]" in text
        _, _, text = _slash(agent, "/onboard offer offer-kista-openai")
        assert "declined" in text
        _, _, text = _slash(agent, "/onboard view view-all")
        assert "filter all" in text
        _, _, text = _slash(agent, "/onboard outcome absent")
        assert "det-anthropic-env" in text
        assert "det-ollama-door" not in text
        _, _, text = _slash(agent, "/onboard panel")
        assert "Onboarding panel under view view-all" in text
        _, _, text = _slash(agent, "/onboard verdict")
        assert "strained" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/onboard [show|detection <detection-id>"
                "|walk|offer <offer-id>|view <view-id>"
                "|outcome <outcome>|panel|verdict]") in text
        _, _, text = _slash(agent, "/onboard dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/onboard detection det-nope")
        assert "no detection named" in text


@pytest.fixture()
def onboard_handler(agent, monkeypatch):
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


def _onboard_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestOnboardingCommand:
    def test_show_is_default(self, onboard_handler, agent):
        onboard_handler._handle_onboard("")
        assert "Onboarding in Five Minutes (M-184)" in (
            _onboard_published_text(onboard_handler))

    def test_detection_walk_offer_view_outcome_panel_verdict(
            self, onboard_handler, agent):
        onboard_handler._handle_onboard("detection det-ollama-door")
        assert "Provider: Ollama" in _onboard_published_text(
            onboard_handler)
        onboard_handler._handle_onboard("walk")
        assert "[success]" in _onboard_published_text(onboard_handler)
        onboard_handler._handle_onboard("offer offer-kista-openai")
        assert "declined" in _onboard_published_text(onboard_handler)
        onboard_handler._handle_onboard("view view-all")
        assert "filter all" in _onboard_published_text(onboard_handler)
        onboard_handler._handle_onboard("outcome absent")
        assert "det-anthropic-env" in _onboard_published_text(
            onboard_handler)
        onboard_handler._handle_onboard("panel")
        assert "Onboarding panel under view" in _onboard_published_text(
            onboard_handler)
        onboard_handler._handle_onboard("verdict")
        assert "strained" in _onboard_published_text(onboard_handler)

    def test_bad_grammar_is_published(
            self, onboard_handler, agent):
        onboard_handler._handle_onboard("dance party")
        assert USAGE in _onboard_published_text(onboard_handler)
        onboard_handler._handle_onboard("detection det-nope")
        assert "no detection named" in _onboard_published_text(
            onboard_handler)


class TestChatScreenRoutingOnboarding:
    def test_onboard_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/onboard panel", _FakeLog())
        assert calls == [("/onboard", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/onboard[/green] - show onboarding in five minutes (M-184)" in (
            text)
        assert ('"/onboard": "Usage: /onboard | '
                '/onboard detection <detection-id>') in text


class TestOnboardingDerivedRoads:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.onboarding_five_panel()
        assert panel.total_shown == 6
        assert panel.panel_id == "panel-view-all"
        verdict = agent.onboarding_five_verdict()
        assert verdict.verdict == "strained"
        found = agent.onboarding_five_verdict("view-found")
        assert found.verdict == "open"
        assert found.passing_shown == 4
        agent.register_onboarding_detection(_detection())
        with pytest.raises(ValueError):
            agent.onboarding_five_panel()
        with pytest.raises(ValueError):
            agent.onboarding_five_verdict()

    def test_absent_detection_stands_named_in_its_gaps(self, agent):
        detection = agent.get_onboarding_detection("det-anthropic-env")
        assert detection_gaps(detection) == ("provider",)
        assert detection_passes(detection) is False
        status = agent.onboarding_five_status()
        assert status["verdict"]["passing_shown"] == 4
        assert status["walk"]["steps"][2]["phase"] == "success"
        assert status["walk"]["steps"][4]["phase"] == "configure"
