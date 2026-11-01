"""Streaming discipline (All-Features roadmap slice M-034).

Part II — The Provider Ocean — gives its streaming road a
discipline here: token streaming with a clean interrupt,
partial-answer salvage, and resume-the-thought where the
provider allows; a killed stream never corrupts the journal.

What already shipped, and what this slice adds:

* ``Agent._request_streaming`` (``mythic_agent.agents.llm``)
  already assembles one normalized response from SSE deltas via
  ``_StreamAccumulator``, retries only before the first chunk,
  and refuses malformed or incomplete streams before any tool
  fragment becomes executable. On a mid-stream cancel it
  checkpoints ``{"type": "stream_interrupted", "partial_text":
  ...}`` and raises ``TurnCancelled`` — but, until this slice,
  that checkpoint had **no consumer**: the partial answer was
  journaled yet never salvaged, so the user lost the words and
  the conversation pretended they were never said.
* This slice is the consumer. The pure layer lives here: the
  salvage message shape (a plain assistant message whose text
  is the marker line plus the partial, verbatim — no extra
  keys, no tool calls, so session validation and every
  provider accept it as ordinary history), the resume gate
  (M-027 capability truth: only a model whose streaming flag
  is known-true may resume a thought), the resume prompt, and
  the plain-words surfaces the terminal and the TUI share.
  The agent layer owns the journal: it appends the salvage
  through ``_append_message`` when a stream dies, restores it
  from the ``stream_interrupted`` checkpoint when a session is
  resumed and the live turn never got to salvage it, and
  journals ``thought_resumed`` before a continuation runs.

Honesty rules, enforced here and pinned by the slice's tests:

* **A salvage is marked, never dressed as complete.** Every
  salvaged message opens with :data:`PARTIAL_MARKER`, in plain
  words: the answer was interrupted mid-stream and is not
  complete.
* **An empty partial salvages nothing.** Whitespace is not an
  answer; no message is invented for it.
* **A salvage carries no tool calls, ever.** A killed stream
  leaves no dangling calls for the journal to trip over: the
  salvage is a plain ``{"role": "assistant", "content": ...}``
  message and nothing else.
* **Resume only where the door allows.** The gate reads
  M-027's capability truth for the session's model: streaming
  known-true allows; known-false or unknown (including an
  unlisted model) refuses, plainly, naming the model — a fake
  resume is never offered.
* **The partial is kept verbatim.** Salvage, detection, and
  the resume prompt never rewrite the words the model managed
  to say before the interrupt.
"""

from __future__ import annotations

__all__ = [
    "PARTIAL_MARKER",
    "PLAIN_EXPLANATION",
    "STREAMING_SLICE",
    "Any",
    "Dict",
    "List",
    "Optional",
    "ResumeDecision",
    "Tuple",
    "can_resume",
    "find_partial",
    "format_resume_status",
    "is_partial_message",
    "parse_resume_args",
    "partial_text_of",
    "resume_prompt",
    "salvage_message",
    "salvage_notice",
]

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .model_capabilities import load_capabilities

#: The slice that owns this module.
STREAMING_SLICE = "M-034"

#: The marker line that opens every salvaged partial answer.
#: Plain words, on purpose: anyone reading the transcript —
#: human or model — can see this answer was interrupted
#: mid-stream and is not complete.
PARTIAL_MARKER = (
    "[Partial answer — interrupted mid-stream; "
    "this answer is not complete.]"
)

#: Streaming discipline explained in plain words — the text
#: every surface shows. A killed stream keeps what was said,
#: marks it partial, and offers an honest road onward.
PLAIN_EXPLANATION = (
    "Streaming discipline: when a streaming answer is "
    "interrupted, the words it managed to say are kept in the "
    "conversation as a partial answer, clearly marked as not "
    "complete — they are never silently dropped and never "
    "presented as finished. Where the current model's "
    "streaming ability is known to support it, /resume-thought "
    "asks the model to carry on from exactly where the partial "
    "stopped, without repeating what was already said. Where "
    "that ability is not known, resuming is refused plainly, "
    "with the reason, and the partial stays in the "
    "conversation for you to read or build on yourself."
)


