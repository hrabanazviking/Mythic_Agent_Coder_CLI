"""Slice 32 tests: dependency-free Markdown rendering."""

from mythic_agent.ui.markdown import render_markdown


def test_bold_renders_with_ansi():
    assert render_markdown("**hello**") == "\x1b[1mhello\x1b[0m"


def test_italic_renders_with_ansi():
    out = render_markdown("*hello*")
    assert out == "\x1b[3mhello\x1b[0m"


def test_plain_ansi_disabled_returns_clean_text():
    out = render_markdown("**bold** and *italic* and `code`", ansi=False)
    assert out == "bold and italic and code"


def test_code_block_is_preserved():
    out = render_markdown("```python\nprint(1)\n```")
    assert "print(1)" in out


def test_heading_drops_hashes():
    out = render_markdown("## Title", ansi=False)
    assert out == "Title"
    assert "#" not in out


def test_link_keeps_label_drops_target():
    out = render_markdown("[click](https://example.com)", ansi=False)
    assert out == "click"


def test_list_bullets_normalized():
    out = render_markdown("- one\n* two", ansi=False)
    assert out == "• one\n• two"


def test_inline_code_does_not_format_inside():
    out = render_markdown("`**x**`", ansi=False)
    assert out == "**x**"
