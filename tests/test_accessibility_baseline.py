"""
TIER: unit
Accessibility Baseline gate (All-Features roadmap slice M-016).

The shipped baseline (``mythic_agent/data/accessibility_baseline.yaml``)
is the "before" picture for Part VIII: keyboard-only task completion,
a screen-reader pass over the TUI, and a WCAG contrast audit. These
tests cross-check it against the live tree and re-measure its core
claims: every recorded contrast ratio is recomputed from the live
themes, the approval dialog is driven by keyboard alone under the
Textual pilot (press, never click), the shortcut registry gap the
baseline reports is still the tree's real gap, NO_COLOR is still
claimed-but-unread, and no PASS verdict rests on anything but
locally measured evidence.
"""

import asyncio
import copy
import re
from pathlib import Path

import pytest

from mythic_agent.core.accessibility_baseline import (
    AA_LARGE,
    AA_NORMAL,
    AccessibilityBaseline,
    contrast_ratio,
    load_baseline,
    render_markdown,
    validate_baseline,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource
from mythic_agent.ui.shortcuts import SHORTCUTS
from mythic_agent.ui.themes import THEMES, list_themes

REPO_ROOT = Path(__file__).resolve().parent.parent
PKG_DIR = REPO_ROOT / "mythic_agent"
UI_DIR = PKG_DIR / "ui"

# TUI actions the registry advertises but (per the baseline) no
# screen binds: the F-03 gap, pinned so a fix must update the data.
UNWIRED_TUI_ACTIONS = (
    "help",
    "clear",
    "focus_input",
    "scroll_up",
    "scroll_down",
    "new_tab",
    "next_tab",
    "prev_tab",
    "close_tab",
    "command_palette",
    "toggle_sidebar",
)


@pytest.fixture(scope="module")
def baseline() -> AccessibilityBaseline:
    return load_baseline()


def test_shipped_baseline_loads_and_validates(baseline):
    assert isinstance(baseline, AccessibilityBaseline)
    assert validate_baseline(load_resource("accessibility_baseline.yaml")) == []
    assert baseline.counts() == (6, 6, 3, 6)


def test_ids_are_sequential(baseline):
    assert baseline.keyboard_ids() == tuple(f"K-{n:02d}" for n in range(1, 7))
    assert baseline.screen_reader_ids() == tuple(f"S-{n:02d}" for n in range(1, 7))
    assert baseline.finding_ids() == tuple(f"F-{n:02d}" for n in range(1, 7))


def test_no_pass_without_measured_evidence(baseline):
    for check in baseline.keyboard_checks + baseline.screen_reader_checks:
        if check.verdict == "PASS":
            assert check.evidence_kind == "local-measured", check.id
    # The real screen-reader pass has never been run: it stays honest.
    sr = {c.id: c for c in baseline.screen_reader_checks}
    assert sr["S-06"].verdict == "NOT PROVEN"
    assert sr["S-06"].evidence_kind == "none"


def test_contrast_ratios_recompute_from_live_themes(baseline):
    assert set(baseline.theme_names()) == set(list_themes())
    for entry in baseline.contrast_entries:
        theme = THEMES[entry.theme]
        for pair, recorded in entry.ratios:
            role, background = pair.split("_on_")
            live = round(contrast_ratio(theme[role], theme[background]), 2)
            assert live == recorded, (entry.theme, pair, live, recorded)


def test_contrast_verdicts_match_the_numbers(baseline):
    by_theme = {e.theme: e for e in baseline.contrast_entries}
    for entry in baseline.contrast_entries:
        # Body text clears AA normal in every shipped theme.
        assert entry.ratio("text_on_background") >= AA_NORMAL, entry.theme
        # No theme claims PASS while a recorded pair fails AA normal.
        if entry.verdict == "PASS":
            assert entry.worst()[1] >= AA_NORMAL, entry.theme
    # The two headline failures the findings name are real.
    assert by_theme["viking_dark"].ratio("error_on_background") < AA_LARGE
    for entry in baseline.contrast_entries:
        assert entry.ratio("muted_on_background") < AA_NORMAL, entry.theme


def test_keyboard_approval_approve_and_reject_without_a_mouse():
    pytest.importorskip("textual")
    from textual.app import App

    from mythic_agent.ui.components.modals import CommandApproval

    async def scenario():
        # Approve: Allow opens focused, Tab cycles, Enter approves.
        state = {"approved": False, "rejected": False}

        class ApproveUI(App):
            def on_mount(self):
                self.push_screen(
                    CommandApproval(
                        "run ls",
                        lambda: state.update(approved=True),
                        lambda: state.update(rejected=True),
                    )
                )

        app = ApproveUI()
        async with app.run_test() as pilot:
            for _ in range(50):
                await pilot.pause(0.05)
                if isinstance(app.screen, CommandApproval) and app.screen.query("#allow"):
                    break
            assert getattr(app.screen.focused, "id", None) == "allow"
            await pilot.press("tab")
            await pilot.pause(0.05)
            assert getattr(app.screen.focused, "id", None) == "reject"
            await pilot.press("tab")
            await pilot.pause(0.05)
            assert getattr(app.screen.focused, "id", None) == "allow"
            await pilot.press("enter")
            await pilot.pause(0.1)
            assert state == {"approved": True, "rejected": False}
            assert not isinstance(app.screen, CommandApproval)

        # Reject: Escape rejects, and rejection grants nothing.
        state2 = {"approved": False, "rejected": False}

        class RejectUI(App):
            def on_mount(self):
                self.push_screen(
                    CommandApproval(
                        "run ls",
                        lambda: state2.update(approved=True),
                        lambda: state2.update(rejected=True),
                    )
                )

        app2 = RejectUI()
        async with app2.run_test() as pilot:
            for _ in range(50):
                await pilot.pause(0.05)
                if isinstance(app2.screen, CommandApproval):
                    break
            await pilot.press("escape")
            await pilot.pause(0.1)
            assert state2 == {"approved": False, "rejected": True}

    asyncio.run(scenario())


def test_shortcut_registry_gap_is_the_trees_real_gap(baseline):
    # Every "unwired" action is really in the registry...
    for action in UNWIRED_TUI_ACTIONS:
        assert action in SHORTCUTS, action
    # ...and really has no binding or action anywhere in the UI
    # package outside the registry itself: neither its key string
    # nor an action_<name> handler appears in any other UI module.
    ui_source = "\n".join(
        p.read_text(encoding="utf-8")
        for p in sorted(UI_DIR.rglob("*.py"))
        if p.name != "shortcuts.py" and "__pycache__" not in p.parts
    )
    for action in UNWIRED_TUI_ACTIONS:
        assert f'"{SHORTCUTS[action]}"' not in ui_source, action
        assert f"action_{action}" not in ui_source, action
    # The wired chat bindings the baseline credits are really there.
    chat = (UI_DIR / "screens/chat_screen.py").read_text(encoding="utf-8")
    for needle in ('"ctrl+q"', '"f2"', '"f3"', '"f4"', '"f5"', '"escape"'):
        assert needle in chat, needle
    assert 'query_one("#chat-input").focus()' in chat
    finding = {f.id: f for f in baseline.findings}["F-03"]
    assert "f1" in finding.detail and "ctrl+k" in finding.detail


def test_no_color_is_claimed_but_never_read(baseline):
    progress = (PKG_DIR / "core/progress.py").read_text(encoding="utf-8")
    assert "NO_COLOR" in progress  # the docstring claim
    package = "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in sorted(PKG_DIR.rglob("*.py"))
        if "__pycache__" not in p.parts
    )
    # No code anywhere reads NO_COLOR from the environment.
    assert not re.search(r"environ[^\n]*NO_COLOR|getenv\([^\n]*NO_COLOR", package)
    assert "isatty" in progress
    assert {f.id: f for f in baseline.findings}["F-04"].name.startswith("NO_COLOR")


