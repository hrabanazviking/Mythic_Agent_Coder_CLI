"""Onboarding in five minutes (All-Features roadmap slice M-184).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *first run detects providers,
offers Kista key-keeping, walks one tiny real
task - success before configuration, always.*

What already ships, and what this slice adds:

* The shipped tree already knows its providers
  (the provider registry), already keeps keys in
  Kista (the key-custody layer, where the config
  holds references and Kista holds the keys), and
  already carries a first-run tutorial and a setup
  wizard. What nothing held is the *first run
  itself*, as checkable data: which providers a
  first run actually detected, by which named
  probe; the Kista offer, held as an offer with
  its answer; and the walk - one tiny real task,
  its steps held in order - under the one ordering
  rule the roadmap names. This slice is that book,
  in its own module; the shipped provider, Kista,
  tutorial and setup roads stand untouched behind
  seams, and this layer holds the first run in
  their shape, never rewriting them.
* Detection is DERIVED from named probes: every
  detection names the probe that looked - an
  environment key probe (which reads a key's name,
  never the key), a local door probe, a registry
  probe, a config reference probe - and the
  outcome that probe honestly returned, found or
  absent. Availability is never faked: a provider
  no probe found stands absent, named in its gaps.
* The Kista offer stands as DATA: an offer record
  holds the provider it was made for and the
  answer it was given - accepted, declined or
  still pending. The keys themselves are never
  held by this layer: a record naming a key,
  secret, token or password refuses BY NAME.
* The walk's steps stand HELD IN ORDER, and the
  ordering rule stands as data
  (:data:`SUCCESS_BEFORE_CONFIGURATION_RULE`):
  success before configuration, always. A walk
  whose configure step stands before its first
  success step - or any record claiming
  configuration comes first - refuses BY NAME.
  Configuration is offered after the first
  success, never required before it.
* The shipped data file (``mythic_agent/data/
  onboarding_five.yaml``) holds one example book
  in exactly the shape a real first-run file
  takes, a loader reads a first-run file anywhere
  on disk, detections and views are shaped as
  session news, and a small in-memory registry
  holds records one by one. The agent layer owns
  holding an onboarding book for a session and
  walking it. This layer reaches no live road:
  it detects nothing live, keeps no key, runs no
  task and configures nothing - it holds the
  first run as data and tells it.

Honesty rules, enforced here and pinned by tests:

* **Availability never faked.** A detection's
  outcome is the named probe's own answer; an
  unfound provider stands absent and named in
  its gaps, and no outcome is invented for it.
* **Keys never held.** An offer holds the offer
  and its answer alone; a record naming a key
  itself refuses by name.
* **Success before configuration, always.** A
  walk demanding configuration before the first
  success refuses by name; configuration is
  offered after, never required before.
* **The task is tiny and real.** The walk holds
  its steps in order - detect, walk, success,
  offer, configure - and the walked task is one
  small real task, named in its step, not a tour
  of imaginary screens.
"""

from __future__ import annotations

__all__ = [
    "DETECTION_OUTCOMES",
    "OFFER_DECISIONS",
    "ONBOARDING_FIVE_RESOURCE",
    "ONBOARDING_FIVE_SCHEMA",
    "ONBOARDING_FIVE_SLICE",
    "PLAIN_EXPLANATION",
    "PROBES",
    "SUCCESS_BEFORE_CONFIGURATION_RULE",
    "THE_ONBOARDING_FIVE_SLICE",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_FILTERS",
    "WALK_ACTION",
    "WALK_PHASES",
    "Any",
    "Dict",
    "List",
    "Optional",
    "DetectionRecord",
    "OfferRecord",
    "OnboardingBook",
    "OnboardingPanel",
    "OnboardingPanelRow",
    "OnboardingRegistry",
    "OnboardingVerdict",
    "OnboardingView",
    "OnboardingWalk",
    "OutcomeCount",
    "WalkStep",
    "book_record",
    "build_book",
    "build_detection",
    "build_offer",
    "build_panel",
    "build_row",
    "build_step",
    "build_verdict",
    "build_view",
    "derive_panel",
    "derive_verdict",
    "derive_walk",
    "detection_gaps",
    "detection_passes",
    "detection_plain_words",
    "detections_for_outcome",
    "format_book",
    "format_detection",
    "format_offer",
    "format_onboarding_five_screen",
    "format_panel",
    "format_verdict",
    "format_view",
    "format_walk",
    "inspect_onboarding_source",
    "load_onboarding_five",
    "load_onboarding_five_file",
    "normalize_decision",
    "normalize_outcome",
    "normalize_phase",
    "normalize_probe",
    "normalize_view_filter",
    "offer_record",
    "panel_plain_words",
    "panel_record",
    "parse_onboarding_args",
    "passing_detections",
    "plain_lines",
    "plain_words",
    "segment_of",
    "shown_detections",
    "step_record",
    "total_detections",
    "validate_book",
    "validate_detection",
    "validate_offer",
    "validate_panel",
    "validate_row",
    "validate_step",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
    "walk_plain_words",
    "walk_record",
    "walk_steps",
]

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource

ONBOARDING_FIVE_SCHEMA = "mythic.onboarding_five/1"
ONBOARDING_FIVE_SLICE = "M-184"
THE_ONBOARDING_FIVE_SLICE = ONBOARDING_FIVE_SLICE
ONBOARDING_FIVE_RESOURCE = "onboarding_five.yaml"
WALK_ACTION = "walk"
DETECTION_OUTCOMES = ("found", "absent")
PROBES = (
    "environment key probe", "local door probe",
    "registry probe", "config reference probe")
VIEW_FILTERS = ("all", "found", "absent")
WALK_PHASES = ("detect", "walk", "success", "offer", "configure")
OFFER_DECISIONS = ("accepted", "declined", "pending")
VERDICT_WORDS = ("open", "strained", "shut")
SUCCESS_BEFORE_CONFIGURATION_RULE = (
    "success before configuration, always: the first run "
    "reaches one real success before any configuration is "
    "asked for; configuration is offered after the first "
    "success, never required before it")
PLAIN_EXPLANATION = (
    "Onboarding in five minutes (M-184): the first run "
    "detects providers, offers Kista key-keeping, and "
    "walks one tiny real task - success before "
    "configuration, always.")
USAGE = (
    "Usage: /onboard | /onboard detection <detection-id> | "
    "/onboard walk | /onboard offer <offer-id> | "
    "/onboard view <view-id> | /onboard outcome <outcome> | "
    "/onboard panel | /onboard verdict")

