"""Tests for mythic_agent.core.progress (Slice 29)."""

import io

from mythic_agent.core.progress import ProgressBar, Spinner


def test_progress_bar_fraction():
    bar = ProgressBar(total=10, enabled=False)
    assert bar.fraction == 0.0
    bar.update(5)
    assert bar.fraction == 0.5
    bar.update(10)
    assert bar.fraction == 1.0  # clamped


def test_progress_bar_set():
    bar = ProgressBar(total=100, enabled=False)
    bar.set(25)
    assert bar.fraction == 0.25
    bar.set(-5)
    assert bar.fraction == 0.0


def test_progress_bar_context_manager():
    bar = ProgressBar(total=4, enabled=False)
    with bar:
        bar.update(4)
    assert bar.fraction == 1.0


def test_progress_bar_writes_when_enabled():
    stream = io.StringIO()
    bar = ProgressBar(total=2, label="Test", stream=stream, enabled=True)
    bar.update(1)
    bar.finish()
    out = stream.getvalue()
    assert "Test" in out
    assert "50.0%" in out


def test_progress_bar_silent_when_disabled():
    stream = io.StringIO()
    bar = ProgressBar(total=2, stream=stream, enabled=False)
    bar.update(2)
    bar.finish()
    assert stream.getvalue() == ""


def test_spinner_context_manager_disabled():
    stream = io.StringIO()
    with Spinner("Working", stream=stream, enabled=False):
        pass  # should not raise or write
    assert stream.getvalue() == ""
