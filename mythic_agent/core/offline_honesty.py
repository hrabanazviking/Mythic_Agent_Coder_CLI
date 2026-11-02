"""Offline honesty (All-Features roadmap slice M-040).

Part II — The Provider Ocean — closes its honesty road here.
The M-039 health board can say, door by door, that every
door is unreachable, needs-key, or unknown — but no layer
turned that into the app's own plain declaration. Each
surface discovered a dead world failure by failure: a chat
request died on its provider error and said nothing about
the whole picture. This slice is that declaration.

What this layer is:

* A pure assessment over an M-039 :class:`Board`:
  :func:`assess_board` reads the board's entries and says
  one of three things — ``online`` (a door answered its
  probe), ``offline`` (the declaration below), or
  ``unknown`` (the board cannot honestly say).
* The offline declaration is exact and is said once, in
  plain words: there is no network route to a model and no
  local model answering. Beside it stand the non-model
  tools that still work — each one a real, shipped CLI
  surface that needs no model: static review
  (``mythic review``), recorded metrics (``mythic metrics``),
  and session search (``mythic sessions --search``).
* The live roads: ``Agent.offline_status()`` builds the
  board for the session and assesses it; ``/offline`` shows
  the assessment on the terminal and TUI system-command
  roads; the terminal chat prints the declaration once at
  start when the state is offline; ``mythic doctor --live``
  carries the assessment beside its board.

Honesty rules, enforced here and pinned by the slice's tests:

* **Offline is claimed only from a probed board.** A board
  built without probing (every entry ``unknown``) claims
  nothing: the state is ``unknown``, never ``offline``.
* **A keyed door the board cannot probe blocks the claim.**
  Native-SDK doors report ``unknown`` on the board because
  their address belongs to their vendor's kit; if such a
  door's key is held, it may well serve over a live network,
  so the state stays ``unknown`` and says why — a keyed
  remote door over a live network is not offline.
* **One reachable door is online.** Any entry with status
  ``reachable`` — local or remote — means the app is not
  offline, and the assessment names the doors that answered.
* **The still-working tools are real.** Every offered tool
  names the exact CLI command that runs it without a model;
  the slice's tests pin those commands against the live CLI
  parser, so an offered tool cannot quietly stop existing.
"""

from __future__ import annotations

__all__ = [
    "OFFLINE_SLICE",
    "DECLARATION",
    "PLAIN_EXPLANATION",
    "STATES",
    "STILL_AVAILABLE",
    "Any",
    "Board",
    "Dict",
    "List",
    "OfflineAssessment",
    "Optional",
    "ToolOffer",
    "Tuple",
    "assess_board",
    "format_offline_status",
    "parse_offline_args",
]

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .provider_health import Board

#: The slice that owns this module.
OFFLINE_SLICE = "M-040"

#: The assessment vocabulary, in honesty order.
STATES: Tuple[str, ...] = ("online", "offline", "unknown")

#: The exact offline declaration — the app says exactly this.
DECLARATION = (
    "You are offline: no network route to a model is "
    "answering, and no local model is answering either."
)

#: Offline honesty explained in plain words — the sentence
#: every surface shows.
PLAIN_EXPLANATION = (
    "Offline honesty: when the provider health board has "
    "actually probed the doors and none of them can serve — "
    "every local door unreachable, every remote door "
    "unreachable or missing its key, and no keyed door the "
    "board cannot probe still standing — the app says "
    "exactly that, once, instead of letting each request die "
    "on its own error. If any door answered, the app is not "
    "offline. If the board was never probed, or a keyed "
    "door's health is unknown to the board, the app claims "
    "nothing. Either way, the tools that need no model — "
    "review, metrics, and session search — still work."
)


@dataclass(frozen=True)
class ToolOffer:
    """A non-model tool that still works while offline.

    ``command`` is the exact CLI invocation, pinned by the
    slice's tests against the live CLI parser. ``what`` says
    in plain words what the tool does without a model.
    """

    name: str
    command: str
    what: str

    def record(self) -> Dict[str, Any]:
        """This offer as a plain mapping."""
        return {"name": self.name, "command": self.command,
                "what": self.what}


#: The non-model tools that still work while offline, in the
#: roadmap's own order (review, metrics, session search).
STILL_AVAILABLE: Tuple[ToolOffer, ...] = (
    ToolOffer(
        name="review",
        command="mythic review <path>",
        what="Statically review Python files for common "
             "issues — no model is consulted."),
    ToolOffer(
        name="metrics",
        command="mythic metrics",
        what="Show the metrics and traces already recorded "
             "for this workspace."),
    ToolOffer(
        name="session search",
        command="mythic sessions --search <query>",
        what="Search past sessions by id, status, model, or "
             "metadata text, and read what is already saved."),
)


