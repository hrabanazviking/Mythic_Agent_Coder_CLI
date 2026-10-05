# Maintained automated tests

Run `python -m pytest` after installing `.[dev]`. These tests must not contact
hosted providers, user databases, or real configuration directories. Use temporary
workspaces and fake providers. Tests for optional capabilities may explicitly skip
when their extra is absent; CI also installs the TUI extra.

Root-level `test_*.py` files are preserved prototype experiments. Some launch
interactive apps during import. Pytest intentionally collects only this directory.