_PROVENANCE = ("recorded_on", "actor", "source", "origin_session")
_DETECTION_KEYS = frozenset({
    "detection_id", "seq", "provider", "probe", "outcome",
    "detail",
} | set(_PROVENANCE))
_VIEW_KEYS = frozenset({
    "view_id", "seq", "view_filter", "detail",
} | set(_PROVENANCE))
_STEP_KEYS = frozenset({
    "step_id", "seq", "phase", "title", "detail",
} | set(_PROVENANCE))
_OFFER_KEYS = frozenset({
    "offer_id", "seq", "provider", "decision", "detail",
} | set(_PROVENANCE))
_DERIVED_KEYS = frozenset({
    "passes", "gaps", "segment", "plain_lines", "telling",
    "verdict", "in_order", "walk"})
_CONFIG_FIRST_KEYS = (
    "config_first", "configuration_first",
    "requires_configuration", "config_before_success")
_KEY_KEYS = ("api_key", "key", "secret", "token", "password")


# ---------------------------------------------------------------------
# Small judges, in the sibling shape.
# ---------------------------------------------------------------------

def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_count(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a whole number")
    if value < 0:
        raise ValueError(f"{what} must not be negative")
    return value


def _check_seq(value: Any, what: str = "a sequence") -> int:
    number = _check_count(value, what)
    if number < 1:
        raise ValueError(f"{what} must stand at 1 or later")
    return number


def _check_lines(value: Any, what: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError(f"{what} must be a list of lines")
    lines = []
    for line in value:
        lines.append(_clean_text(line, f"a line of {what}"))
    return tuple(lines)


def _provenance(mapping: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in _PROVENANCE:
        if key == "recorded_on":
            out[key] = _clean_text(mapping.get(key), "a recorded_on day")
        else:
            out[key] = _clean_text(mapping.get(key), f"a {key}")
    return out


def _needed(mapping: Dict[str, Any], allowed: frozenset,
            what: str) -> None:
    if not isinstance(mapping, dict):
        raise ValueError(f"{what} must be a mapping")
    for key in _CONFIG_FIRST_KEYS:
        if key in mapping:
            raise ValueError(
                f"{what} claims configuration comes first "
                f"({key!r} is named on it): "
                f"{SUCCESS_BEFORE_CONFIGURATION_RULE}")
    for key in _KEY_KEYS:
        if key in mapping:
            raise ValueError(
                f"{what} names a key itself ({key!r}): keys "
                f"themselves are never held by this layer - "
                f"Kista holds the keys; this layer holds the "
                f"offer and its answer alone")
    for key in mapping:
        if key in _DERIVED_KEYS:
            raise ValueError(
                f"{what} carries {key!r}, which is derived from its "
                f"own fields and never stored")
        if key not in allowed:
            raise ValueError(f"{what} carries unknown field {key!r}")


def normalize_outcome(value: Any) -> str:
    outcome = _clean_text(value, "a detection outcome").lower()
    if outcome not in DETECTION_OUTCOMES:
        raise ValueError(
            f"detection outcome {outcome!r} is not one of the held "
            f"outcomes: " + ", ".join(DETECTION_OUTCOMES))
    return outcome


def normalize_probe(value: Any) -> str:
    probe = _clean_text(value, "a probe").lower()
    if probe not in PROBES:
        raise ValueError(
            f"probe {probe!r} is not one of the named probes: "
            + ", ".join(PROBES))
    return probe


def normalize_view_filter(value: Any) -> str:
    view_filter = _clean_text(value, "a view filter").lower()
    if view_filter not in VIEW_FILTERS:
        raise ValueError(
            f"view filter {view_filter!r} is not one of the held "
            f"filters: " + ", ".join(VIEW_FILTERS))
    return view_filter


def normalize_phase(value: Any) -> str:
    phase = _clean_text(value, "a walk phase").lower()
    if phase not in WALK_PHASES:
        raise ValueError(
            f"walk phase {phase!r} is not one of the held phases: "
            + ", ".join(WALK_PHASES))
    return phase


def normalize_decision(value: Any) -> str:
    decision = _clean_text(value, "an offer decision").lower()
    if decision not in OFFER_DECISIONS:
        raise ValueError(
            f"offer decision {decision!r} is not one of the held "
            f"decisions: " + ", ".join(OFFER_DECISIONS))
    return decision


# ---------------------------------------------------------------------
# The held detection: one provider, the named probe that looked for
# it, and the outcome that probe honestly returned.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class DetectionRecord:
    """One provider detection, held as data.

    The detection names the provider, the named
    probe that looked for it - an environment key
    probe reads a key's name, never the key - and
    the outcome the probe returned, found or
    absent. A provider no probe found stands
    absent, named in its gaps, and does not stand
    found: availability is never faked here.
    """

    detection_id: str
    seq: int
    provider: str
    probe: str
    outcome: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "detection_id",
            _clean_text(self.detection_id, "a detection id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "provider", _clean_text(self.provider, "a provider"))
        object.__setattr__(self, "probe", normalize_probe(self.probe))
        object.__setattr__(
            self, "outcome", normalize_outcome(self.outcome))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a detection detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.detection_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "detection_id": self.detection_id, "seq": self.seq,
            "provider": self.provider, "probe": self.probe,
            "outcome": self.outcome, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_detection_ref(value: Any) -> DetectionRecord:
    if not isinstance(value, DetectionRecord):
        raise ValueError("a detection must be a DetectionRecord")
    return value


def validate_detection(detection: Any) -> DetectionRecord:
    return _check_detection_ref(detection)


def build_detection(detection: Any = None, **kwargs: Any) -> DetectionRecord:
    """Build one held detection from a mapping or fields."""
    if detection is None:
        data = dict(kwargs)
    elif isinstance(detection, DetectionRecord):
        if kwargs:
            raise ValueError(
                "a detection stands whole or by fields, not both")
        return detection
    elif isinstance(detection, dict):
        data = dict(detection)
        data.update(kwargs)
    else:
        raise ValueError(
            "a detection must be a mapping or a DetectionRecord")
    _needed(data, _DETECTION_KEYS, "a detection")
    return DetectionRecord(
        detection_id=data.get("detection_id"), seq=data.get("seq"),
        provider=data.get("provider"), probe=data.get("probe"),
        outcome=data.get("outcome"), detail=data.get("detail"),
        **_provenance(data))


def detection_gaps(detection: Any) -> Tuple[str, ...]:
    """The gaps that keep a detection from standing found."""
    checked = _check_detection_ref(detection)
    return () if checked.outcome == "found" else ("provider",)


def detection_passes(detection: Any) -> bool:
    return not detection_gaps(detection)


def plain_lines(detection: Any) -> Tuple[str, ...]:
    """The plain telling, DERIVED from the detection's own fields."""
    checked = _check_detection_ref(detection)
    return (
        f"Provider: {checked.provider}",
        f"Looked for by: {checked.probe}",
        f"What the probe found: {checked.outcome}",
    )


def segment_of(detection: Any) -> str:
    checked = _check_detection_ref(detection)
    gaps = detection_gaps(checked)
    return (
        f"{checked.detection_id}: {checked.provider} probed by "
        f"'{checked.probe}' - outcome: '{checked.outcome}' - "
        f"detail: '{checked.detail}' - gaps: "
        f"{', '.join(gaps) if gaps else 'none'}")


# ---------------------------------------------------------------------
# The held view: which detections a telling shows.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class OnboardingView:
    """A view over the book: every detection, the found, the absent."""

    view_id: str
    seq: int
    view_filter: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "view_id", _clean_text(self.view_id, "a view id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "view_filter", normalize_view_filter(self.view_filter))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a view detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    def to_record(self) -> Dict[str, Any]:
        record = {
            "view_id": self.view_id, "seq": self.seq,
            "view_filter": self.view_filter, "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_view_ref(value: Any) -> OnboardingView:
    if not isinstance(value, OnboardingView):
        raise ValueError("a view must be an OnboardingView")
    return value


def validate_view(view: Any) -> OnboardingView:
    return _check_view_ref(view)


def build_view(view: Any = None, **kwargs: Any) -> OnboardingView:
    if view is None:
        data = dict(kwargs)
    elif isinstance(view, OnboardingView):
        if kwargs:
            raise ValueError("a view stands whole or by fields, not both")
        return view
    elif isinstance(view, dict):
        data = dict(view)
        data.update(kwargs)
    else:
        raise ValueError("a view must be a mapping or an OnboardingView")
    _needed(data, _VIEW_KEYS, "a view")
    return OnboardingView(
        view_id=data.get("view_id"), seq=data.get("seq"),
        view_filter=data.get("view_filter"), detail=data.get("detail"),
        **_provenance(data))


# ---------------------------------------------------------------------
# The held walk step and the Kista offer: the walk in order, the
# offer as data, keys never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class WalkStep:
    """One step of the first-run walk, held in order.

    The step stands under its phase - detect, walk,
    success, offer or configure - with its title
    and its detail. The walk is the steps in held
    order; the ordering rule is judged on the
    whole walk in the book, never on one step.
    """

    step_id: str
    seq: int
    phase: str
    title: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "step_id", _clean_text(self.step_id, "a step id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(self, "phase", normalize_phase(self.phase))
        object.__setattr__(
            self, "title", _clean_text(self.title, "a step title"))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "a step detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.step_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "step_id": self.step_id, "seq": self.seq,
            "phase": self.phase, "title": self.title,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_step_ref(value: Any) -> WalkStep:
    if not isinstance(value, WalkStep):
        raise ValueError("a walk step must be a WalkStep")
    return value


def validate_step(step: Any) -> WalkStep:
    return _check_step_ref(step)


def build_step(step: Any = None, **kwargs: Any) -> WalkStep:
    if step is None:
        data = dict(kwargs)
    elif isinstance(step, WalkStep):
        if kwargs:
            raise ValueError("a step stands whole or by fields, not both")
        return step
    elif isinstance(step, dict):
        data = dict(step)
        data.update(kwargs)
    else:
        raise ValueError("a step must be a mapping or a WalkStep")
    _needed(data, _STEP_KEYS, "a walk step")
    return WalkStep(
        step_id=data.get("step_id"), seq=data.get("seq"),
        phase=data.get("phase"), title=data.get("title"),
        detail=data.get("detail"), **_provenance(data))


@dataclass(frozen=True)
class OfferRecord:
    """One Kista key-keeping offer, held as data.

    The offer holds the provider it was made for
    and the answer it was given - accepted,
    declined or still pending. The key itself is
    never part of the record: Kista holds the
    keys; this layer holds the offer alone.
    """

    offer_id: str
    seq: int
    provider: str
    decision: str
    detail: str = ""
    recorded_on: str = ""
    actor: str = ""
    source: str = ""
    origin_session: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "offer_id", _clean_text(self.offer_id, "an offer id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "provider", _clean_text(self.provider, "a provider"))
        object.__setattr__(
            self, "decision", normalize_decision(self.decision))
        object.__setattr__(
            self, "detail", _clean_text(self.detail, "an offer detail"))
        for key in _PROVENANCE:
            object.__setattr__(
                self, key, _clean_text(getattr(self, key), f"a {key}"))

    @property
    def item_id(self) -> str:
        return self.offer_id

    def to_record(self) -> Dict[str, Any]:
        record = {
            "offer_id": self.offer_id, "seq": self.seq,
            "provider": self.provider, "decision": self.decision,
            "detail": self.detail,
        }
        for key in _PROVENANCE:
            record[key] = getattr(self, key)
        return record


def _check_offer_ref(value: Any) -> OfferRecord:
    if not isinstance(value, OfferRecord):
        raise ValueError("an offer must be an OfferRecord")
    return value


def validate_offer(offer: Any) -> OfferRecord:
    return _check_offer_ref(offer)


def build_offer(offer: Any = None, **kwargs: Any) -> OfferRecord:
    if offer is None:
        data = dict(kwargs)
    elif isinstance(offer, OfferRecord):
        if kwargs:
            raise ValueError("an offer stands whole or by fields, not both")
        return offer
    elif isinstance(offer, dict):
        data = dict(offer)
        data.update(kwargs)
    else:
        raise ValueError("an offer must be a mapping or an OfferRecord")
    _needed(data, _OFFER_KEYS, "an offer")
    return OfferRecord(
        offer_id=data.get("offer_id"), seq=data.get("seq"),
        provider=data.get("provider"), decision=data.get("decision"),
        detail=data.get("detail"), **_provenance(data))


def inspect_onboarding_source(piece: Any) -> Dict[str, Any]:
    """Name what one onboarding source piece is, without judging it."""
    if isinstance(piece, DetectionRecord):
        return {"kind": "detection", "detection_id": piece.detection_id}
    if isinstance(piece, dict):
        if "detection_id" in piece:
            return {"kind": "detection",
                    "detection_id": piece.get("detection_id")}
        if "view_id" in piece:
            return {"kind": "view", "view_id": piece.get("view_id")}
        if "step_id" in piece:
            return {"kind": "step", "step_id": piece.get("step_id")}
        if "offer_id" in piece:
            return {"kind": "offer", "offer_id": piece.get("offer_id")}
    return {"kind": "unknown", "detection_id": None}


# ---------------------------------------------------------------------
# The panel and the verdict: derived from the whole book, never held.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class OnboardingPanelRow:
    item_id: str
    outcome: str
    label: str
    segment: str
    recorded_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id, "outcome": self.outcome,
            "label": self.label, "segment": self.segment,
            "recorded_on": self.recorded_on,
        }


def _row_for_detection(detection: DetectionRecord) -> OnboardingPanelRow:
    return OnboardingPanelRow(
        item_id=detection.detection_id, outcome=detection.outcome,
        label=detection.provider, segment=segment_of(detection),
        recorded_on=detection.recorded_on)


def _check_row_ref(value: Any) -> OnboardingPanelRow:
    if not isinstance(value, OnboardingPanelRow):
        raise ValueError("a panel row must be an OnboardingPanelRow")
    return value


def validate_row(row: Any, detection: Any = None) -> OnboardingPanelRow:
    checked = _check_row_ref(row)
    if detection is not None:
        derived = _row_for_detection(_check_detection_ref(detection))
        if checked != derived:
            raise ValueError(
                f"panel row {checked.item_id!r} does not agree with "
                f"the row derived from its detection")
    return checked


def build_row(row: Any = None, detection: Any = None,
              **kwargs: Any) -> OnboardingPanelRow:
    if detection is not None:
        derived = _row_for_detection(_check_detection_ref(detection))
        if row is None and not kwargs:
            return derived
        built = build_row(row, **kwargs) if row is not None else (
            OnboardingPanelRow(**kwargs))
        return validate_row(built, detection)
    if isinstance(row, OnboardingPanelRow):
        if kwargs:
            raise ValueError("a row stands whole or by fields, not both")
        return row
    if isinstance(row, dict):
        data = dict(row)
        data.update(kwargs)
        return OnboardingPanelRow(
            item_id=_clean_text(data.get("item_id"), "a row item id"),
            outcome=normalize_outcome(data.get("outcome")),
            label=_clean_text(data.get("label"), "a row label"),
            segment=_clean_text(data.get("segment"), "a row segment"),
            recorded_on=_clean_text(
                data.get("recorded_on"), "a row recorded_on day"))
    if row is None and kwargs:
        return OnboardingPanelRow(**kwargs)
    raise ValueError(
        "a panel row must be a mapping or an OnboardingPanelRow")


@dataclass(frozen=True)
class OutcomeCount:
    outcome: str
    items: int

    def to_record(self) -> Dict[str, Any]:
        return {"outcome": self.outcome, "items": self.items}


def _outcome_counts(rows: Tuple[OnboardingPanelRow, ...]
                    ) -> Tuple[OutcomeCount, ...]:
    counts: List[OutcomeCount] = []
    for outcome in DETECTION_OUTCOMES:
        number = sum(1 for row in rows if row.outcome == outcome)
        if number:
            counts.append(OutcomeCount(outcome=outcome, items=number))
    return tuple(counts)


def _panel_account(total_items: int, total_shown: int,
                   passing_shown: int,
                   outcome_counts: Tuple[OutcomeCount, ...],
                   view_filter: str, as_of: str) -> Tuple[str, ...]:
    outcomes = ", ".join(
        f"{count.outcome} {count.items}"
        for count in outcome_counts) or "none"
    return (
        f"The onboarding book holds {total_items} detections as of "
        f"{as_of}: the view '{view_filter}' shows {total_shown} of "
        f"them: {outcomes}; {passing_shown} of the shown providers "
        f"stand found.",
        "Rows stand in held order, the order the book itself "
        "stands in, so two panels of one view diff cleanly, "
        "segment by segment.",
        "Every segment is derived from its detection's own fields "
        "- the provider, the named probe that looked for it and "
        "the outcome that probe honestly returned - and no "
        "judgement is stored on any detection.",
        "Availability is never faked: a provider no probe found "
        "stands absent, named in its gaps, and no key is ever "
        "held by this layer - Kista key-keeping is offered, "
        "never assumed, and success stands before configuration, "
        "always.",
    )


@dataclass(frozen=True)
class OnboardingPanel:
    panel_id: str
    view_id: Optional[str]
    view_filter: str
    rows: Tuple[OnboardingPanelRow, ...]
    total_items: int
    total_shown: int
    outcome_counts: Tuple[OutcomeCount, ...]
    as_of: str
    account: Tuple[str, ...]

    def to_record(self) -> Dict[str, Any]:
        return {
            "panel_id": self.panel_id, "view_id": self.view_id,
            "view_filter": self.view_filter,
            "rows": [row.to_record() for row in self.rows],
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "outcome_counts": [c.to_record() for c in self.outcome_counts],
            "as_of": self.as_of, "account": list(self.account),
        }


def _held_detections(source: Any) -> Tuple[DetectionRecord, ...]:
    return _source_book(source).detections


def _resolve_view(source: Any, view: Any) -> OnboardingView:
    book = _source_book(source)
    if view is None:
        if not book.views:
            raise ValueError("the book holds no view to derive under")
        return book.views[0]
    if isinstance(view, OnboardingView):
        return view
    return book.view_for(view)


def shown_detections(source: Any, view: Any = None
                     ) -> Tuple[DetectionRecord, ...]:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    if resolved.view_filter == "all":
        return book.detections
    if resolved.view_filter == "found":
        return tuple(d for d in book.detections if detection_passes(d))
    return tuple(d for d in book.detections if not detection_passes(d))


def detections_for_outcome(source: Any, outcome: Any
                           ) -> Tuple[DetectionRecord, ...]:
    wanted = normalize_outcome(outcome)
    return tuple(
        d for d in _source_book(source).detections
        if d.outcome == wanted)


def passing_detections(source: Any) -> Tuple[DetectionRecord, ...]:
    return tuple(
        d for d in _source_book(source).detections
        if detection_passes(d))


def total_detections(source: Any) -> int:
    return len(_source_book(source).detections)


def derive_panel(source: Any, view: Any = None) -> OnboardingPanel:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_detections(book, resolved)
    rows = tuple(_row_for_detection(detection) for detection in shown)
    counts = _outcome_counts(rows)
    as_of = max((d.recorded_on for d in book.detections), default="")
    passing = sum(1 for d in shown if detection_passes(d))
    return OnboardingPanel(
        panel_id=f"panel-{resolved.view_id}", view_id=resolved.view_id,
        view_filter=resolved.view_filter, rows=rows,
        total_items=len(book.detections), total_shown=len(shown),
        outcome_counts=counts, as_of=as_of,
        account=_panel_account(
            len(book.detections), len(shown), passing, counts,
            resolved.view_filter, as_of))


def _check_panel_ref(value: Any) -> OnboardingPanel:
    if not isinstance(value, OnboardingPanel):
        raise ValueError("a panel must be an OnboardingPanel")
    return value


def validate_panel(panel: Any, source: Any = None) -> OnboardingPanel:
    """Judge a stored panel against the panel derived from its book.

    Every derived field must agree; the stored
    panel's own name is its identity, not derived
    content (the M-182 lesson).
    """
    checked = _check_panel_ref(panel)
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(checked.view_id)
                if checked.view_id is not None else None)
        derived = derive_panel(book, view)
        for attr in ("view_id", "view_filter", "rows", "total_items",
                     "total_shown", "outcome_counts", "as_of", "account"):
            if getattr(checked, attr) != getattr(derived, attr):
                raise ValueError(
                    f"panel {checked.panel_id!r} disagrees with the "
                    f"panel derived from its book on {attr}")
    return checked


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> OnboardingPanel:
    if isinstance(panel, OnboardingPanel):
        if kwargs:
            raise ValueError("a panel stands whole or by fields, not both")
        return validate_panel(panel, source)
    if isinstance(panel, dict):
        data = dict(panel)
        data.update(kwargs)
        rows = tuple(build_row(row) for row in data.get("rows") or ())
        counts = tuple(
            OutcomeCount(
                outcome=normalize_outcome(c.get("outcome")),
                items=_check_count(c.get("items"), "an outcome count"))
            for c in data.get("outcome_counts") or ()
            if isinstance(c, dict))
        built = OnboardingPanel(
            panel_id=_clean_text(data.get("panel_id"), "a panel id"),
            view_id=data.get("view_id"),
            view_filter=normalize_view_filter(data.get("view_filter")),
            rows=rows,
            total_items=_check_count(
                data.get("total_items"), "a total_items count"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            outcome_counts=counts,
            as_of=_clean_text(data.get("as_of"), "an as_of day"),
            account=_check_lines(data.get("account"), "the account"))
        return validate_panel(built, source)
    if panel is None and source is not None:
        return derive_panel(source, kwargs.get("view"))
    raise ValueError("a panel must be a mapping, an OnboardingPanel, or derived")


def _verdict_word(total_shown: int, passing_shown: int) -> str:
    if total_shown > 0 and passing_shown == total_shown:
        return "open"
    if passing_shown == 0:
        return "shut"
    return "strained"


@dataclass(frozen=True)
class OnboardingVerdict:
    verdict: str
    view_id: Optional[str]
    total_shown: int
    passing_shown: int
    latest_on: str

    def to_record(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict, "view_id": self.view_id,
            "total_shown": self.total_shown,
            "passing_shown": self.passing_shown,
            "latest_on": self.latest_on,
        }


def derive_verdict(source: Any, view: Any = None) -> OnboardingVerdict:
    book = _source_book(source)
    resolved = _resolve_view(book, view)
    shown = shown_detections(book, resolved)
    passing = sum(1 for d in shown if detection_passes(d))
    latest = max((d.recorded_on for d in shown), default="")
    return OnboardingVerdict(
        verdict=_verdict_word(len(shown), passing),
        view_id=resolved.view_id, total_shown=len(shown),
        passing_shown=passing, latest_on=latest)


def _check_verdict_ref(value: Any) -> OnboardingVerdict:
    if not isinstance(value, OnboardingVerdict):
        raise ValueError("a verdict must be an OnboardingVerdict")
    return value


def validate_verdict(verdict: Any, source: Any = None) -> OnboardingVerdict:
    checked = _check_verdict_ref(verdict)
    if checked.verdict not in VERDICT_WORDS:
        raise ValueError(f"verdict {checked.verdict!r} is not a held word")
    if source is not None:
        book = _source_book(source)
        view = (book.view_for(checked.view_id)
                if checked.view_id is not None else None)
        derived = derive_verdict(book, view)
        if checked != derived:
            raise ValueError(
                "the stored verdict disagrees with the verdict "
                "derived from its book")
    return checked


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> OnboardingVerdict:
    if isinstance(verdict, OnboardingVerdict):
        if kwargs:
            raise ValueError(
                "a verdict stands whole or by fields, not both")
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        data = dict(verdict)
        data.update(kwargs)
        built = OnboardingVerdict(
            verdict=_clean_text(data.get("verdict"), "a verdict"),
            view_id=data.get("view_id"),
            total_shown=_check_count(
                data.get("total_shown"), "a total_shown count"),
            passing_shown=_check_count(
                data.get("passing_shown"), "a passing_shown count"),
            latest_on=_clean_text(data.get("latest_on"), "a latest day"))
        return validate_verdict(built, source)
    if verdict is None and source is not None:
        return derive_verdict(source, kwargs.get("view"))
    raise ValueError(
        "a verdict must be a mapping, an OnboardingVerdict, or derived")


# ---------------------------------------------------------------------
# The walk: the held steps in order, judged under the ordering rule -
# success before configuration, always.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class OnboardingWalk:
    """The first-run walk, derived from the book's held steps.

    The walk is its steps in held order, with the
    first success step and the first configure
    step named by sequence. The walk stands in
    order when a success stands, and no configure
    step stands before it: success before
    configuration, always.
    """

    steps: Tuple[WalkStep, ...]
    success_seq: Optional[int]
    configure_seq: Optional[int]

    def passes(self) -> bool:
        if self.success_seq is None:
            return False
        return (self.configure_seq is None
                or self.success_seq < self.configure_seq)

    def to_record(self) -> Dict[str, Any]:
        return {
            "steps": [step.to_record() for step in self.steps],
            "success_seq": self.success_seq,
            "configure_seq": self.configure_seq,
            "passes": self.passes(),
        }


def walk_steps(source: Any) -> Tuple[WalkStep, ...]:
    """The book's walk steps, in held order."""
    return _source_book(source).steps


def derive_walk(source: Any) -> OnboardingWalk:
    book = _source_book(source)
    success = next(
        (s.seq for s in book.steps if s.phase == "success"), None)
    configure = next(
        (s.seq for s in book.steps if s.phase == "configure"), None)
    return OnboardingWalk(
        steps=book.steps, success_seq=success, configure_seq=configure)


def _judge_walk_order(steps: Tuple[WalkStep, ...]) -> None:
    success = next((s.seq for s in steps if s.phase == "success"), None)
    configure = next(
        (s.seq for s in steps if s.phase == "configure"), None)
    if configure is not None and (
            success is None or configure < success):
        raise ValueError(
            f"the walk demands configuration before the first "
            f"success: {SUCCESS_BEFORE_CONFIGURATION_RULE}")


# ---------------------------------------------------------------------
# The book: detections, views, walk steps and offers held together,
# one pinned panel at most per telling, and no verdict ever stored.
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class OnboardingBook:
    title: str
    detections: Tuple[DetectionRecord, ...] = ()
    views: Tuple[OnboardingView, ...] = ()
    steps: Tuple[WalkStep, ...] = ()
    offers: Tuple[OfferRecord, ...] = ()
    panels: Tuple[OnboardingPanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a book title"))
        detections = tuple(
            _check_detection_ref(d) for d in self.detections)
        views = tuple(_check_view_ref(v) for v in self.views)
        steps = tuple(_check_step_ref(s) for s in self.steps)
        offers = tuple(_check_offer_ref(o) for o in self.offers)
        panels = tuple(_check_panel_ref(p) for p in self.panels)
        seen_ids = set()
        seen_seqs = set()
        for detection in detections:
            if detection.detection_id in seen_ids:
                raise ValueError(
                    f"two detections stand under id "
                    f"{detection.detection_id!r}")
            if detection.seq in seen_seqs:
                raise ValueError(
                    f"two detections stand at sequence {detection.seq}")
            seen_ids.add(detection.detection_id)
            seen_seqs.add(detection.seq)
        view_ids = set()
        view_seqs = set()
        for view in views:
            if view.view_id in view_ids:
                raise ValueError(
                    f"two views stand under id {view.view_id!r}")
            if view.seq in view_seqs:
                raise ValueError(
                    f"two views stand at sequence {view.seq}")
            view_ids.add(view.view_id)
            view_seqs.add(view.seq)
        step_ids = set()
        step_seqs = set()
        for step in steps:
            if step.step_id in step_ids:
                raise ValueError(
                    f"two walk steps stand under id {step.step_id!r}")
            if step.seq in step_seqs:
                raise ValueError(
                    f"two walk steps stand at sequence {step.seq}")
            step_ids.add(step.step_id)
            step_seqs.add(step.seq)
        offer_ids = set()
        offer_seqs = set()
        for offer in offers:
            if offer.offer_id in offer_ids:
                raise ValueError(
                    f"two offers stand under id {offer.offer_id!r}")
            if offer.seq in offer_seqs:
                raise ValueError(
                    f"two offers stand at sequence {offer.seq}")
            offer_ids.add(offer.offer_id)
            offer_seqs.add(offer.seq)
        ordered_steps = tuple(sorted(steps, key=lambda s: s.seq))
        _judge_walk_order(ordered_steps)
        object.__setattr__(
            self, "detections",
            tuple(sorted(detections, key=lambda d: d.seq)))
        object.__setattr__(
            self, "views", tuple(sorted(views, key=lambda v: v.seq)))
        object.__setattr__(self, "steps", ordered_steps)
        object.__setattr__(
            self, "offers", tuple(sorted(offers, key=lambda o: o.seq)))
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        return self.detections + self.views

    def item_ids(self) -> Tuple[str, ...]:
        return tuple(d.detection_id for d in self.detections) + tuple(
            v.view_id for v in self.views)

    def detection_ids(self) -> Tuple[str, ...]:
        return tuple(d.detection_id for d in self.detections)

    def detection_for(self, detection_id: Any) -> DetectionRecord:
        wanted = _clean_text(detection_id, "a detection id")
        for detection in self.detections:
            if detection.detection_id == wanted:
                return detection
        raise KeyError(
            f"no detection named {wanted!r} stands in this book")

    def view_for(self, view_id: Any) -> OnboardingView:
        wanted = _clean_text(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands in this book")

    def step_for(self, step_id: Any) -> WalkStep:
        wanted = _clean_text(step_id, "a step id")
        for step in self.steps:
            if step.step_id == wanted:
                return step
        raise KeyError(f"no step named {wanted!r} stands in this book")

    def offer_for(self, offer_id: Any) -> OfferRecord:
        wanted = _clean_text(offer_id, "an offer id")
        for offer in self.offers:
            if offer.offer_id == wanted:
                return offer
        raise KeyError(f"no offer named {wanted!r} stands in this book")

    def item_for(self, item_id: Any) -> Any:
        wanted = _clean_text(item_id, "an item id")
        for detection in self.detections:
            if detection.detection_id == wanted:
                return detection
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no item named {wanted!r} stands in this book")

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "detections": [d.to_record() for d in self.detections],
            "views": [v.to_record() for v in self.views],
            "steps": [s.to_record() for s in self.steps],
            "offers": [o.to_record() for o in self.offers],
            "panels": [p.to_record() for p in self.panels],
        }


def _judge_book_panels(book: OnboardingBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _check_example(book: OnboardingBook) -> None:
    if book.title != "Onboarding in five minutes at the M-183 slice boundary":
        raise ValueError("the shipped example book carries another title")
    if len(book.detections) != 6 or len(book.views) != 2:
        raise ValueError(
            "the shipped example book must hold six detections and "
            "two views")
    if len(book.steps) != 5 or len(book.offers) != 1:
        raise ValueError(
            "the shipped example book must hold five walk steps and "
            "one offer")
    if len(book.panels) != 1:
        raise ValueError("the shipped example book holds one pinned panel")
    panel = book.panels[0]
    if panel.panel_id != "panel-m183-boundary":
        raise ValueError("the pinned panel is panel-m183-boundary")
    verdict = derive_verdict(book, book.view_for(panel.view_id))
    if verdict.verdict != "strained" or verdict.passing_shown != 4:
        raise ValueError(
            "the shipped example book's verdict must stand strained "
            "at four found of six")
    walk = derive_walk(book)
    if not walk.passes():
        raise ValueError(
            "the shipped example book's walk must stand in order: "
            "success before configuration")


def validate_book(data: Any, *, require_example: bool = False) -> OnboardingBook:
    """Judge raw book data whole and return the held book."""
    if isinstance(data, OnboardingBook):
        _judge_book_panels(data)
        if require_example:
            _check_example(data)
        return data
    if not isinstance(data, dict):
        raise ValueError("an onboarding book must be a mapping")
    for key in _CONFIG_FIRST_KEYS:
        if key in data:
            raise ValueError(
                f"the book claims configuration comes first "
                f"({key!r} is named on it): "
                f"{SUCCESS_BEFORE_CONFIGURATION_RULE}")
    for key in _KEY_KEYS:
        if key in data:
            raise ValueError(
                f"the book names a key itself ({key!r}): keys "
                f"themselves are never held by this layer")
    if "verdict" in data or "verdicts" in data:
        raise ValueError(
            "a book stores no verdict: the verdict is derived from "
            "its detections under a view")
    if data.get("schema") is not None and (
            data["schema"] != ONBOARDING_FIVE_SCHEMA):
        raise ValueError(
            f"a book's schema must be {ONBOARDING_FIVE_SCHEMA!r}")
    if data.get("slice") is not None and (
            data["slice"] != ONBOARDING_FIVE_SLICE):
        raise ValueError(
            f"a book's slice must be {ONBOARDING_FIVE_SLICE!r}")
    guide = data.get("guide") or {}
    if not isinstance(guide, dict):
        raise ValueError("a book's guide must be a mapping")
    title = guide.get("title") or data.get("title")
    detections = tuple(
        build_detection(d) for d in data.get("detections") or ())
    views = tuple(build_view(v) for v in data.get("views") or ())
    steps = tuple(build_step(s) for s in data.get("steps") or ())
    offers = tuple(build_offer(o) for o in data.get("offers") or ())
    book = OnboardingBook(
        title=title, detections=detections, views=views, steps=steps,
        offers=offers, panels=())
    panels = tuple(
        build_panel(p, book) for p in data.get("panels") or ())
    book = OnboardingBook(
        title=book.title, detections=book.detections, views=book.views,
        steps=book.steps, offers=book.offers, panels=panels)
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def build_book(book: Any = None, **kwargs: Any) -> OnboardingBook:
    if book is None:
        data = dict(kwargs)
    elif isinstance(book, (OnboardingBook, dict)):
        if kwargs:
            raise ValueError("a book stands whole or by fields, not both")
        return validate_book(book)
    else:
        raise ValueError("a book must be a mapping or an OnboardingBook")
    return validate_book(data)


def _book_from(data: Any, *, require_example: bool) -> OnboardingBook:
    return validate_book(data, require_example=require_example)


def load_onboarding_five(
        data: Optional[Dict[str, Any]] = None) -> OnboardingBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(ONBOARDING_FIVE_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_onboarding_five_file(path: Any) -> OnboardingBook:
    """Load one first-run file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: detections and views held one by one.
# ---------------------------------------------------------------------

class OnboardingRegistry:
    """An in-memory holding of detections and views.

    The registry is the pure layer's model of a
    session's onboarding book: detections are held
    under their ids, one detection per id and per
    sequence, and views are held in recorded
    order, one view per sequence and per id.
    Holding is data only - nothing held here
    detects anything live, keeps a key, runs a
    task, or configures anything.
    """

    def __init__(self, book: Any = None) -> None:
        self._detections: List[DetectionRecord] = []
        self._views: List[OnboardingView] = []
        self._title: Optional[str] = None
        if book is not None:
            self.register_book(book)

    def title(self) -> Optional[str]:
        return self._title

    def _fresh_view_id(self, held_ids: Any) -> str:
        n = 1
        while f"view-{n}" in held_ids:
            n += 1
        return f"view-{n}"

    def _register(self, held: List[Any], item: Any,
                  id_attr: str, what: str) -> Any:
        for other in held:
            if getattr(other, id_attr) == getattr(item, id_attr):
                raise ValueError(
                    f"a {what} already stands under id "
                    f"{getattr(item, id_attr)!r}")
            if other.seq == item.seq:
                raise ValueError(
                    f"a {what} already stands at sequence {item.seq}")
        held.append(item)
        held.sort(key=lambda held_item: held_item.seq)
        return item

    def register_detection(self, item: Any) -> DetectionRecord:
        """Hold one detection, judged whole before held."""
        return self._register(
            self._detections, _check_detection_ref(item),
            "detection_id", "detection")

    def register_view(self, view: Any) -> OnboardingView:
        """Hold one view; a view naming no id takes a fresh one."""
        checked = _check_view_ref(view)
        if not checked.view_id:
            fresh = self._fresh_view_id(
                [held.view_id for held in self._views])
            checked = build_view({**checked.to_record(),
                                  "view_id": fresh})
        return self._register(
            self._views, checked, "view_id", "view")

    def register_book(self, book: Any) -> OnboardingBook:
        """Hold a whole book's detections and views, under its title."""
        checked = build_book(book)
        if self._title is not None and checked.title != self._title:
            raise ValueError(
                "a second book title refuses: this registry holds "
                f"{self._title!r}, not {checked.title!r}")
        for detection in checked.detections:
            self.register_detection(detection)
        for view in checked.views:
            self.register_view(view)
        self._title = checked.title
        return self.book()

    def book(self) -> OnboardingBook:
        return OnboardingBook(
            title=self._title or "An unheld onboarding book",
            detections=tuple(self._detections),
            views=tuple(self._views), steps=(), offers=(), panels=())

    def list_detections(self) -> Tuple[DetectionRecord, ...]:
        return tuple(self._detections)

    def list_views(self) -> Tuple[OnboardingView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._detections) + tuple(self._views)

    def get_detection(self, detection_id: Any) -> DetectionRecord:
        return self.book().detection_for(detection_id)

    def get_view(self, view_id: Any) -> OnboardingView:
        return self.book().view_for(view_id)

    def get_item(self, item_id: Any) -> Any:
        return self.book().item_for(item_id)


# ---------------------------------------------------------------------
# Session news: records shaped for the journal road.
# ---------------------------------------------------------------------

def _source_book(source: Any) -> OnboardingBook:
    if source is None:
        return load_onboarding_five()
    if isinstance(source, OnboardingBook):
        return source
    if isinstance(source, OnboardingRegistry):
        return source.book()
    return build_book(source)


def _provenance_record(item: Any) -> Dict[str, Any]:
    return {key: getattr(item, key) for key in _PROVENANCE}


def detection_record(detection: Any, source: Any = None) -> Dict[str, Any]:
    checked = _check_detection_ref(detection)
    record = {
        "type": "onboarding_detection",
        "slice": ONBOARDING_FIVE_SLICE,
        "detection_id": checked.detection_id,
        "provider": checked.provider,
        "segment": segment_of(checked),
        "passes": detection_passes(checked),
        "gaps": list(detection_gaps(checked)),
    }
    record.update(_provenance_record(checked))
    return record


def view_record(view: Any) -> Dict[str, Any]:
    checked = _check_view_ref(view)
    record = {
        "type": "onboarding_view",
        "slice": ONBOARDING_FIVE_SLICE,
        "view_id": checked.view_id, "seq": checked.seq,
        "view_filter": checked.view_filter,
    }
    record.update(_provenance_record(checked))
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    checked = validate_panel(panel, source)
    record = {"type": "onboarding_panel",
              "slice": ONBOARDING_FIVE_SLICE}
    record.update(checked.to_record())
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    if isinstance(verdict, OnboardingVerdict):
        checked = validate_verdict(verdict, source)
    else:
        checked = derive_verdict(_source_book(verdict), view)
    record = {"type": "onboarding_verdict",
              "slice": ONBOARDING_FIVE_SLICE}
    record.update(checked.to_record())
    return record


def step_record(step: Any) -> Dict[str, Any]:
    checked = _check_step_ref(step)
    record = {
        "type": "onboarding_step",
        "slice": ONBOARDING_FIVE_SLICE,
        "step_id": checked.step_id, "seq": checked.seq,
        "phase": checked.phase,
    }
    record.update(_provenance_record(checked))
    return record


def offer_record(offer: Any) -> Dict[str, Any]:
    checked = _check_offer_ref(offer)
    record = {
        "type": "onboarding_offer",
        "slice": ONBOARDING_FIVE_SLICE,
        "offer_id": checked.offer_id,
        "provider": checked.provider,
        "decision": checked.decision,
    }
    record.update(_provenance_record(checked))
    return record


def walk_record(source: Any) -> Dict[str, Any]:
    walk = derive_walk(source)
    record = {"type": "onboarding_walk",
              "slice": ONBOARDING_FIVE_SLICE}
    record.update(walk.to_record())
    return record


def book_record(book: Any) -> Dict[str, Any]:
    checked = _source_book(book)
    record = {"type": "onboarding_book",
              "slice": ONBOARDING_FIVE_SLICE, "title": checked.title}
    record.update(checked.to_record())
    return record


# ---------------------------------------------------------------------
# Plain words and formatters.
# ---------------------------------------------------------------------

def plain_words(detection: Any, source: Any = None) -> str:
    checked = _check_detection_ref(detection)
    return (
        f"{checked.provider} - looked for by {checked.probe}: "
        f"{checked.outcome}. {checked.detail}")


def detection_plain_words(detection: Any, source: Any = None) -> str:
    return plain_words(detection, source)


def panel_plain_words(source: Any, view: Any = None) -> str:
    panel = derive_panel(source, view)
    return panel.account[0] if panel.account else ""


def verdict_plain_words(source: Any, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return (
        f"The onboarding book stands {verdict.verdict}: "
        f"{verdict.passing_shown} of {verdict.total_shown} shown "
        f"providers stand found.")


def view_plain_words(view: Any) -> str:
    checked = _check_view_ref(view)
    return f"View {checked.view_id}: shows {checked.view_filter} detections."


def walk_plain_words(source: Any) -> str:
    walk = derive_walk(source)
    phases = ", ".join(step.phase for step in walk.steps) or "none"
    return (
        f"The walk stands in {len(walk.steps)} steps ({phases}) and "
        f"stands in order: {walk.passes()} - success before "
        f"configuration, always.")


def format_detection(detection: Any, source: Any = None) -> str:
    checked = _check_detection_ref(detection)
    lines = [f"{checked.provider} ({checked.detection_id})"]
    lines.extend(plain_lines(checked))
    lines.append(checked.detail)
    if detection_passes(checked):
        lines.append("This provider stands found, ready for a first task.")
    else:
        lines.append(
            "This provider stands absent - named in its gaps, "
            "never faked as found.")
    return "\n".join(lines)


def format_view(view: Any) -> str:
    checked = _check_view_ref(view)
    return (
        f"View {checked.view_id}: filter {checked.view_filter} - "
        f"{checked.detail}")


def format_offer(offer: Any) -> str:
    checked = _check_offer_ref(offer)
    return (
        f"Offer {checked.offer_id}: Kista key-keeping for "
        f"{checked.provider} - {checked.decision}. {checked.detail}")


def format_book(source: Any = None, outcome: Any = None) -> str:
    book = _source_book(source)
    detections = (detections_for_outcome(book, outcome)
                  if outcome is not None else book.detections)
    lines = [f"Onboarding in Five Minutes (M-184) - {book.title}"]
    lines.extend(segment_of(detection) for detection in detections)
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    panel = derive_panel(source, view)
    lines = [f"Onboarding panel under view {panel.view_id}:"]
    lines.extend(row.segment for row in panel.rows)
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, view: Any = None) -> str:
    verdict = derive_verdict(source, view)
    return verdict_plain_words(source, view) + (
        f" (view {verdict.view_id}, as of {verdict.latest_on})")


def format_walk(source: Any = None) -> str:
    book = _source_book(source)
    walk = derive_walk(book)
    lines = ["The first-run walk, in held order:"]
    for step in walk.steps:
        lines.append(
            f"{step.seq}. [{step.phase}] {step.title} - {step.detail}")
    lines.append(walk_plain_words(book))
    for offer in book.offers:
        lines.append(format_offer(offer))
    return "\n".join(lines)


def format_onboarding_five_screen(source: Any = None) -> str:
    book = _source_book(source)
    lines = [
        "Onboarding in Five Minutes (M-184)",
        f"{book.title}: {len(book.detections)} detections held, "
        f"{len(passing_detections(book))} providers standing found, "
        f"{len(book.steps)} walk steps held in order.",
    ]
    if book.views:
        panel = derive_panel(book, book.views[0])
        lines.append(
            f"{panel.total_shown} of {panel.total_items} items show "
            f"under the first view.")
        lines.extend(row.segment for row in panel.rows)
    lines.append(PLAIN_EXPLANATION)
    return "\n".join(lines)


def parse_onboarding_args(args: Any) -> Tuple[str, Any]:
    """Parse the /onboard grammar into (action, target)."""
    text = "" if args is None else str(args)
    parts = text.split()
    if not parts or parts == ["show"]:
        return ("show", None)
    head = parts[0].lower()
    if head in ("detection", "offer", "view", "outcome"):
        if len(parts) != 2:
            raise ValueError(USAGE)
        return (head, parts[1])
    if head in ("walk", "panel", "verdict") and len(parts) == 1:
        return (head, None)
    raise ValueError(USAGE)
