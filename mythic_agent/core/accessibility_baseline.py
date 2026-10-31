"""The Accessibility Baseline (All-Features roadmap slice M-016).

The "before" picture for Part VIII, measured — not asserted — on
2026-10-31: a keyboard-only task completion pass, a screen-reader
pass over the TUI, and a contrast audit of every shipped theme.
Each check carries a verdict in ``PASS / PARTIAL / FAIL /
NOT PROVEN`` and the kind of evidence behind it; following the
platform truth table's rule (M-013), the validator refuses a
``PASS`` verdict on anything but ``local-measured`` evidence, so a
code inspection or a documentation promise can never be dressed up
as a completed accessibility pass. A real screen-reader pass with
NVDA, JAWS, VoiceOver, or Orca has never been run — that check is
honestly ``NOT PROVEN`` here, and Part VIII (whose M-199 gate
re-runs this baseline's tests) owns closing it.

What the baseline found, plainly:

* The work itself is keyboard-completable: the CLI is stdin/stdout
  only, the terminal chat loop is prompt_toolkit keys, and the
  security approval dialog — the one modal that gates tool use —
  is fully keyboard-driven (Allow is focused on open, Tab cycles
  Allow/Reject, Enter approves, Escape rejects), all measured
  this tick with ``pilot.press`` and no mouse click.
* The shortcut registry advertises more TUI keys than any screen
  actually binds (help, clear, tabs, command palette, sidebar,
  scroll, focus-input): only quit and the chat screen's F-keys and
  Escape are wired. That gap is finding F-03.
* Contrast (WCAG 2.x ratios computed from the live themes):
  body text passes everywhere, but the ``muted`` role fails the
  4.5:1 AA bar for normal text in all three themes, and
  viking_dark's ``error`` role fails even the 3:1 large-text bar.
* The agent portrait carries no alternative text at all, the
  splash screen's block-character art has no text alternative,
  and ``progress.py`` claims NO_COLOR support it never reads.

Data lives in ``mythic_agent/data/accessibility_baseline.yaml``;
the contrast ratios recorded there are recomputed from the live
themes by this module's own WCAG functions in the slice's tests,
so the audit cannot drift away from the shipped colours.
"""

from __future__ import annotations

