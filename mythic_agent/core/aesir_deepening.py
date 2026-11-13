"""Aesir deepening (roadmap slice M-245) — pure layer.

Part X — Bridges. The roadmap words: **Aesir sessions
selectable per role; its honest capability reports shape
what the router asks of it.**

What already ships, and what this slice adds:

* Project Aesir already stands in the Provider Ocean as a
  provider (M-025, ``mythic_agent/providers/aesir.py``):
  its adapter reports its capability limits *as Aesir
  reports them* — streaming yes; general tool calling,
  vision and embeddings no; structured output only as a
  strict Boolean ``json_schema`` subset; one resident
  model at a time, and a catalog listing that is never
  readiness. :meth:`AesirProvider.reported_capabilities`
  returns that picture, with the live half (backend,
  profile, context, resident model, digest) filled from
  the server's own readiness record when it answers and
  ``None`` — an honest unknown — when it does not.
* Roles already stand as the crew's offices (M-029,
  ``mythic_agent/core/role_routing.py``): nine offices,
  each with an effective route the router resolves from
  the session config. Until this slice, nothing recorded
  *which* offices may ride Aesir, and nothing shaped a
  router ask by Aesir's reported limits — a route could
  name Aesir for work Aesir itself says it cannot do.

This layer is the deepening, held as data:

* A **capability report** is held whole and validated
  against Aesir's documented v1 ceiling. A report may
  only ever *narrow* what Aesir is asked: a report
  claiming a capability beyond the ceiling (general
  tool calling, vision, embeddings, free-form JSON
  mode, more than one resident model) refuses BY NAME —
  the deepening never widens Aesir's own telling.
  Live fields a report does not carry stay ``None``;
  an unknown is never dressed up as a fact, and
  ``reachable`` false means no ask is shaped at all.
* A **selection book** (packaged data, schema
  ``mythic.aesir_deepening/1``) records, per office,
  whether an Aesir session is selectable for that role
  and why, in plain words tied to a named capability.
  An office the crew does not hold refuses BY NAME; a
  duplicated or half-written selection refuses whole.
  The book is data: a new casting of the selections
  needs no code change.
* An **ask** is DERIVED at call time from one office,
  its selection, one report and the caller's named
  needs: the router may ask Aesir only for what the
  report grants. A need the report denies is refused
  BY NAME in the ask; a ``json_mode`` need is granted
  only in its Boolean-subset shape, and says so; a need
  naming a model is granted only for the resident
  model — catalog membership is never readiness. An
  office not selected for Aesir, or a report that is
  unreachable, shapes no ask at all: the verdict names
  the session default as the road instead.

Honest boundary: this layer holds reports, selections
and derived asks as data. It opens no session, calls
no model, probes no server and rewrites no route; the
agent layer owns holding a session's selections and
applying a shaped ask on the router's road.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

import yaml

from ..resources import load_resource
from .role_routing import office_ids
from .validation import ValidationError

__all__ = [
    "AESIR_SCHEMA",
    "AESIR_SLICE",
    "CAPABILITY_CEILING",
    "NEEDS",
    "PLAIN_EXPLANATION",
    "SELECTION_RESOURCE",
    "USAGE",
    "AesirAsk",
    "AesirCapabilityReport",
    "AesirSelection",
    "SelectionBook",
    "format_ask",
    "format_report",
    "format_selection",
    "format_selections",
    "load_selection_book",
    "load_selection_book_file",
    "normalize_report",
    "plain_words",
    "selection_record",
    "shape_ask",
    "validate_report",
    "validate_selection",
    "validate_selection_book",
]

AESIR_SLICE = "M-245"

#: The packaged data resource holding the shipped selections.
SELECTION_RESOURCE = "aesir_deepening.yaml"

#: The schema word a selection book file must carry.
AESIR_SCHEMA = "mythic.aesir_deepening/1"

#: Aesir's documented v1 capability ceiling (M-025): the
#: most any report may ever claim. Reports narrow from
#: here; they never widen past it.
CAPABILITY_CEILING: Dict[str, Any] = {
    "streaming": True,
    "tool_calling": False,
    "vision": False,
    "json_mode": False,
    "embeddings": False,
    "resident_models": 1,
}

#: The needs a router ask may name. ``structured_boolean``
#: is the one structured-output shape Aesir accepts.
NEEDS: Tuple[str, ...] = (
    "streaming",
    "tool_calling",
    "vision",
    "json_mode",
    "structured_boolean",
    "embeddings",
)

_FLAG_KEYS = ("streaming", "tool_calling", "vision",
              "json_mode", "embeddings")
_LIVE_KEYS = ("backend", "profile", "context", "model",
              "model_digest")
_REPORT_KEYS = frozenset(
    _FLAG_KEYS + _LIVE_KEYS
    + ("tool_calling_note", "json_mode_note",
       "resident_models", "catalog_is_readiness", "reachable"))
_SELECTION_KEYS = frozenset(
    ("office", "selected", "reason", "capability"))
_BOOK_KEYS = frozenset(("schema", "selections"))

PLAIN_EXPLANATION = (
    "Aesir can be chosen per role, and Aesir's own "
    "honest report decides what it may be asked. The "
    "selection book names, for each crew office, whether "
    "an Aesir session may be picked for that role and "
    "why. When the router shapes an ask, it may ask "
    "Aesir only for what Aesir reports it can do: plain "
    "streamed words, and a strict yes-or-no structured "
    "answer — never tools, never pictures, never a "
    "model that is merely listed instead of resident. "
    "If Aesir is not answering, or the role is not "
    "selected, the ask is not shaped at all and the "
    "session default carries the work instead.")

USAGE = (
    "shape_ask(config-free): pick an office, read its "
    "selection from the book, take Aesir's reported "
    "capabilities as they stand, and name the needs; "
    "the returned ask lists what is granted and what "
    "is refused, by name, or declines to shape an ask "
    "and names the session-default road instead.")


def plain_words() -> str:
    """The plain-language explanation of this slice."""
    return PLAIN_EXPLANATION


@dataclass(frozen=True)
class AesirCapabilityReport:
    """Aesir's capability picture, held whole and honest.

    Flag fields are exactly Aesir's reported flags;
    live fields are the server's own telling or
    ``None`` when it did not answer.
    """

    streaming: bool
    tool_calling: bool
    vision: bool
    json_mode: bool
    embeddings: bool
    resident_models: int
    reachable: bool
    backend: Optional[str] = None
    profile: Optional[str] = None
    context: Optional[int] = None
    model: Optional[str] = None
    model_digest: Optional[str] = None

    def record(self) -> Dict[str, Any]:
        """This report as a plain mapping."""
        return {
            "streaming": self.streaming,
            "tool_calling": self.tool_calling,
            "vision": self.vision,
            "json_mode": self.json_mode,
            "embeddings": self.embeddings,
            "resident_models": self.resident_models,
            "reachable": self.reachable,
            "backend": self.backend,
            "profile": self.profile,
            "context": self.context,
            "model": self.model,
            "model_digest": self.model_digest,
        }


def validate_report(raw: Any) -> AesirCapabilityReport:
    """Validate a reported-capabilities mapping, whole.

    Raises :class:`ValidationError` naming the problem:
    a non-mapping, an unknown key, a non-boolean flag,
    a claim past Aesir's documented ceiling, a resident
    count that is not a positive whole number, or a
    live field of the wrong shape. Missing flags fall
    back to the ceiling's own (narrowest honest) value;
    missing live fields stay ``None``.
    """
    if not isinstance(raw, dict):
        raise ValidationError(
            "an Aesir capability report must be a mapping, "
            f"not {type(raw).__name__}")
    unknown = sorted(set(raw) - _REPORT_KEYS)
    if unknown:
        raise ValidationError(
            "unknown capability report keys: "
            + ", ".join(unknown))
    flags: Dict[str, bool] = {}
    for key in _FLAG_KEYS:
        value = raw.get(key, CAPABILITY_CEILING[key])
        if not isinstance(value, bool):
            raise ValidationError(
                f"capability {key!r} must be true or false, "
                f"not {value!r}")
        if value and not CAPABILITY_CEILING[key]:
            raise ValidationError(
                f"capability {key!r} claims more than Aesir's "
                "documented v1 ceiling allows; a report may "
                "narrow Aesir's telling, never widen it")
        flags[key] = value
    resident = raw.get("resident_models",
                       CAPABILITY_CEILING["resident_models"])
    if (not isinstance(resident, int)
            or isinstance(resident, bool) or resident < 1):
        raise ValidationError(
            "resident_models must be a positive whole "
            f"number, not {resident!r}")
    if resident > CAPABILITY_CEILING["resident_models"]:
        raise ValidationError(
            "resident_models claims more resident models "
            "than Aesir's documented v1 ceiling allows; a "
            "report may narrow Aesir's telling, never "
            "widen it")
    if raw.get("catalog_is_readiness"):
        raise ValidationError(
            "catalog_is_readiness may never stand true: a "
            "catalog listing is not readiness")
    reachable = raw.get("reachable", False)
    if not isinstance(reachable, bool):
        raise ValidationError(
            f"reachable must be true or false, not "
            f"{reachable!r}")
    live: Dict[str, Any] = {}
    for key in _LIVE_KEYS:
        value = raw.get(key)
        if value is None:
            live[key] = None
        elif key == "context":
            if (not isinstance(value, int)
                    or isinstance(value, bool) or value < 1):
                raise ValidationError(
                    "context must be a positive whole "
                    f"number or unknown, not {value!r}")
            live[key] = value
        elif isinstance(value, str) and value:
            live[key] = value
        else:
            raise ValidationError(
                f"{key} must be a non-empty string or "
                f"unknown, not {value!r}")
    return AesirCapabilityReport(
        resident_models=resident, reachable=reachable,
        **flags, **live)


#: Reading a report and validating it are the same road.
normalize_report = validate_report


@dataclass(frozen=True)
class AesirSelection:
    """One office's Aesir selection, held as data."""

    office: str
    selected: bool
    reason: str
    capability: str

    def record(self) -> Dict[str, Any]:
        """This selection as a plain mapping."""
        return {"office": self.office,
                "selected": self.selected,
                "reason": self.reason,
                "capability": self.capability}


