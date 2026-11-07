"""Plan mode perfected (roadmap slice M-100).

Part V - Autonomy & Safety. The roadmap's words:
``in plan posture the coder may read everything
and write nothing; the plan it produces is slices
with acceptance checks (Part IX form), and
approving the plan is the one gate to building.``

What already shipped, and what this slice adds:

* The M-095 permission profiles ship a Read-Only
  Scout posture - tools bound ``read_only``, paths
  bound ``read``, network and commands denied -
  and the elder ``core/policy.py`` ToolPolicy knows
  a read-only mode. A posture is an answer to what
  a session may touch; neither road produces a
  plan, and neither makes approval of one specific
  plan the gate to building. A session could sit
  read-only forever and still have nothing to
  approve, or leave read-only with no plan at all.
* This slice is that missing gate, as a pure
  layer: a plan posture (read everything, write
  nothing, execute nothing), a plan document in
  Part IX form - an ordered list of slices, each
  carrying a title, an intent, and acceptance
  checks, in the shape the roadmap itself uses -
  and approval of that one plan as the single
  gate between planning and building. The layer
  decides mechanically, validates the plan as
  data, and formats the status line and the
  refusal. This module writes no file, changes no
  setting, runs nothing and approves nothing in
  the world itself; the agent layer owns storing
  the gate, holding the current plan, asking this
  layer before a tool runs or a build begins, and
  publishing a refusal as session news.

Honesty rules, enforced here and pinned by tests:

* **Read-all / write-nothing is mechanical.** In
  plan posture a ``read`` effect is allowed and
  ``write`` / ``execute`` effects are denied -
  from the effect alone, never from vibes about
  the call. Out of plan posture every effect is
  allowed: building is the normal posture.
* **The gate ships OFF.** With no stored setting,
  plan mode is off. Entering the posture is a
  deliberate act, never a silent default, and a
  malformed stored setting raises instead of
  being guessed at.
* **Approval belongs to one plan.** A plan starts
  unapproved. ``approve`` returns an approved
  copy; the original stays unapproved, and no
  other plan gains approval by association.
* **A plan with no slices is not a plan, and a
  slice without acceptance checks is not a
  slice.** Validation refuses an empty plan, a
  blank title or intent, and a slice carrying no
  check - Part IX form is the whole point, so
  the form is enforced, never assumed.
* **Refusals are news.** A denied write or a
  refused build renders as a structured refusal
  record (``type: plan_mode_refusal``, ``news``
  true, surfaced as a session event) and as one
  plain headline, mirroring the path jail and
  the network gates.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, Optional, Sequence, Tuple

__all__ = [
    "DECISIONS",
    "EFFECTS",
    "PLAIN_EXPLANATION",
    "PLAN_MODE_SLICE",
    "SETTING_KEY",
    "USAGE",
    "GateChange",
    "Plan",
    "PlanRefusal",
    "PlanSlice",
    "approve",
    "approve_plan",
    "build_plan",
    "build_refusal",
    "can_build",
    "decide",
    "decide_effect",
    "enabled_from_config",
    "format_gate_change",
    "format_plan",
    "format_plan_mode",
    "format_plan_status",
    "format_refusal",
    "parse_plan_args",
    "plan_mode_enabled",
    "refusal_for_build",
    "refusal_for_effect",
    "refusal_record",
    "set_enabled",
    "validate_plan",
    "validate_plan_slice",
]

PLAN_MODE_SLICE = "M-100"

SETTING_KEY = "plan_mode"

DECISIONS = ("allow", "deny")

#: The effects a tool call can have, as data.
EFFECTS = ("read", "write", "execute")

#: Tool-kind words the surfaces already use, read
#: as the effect they name. An effect word itself
#: is always accepted; anything else raises.
_EFFECT_ALIASES = {
    "path_read": "read",
    "path_write": "write",
    "edit": "write",
    "command": "execute",
    "run": "execute",
}

PLAIN_EXPLANATION = (
    "Plan mode is a read-everything, write-nothing "
    "posture: while it is on, the coder may read and "
    "plan but may not write or execute, the plan it "
    "produces is an ordered list of slices - each "
    "with a title, an intent, and acceptance checks "
    "- in Part IX form, and approving that one plan "
    "is the only gate to building; with plan mode "
    "off, building is the normal posture. This "
    "layer judges and formats only; it writes "
    "nothing itself."
)

USAGE = (
    "Usage: /plan, /plan show, /plan on, /plan off, "
    "/plan approve, /plan build, "
    "/plan check <read|write|execute>"
)

_PLAN_KEYS = frozenset(
    {"title", "intent", "what", "slices", "approved",
     "type", "slice"})

_SLICE_KEYS = frozenset(
    {"title", "intent", "what", "acceptance_checks",
     "checks"})


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _effect_for(value: Any) -> str:
    """The canonical effect a word names, or a refusal."""
    if isinstance(value, str):
        wanted = value.strip().lower()
        if wanted in EFFECTS:
            return wanted
        if wanted in _EFFECT_ALIASES:
            return _EFFECT_ALIASES[wanted]
    raise ValueError(
        "an effect must be one of %s, got %r"
        % ("/".join(EFFECTS), value))


def _check_posture(plan_mode_on: Any) -> bool:
    if not isinstance(plan_mode_on, bool):
        raise ValueError(
            f"plan_mode_on must be true or false, got {plan_mode_on!r}")
    return plan_mode_on


def _clean_checks(value: Any) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(
            value, (list, tuple)):
        raise ValueError(
            "acceptance checks must be a list of strings")
    checks = tuple(
        _clean_text(check, "an acceptance check") for check in value)
    if not checks:
        raise ValueError(
            "a plan slice needs at least one acceptance check")
    return checks


# ---------------------------------------------------------------------
# The plan document: Part IX form, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PlanSlice:
    """One slice of a plan: title, intent, checks.

    Constructing one validates it - a blank title
    or intent, or no acceptance check, raises -
    so a PlanSlice that exists is in Part IX form.
    """

    title: str
    intent: str
    acceptance_checks: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a slice title"))
        object.__setattr__(
            self, "intent", _clean_text(self.intent, "a slice intent"))
        object.__setattr__(
            self, "acceptance_checks",
            _clean_checks(self.acceptance_checks))

    @property
    def what(self) -> str:
        """The slice's intent, under its other name."""
        return self.intent

    def to_record(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "intent": self.intent,
            "acceptance_checks": list(self.acceptance_checks),
        }


