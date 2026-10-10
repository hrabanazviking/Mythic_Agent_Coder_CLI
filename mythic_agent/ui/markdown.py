"""Lightweight Markdown renderer that works without optional dependencies.

The TUI and terminal loop prefer ``rich.Markdown`` when rich is installed;
this module is a dependency-free fallback that turns Markdown into plain
text decorated with ANSI styles (bold, italic, code) for monochrome-safe
terminal output.  It is intentionally small: headings, code blocks, inline
code, bold, italic, strikethrough, links, lists, and blockquotes.
"""


from __future__ import annotations

__all__ = [
    "render_markdown",
]

import re

_ANSI = {
    "bold": "\x1b[1m",
    "italic": "\x1b[3m",
    "dim": "\x1b[2m",
    "code": "\x1b[38;5;180m",  # warm sand color for inline code
    "reset": "\x1b[0m",
}


def _styled(text: str, style: str, ansi: bool) -> str:
    return f"{_ANSI[style]}{text}{_ANSI['reset']}" if ansi else text


def render_markdown(text: str, *, ansi: bool = True) -> str:
    """Render a Markdown string to styled text.

    Args:
        text: The Markdown source.
        ansi: When False, strip styling and return plain text (formatting
            characters are removed, code-block content is preserved).

    Returns:
        The rendered string, line-for-line with the input.
    """
    if not text:
        return text
    out: list[str] = []
    in_fence = False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append("" if ansi else "")
            continue
        if in_fence:
            out.append(_styled(line, "code", ansi) if ansi else line)
            continue
        rendered = _render_block_line(line, ansi)
        out.append(_render_inline(rendered, ansi))
    return "\n".join(out)


def _render_block_line(line: str, ansi: bool) -> str:
    stripped = line.lstrip()
    if stripped.startswith(">"):
        content = stripped[1:].lstrip()
        return _styled(f"│ {content}", "dim", ansi) if ansi else f"> {content}"
    heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
    if heading:
        level = len(heading.group(1))
        title = heading.group(2).strip()
        return _styled(title, "bold", ansi) if ansi else title
    ordered = re.match(r"^\s*\d+\.\s+(.*)$", line)
    if ordered:
        prefix = re.match(r"^(\s*)\d+\.", line).group(1)
        return f"{prefix}• {ordered.group(1)}"
    unordered = re.match(r"^(\s*)[-*+]\s+(.*)$", line)
    if unordered:
        return f"{unordered.group(1)}• {unordered.group(2)}"
    return line


def _render_inline(text: str, ansi: bool) -> str:
    # Inline code first: stash code spans behind placeholders so later
    # formatting passes leave them alone.
    codes: list[str] = []

    def _code(match: re.Match[str]) -> str:
        codes.append(_styled(match.group(1), "code", ansi))
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", _code, text)
    text = re.sub(r"\*\*([^*]+)\*\*", lambda m: _styled(m.group(1), "bold", ansi), text)
    text = re.sub(r"__([^_]+)__", lambda m: _styled(m.group(1), "bold", ansi), text)
    text = re.sub(r"(?<!\w)\*([^*]+)\*(?!\w)", lambda m: _styled(m.group(1), "italic", ansi), text)
    text = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", lambda m: _styled(m.group(1), "italic", ansi), text)
    text = re.sub(r"~~([^~]+)~~", lambda m: _styled(m.group(1), "dim", ansi), text)
    # Links: keep the label, drop the target.
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", lambda m: m.group(1), text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", lambda m: f"[image: {m.group(1)}]", text)
    for index, code in enumerate(codes):
        text = text.replace(f"\x00{index}\x00", code)
    return text