@dataclass(frozen=True)
class OfflineAssessment:
    """The board read plainly: online, offline, or unknown.

    ``reachable`` names the doors that answered (empty unless
    the state is ``online``). ``reasons`` carries the board
    evidence in plain words — why this state, never just the
    verdict. ``declaration`` is the exact offline declaration
    when the state is ``offline``, else None — no surface may
    print a declaration this layer did not make.
    ``still_available`` offers the non-model tools whenever
    the state is ``offline``.
    """

    state: str
    probed: bool
    reachable: Tuple[str, ...]
    reasons: Tuple[str, ...]
    declaration: Optional[str]
    still_available: Tuple[ToolOffer, ...]

    def record(self) -> Dict[str, Any]:
        """This assessment as a plain mapping."""
        return {
            "slice": OFFLINE_SLICE,
            "state": self.state,
            "probed": self.probed,
            "reachable": list(self.reachable),
            "reasons": list(self.reasons),
            "declaration": self.declaration,
            "still_available": [o.record()
                                for o in self.still_available],
        }


def assess_board(board: Board) -> OfflineAssessment:
    """Read *board* plainly: online, offline, or unknown.

    The honesty rules in this module's docstring are the
    whole algorithm: a reachable door is online; an unprobed
    board claims nothing; a keyed-but-unprobed door (its
    board status ``unknown`` with a key held) blocks the
    offline claim; otherwise every probed door failed and
    every remote door wants a key it does not hold, and the
    state is offline with the exact declaration.
    """
    entries = board.entries
    probed = any(entry.probed for entry in entries)
    reachable = tuple(entry.provider for entry in entries
                      if entry.status == "reachable")
    if reachable:
        return OfflineAssessment(
            state="online", probed=probed, reachable=reachable,
            reasons=(f"{len(reachable)} door(s) answered their "
                     f"probe: {', '.join(reachable)}. A door "
                     "that answers can serve, so the app is "
                     "not offline.",),
            declaration=None, still_available=())
    if not probed:
        return OfflineAssessment(
            state="unknown", probed=False, reachable=(),
            reasons=("No door on the health board was probed, "
                     "so the board claims nothing: offline is "
                     "never guessed from an unprobed board.",),
            declaration=None, still_available=())
    keyed_unprobed = tuple(
        entry.provider for entry in entries
        if entry.status == "unknown" and entry.key_present)
    if keyed_unprobed:
        return OfflineAssessment(
            state="unknown", probed=True, reachable=(),
            reasons=(
                "No probed door answered, but a key is held "
                f"for {', '.join(keyed_unprobed)}, whose "
                "health the board cannot probe (its address "
                "belongs to its vendor's own software kit). "
                "That door may still serve over a live "
                "network, so the app does not claim offline.",),
            declaration=None, still_available=())
    unreachable = tuple(entry.provider for entry in entries
                        if entry.status == "unreachable")
    needs_key = tuple(entry.provider for entry in entries
                      if entry.status == "needs-key")
    reasons = []
    if unreachable:
        reasons.append(
            f"Probed and not answering: {', '.join(unreachable)}.")
    if needs_key:
        reasons.append(
            "No key held, so never probed and cannot serve: "
            f"{', '.join(needs_key)}.")
    unknown_unkeyed = tuple(
        entry.provider for entry in entries
        if entry.status == "unknown" and not entry.key_present)
    if unknown_unkeyed:
        reasons.append(
            "Unknown to the board and no key held, so cannot "
            f"be counted on to serve: {', '.join(unknown_unkeyed)}.")
    return OfflineAssessment(
        state="offline", probed=True, reachable=(),
        reasons=tuple(reasons), declaration=DECLARATION,
        still_available=STILL_AVAILABLE)


def parse_offline_args(text: Any) -> Dict[str, Any]:
    """Parse the ``/offline`` slash-command argument string.

    ``/offline`` and ``/offline show`` both show the
    assessment; anything else is a usage error, never a
    silent guess.
    """
    words = str(text or "").strip().split()
    if not words or words == ["show"]:
        return {"action": "show"}
    raise ValueError(
        "Usage: /offline — show whether the app is offline "
        "(no network route to a model and no local model "
        "answering), and the non-model tools that still work.")


def format_offline_status(status: Dict[str, Any]) -> str:
    """The ``/offline`` report from an Agent status mapping."""
    assessment = status["assessment"]
    lines = [f"Offline honesty ({OFFLINE_SLICE}): "
             f"state — {assessment['state']}."]
    if assessment["declaration"]:
        lines.append(assessment["declaration"])
    for reason in assessment["reasons"]:
        lines.append(f"  {reason}")
    if assessment["still_available"]:
        lines.append("Still available without a model:")
        for offer in assessment["still_available"]:
            lines.append(f"  {offer['command']} — {offer['what']}")
    lines.append(PLAIN_EXPLANATION)
    return "\n".join(lines)