def test_images_carry_no_alt_text_today(baseline):
    chat = (UI_DIR / "screens/chat_screen.py").read_text(encoding="utf-8")
    assert 'id="agent-image"' in chat
    assert "agent_image_widget.image" in chat or "update_agent_image" in chat
    splash = (UI_DIR / "screens/splash_screen.py").read_text(encoding="utf-8")
    assert "THE VIKING AI" in splash  # the caption that does exist
    assert "set_timer(2.0" in splash  # the brief auto-advance S-02 cites
    sr = {c.id: c for c in baseline.screen_reader_checks}
    assert sr["S-02"].verdict == "FAIL"
    assert sr["S-03"].verdict == "FAIL"


def test_setup_fields_have_visible_labels(baseline):
    setup = (UI_DIR / "screens/setup_screen.py").read_text(encoding="utf-8")
    # A Label step precedes the API-key input in compose order.
    assert setup.index('Label("2. Offer your Tribute') < setup.index('id="api-key-input"')
    assert 'id="save-btn"' in setup and "disabled=True" in setup
    sr = {c.id: c for c in baseline.screen_reader_checks}
    assert sr["S-04"].verdict == "PARTIAL"


def test_render_covers_every_entry(baseline):
    text = render_markdown(baseline)
    for check in baseline.keyboard_checks + baseline.screen_reader_checks:
        assert check.id in text and check.name in text
    for entry in baseline.contrast_entries:
        assert entry.theme in text
        assert str(entry.ratio("text_on_background")) in text
    for finding in baseline.findings:
        assert finding.id in text and finding.detail in text


def _tampered(mutator):
    data = copy.deepcopy(load_resource("accessibility_baseline.yaml"))
    mutator(data)
    return data


def test_validation_rejects_a_pass_on_inspected_evidence():
    data = _tampered(lambda d: d["keyboard_checks"][0].update(evidence_kind="code-inspected"))
    problems = validate_baseline(data)
    assert any("PASS" in p and "local-measured" in p for p in problems)
    with pytest.raises(ValidationError):
        load_baseline(data)


def test_validation_rejects_a_contrast_pass_the_numbers_refute():
    data = _tampered(lambda d: d["contrast_entries"][0].update(verdict="PASS"))
    problems = validate_baseline(data)
    assert any("PASS" in p for p in problems)


def test_validation_rejects_a_finding_without_part_viii():
    data = _tampered(lambda d: d["findings"][0].update(owner="Part II"))
    problems = validate_baseline(data)
    assert any("Part VIII" in p for p in problems)


def test_validation_rejects_nonsequential_ids():
    data = _tampered(lambda d: d["screen_reader_checks"][1].update(id="S-09"))
    problems = validate_baseline(data)
    assert any("sequential" in p for p in problems)