@dataclass(frozen=True)
class Plan:
    """One plan: an ordered list of slices, plus approval.

    A plan starts unapproved (``approved`` false).
    Approval never edits a plan in place - see
    :func:`approve`, which returns a new plan - so
    an approval cannot leak into a plan it was
    not given to.
    """

    title: str
    intent: str
    slices: Tuple[PlanSlice, ...]
    approved: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _clean_text(self.title, "a plan title"))
        object.__setattr__(
            self, "intent", _clean_text(self.intent, "a plan intent"))
        if isinstance(self.slices, (str, bytes)) or not isinstance(
                self.slices, (list, tuple)):
            raise ValueError("a plan's slices must be a list of slices")
        slices = tuple(self.slices)
        if not slices:
            raise ValueError("a plan needs at least one slice")
        for slice_ in slices:
            if not isinstance(slice_, PlanSlice):
                raise ValueError(
                    "a plan's slices must be plan slices, "
                    f"got {slice_!r}")
        object.__setattr__(self, "slices", slices)
        if not isinstance(self.approved, bool):
            raise ValueError(
                f"a plan's approved flag must be true or false, "
                f"got {self.approved!r}")

    @property
    def what(self) -> str:
        """The plan's intent, under its other name."""
        return self.intent

    @property
    def slice_count(self) -> int:
        return len(self.slices)

    @property
    def check_count(self) -> int:
        return sum(len(s.acceptance_checks) for s in self.slices)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "plan",
            "slice": PLAN_MODE_SLICE,
            "title": self.title,
            "intent": self.intent,
            "approved": self.approved,
            "slices": [s.to_record() for s in self.slices],
        }


