"""The TUI Redesign Charter (All-Features roadmap slice M-171).

Part VIII — The Beautiful Face — opens here. The
roadmap's words: *every screen re-judged against
M-004's kindness rules and the Visual Design Lawbook;
a written verdict per screen before code moves.*

This module is that judgement, held as data:

* A validated charter record
  (``mythic_agent/data/tui_redesign_charter.yaml``)
  naming the eight TUI surfaces that actually ship —
  the three Textual screens (splash, setup wizard,
  main chat), the three modal screens (command
  approval, GitHub config, subagent picker), the
  subagent editor panel embedded in setup, and the
  terminal chat loop, the app's non-Textual face —
  each named by the file and symbol that carry it,
  so no screen is invented and none is skipped.
* Every screen carries one judgement per kindness
  principle that binds Part VIII — the M-004
  charter's own ``for_part("VIII")`` set, K-01..K-07
  and K-09 (K-08 binds Parts II, V, VII and X in
  M-004's own table, so it is not re-judged here) —
  and one judgement per Visual Design Lawbook rule
  this charter cites (L-01..L-06, distilled from the
  Lawbook's Prime Directive and the standing design
  doctrine: a themed element must have a measurable
  job; when theme fights task, ornament is cut
  before information architecture; colour is never
  the only status signal; the primary task is
  obvious at a glance; ornament and accent stay
  inside their budgets; surfaces carry depth and
  text stays legible). Each judgement stands as
  ``holds``, ``strains``, ``fails`` or
  ``not-engaged``, with its evidence note in plain
  words.
* A screen's verdict is DERIVED from its judgements,
  never chosen: two or more ``fails`` derive
  ``rebuild``; exactly one ``fail``, or four or more
  ``strains``, derives ``repair``; anything cleaner
  derives ``keep``. The stored verdict must equal
  the derived one, and the charter's overall verdict
  is derived from the screens' verdicts the same
  way — a charter cannot soften its own findings.
* Every screen names the Part VIII slices that own
  its follow-through (M-172..M-200), so the verdict
  lands on a named road before any code moves.

Shape precedent: this is a charter slice, built in
the M-004 / M-005 charter shape exactly (a core
module, a data yaml holding the charter record, and
pure tests), with the M-016 accessibility baseline's
verdict discipline and the part gates' purity rule.
No agent layer is owed and none is built: a charter
holds judgements as data, rides no live Agent road,
and — by its own order — moves no screen code at
all. The redesign itself belongs to the Part VIII
slices the charter names.

Honesty rules, enforced by the validator and pinned
by tests:

* The evidence kind is ``code-inspected`` and no
  stronger claim is made anywhere in the record:
  every judgement was read off the shipped screens'
  own code (and the M-016 baseline's measured
  findings, cited in the notes where they carry
  weight). No user was tested, no screen was run
  under a screen reader by this slice, and no
  verdict claims a measurement this slice did not
  make.
* The screens are the tree's own: the tests prove
  live that every named surface file exists and
  defines the symbol the record names.
* The kindness set is M-004's own: the tests prove
  live that :data:`KINDNESS_IDS` is exactly the set
  the shipped M-004 charter binds on Part VIII.
"""

from __future__ import annotations

