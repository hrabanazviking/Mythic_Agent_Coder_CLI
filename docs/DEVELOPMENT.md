# Development and validation

Use Python 3.10 or later in an isolated environment:

```sh
python -m venv .venv
# Activate using your shell's venv command.
python -m pip install -e '.[dev,tui]'
python -m pytest
python -m build
```

Core installation is `pip install .`; `mythic --help` and `mythic --version` do not
load settings, start agents, or import optional UI/audio packages. Default launch
requires `.[tui]`. Optional extras are `mcp`, `knowledge`, `voice`, and
`voice-cloning`. Voice cloning has separate platform/runtime dependencies and is
not a core support gate. Wheel resources include persona Markdown/art and the
engineering protocol; README screenshots are not bundled.

CI runs maintained tests on Linux, Windows and macOS with Python 3.10 and 3.13,
builds distributions, installs the wheel into a new environment, and checks its
entry points/resources from outside the source checkout. See `ROADMAP.md` for
slice requirements. Tests use fakes/temporary data; real-provider/platform evidence
must be recorded separately. Preserve old root experiments rather than collecting
them as automated tests.
