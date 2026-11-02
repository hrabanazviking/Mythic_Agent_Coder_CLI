"""Vision input routing (All-Features roadmap slice M-037).

Part II — The Provider Ocean — continues here. Image tasks
route only to models whose capability record says they can
see; otherwise the app says so plainly and offers the switch.

What already shipped, and what this slice adds:

* ``mythic_agent.providers.vision`` (elder slice 042)
  normalises canonical content parts into each provider
  *family*'s wire shape, with a raise/strip downgrade policy
  keyed on the provider door's own vision flag — but it
  reasons per family and per door, never per model: a model
  whose M-027 record says it cannot see (or whose sight is
  unknown) on a vision-shaped family still received image
  parts, and no surface said so plainly.
* M-027 (``mythic_agent.core.model_capabilities``) stores the
  per-model truth: ``vision`` known-true, known-false, or
  unknown — never guessed.
* This slice is the routing gate that reads that truth. The
  pure decision lives here; it is wired into
  ``providers.vision.normalize`` (every named model, under
  the raise policy) and into the agent layer, which journals
  a refusal and can apply the offered switch through M-028's
  journaled ``model_switched`` machinery.

Honesty rules, enforced here and pinned by the slice's tests:

* **Only known sight receives images.** A model whose record
  says ``vision`` is exactly True may receive image work.
  Known-false refuses, and unknown — including a model the
  capability data does not list at all — refuses too: sight
  is never assumed from the door's shape or family.
* **A refusal names the model and its record.** The reason
  says which model was asked, what its capability record
  says (recorded as unable to see, or sight unknown), and
  how many image parts were held back. Nothing is sent and
  nothing is silently dropped on the raise road.
* **The switch offered is a real one.** The suggested door
  is one the user has already configured (the M-031
  candidate pool: current door, fallback chain, role
  routes), the live session can actually speak (M-028's
  switchable bound), and its model is known to see. When no
  configured door qualifies, the refusal says that plainly
  and names known-seeing models from the capability data
  instead of inventing a door.
* **No images, no gate.** A request carrying no image parts
  is never refused by this layer, whatever the model's
  record says — text work is not vision work.
* The explicit ``strip`` downgrade in the elder negotiation
  stays the caller's counted choice (its drops are reported
  in ``VisionPayload.dropped``); the gate governs the road
  where images would actually be sent.
"""

from __future__ import annotations

__all__ = [
    "IMAGE_PART_TYPES",
    "PLAIN_EXPLANATION",
    "VISION_SLICE",
    "Any",
    "Dict",
    "List",
    "Optional",
    "Tuple",
    "VisionDecision",
    "count_image_parts",
    "format_vision_decision",
    "format_vision_status",
    "gate_for_model",
    "known_seeing_models",
    "parse_vision_args",
    "route_images",
    "suggest_switch",
]

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .cost_routing import Door, candidate_doors
from .model_capabilities import load_capabilities
from .model_switch import SWITCHABLE_DIALECTS, infer_provider
from .provider_registry import load_registry

#: The slice that owns this module.
VISION_SLICE = "M-037"

#: Content-part types that carry an image — the same
#: definition ``mythic_agent.providers.vision.has_images``
#: uses, so the gate and the negotiation can never disagree
#: about what counts as image work.
IMAGE_PART_TYPES = ("image_url", "image_bytes")

#: Vision routing explained in plain words — the sentence
#: every surface shows. Images go only where sight is known;
#: a refusal is plain, names the record, and offers a switch.
PLAIN_EXPLANATION = (
    "Vision input routing: image work is sent only to a "
    "model whose capability record says it can see. If the "
    "current model's record says it cannot see — or its "
    "sight is simply not known — the images are not sent: "
    "the app says so plainly, names the model and its "
    "record, and offers a switch to a model that is known "
    "to see, when you have such a door set up."
)


def count_image_parts(parts: Any) -> int:
    """How many image parts *parts* carries.

    *parts* is the canonical content-part list the vision
    negotiation consumes. A non-list raises ValueError — a
    malformed request surfaces, it is never routed around.
    Non-mapping entries carry no image and are not counted
    (the negotiation itself refuses them on its own road).
    """
    if not isinstance(parts, list):
        raise ValueError(
            f"Content parts must be a list, got {type(parts).__name__}")
    return sum(
        1 for part in parts
        if isinstance(part, dict) and part.get("type") in IMAGE_PART_TYPES)


