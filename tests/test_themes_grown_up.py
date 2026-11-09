"""M-179 Themes Grown Up - pure-layer tests.

TIER: integration

The pure layer is the theme, held as data: one
named theme with its mode (full colour, high
contrast or no colour), its colours role by role
in the shipped role order, the non-colour cue
each state it names carries, and its declared
accent and ornament shares, with its provenance
whole (the day it was recorded, who recorded it,
its source and the session it was recorded in).
Every judgement - the ladder count, the budget
word, whether colour stands alone, and what the
theme loses when colour falls away - is derived
from the theme's own colours, cues and shares,
never stored, never written by hand. A share that
is not measured stands honestly unknown. A view
is held as its own record, the one mode it looks
at or every mode at once. The panel is derived
for one held view and the verdict is derived for
the whole book under one view. The shipped
example book is held in a data file, and a loader
reads a book from any file. No row of the M-171
charter names M-179, so the slice is built to the
roadmap words alone, as M-177 was. Nothing here
repaints a live UI, applies a theme live, renders
a live UI, measures a running screen, calls a
model or persists anything: a theme held here is
a finding, never the live face of the app.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.themes_grown_up import (
    ACCENT_MAX_PERCENT,
    ACCENT_MIN_PERCENT,
    BUDGET_WORDS,
    MIN_LADDER_RUNGS,
    MIN_VALUE_GAP,
    MODES,
    ORNAMENT_MAX_PERCENT,
    ORNAMENT_MIN_PERCENT,
    PLAIN_EXPLANATION,
    ROLES,
    STATE_ROLES,
    SURFACE_ROLES,
    THEMES_GROWN_UP_RESOURCE,
    THEMES_GROWN_UP_SCHEMA,
    THEMES_GROWN_UP_SLICE,
    USAGE,
    VERDICT_WORDS,
    ThemeBook,
    ThemeModeCount,
    ThemePanel,
    ThemePanelRow,
    ThemeProfile,
    ThemeRegistry,
    ThemeVerdict,
    ThemeView,
    book_record,
    budget_word,
    build_book,
    build_panel,
    build_row,
    build_theme,
    build_verdict,
    build_view,
    colliding_pairs,
    colour_not_only_signal,
    colour_value,
    cued_states,
    derive_panel,
    derive_verdict,
    format_book,
    format_panel,
    format_theme,
    format_themes_grown_up_screen,
    format_verdict,
    format_view,
    inspect_theme_source,
    ladder_count,
    ladder_holds,
    load_themes_grown_up,
    load_themes_grown_up_file,
    loses_nothing,
    lost_labels,
    measured_theme,
    missing_roles,
    normalize_mode,
    normalize_mode_filter,
    normalize_role,
    panel_plain_words,
    panel_record,
    parse_themes_grown_up_args,
    passing_themes,
    plain_words,
    segment_of,
    shown_themes,
    theme_passes,
    theme_record,
    themes_for_mode,
    total_themes,
    unmeasured_theme,
    validate_panel,
    validate_row,
    validate_theme,
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

EXAMPLE_TITLE = "Themes at the M-178 slice boundary"

BY = "the coordinator"
ON = "2026-11-09"

PALETTE = {
    "background": "#000000", "surface": "#262626",
    "primary": "#ffcc00", "secondary": "#33ccff",
    "accent": "#ff6600", "text": "#ffffff",
    "muted": "#9a9a9a", "success": "#00cc44",
    "warning": "#ff8800", "error": "#ff2244"}

CUES = {
    "success": "check mark and the word OK",
    "warning": "triangle and the word Caution",
    "error": "cross and the word Stop"}


def _theme(**overrides):
    fields = {
        "theme_id": "theme-test",
        "name": "test_theme",
        "mode": "full_colour",
        "colours": dict(PALETTE),
        "signals": dict(CUES),
        "accent_percent": 8,
        "ornament_percent": 3,
        "detail": "A theme held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_theme(fields)


def _stored_theme(theme):
    stored = theme.to_record()
    for key in ("type", "slice", "ladder_count", "budget",
                "colour_not_only_signal", "missing_roles",
                "colliding_pairs", "loses_nothing",
                "passes", "segment"):
        stored.pop(key)
    return stored


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "mode_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    stored = view.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    return stored


def _book(themes=None, views=(), **overrides):
    fields = {
        "title": "A test theme book",
        "themes": [_stored_theme(theme) for theme in (
            themes if themes is not None else [_theme()])],
        "views": [_stored_view(item) for item in views],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(
        themes=[
            _theme(),
            _theme(theme_id="theme-plain", name="plain_theme",
                   accent_percent=None, ornament_percent=None,
                   signals={}),
            _theme(theme_id="theme-grey", name="grey_theme",
                   mode="no_colour"),
        ],
        views=[_view()])


# ---------------------------------------------------------------------
# The shipped example book, the roadmap and the charter.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_themes_grown_up()
    assert book.title == EXAMPLE_TITLE
    assert book.theme_ids() == (
        "theme-tokyo-night", "theme-viking-dark",
        "theme-light", "theme-high-contrast",
        "theme-no-colour")
    first = book.themes[0]
    assert first.name == "tokyo_night"
    assert first.mode == "full_colour"
    assert first.colour_of("background") == "#1a1b26"
    assert book.view_ids() == ("view-all", "view-nocolour")
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m178-boundary"
    assert panel.as_of == "2026-11-09"
    assert [row.theme_id for row in panel.rows] == [
        "theme-tokyo-night", "theme-viking-dark",
        "theme-light", "theme-high-contrast",
        "theme-no-colour"]
    derived = derive_panel(book, "view-all")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_themes == derived.total_themes == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.mode: c.themes for c in panel.mode_counts} == {
        "full_colour": 3, "high_contrast": 1, "no_colour": 1}
    assert derive_verdict(book, "view-all").verdict == "strained"
    assert derive_verdict(book, "view-nocolour").verdict == (
        "disciplined")
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / THEMES_GROWN_UP_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == THEMES_GROWN_UP_SCHEMA
    assert raw["slice"] == "M-179"
    assert "verdict" not in raw
    assert "segment" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-179")]
    assert slice_.title == "Themes grown up"
    assert slice_.part == 8
    assert "Design Lawbook" in slice_.summary
    assert "darkness ladders" in slice_.summary
    assert "accent budgets" in slice_.summary
    assert "high-contrast" in slice_.summary
    assert "no-colour" in slice_.summary
    assert "lose nothing" in slice_.summary
    assert THEMES_GROWN_UP_SLICE == "M-179"


def test_charter_names_no_row_for_m179():
    # No M-171 charter row names M-179 as an owning
    # slice, so the slice is built to the roadmap
    # words alone, as M-177 was - proven live
    # against every charter row.
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert "M-179" not in owners
    assert "M-178" in owners


def test_closed_vocabularies():
    assert ROLES == (
        "background", "surface", "primary", "secondary",
        "accent", "text", "muted", "success", "warning",
        "error")
    assert MODES == ("full_colour", "high_contrast", "no_colour")
    assert SURFACE_ROLES == ("background", "surface", "muted", "text")
    assert STATE_ROLES == ("success", "warning", "error")
    assert VERDICT_WORDS == ("disciplined", "strained", "bare")
    assert BUDGET_WORDS == ("within", "outside", "unknown")
    assert MIN_LADDER_RUNGS == 4
    assert (ACCENT_MIN_PERCENT, ACCENT_MAX_PERCENT) == (5, 12)
    assert (ORNAMENT_MIN_PERCENT, ORNAMENT_MAX_PERCENT) == (1, 5)
    assert MIN_VALUE_GAP == 0.005
    assert normalize_role("BG") == "background"
    assert normalize_role("panel") == "surface"
    assert normalize_mode("Monochrome") == "no_colour"
    assert normalize_mode("contrast") == "high_contrast"
    assert normalize_mode_filter("ALL") == "all"
    assert normalize_mode_filter("grey") == "no_colour"
    with pytest.raises(ValueError):
        normalize_role("whenever")
    with pytest.raises(ValueError):
        normalize_mode("whenever")
    assert "darkness ladders" in PLAIN_EXPLANATION
    assert "colour never the only signal" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /themesgrownup")


def test_shipped_themes_judged_honestly_as_data():
    # The shipped colour tables, judged whole:
    # every ladder holds at four rungs; tokyo_night
    # loses nothing by value; viking_dark loses
    # secondary~success (one shared colour in the
    # shipped table); light loses primary~secondary
    # (values closer than the telling gap); no
    # shipped table records cues or shares, so
    # colour stands alone for their states and
    # their budgets stand honestly unknown - and
    # the two themes this slice authors pass whole.
    book = load_themes_grown_up()
    tokyo = book.theme_for("theme-tokyo-night")
    assert ladder_count(tokyo) == 4
    assert loses_nothing(tokyo) is True
    assert budget_word(tokyo) == "unknown"
    assert colour_not_only_signal(tokyo) is False
    assert theme_passes(tokyo) is False
    viking = book.theme_for("theme-viking-dark")
    assert colliding_pairs(viking) == (("secondary", "success"),)
    assert loses_nothing(viking) is False
    light = book.theme_for("theme-light")
    assert colliding_pairs(light) == (("primary", "secondary"),)
    assert ladder_holds(light) is True
    for theme_id in ("theme-high-contrast", "theme-no-colour"):
        theme = book.theme_for(theme_id)
        assert theme_passes(theme) is True
        assert loses_nothing(theme) is True
        assert budget_word(theme) == "within"
        assert colour_not_only_signal(theme) is True
        assert cued_states(theme) == STATE_ROLES
    grey = book.theme_for("theme-no-colour")
    for _role, colour in grey.colours:
        assert colour[1:3] == colour[3:5] == colour[5:7]
    assert [t.theme_id for t in passing_themes(book)] == [
        "theme-high-contrast", "theme-no-colour"]


# ---------------------------------------------------------------------
# The theme: judged whole, its segment derived from its own fields.
# ---------------------------------------------------------------------


def test_theme_record_round_trips():
    theme = _theme()
    assert validate_theme(_stored_theme(theme)) == theme
    record = theme.to_record()
    assert record["ladder_count"] == 4
    assert record["budget"] == "within"
    assert record["loses_nothing"] is True
    assert record["passes"] is True
    assert segment_of(theme) == (
        "test_theme: ladder 4 rungs, budget within, "
        "colour never alone, loses nothing")
    assert theme.segment == segment_of(theme)


def test_theme_provenance_is_whole_and_required():
    theme = _theme()
    assert theme.recorded_on == ON
    assert theme.actor == BY
    assert theme.source == "test source"
    assert theme.origin_session == "session-test"
    for missing in ("recorded_on", "actor", "source",
                    "origin_session", "name", "mode",
                    "colours", "detail"):
        fields = _stored_theme(theme)
        fields.pop(missing)
        with pytest.raises(ValueError):
            build_theme(fields)


def test_theme_refuses_unknown_keys_and_derived_keys():
    fields = _stored_theme(_theme())
    fields["surprise"] = "x"
    with pytest.raises(ValueError):
        build_theme(fields)
    # The derived-judgement law: a theme carries no
    # ladder, no budget, no verdict and no summary -
    # those are derived from the theme, never
    # stored on one.
    for derived_key in ("ladder", "ladder_count", "budget",
                        "verdict", "segment", "loses_nothing",
                        "passes"):
        fields = _stored_theme(_theme())
        fields[derived_key] = "within"
        with pytest.raises(ValueError):
            build_theme(fields)


def test_theme_alias_spellings_read_onto_the_fields():
    theme = build_theme({
        "id": "theme-alias", "title": "alias_theme",
        "type_of": "monochrome",
        "colors": {"bg": "#0A0A0A", "panel": "#1F1F1F",
                   "foreground": "#F5F5F5"},
        "cues": {"ok": "a check mark"},
        "note": "An aliased theme, for the tests.",
        "day": ON, "by": BY, "source": "test source",
        "session": "session-test"})
    assert theme.mode == "no_colour"
    assert theme.name == "alias_theme"
    assert [role for role, _c in theme.colours] == [
        "background", "surface", "text"]
    assert theme.colour_of("background") == "#0a0a0a"
    assert theme.cue_of("success") == "a check mark"
    fields = _stored_theme(_theme())
    fields["title"] = "another_theme"
    with pytest.raises(ValueError):
        build_theme(fields)


def test_colours_stand_in_role_order_and_hex_is_checked():
    theme = _theme(colours={
        "error": "#FF2244", "background": "#000000",
        "text": "#FFFFFF"})
    assert [role for role, _c in theme.colours] == [
        "background", "text", "error"]
    assert theme.colour_of("error") == "#ff2244"
    with pytest.raises(ValueError):
        _theme(colours={"background": "black"})
    with pytest.raises(ValueError):
        _theme(colours=[("background", "#000000"),
                        ("bg", "#111111")])
    with pytest.raises(ValueError):
        _theme(colours={})


def test_signals_cue_states_only_and_never_share_a_cue():
    theme = _theme()
    assert cued_states(theme) == STATE_ROLES
    assert theme.cue_of("warning") == "triangle and the word Caution"
    with pytest.raises(ValueError):
        _theme(signals={"primary": "a star"})
    with pytest.raises(ValueError):
        _theme(signals={"success": "same cue",
                        "warning": "same cue"})
    bare = _theme(signals={})
    assert cued_states(bare) == ()
    assert colour_not_only_signal(bare) is False


# ---------------------------------------------------------------------
# The derived judgements: ladder, budget, signal, loss.
# ---------------------------------------------------------------------


def test_ladder_is_counted_from_the_surface_values():
    theme = _theme()
    assert ladder_count(theme) == 4
    assert ladder_holds(theme) is True
    flat = _theme(colours={
        "background": "#101010", "surface": "#101010",
        "muted": "#505050", "text": "#f0f0f0"})
    assert ladder_count(flat) == 3
    assert ladder_holds(flat) is False
    assert theme_passes(flat) is False
    assert colour_value("#000000") == 0.0
    assert colour_value("#ffffff") == pytest.approx(1.0)


def test_budget_word_within_outside_unknown():
    assert budget_word(_theme()) == "within"
    assert budget_word(_theme(accent_percent=5)) == "within"
    assert budget_word(_theme(accent_percent=12)) == "within"
    assert budget_word(_theme(accent_percent=13)) == "outside"
    assert budget_word(_theme(accent_percent=4)) == "outside"
    assert budget_word(_theme(ornament_percent=6)) == "outside"
    assert budget_word(_theme(ornament_percent=0)) == "outside"
    # An unmeasured share stands honestly unknown -
    # never dressed as within, never as outside.
    assert budget_word(_theme(accent_percent=None)) == "unknown"
    assert budget_word(_theme(ornament_percent=None)) == "unknown"
    assert theme_passes(_theme(accent_percent=None)) is False


def test_colour_is_never_the_only_signal():
    assert colour_not_only_signal(_theme()) is True
    partial = _theme(signals={"success": "a check mark"})
    assert colour_not_only_signal(partial) is False
    assert cued_states(partial) == ("success",)
    # A theme colouring no state role breaks no
    # signal law: nothing is named by colour alone.
    stateless = _theme(colours={"background": "#000000"},
                       signals={})
    assert colour_not_only_signal(stateless) is True


def test_loses_nothing_missing_colliding_and_cue_rescue():
    theme = _theme()
    assert missing_roles(theme) == ()
    assert colliding_pairs(theme) == ()
    assert loses_nothing(theme) is True
    short = _theme(colours={"background": "#000000",
                            "text": "#ffffff"})
    assert "error" in missing_roles(short)
    assert loses_nothing(short) is False
    assert "no error role" in lost_labels(short)
    # Two states sharing one value, told apart by
    # their cues, lose nothing; the same pair with
    # no cues told apart collides.
    shared = dict(PALETTE)
    shared["warning"] = shared["success"]
    rescued = _theme(colours=shared)
    assert colliding_pairs(rescued) == ()
    assert loses_nothing(rescued) is True
    uncued = _theme(colours=shared, signals={})
    assert colliding_pairs(uncued) == (("success", "warning"),)
    assert "success and warning share one value" in (
        lost_labels(uncued))


def test_measured_and_unmeasured_composition_roads():
    theme = measured_theme(
        "made_theme", "high_contrast", dict(PALETTE),
        theme_id="theme-made", accent_percent=10,
        ornament_percent=2, signals=dict(CUES),
        detail="A measured theme, for the tests.")
    assert theme_passes(theme) is True
    with pytest.raises(ValueError):
        measured_theme(
            "made_theme", "high_contrast", dict(PALETTE),
            theme_id="theme-made", accent_percent=None,
            ornament_percent=2,
            detail="No measurement stands here.")
    unknown = unmeasured_theme(
        "plain_theme", "full_colour", dict(PALETTE),
        theme_id="theme-plain")
    assert unknown.accent_percent is None
    assert budget_word(unknown) == "unknown"
    assert "honestly unknown" in unknown.detail


def test_inspect_theme_source_names_what_a_piece_is():
    named = inspect_theme_source(
        {"name": "x_theme", "mode": "grey",
         "colours": {"background": "#000000"}})
    assert named["mode"] == "no_colour"
    assert inspect_theme_source({"name": "x"})["mode"] is None
    assert inspect_theme_source("nope")["mode"] is None
    bad = inspect_theme_source(
        {"name": "x", "mode": "whenever", "colours": {}})
    assert bad["mode"] is None
    assert "one of" in bad["reason"]


# ---------------------------------------------------------------------
# The view, the panel and the verdict.
# ---------------------------------------------------------------------


def test_view_is_judged_whole():
    view = _view()
    assert validate_view(_stored_view(view)) == view
    assert view.mode_filter == "all"
    with pytest.raises(ValueError):
        _view(seq=0)
    fields = _stored_view(view)
    fields["surprise"] = "x"
    with pytest.raises(ValueError):
        build_view(fields)


def test_view_narrows_never_judges():
    book = _mixed_book()
    grey_view = _view(view_id="view-grey", mode_filter="no_colour")
    shown = shown_themes(book.themes, grey_view)
    assert [t.theme_id for t in shown] == ["theme-grey"]
    shown = shown_themes(book.themes, _view())
    assert [t.theme_id for t in shown] == [
        "theme-test", "theme-plain", "theme-grey"]
    assert total_themes(book) == 3
    assert [t.theme_id for t in themes_for_mode(book, "grey")] == [
        "theme-grey"]
    assert [t.theme_id for t in themes_for_mode(
        book, "full_colour")] == ["theme-test", "theme-plain"]


def test_panel_is_derived_for_one_view():
    book = _mixed_book()
    panel = derive_panel(book, _view())
    assert panel.total_themes == 3
    assert panel.total_shown == 3
    assert [row.name for row in panel.rows] == [
        "test_theme", "plain_theme", "grey_theme"]
    assert panel.rows[0].segment == (
        "test_theme: ladder 4 rungs, budget within, "
        "colour never alone, loses nothing")
    assert panel.rows[0].passes is True
    assert panel.rows[1].passes is False
    assert {c.mode: c.themes for c in panel.mode_counts} == {
        "full_colour": 2, "no_colour": 1}
    grey_panel = derive_panel(
        book, _view(view_id="view-grey", mode_filter="no_colour"))
    assert grey_panel.total_shown == 1
    assert grey_panel.rows[0].theme_id == "theme-grey"
    assert build_panel(source=book, view=_view()) == panel


def test_panel_refuses_a_stored_panel_that_disagrees():
    book = load_themes_grown_up()
    panel = book.panels[0]
    stored = panel.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    assert validate_panel(stored, book) == panel
    stored["rows"][0]["segment"] = "tokyo_night: written loose"
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    stored = panel.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    stored["total_shown"] = 4
    with pytest.raises(ValueError):
        validate_panel(stored, book)


def test_row_is_judged_against_its_theme():
    theme = _theme()
    row = build_row(theme=theme)
    assert row.segment == segment_of(theme)
    assert row.passes is True
    assert validate_row(row.to_record(), theme) == row
    stored = row.to_record()
    stored["segment"] = "test_theme: written loose"
    with pytest.raises(ValueError):
        validate_row(stored, theme)
    with pytest.raises(ValueError):
        build_row(theme=theme, segment="test_theme: loose")


def test_verdict_words_disciplined_strained_bare():
    passing = _book(themes=[_theme()], views=[_view()])
    verdict = derive_verdict(passing, _view())
    assert verdict.verdict == "disciplined"
    assert verdict.passing_shown == 1
    assert verdict.distinct_modes == 1
    assert build_verdict(source=passing, view=_view()) == verdict
    mixed = _mixed_book()
    assert derive_verdict(mixed, _view()).verdict == "strained"
    plain_only = _book(
        themes=[_theme(theme_id="theme-plain", name="plain_theme",
                       signals={}, accent_percent=None,
                       ornament_percent=None)],
        views=[_view()])
    assert derive_verdict(plain_only, _view()).verdict == "bare"
    empty = derive_verdict(
        mixed, _view(view_id="view-hc", mode_filter="high_contrast"))
    assert empty.total_shown == 0
    assert empty.verdict == "bare"
    stored = verdict.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    stored["verdict"] = "strained"
    with pytest.raises(ValueError):
        validate_verdict(stored)


# ---------------------------------------------------------------------
# The book, the file loader and the registry.
# ---------------------------------------------------------------------


def test_book_laws_one_theme_per_id_and_per_name():
    book = _book(themes=[_theme()], views=[_view()])
    assert book.theme_for("theme-test").name == "test_theme"
    assert book.view_for("view-test").mode_filter == "all"
    with pytest.raises(KeyError):
        book.theme_for("theme-nope")
    with pytest.raises(ValueError):
        _book(themes=[_theme(), _theme(name="other_theme")])
    with pytest.raises(ValueError):
        _book(themes=[_theme(), _theme(theme_id="theme-two")])
    with pytest.raises(ValueError):
        _book(themes=[_theme()], views=[_view(), _view(seq=1)])


def test_book_file_loader_reads_any_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / THEMES_GROWN_UP_RESOURCE).read_text(encoding="utf-8")
    path = tmp_path / "themes.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_themes_grown_up_file(path)
    assert book.title == EXAMPLE_TITLE
    assert len(book.themes) == 5


def test_registry_holds_themes_and_views_one_by_one():
    registry = ThemeRegistry()
    theme = registry.register_theme(_theme())
    assert theme.theme_id == "theme-test"
    with pytest.raises(ValueError):
        registry.register_theme(_theme())
    with pytest.raises(ValueError):
        registry.register_theme(_theme(theme_id="theme-two"))
    view = registry.register_view(_view(view_id=None))
    assert view.view_id == "view-1"
    with pytest.raises(ValueError):
        registry.register_view(_view(view_id="view-two"))
    assert registry.latest_view().view_id == "view-1"
    assert registry.get_theme("theme-test").name == "test_theme"
    with pytest.raises(KeyError):
        registry.get_theme("theme-nope")
    book = registry.book()
    assert book.title == "Themes Grown Up"
    assert registry.panel(_view()).total_shown == 1
    assert registry.verdict(_view()).verdict == "disciplined"


def test_registry_register_book_and_refusals():
    registry = ThemeRegistry()
    book = registry.register_book(_mixed_book())
    assert len(book.themes) == 3
    assert registry.title() == "A test theme book"
    with pytest.raises(ValueError):
        registry.register_book(_mixed_book())
    other = _book(themes=[_theme(theme_id="theme-x",
                                 name="x_theme")],
                  title="Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)
    seeded = ThemeRegistry(_mixed_book())
    assert len(seeded.list_themes()) == 3
    assert len(seeded.list_views()) == 1


def test_news_records_carry_headlines():
    theme = _theme()
    record = theme_record(theme)
    assert record["news"] is True
    assert record["type"] == "themes_grown_up_theme"
    assert "theme-test" in record["headline"]
    view = view_record(_view())
    assert view["type"] == "themes_grown_up_view"
    assert "view-test" in view["headline"]
    book = _mixed_book()
    panel = panel_record(derive_panel(book, _view()))
    assert panel["type"] == "themes_grown_up_panel"
    assert "3 of 3" in panel["headline"]
    verdict = verdict_record(derive_verdict(book, _view()))
    assert verdict["type"] == "themes_grown_up_verdict"
    assert verdict["verdict"] == "strained"
    whole = book_record(book)
    assert whole["theme_count"] == 3
    assert "2 of 3" in whole["headline"]


def test_formatters_and_screen():
    theme = _theme()
    text = format_theme(theme)
    assert "Name: test_theme" in text
    assert "Mode: full_colour" in text
    assert "Colour success: #00cc44" in text
    assert "Cue warning: triangle and the word Caution" in text
    assert "Accent share: 8" in text
    assert "test_theme: ladder 4 rungs" in plain_words(theme)
    view_text = format_view(_view())
    assert "mode 'all'" in view_text
    assert "looks at mode 'all'" in view_plain_words(_view())
    book = _mixed_book()
    assert "theme-grey" in format_book(book)
    grey_only = format_book(book, "no_colour")
    assert "theme-grey" in grey_only
    assert "theme-test" not in grey_only
    panel_text = format_panel(book)
    assert "Panel in A test theme book" in panel_text
    assert "stand disciplined whole" in panel_text
    assert panel_plain_words(book).startswith("A test theme book")
    verdict_text = format_verdict(book)
    assert "strained" in verdict_text
    assert "strained" in verdict_plain_words(book)
    screen = format_themes_grown_up_screen(load_themes_grown_up())
    assert "Themes Grown Up (M-179)" in screen
    assert "5 of 5 themes show" in screen
    assert "Verdict: strained." in screen


def test_parse_themes_grown_up_args_grammar():
    assert parse_themes_grown_up_args("") == ("show", None)
    assert parse_themes_grown_up_args(None) == ("show", None)
    assert parse_themes_grown_up_args("show") == ("show", None)
    assert parse_themes_grown_up_args("list") == ("show", None)
    assert parse_themes_grown_up_args("theme theme-test") == (
        "theme", "theme-test")
    assert parse_themes_grown_up_args("view view-all") == (
        "view", "view-all")
    assert parse_themes_grown_up_args("mode grey") == (
        "mode", "no_colour")
    assert parse_themes_grown_up_args("panel") == ("panel", None)
    assert parse_themes_grown_up_args("verdict") == ("verdict", None)
    for bad in ("dance", "theme", "theme a b", "mode whenever",
                "panel now"):
        with pytest.raises(ValueError) as excinfo:
            parse_themes_grown_up_args(bad)
        assert str(excinfo.value) == USAGE
    with pytest.raises(ValueError):
        parse_themes_grown_up_args(42)


def test_pure_layer_imports_no_agent_or_ui():
    text = (ROOT / "mythic_agent" / "core"
            / "themes_grown_up.py").read_text(encoding="utf-8")
    assert "mythic_agent.agents" not in text
    assert "import textual" not in text
    assert "from ..agents" not in text
    assert "from ..ui" not in text


# -- agent layer -----------------------------------------------------------
#
# M-179 agent layer: the agent holds a
# ThemeRegistry for the session (session state
# only, no new setting), themes and view records
# are held by being registered - each judged whole
# before it is held - published as their
# theme_record / view_record session news through
# the checkpoint road, deduped per shape - a theme
# composed from measured shares or raised honestly
# unmeasured stands on the register road exactly
# as the pure layer composed it, the viewing road
# composes one view record at the held book's next
# sequence and publishes the derived panel and
# verdict news with it, whole-book register and
# record roads hold a book judged whole first, the
# report road renders the held book (or the shipped
# example when unheld) through the pure formatters,
# and the /themesgrownup surface rides both roads
# on the pure parser + formatters. Status, get,
# mode, passing, panel and verdict reads register
# and publish nothing, answer from the held registry
# first and from the shipped example only while
# nothing is held - a held theme never falls back
# to the example. The panel and the verdict derive
# at call time from the whole book under a view,
# never held. This layer repaints no live UI,
# applies no theme live, renders no live UI,
# measures no running screen, calls no model,
# persists nothing beyond the session journal news
# and banks nothing - a theme held here is a
# finding, never the live face of the app.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _theme_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "themes_grown_up.yaml").read_text(encoding="utf-8")
    path = tmp_path / "themes_grown_up.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestThemesGrownUpAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.themes_grown_up_status()
        assert status["themes"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["themes_grown_up"]["title"] == EXAMPLE_TITLE
        assert len(status["themes_grown_up"]["themes"]) == 5
        assert len(status["themes_grown_up"]["views"]) == 2
        assert status["panel"]["total_themes"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m178-boundary"
        assert status["book_record"]["theme_count"] == 5
        assert status["book_record"]["view_count"] == 2
        assert status["verdict"]["verdict"] == "strained"
        assert "no_colour: ladder 4 rungs" in status["plain_words"]
        assert "Themes Grown Up (M-179)" in status["screen"]
        assert "5 of 5 themes show" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._themes_grown_up_registry()
        assert agent._themes_grown_up_registry() is first
        assert agent._themes_grown_up_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.themes_grown_up_status()
        assert agent.get_theme_profile(
            "theme-no-colour").mode == "no_colour"
        assert agent.get_theme_view(
            "view-all").mode_filter == "all"
        assert [t.theme_id for t in agent.themes_grown_up_with_mode(
            "full_colour")] == [
                "theme-tokyo-night", "theme-viking-dark", "theme-light"]
        assert [t.theme_id for t in agent.themes_grown_up_with_mode(
            "grey")] == ["theme-no-colour"]
        assert [t.theme_id for t in agent.themes_grown_up_passing()] == [
            "theme-high-contrast", "theme-no-colour"]
        agent.themes_grown_up_panel()
        agent.themes_grown_up_verdict()
        agent.report_themes_grown_up()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("themes_grown_up")] == []
        with pytest.raises(KeyError):
            agent.get_theme_profile("theme-nope")
        with pytest.raises(KeyError):
            agent.get_theme_view("view-nope")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_theme_profile(_theme())
        status = agent.themes_grown_up_status()
        assert [t["theme_id"] for t in status["themes"]] == [
            "theme-test"]
        assert status["book"]["title"] == "Themes Grown Up"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert "test_theme: ladder 4 rungs" in status["screen"]

    def test_held_theme_never_falls_back_to_the_example(
            self, agent):
        agent.register_theme_profile(_theme())
        with pytest.raises(KeyError):
            agent.get_theme_profile("theme-tokyo-night")
        with pytest.raises(KeyError):
            agent.get_theme_view("view-all")
        theme = agent.get_theme_profile("theme-test")
        assert theme.name == "test_theme"
        assert agent.themes_grown_up_book().title == "Themes Grown Up"


class TestThemesGrownUpAgentHolding:
    def test_register_theme_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_theme_profile(_theme())
        assert outcome["theme"]["theme_id"] == "theme-test"
        assert outcome["record_news"]["news"] is True
        assert outcome["record_news"]["type"] == (
            "themes_grown_up_theme")
        assert "theme-test" in outcome["screen"]
        agent.register_theme_profile(_theme(
            theme_id="theme-grey", name="grey_theme",
            mode="no_colour"))
        events = _theme_events(
            store, session_id, "themes_grown_up_theme")
        assert len(events) == 2
        agent._publish_themes_grown_up_record(theme_record(_theme()))
        agent._publish_themes_grown_up_record(
            {"type": "slice_board_card", "news": True})
        events = _theme_events(
            store, session_id, "themes_grown_up_theme")
        assert len(events) == 2
        agent.close()

    def test_duplicate_theme_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_theme_profile(_theme())
        with pytest.raises(ValueError):
            agent.register_theme_profile(_theme())
        with pytest.raises(ValueError):
            agent.register_theme_profile(
                _theme(theme_id="theme-other"))
        events = _theme_events(
            store, session_id, "themes_grown_up_theme")
        assert len(events) == 1
        agent.close()

    def test_composed_themes_hold_by_the_register_road(self, agent):
        measured = measured_theme(
            "made_theme", "high_contrast", dict(PALETTE),
            theme_id="theme-made", accent_percent=10,
            ornament_percent=2, signals=dict(CUES),
            detail="A measured theme, for the tests.")
        outcome = agent.register_theme_profile(measured)
        assert outcome["theme"]["mode"] == "high_contrast"
        unknown = unmeasured_theme(
            "plain_theme", "full_colour", dict(PALETTE),
            theme_id="theme-plain")
        agent.register_theme_profile(unknown)
        assert [t.theme_id for t in agent.themes_grown_up_passing()] == [
            "theme-made"]
        assert agent.get_theme_profile("theme-plain").passes is False
        assert "budget unknown" in segment_of(
            agent.get_theme_profile("theme-plain"))

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_theme_profile(_theme())
        outcome = agent.register_theme_view(_view())
        assert outcome["view"]["view_id"] == "view-test"
        assert outcome["record_news"]["type"] == "themes_grown_up_view"
        with pytest.raises(ValueError):
            agent.register_theme_view(_view(seq=2))
        with pytest.raises(ValueError):
            agent.register_theme_view(
                _view(view_id="view-two"))
        assert [v.view_id for v in
                agent._themes_grown_up_registry().list_views()] == [
                    "view-test"]
        events = _theme_events(
            store, session_id, "themes_grown_up_view")
        assert len(events) == 1
        agent.close()

    def test_view_road_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_theme_profile(_theme())
        agent.register_theme_profile(_theme(
            theme_id="theme-plain", name="plain_theme",
            signals={}, accent_percent=None, ornament_percent=None))
        outcome = agent.view_themes_grown_up("all")
        assert outcome["view"]["seq"] == 1
        assert outcome["view"]["view_id"] == "view-1"
        assert outcome["record_news"]["type"] == "themes_grown_up_view"
        assert outcome["panel_record"]["type"] == (
            "themes_grown_up_panel")
        assert outcome["panel_record"]["total_shown"] == 2
        assert outcome["verdict_record"]["type"] == (
            "themes_grown_up_verdict")
        assert outcome["verdict_record"]["verdict"] == "strained"
        second = agent.view_themes_grown_up(
            "no_colour",
            detail="See the no-colour themes alone, for the tests.")
        assert second["view"]["seq"] == 2
        assert second["verdict_record"]["verdict"] == "bare"
        assert agent.themes_grown_up_verdict().verdict == "strained"
        assert len(_theme_events(
            store, session_id, "themes_grown_up_view")) == 2
        assert len(_theme_events(
            store, session_id, "themes_grown_up_verdict")) == 2
        agent.close()

    def test_view_road_over_an_unheld_mode_is_bare(self, agent):
        agent.register_theme_profile(_theme())
        outcome = agent.view_themes_grown_up("no_colour")
        assert outcome["panel_record"]["total_shown"] == 0
        assert outcome["verdict_record"]["verdict"] == "bare"
        assert agent.themes_grown_up_panel(
            outcome["view"]["view_id"]).total_shown == 0

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_themes_grown_up_book(_mixed_book())
        assert outcome["count"] == 3
        assert [t["theme_id"] for t in outcome["themes"]] == [
            "theme-test", "theme-plain", "theme-grey"]
        assert [r["type"] for r in outcome["records_news"]] == [
            "themes_grown_up_theme", "themes_grown_up_theme",
            "themes_grown_up_theme", "themes_grown_up_view"]
        events = _theme_events(
            store, session_id, "themes_grown_up_theme")
        assert [e["theme_id"] for e in events] == [
            "theme-test", "theme-plain", "theme-grey"]
        assert agent.themes_grown_up_book().title == (
            "A test theme book")
        with pytest.raises(ValueError):
            agent.register_themes_grown_up_book(_mixed_book())
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_themes_grown_up_book()
        assert outcome["count"] == 5
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_theme_events(
            store, session_id, "themes_grown_up_theme")) == 5
        assert len(_theme_events(
            store, session_id, "themes_grown_up_view")) == 2
        status = agent.themes_grown_up_status()
        assert status["panels"][0]["panel_id"] == "panel-m178-boundary"
        with pytest.raises(ValueError):
            agent.record_themes_grown_up_book()
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_book_file(tmp_path)
        book = load_themes_grown_up_file(path)
        outcome = agent.record_themes_grown_up_book(book)
        assert outcome["count"] == 5
        assert agent.themes_grown_up_book().title == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_themes_grown_up()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert len(report["themes"]) == 5
        assert report["verdict"]["verdict"] == "strained"
        assert "theme-no-colour: no_colour: ladder 4 rungs" in (
            report["book_text"])
        agent.register_theme_profile(_theme())
        report = agent.report_themes_grown_up()
        assert [t["theme_id"] for t in report["themes"]] == [
            "theme-test"]
        assert "theme-test: test_theme: ladder 4 rungs" in (
            report["book_text"])
        assert report["verdict"] is None

    def test_holding_and_viewing_execute_nothing(self, agent):
        for name in (
                "measure_theme_area", "read_live_theme",
                "apply_theme", "repaint_ui",
                "render_themes_ui", "set_live_theme",
                "persist_themes_grown_up", "bank_themes_grown_up",
                "run_themes_grown_up", "delete_theme"):
            assert not hasattr(agent, name), name
        agent.register_theme_profile(_theme())
        agent.view_themes_grown_up("all")
        # A view held here only ever looks: no theme was
        # applied live, no screen was repainted, no area
        # was measured, and the book's standing lives in
        # no setting.
        assert agent.themes_grown_up_book().title == "Themes Grown Up"
        assert agent.config.get("themes_grown_up") is None


class TestThemesGrownUpTerminalSurface:
    def test_show_theme_view_mode_panel_verdict(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/themesgrownup")
        assert "Themes Grown Up (M-179)" in text
        _, _, text = _slash(
            agent, "/themesgrownup theme theme-no-colour")
        assert "Name: no_colour" in text
        assert "Mode: no_colour" in text
        _, _, text = _slash(agent, "/themesgrownup view view-all")
        assert "mode 'all'" in text
        _, _, text = _slash(agent, "/themesgrownup mode no_colour")
        assert "theme-no-colour" in text
        assert "theme-tokyo-night" not in text
        _, _, text = _slash(agent, "/themesgrownup panel")
        assert "Panel in Themes at the M-178 slice boundary" in text
        _, _, text = _slash(agent, "/themesgrownup verdict")
        assert "strained" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/themesgrownup [show|theme <theme-id>"
                "|view <view-id>|mode <mode>|panel|verdict]") in text
        _, _, text = _slash(agent, "/themesgrownup dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/themesgrownup theme theme-nope")
        assert "no theme named" in text


@pytest.fixture()
def theme_handler(agent, monkeypatch):
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


def _theme_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestThemesGrownUpCommand:
    def test_show_is_default(self, theme_handler, agent):
        theme_handler._handle_themesgrownup("")
        assert "Themes Grown Up (M-179)" in (
            _theme_published_text(theme_handler))

    def test_theme_view_mode_panel_verdict(
            self, theme_handler, agent):
        theme_handler._handle_themesgrownup("theme theme-no-colour")
        assert "Name: no_colour" in (
            _theme_published_text(theme_handler))
        theme_handler._handle_themesgrownup("view view-all")
        assert "mode 'all'" in _theme_published_text(
            theme_handler)
        theme_handler._handle_themesgrownup("mode full_colour")
        assert "theme-light" in _theme_published_text(theme_handler)
        theme_handler._handle_themesgrownup("panel")
        assert "Panel in Themes" in (
            _theme_published_text(theme_handler))
        theme_handler._handle_themesgrownup("verdict")
        assert "strained" in _theme_published_text(theme_handler)

    def test_bad_grammar_is_published(
            self, theme_handler, agent):
        theme_handler._handle_themesgrownup("dance party")
        assert USAGE in _theme_published_text(theme_handler)
        theme_handler._handle_themesgrownup("theme theme-nope")
        assert "no theme named" in _theme_published_text(
            theme_handler)


class TestChatScreenRoutingThemesGrownUp:
    def test_themesgrownup_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/themesgrownup panel", _FakeLog())
        assert calls == [("/themesgrownup", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/themesgrownup[/green] - show themes grown up (M-179)" in (
            text)
        assert ('"/themesgrownup": "Usage: /themesgrownup | '
                '/themesgrownup theme <theme-id>') in text
