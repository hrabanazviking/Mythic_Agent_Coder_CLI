"""Slice 30 tests: named UI themes."""

import pytest

from mythic_agent.ui import themes


def test_list_themes_includes_required_names():
    names = themes.list_themes()
    assert "tokyo_night" in names
    assert "viking_dark" in names
    assert "light" in names


def test_get_theme_returns_color_roles():
    theme = themes.get_theme("tokyo_night")
    for role in ("background", "surface", "primary", "text", "error"):
        assert role in theme
        assert theme[role].startswith("#")


def test_get_theme_returns_a_copy():
    first = themes.get_theme("light")
    first["primary"] = "#000000"
    assert themes.get_theme("light")["primary"] != "#000000"


def test_get_theme_unknown_raises_key_error():
    with pytest.raises(KeyError):
        themes.get_theme("not_a_theme")


def test_is_valid_theme():
    assert themes.is_valid_theme("viking_dark")
    assert not themes.is_valid_theme("mordor")


def test_to_textual_kwargs_matches_theme():
    kwargs = themes.to_textual_kwargs("viking_dark")
    assert kwargs == themes.get_theme("viking_dark")