def validate_selection(raw: Any) -> AesirSelection:
    """Validate one selection record, whole, by name."""
    if not isinstance(raw, dict):
        raise ValidationError(
            "an Aesir selection must be a mapping, not "
            f"{type(raw).__name__}")
    unknown = sorted(set(raw) - _SELECTION_KEYS)
    if unknown:
        raise ValidationError(
            "unknown selection keys: " + ", ".join(unknown))
    office = raw.get("office")
    if office not in office_ids():
        raise ValidationError(
            f"unknown office {office!r}; the crew holds: "
            + ", ".join(office_ids()))
    selected = raw.get("selected")
    if not isinstance(selected, bool):
        raise ValidationError(
            "selected must be true or false, not "
            f"{selected!r}")
    reason = raw.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise ValidationError(
            "a selection must carry its reason in plain "
            "words")
    capability = raw.get("capability")
    if capability not in NEEDS + ("none",):
        raise ValidationError(
            f"unknown capability {capability!r}; a "
            "selection names one of: "
            + ", ".join(NEEDS + ("none",)))
    return AesirSelection(office=office, selected=selected,
                          reason=reason.strip(),
                          capability=capability)


@dataclass(frozen=True)
class SelectionBook:
    """The whole selection book: one record per office."""

    selections: Tuple[AesirSelection, ...]

    def for_office(self, office_id: Any) -> AesirSelection:
        """The selection for *office_id*, refused by name."""
        if office_id not in office_ids():
            raise ValidationError(
                f"unknown office {office_id!r}; the crew "
                "holds: " + ", ".join(office_ids()))
        for selection in self.selections:
            if selection.office == office_id:
                return selection
        raise ValidationError(
            f"the selection book holds no selection for "
            f"office {office_id!r}")

    def record(self) -> Dict[str, Any]:
        """This book as a plain mapping."""
        return {"schema": AESIR_SCHEMA,
                "selections": [s.record()
                               for s in self.selections]}


