"""Fuzzy file finding, .gitignore-aware filtering, and edit previews (Slice 18)."""

from .smart_files import (
    fuzzy_find,
    fuzzy_score,
    load_gitignore,
    preview_edit,
    respect_gitignore,
)

__all__ = [
    "fuzzy_find",
    "fuzzy_score",
    "load_gitignore",
    "preview_edit",
    "respect_gitignore",
]
