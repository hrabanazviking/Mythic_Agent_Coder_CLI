"""Voice in and out (All-Features roadmap slice M-180).

Part VIII - The Beautiful Face - builds here. The
roadmap's words: *push-to-talk dictation for
prompts, and spoken stand-ups via the existing
TTS (direct catalog casting, the house voice
law) - voice is an extra door, never the only
door.*

What already ships, and what this slice adds:

* The shipped tree already carries the roads
  voice travels: ``mythic_agent/core/audio.py``
  records and transcribes (an ``AudioRecorder``
  with ``start_recording`` / ``stop_recording`` /
  ``transcribe``), and ``mythic_agent/core/tts.py``
  speaks (a ``TTSManager`` with ``speak``), with
  ``mythic_agent/core/character_voices.py``
  (M-136) holding how cast members report. What
  nothing held is voice itself as checkable
  data: a dictation session judged whole from
  push to draft, a stand-up held as the text
  that will be spoken and the catalog voice
  cast for it, and the standing law - every
  voice action has a text equivalent - held as
  data instead of as a hope.
* M-177's prompt craft (``core/prompt_craft.py``)
  deliberately did NOT build dictation: its kind
  set is closed without it and its own text says
  dictation is M-180's road. This slice is that
  road, built in its own module; prompt craft's
  pinned behaviour is untouched.
* This slice is the voice room, as a pure layer:
  a dictation session held whole (its state -
  recording, landed or drafted - its transcript,
  the capture and transcriber backends it names,
  and its provenance whole); a spoken stand-up
  held whole (its speaker, its text, the catalog
  voice cast for it by direct catalog casting -
  the house voice law: render straight from the
  voice catalog and use the render as it comes -
  the TTS backend it names, and its provenance);
  and a voice action held whole (its name, its
  spoken phrase, the text equivalent that stands
  beside it, and its provenance). Availability -
  available, unavailable by a named reason, or
  honestly unknown - is DERIVED from the backends
  and voices a record names at call time, never
  stored and never faked. A dictation's
  transcript lands as a prompt draft and is
  never auto-sent: a record claiming a dictation
  was sent refuses. The panel is DERIVED for one
  held view and a verdict is DERIVED for the
  whole book under one view (open while every
  shown item stands whole, strained while some
  do, shut while none does). The shipped data
  file (``mythic_agent/data/voice_in_out.yaml``)
  holds one example book in exactly the shape a
  real voice file takes, a loader reads a voice
  file anywhere on disk, items and views are
  shaped as session news, and a small in-memory
  registry holds items and views one by one.
  The agent layer owns holding voice for a
  session. Live roads stand behind seams: a
  caller may hand ``transcribe_dictation`` a
  transcriber callable and ``speak_standup`` a
  speaker callable; the defaults reach for the
  shipped ``audio.py`` / ``tts.py`` singletons
  lazily, by import inside the call, so this
  module imports cleanly where no microphone,
  no PortAudio and no TTS stack stand.

Honesty rules, enforced here and pinned by tests:

* **Voice is an extra door, never the only
  door.** Every voice action names a text
  equivalent, held as data. An action naming
  none - or claiming to be voice-only - refuses
  by name: the law is not a comment, it is a
  build rule of this layer.
* **A dictated prompt is a draft, never a
  send.** A transcript lands, then becomes a
  prompt draft whose text is the transcript
  itself, derived at call time. Nothing here
  sends a prompt: a dictation record carrying
  a sent claim, or a stored draft that
  disagrees with its transcript, refuses.
* **Availability is derived, never faked.** A
  channel whose backends are named stands
  available; one naming no capture, no
  transcriber, no TTS backend or no catalog
  voice stands unavailable, with the missing
  piece named as the reason; one naming the
  unknown backend stands honestly unknown. No
  record stores an availability word: a
  mapping naming one refuses.
* **Data and seams only.** This layer captures
  no live audio in tests, builds no new TTS
  engine, clones no voice, converts no voice
  and masters no audio: spoken stand-ups go
  through the existing TTS seam and dictation
  through the existing audio/transcribe seam,
  each behind a callable a test can fake. A
  seam that stands absent renders nothing and
  transcribes nothing - the outcome is named
  unavailable, never spoken or landed by
  invention.
"""

from __future__ import annotations

__all__ = [
    "AVAILABILITY_WORDS",
    "BACKEND_UNKNOWN",
    "EVERY_VOICE_ACTION_HAS_A_TEXT_EQUIVALENT",
    "ITEM_KINDS",
    "PLAIN_EXPLANATION",
    "STATES",
    "USAGE",
    "VERDICT_WORDS",
    "VIEW_KINDS",
    "VOICE_IN_OUT_RESOURCE",
    "VOICE_IN_OUT_SCHEMA",
    "VOICE_IN_OUT_SLICE",
    "THE_VOICE_IN_OUT_SLICE",
    "Any",
    "Dict",
    "DictationSession",
    "List",
    "Optional",
    "SpeechRender",
    "SpokenStandup",
    "Tuple",
    "VoiceAction",
    "VoiceBook",
    "VoiceKindCount",
    "VoicePanel",
    "VoicePanelRow",
    "VoiceRegistry",
    "VoiceVerdict",
    "VoiceView",
    "action_plain_words",
    "action_record",
    "availability_of",
    "book_record",
    "build_action",
    "build_book",
    "build_dictation",
    "build_panel",
    "build_row",
    "build_standup",
    "build_verdict",
    "build_view",
    "default_speaker",
    "default_transcriber",
    "derive_panel",
    "derive_verdict",
    "dictation_availability",
    "dictation_passes",
    "dictation_record",
    "draft_dictation",
    "draft_text_of",
    "format_action",
    "format_book",
    "format_dictation",
    "format_panel",
    "format_standup",
    "format_verdict",
    "format_view",
    "format_voice_in_out_screen",
    "inspect_item_source",
    "item_passes",
    "item_record",
    "items_for_kind",
    "load_voice_in_out",
    "load_voice_in_out_file",
    "normalize_kind",
    "normalize_kind_filter",
    "normalize_state",
    "panel_plain_words",
    "panel_record",
    "parse_voice_in_out_args",
    "passing_items",
    "plain_words",
    "segment_of",
    "shown_items",
    "speak_standup",
    "standup_availability",
    "standup_passes",
    "standup_plain_words",
    "standup_record",
    "start_dictation",
    "stop_dictation",
    "total_items",
    "transcribe_dictation",
    "validate_action",
    "validate_book",
    "validate_dictation",
    "validate_panel",
    "validate_row",
    "validate_standup",
    "validate_verdict",
    "validate_view",
    "verdict_plain_words",
    "verdict_record",
    "view_plain_words",
    "view_record",
]

from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id

VOICE_IN_OUT_SLICE = "M-180"

#: The longer name other layers cite for this slice.
THE_VOICE_IN_OUT_SLICE = VOICE_IN_OUT_SLICE

VOICE_IN_OUT_RESOURCE = "voice_in_out.yaml"

VOICE_IN_OUT_SCHEMA = "mythic.voice_in_out/1"

#: The kinds of item one voice book holds, in
#: held order: dictation in, stand-ups out, and
#: the actions the standing law governs.
ITEM_KINDS = ("dictation", "standup", "action")

_KIND_ALIASES = {
    "dictation": "dictation", "dictate": "dictation",
    "push-to-talk": "dictation", "push_to_talk": "dictation",
    "ptt": "dictation", "voice-in": "dictation",
    "standup": "standup", "stand-up": "standup",
    "stand_up": "standup", "spoken": "standup",
    "voice-out": "standup",
    "action": "action", "actions": "action",
    "command": "action"}

#: The views a panel may stand under: every kind
#: at once, or one kind alone.
VIEW_KINDS = ("all",) + ITEM_KINDS

#: A dictation session's states, in the order a
#: session walks them: the push is held, the
#: transcript lands, the draft stands.
STATES = ("recording", "landed", "drafted")

_STATE_ALIASES = {
    "recording": "recording", "live": "recording",
    "held": "recording",
    "landed": "landed", "stopped": "landed",
    "transcribed": "landed",
    "drafted": "drafted", "draft": "drafted"}

#: The words availability may stand at, always
#: derived from what a record names.
AVAILABILITY_WORDS = ("available", "unavailable", "unknown")

#: The backend name that stands honestly unknown:
#: a record naming it claims no working road.
BACKEND_UNKNOWN = "unknown"

#: The standing law, as data: every voice action
#: in this layer carries a text equivalent.
EVERY_VOICE_ACTION_HAS_A_TEXT_EQUIVALENT = True

VERDICT_WORDS = ("open", "strained", "shut")