def validate_selection_book(raw: Any) -> SelectionBook:
    """Validate a whole selection book mapping, whole."""
    if not isinstance(raw, dict):
        raise ValidationError(
            "a selection book must be a mapping, not "
            f"{type(raw).__name__}")
    unknown = sorted(set(raw) - _BOOK_KEYS)
    if unknown:
        raise ValidationError(
            "unknown selection book keys: "
            + ", ".join(unknown))
    if raw.get("schema") != AESIR_SCHEMA:
        raise ValidationError(
            f"a selection book must carry schema "
            f"{AESIR_SCHEMA!r}")
    rows = raw.get("selections")
    if not isinstance(rows, list) or not rows:
        raise ValidationError(
            "a selection book must hold a non-empty "
            "selections list")
    selections = tuple(validate_selection(row) for row in rows)
    seen = set()
    for selection in selections:
        if selection.office in seen:
            raise ValidationError(
                "duplicate selection for office "
                f"{selection.office!r}")
        seen.add(selection.office)
    return SelectionBook(selections=selections)


def selection_record(book: SelectionBook,
                     office_id: Any) -> Dict[str, Any]:
    """One office's selection as a plain mapping."""
    return book.for_office(office_id).record()


def load_selection_book() -> SelectionBook:
    """Load the shipped selection book from packaged data."""
    data = load_resource(SELECTION_RESOURCE)
    return validate_selection_book(data)


def load_selection_book_file(path: Any) -> SelectionBook:
    """Load and validate a selection book from any file."""
    text = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    return validate_selection_book(data)


@dataclass(frozen=True)
class AesirAsk:
    """What the router may ask of Aesir, derived whole.

    ``shaped`` false means no ask was shaped: ``road``
    names where the work goes instead, and ``granted``
    stands empty. ``refused`` names every need the
    report denied, by name, either way.
    """

    office: str
    shaped: bool
    road: str
    granted: Tuple[str, ...]
    refused: Tuple[str, ...]
    model: Optional[str]
    notes: Tuple[str, ...]

    def record(self) -> Dict[str, Any]:
        """This ask as a plain mapping."""
        return {"office": self.office,
                "shaped": self.shaped,
                "road": self.road,
                "granted": list(self.granted),
                "refused": list(self.refused),
                "model": self.model,
                "notes": list(self.notes)}