__all__ = [
    "CHARTER_RESOURCE",
    "CHARTER_SCHEMA",
    "CHARTER_SLICE",
    "EVIDENCE_KINDS",
    "KINDNESS_IDS",
    "LAWBOOK_IDS",
    "OVERALL_VERDICTS",
    "PLAIN_EXPLANATION",
    "SCREEN_KINDS",
    "SCREENS",
    "STANDINGS",
    "TUI_REDESIGN_CHARTER_SLICE",
    "VERDICTS",
    "Any",
    "Charter",
    "Dict",
    "Judgement",
    "LawbookRule",
    "List",
    "Optional",
    "Panel",
    "ScreenReview",
    "Tuple",
    "charter_record",
    "derive_overall",
    "derive_panel",
    "derived_verdict_for",
    "load_charter",
    "plain_words",
    "render_markdown",
    "validate_charter",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the charter data file inside ``mythic_agent/data``.
CHARTER_RESOURCE = "tui_redesign_charter.yaml"

#: The only schema this loader accepts.
CHARTER_SCHEMA = "mythic.tui_redesign_charter/1"

#: The slice that owns this charter.
CHARTER_SLICE = "M-171"

#: The longer name other layers cite for this slice.
TUI_REDESIGN_CHARTER_SLICE = CHARTER_SLICE

#: The TUI surfaces that ship, in the order a user meets them.
SCREENS = (
    "splash",
    "setup_wizard",
    "main_chat",
    "command_approval",
    "github_config",
    "subagent_picker",
    "subagent_editor",
    "terminal_loop",
)

#: The kinds a reviewed surface may be.
SCREEN_KINDS = ("screen", "modal", "panel", "terminal")

#: The M-004 kindness principles binding Part VIII, in charter order.
KINDNESS_IDS = (
    "K-01", "K-02", "K-03", "K-04",
    "K-05", "K-06", "K-07", "K-09",
)

#: The Visual Design Lawbook rules this charter judges by.
LAWBOOK_IDS = ("L-01", "L-02", "L-03", "L-04", "L-05", "L-06")

#: The standings one judgement may carry.
STANDINGS = ("holds", "strains", "fails", "not-engaged")

#: The verdicts one screen may derive.
VERDICTS = ("keep", "repair", "rebuild")

#: The overall verdicts the whole charter may derive.
OVERALL_VERDICTS = ("holds", "repair-first", "rebuild-where-named")

#: Evidence kinds a charter judgement may honestly claim.
EVIDENCE_KINDS = ("code-inspected",)

PLAIN_EXPLANATION = (
    "The TUI redesign charter: every screen that "
    "ships — splash, setup wizard, main chat, the "
    "three modals, the subagent editor panel and the "
    "terminal loop — re-judged against M-004's "
    "kindness rules that bind Part VIII and the "
    "Visual Design Lawbook, one written judgement "
    "per rule per screen, each screen's verdict "
    "derived from its judgements and its redesign "
    "owned by named Part VIII slices, before any "
    "screen code moves. The charter judges from the "
    "shipped code alone and claims no measurement "
    "it did not make."
)

_ID_RE = re.compile(r"^S-\d{2}$")
_SLICE_RE = re.compile(r"^M-\d{3}$")


@dataclass(frozen=True)
class LawbookRule:
    """One Visual Design Lawbook rule the charter judges by."""

    id: str
    name: str
    rule: str
    check: str


@dataclass(frozen=True)
class Judgement:
    """One rule judged on one screen: standing plus evidence note."""

    ref: str
    standing: str
    note: str


@dataclass(frozen=True)
class ScreenReview:
    """One shipped surface, re-judged whole, with its verdict."""

    id: str
    key: str
    title: str
    kind: str
    surface: str
    symbol: str
    evidence: str
    kindness: Tuple[Judgement, ...]
    lawbook: Tuple[Judgement, ...]
    verdict: str
    direction: str
    owning_slices: Tuple[str, ...]

    def judgements(self) -> Tuple[Judgement, ...]:
        """Every judgement on this screen, kindness then Lawbook."""
        return self.kindness + self.lawbook

    def fails(self) -> int:
        """How many judgements on this screen fail outright."""
        return sum(1 for j in self.judgements() if j.standing == "fails")

    def strains(self) -> int:
        """How many judgements on this screen strain."""
        return sum(1 for j in self.judgements() if j.standing == "strains")

    def derived_verdict(self) -> str:
        """The verdict this screen's judgements derive."""
        return derived_verdict_for(self.fails(), self.strains())

    def judgement(self, ref: str) -> Judgement:
        """The judgement carrying rule *ref* (KeyError if absent)."""
        for judgement in self.judgements():
            if judgement.ref == ref:
                return judgement
        raise KeyError(f"no judgement {ref!r} on screen {self.key!r}")


@dataclass(frozen=True)
class Panel:
    """The charter's derived totals: the findings at a glance."""

    total_screens: int
    keeps: int
    repairs: int
    rebuilds: int
    total_judgements: int
    holds: int
    strains: int
    fails: int
    not_engaged: int
    overall: str


@dataclass(frozen=True)
class Charter:
    """The validated TUI redesign charter: verdicts before code."""

    chartered: str
    binding_on: str
    source_note: str
    order: str
    evidence_kind: str
    overall_verdict: str
    lawbook: Tuple[LawbookRule, ...]
    screens: Tuple[ScreenReview, ...]

    def screen(self, key: str) -> ScreenReview:
        """Return the review of screen *key* (KeyError if absent)."""
        for review in self.screens:
            if review.key == key:
                return review
        raise KeyError(f"no screen {key!r}")

    def screen_keys(self) -> Tuple[str, ...]:
        """The reviewed screens, in the order a user meets them."""
        return tuple(review.key for review in self.screens)

    def verdict_counts(self) -> Tuple[int, int, int]:
        """(keeps, repairs, rebuilds) across the whole charter."""
        keeps = sum(1 for s in self.screens if s.verdict == "keep")
        repairs = sum(1 for s in self.screens if s.verdict == "repair")
        rebuilds = sum(1 for s in self.screens if s.verdict == "rebuild")
        return (keeps, repairs, rebuilds)


def derived_verdict_for(fails: int, strains: int) -> str:
    """The verdict a screen's own counts derive, never chosen.

    Two or more outright failures mean the screen is
    rebuilt; exactly one failure, or strain on four
    or more rules, means it is repaired before new
    features land on it; anything cleaner is kept.
    """
    if fails >= 2:
        return "rebuild"
    if fails == 1 or strains >= 4:
        return "repair"
    return "keep"


def derive_overall(verdicts: Tuple[str, ...]) -> str:
    """The charter's overall verdict, derived from its screens."""
    if "rebuild" in verdicts:
        return "rebuild-where-named"
    if "repair" in verdicts:
        return "repair-first"
    return "holds"


def derive_panel(charter: Charter) -> Panel:
    """Derive the charter's panel from its screens' judgements."""
    keeps, repairs, rebuilds = charter.verdict_counts()
    judgements = [j for s in charter.screens for j in s.judgements()]
    return Panel(
        total_screens=len(charter.screens),
        keeps=keeps,
        repairs=repairs,
        rebuilds=rebuilds,
        total_judgements=len(judgements),
        holds=sum(1 for j in judgements if j.standing == "holds"),
        strains=sum(1 for j in judgements if j.standing == "strains"),
        fails=sum(1 for j in judgements if j.standing == "fails"),
        not_engaged=sum(
            1 for j in judgements if j.standing == "not-engaged"),
        overall=derive_overall(
            tuple(s.verdict for s in charter.screens)),
    )


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _judgement_problems(rows: Any, wanted: Tuple[str, ...], label: str,
                        screen_key: Any) -> List[str]:
    """Every problem in one screen's judgement rows for *wanted*."""
    problems: List[str] = []
    if not isinstance(rows, list):
        return [f"screen {screen_key}: {label} must be a list"]
    refs = [r.get("ref") for r in rows if isinstance(r, dict)]
    if tuple(refs) != wanted:
        problems.append(
            f"screen {screen_key}: {label} refs must be exactly "
            f"{wanted} in order, got {refs}")
    for row in rows:
        if not isinstance(row, dict):
            problems.append(
                f"screen {screen_key}: {label} entry is not a "
                f"mapping: {row!r}")
            continue
        ref = row.get("ref")
        if row.get("standing") not in STANDINGS:
            problems.append(
                f"screen {screen_key}: {label} {ref}: standing must "
                f"be one of {STANDINGS}, got {row.get('standing')!r}")
        if not _nonempty(row.get("note")):
            problems.append(
                f"screen {screen_key}: {label} {ref}: note must be "
                "non-empty - a judgement without its evidence is "
                "not a judgement")
    return problems


def validate_charter(data: Any) -> List[str]:
    """Return a list of human-readable problems with charter *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"charter root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != CHARTER_SCHEMA:
        problems.append(
            f"schema must be {CHARTER_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != CHARTER_SLICE:
        problems.append(
            f"slice must be {CHARTER_SLICE!r}, got {data.get('slice')!r}")
    for key in ("chartered", "binding_on", "source_note", "order"):
        if not _nonempty(data.get(key)):
            problems.append(f"{key} must be a non-empty string")
    if data.get("evidence_kind") not in EVIDENCE_KINDS:
        problems.append(
            f"evidence_kind must be one of {EVIDENCE_KINDS} - the "
            f"charter judges from the shipped code and claims no "
            f"stronger evidence, got {data.get('evidence_kind')!r}")
    if data.get("overall_verdict") not in OVERALL_VERDICTS:
        problems.append(
            f"overall_verdict must be one of {OVERALL_VERDICTS}, "
            f"got {data.get('overall_verdict')!r}")

    lawbook = data.get("lawbook")
    if not isinstance(lawbook, list) or not lawbook:
        problems.append("lawbook must be a non-empty list")
        lawbook = []
    law_ids = [r.get("id") for r in lawbook if isinstance(r, dict)]
    if tuple(law_ids) != LAWBOOK_IDS:
        problems.append(
            f"lawbook rules must be exactly {LAWBOOK_IDS} in order, "
            f"got {law_ids}")
    for rule in lawbook:
        if not isinstance(rule, dict):
            problems.append(f"lawbook entry is not a mapping: {rule!r}")
            continue
        rid = rule.get("id")
        for key in ("name", "rule"):
            if not _nonempty(rule.get(key)):
                problems.append(f"lawbook {rid}: {key} must be non-empty")
        check = rule.get("check")
        if not _nonempty(check):
            problems.append(f"lawbook {rid}: check must be non-empty")
        elif not check.rstrip().endswith("?"):
            problems.append(
                f"lawbook {rid}: check must be a question (end "
                "with '?') - a reviewer answers it yes or no")

    screens = data.get("screens")
    if not isinstance(screens, list) or not screens:
        problems.append("screens must be a non-empty list")
        screens = []
    keys = [s.get("key") for s in screens if isinstance(s, dict)]
    if tuple(keys) != SCREENS:
        problems.append(
            f"screens must be exactly {SCREENS} in order - every "
            f"screen that ships, none invented, none skipped - "
            f"got {keys}")
    verdicts: List[str] = []
    for position, review in enumerate(screens, start=1):
        if not isinstance(review, dict):
            problems.append(f"screen entry is not a mapping: {review!r}")
            continue
        key = review.get("key")
        expected_id = f"S-{position:02d}"
        sid = review.get("id")
        if not isinstance(sid, str) or not _ID_RE.match(sid):
            problems.append(f"screen {key}: id must look like 'S-01'")
        elif sid != expected_id:
            problems.append(
                f"screen {key}: ids must be sequential, expected "
                f"{expected_id}, got {sid}")
        if review.get("kind") not in SCREEN_KINDS:
            problems.append(
                f"screen {key}: kind must be one of {SCREEN_KINDS}, "
                f"got {review.get('kind')!r}")
        for field in ("title", "evidence", "direction"):
            if not _nonempty(review.get(field)):
                problems.append(f"screen {key}: {field} must be non-empty")
        surface = review.get("surface")
        if not _nonempty(surface) or not str(surface).endswith(".py"):
            problems.append(
                f"screen {key}: surface must name the shipped .py "
                f"file that carries it, got {surface!r}")
        if not _nonempty(review.get("symbol")):
            problems.append(f"screen {key}: symbol must be non-empty")
        problems.extend(_judgement_problems(
            review.get("kindness"), KINDNESS_IDS, "kindness", key))
        problems.extend(_judgement_problems(
            review.get("lawbook"), LAWBOOK_IDS, "lawbook", key))
        owning = review.get("owning_slices")
        if not isinstance(owning, list) or not owning:
            problems.append(
                f"screen {key}: owning_slices must be a non-empty "
                "list - every verdict lands on a named Part VIII road")
        else:
            for sid2 in owning:
                if not isinstance(sid2, str) or not _SLICE_RE.match(sid2) \
                        or not ("M-172" <= sid2 <= "M-200"):
                    problems.append(
                        f"screen {key}: owning slice {sid2!r} must "
                        "name a Part VIII slice (M-172..M-200)")
        verdict = review.get("verdict")
        if verdict not in VERDICTS:
            problems.append(
                f"screen {key}: verdict must be one of {VERDICTS}, "
                f"got {verdict!r}")
        else:
            verdicts.append(verdict)
            rows = []
            for field in ("kindness", "lawbook"):
                named = review.get(field)
                if isinstance(named, list):
                    rows.extend(
                        r for r in named if isinstance(r, dict))
            fails = sum(
                1 for r in rows if r.get("standing") == "fails")
            strains = sum(
                1 for r in rows if r.get("standing") == "strains")
            derived = derived_verdict_for(fails, strains)
            if verdict != derived:
                problems.append(
                    f"screen {key}: verdict is derived, never "
                    f"chosen - {fails} fails and {strains} strains "
                    f"derive {derived!r}, got {verdict!r}")
    if len(verdicts) == len(screens) and screens:
        derived_overall = derive_overall(tuple(verdicts))
        if data.get("overall_verdict") in OVERALL_VERDICTS \
                and data.get("overall_verdict") != derived_overall:
            problems.append(
                f"overall_verdict is derived, never chosen - the "
                f"screens' verdicts derive {derived_overall!r}, got "
                f"{data.get('overall_verdict')!r}")
    return problems


def _to_judgements(rows: List[Dict[str, Any]]) -> Tuple[Judgement, ...]:
    return tuple(
        Judgement(ref=r["ref"], standing=r["standing"], note=r["note"])
        for r in rows)


def _to_charter(data: Dict[str, Any]) -> Charter:
    return Charter(
        chartered=data["chartered"],
        binding_on=data["binding_on"],
        source_note=data["source_note"],
        order=data["order"],
        evidence_kind=data["evidence_kind"],
        overall_verdict=data["overall_verdict"],
        lawbook=tuple(
            LawbookRule(id=r["id"], name=r["name"], rule=r["rule"],
                        check=r["check"])
            for r in data["lawbook"]),
        screens=tuple(
            ScreenReview(
                id=s["id"], key=s["key"], title=s["title"],
                kind=s["kind"], surface=s["surface"],
                symbol=s["symbol"], evidence=s["evidence"],
                kindness=_to_judgements(s["kindness"]),
                lawbook=_to_judgements(s["lawbook"]),
                verdict=s["verdict"], direction=s["direction"],
                owning_slices=tuple(s["owning_slices"]))
            for s in data["screens"]),
    )


def load_charter(data: Optional[Dict[str, Any]] = None) -> Charter:
    """Load and validate the shipped TUI redesign charter (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed charter.
    """
    raw = data if data is not None else load_resource(CHARTER_RESOURCE)
    problems = validate_charter(raw)
    if problems:
        raise ValidationError(
            "tui redesign charter failed validation: "
            + "; ".join(problems))
    return _to_charter(raw)  # type: ignore[arg-type]


def plain_words(charter: Charter) -> str:
    """The charter stated in plain words, from its own accessors."""
    panel = derive_panel(charter)
    return (
        f"TUI redesign charter ({CHARTER_SLICE}): "
        f"{panel.total_screens} screens re-judged against "
        f"M-004's kindness rules and the Visual Design "
        f"Lawbook ({panel.total_judgements} judgements: "
        f"{panel.holds} hold, {panel.strains} strain, "
        f"{panel.fails} fail, {panel.not_engaged} not "
        f"engaged) - {panel.keeps} screens keep, "
        f"{panel.repairs} repair, {panel.rebuilds} "
        f"rebuild; overall verdict "
        f"{panel.overall}, before any screen code moves.")


def charter_record(charter: Charter) -> Dict[str, Any]:
    """The session-news record of the charter."""
    panel = derive_panel(charter)
    return {
        "type": "tui_redesign_charter",
        "slice": CHARTER_SLICE,
        "screens": list(charter.screen_keys()),
        "verdicts": {s.key: s.verdict for s in charter.screens},
        "overall": panel.overall,
        "judgements": panel.total_judgements,
        "fails": panel.fails,
        "plain": plain_words(charter),
    }


def render_markdown(charter: Charter) -> str:
    """Render the charter as markdown: law, verdicts, directions.

    Built from the charter's own accessors and
    :func:`derive_panel`, so the rendered page itself
    is computed from the same values the tests pin.
    """
    panel = derive_panel(charter)
    lines = [
        "# The TUI Redesign Charter (M-171)",
        "",
        f"*Chartered {charter.chartered}. Slice M-171 of the "
        "All-Features road, opening Part VIII.*",
        "",
        charter.source_note,
        "",
        f"**Binding on:** {charter.binding_on}",
        "",
        f"**The order:** {charter.order}",
        "",
        "## The Lawbook rules judged by",
        "",
    ]
    for rule in charter.lawbook:
        lines.append(f"### {rule.id} - {rule.name}")
        lines.append("")
        lines.append(rule.rule)
        lines.append("")
        lines.append(f"*Review:* {rule.check}")
        lines.append("")
    lines += ["## Verdicts, per screen", ""]
    for review in charter.screens:
        lines.append(
            f"### {review.id} - {review.title} ({review.key}): "
            f"**{review.verdict}**")
        lines.append("")
        lines.append(
            f"*Surface:* `{review.surface}` - `{review.symbol}`. "
            f"{review.evidence}")
        lines.append("")
        for judgement in review.judgements():
            lines.append(
                f"- {judgement.ref}: {judgement.standing} - "
                f"{judgement.note}")
        lines.append("")
        lines.append(
            f"*Direction (owned by {', '.join(review.owning_slices)}):* "
            f"{review.direction}")
        lines.append("")
    lines += [
        "## The charter in plain words",
        "",
        plain_words(charter),
        "",
        f"*{panel.keeps} keep, {panel.repairs} repair, "
        f"{panel.rebuilds} rebuild of {panel.total_screens} "
        f"screens; overall: {panel.overall}.*",
        "",
    ]
    return "\n".join(lines)