def known_seeing_models(capabilities: Any = None) -> Tuple[str, ...]:
    """Every model whose capability record says it can see.

    In capability-data order; only a known-true ``vision``
    flag counts — known-false and unknown are both absent.
    """
    caps = capabilities if capabilities is not None else load_capabilities()
    return tuple(r.model for r in caps.records if r.vision is True)


def _door_switchable(base_url: str) -> bool:
    """Whether the live session can speak this door (M-028's bound)."""
    provider = infer_provider(base_url)
    if provider is None:
        return True
    return load_registry().provider(provider).dialect in SWITCHABLE_DIALECTS


def suggest_switch(config: Dict[str, Any],
                   capabilities: Any = None) -> Optional[Door]:
    """The configured door vision work should switch to, or None.

    The pool is exactly the doors the user has configured
    (M-031's candidate pool, current door first). The current
    door itself never qualifies — it is the door being
    refused. A qualifying door is one the live session can
    speak (M-028's bound) whose model's capability record
    says it can see (known-true only).
    """
    caps = capabilities if capabilities is not None else load_capabilities()
    doors = candidate_doors(config)
    if not doors:
        return None
    current = doors[0]
    for door in doors[1:]:
        if door.model == current.model and door.base_url == current.base_url:
            continue
        if not _door_switchable(door.base_url):
            continue
        if caps.for_model(door.model).vision is True:
            return door
    return None


@dataclass(frozen=True)
class VisionDecision:
    """The routing gate's verdict for one request, with its reason.

    ``vision`` is the model's recorded M-027 truth: True
    (known to see), False (recorded as unable to see), or
    None (unknown). ``suggestion`` is the configured
    known-seeing door a switch is offered to, or None when
    no configured door qualifies.
    """

    model: str
    image_count: int
    allowed: bool
    vision: Optional[bool]
    reason: str
    suggestion: Optional[Door] = None

    def record(self) -> Dict[str, Any]:
        """This decision as a plain mapping."""
        return {
            "model": self.model,
            "image_count": self.image_count,
            "allowed": self.allowed,
            "vision": self.vision,
            "reason": self.reason,
            "suggestion": (self.suggestion.selection()
                           if self.suggestion is not None else None),
        }


def _vision_word(vision: Optional[bool]) -> str:
    if vision is True:
        return "known to see"
    if vision is False:
        return "recorded as not able to see"
    return "sight unknown"


def gate_for_model(model_name: Any, image_count: int,
                   capabilities: Any = None) -> VisionDecision:
    """The gate's verdict for *image_count* images on *model_name*.

    Pure over the capability truth: no images always allows;
    a known-seeing model allows; known-false and unknown
    refuse with a plain reason naming the model and its
    record. No switch suggestion is computed here — that
    needs the user's configured doors (see
    :func:`route_images`).
    """
    model = model_name.strip() if isinstance(model_name, str) else ""
    if image_count <= 0:
        vision = None
        if model:
            caps = (capabilities if capabilities is not None
                    else load_capabilities())
            vision = caps.for_model(model).vision
        return VisionDecision(
            model=model, image_count=0, allowed=True, vision=vision,
            reason=(
                "This request carries no image parts, so there "
                "is no vision work to route; the current door "
                "is used as it stands."))
    if not model:
        return VisionDecision(
            model=model, image_count=image_count, allowed=False,
            vision=None,
            reason=(
                f"{image_count} image part(s) cannot be sent: "
                "no model is selected, so there is no door whose "
                "sight could allow them. Choose a model whose "
                "capability record says it can see, then send "
                "the images again."))
    caps = capabilities if capabilities is not None else load_capabilities()
    vision = caps.for_model(model).vision
    plural = "part" if image_count == 1 else "parts"
    if vision is True:
        return VisionDecision(
            model=model, image_count=image_count, allowed=True,
            vision=True,
            reason=(
                f"{model} is known to see (its capability record "
                f"says vision: yes), so the {image_count} image "
                f"{plural} may be sent to it."))
    if vision is False:
        reason = (
            f"{image_count} image {plural} cannot be sent to "
            f"{model}: that model's capability record says it "
            "cannot see (vision: no). The images were not sent "
            "and were not dropped silently — switch to a model "
            "whose record says it can see, then send them again.")
    else:
        reason = (
            f"{image_count} image {plural} cannot be sent to "
            f"{model}: that model's sight is unknown — its "
            "capability record does not say it can see, and "
            "sight is never assumed. The images were not sent "
            "and were not dropped silently — switch to a model "
            "whose record says it can see, then send them again.")
    return VisionDecision(
        model=model, image_count=image_count, allowed=False,
        vision=vision, reason=reason)