def shape_ask(book: SelectionBook,
              report: AesirCapabilityReport,
              office_id: Any,
              needs: Iterable[str] = (),
              model: Optional[str] = None) -> AesirAsk:
    """Derive what the router may ask of Aesir for a role.

    The derivation is the honesty rule made code: an
    office not selected for Aesir, or a report whose
    server is not answering, shapes no ask — the road
    named is the session default. Otherwise each named
    need is granted only as the report grants it:
    ``json_mode`` is never granted as free-form JSON,
    only reshaped to ``structured_boolean`` and noted;
    a named model is granted only when it is the
    resident model the report names.
    """
    selection = book.for_office(office_id)
    wanted = []
    for need in needs:
        if need not in NEEDS:
            raise ValidationError(
                f"unknown need {need!r}; an ask names one "
                "of: " + ", ".join(NEEDS))
        if need not in wanted:
            wanted.append(need)
    if not selection.selected:
        return AesirAsk(
            office=selection.office, shaped=False,
            road="session_default", granted=(),
            refused=tuple(wanted), model=None,
            notes=(f"office {selection.office!r} is not "
                   "selected for Aesir: "
                   + selection.reason,))
    if not report.reachable:
        return AesirAsk(
            office=selection.office, shaped=False,
            road="session_default", granted=(),
            refused=tuple(wanted), model=None,
            notes=("Aesir is not answering, so no ask is "
                   "shaped from an honest unknown",))
    granted: list = []
    refused: list = []
    notes: list = []
    for need in wanted:
        if need == "structured_boolean":
            granted.append(need)
            notes.append(
                "structured output is granted only as "
                "Aesir's strict Boolean json_schema subset")
        elif need == "json_mode":
            refused.append(need)
            granted.append("structured_boolean")
            notes.append(
                "free-form json_mode is refused by Aesir's "
                "own report; the ask is reshaped to the "
                "strict Boolean subset instead")
        elif getattr(report, need):
            granted.append(need)
        else:
            refused.append(need)
    ask_model: Optional[str] = None
    if model is not None:
        if report.model is not None and model == report.model:
            ask_model = model
        else:
            refused.append("model:" + str(model))
            notes.append(
                f"model {model!r} is not the resident "
                "model Aesir reports; a catalog listing "
                "is not readiness")
    elif report.model is not None:
        ask_model = report.model
    return AesirAsk(
        office=selection.office, shaped=True, road="aesir",
        granted=tuple(granted), refused=tuple(refused),
        model=ask_model, notes=tuple(notes))


def format_report(report: AesirCapabilityReport) -> str:
    """One report as a readable block of plain words."""
    def word(value: bool) -> str:
        return "yes" if value else "no"

    lines = [
        "Aesir capability report (as Aesir reports it):",
        f"  streaming: {word(report.streaming)}",
        f"  tool calling: {word(report.tool_calling)}",
        f"  vision: {word(report.vision)}",
        f"  json mode: {word(report.json_mode)} "
        "(strict Boolean subset only)",
        f"  embeddings: {word(report.embeddings)}",
        f"  resident models: {report.resident_models}",
        f"  reachable: {word(report.reachable)}",
    ]
    for label, value in (("backend", report.backend),
                         ("profile", report.profile),
                         ("context", report.context),
                         ("model", report.model),
                         ("model digest", report.model_digest)):
        shown = value if value is not None else "unknown"
        lines.append(f"  {label}: {shown}")
    return "\n".join(lines)


def format_selection(selection: AesirSelection) -> str:
    """One selection as a single readable line."""
    picked = "selected" if selection.selected else "not selected"
    return (f"{selection.office}: {picked} for Aesir "
            f"({selection.capability}) — {selection.reason}")


def format_selections(book: SelectionBook) -> str:
    """The whole book as readable lines, in book order."""
    lines = ["Aesir per-role selections:"]
    lines.extend(format_selection(s) for s in book.selections)
    return "\n".join(lines)


def format_ask(ask: AesirAsk) -> str:
    """One derived ask as a readable block."""
    if not ask.shaped:
        lines = [f"{ask.office}: no Aesir ask shaped; "
                 f"the road is {ask.road}."]
    else:
        lines = [f"{ask.office}: Aesir may be asked — "
                 + (", ".join(ask.granted) or "plain "
                    "generation only") + "."]
        if ask.model is not None:
            lines.append(f"  resident model: {ask.model}")
    if ask.refused:
        lines.append("  refused: " + ", ".join(ask.refused))
    lines.extend("  note: " + note for note in ask.notes)
    return "\n".join(lines)