# ----------------------------------------------------------------------
# Salvage — the partial becomes a marked, plain assistant message
# ----------------------------------------------------------------------


def salvage_message(partial_text: Any) -> Optional[Dict[str, Any]]:
    """The salvage message for *partial_text*, or None.

    None for an empty or whitespace-only partial (nothing was
    said, so nothing is kept) and for non-text input. Otherwise
    a plain assistant message — exactly ``role`` and
    ``content``, no tool calls, no extra keys — whose content
    is the marker line followed by the partial, verbatim.
    Session validation accepts it as ordinary history and every
    provider can be sent it as-is.
    """
    if not isinstance(partial_text, str) or not partial_text.strip():
        return None
    return {"role": "assistant",
            "content": PARTIAL_MARKER + "\n" + partial_text}


def is_partial_message(message: Any) -> bool:
    """True when *message* is a salvaged partial answer."""
    if not isinstance(message, dict):
        return False
    if message.get("role") != "assistant":
        return False
    content = message.get("content")
    return isinstance(content, str) and content.startswith(PARTIAL_MARKER)


def partial_text_of(message: Any) -> Optional[str]:
    """The verbatim partial carried by *message*, or None.

    None when the message is not a salvaged partial. The marker
    line (and the one newline after it) is stripped; the words
    themselves are returned exactly as they were streamed.
    """
    if not is_partial_message(message):
        return None
    rest = message["content"][len(PARTIAL_MARKER):]
    if rest.startswith("\n"):
        rest = rest[1:]
    return rest


def find_partial(messages: Any) -> Optional[Tuple[int, str]]:
    """``(index, partial_text)`` of the LAST salvaged partial.

    Scans *messages* from the end: the most recent interrupted
    answer is the one a resume would continue. Returns None
    when no message in the list is a salvaged partial.
    """
    if not isinstance(messages, (list, tuple)):
        return None
    for index in range(len(messages) - 1, -1, -1):
        text = partial_text_of(messages[index])
        if text is not None:
            return index, text
    return None


def salvage_notice(partial_text: Any) -> str:
    """The plain-words notice shown when a partial is salvaged.

    It says what was kept (and that it is partial, never
    complete) and how to resume the thought.
    """
    kept = partial_text.strip() if isinstance(partial_text, str) else ""
    return (
        "The stream was interrupted. The partial answer above "
        f"was kept in the conversation ({len(kept)} characters), "
        "marked as a partial answer — it is not complete. "
        "Resume the thought with /resume-thought (where the "
        "current model is known to support resuming), or just "
        "ask a new question; the partial stays either way."
    )


# ----------------------------------------------------------------------
# The resume gate — M-027 capability truth governs
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class ResumeDecision:
    """The resume gate's verdict for one model, with its reason.

    ``streaming`` is the model's recorded M-027 streaming
    truth: True (known to stream), False (known not to), or
    None (unknown). Only True allows a resume.
    """

    model: str
    allowed: bool
    streaming: Optional[bool]
    reason: str

    def record(self) -> Dict[str, Any]:
        """This decision as a plain mapping."""
        return {"model": self.model, "allowed": self.allowed,
                "streaming": self.streaming, "reason": self.reason}