def route_images(config: Dict[str, Any], parts: Any,
                 capabilities: Any = None) -> VisionDecision:
    """Decide image routing for *parts* under the user's *config*.

    The current door is the config's model; the gate is
    :func:`gate_for_model` over the counted image parts.
    When the gate refuses, the configured known-seeing door
    a switch is offered to (see :func:`suggest_switch`) is
    named in the reason and carried on the decision; when
    no configured door qualifies, the reason names
    known-seeing models from the capability data instead.
    """
    caps = capabilities if capabilities is not None else load_capabilities()
    count = count_image_parts(parts)
    decision = gate_for_model(config.get("model"), count, caps)
    if decision.allowed or count == 0:
        return decision
    suggestion = suggest_switch(config, caps)
    if suggestion is not None:
        reason = (
            decision.reason + " Switch offered: "
            f"{suggestion.describe()} is a door you have set "
            "up whose model is known to see — /vision switch "
            "takes it through the journaled model switch.")
        return VisionDecision(
            model=decision.model, image_count=decision.image_count,
            allowed=False, vision=decision.vision, reason=reason,
            suggestion=suggestion)
    seeing = known_seeing_models(caps)
    if seeing:
        reason = (
            decision.reason + " No door you have set up is "
            "known to see; models whose records say they can "
            "see include: " + ", ".join(seeing[:5]) + ".")
    else:  # pragma: no cover - the shipped data lists seeing models
        reason = (
            decision.reason + " No model in the capability "
            "data is known to see.")
    return VisionDecision(
        model=decision.model, image_count=decision.image_count,
        allowed=False, vision=decision.vision, reason=reason,
        suggestion=None)


def parse_vision_args(text: Any) -> Dict[str, Any]:
    """Parse the ``/vision`` slash-command argument string.

    Grammar::

        /vision         -> show the current model's sight truth
        /vision show    -> show the current model's sight truth
        /vision switch  -> take the offered switch to a
                           known-seeing configured door

    Returns a dict with key ``action`` (``show`` / ``switch``).
    Raises :class:`ValueError` on a usage error.
    """
    if text is None:
        text = ""
    if not isinstance(text, str):
        raise ValueError(
            f"Vision arguments must be text, got {type(text).__name__}")
    stripped = text.strip().lower()
    if not stripped or stripped in ("show", "status"):
        return {"action": "show"}
    if stripped == "switch":
        return {"action": "switch"}
    raise ValueError("Usage: /vision, /vision show, or /vision switch")


def format_vision_status(status: Dict[str, Any]) -> str:
    """The visible status: the current model's sight, and the offer.

    *status* is the agent's vision-status mapping (current
    model, its recorded vision truth, the configured
    known-seeing doors, the offered switch, and the plain
    explanation).
    """
    model = status.get("model") or "no model selected"
    lines = [
        f"Vision routing for the current model ({model}): "
        + _vision_word(status.get("vision")) + ".",
        PLAIN_EXPLANATION,
    ]
    doors = status.get("seeing_doors") or []
    if doors:
        lines.append("  Doors you have set up whose models can see:")
        for door in doors:
            label = door["model"]
            if door.get("provider"):
                label += f" via {door['provider']}"
            lines.append(f"    {label} ({door['base_url']}, {door['source']})")
    else:
        lines.append(
            "  No door you have set up has a model known to see.")
    suggestion = status.get("suggestion")
    if status.get("vision") is not True and suggestion:
        lines.append(
            f"  Switch offered: {suggestion['model']} "
            f"({suggestion['base_url']}) — /vision switch takes it.")
    lines.append(
        "  Image parts sent to a model that is not known to see "
        "are refused before anything is sent, with the reason "
        "recorded; text-only work is never gated.")
    return "\n".join(lines)


def format_vision_decision(decision: VisionDecision) -> str:
    """One plain paragraph: the gate's verdict and its reason."""
    if decision.allowed:
        head = (f"Vision routing: the {decision.image_count} "
                "image part(s) may go to "
                f"{decision.model or 'the current door'}. ")
    else:
        head = (f"Vision routing: the {decision.image_count} "
                "image part(s) were NOT sent. ")
    return head + decision.reason