def validate_plan_slice(spec: Any) -> PlanSlice:
    """Validate one plan-slice mapping into a PlanSlice.

    The mapping names a ``title``, an ``intent``
    (or ``what``), and ``acceptance_checks`` (or
    ``checks``). Unknown keys refuse, a missing
    piece refuses, and the checks must be a
    non-empty list of non-empty strings - a slice
    without checks is not a slice.
    """
    if isinstance(spec, PlanSlice):
        return spec
    if not isinstance(spec, dict):
        raise ValueError("a plan slice must be a mapping")
    unknown = set(spec) - _SLICE_KEYS
    if unknown:
        raise ValueError(
            "unknown plan slice keys: %s"
            % ", ".join(sorted(unknown)))
    if "title" not in spec:
        raise ValueError("a plan slice is missing its title")
    intent = spec.get("intent", spec.get("what"))
    if intent is None:
        raise ValueError("a plan slice is missing its intent")
    if "intent" in spec and "what" in spec \
            and spec["intent"] != spec["what"]:
        raise ValueError(
            "a plan slice names two different intents")
    checks = spec.get("acceptance_checks", spec.get("checks"))
    if checks is None:
        raise ValueError(
            "a plan slice is missing its acceptance checks")
    return PlanSlice(
        title=spec["title"], intent=intent,
        acceptance_checks=_clean_checks(checks))


def validate_plan(spec: Any) -> Plan:
    """Validate a whole plan mapping into a Plan.

    The mapping names a ``title``, an ``intent``
    (or ``what``), and a non-empty ordered
    ``slices`` list; ``approved`` may ride along
    as a bool and defaults to false - a plan
    starts unapproved. Every slice must validate
    as a plan slice. One malformed piece refuses
    the whole plan rather than silently narrowing
    what was written.
    """
    if isinstance(spec, Plan):
        return spec
    if not isinstance(spec, dict):
        raise ValueError("a plan must be a mapping")
    unknown = set(spec) - _PLAN_KEYS
    if unknown:
        raise ValueError(
            "unknown plan keys: %s" % ", ".join(sorted(unknown)))
    if "title" not in spec:
        raise ValueError("a plan is missing its title")
    intent = spec.get("intent", spec.get("what"))
    if intent is None:
        raise ValueError("a plan is missing its intent")
    if "intent" in spec and "what" in spec \
            and spec["intent"] != spec["what"]:
        raise ValueError("a plan names two different intents")
    if "slices" not in spec:
        raise ValueError("a plan is missing its slices")
    raw_slices = spec["slices"]
    if isinstance(raw_slices, (str, bytes)) or not isinstance(
            raw_slices, (list, tuple)):
        raise ValueError("a plan's slices must be a list of slices")
    slices = tuple(validate_plan_slice(s) for s in raw_slices)
    approved = spec.get("approved", False)
    if not isinstance(approved, bool):
        raise ValueError(
            f"a plan's approved flag must be true or false, "
            f"got {approved!r}")
    return Plan(title=spec["title"], intent=intent,
                slices=slices, approved=approved)


def build_plan(title: Any, intent: Any,
               slices: Sequence[Any]) -> Plan:
    """Build one validated plan from its pieces."""
    if isinstance(slices, (str, bytes)) or not isinstance(
            slices, (list, tuple)):
        raise ValueError("a plan's slices must be a list of slices")
    return Plan(
        title=_clean_text(title, "a plan title"),
        intent=_clean_text(intent, "a plan intent"),
        slices=tuple(validate_plan_slice(s) for s in slices))


def approve(plan: Any) -> Plan:
    """The approved copy of *plan*.

    The original is untouched - approval is a new
    record, so it belongs to this plan alone and
    cannot leak into another plan built from the
    same slices. Approving an approved plan
    returns an approved copy again.
    """
    if not isinstance(plan, Plan):
        raise ValueError(f"approve needs a plan, got {plan!r}")
    return replace(plan, approved=True)


#: Approval under its longer name.
approve_plan = approve


# ---------------------------------------------------------------------
# The plan_mode gate: stored posture, read purely.
# ---------------------------------------------------------------------


def enabled_from_config(config: Dict[str, Any]) -> bool:
    """The plan_mode gate stored in *config*.

    Absent means False (plan mode ships OFF -
    building is the normal posture). A stored
    value that is not a bool raises - never
    guessed at.
    """
    raw = config.get(SETTING_KEY, False)
    if not isinstance(raw, bool):
        raise ValueError(
            f"{SETTING_KEY} must be true or false, "
            f"got {type(raw).__name__}")
    return raw


#: The gate reader under its posture name.
plan_mode_enabled = enabled_from_config