def can_resume(model_name: Any, capabilities: Any = None) -> ResumeDecision:
    """Whether the thought may be resumed on *model_name*.

    The gate is M-027 capability truth
    (:func:`mythic_agent.core.model_capabilities.load_capabilities`):
    a model whose ``streaming`` flag is known-true allows the
    resume. Known-false and unknown — including a model the
    capability data does not list at all — refuse, with a plain
    reason naming the model: a resume is offered only where it
    is known the door supports carrying a stream's thought on.
    """
    model = model_name.strip() if isinstance(model_name, str) else ""
    if not model:
        return ResumeDecision(
            model=model, allowed=False, streaming=None,
            reason=(
                "No model is selected, so there is no door whose "
                "streaming ability could allow resuming the "
                "thought. Choose a model first, then resume."))
    caps = capabilities if capabilities is not None else load_capabilities()
    streaming = caps.for_model(model).streaming
    if streaming is True:
        return ResumeDecision(
            model=model, allowed=True, streaming=True,
            reason=(
                f"{model} is known to support streaming, so the "
                "interrupted thought can be resumed on this door: "
                "the model will be asked to continue from exactly "
                "where the partial answer stopped."))
    if streaming is False:
        return ResumeDecision(
            model=model, allowed=False, streaming=False,
            reason=(
                f"Resuming is not offered on {model}: that model "
                "is recorded as not supporting streaming, and a "
                "thought can only be resumed where streaming is "
                "known to be supported. The partial answer stays "
                "in the conversation; switch to a model known to "
                "support streaming, or ask a new question."))
    return ResumeDecision(
        model=model, allowed=False, streaming=None,
        reason=(
            f"Resuming is not offered on {model}: its streaming "
            "ability is not known to support resuming — the "
            "capability record for this model says streaming is "
            "unknown, and a resume is never faked on an unknown. "
            "The partial answer stays in the conversation; "
            "switch to a model known to support streaming, or "
            "ask a new question."))


def resume_prompt(partial_text: str) -> str:
    """The user-turn text that asks for the thought's continuation.

    It names the situation plainly — the partial answer is in
    the conversation above, marked as partial — and asks the
    model to continue from exactly where it stopped, without
    repeating what was already said.
    """
    return (
        "Your previous answer was interrupted mid-stream. The "
        "partial answer you managed to give is in the "
        "conversation above, marked as a partial answer — it "
        "is not complete. Please continue that same answer "
        "from exactly where it stopped, picking up mid-thought "
        "if that is where it ended. Do not repeat anything you "
        "already said, do not restart the answer, and do not "
        "apologise for the interruption — just carry the "
        "thought on to its end."
    )


# ----------------------------------------------------------------------
# The /resume-thought grammar + formatters
# ----------------------------------------------------------------------


def parse_resume_args(text: Any) -> Dict[str, Any]:
    """Parse the ``/resume-thought`` slash-command argument string.

    Grammar::

        /resume-thought         -> resume the waiting thought
        /resume-thought resume  -> resume the waiting thought
        /resume-thought show    -> show whether a partial waits

    Returns a dict with key ``action`` (``resume`` / ``show``).
    Raises :class:`ValueError` on a usage error.
    """
    if text is None:
        text = ""
    if not isinstance(text, str):
        raise ValueError(
            f"Resume arguments must be text, "
            f"got {type(text).__name__}")
    stripped = text.strip()
    if not stripped:
        return {"action": "resume"}
    head = stripped.lower()
    if head in ("show", "status"):
        return {"action": "show"}
    if head == "resume":
        return {"action": "resume"}
    raise ValueError(
        "Usage: /resume-thought, /resume-thought resume, or "
        "/resume-thought show")


def format_resume_status(partial: Optional[Dict[str, Any]],
                         decision: ResumeDecision) -> str:
    """The visible status: whether a partial waits, and the gate.

    *partial* is the agent's salvaged-partial record (a mapping
    with ``partial_text``) or None; *decision* is the resume
    gate's verdict for the current model. When no partial is
    waiting, that is said plainly, first.
    """
    lines = []
    if partial is None:
        lines.append(
            "No interrupted answer is waiting: there is no "
            "partial answer in this conversation to resume.")
    else:
        text = partial.get("partial_text", "")
        lines.append(
            "A partial answer is waiting in this conversation "
            f"({len(text)} characters kept, marked as partial — "
            "not complete).")
        preview = text.strip()
        if preview:
            lines.append(f"  It begins: {preview[:120]}")
    lines.append(PLAIN_EXPLANATION)
    lines.append(f"  Resume gate for {decision.model or 'no model'}: "
                 + ("open — /resume-thought continues the thought."
                    if decision.allowed else
                    "closed — " + decision.reason))
    return "\n".join(lines)