__all__ = [
    "AA_LARGE",
    "AA_NORMAL",
    "CATALOG_RESOURCE",
    "CATALOG_SCHEMA",
    "EVIDENCE_KINDS",
    "VERDICTS",
    "AccessibilityBaseline",
    "Any",
    "Check",
    "ContrastEntry",
    "Dict",
    "Finding",
    "List",
    "Optional",
    "Tuple",
    "contrast_ratio",
    "load_baseline",
    "relative_luminance",
    "render_markdown",
    "validate_baseline",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the baseline data file inside ``mythic_agent/data``.
CATALOG_RESOURCE = "accessibility_baseline.yaml"

#: The only schema this loader accepts.
CATALOG_SCHEMA = "mythic.accessibility_baseline/1"

VERDICTS = ("PASS", "PARTIAL", "FAIL", "NOT PROVEN")

EVIDENCE_KINDS = ("local-measured", "code-inspected", "none")

#: WCAG 2.x contrast bars: normal text and large text, level AA.
AA_NORMAL = 4.5
AA_LARGE = 3.0

_CHECK_ID_RE = re.compile(r"^[KS]-\d{2}$")
_CONTRAST_ID_RE = re.compile(r"^C-\d{2}$")
_FINDING_ID_RE = re.compile(r"^F-\d{2}$")

#: The contrast pairs the audit records for every theme, in order.
CONTRAST_PAIRS = (
    "text_on_background",
    "text_on_surface",
    "muted_on_background",
    "muted_on_surface",
    "primary_on_background",
    "success_on_background",
    "warning_on_background",
    "error_on_background",
)


def _channel(value: float) -> float:
    return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    """WCAG 2.x relative luminance of an ``#rrggbb`` colour."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(first: str, second: str) -> float:
    """WCAG 2.x contrast ratio between two ``#rrggbb`` colours."""
    lum1, lum2 = relative_luminance(first), relative_luminance(second)
    hi, lo = max(lum1, lum2), min(lum1, lum2)
    return (hi + 0.05) / (lo + 0.05)


@dataclass(frozen=True)
class Check:
    """One measured accessibility check (keyboard or screen-reader)."""

    id: str
    area: str
    name: str
    verdict: str
    evidence_kind: str
    evidence: str


@dataclass(frozen=True)
class ContrastEntry:
    """The audited contrast ratios for one shipped theme."""

    id: str
    theme: str
    verdict: str
    ratios: Tuple[Tuple[str, float], ...]

    def ratio(self, pair: str) -> float:
        """The recorded ratio for one pair, e.g. ``text_on_background``."""
        return dict(self.ratios)[pair]

    def worst(self) -> Tuple[str, float]:
        """The (pair, ratio) with the lowest recorded contrast."""
        return min(self.ratios, key=lambda item: item[1])


@dataclass(frozen=True)
class Finding:
    """One gap the baseline hands to Part VIII."""

    id: str
    name: str
    detail: str
    owner: str


@dataclass(frozen=True)
class AccessibilityBaseline:
    """The validated baseline: checks, contrast entries, findings."""

    recorded: str
    scope_note: str
    keyboard_checks: Tuple[Check, ...]
    screen_reader_checks: Tuple[Check, ...]
    contrast_entries: Tuple[ContrastEntry, ...]
    findings: Tuple[Finding, ...]

    def counts(self) -> Tuple[int, int, int, int]:
        """(keyboard checks, screen-reader checks, contrast entries, findings)."""
        return (
            len(self.keyboard_checks),
            len(self.screen_reader_checks),
            len(self.contrast_entries),
            len(self.findings),
        )

    def keyboard_ids(self) -> Tuple[str, ...]:
        """Ids of the keyboard checks, in baseline order."""
        return tuple(c.id for c in self.keyboard_checks)

    def screen_reader_ids(self) -> Tuple[str, ...]:
        """Ids of the screen-reader checks, in baseline order."""
        return tuple(c.id for c in self.screen_reader_checks)

    def theme_names(self) -> Tuple[str, ...]:
        """Names of the audited themes, in baseline order."""
        return tuple(e.theme for e in self.contrast_entries)

    def finding_ids(self) -> Tuple[str, ...]:
        """Ids of the findings, in baseline order."""
        return tuple(f.id for f in self.findings)

    def verdicts(self) -> Tuple[str, ...]:
        """Every check and contrast verdict, in baseline order."""
        checks = self.keyboard_checks + self.screen_reader_checks
        return tuple(c.verdict for c in checks) + tuple(
            e.verdict for e in self.contrast_entries
        )


def _check_checks(entries: Any, prefix: str, area: str, problems: List[str]) -> None:
    if not isinstance(entries, list) or not entries:
        problems.append(f"{area} checks must be a non-empty list")
        return
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"{area} entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"{prefix}-{position:02d}"
        if not isinstance(eid, str) or not _CHECK_ID_RE.match(eid):
            problems.append(f"{area} entry {eid!r}: id must look like '{prefix}-01'")
        elif eid != expected:
            problems.append(
                f"{area} entry {eid}: ids must be sequential, expected {expected}"
            )
        if entry.get("area") != area:
            problems.append(f"{area} entry {eid}: area must be {area!r}")
        verdict = entry.get("verdict")
        if verdict not in VERDICTS:
            problems.append(f"{area} entry {eid}: verdict {verdict!r} not in {VERDICTS}")
        kind = entry.get("evidence_kind")
        if kind not in EVIDENCE_KINDS:
            problems.append(
                f"{area} entry {eid}: evidence_kind {kind!r} not in {EVIDENCE_KINDS}"
            )
        elif verdict == "PASS" and kind != "local-measured":
            problems.append(
                f"{area} entry {eid}: a PASS verdict requires local-measured "
                "evidence — inspection or documentation can never be a pass"
            )
        for key in ("name", "evidence"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"{area} entry {eid}: {key} must be non-empty")


def _check_contrast(entries: Any, problems: List[str]) -> None:
    if not isinstance(entries, list) or not entries:
        problems.append("contrast_entries must be a non-empty list")
        return
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"contrast entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"C-{position:02d}"
        if not isinstance(eid, str) or not _CONTRAST_ID_RE.match(eid):
            problems.append(f"contrast entry {eid!r}: id must look like 'C-01'")
        elif eid != expected:
            problems.append(
                f"contrast entry {eid}: ids must be sequential, expected {expected}"
            )
        if not isinstance(entry.get("theme"), str) or not entry["theme"]:
            problems.append(f"contrast entry {eid}: theme must be non-empty")
        if entry.get("verdict") not in VERDICTS:
            problems.append(
                f"contrast entry {eid}: verdict {entry.get('verdict')!r} not in {VERDICTS}"
            )
        ratios = entry.get("ratios")
        if not isinstance(ratios, dict):
            problems.append(f"contrast entry {eid}: ratios must be a mapping")
            continue
        if tuple(ratios) != CONTRAST_PAIRS:
            problems.append(
                f"contrast entry {eid}: ratio pairs must be exactly "
                f"{CONTRAST_PAIRS} in order, got {tuple(ratios)}"
            )
        for pair, value in ratios.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                problems.append(f"contrast entry {eid}: ratio {pair} must be a number")
            elif not 1.0 < float(value) <= 21.0:
                problems.append(
                    f"contrast entry {eid}: ratio {pair}={value} outside (1, 21]"
                )
        # A theme whose worst recorded pair fails even the large-text
        # bar can never claim PASS or PARTIAL-by-omission: it is FAIL
        # or PARTIAL with the failure visible in the numbers.
        numeric = [float(v) for v in ratios.values() if isinstance(v, (int, float))]
        if numeric and entry.get("verdict") == "PASS" and min(numeric) < AA_NORMAL:
            problems.append(
                f"contrast entry {eid}: verdict PASS but a recorded pair "
                f"({min(numeric)}) is below the AA normal-text bar {AA_NORMAL}"
            )


def _check_findings(entries: Any, problems: List[str]) -> None:
    if not isinstance(entries, list) or len(entries) < 4:
        problems.append("findings must list at least four findings")
        return
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"finding entry is not a mapping: {entry!r}")
            continue
        eid = entry.get("id")
        expected = f"F-{position:02d}"
        if not isinstance(eid, str) or not _FINDING_ID_RE.match(eid):
            problems.append(f"finding entry {eid!r}: id must look like 'F-01'")
        elif eid != expected:
            problems.append(
                f"finding entry {eid}: ids must be sequential, expected {expected}"
            )
        for key in ("name", "detail", "owner"):
            if not isinstance(entry.get(key), str) or not entry[key]:
                problems.append(f"finding entry {eid}: {key} must be non-empty")
        owner = entry.get("owner")
        if isinstance(owner, str) and "Part VIII" not in owner:
            problems.append(
                f"finding entry {eid}: owner must name Part VIII (the "
                "part this baseline is the 'before' for)"
            )