@dataclass(frozen=True)
class GateChange:
    """A recorded change of the plan_mode gate."""

    before: bool
    after: bool

    def event(self) -> Dict[str, Any]:
        return {"type": "plan_mode_setting_changed",
                "from": self.before, "to": self.after}

    def record(self, session_id: Optional[str],
               journaled: bool) -> Dict[str, Any]:
        return {"type": "plan_mode_setting_changed",
                "from": self.before, "to": self.after,
                "session_id": session_id, "journaled": journaled}


def set_enabled(config: Dict[str, Any],
                enabled: Any) -> Tuple[bool, GateChange]:
    """Validate a gate change against *config*, purely."""
    if not isinstance(enabled, bool):
        raise ValueError(
            f"{SETTING_KEY} is turned on or off; got {enabled!r}")
    before = enabled_from_config(config)
    if enabled == before:
        raise ValueError(
            f"plan mode is already {'on' if before else 'off'}")
    return enabled, GateChange(before=before, after=enabled)


# ---------------------------------------------------------------------
# The mechanical judgements: effects, and the build gate.
# ---------------------------------------------------------------------


def decide(plan_mode_on: bool, effect: str) -> str:
    """One mechanical answer: ``allow`` or ``deny``.

    In plan posture a ``read`` effect is allowed
    and ``write`` / ``execute`` effects are denied
    - the coder may read everything and write
    nothing. Out of plan posture every effect is
    allowed. An unknown effect raises - a question
    this layer does not cover is never guessed at.
    """
    on = _check_posture(plan_mode_on)
    canonical = _effect_for(effect)
    if not on:
        return "allow"
    return "allow" if canonical == "read" else "deny"


#: The judgement under its effect-shaped name.
decide_effect = decide


def can_build(plan_mode_on: bool, plan: Optional[Plan]) -> bool:
    """Whether building may begin, mechanically.

    Out of plan posture building is the normal
    posture and is always allowed. In plan posture
    an approved plan is the one gate: building is
    allowed only when *plan* exists and is
    approved. Anything that is not a plan refuses
    by raising - stored data is never guessed at.
    """
    on = _check_posture(plan_mode_on)
    if plan is not None and not isinstance(plan, Plan):
        raise ValueError(f"can_build needs a plan or None, got {plan!r}")
    if not on:
        return True
    return plan is not None and plan.approved


# ---------------------------------------------------------------------
# Refusals, shaped as news.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PlanRefusal:
    """One refusal, shaped as news for the session.

    A write attempted in plan posture, or a build
    attempted without an approved plan, is a gate
    doing its named work - the agent layer
    publishes this record as a session event, and
    ``news`` is true with ``surface`` naming that
    road, mirroring the path jail and the network
    gates.
    """

    reason: str
    effect: Optional[str] = None
    plan_title: Optional[str] = None

    @property
    def headline(self) -> str:
        return f"Plan mode refusal: {self.reason}"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "plan_mode_refusal",
            "slice": PLAN_MODE_SLICE,
            "news": True,
            "surface": "session_event",
            "effect": self.effect,
            "plan_title": self.plan_title,
            "reason": self.reason,
            "headline": self.headline,
        }


def build_refusal(effect: Any = None, plan: Any = None,
                  reason: Optional[str] = None) -> PlanRefusal:
    """The refusal record for one denied act.

    Names the denied *effect* or the unapproved
    *plan* the build was gated on; a caller may
    state the *reason* plainly, or the layer
    states its own from the gate's rules.
    """
    canonical = _effect_for(effect) if effect is not None else None
    if plan is not None and not isinstance(plan, Plan):
        raise ValueError(f"a refusal needs a plan or None, got {plan!r}")
    if reason is None:
        if canonical is not None:
            reason = (
                f"a {canonical} effect is denied in plan "
                "posture - plan mode may read everything "
                "and write nothing")
        elif plan is None:
            reason = (
                "building in plan posture needs an "
                "approved plan, and no plan is approved")
        else:
            reason = (
                f"building in plan posture needs an "
                f"approved plan, and {plan.title!r} is "
                "not approved")
    return PlanRefusal(
        reason=_clean_text(reason, "a refusal reason"),
        effect=canonical,
        plan_title=plan.title if plan is not None else None)


