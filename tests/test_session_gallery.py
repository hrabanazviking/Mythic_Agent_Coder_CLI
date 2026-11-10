"""M-189 Session Gallery - pure-layer tests.

TIER: integration

The pure layer is the session gallery, held as
data: one record per past session, held whole
as a browsable card - under its task, its
outcome in the closed vocabulary, its cost and
its duration held honestly (unknown stays
empty, never invented), the resume road that
reaches it, named as data, and its detail - the
resume, fork and export roads held as data
beside them, each naming its session, its
action and its target, and the gallery index
derived at call time from the held cards alone,
never stored where it could drift. A card
naming no resume road stands unresumable, named
in its gaps; two cards standing for one session
id refuse by name, and one action record stands
per session road. A record claiming a session
actually resumed, forked or exported refuses by
name, and a stored index or verdict refuses by
name. The panel is derived for one held view
and the verdict is derived for the whole book
under one view. The shipped example book is
held in a data file, and a loader reads a book
from any file. This layer resumes no session,
forks nothing, exports nothing and opens no
network: it holds the gallery as data and
tells it.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.session_gallery import (
    OUTCOMES,
    EXAMPLE_ROAD,
    ACTIONS,
    INDEX_ACTION,
    SESSION_GALLERY_RESOURCE,
    SESSION_GALLERY_SCHEMA,
    SESSION_GALLERY_SLICE,
    GALLERY_RULE,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    ROAD_WORDS,
    SessionCard,
    ActionRecord,
    GalleryBook,
    GalleryPanel,
    SessionGalleryRegistry,
    GalleryVerdict,
    GalleryView,
    book_record,
    build_book,
    build_card,
    build_action,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    derive_index,
    derive_panel,
    derive_verdict,
    first_action,
    format_book,
    format_card,
    format_index,
    format_action,
    format_gallery_screen,
    format_panel,
    format_road,
    format_verdict,
    format_view,
    card_for_road,
    card_gaps,
    card_passes,
    card_plain_words,
    card_record,
    cards_for_outcome,
    index_plain_words,
    index_record,
    inspect_gallery_source,
    action_for_session,
    action_plain_words,
    action_record,
    load_session_gallery,
    load_session_gallery_file,
    normalize_outcome,
    normalize_action,
    normalize_view_filter,
    panel_plain_words,
    panel_record,
    parse_gallery_args,
    passing_cards,
    plain_lines,
    plain_words,
    shown_cards,
    total_cards,
    validate_book,
    validate_card,
    validate_action,
    validate_panel,
    validate_row,
    validate_verdict,
    validate_view,
    verdict_plain_words,
    verdict_record,
    view_plain_words,
    view_record,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]
ON = "2026-11-09"
BY = "the coordinator"
EXAMPLE_TITLE = "Session gallery at the M-188 slice boundary"


def _card(**overrides):
    fields = {
        "card_id": "session-test",
        "seq": 1,
        "task": "A test session",
        "outcome": "completed",
        "cost": "$0.10",
        "duration": "12 minutes",
        "road": "resume",
        "detail": "A test session held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_card(fields)


def _stored_card(card):
    return card.to_record()


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


def _action(**overrides):
    fields = {
        "action_id": "action-test",
        "seq": 1,
        "session_id": "session-test",
        "action": "resume",
        "target": "a new live session",
        "title": "A test action",
        "detail": "A test action held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_action(fields)


def _book(cards=None, views=None, actions=None, **overrides):
    fields = {
        "schema": SESSION_GALLERY_SCHEMA,
        "slice": "M-189",
        "gallery": {"title": "A test gallery book"},
        "cards": [_stored_card(item) for item in (
            cards if cards is not None else [_card()])],
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "actions": [item.to_record() for item in (actions or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(cards=[
        _card(),
        _card(card_id="session-stopped", seq=2,
                 task="A stopped session", outcome="stopped",
                 cost="", duration="", road=""),
    ])


# ---------------------------------------------------------------------
# The shipped example book, the roadmap and the charter.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_session_gallery()
    assert book.title == EXAMPLE_TITLE
    assert book.card_ids() == (
        "session-fix-login-redirect", "session-draft-costs-face",
        "session-repair-flaky-gate", "session-write-gallery-guide",
        "session-abandoned-sweep", "session-bank-m188-wave")
    assert [v.view_id for v in book.views] == [
        "view-all", "view-resumable"]
    assert [m.session_id for m in book.actions] == [
        "session-fix-login-redirect",
        "session-write-gallery-guide"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m188-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.card_ids())
    derived = derive_panel(book, "view-all")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.standing: c.items for c in panel.road_counts} == {
        "resumable": 5, "unresumable": 1}
    assert derive_verdict(book, "view-all").verdict == "strained"
    assert derive_verdict(book, "view-all").passing_shown == 5
    assert derive_verdict(book, "view-resumable").verdict == "open"
    assert derive_verdict(book, "view-resumable").passing_shown == 5
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / SESSION_GALLERY_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == SESSION_GALLERY_SCHEMA
    assert raw["slice"] == "M-189"
    assert "verdict" not in raw
    assert "gallery_index" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-189")]
    assert slice_.title == "Session gallery"
    assert slice_.part == 8
    assert "past sessions as browsable cards" in slice_.summary
    assert "resume/fork/export" in slice_.summary
    assert "history as a library" in slice_.summary
    assert SESSION_GALLERY_SLICE == "M-189"


def test_charter_does_not_name_m189():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert owners.count("M-187") == 1
    assert "M-189" not in owners


def test_closed_vocabularies():
    assert ROAD_WORDS == ("resumable", "unresumable")
    assert OUTCOMES == ("completed", "failed", "stopped", "abandoned")
    assert ACTIONS == ("resume", "fork", "export")
    assert VIEW_FILTERS == ("all", "resumable", "unresumable")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert INDEX_ACTION == "index"
    assert EXAMPLE_ROAD == "resume"
    assert normalize_outcome("COMPLETED") == "completed"
    assert normalize_action("FORK") == "fork"
    assert normalize_view_filter("ALL") == "all"
    with pytest.raises(ValueError):
        normalize_outcome("the void")
    with pytest.raises(ValueError):
        normalize_action("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    assert "held as data alone" in GALLERY_RULE
    assert "resumes no session" in GALLERY_RULE
    assert "M-189" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /gallery")


def test_shipped_book_judged_honestly_as_data():
    book = load_session_gallery()
    login = book.card_for("session-fix-login-redirect")
    assert card_passes(login) is True
    assert card_gaps(login) == ()
    assert plain_lines(login) == (
        "Card: Fix the login redirect",
        "Outcome: completed",
        "Cost: $0.42",
        "Duration: 18 minutes",
        "Road: resume")
    costs = book.card_for("session-draft-costs-face")
    assert costs.cost == ""
    assert "Cost: unknown" in plain_lines(costs)
    flaky = book.card_for("session-repair-flaky-gate")
    assert flaky.duration == ""
    assert "Duration: unknown" in plain_lines(flaky)
    sweep = book.card_for("session-abandoned-sweep")
    assert card_gaps(sweep) == ("no resume road",)
    assert card_passes(sweep) is False
    assert [g.card_id for g in passing_cards(book)] == [
        "session-fix-login-redirect", "session-draft-costs-face",
        "session-repair-flaky-gate", "session-write-gallery-guide",
        "session-bank-m188-wave"]
    assert total_cards(book) == 6
    index = derive_index(book)
    assert [e.road for e in index.entries] == [
        "resume", "resume from checkpoint", "fork and resume",
        "resume", "resume from checkpoint"]
    assert index.gaps == ("session-abandoned-sweep",)
    assert card_for_road(book, "resume").card_id == (
        "session-fix-login-redirect")
    assert card_for_road(book, "triple resume") is None
    assert first_action(book).action_id == "action-resume-login"
    assert action_for_session(
        book, "session-fix-login-redirect", "resume").action_id == (
            "action-resume-login")
    assert action_for_session(book, "session-nope") is None


# ---------------------------------------------------------------------
# The held card: judged whole, its telling derived.
# ---------------------------------------------------------------------


def test_card_record_round_trips():
    card = _card()
    assert validate_card(card) is card
    rebuilt = build_card(_stored_card(card))
    assert rebuilt == card
    assert rebuilt.item_id == "session-test"
    assert rebuilt.road == "resume"
    record = card_record(card)
    assert record["type"] == "session_card"
    assert record["passes"] is True
    assert record["gaps"] == []


def test_card_refuses_stored_judgements():
    for key in ("standing", "resumable", "gaps", "segment", "verdict",
                "index", "entries", "coverage"):
        fields = _stored_card(_card())
        fields[key] = "stored"
        with pytest.raises(ValueError):
            build_card(fields)
    fields = _stored_card(_card())
    fields["surprise"] = "stored"
    with pytest.raises(ValueError):
        build_card(fields)


def test_card_refuses_a_live_session_claim():
    for key in ("resumes_session", "resumed_session", "forks_session",
                "exported_session", "opens_session"):
        fields = _stored_card(_card())
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_card(fields)
        assert "held as data alone" in str(caught.value)
    for key in ("exports_session", "resumed_session"):
        fields = _action().to_record()
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_action(fields)
        assert "held as data alone" in str(caught.value)
    record = _action(session_id="session-test")
    assert validate_action(record) is record
    assert record.session_id == "session-test"
    assert action_record(record)["type"] == "gallery_action"


def test_card_vocabularies_are_closed():
    assert _card(outcome="COMPLETED").outcome == "completed"
    assert _card(cost="").cost == ""
    assert _card(duration=None).duration == ""
    with pytest.raises(ValueError):
        _card(outcome="a hunch")
    with pytest.raises(ValueError):
        _card(task="   ")
    with pytest.raises(ValueError):
        _card(seq=0)
    with pytest.raises(ValueError):
        _card(road=5)
    with pytest.raises(ValueError):
        _card(cost=5)
    with pytest.raises(ValueError):
        _card(duration=5)
    with pytest.raises(ValueError):
        _card(detail="   ")


def test_plain_telling_derives_from_the_cards_own_fields():
    card = _card(
        task="Test Session", outcome="failed", cost="", duration="",
        road="", detail="The road waits on a held card.")
    lines = plain_lines(card)
    assert lines[0] == "Card: Test Session"
    assert lines[1] == "Outcome: failed"
    assert lines[2] == "Cost: unknown"
    assert lines[3] == "Duration: unknown"
    assert lines[4] == "Road: none"
    assert plain_words(card) == card_plain_words(card)
    assert "Test Session" in plain_words(card)
    assert "held card" in plain_words(card)


def test_unresumable_card_stands_named_in_its_gaps():
    card = _card(road="")
    assert card_gaps(card) == ("no resume road",)
    assert card_passes(card) is False
    text = format_card(card)
    assert "stands unresumable" in text
    current_text = format_card(_card())
    assert "stands resumable" in current_text


def test_view_and_action_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(_stored_view(view)) == view
    record = view_record(view)
    assert record["type"] == "gallery_view"
    assert record["view_filter"] == "all"
    assert "shows all cards" in view_plain_words(view)
    assert "filter all" in format_view(view)
    with pytest.raises(ValueError):
        _view(view_filter="some")
    action = _action()
    assert build_action(action.to_record()) == action
    assert "Session action resume session-test" in format_action(action)
    assert "resumes no session" in format_action(action)
    assert "toward a new live session" in action_plain_words(action)
    with pytest.raises(ValueError):
        _action(action="dance")


# ---------------------------------------------------------------------
# The index and the action roads: derived at call time, never held.
# ---------------------------------------------------------------------


def test_index_is_derived_from_the_held_cards_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.card_id for e in index.entries] == ["session-test"]
    assert index.entries[0].road == "resume"
    assert index.gaps == ("session-stopped",)
    assert index_record(index)["type"] == "gallery_index"
    assert index_record(book)["gaps"] == ["session-stopped"]
    assert "1 roads" in index_plain_words(book)
    text = format_index(book)
    assert "Card index" in text
    assert "resume - A test session (session-test)" in text
    assert "session-stopped" in text
    assert "resumes no session" in text


def test_road_reaches_its_card_and_an_unheld_road_reaches_nothing():
    book = _mixed_book()
    assert card_for_road(book, "resume").card_id == "session-test"
    assert card_for_road(book, "triple resume") is None
    assert card_for_road(book, "") is None
    assert "A test session" in format_road(book, "resume")
    assert "reaches nothing in this book" in format_road(
        book, "triple resume")


def test_first_action_is_held_as_data():
    book = _book(actions=[_action(), _action(
        action_id="action-two", seq=2, session_id="session-other",
        action="export", title="The second action")])
    assert first_action(book).action_id == "action-test"
    assert action_for_session(book, "session-other").action_id == (
        "action-two")
    assert action_for_session(
        book, "session-other", "export").action_id == "action-two"
    assert action_for_session(book, "session-other", "fork") is None
    bare = _book()
    assert first_action(bare) is None
    assert action_for_session(bare, "session-other") is None
    text = format_action(first_action(book))
    assert "held as data alone" in text
    assert "exports nothing" in text


def test_action_roads_stand_held_whole():
    action = _action(
        session_id="session-x", action="fork",
        target="a branched session")
    assert action.action == "fork"
    rebuilt = build_action(action.to_record())
    assert rebuilt == action
    assert rebuilt.session_id == "session-x"
    assert rebuilt.target == "a branched session"
    with pytest.raises(ValueError):
        _action(session_id="   ")
    with pytest.raises(ValueError):
        _action(target="   ")
    with pytest.raises(ValueError):
        _action(action="teleport")


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert isinstance(panel, GalleryPanel)
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book).rows == panel.rows
    assert build_row(panel.rows[0], book.cards[0]) == panel.rows[0]
    assert validate_row(panel.rows[0], book.cards[0]) == panel.rows[0]
    tampered = dict(panel.to_record())
    tampered["total_shown"] = 99
    with pytest.raises(ValueError):
        build_panel(tampered, book)
    renamed = dict(panel.to_record())
    renamed["panel_id"] = "panel-renamed"
    assert build_panel(renamed, book).panel_id == "panel-renamed"
    record = panel_record(panel, book)
    assert record["type"] == "gallery_panel"
    assert record["panel_id"] == panel.panel_id


def test_verdict_is_derived_from_the_shown_cards():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert isinstance(verdict, GalleryVerdict)
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 2
    assert verdict.passing_shown == 1
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    record = verdict_record(verdict, book)
    assert record["type"] == "gallery_verdict"
    assert "strained" in verdict_plain_words(book)
    assert "strained" in format_verdict(book)


def test_verdict_open_and_shut_edges():
    whole = _book(cards=[_card()])
    assert derive_verdict(whole).verdict == "open"
    absent_book = _book(cards=[_card(road="")])
    assert derive_verdict(absent_book).verdict == "shut"
    none_shown = _book(
        cards=[_card(road="")],
        views=[_view(view_filter="resumable")])
    verdict = derive_verdict(none_shown)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"


def test_shown_and_outcome_readings():
    book = _mixed_book()
    assert [g.card_id for g in shown_cards(book)] == [
        "session-test", "session-stopped"]
    resumable_view = _view(
        view_id="view-r", seq=2, view_filter="resumable")
    book2 = _book(
        cards=[_card(), _card(
            card_id="session-stopped", seq=2, task="A stopped session",
            outcome="stopped", cost="", duration="", road="")],
        views=[_view(), resumable_view])
    assert [g.card_id for g in shown_cards(book2, resumable_view)] == [
        "session-test"]
    assert [g.card_id for g in cards_for_outcome(book2, "stopped")] == [
        "session-stopped"]
    assert [g.card_id for g in passing_cards(book2)] == [
        "session-test"]
    assert total_cards(book2) == 2
    with pytest.raises(ValueError):
        cards_for_outcome(book2, "the void")


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(cards=[_card(), _card(seq=2)])
    with pytest.raises(ValueError):
        _book(cards=[_card(), _card(card_id="session-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_filter="resumable")])
    with pytest.raises(ValueError) as caught:
        _book(actions=[_action(), _action(action_id="action-two", seq=2)])
    assert "one action stands per session road" in str(caught.value)
    fields = {
        "schema": SESSION_GALLERY_SCHEMA, "slice": "M-189",
        "gallery": {"title": "A test gallery book"},
        "cards": [_stored_card(_card())],
        "views": [_stored_view(_view())], "actions": [],
        "panels": [], "verdict": "open",
    }
    with pytest.raises(ValueError):
        build_book(fields)
    del fields["verdict"]
    fields["gallery_index"] = "stored"
    with pytest.raises(ValueError):
        build_book(fields)
    raw = {
        "schema": SESSION_GALLERY_SCHEMA, "slice": "M-189",
        "gallery": {"title": "A test gallery book"},
        "cards": [], "views": [], "actions": [], "panels": [],
        "resumes_session": True,
    }
    with pytest.raises(ValueError) as caught:
        build_book(raw)
    assert "held as data alone" in str(caught.value)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / SESSION_GALLERY_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "session_gallery.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_session_gallery_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_cards(book) == 6


def test_registry_holds_cards_and_views_one_by_one():
    registry = SessionGalleryRegistry()
    assert registry.list_items() == ()
    held = registry.register_card(_card())
    assert held.card_id == "session-test"
    registry.register_view(_view())
    assert [i.item_id if hasattr(i, "item_id") else i.view_id
            for i in registry.list_items()] == ["session-test", "view-test"]
    assert registry.get_card("session-test").task == "A test session"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.book().title == "An unheld gallery book"
    with pytest.raises(ValueError):
        registry.register_card(_card(seq=2))
    with pytest.raises(ValueError):
        registry.register_card(_card(card_id="session-two"))
    with pytest.raises(KeyError):
        registry.get_card("session-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = SessionGalleryRegistry()
    book = _mixed_book()
    held = registry.register_book(book)
    assert held.title == "A test gallery book"
    assert len(registry.list_cards()) == 2
    other = _book(cards=[_card(
        card_id="session-x", seq=9, task="Other", road="resume")],
        views=[_view(view_id="view-x", seq=9)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_plain_words_and_formatters():
    book = _mixed_book()
    assert "outcome: 'completed'" in format_book(book)
    assert "session-stopped" in format_book(book, "stopped")
    assert "session-test" not in format_book(book, "stopped")
    assert "Gallery panel under view view-test" in format_panel(book)
    assert panel_plain_words(book).startswith(
        "The gallery book holds 2 cards")
    screen = format_gallery_screen(book)
    assert "Session Gallery (M-189)" in screen
    assert PLAIN_EXPLANATION in screen
    assert "session-abandoned-sweep" not in screen
    assert "session-stopped" in screen
    record = book_record(book)
    assert record["type"] == "gallery_book"
    assert record["title"] == "A test gallery book"
    assert len(record["cards"]) == 2
    panel = derive_panel(book)
    assert panel_record(panel, book)["rows"][0]["item_id"] == "session-test"
    assert verdict_record(derive_verdict(book), book)["verdict"] == (
        "strained")
    card_text = format_card(book.cards[0])
    assert "Card: A test session" in card_text
    assert "Road: resume" in card_text


def test_parse_args_inspect_and_loader_roads():
    assert parse_gallery_args("") == ("show", None)
    assert parse_gallery_args("show") == ("show", None)
    assert parse_gallery_args(None) == ("show", None)
    assert parse_gallery_args("card session-test") == (
        "card", "session-test")
    assert parse_gallery_args("road resume from checkpoint") == (
        "road", "resume from checkpoint")
    assert parse_gallery_args("outcome completed") == (
        "outcome", "completed")
    assert parse_gallery_args("view view-test") == ("view", "view-test")
    assert parse_gallery_args("action action-test") == (
        "action", "action-test")
    assert parse_gallery_args("index") == ("index", None)
    assert parse_gallery_args("panel") == ("panel", None)
    assert parse_gallery_args("verdict") == ("verdict", None)
    for bad in ("dance", "card", "road", "outcome", "index now",
                "action a b"):
        with pytest.raises(ValueError):
            parse_gallery_args(bad)
    card = _card()
    assert inspect_gallery_source(card) == {
        "kind": "card", "card_id": "session-test"}
    assert inspect_gallery_source(_stored_card(card))["kind"] == (
        "card")
    assert inspect_gallery_source(_stored_view(_view()))["kind"] == (
        "view")
    assert inspect_gallery_source(_action().to_record())["kind"] == (
        "action")
    assert inspect_gallery_source(42)["kind"] == "unknown"
    book = load_session_gallery({
        "schema": SESSION_GALLERY_SCHEMA, "slice": "M-189",
        "gallery": {"title": "A judged book"},
        "cards": [_stored_card(_card())],
        "views": [_stored_view(_view())], "actions": [], "panels": []})
    assert isinstance(book, GalleryBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_session_gallery({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_session_gallery({"slice": "M-999"})
    built = build_card(
        card_id="session-kw", seq=3, task="Kw Session",
        outcome="completed", cost="$0.01", duration="1 minute",
        road="resume", detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="session-test")
    assert built.card_id == "session-kw"
    assert card_passes(built) is True