def validate_baseline(data: Any) -> List[str]:
    """Return a list of human-readable problems with baseline *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"baseline root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != CATALOG_SCHEMA:
        problems.append(f"schema must be {CATALOG_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != "M-016":
        problems.append(f"slice must be 'M-016', got {data.get('slice')!r}")
    for key in ("recorded", "scope_note"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")
    _check_checks(data.get("keyboard_checks"), "K", "keyboard-only", problems)
    _check_checks(data.get("screen_reader_checks"), "S", "screen-reader", problems)
    _check_contrast(data.get("contrast_entries"), problems)
    _check_findings(data.get("findings"), problems)
    return problems


def _to_check(entry: Dict[str, Any]) -> Check:
    return Check(
        id=entry["id"],
        area=entry["area"],
        name=entry["name"],
        verdict=entry["verdict"],
        evidence_kind=entry["evidence_kind"],
        evidence=entry["evidence"],
    )


def _to_baseline(data: Dict[str, Any]) -> AccessibilityBaseline:
    return AccessibilityBaseline(
        recorded=data["recorded"],
        scope_note=data["scope_note"],
        keyboard_checks=tuple(_to_check(c) for c in data["keyboard_checks"]),
        screen_reader_checks=tuple(_to_check(c) for c in data["screen_reader_checks"]),
        contrast_entries=tuple(
            ContrastEntry(
                id=e["id"],
                theme=e["theme"],
                verdict=e["verdict"],
                ratios=tuple((pair, float(e["ratios"][pair])) for pair in CONTRAST_PAIRS),
            )
            for e in data["contrast_entries"]
        ),
        findings=tuple(
            Finding(id=f["id"], name=f["name"], detail=f["detail"], owner=f["owner"])
            for f in data["findings"]
        ),
    )


def load_baseline(data: Optional[Dict[str, Any]] = None) -> AccessibilityBaseline:
    """Load and validate the shipped accessibility baseline (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed baseline.
    """
    raw = data if data is not None else load_resource(CATALOG_RESOURCE)
    problems = validate_baseline(raw)
    if problems:
        raise ValidationError(
            "accessibility baseline failed validation: " + "; ".join(problems)
        )
    return _to_baseline(raw)  # type: ignore[arg-type]


def render_markdown(baseline: AccessibilityBaseline) -> str:
    """Render the baseline as markdown.

    Built from :meth:`AccessibilityBaseline.counts`,
    :meth:`AccessibilityBaseline.keyboard_ids`,
    :meth:`AccessibilityBaseline.screen_reader_ids`,
    :meth:`AccessibilityBaseline.theme_names`,
    :meth:`AccessibilityBaseline.finding_ids`,
    :meth:`AccessibilityBaseline.verdicts`, each entry's
    :meth:`ContrastEntry.ratio` / :meth:`ContrastEntry.worst`, and
    this module's :func:`contrast_ratio` (applied to the AA bars
    below), so the rendered page is computed from the same
    accessors and functions the tests pin. (The live-theme
    recomputation lives in the tests, not here: ``core`` is
    UI-agnostic and may not import ``mythic_agent.ui``.)
    """
    n_kbd, n_sr, n_con, n_find = baseline.counts()
    lines = [
        "# Accessibility Baseline (M-016)",
        "",
        f"*Recorded {baseline.recorded}: {n_kbd} keyboard checks, "
        f"{n_sr} screen-reader checks, {n_con} contrast entries, "
        f"{n_find} findings. Verdicts: {', '.join(baseline.verdicts())}.*",
        "",
        baseline.scope_note,
        "",
        "## Keyboard-only",
        "",
    ]
    for check in baseline.keyboard_checks:
        lines.append(
            f"- {check.id} {check.name}: **{check.verdict}** "
            f"({check.evidence_kind}) — {check.evidence}"
        )
    lines += ["", "## Screen-reader pass", ""]
    for check in baseline.screen_reader_checks:
        lines.append(
            f"- {check.id} {check.name}: **{check.verdict}** "
            f"({check.evidence_kind}) — {check.evidence}"
        )
    lines += [
        "",
        "## Contrast audit (WCAG 2.x ratios)",
        "",
        f"AA bars: {AA_NORMAL}:1 normal text, {AA_LARGE}:1 large text. "
        f"A black-on-white sanity pair via contrast_ratio() reads "
        f"{contrast_ratio('#000000', '#ffffff'):.1f}:1; the slice's "
        f"tests recompute every recorded ratio from the live themes.",
        "",
    ]
    for entry in baseline.contrast_entries:
        worst_pair, worst_ratio = entry.worst()
        lines.append(
            f"- {entry.id} {entry.theme}: **{entry.verdict}** — "
            f"text/background {entry.ratio('text_on_background')}, "
            f"muted/background "
            f"{entry.ratio('muted_on_background')}, worst pair "
            f"{worst_pair} at {worst_ratio}."
        )
    lines += ["", "## Findings for Part VIII", ""]
    for finding in baseline.findings:
        lines.append(
            f"- {finding.id} {finding.name} ({finding.owner}): {finding.detail}"
        )
    lines += [
        "",
        "## The count, plainly",
        "",
        f"Keyboard: {', '.join(baseline.keyboard_ids())}.",
        f"Screen-reader: {', '.join(baseline.screen_reader_ids())}.",
        f"Themes: {', '.join(baseline.theme_names())}.",
        f"Findings: {', '.join(baseline.finding_ids())}.",
        "",
    ]
    return "\n".join(lines)