_DICTATION_KEYS = frozenset({
    "dictation_id", "id", "seq", "sequence", "order",
    "state", "status", "transcript", "text",
    "capture_backend", "capture",
    "transcriber_backend", "transcriber",
    "detail", "reason",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_DICTATION_DERIVED = frozenset({
    "availability", "availability_reason", "draft_text",
    "draft", "sent", "auto_sent", "passes", "segment"})

_STANDUP_KEYS = frozenset({
    "standup_id", "id", "seq", "sequence", "order",
    "speaker", "agent", "text", "words",
    "voice_name", "voice", "catalog_voice",
    "tts_backend", "tts", "backend",
    "detail", "reason",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_STANDUP_DERIVED = frozenset({
    "availability", "availability_reason", "rendered",
    "spoken", "passes", "segment"})

_ACTION_KEYS = frozenset({
    "action_id", "id", "seq", "sequence", "order",
    "name", "voice_phrase", "phrase", "spoken_phrase",
    "text_equivalent", "text", "equivalent",
    "voice_only",
    "detail", "reason",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_ACTION_DERIVED = frozenset({"passes", "segment"})

_VIEW_KEYS = frozenset({
    "view_id", "id", "seq", "sequence", "order",
    "kind_filter", "filter", "kind",
    "detail", "reason",
    "recorded_on", "day", "date",
    "actor", "by", "who", "source",
    "origin_session", "session"})

_ROW_KEYS = frozenset({
    "item_id", "id", "kind", "label", "name",
    "segment", "recorded_on", "day", "date"})

_PANEL_KEYS = frozenset({
    "panel_id", "id", "view_id", "view",
    "kind_filter", "filter", "kind", "rows", "shown",
    "total_items", "items", "total_shown", "matched",
    "kind_counts", "kinds", "as_of", "day",
    "account", "statements"})

_VERDICT_KEYS = frozenset({
    "total_items", "items", "total_shown", "matched",
    "passing_shown", "passing", "distinct_kinds", "kinds",
    "earliest_on", "earliest", "latest_on", "latest",
    "verdict"})

_BOOK_KEYS = frozenset({"title", "name"})

_VOICE_IN_OUT_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "canon_note", "guide", "dictations", "standups",
    "actions", "views", "panels"})

_EXAMPLE_TITLE = "Voice at the M-179 slice boundary"

_EXAMPLE_DICTATION_IDS = (
    "dictation-morning-prompt", "dictation-evening-note")

_EXAMPLE_STANDUP_IDS = (
    "standup-morning", "standup-evening")

_EXAMPLE_ACTION_IDS = (
    "action-dictate-prompt", "action-speak-standup",
    "action-mute-speech")

_EXAMPLE_FIRST_DICTATION_ID = "dictation-morning-prompt"

_EXAMPLE_PANEL_ID = "panel-m179-boundary"

_EXAMPLE_AS_OF = "2026-11-09"

_EXAMPLE_VIEW_IDS = ("view-all", "view-dictation")

PLAIN_EXPLANATION = (
    "Voice In and Out: push-to-talk dictation for "
    "prompts, and spoken stand-ups via the existing "
    "TTS (direct catalog casting, the house voice "
    "law) - voice is an extra door, never the only "
    "door. A dictation session is held whole - its "
    "state (recording, landed or drafted), its "
    "transcript, the capture and transcriber "
    "backends it names, and its provenance whole - "
    "and its transcript lands as a prompt draft, "
    "never auto-sent. A spoken stand-up is held "
    "whole - its speaker, its text, the catalog "
    "voice cast for it and the TTS backend it "
    "names. A voice action is held whole - its "
    "spoken phrase and the text equivalent that "
    "stands beside it, because every voice action "
    "has a text equivalent and voice is never the "
    "only door: an action naming none refuses by "
    "name. Availability - available, unavailable "
    "by a named reason, or honestly unknown - is "
    "derived from the backends and voices a record "
    "names, never stored and never faked. This "
    "layer holds voice as data and reaches live "
    "roads only through seams: it captures no live "
    "audio in tests, builds no new TTS engine, "
    "clones no voice and sends no prompt."
)

USAGE = (
    "Usage: /voiceinout, /voiceinout show, "
    "/voiceinout dictation <dictation-id>, "
    "/voiceinout standup <standup-id>, "
    "/voiceinout action <action-id>, "
    "/voiceinout view <view-id>, "
    "/voiceinout kind <kind>, "
    "/voiceinout panel, /voiceinout verdict"
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_title(value: Any, what: str = "a title") -> str:
    text = _clean_text(value, what)
    if len(text) > 120 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"120 characters, got {len(text)} characters")
    return text


def _check_long_text(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if len(text) > 2000 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"2000 characters, got {len(text)} characters")
    return text


def _check_account(value: Any) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"an account must be a list of statements, "
            f"got {value!r}")
    account = tuple(
        _check_long_text(a, "an account statement")
        for a in value)
    if not account:
        raise ValueError("an account carries at least one statement")
    if len(account) > 16:
        raise ValueError(
            f"an account carries at most 16 statements, "
            f"got {len(account)}")
    if len(set(account)) != len(account):
        raise ValueError("an account states one statement twice")
    return account


def _pick_any(mapping: Dict[str, Any], spellings: Tuple[str, ...],
              what: str) -> Any:
    values = [mapping[s] for s in spellings if s in mapping]
    if not values:
        return None
    if any(value != values[0] for value in values[1:]):
        raise ValueError(f"a record names two different {what}")
    return values[0]


def _check_count(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{what} must be a count, got {value!r}")
    if value < 0:
        raise ValueError(f"{what} must not be negative, got {value!r}")
    return value


def _check_seq(value: Any, what: str = "a sequence") -> int:
    seq = _check_count(value, what)
    if seq < 1:
        raise ValueError(f"{what} stands from 1, got {value!r}")
    return seq


def _check_word(value: Any, what: str) -> str:
    try:
        return normalize_member_id(value)
    except ValueError:
        raise ValueError(
            f"{what} must be one plain word, "
            f"got {value!r}") from None


def _check_day(value: Any, what: str = "a day") -> str:
    text = _clean_text(value, what)
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"{what} must be an ISO date "
            f"(YYYY-MM-DD), got {text!r}") from None
    if parsed.isoformat() != text:
        raise ValueError(
            f"{what} must be an ISO date "
            f"(YYYY-MM-DD), got {text!r}")
    return text


def _check_backend(value: Any, what: str) -> Optional[str]:
    if value is None:
        return None
    text = _clean_text(value, what)
    if len(text) > 80 or "\x00" in text:
        raise ValueError(
            f"{what} must be a plain backend name of at "
            f"most 80 characters, got {value!r}")
    return text


def normalize_kind(value: Any) -> str:
    """One item kind, read onto the closed kind set."""
    text = _clean_text(value, "a kind").lower()
    kind = _KIND_ALIASES.get(text)
    if kind is None:
        raise ValueError(
            f"a kind is one of {ITEM_KINDS}, got {value!r}")
    return kind


def normalize_kind_filter(value: Any) -> str:
    """One view's kind filter: every kind, or one."""
    text = _clean_text(value, "a kind filter").lower()
    if text == "all":
        return "all"
    return normalize_kind(text)


def normalize_state(value: Any) -> str:
    """One dictation state, read onto the closed set."""
    text = _clean_text(value, "a dictation state").lower()
    state = _STATE_ALIASES.get(text)
    if state is None:
        raise ValueError(
            f"a dictation state is one of {STATES}, "
            f"got {value!r}")
    return state


def _needed(mapping: Dict[str, Any],
            spellings: Tuple[str, ...], what: str) -> Any:
    value = _pick_any(mapping, spellings, what)
    if value is None:
        raise ValueError(f"a record names no {what}")
    return value


def _provenance(mapping: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "detail": _check_long_text(
            _needed(mapping, ("detail", "reason"), "detail"),
            "a detail"),
        "recorded_on": _check_day(
            _needed(mapping, ("recorded_on", "day", "date"),
                    "recorded day")),
        "actor": _check_long_text(
            _needed(mapping, ("actor", "by", "who"), "actor"),
            "an actor"),
        "source": _check_long_text(
            _needed(mapping, ("source",), "source"), "a source"),
        "origin_session": _check_word(
            _needed(mapping, ("origin_session", "session"),
                    "origin session"), "an origin session"),
    }


# ---------------------------------------------------------------------
# The dictation session: push-to-talk in, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DictationSession:
    """One push-to-talk dictation session, as data.

    The session stands in one state - recording
    while the push is held, landed when its
    transcript stands, drafted when the transcript
    stands as a prompt draft - and names the
    capture and transcriber backends its road
    travels. Its availability, its draft text and
    its segment are derived from those fields at
    call time, never stored. A drafted session's
    draft is its transcript, word for word, and
    no session here is ever sent: ``sent`` is a
    derived constant, not a field.
    """

    dictation_id: str
    seq: int
    state: str
    transcript: str
    capture_backend: Optional[str]
    transcriber_backend: Optional[str]
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "dictation_id",
            _check_word(self.dictation_id, "a dictation id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "state", normalize_state(self.state))
        transcript = self.transcript
        if not isinstance(transcript, str) or "\x00" in transcript:
            raise ValueError(
                f"a transcript must be plain text, "
                f"got {transcript!r}")
        transcript = transcript.strip()
        if self.state == "recording" and transcript:
            raise ValueError(
                "a recording dictation holds no transcript "
                "yet - the push is still held")
        if self.state != "recording" and not transcript:
            raise ValueError(
                f"a {self.state} dictation names its "
                f"transcript - a landed transcript is the "
                f"session's whole cargo")
        if len(transcript) > 2000:
            raise ValueError(
                "a transcript is plain text of at most "
                "2000 characters")
        object.__setattr__(self, "transcript", transcript)
        object.__setattr__(
            self, "capture_backend",
            _check_backend(self.capture_backend, "a capture backend"))
        object.__setattr__(
            self, "transcriber_backend",
            _check_backend(
                self.transcriber_backend, "a transcriber backend"))
        object.__setattr__(
            self, "detail", _check_long_text(self.detail, "a detail"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_long_text(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_long_text(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    @property
    def kind(self) -> str:
        return "dictation"

    @property
    def item_id(self) -> str:
        return self.dictation_id

    @property
    def label(self) -> str:
        return self.dictation_id

    @property
    def availability(self) -> str:
        return dictation_availability(self)[0]

    @property
    def availability_reason(self) -> str:
        return dictation_availability(self)[1]

    @property
    def draft_text(self) -> str:
        return draft_text_of(self)

    @property
    def sent(self) -> bool:
        return False

    @property
    def passes(self) -> bool:
        return dictation_passes(self)

    @property
    def segment(self) -> str:
        return segment_of(self)

    def to_record(self) -> Dict[str, Any]:
        word, reason = dictation_availability(self)
        return {
            "type": "voice_in_out_dictation",
            "slice": VOICE_IN_OUT_SLICE,
            "dictation_id": self.dictation_id,
            "seq": self.seq,
            "state": self.state,
            "transcript": self.transcript,
            "capture_backend": self.capture_backend,
            "transcriber_backend": self.transcriber_backend,
            "availability": word,
            "availability_reason": reason,
            "draft_text": self.draft_text,
            "sent": False,
            "passes": self.passes,
            "segment": self.segment,
            "detail": self.detail,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_dictation_ref(value: Any) -> DictationSession:
    if isinstance(value, DictationSession):
        return value
    if isinstance(value, dict):
        return validate_dictation(value)
    raise ValueError(
        f"a dictation session is needed, got {value!r}")


def dictation_availability(
        session: Any) -> Tuple[str, str]:
    """A dictation's availability, derived whole.

    Available while the session names a capture
    and a transcriber backend, neither of them the
    unknown backend; unavailable with the missing
    piece named while either stands unnamed;
    honestly unknown while a named backend is the
    unknown backend.
    """
    current = _check_dictation_ref(session)
    if current.capture_backend is None:
        return ("unavailable",
                "no capture backend is named - no road "
                "in stands recorded for this session")
    if current.transcriber_backend is None:
        return ("unavailable",
                "no transcriber backend is named - a "
                "recording here would land as no words")
    if BACKEND_UNKNOWN in (
            current.capture_backend, current.transcriber_backend):
        return ("unknown",
                "a named backend stands unknown - whether "
                "this road travels is not proven")
    return ("available",
            f"capture {current.capture_backend!r} and "
            f"transcriber {current.transcriber_backend!r} "
            f"stand named")


def draft_text_of(session: Any) -> str:
    """A dictation's prompt draft, derived.

    The transcript itself, once the session stands
    drafted; nothing before that, and never a
    sent text - drafting is all this layer does
    with a transcript.
    """
    current = _check_dictation_ref(session)
    if current.state != "drafted":
        return ""
    return current.transcript


def dictation_passes(session: Any) -> bool:
    """Whether a dictation stands whole.

    Whole while its transcript has landed and
    become a prompt draft on an available road,
    never sent - a session still recording, or
    one whose road stands unavailable or unknown,
    does not yet stand whole.
    """
    current = _check_dictation_ref(session)
    return (current.state == "drafted"
            and current.availability == "available")


def validate_dictation(session: Any) -> DictationSession:
    """Judge one dictation mapping whole."""
    if isinstance(session, DictationSession):
        return session
    if not isinstance(session, dict):
        raise ValueError(
            f"a dictation session must be a mapping, "
            f"got {session!r}")
    derived = set(session) & _DICTATION_DERIVED
    if derived:
        raise ValueError(
            f"a dictation session carries no stored "
            f"{sorted(derived)} - availability, draft and "
            f"segment are derived from its own fields, "
            f"and a dictated prompt is never sent from "
            f"this layer")
    unknown = set(session) - _DICTATION_KEYS - {"type", "slice"}
    if unknown:
        raise ValueError(
            f"a dictation session carries unknown keys: "
            f"{sorted(unknown)}")
    fields = _provenance(session)
    return DictationSession(
        dictation_id=_needed(
            session, ("dictation_id", "id"), "dictation id"),
        seq=_needed(session, ("seq", "sequence", "order"),
                    "sequence"),
        state=_needed(session, ("state", "status"), "state"),
        transcript=session.get("transcript", session.get("text", "")),
        capture_backend=_pick_any(
            session, ("capture_backend", "capture"),
            "capture backend"),
        transcriber_backend=_pick_any(
            session, ("transcriber_backend", "transcriber"),
            "transcriber backend"),
        **fields)


def build_dictation(session: Any = None, **kwargs: Any) -> DictationSession:
    """Build one dictation session from a mapping or fields."""
    if isinstance(session, DictationSession) and not kwargs:
        return session
    if kwargs:
        if session is not None:
            raise ValueError("a dictation is built one way at a time")
        return validate_dictation(dict(kwargs))
    return validate_dictation(session)


def start_dictation(
        dictation_id: Any = "dictation-1", *,
        seq: Any = 1,
        capture_backend: Any = None,
        transcriber_backend: Any = None,
        detail: Any = "Push-to-talk held: the dictation "
                      "session stands recording.",
        recorded_on: Any = "2026-11-09",
        actor: Any = "the jarl",
        source: Any = "voice in and out",
        origin_session: Any = "session-m180") -> DictationSession:
    """Open one push-to-talk dictation session.

    The push is held: the session stands recording
    and holds no transcript yet. The backends it
    names decide its derived availability - naming
    none stands honestly unavailable.
    """
    return DictationSession(
        dictation_id=dictation_id, seq=seq, state="recording",
        transcript="", capture_backend=capture_backend,
        transcriber_backend=transcriber_backend, detail=detail,
        recorded_on=recorded_on, actor=actor, source=source,
        origin_session=origin_session)


def stop_dictation(session: Any, transcript: Any) -> DictationSession:
    """Stop one recording session: its transcript lands.

    The push is released and the words stand as
    the session's transcript - landed, not yet a
    draft, and never sent.
    """
    current = _check_dictation_ref(session)
    if current.state != "recording":
        raise ValueError(
            f"only a recording dictation stops, got a "
            f"{current.state} session")
    return replace(
        current, state="landed",
        transcript=_check_long_text(transcript, "a transcript"))


def draft_dictation(session: Any) -> DictationSession:
    """Stand one landed transcript as a prompt draft.

    The draft's text is the transcript itself,
    derived at call time. Drafting sends nothing:
    the draft waits for the jarl's own hand, as
    every prompt does.
    """
    current = _check_dictation_ref(session)
    if current.state != "landed":
        raise ValueError(
            f"only a landed dictation drafts, got a "
            f"{current.state} session - a transcript "
            f"lands before it drafts")
    return replace(current, state="drafted")


def default_transcriber() -> Any:
    """The shipped audio layer's transcriber, lazily.

    Reaches for ``core/audio.py``'s singleton only
    when called, and returns None where that road
    does not stand (no PortAudio, no sounddevice,
    no key) - an absent road is named, never faked.
    """
    try:
        from .audio import audio_recorder
    except Exception:
        return None
    return audio_recorder.transcribe


def transcribe_dictation(
        session: Any, wav_path: Any,
        transcribe: Any = None) -> DictationSession:
    """Land one recording session's transcript via a seam.

    The transcriber is a callable taking a WAV path
    and returning its words - the shipped audio
    layer's ``transcribe`` by default, reached
    lazily. Where no transcriber stands, or the
    seam returns no words, this refuses plainly
    and lands nothing: a transcript is never
    invented.
    """
    current = _check_dictation_ref(session)
    if current.state != "recording":
        raise ValueError(
            f"only a recording dictation transcribes, "
            f"got a {current.state} session")
    seam = transcribe if transcribe is not None \
        else default_transcriber()
    if seam is None:
        raise ValueError(
            "no transcriber stands on the audio seam - "
            "the existing audio road is unavailable "
            "here, and no transcript is invented")
    text = seam(str(wav_path))
    if not isinstance(text, str) or not text.strip():
        raise ValueError(
            "the transcriber returned no words - the "
            "dictation lands nothing")
    return stop_dictation(current, text)


# ---------------------------------------------------------------------
# The spoken stand-up: text out, through the TTS seam.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SpokenStandup:
    """One spoken stand-up, held as data.

    The stand-up is its text, its speaker, the
    catalog voice cast for it - cast directly
    from the voice catalog, per the house voice
    law, with no cloning and no conversion - and
    the TTS backend it names, with its provenance
    whole. Its availability and segment are
    derived at call time, never stored; the
    speaking itself travels the existing TTS seam
    at the agent layer's word, never here.
    """

    standup_id: str
    seq: int
    speaker: str
    text: str
    voice_name: Optional[str]
    tts_backend: Optional[str]
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "standup_id",
            _check_word(self.standup_id, "a stand-up id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "speaker",
            _check_long_text(self.speaker, "a speaker"))
        object.__setattr__(
            self, "text", _check_long_text(self.text, "a stand-up text"))
        object.__setattr__(
            self, "voice_name",
            _check_backend(self.voice_name, "a catalog voice"))
        object.__setattr__(
            self, "tts_backend",
            _check_backend(self.tts_backend, "a TTS backend"))
        object.__setattr__(
            self, "detail", _check_long_text(self.detail, "a detail"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_long_text(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_long_text(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    @property
    def kind(self) -> str:
        return "standup"

    @property
    def item_id(self) -> str:
        return self.standup_id

    @property
    def label(self) -> str:
        return self.standup_id

    @property
    def availability(self) -> str:
        return standup_availability(self)[0]

    @property
    def availability_reason(self) -> str:
        return standup_availability(self)[1]

    @property
    def passes(self) -> bool:
        return standup_passes(self)

    @property
    def segment(self) -> str:
        return segment_of(self)

    def to_record(self) -> Dict[str, Any]:
        word, reason = standup_availability(self)
        return {
            "type": "voice_in_out_standup",
            "slice": VOICE_IN_OUT_SLICE,
            "standup_id": self.standup_id,
            "seq": self.seq,
            "speaker": self.speaker,
            "text": self.text,
            "voice_name": self.voice_name,
            "tts_backend": self.tts_backend,
            "availability": word,
            "availability_reason": reason,
            "passes": self.passes,
            "segment": self.segment,
            "detail": self.detail,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_standup_ref(value: Any) -> SpokenStandup:
    if isinstance(value, SpokenStandup):
        return value
    if isinstance(value, dict):
        return validate_standup(value)
    raise ValueError(f"a spoken stand-up is needed, got {value!r}")


def standup_availability(standup: Any) -> Tuple[str, str]:
    """A stand-up's availability, derived whole.

    Available while it names a TTS backend and a
    catalog voice, neither of them the unknown
    backend or voice; unavailable with the missing
    piece named while either stands unnamed;
    honestly unknown while a named piece stands
    unknown.
    """
    current = _check_standup_ref(standup)
    if current.tts_backend is None:
        return ("unavailable",
                "no TTS backend is named - no road out "
                "stands recorded for this stand-up")
    if current.voice_name is None:
        return ("unavailable",
                "no catalog voice is cast - a stand-up "
                "is cast directly from the voice "
                "catalog before it is spoken")
    if BACKEND_UNKNOWN in (current.tts_backend, current.voice_name):
        return ("unknown",
                "a named backend or voice stands unknown "
                "- whether this road travels is not proven")
    return ("available",
            f"TTS backend {current.tts_backend!r} and "
            f"catalog voice {current.voice_name!r} stand named")


def standup_passes(standup: Any) -> bool:
    """Whether a stand-up stands whole: its road out stands available."""
    current = _check_standup_ref(standup)
    return current.availability == "available"


def validate_standup(standup: Any) -> SpokenStandup:
    """Judge one spoken stand-up mapping whole."""
    if isinstance(standup, SpokenStandup):
        return standup
    if not isinstance(standup, dict):
        raise ValueError(
            f"a spoken stand-up must be a mapping, got {standup!r}")
    derived = set(standup) & _STANDUP_DERIVED
    if derived:
        raise ValueError(
            f"a spoken stand-up carries no stored "
            f"{sorted(derived)} - availability and segment "
            f"are derived from its own fields, and no "
            f"stand-up here is stored as already spoken")
    unknown = set(standup) - _STANDUP_KEYS - {"type", "slice"}
    if unknown:
        raise ValueError(
            f"a spoken stand-up carries unknown keys: "
            f"{sorted(unknown)}")
    fields = _provenance(standup)
    return SpokenStandup(
        standup_id=_needed(standup, ("standup_id", "id"), "stand-up id"),
        seq=_needed(standup, ("seq", "sequence", "order"), "sequence"),
        speaker=_needed(standup, ("speaker", "agent"), "speaker"),
        text=_needed(standup, ("text", "words"), "stand-up text"),
        voice_name=_pick_any(
            standup, ("voice_name", "voice", "catalog_voice"),
            "catalog voice"),
        tts_backend=_pick_any(
            standup, ("tts_backend", "tts", "backend"), "TTS backend"),
        **fields)


def build_standup(standup: Any = None, **kwargs: Any) -> SpokenStandup:
    """Build one spoken stand-up from a mapping or fields."""
    if isinstance(standup, SpokenStandup) and not kwargs:
        return standup
    if kwargs:
        if standup is not None:
            raise ValueError("a stand-up is built one way at a time")
        return validate_standup(dict(kwargs))
    return validate_standup(standup)


@dataclass(frozen=True)
class SpeechRender:
    """One stand-up's rendering outcome, as data.

    The outcome is the availability word the
    rendering stood at - spoken only while the
    stand-up's road stood available and a speaker
    seam stood on it - with the reason named
    whole. A render is a finding about one call
    through the seam, never a stored claim on the
    stand-up itself.
    """

    standup_id: str
    speaker: str
    voice_name: Optional[str]
    text: str
    outcome: str
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "standup_id",
            _check_word(self.standup_id, "a stand-up id"))
        object.__setattr__(
            self, "speaker",
            _check_long_text(self.speaker, "a speaker"))
        object.__setattr__(
            self, "voice_name",
            _check_backend(self.voice_name, "a catalog voice"))
        object.__setattr__(
            self, "text", _check_long_text(self.text, "a stand-up text"))
        outcome = _clean_text(self.outcome, "an outcome")
        if outcome not in ("spoken",) + AVAILABILITY_WORDS:
            raise ValueError(
                f"a render outcome is 'spoken' or one of "
                f"{AVAILABILITY_WORDS}, got {outcome!r}")
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(
            self, "reason",
            _check_long_text(self.reason, "a reason"))

    @property
    def spoken(self) -> bool:
        return self.outcome == "spoken"

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "voice_in_out_speech_render",
            "slice": VOICE_IN_OUT_SLICE,
            "standup_id": self.standup_id,
            "speaker": self.speaker,
            "voice_name": self.voice_name,
            "text": self.text,
            "outcome": self.outcome,
            "reason": self.reason,
            "spoken": self.spoken,
        }


def default_speaker() -> Any:
    """The shipped TTS layer's speaker, lazily.

    Reaches for ``core/tts.py``'s singleton only
    when called, and returns None where that road
    does not stand. The returned callable takes an
    agent name and a text, as ``TTSManager.speak``
    does, and reports whether the manager stands
    running - speech queued on a stopped manager
    is no speech at all, and is never reported as
    spoken.
    """
    try:
        from .tts import tts_manager
    except Exception:
        return None

    def _speak(agent_name: str, text: str) -> bool:
        if not tts_manager.is_running or tts_manager.is_muted:
            return False
        tts_manager.speak(agent_name, text)
        return True

    return _speak


def speak_standup(standup: Any, speak: Any = None) -> SpeechRender:
    """Render one stand-up to speech through the TTS seam.

    The speaker is a callable taking the speaker's
    name and the stand-up's text - the shipped TTS
    manager's road by default, reached lazily. The
    seam is called only while the stand-up's
    derived availability stands available: an
    unavailable or unknown road is not travelled,
    and its outcome is named, never faked as
    spoken. A seam returning False, or no seam at
    all, likewise renders nothing and says so.
    """
    current = _check_standup_ref(standup)
    word, reason = standup_availability(current)
    if word != "available":
        return SpeechRender(
            standup_id=current.standup_id, speaker=current.speaker,
            voice_name=current.voice_name, text=current.text,
            outcome=word, reason=reason)
    seam = speak if speak is not None else default_speaker()
    if seam is None:
        return SpeechRender(
            standup_id=current.standup_id, speaker=current.speaker,
            voice_name=current.voice_name, text=current.text,
            outcome="unavailable",
            reason="no speaker stands on the TTS seam - "
                   "the existing TTS road is unavailable "
                   "here, and no speech is invented")
    spoken = seam(current.speaker, current.text)
    if spoken is False:
        return SpeechRender(
            standup_id=current.standup_id, speaker=current.speaker,
            voice_name=current.voice_name, text=current.text,
            outcome="unavailable",
            reason="the TTS seam took no speech - the "
                   "manager stands stopped or muted, and "
                   "nothing was spoken")
    return SpeechRender(
        standup_id=current.standup_id, speaker=current.speaker,
        voice_name=current.voice_name, text=current.text,
        outcome="spoken",
        reason="rendered through the existing TTS seam, "
               "in the catalog voice cast for the stand-up")


# ---------------------------------------------------------------------
# The voice action: the standing law, held as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class VoiceAction:
    """One voice action, held whole under the law.

    An action names its spoken phrase and the text
    equivalent that stands beside it - typed words
    that do the same work - with its provenance
    whole. The equivalent is not decoration: an
    action without one is voice-only, and
    voice-only refuses at build time, by name.
    """

    action_id: str
    seq: int
    name: str
    voice_phrase: str
    text_equivalent: str
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "action_id",
            _check_word(self.action_id, "an action id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "name", _check_word(self.name, "an action name"))
        object.__setattr__(
            self, "voice_phrase",
            _check_long_text(self.voice_phrase, "a voice phrase"))
        equivalent = self.text_equivalent
        if not isinstance(equivalent, str) or not equivalent.strip():
            raise ValueError(
                f"voice action {self.name!r} is voice-only: "
                f"it names no text equivalent - voice is "
                f"an extra door, never the only door, and "
                f"a voice-only action refuses by name")
        object.__setattr__(
            self, "text_equivalent",
            _check_long_text(equivalent, "a text equivalent"))
        object.__setattr__(
            self, "detail", _check_long_text(self.detail, "a detail"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_long_text(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_long_text(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    @property
    def kind(self) -> str:
        return "action"

    @property
    def item_id(self) -> str:
        return self.action_id

    @property
    def label(self) -> str:
        return self.name

    @property
    def passes(self) -> bool:
        return True

    @property
    def segment(self) -> str:
        return segment_of(self)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "voice_in_out_action",
            "slice": VOICE_IN_OUT_SLICE,
            "action_id": self.action_id,
            "seq": self.seq,
            "name": self.name,
            "voice_phrase": self.voice_phrase,
            "text_equivalent": self.text_equivalent,
            "voice_only": False,
            "passes": True,
            "segment": self.segment,
            "detail": self.detail,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_action_ref(value: Any) -> VoiceAction:
    if isinstance(value, VoiceAction):
        return value
    if isinstance(value, dict):
        return validate_action(value)
    raise ValueError(f"a voice action is needed, got {value!r}")


def validate_action(action: Any) -> VoiceAction:
    """Judge one voice action mapping whole.

    The standing law is enforced here, by name: a
    mapping claiming the action is voice-only
    refuses with the action's own name in the
    refusal, and a mapping naming no text
    equivalent refuses the same way at the
    dataclass gate.
    """
    if isinstance(action, VoiceAction):
        return action
    if not isinstance(action, dict):
        raise ValueError(
            f"a voice action must be a mapping, got {action!r}")
    derived = set(action) & _ACTION_DERIVED
    if derived:
        raise ValueError(
            f"a voice action carries no stored "
            f"{sorted(derived)} - its segment is derived "
            f"from its own fields")
    unknown = set(action) - _ACTION_KEYS - {"type", "slice"}
    if unknown:
        raise ValueError(
            f"a voice action carries unknown keys: "
            f"{sorted(unknown)}")
    name = _pick_any(action, ("name",), "action name")
    if action.get("voice_only"):
        raise ValueError(
            f"voice action {name!r} is voice-only: it "
            f"claims no text equivalent stands beside "
            f"it - voice is an extra door, never the "
            f"only door, and a voice-only action "
            f"refuses by name")
    fields = _provenance(action)
    return VoiceAction(
        action_id=_needed(action, ("action_id", "id"), "action id"),
        seq=_needed(action, ("seq", "sequence", "order"), "sequence"),
        name=_needed(action, ("name",), "action name"),
        voice_phrase=_needed(
            action, ("voice_phrase", "phrase", "spoken_phrase"),
            "voice phrase"),
        text_equivalent=_pick_any(
            action, ("text_equivalent", "text", "equivalent"),
            "text equivalent"),
        **fields)


def build_action(action: Any = None, **kwargs: Any) -> VoiceAction:
    """Build one voice action from a mapping or fields."""
    if isinstance(action, VoiceAction) and not kwargs:
        return action
    if kwargs:
        if action is not None:
            raise ValueError("an action is built one way at a time")
        return validate_action(dict(kwargs))
    return validate_action(action)


# ---------------------------------------------------------------------
# Derived judgements shared by every item kind.
# ---------------------------------------------------------------------


def segment_of(item: Any) -> str:
    """One item's derived segment, from its own fields."""
    if isinstance(item, DictationSession):
        word, _reason = dictation_availability(item)
        return (
            f"{item.dictation_id}: dictation {item.state}, "
            f"availability {word}, draft never sent")
    if isinstance(item, SpokenStandup):
        word, _reason = standup_availability(item)
        voice = item.voice_name if item.voice_name is not None \
            else "no voice cast"
        return (
            f"{item.standup_id}: standup by {item.speaker}, "
            f"availability {word}, voice {voice}")
    if isinstance(item, VoiceAction):
        return (
            f"{item.name}: text equivalent "
            f"{item.text_equivalent!r} stands - never voice-only")
    raise ValueError(f"a voice item is needed, got {item!r}")


def availability_of(item: Any) -> Tuple[str, str]:
    """One item's availability, derived whole.

    Dictations and stand-ups derive theirs from
    the backends and voices they name. An action's
    road stands available by the law itself: its
    text equivalent stands beside its voice.
    """
    if isinstance(item, DictationSession):
        return dictation_availability(item)
    if isinstance(item, SpokenStandup):
        return standup_availability(item)
    if isinstance(item, VoiceAction):
        return ("available",
                "its text equivalent stands beside its "
                "voice - the action travels by text "
                "whether or not voice stands")
    raise ValueError(f"a voice item is needed, got {item!r}")


def item_passes(item: Any) -> bool:
    """Whether one item of any kind stands whole."""
    if isinstance(item, DictationSession):
        return dictation_passes(item)
    if isinstance(item, SpokenStandup):
        return standup_passes(item)
    if isinstance(item, VoiceAction):
        return True
    raise ValueError(f"a voice item is needed, got {item!r}")


def _check_item_ref(value: Any) -> Any:
    if isinstance(value, (DictationSession, SpokenStandup, VoiceAction)):
        return value
    raise ValueError(f"a voice item is needed, got {value!r}")


def inspect_item_source(piece: Any) -> Dict[str, Any]:
    """Judge one raw voice piece and name what it is.

    A mapping carrying a transcript or a state is
    read as a dictation piece, one carrying a
    speaker or a catalog voice as a stand-up
    piece, and one carrying a voice phrase or a
    text equivalent as an action piece. Anything
    else is named not-a-voice-item.
    """
    if not isinstance(piece, dict):
        return {"kind": None,
                "reason": "not a mapping - no voice item stands here"}
    if "transcript" in piece or "state" in piece \
            or "capture_backend" in piece:
        return {"kind": "dictation",
                "reason": "a dictation piece in the closed kind set"}
    if "speaker" in piece or "voice_name" in piece \
            or "tts_backend" in piece:
        return {"kind": "standup",
                "reason": "a stand-up piece in the closed kind set"}
    if "voice_phrase" in piece or "text_equivalent" in piece:
        if piece.get("voice_only"):
            return {"kind": None,
                    "reason": "a voice-only action piece - "
                              "voice is never the only door, "
                              "and the piece refuses by name"}
        return {"kind": "action",
                "reason": "an action piece in the closed kind set"}
    return {"kind": None,
            "reason": "no transcript, no speaker and no "
                      "voice phrase named - no voice "
                      "item stands here"}


# ---------------------------------------------------------------------
# The view record: the one kind a panel looks at, held whole.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class VoiceView:
    """One view, held as its own record.

    A view looks at every kind at once, or at one
    kind alone. A view only ever looks: standing
    one derives its panel, captures nothing,
    speaks nothing and sends nothing.
    """

    view_id: Optional[str]
    seq: int
    kind_filter: str
    detail: str
    recorded_on: str
    actor: str
    source: str
    origin_session: str

    def __post_init__(self) -> None:
        if self.view_id is not None:
            object.__setattr__(
                self, "view_id",
                _check_word(self.view_id, "a view id"))
        object.__setattr__(self, "seq", _check_seq(self.seq))
        object.__setattr__(
            self, "kind_filter",
            normalize_kind_filter(self.kind_filter))
        object.__setattr__(
            self, "detail", _check_long_text(self.detail, "a detail"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))
        object.__setattr__(
            self, "actor", _check_long_text(self.actor, "an actor"))
        object.__setattr__(
            self, "source", _check_long_text(self.source, "a source"))
        object.__setattr__(
            self, "origin_session",
            _check_word(self.origin_session, "an origin session"))

    def shows(self, item: Any) -> bool:
        current = _check_item_ref(item)
        return self.kind_filter == "all" \
            or current.kind == self.kind_filter

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "voice_in_out_view",
            "slice": VOICE_IN_OUT_SLICE,
            "view_id": self.view_id,
            "seq": self.seq,
            "kind_filter": self.kind_filter,
            "detail": self.detail,
            "recorded_on": self.recorded_on,
            "actor": self.actor,
            "source": self.source,
            "origin_session": self.origin_session,
        }


def _check_view_ref(value: Any) -> VoiceView:
    if isinstance(value, VoiceView):
        return value
    if isinstance(value, dict):
        return validate_view(value)
    raise ValueError(f"a voice view is needed, got {value!r}")


def validate_view(view: Any) -> VoiceView:
    """Judge one view mapping whole."""
    if isinstance(view, VoiceView):
        return view
    if not isinstance(view, dict):
        raise ValueError(f"a voice view must be a mapping, got {view!r}")
    unknown = set(view) - _VIEW_KEYS - {"type", "slice"}
    if unknown:
        raise ValueError(
            f"a voice view carries unknown keys: {sorted(unknown)}")
    fields = _provenance(view)
    return VoiceView(
        view_id=_pick_any(view, ("view_id", "id"), "view id"),
        seq=_needed(view, ("seq", "sequence", "order"), "sequence"),
        kind_filter=_needed(
            view, ("kind_filter", "filter", "kind"), "kind filter"),
        **fields)


def build_view(view: Any = None, **kwargs: Any) -> VoiceView:
    """Build one view from a mapping, a view, or fields."""
    if isinstance(view, VoiceView) and not kwargs:
        return view
    if kwargs:
        if view is not None:
            raise ValueError("a view is built one way at a time")
        return validate_view(dict(kwargs))
    return validate_view(view)


# ---------------------------------------------------------------------
# The panel: derived for one held view.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class VoicePanelRow:
    """One shown item's row on a derived panel."""

    item_id: str
    kind: str
    label: str
    segment: str
    recorded_on: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "item_id", _check_word(self.item_id, "an item id"))
        object.__setattr__(
            self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "label", _check_long_text(self.label, "a label"))
        object.__setattr__(
            self, "segment",
            _check_long_text(self.segment, "a segment"))
        object.__setattr__(
            self, "recorded_on", _check_day(self.recorded_on))

    def to_record(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "kind": self.kind,
            "label": self.label,
            "segment": self.segment,
            "recorded_on": self.recorded_on,
        }


def _row_for_item(item: Any) -> VoicePanelRow:
    current = _check_item_ref(item)
    return VoicePanelRow(
        item_id=current.item_id, kind=current.kind,
        label=current.label, segment=segment_of(current),
        recorded_on=current.recorded_on)


def _check_row_ref(value: Any) -> VoicePanelRow:
    if isinstance(value, VoicePanelRow):
        return value
    raise ValueError(f"a panel row is needed, got {value!r}")


def validate_row(row: Any, item: Any = None) -> VoicePanelRow:
    """Judge one panel row, against its item when one is named."""
    if isinstance(row, VoicePanelRow):
        current = row
    elif isinstance(row, dict):
        unknown = set(row) - _ROW_KEYS
        if unknown:
            raise ValueError(
                f"a panel row carries unknown keys: "
                f"{sorted(unknown)}")
        current = VoicePanelRow(
            item_id=_needed(row, ("item_id", "id"), "item id"),
            kind=_needed(row, ("kind",), "kind"),
            label=_needed(row, ("label", "name"), "label"),
            segment=_needed(row, ("segment",), "segment"),
            recorded_on=_needed(
                row, ("recorded_on", "day", "date"), "recorded day"))
    else:
        raise ValueError(f"a panel row must be a mapping, got {row!r}")
    if item is not None:
        expected = _row_for_item(item)
        if current != expected:
            raise ValueError(
                "a panel row is its item's own derived row - "
                "a stored row disagreeing with its item refuses")
    return current


def build_row(row: Any = None, item: Any = None,
              **kwargs: Any) -> VoicePanelRow:
    """Build one panel row from a mapping, a row, or an item."""
    if item is not None:
        if kwargs:
            raise ValueError("a row is built one way at a time")
        if row is not None:
            return validate_row(row, item)
        return _row_for_item(item)
    if isinstance(row, VoicePanelRow) and not kwargs:
        return row
    if kwargs:
        if row is not None:
            raise ValueError("a row is built one way at a time")
        return validate_row(dict(kwargs))
    return validate_row(row)


@dataclass(frozen=True)
class VoiceKindCount:
    """How many shown items stand of one kind."""

    kind: str
    items: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind", normalize_kind(self.kind))
        object.__setattr__(
            self, "items", _check_count(self.items, "a kind count"))

    def to_record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "items": self.items}


def _check_kind_count_ref(value: Any) -> VoiceKindCount:
    if isinstance(value, VoiceKindCount):
        return value
    if isinstance(value, dict):
        return VoiceKindCount(
            kind=_needed(value, ("kind",), "kind"),
            items=_needed(value, ("items",), "items"))
    raise ValueError(f"a kind count is needed, got {value!r}")


def _kind_counts(rows: Tuple[VoicePanelRow, ...]) -> Tuple[VoiceKindCount, ...]:
    counts = []
    for kind in ITEM_KINDS:
        n = sum(1 for row in rows if row.kind == kind)
        if n:
            counts.append(VoiceKindCount(kind=kind, items=n))
    return tuple(counts)


def _panel_account(total_items: int, total_shown: int,
                   kind_counts: Tuple[VoiceKindCount, ...],
                   kind_filter: str, as_of: Optional[str],
                   passing: int) -> Tuple[str, ...]:
    kinds = ", ".join(f"{c.kind} {c.items}" for c in kind_counts)
    if not kinds:
        kinds = "no kinds"
    return (
        f"The voice book holds {total_items} items as of "
        f"{as_of}: the view {kind_filter!r} shows "
        f"{total_shown} of them: {kinds}; {passing} of "
        f"the shown items stand whole.",
        "Rows stand in held order, the order the book "
        "itself stands in, so two panels of one view "
        "diff cleanly, segment by segment.",
        "Every segment is derived from its item's own "
        "fields - availability from the backends and "
        "voices it names, a draft from its transcript "
        "- and no judgement is stored on any item.",
        "Voice is an extra door, never the only door: "
        "every shown action names a text equivalent, "
        "and no dictated prompt is sent from this layer.",
    )


@dataclass(frozen=True)
class VoicePanel:
    """The derived panel of one book under one view.

    Rows stand in held order; the totals are the
    rows' own counts and the kind counts stand in
    the closed kind order. A stored panel is
    judged whole: its totals, counts and account
    must all be the rows' own derived shape.
    """

    panel_id: Optional[str]
    view_id: Optional[str]
    kind_filter: str
    rows: Tuple[VoicePanelRow, ...]
    total_items: int
    total_shown: int
    kind_counts: Tuple[VoiceKindCount, ...]
    as_of: Optional[str]
    account: Tuple[str, ...]

    def __post_init__(self) -> None:
        if self.panel_id is not None:
            object.__setattr__(
                self, "panel_id",
                _check_word(self.panel_id, "a panel id"))
        if self.view_id is not None:
            object.__setattr__(
                self, "view_id",
                _check_word(self.view_id, "a view id"))
        object.__setattr__(
            self, "kind_filter",
            normalize_kind_filter(self.kind_filter))
        rows = tuple(_check_row_ref(r) for r in self.rows)
        object.__setattr__(self, "rows", rows)
        ids = [r.item_id for r in rows]
        if len(set(ids)) != len(ids):
            raise ValueError("panel rows stand one row per item")
        for row in rows:
            if self.kind_filter != "all" and (
                    row.kind != self.kind_filter):
                raise ValueError(
                    "a panel row stands outside its view's "
                    "kind - the view narrows the panel, "
                    "never widens it")
        for field in ("total_items", "total_shown"):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a panel's {field}"))
        counts = tuple(
            _check_kind_count_ref(c) for c in self.kind_counts)
        object.__setattr__(self, "kind_counts", counts)
        if self.as_of is not None:
            object.__setattr__(
                self, "as_of", _check_day(self.as_of, "an as-of day"))
        object.__setattr__(self, "account", _check_account(self.account))
        if self.total_shown != len(rows):
            raise ValueError("a panel's shown total is its rows' own count")
        if self.total_items < self.total_shown:
            raise ValueError(
                "a panel's item total cannot stand below "
                "its shown total")
        if counts != _kind_counts(rows):
            raise ValueError("a panel's kind counts are its rows' own counts")
        if rows and self.as_of is not None and (
                self.as_of < max(r.recorded_on for r in rows)):
            raise ValueError("a panel's as-of day precedes one of its rows")

    def row_for(self, item_id: Any) -> VoicePanelRow:
        """The row one item id names (KeyError if absent)."""
        wanted = _check_word(item_id, "an item id")
        for row in self.rows:
            if row.item_id == wanted:
                return row
        raise KeyError(f"no row named {wanted!r} stands on the panel")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "voice_in_out_panel",
            "slice": VOICE_IN_OUT_SLICE,
            "panel_id": self.panel_id,
            "view_id": self.view_id,
            "kind_filter": self.kind_filter,
            "rows": [r.to_record() for r in self.rows],
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "kind_counts": [c.to_record() for c in self.kind_counts],
            "as_of": self.as_of,
            "account": list(self.account),
        }


def _held_items(source: Any) -> Tuple[Any, ...]:
    if isinstance(source, VoiceBook):
        return source.items()
    if isinstance(source, VoiceRegistry):
        return source.book().items()
    if isinstance(source, (DictationSession, SpokenStandup, VoiceAction)):
        return (source,)
    if isinstance(source, (list, tuple)):
        return tuple(_check_item_ref(i) for i in source)
    raise ValueError(f"a voice source is needed, got {source!r}")


def _held_views(source: Any) -> Tuple[VoiceView, ...]:
    if isinstance(source, VoiceBook):
        return source.views
    if isinstance(source, VoiceRegistry):
        return source.book().views
    return ()


def _resolve_view(source: Any, view: Any) -> VoiceView:
    if isinstance(view, VoiceView):
        return view
    if isinstance(view, str):
        wanted = _check_word(view, "a view id")
        for held in _held_views(source):
            if held.view_id == wanted:
                return held
        raise KeyError(f"no view named {wanted!r} stands in the book")
    if view is None:
        return _default_view(source)
    raise ValueError(f"a voice view is needed, got {view!r}")


def _default_view(source: Any) -> VoiceView:
    views = _held_views(source)
    if isinstance(source, VoiceBook) and source.panels:
        for panel in source.panels:
            if panel.view_id is not None:
                for held in views:
                    if held.view_id == panel.view_id:
                        return held
    if views:
        return views[0]
    return VoiceView(
        view_id=None, seq=1, kind_filter="all",
        detail="See the whole voice book, every kind at once.",
        recorded_on="2026-11-09", actor="the coordinator",
        source="voice in and out", origin_session="session-m180")


def shown_items(source: Any, view: Any = None) -> Tuple[Any, ...]:
    """The items one view shows, in held order."""
    held_view = _resolve_view(source, view)
    return tuple(i for i in _held_items(source) if held_view.shows(i))


def items_for_kind(source: Any, kind: Any) -> Tuple[Any, ...]:
    """The items of one kind, in held order."""
    wanted = normalize_kind(kind)
    return tuple(i for i in _held_items(source) if i.kind == wanted)


def passing_items(source: Any) -> Tuple[Any, ...]:
    """The items standing whole, in held order."""
    return tuple(i for i in _held_items(source) if item_passes(i))


def total_items(source: Any) -> int:
    """How many items a source holds."""
    return len(_held_items(source))


def derive_panel(source: Any, view: Any = None) -> VoicePanel:
    """Derive the panel of a book under one view."""
    held_view = _resolve_view(source, view)
    items = _held_items(source)
    shown = tuple(i for i in items if held_view.shows(i))
    rows = tuple(_row_for_item(i) for i in shown)
    counts = _kind_counts(rows)
    days = [i.recorded_on for i in shown] or \
        [i.recorded_on for i in items]
    as_of = max(days) if days else None
    passing = sum(1 for i in shown if item_passes(i))
    return VoicePanel(
        panel_id=None, view_id=held_view.view_id,
        kind_filter=held_view.kind_filter, rows=rows,
        total_items=len(items), total_shown=len(shown),
        kind_counts=counts, as_of=as_of,
        account=_panel_account(
            len(items), len(shown), counts,
            held_view.kind_filter, as_of, passing))


def validate_panel(panel: Any, source: Any = None) -> VoicePanel:
    """Judge one panel whole, against its source when named."""
    if isinstance(panel, VoicePanel):
        current = panel
    elif isinstance(panel, dict):
        unknown = set(panel) - _PANEL_KEYS - {"type", "slice"}
        if unknown:
            raise ValueError(
                f"a panel carries unknown keys: {sorted(unknown)}")
        rows_in = _needed(panel, ("rows", "shown"), "rows")
        counts_in = _pick_any(
            panel, ("kind_counts", "kinds"), "kind counts") or ()
        current = VoicePanel(
            panel_id=_pick_any(panel, ("panel_id", "id"), "panel id"),
            view_id=_pick_any(panel, ("view_id", "view"), "view id"),
            kind_filter=_needed(
                panel, ("kind_filter", "filter", "kind"),
                "kind filter"),
            rows=tuple(validate_row(r) for r in rows_in),
            total_items=_needed(
                panel, ("total_items", "items"), "total items"),
            total_shown=_needed(
                panel, ("total_shown", "matched"), "total shown"),
            kind_counts=tuple(
                _check_kind_count_ref(c) for c in counts_in),
            as_of=_pick_any(panel, ("as_of", "day"), "as-of day"),
            account=_needed(
                panel, ("account", "statements"), "account"))
    else:
        raise ValueError(f"a panel must be a mapping, got {panel!r}")
    if source is not None:
        derived = derive_panel(source, current.view_id)
        if (current.kind_filter != derived.kind_filter
                or current.rows != derived.rows
                or current.total_items != derived.total_items
                or current.total_shown != derived.total_shown
                or current.kind_counts != derived.kind_counts
                or current.as_of != derived.as_of
                or current.account != derived.account):
            raise ValueError(
                "a stored panel disagreeing with its derived "
                "panel refuses - panels are derived, never "
                "written by hand")
    return current


def build_panel(panel: Any = None, source: Any = None,
                **kwargs: Any) -> VoicePanel:
    """Build one panel from a mapping, a panel, or a source."""
    if kwargs:
        if panel is not None:
            raise ValueError("a panel is built one way at a time")
        return validate_panel(dict(kwargs), source)
    if isinstance(panel, VoicePanel):
        return validate_panel(panel, source)
    if isinstance(panel, dict):
        return validate_panel(panel, source)
    if panel is None and source is not None:
        return derive_panel(source)
    return validate_panel(panel, source)


# ---------------------------------------------------------------------
# The verdict: derived for the whole book under one view.
# ---------------------------------------------------------------------


def _verdict_word(total_shown: int, passing_shown: int) -> str:
    if total_shown == 0 or passing_shown == 0:
        return "shut"
    if passing_shown == total_shown:
        return "open"
    return "strained"


@dataclass(frozen=True)
class VoiceVerdict:
    """The derived verdict of one whole book under one view.

    The word is read off the shown items alone:
    shut while no shown item stands whole, open
    while every shown item does, strained
    otherwise. A stored verdict is judged against
    those tallies in ``__post_init__``.
    """

    total_items: int
    total_shown: int
    passing_shown: int
    distinct_kinds: int
    earliest_on: Optional[str]
    latest_on: Optional[str]
    verdict: str

    def __post_init__(self) -> None:
        for field in ("total_items", "total_shown",
                      "passing_shown", "distinct_kinds"):
            object.__setattr__(
                self, field,
                _check_count(getattr(self, field), f"a verdict's {field}"))
        if self.earliest_on is not None:
            object.__setattr__(
                self, "earliest_on",
                _check_day(self.earliest_on, "an earliest day"))
        if self.latest_on is not None:
            object.__setattr__(
                self, "latest_on",
                _check_day(self.latest_on, "a latest day"))
        if self.earliest_on is not None and self.latest_on is not None \
                and self.latest_on < self.earliest_on:
            raise ValueError("a verdict's latest day precedes its earliest")
        if self.total_shown > self.total_items:
            raise ValueError(
                "a verdict's shown tally cannot exceed its item total")
        if self.passing_shown > self.total_shown:
            raise ValueError(
                "a verdict's passing tally cannot exceed its shown tally")
        if self.total_shown == 0 and (
                self.distinct_kinds != 0 or self.passing_shown != 0):
            raise ValueError(
                "an empty showing names no kind and no passing item")
        if self.distinct_kinds > self.total_shown:
            raise ValueError(
                "a verdict's kinds cannot exceed its shown items")
        word = _clean_text(self.verdict, "a verdict")
        if word not in VERDICT_WORDS:
            raise ValueError(
                f"a verdict is one of {VERDICT_WORDS}, got {word!r}")
        object.__setattr__(self, "verdict", word)
        if word != _verdict_word(self.total_shown, self.passing_shown):
            raise ValueError(
                "a verdict's word is derived from its tallies, "
                "never chosen")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "voice_in_out_verdict",
            "slice": VOICE_IN_OUT_SLICE,
            "total_items": self.total_items,
            "total_shown": self.total_shown,
            "passing_shown": self.passing_shown,
            "distinct_kinds": self.distinct_kinds,
            "earliest_on": self.earliest_on,
            "latest_on": self.latest_on,
            "verdict": self.verdict,
        }


def derive_verdict(source: Any, view: Any = None) -> VoiceVerdict:
    """Derive the verdict of a book under one view."""
    held_view = _resolve_view(source, view)
    items = _held_items(source)
    shown = tuple(i for i in items if held_view.shows(i))
    passing = sum(1 for i in shown if item_passes(i))
    days = [i.recorded_on for i in shown]
    return VoiceVerdict(
        total_items=len(items), total_shown=len(shown),
        passing_shown=passing,
        distinct_kinds=len({i.kind for i in shown}),
        earliest_on=min(days) if days else None,
        latest_on=max(days) if days else None,
        verdict=_verdict_word(len(shown), passing))


def _check_verdict_ref(value: Any) -> VoiceVerdict:
    if isinstance(value, VoiceVerdict):
        return value
    raise ValueError(f"a voice verdict is needed, got {value!r}")


def validate_verdict(verdict: Any, source: Any = None,
                     view: Any = None) -> VoiceVerdict:
    """Judge one verdict whole, against its source when named."""
    if isinstance(verdict, VoiceVerdict):
        current = verdict
    elif isinstance(verdict, dict):
        unknown = set(verdict) - _VERDICT_KEYS - {"type", "slice"}
        if unknown:
            raise ValueError(
                f"a verdict carries unknown keys: {sorted(unknown)}")
        current = VoiceVerdict(
            total_items=_needed(
                verdict, ("total_items", "items"), "total items"),
            total_shown=_needed(
                verdict, ("total_shown", "matched"), "total shown"),
            passing_shown=_needed(
                verdict, ("passing_shown", "passing"), "passing shown"),
            distinct_kinds=_needed(
                verdict, ("distinct_kinds", "kinds"), "distinct kinds"),
            earliest_on=_pick_any(
                verdict, ("earliest_on", "earliest"), "earliest day"),
            latest_on=_pick_any(
                verdict, ("latest_on", "latest"), "latest day"),
            verdict=_needed(verdict, ("verdict",), "verdict"))
    else:
        raise ValueError(f"a verdict must be a mapping, got {verdict!r}")
    if source is not None:
        derived = derive_verdict(source, view)
        if current != derived:
            raise ValueError(
                "a stored verdict disagreeing with its derived "
                "verdict refuses - verdicts are derived, "
                "never written by hand")
    return current


def build_verdict(verdict: Any = None, source: Any = None,
                  **kwargs: Any) -> VoiceVerdict:
    """Build one verdict from a mapping, a verdict, or a source."""
    if kwargs:
        if verdict is not None:
            raise ValueError("a verdict is built one way at a time")
        return validate_verdict(dict(kwargs), source)
    if isinstance(verdict, VoiceVerdict):
        return validate_verdict(verdict, source)
    if isinstance(verdict, dict):
        return validate_verdict(verdict, source)
    if verdict is None and source is not None:
        return derive_verdict(source)
    return validate_verdict(verdict, source)


# ---------------------------------------------------------------------
# The book: voice in and out, held whole under a title.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class VoiceBook:
    """One set of voice items and views, held whole.

    Dictations, stand-ups and actions stand in
    held order - one item per id within its kind,
    one sequence per kind - views stand in
    recorded order, one view per sequence and per
    id, and every stored panel is judged against
    the book and the view it stands under. The
    book carries no verdict: verdicts are derived
    from its items at call time.
    """

    title: str
    dictations: Tuple[DictationSession, ...] = ()
    standups: Tuple[SpokenStandup, ...] = ()
    actions: Tuple[VoiceAction, ...] = ()
    views: Tuple[VoiceView, ...] = ()
    panels: Tuple[VoicePanel, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_title(self.title, "a book title"))
        dictations = tuple(
            _check_dictation_ref(d) for d in self.dictations)
        object.__setattr__(self, "dictations", dictations)
        ids = [d.dictation_id for d in dictations]
        if len(set(ids)) != len(ids):
            raise ValueError("a book holds one dictation per dictation id")
        seqs = [d.seq for d in dictations]
        if len(set(seqs)) != len(seqs):
            raise ValueError("a book holds one dictation per sequence")
        standups = tuple(_check_standup_ref(s) for s in self.standups)
        object.__setattr__(self, "standups", standups)
        ids = [s.standup_id for s in standups]
        if len(set(ids)) != len(ids):
            raise ValueError("a book holds one stand-up per stand-up id")
        seqs = [s.seq for s in standups]
        if len(set(seqs)) != len(seqs):
            raise ValueError("a book holds one stand-up per sequence")
        actions = tuple(_check_action_ref(a) for a in self.actions)
        object.__setattr__(self, "actions", actions)
        ids = [a.action_id for a in actions]
        if len(set(ids)) != len(ids):
            raise ValueError("a book holds one action per action id")
        names = [a.name for a in actions]
        if len(set(names)) != len(names):
            raise ValueError("a book holds one action per action name")
        seqs = [a.seq for a in actions]
        if len(set(seqs)) != len(seqs):
            raise ValueError("a book holds one action per sequence")
        views = tuple(_check_view_ref(v) for v in self.views)
        object.__setattr__(self, "views", views)
        seqs = [v.seq for v in views]
        if seqs != sorted(seqs) or len(set(seqs)) != len(seqs):
            raise ValueError(
                "a book's views stand in recorded order, "
                "one view per sequence")
        view_ids = [v.view_id for v in views if v.view_id is not None]
        if len(set(view_ids)) != len(view_ids):
            raise ValueError("a book holds one view per view id")
        panels = tuple(validate_panel(p, self) for p in self.panels)
        object.__setattr__(self, "panels", panels)

    def items(self) -> Tuple[Any, ...]:
        """Every item in held order: dictations, stand-ups, actions."""
        return tuple(self.dictations) + tuple(self.standups) \
            + tuple(self.actions)

    def dictation_for(self, dictation_id: Any) -> DictationSession:
        """The dictation one id names (KeyError if absent)."""
        wanted = _check_word(dictation_id, "a dictation id")
        for item in self.dictations:
            if item.dictation_id == wanted:
                return item
        raise KeyError(
            f"no dictation named {wanted!r} stands in the book")

    def standup_for(self, standup_id: Any) -> SpokenStandup:
        """The stand-up one id names (KeyError if absent)."""
        wanted = _check_word(standup_id, "a stand-up id")
        for item in self.standups:
            if item.standup_id == wanted:
                return item
        raise KeyError(f"no stand-up named {wanted!r} stands in the book")

    def action_for(self, action_id: Any) -> VoiceAction:
        """The action one id names (KeyError if absent)."""
        wanted = _check_word(action_id, "an action id")
        for item in self.actions:
            if item.action_id == wanted:
                return item
        raise KeyError(f"no action named {wanted!r} stands in the book")

    def view_for(self, view_id: Any) -> VoiceView:
        """The view one id names (KeyError if absent)."""
        wanted = _check_word(view_id, "a view id")
        for view in self.views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands in the book")

    def panel_for(self, panel_id: Any) -> VoicePanel:
        """The panel one id names (KeyError if absent)."""
        wanted = _check_word(panel_id, "a panel id")
        for panel in self.panels:
            if panel.panel_id == wanted:
                return panel
        raise KeyError(f"no panel named {wanted!r} stands in the book")

    def dictation_ids(self) -> Tuple[str, ...]:
        return tuple(d.dictation_id for d in self.dictations)

    def standup_ids(self) -> Tuple[str, ...]:
        return tuple(s.standup_id for s in self.standups)

    def action_ids(self) -> Tuple[str, ...]:
        return tuple(a.action_id for a in self.actions)

    def view_ids(self) -> Tuple[Optional[str], ...]:
        return tuple(v.view_id for v in self.views)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "voice_in_out_book",
            "slice": VOICE_IN_OUT_SLICE,
            "title": self.title,
            "dictations": [d.to_record() for d in self.dictations],
            "standups": [s.to_record() for s in self.standups],
            "actions": [a.to_record() for a in self.actions],
            "views": [v.to_record() for v in self.views],
            "panels": [p.to_record() for p in self.panels],
            "dictation_count": len(self.dictations),
            "standup_count": len(self.standups),
            "action_count": len(self.actions),
            "view_count": len(self.views),
            "item_count": len(self.items()),
        }


def _judge_book_panels(book: VoiceBook) -> None:
    for panel in book.panels:
        validate_panel(panel, book)


def _strip_derived(raw: Dict[str, Any],
                     derived: frozenset) -> Dict[str, Any]:
    stored = dict(raw)
    stored.pop("type", None)
    stored.pop("slice", None)
    for key in derived:
        stored.pop(key, None)
    stored.pop("voice_only", None)
    return stored


def validate_book(data: Any, *, require_example: bool = False) -> VoiceBook:
    """Judge one voice file's data whole and return its book."""
    if isinstance(data, VoiceBook):
        book = data
        _judge_book_panels(book)
        if require_example:
            _check_example(book)
        return book
    if not isinstance(data, dict):
        raise ValueError(f"a voice book must be a mapping, got {data!r}")
    if "verdict" in data or "segment" in data:
        raise ValueError(
            "a voice book carries no stored verdict or "
            "segment - judgements are derived from its "
            "items, never stored")
    unknown = set(data) - _VOICE_IN_OUT_KEYS
    if unknown:
        raise ValueError(
            f"a voice book carries unknown keys: {sorted(unknown)}")
    if data.get("schema") != VOICE_IN_OUT_SCHEMA:
        raise ValueError(
            f"a voice book's schema must be "
            f"{VOICE_IN_OUT_SCHEMA!r}, got {data.get('schema')!r}")
    if data.get("slice") != VOICE_IN_OUT_SLICE:
        raise ValueError(
            f"a voice book's slice must be "
            f"{VOICE_IN_OUT_SLICE!r}, got {data.get('slice')!r}")
    guide = data.get("guide") or {}
    title = _pick_any(guide, ("title", "name"), "title")
    if title is None:
        title = _pick_any(data, ("title", "name"), "title")
    if title is None:
        raise ValueError("a voice book names no title")
    dictations = [
        validate_dictation(_strip_derived(raw, _DICTATION_DERIVED))
        for raw in data.get("dictations") or []]
    standups = [
        validate_standup(_strip_derived(raw, _STANDUP_DERIVED))
        for raw in data.get("standups") or []]
    actions = []
    for raw in data.get("actions") or []:
        if isinstance(raw, dict) and raw.get("voice_only"):
            validate_action(dict(raw))
        actions.append(
            validate_action(_strip_derived(raw, _ACTION_DERIVED)))
    views = []
    for raw in data.get("views") or []:
        stored = dict(raw)
        stored.pop("type", None)
        stored.pop("slice", None)
        views.append(validate_view(stored))
    book = VoiceBook(
        title=title,
        dictations=tuple(dictations),
        standups=tuple(standups),
        actions=tuple(actions),
        views=tuple(views),
        panels=tuple(
            validate_panel(p) for p in data.get("panels") or []))
    _judge_book_panels(book)
    if require_example:
        _check_example(book)
    return book


def _check_example(book: VoiceBook) -> None:
    if book.title != _EXAMPLE_TITLE:
        raise ValueError(
            f"the shipped example book is {_EXAMPLE_TITLE!r}, "
            f"got {book.title!r}")
    if book.dictation_ids() != _EXAMPLE_DICTATION_IDS:
        raise ValueError("the shipped example book's dictations differ")
    if book.standup_ids() != _EXAMPLE_STANDUP_IDS:
        raise ValueError("the shipped example book's stand-ups differ")
    if book.action_ids() != _EXAMPLE_ACTION_IDS:
        raise ValueError("the shipped example book's actions differ")
    first = book.dictations[0]
    if first.dictation_id != _EXAMPLE_FIRST_DICTATION_ID:
        raise ValueError("the shipped example book's first dictation differs")
    if book.view_ids() != _EXAMPLE_VIEW_IDS:
        raise ValueError("the shipped example book's views differ")
    if len(book.panels) != 1 or (
            book.panels[0].panel_id != _EXAMPLE_PANEL_ID):
        raise ValueError("the shipped example book's panel differs")
    if book.panels[0].as_of != _EXAMPLE_AS_OF:
        raise ValueError("the shipped example book's as-of day differs")
    derived = derive_panel(book, book.panels[0].view_id)
    if tuple(r.item_id for r in book.panels[0].rows) != tuple(
            r.item_id for r in derived.rows):
        raise ValueError("the shipped example book's panel rows differ")


def build_book(book: Any = None, **kwargs: Any) -> VoiceBook:
    """Build one book from a mapping, a book, or fields."""
    if isinstance(book, VoiceBook) and not kwargs:
        return validate_book(book)
    if kwargs:
        if book is not None:
            raise ValueError("a book is built one way at a time")
        fields = dict(kwargs)
    elif isinstance(book, dict) and (
            "dictations" in book or "standups" in book
            or "actions" in book) and (
            "schema" not in book and "guide" not in book
            and "canon_note" not in book):
        fields = dict(book)
    else:
        return _book_from(book, require_example=False)
    unknown = set(fields) - _BOOK_KEYS - {
        "dictations", "standups", "actions", "views", "panels"}
    if unknown:
        raise ValueError(
            f"a voice book carries unknown keys: {sorted(unknown)}")
    title = _pick_any(fields, ("title", "name"), "title")
    if title is None:
        raise ValueError("a voice book names no title")
    return VoiceBook(
        title=title,
        dictations=tuple(
            _check_dictation_ref(d)
            for d in fields.get("dictations") or ()),
        standups=tuple(
            _check_standup_ref(s)
            for s in fields.get("standups") or ()),
        actions=tuple(
            _check_action_ref(a)
            for a in fields.get("actions") or ()),
        views=tuple(
            _check_view_ref(v) for v in fields.get("views") or ()),
        panels=tuple(
            validate_panel(p) for p in fields.get("panels") or ()))


def _book_from(data: Any, *, require_example: bool) -> VoiceBook:
    if isinstance(data, VoiceBook):
        return validate_book(data, require_example=require_example)
    if isinstance(data, dict):
        return validate_book(data, require_example=require_example)
    raise ValueError(f"a voice book must be a mapping, got {data!r}")


def load_voice_in_out(
        data: Optional[Dict[str, Any]] = None) -> VoiceBook:
    """Load the shipped example book, or judge *data* as one."""
    if data is None:
        data = load_resource(VOICE_IN_OUT_RESOURCE)
        return _book_from(data, require_example=True)
    return _book_from(data, require_example=False)


def load_voice_in_out_file(path: Any) -> VoiceBook:
    """Load one voice file from disk, anywhere it stands."""
    import yaml
    text = Path(str(path)).read_text(encoding="utf-8")
    return _book_from(yaml.safe_load(text), require_example=False)


# ---------------------------------------------------------------------
# The registry: voice items and views held one by one.
# ---------------------------------------------------------------------


class VoiceRegistry:
    """An in-memory holding of voice items and views.

    The registry is the pure layer's model of a
    session's voice book: dictations, stand-ups
    and actions are held under their ids, one item
    per id within its kind and one action per
    name, in held order, and views are held in
    recorded order, one view per sequence and per
    id. Holding is data only - nothing held here
    captures audio, speaks, or sends a prompt.
    """

    def __init__(self, book: Any = None) -> None:
        self._dictations: List[DictationSession] = []
        self._standups: List[SpokenStandup] = []
        self._actions: List[VoiceAction] = []
        self._views: List[VoiceView] = []
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

    def _check_dictation_free(self, item: DictationSession) -> None:
        for held in self._dictations:
            if held.dictation_id == item.dictation_id:
                raise ValueError(
                    f"a dictation already stands under id "
                    f"{item.dictation_id!r}")
            if held.seq == item.seq:
                raise ValueError(
                    f"a dictation already stands at sequence "
                    f"{item.seq}")

    def register_dictation(self, item: Any) -> DictationSession:
        """Hold one dictation, judged whole before it is held."""
        validated = _check_dictation_ref(item)
        self._check_dictation_free(validated)
        self._dictations.append(validated)
        return validated

    def _check_standup_free(self, item: SpokenStandup) -> None:
        for held in self._standups:
            if held.standup_id == item.standup_id:
                raise ValueError(
                    f"a stand-up already stands under id "
                    f"{item.standup_id!r}")
            if held.seq == item.seq:
                raise ValueError(
                    f"a stand-up already stands at sequence "
                    f"{item.seq}")

    def register_standup(self, item: Any) -> SpokenStandup:
        """Hold one stand-up, judged whole before it is held."""
        validated = _check_standup_ref(item)
        self._check_standup_free(validated)
        self._standups.append(validated)
        return validated

    def _check_action_free(self, item: VoiceAction) -> None:
        for held in self._actions:
            if held.action_id == item.action_id:
                raise ValueError(
                    f"an action already stands under id "
                    f"{item.action_id!r}")
            if held.name == item.name:
                raise ValueError(
                    f"an action already stands under name "
                    f"{item.name!r} - the book holds one "
                    f"action per name")
            if held.seq == item.seq:
                raise ValueError(
                    f"an action already stands at sequence "
                    f"{item.seq}")

    def register_action(self, item: Any) -> VoiceAction:
        """Hold one action, judged whole before it is held."""
        validated = _check_action_ref(item)
        self._check_action_free(validated)
        self._actions.append(validated)
        return validated

    def _check_view_free(self, view: VoiceView) -> None:
        for held in self._views:
            if view.view_id is not None and (
                    held.view_id == view.view_id):
                raise ValueError(
                    f"a view already stands under id "
                    f"{view.view_id!r}")
            if held.seq == view.seq:
                raise ValueError(
                    f"a view already stands at sequence "
                    f"{view.seq} - the book holds one "
                    f"view per place")

    def register_view(self, view: Any) -> VoiceView:
        """Hold one view record, judged whole first."""
        validated = _check_view_ref(view)
        self._check_view_free(validated)
        if validated.view_id is None:
            validated = VoiceView(
                view_id=self._fresh_view_id(
                    {v.view_id for v in self._views}),
                seq=validated.seq,
                kind_filter=validated.kind_filter,
                detail=validated.detail,
                recorded_on=validated.recorded_on,
                actor=validated.actor, source=validated.source,
                origin_session=validated.origin_session)
        self._views.append(validated)
        self._views.sort(key=lambda v: v.seq)
        return validated

    def register_book(self, book: Any) -> VoiceBook:
        """Hold a whole book, judged whole first."""
        validated = build_book(book)
        for item in validated.dictations:
            self._check_dictation_free(item)
        for item in validated.standups:
            self._check_standup_free(item)
        for item in validated.actions:
            self._check_action_free(item)
        if self._title is None:
            self._title = validated.title
        elif validated.title != self._title:
            raise ValueError(
                "a second book under a different title refuses - "
                "one book stands in one registry")
        for item in validated.dictations:
            self._dictations.append(item)
        for item in validated.standups:
            self._standups.append(item)
        for item in validated.actions:
            self._actions.append(item)
        for view in validated.views:
            self.register_view(view)
        return self.book()

    def get_dictation(self, dictation_id: Any) -> DictationSession:
        wanted = _check_word(dictation_id, "a dictation id")
        for item in self._dictations:
            if item.dictation_id == wanted:
                return item
        raise KeyError(f"no dictation named {wanted!r} stands held")

    def get_standup(self, standup_id: Any) -> SpokenStandup:
        wanted = _check_word(standup_id, "a stand-up id")
        for item in self._standups:
            if item.standup_id == wanted:
                return item
        raise KeyError(f"no stand-up named {wanted!r} stands held")

    def get_action(self, action_id: Any) -> VoiceAction:
        wanted = _check_word(action_id, "an action id")
        for item in self._actions:
            if item.action_id == wanted:
                return item
        raise KeyError(f"no action named {wanted!r} stands held")

    def get_view(self, view_id: Any) -> VoiceView:
        wanted = _check_word(view_id, "a view id")
        for view in self._views:
            if view.view_id == wanted:
                return view
        raise KeyError(f"no view named {wanted!r} stands held")

    def latest_view(self) -> VoiceView:
        if not self._views:
            raise KeyError("no view stands held")
        return self._views[-1]

    def list_dictations(self) -> Tuple[DictationSession, ...]:
        return tuple(self._dictations)

    def list_standups(self) -> Tuple[SpokenStandup, ...]:
        return tuple(self._standups)

    def list_actions(self) -> Tuple[VoiceAction, ...]:
        return tuple(self._actions)

    def list_views(self) -> Tuple[VoiceView, ...]:
        return tuple(self._views)

    def list_items(self) -> Tuple[Any, ...]:
        return tuple(self._dictations) + tuple(self._standups) \
            + tuple(self._actions)

    def book(self) -> VoiceBook:
        return VoiceBook(
            title=self._title or "Voice In and Out",
            dictations=tuple(self._dictations),
            standups=tuple(self._standups),
            actions=tuple(self._actions),
            views=tuple(self._views))

    def panel(self, view: Any = None) -> VoicePanel:
        return derive_panel(self.book(), view)

    def verdict(self, view: Any = None) -> VoiceVerdict:
        return derive_verdict(self.book(), view)


# ---------------------------------------------------------------------
# Session news, plain words, and the screens.
# ---------------------------------------------------------------------


def dictation_record(session: Any) -> Dict[str, Any]:
    """The session-news record of one dictation."""
    current = _check_dictation_ref(session)
    record_out = current.to_record()
    record_out["news"] = True
    record_out["headline"] = (
        f"Voice in and out dictation {current.dictation_id}: "
        f"{segment_of(current)}.")
    return record_out


def standup_record(standup: Any) -> Dict[str, Any]:
    """The session-news record of one stand-up."""
    current = _check_standup_ref(standup)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Voice in and out stand-up {current.standup_id}: "
        f"{segment_of(current)}.")
    return record


def action_record(action: Any) -> Dict[str, Any]:
    """The session-news record of one voice action."""
    current = _check_action_ref(action)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Voice in and out action {current.action_id}: "
        f"{segment_of(current)}.")
    return record


def item_record(item: Any) -> Dict[str, Any]:
    """The session-news record of one item of any kind."""
    if isinstance(item, DictationSession):
        return dictation_record(item)
    if isinstance(item, SpokenStandup):
        return standup_record(item)
    if isinstance(item, VoiceAction):
        return action_record(item)
    raise ValueError(f"a voice item is needed, got {item!r}")


def view_record(view: Any) -> Dict[str, Any]:
    """The session-news record of one view record."""
    current = _check_view_ref(view)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Voice in and out view {current.view_id or current.seq}: "
        f"kind {current.kind_filter!r} - {current.detail}")
    return record


def panel_record(panel: Any, source: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived panel."""
    current = validate_panel(panel, source)
    record = current.to_record()
    record["news"] = True
    kinds = ", ".join(
        f"{c.kind} {c.items}" for c in current.kind_counts)
    record["headline"] = (
        f"Voice in and out panel as of {current.as_of}: "
        f"{current.total_shown} of {current.total_items} "
        f"items show for kind {current.kind_filter!r} "
        f"({kinds}).")
    return record


def verdict_record(verdict: Any, source: Any = None,
                   view: Any = None) -> Dict[str, Any]:
    """The session-news record of one derived verdict."""
    current = validate_verdict(verdict, source, view)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Voice in and out verdict: {current.verdict} - "
        f"{current.passing_shown} of {current.total_shown} "
        f"shown items stand whole across "
        f"{current.distinct_kinds} kinds, from "
        f"{current.earliest_on} to {current.latest_on}.")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one voice book."""
    current = book if isinstance(book, VoiceBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Voice in and out {current.title}: "
        f"{record['item_count']} items named, "
        f"{record['view_count']} views held - "
        f"{len(passing_items(current))} of "
        f"{record['item_count']} items stand whole.")
    return record


def plain_words(session: Any) -> str:
    """One dictation, in one plain sentence."""
    current = _check_dictation_ref(session)
    return (
        f"{segment_of(current)} - one dictation on "
        f"session {current.dictation_id}, standing "
        f"{current.state}. Its transcript lands as a "
        f"prompt draft and is never auto-sent.")


def standup_plain_words(standup: Any) -> str:
    """One stand-up, in one plain sentence."""
    current = _check_standup_ref(standup)
    return (
        f"{segment_of(current)} - one stand-up by "
        f"{current.speaker}, spoken through the "
        f"existing TTS seam in its cast catalog "
        f"voice, and standing in text beside its "
        f"voice, never only in voice.")


def action_plain_words(action: Any) -> str:
    """One voice action, in one plain sentence."""
    current = _check_action_ref(action)
    return (
        f"{segment_of(current)} - say "
        f"{current.voice_phrase!r} or use the text "
        f"equivalent {current.text_equivalent!r}: "
        f"voice is an extra door, never the only door.")


def panel_plain_words(source: Any, view: Any = None) -> str:
    """The panel in plain words, in full."""
    if isinstance(source, VoicePanel):
        panel = validate_panel(source)
        title = None
    elif isinstance(source, (VoiceBook, VoiceRegistry)):
        book = source if isinstance(
            source, VoiceBook) else source.book()
        panel = derive_panel(
            book, view if view is not None
            else _default_view(book))
        title = book.title
    else:
        raise ValueError(f"a voice source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    lines.append("Shown, in held order:")
    for row in panel.rows:
        lines.append(
            f"{row.item_id}: {row.segment} "
            f"({row.recorded_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def verdict_plain_words(source: Any, view: Any = None) -> str:
    """The book verdict in plain words, in full."""
    if isinstance(source, VoiceVerdict):
        verdict = validate_verdict(source)
    elif isinstance(source, (VoiceBook, VoiceRegistry)):
        book = source if isinstance(
            source, VoiceBook) else source.book()
        verdict = derive_verdict(
            book, view if view is not None
            else _default_view(book))
    else:
        raise ValueError(f"a voice source is needed, got {source!r}")
    return (
        f"Voice in and out verdict: {verdict.verdict} - "
        f"{verdict.passing_shown} of {verdict.total_shown} "
        f"shown items stand whole, across "
        f"{verdict.distinct_kinds} kinds, from "
        f"{verdict.earliest_on} to {verdict.latest_on} - "
        f"every judgement is derived from the items' "
        f"own fields.")


def view_plain_words(view: Any) -> str:
    """One view record, in one plain sentence."""
    current = _check_view_ref(view)
    return (
        f"View {current.view_id or current.seq} looks at "
        f"kind {current.kind_filter!r}, recorded on "
        f"{current.recorded_on} by {current.actor}: "
        f"{current.detail} A view only ever looks - it "
        f"captures nothing, speaks nothing and sends "
        f"nothing.")


def _source_book(source: Any) -> VoiceBook:
    if source is None:
        return load_voice_in_out()
    if isinstance(source, VoiceRegistry):
        return source.book()
    if isinstance(source, VoiceBook):
        return source
    raise ValueError(f"a voice book is needed, got {source!r}")


def format_dictation(session: Any) -> str:
    """One dictation session as a screen block."""
    current = _check_dictation_ref(session)
    word, reason = dictation_availability(current)
    lines = [
        f"{current.dictation_id}: {segment_of(current)}",
        f"State: {current.state}",
        f"Transcript: {current.transcript if current.transcript else 'none yet - the push stands held'}",
        f"Capture backend: {current.capture_backend if current.capture_backend is not None else 'none named'}",
        f"Transcriber backend: {current.transcriber_backend if current.transcriber_backend is not None else 'none named'}",
        f"Availability: {word} - {reason}",
        f"Draft: {current.draft_text if current.draft_text else 'no draft stands yet'} (a draft is never auto-sent)",
        f"Words: {current.detail}",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_standup(standup: Any) -> str:
    """One spoken stand-up as a screen block."""
    current = _check_standup_ref(standup)
    word, reason = standup_availability(current)
    lines = [
        f"{current.standup_id}: {segment_of(current)}",
        f"Speaker: {current.speaker}",
        f"Text: {current.text}",
        f"Catalog voice: {current.voice_name if current.voice_name is not None else 'none cast'}",
        f"TTS backend: {current.tts_backend if current.tts_backend is not None else 'none named'}",
        f"Availability: {word} - {reason}",
        f"Words: {current.detail}",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_action(action: Any) -> str:
    """One voice action as a screen block."""
    current = _check_action_ref(action)
    lines = [
        f"{current.action_id}: {segment_of(current)}",
        f"Name: {current.name}",
        f"Voice phrase: {current.voice_phrase}",
        f"Text equivalent: {current.text_equivalent}",
        "Voice-only: no - voice is an extra door, never the only door.",
        f"Words: {current.detail}",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_view(view: Any) -> str:
    """One view record as a screen block."""
    current = _check_view_ref(view)
    lines = [
        f"{current.view_id or '-'}: kind "
        f"{current.kind_filter!r}",
        f"Words: {current.detail}",
        f"Recorded: on {current.recorded_on} by {current.actor} "
        f"from {current.source} in {current.origin_session}.",
    ]
    return "\n".join(lines)


def format_book(source: Any = None, kind: Any = None) -> str:
    """The book as derived segments, in held order.

    By default the lines are every item's derived
    segment. With ``kind`` only that kind's items
    stand in the list.
    """
    book = _source_book(source)
    wanted = normalize_kind(kind) if kind is not None else None
    lines = []
    for item in book.items():
        if wanted is not None and item.kind != wanted:
            continue
        lines.append(f"{item.item_id}: {segment_of(item)}")
    if not lines:
        lines.append("No items stand in the book on that reading.")
    return "\n".join(lines)


def format_panel(source: Any = None, view: Any = None) -> str:
    """The panel as a screen block: every row and the account."""
    if isinstance(source, VoicePanel):
        panel = validate_panel(source)
        lines: list = []
    else:
        book = _source_book(source)
        panel = derive_panel(
            book, view if view is not None
            else _default_view(book))
        lines = [f"Panel in {book.title}:"]
    lines.append("Shown, in held order:")
    for row in panel.rows:
        lines.append(
            f"{row.item_id}: {row.segment} ({row.recorded_on})")
    lines.extend(panel.account)
    return "\n".join(lines)


def format_verdict(source: Any = None, view: Any = None) -> str:
    """The verdict as a screen block."""
    if isinstance(source, VoiceVerdict):
        verdict = validate_verdict(source)
        title = "the book"
    else:
        book = _source_book(source)
        verdict = derive_verdict(
            book, view if view is not None
            else _default_view(book))
        title = book.title
    return (
        f"Verdict in Voice In and Out over {title}: "
        f"{verdict.verdict} - {verdict.passing_shown} of "
        f"{verdict.total_shown} shown items stand whole, "
        f"across {verdict.distinct_kinds} kinds, from "
        f"{verdict.earliest_on} to {verdict.latest_on}.")


def format_voice_in_out_screen(source: Any = None) -> str:
    """The whole voice-in-and-out screen for one book."""
    book = _source_book(source)
    view = _default_view(book)
    panel = derive_panel(book, view)
    verdict = derive_verdict(book, view)
    lines = [
        f"Voice In and Out (M-180) - {book.title}",
        format_book(book),
        f"Panel: {panel.total_shown} of "
        f"{panel.total_items} items show "
        f"for kind {panel.kind_filter!r}.",
        f"Verdict: {verdict.verdict}.",
        "This layer holds voice as data only - it "
        "captures no live audio in tests, builds no "
        "new TTS engine and sends no prompt: voice "
        "is an extra door, never the only door.",
    ]
    return "\n".join(lines)


def parse_voice_in_out_args(args: Any) -> Tuple[str, Any]:
    """Parse the /voiceinout grammar into (action, target).

    ``""``/``show``/``list`` show the book;
    ``dictation <dictation-id>`` shows one
    dictation whole; ``standup <standup-id>``
    shows one stand-up; ``action <action-id>``
    shows one voice action; ``view <view-id>``
    shows one held view record; ``kind <kind>``
    shows one kind's items; ``panel`` and
    ``verdict`` show the derived panel and
    verdict under the book's own view. Anything
    else raises ValueError carrying the usage line.
    """
    if args is None:
        return ("show", None)
    if not isinstance(args, str):
        raise ValueError(USAGE)
    parts = args.split()
    if not parts or parts == ["show"] or parts == ["list"]:
        return ("show", None)
    if parts[0] == "dictation" and len(parts) == 2:
        return ("dictation", _check_word(parts[1], "a dictation id"))
    if parts[0] == "standup" and len(parts) == 2:
        return ("standup", _check_word(parts[1], "a stand-up id"))
    if parts[0] == "action" and len(parts) == 2:
        return ("action", _check_word(parts[1], "an action id"))
    if parts[0] == "view" and len(parts) == 2:
        return ("view", _check_word(parts[1], "a view id"))
    if parts[0] == "kind" and len(parts) == 2:
        try:
            return ("kind", normalize_kind(parts[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if parts == ["panel"]:
        return ("panel", None)
    if parts == ["verdict"]:
        return ("verdict", None)
    raise ValueError(USAGE)