def refusal_for_effect(plan_mode_on: bool, effect: str) -> PlanRefusal:
    """The refusal for one effect, or a plain error if allowed."""
    if decide(plan_mode_on, effect) == "allow":
        raise ValueError(
            f"a {_effect_for(effect)} effect is allowed here; "
            "there is no refusal")
    return build_refusal(effect=effect)


def refusal_for_build(plan_mode_on: bool,
                      plan: Optional[Plan]) -> PlanRefusal:
    """The refusal for one gated build, or an error if allowed."""
    if can_build(plan_mode_on, plan):
        raise ValueError("building is allowed here; there is no refusal")
    return build_refusal(plan=plan)


def refusal_record(effect: Any = None, plan: Any = None,
                   reason: Optional[str] = None) -> Dict[str, Any]:
    """The journal-shaped record of one refusal."""
    return build_refusal(
        effect=effect, plan=plan, reason=reason).to_record()


def format_refusal(refusal: Any) -> str:
    """One refusal as the headline the session shows."""
    if isinstance(refusal, PlanRefusal):
        return refusal.headline
    if isinstance(refusal, dict) \
            and refusal.get("type") == "plan_mode_refusal":
        return str(refusal["headline"])
    raise ValueError("format_refusal needs a plan mode refusal")


# ---------------------------------------------------------------------
# The /plan surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def parse_plan_args(args: str) -> Dict[str, Any]:
    """Parse the /plan grammar both surfaces share.

    No words (or ``show`` / ``status``) shows the
    posture; ``on`` / ``off`` steer the gate;
    ``approve`` approves the current plan;
    ``build`` asks the build gate; ``check
    <effect>`` decides one effect (the effect is
    validated here). Anything else is a usage
    error naming the grammar.
    """
    text = (args or "").strip()
    if not text or text in ("show", "status"):
        return {"action": "show"}
    if text in ("on", "off", "approve", "build"):
        return {"action": text}
    words = text.split(None, 1)
    if words[0] == "check":
        if len(words) != 2 or not words[1].strip():
            raise ValueError(USAGE)
        try:
            effect = _effect_for(words[1].strip())
        except ValueError:
            raise ValueError(USAGE) from None
        return {"action": "check", "effect": effect}
    raise ValueError(USAGE)


def format_gate_change(record: Dict[str, Any]) -> str:
    state = "on" if record.get("to") else "off"
    return f"Plan mode is now {state}."


def format_plan_status(config: Dict[str, Any],
                       plan: Optional[Plan] = None) -> str:
    """The status line's one sentence for the posture."""
    if plan is not None and not isinstance(plan, Plan):
        raise ValueError(f"a status needs a plan or None, got {plan!r}")
    on = enabled_from_config(config)
    if plan is None:
        plan_part = "no plan yet"
    else:
        plan_part = (
            f"plan {plan.title!r}: {plan.slice_count} slice(s), "
            f"{'approved' if plan.approved else 'unapproved'}")
    gate = "allowed" if can_build(on, plan) else "gated on approval"
    return (
        f"Plan mode: {'on' if on else 'off'} ({SETTING_KEY}) - "
        f"{plan_part}; building {gate}.")


def format_plan(plan: Plan) -> str:
    """One whole plan, in plain words, from the plan."""
    if not isinstance(plan, Plan):
        raise ValueError(f"format_plan needs a plan, got {plan!r}")
    lines = [
        f"Plan: {plan.title} "
        f"({'approved' if plan.approved else 'unapproved'})",
        f"Intent: {plan.intent}",
        f"Slices ({plan.slice_count}), "
        f"acceptance checks ({plan.check_count}):",
    ]
    for index, slice_ in enumerate(plan.slices, start=1):
        lines.append(f"  {index}. {slice_.title} - {slice_.intent}")
        for check in slice_.acceptance_checks:
            lines.append(f"     - {check}")
    return "\n".join(lines)


def format_plan_mode(config: Dict[str, Any],
                     plan: Optional[Plan] = None) -> str:
    """The whole slice, in plain words, for /plan.

    Built from the stored gate and the plan
    itself, so the show surface can never drift
    from the posture it names.
    """
    lines = ["Plan mode (M-100) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_plan_status(config, plan))
    if plan is not None:
        lines.append("")
        lines.append(format_plan(plan))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)
