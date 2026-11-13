"""Agent character voices (All-Features roadmap slice M-136).

Part VI continues here. The roadmap's words:
``cast members keep their written characters
(the house cast) in how they report - flavour
in the reporting, never in the code or the
facts.``

What already shipped, and what this slice adds:

* The crew itself is already data
  (``core/crew_members.py``, M-121): every member
  names the character file that carries their
  voice. What nothing held is the voice itself
  as checkable data - the markers and phrasing a
  member reports in - nor a guarantee that the
  flavour stays in the reporting and never
  leaks into the facts being reported.
* This slice is that guarantee, as a pure layer:
  a voice book validated as data - one voice
  profile per member (the member's id, the
  voice's name, its register, its signature
  markers, the greeting that opens a report and
  the sign-off that closes one) under a title,
  plus example reports whose facts a profile's
  voice frames - the shipped data file
  (``mythic_agent/data/character_voices.yaml``)
  holding one example voice book in exactly the
  shape a real voices file takes, a loader for
  a voices file anywhere on disk, report
  rendering that carries facts verbatim under
  the voice's framing, a record shaped as
  session news, and a small in-memory registry
  model. This module calls no model, generates
  nothing live, renders no live report and
  imports no agent / UI code; the agent layer
  owns holding the voices for a session and
  showing a report on demand.

Honesty rules, enforced here and pinned by tests:

* **Flavour lives in the reporting, never in
  the facts.** A report is two separate parts:
  FACTS, carried verbatim from their source,
  byte for byte, unalterable by the voice; and
  FLAVOUR, the profile's greeting and sign-off
  framing those facts. The two never mix: a
  report record holds its facts and its
  flavour in separate fields, and the rendered
  text is the flavour around the facts, never
  inside them.
* **Flavour inside a fact refuses.** A fact
  that carries any of its teller's voice
  markers - the voice's signature phrases -
  refuses: the marker is flavour, and flavour
  inside a fact would let the voice bend what
  it reports. A profile likewise holds no
  facts at all: a profile naming facts
  refuses, because a voice frames facts, it
  does not own them.
* **A report is rendered, never stored
  loose.** A report's flavour is read off its
  teller's profile at render time - the
  greeting and sign-off the profile holds - so
  a stored report whose flavour disagrees
  with its profile, or whose facts disagree
  with their source facts by so much as one
  character, refuses, exactly as a stored
  stand-up digest does (M-134).
* **Members are the shipped casting.** A
  profile names its member as an M-121 member
  id, read exactly as that layer reads one
  (``core/crew_members.py``) - composed by
  import, never re-read here. One member
  holds one voice in a book: two profiles for
  one member refuse.
* **Data only.** No model is called, nothing
  is generated or rendered live, and no
  member's code or facts are altered here: a
  voice here is a validated record of how a
  member reports, and a report is a
  deterministic formatting of facts already
  held. The roadmap names the board (Part
  VIII) as where crew state will be visible;
  that board does not exist yet, so the voices
  are visible through this slice's own
  /voices screen, and nothing here claims a
  board exists.
* **Malformed refuses.** An unknown register,
  an empty voice name, greeting or fact, a
  malformed member, a duplicate member or
  profile id anywhere in the book, a report
  naming a member the book holds no voice
  for, and unknown keys in a profile, a
  report or a voices mapping all raise
  instead of being skipped or guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..resources import load_resource
from .crew_members import normalize_member_id
from .validation import ValidationError

__all__ = [
    "CHARACTER_VOICES_RESOURCE",
    "CHARACTER_VOICES_SCHEMA",
    "CHARACTER_VOICES_SLICE",
    "PLAIN_EXPLANATION",
    "USAGE",
    "VOICE_REGISTERS",
    "VoiceBook",
    "VoiceProfile",
    "VoiceRegistry",
    "VoicedReport",
    "book_record",
    "build_book",
    "build_profile",
    "build_report",
    "format_character_voices_screen",
    "format_profile",
    "format_profiles",
    "format_registers",
    "format_report",
    "load_character_voices",
    "load_character_voices_file",
    "normalize_register",
    "parse_voice_args",
    "plain_words",
    "profile_record",
    "render_report",
    "report_plain_words",
    "report_record",
    "validate_book",
    "validate_profile",
    "validate_report",
]

CHARACTER_VOICES_SLICE = "M-136"

#: The packaged data resource holding the example voice book.
CHARACTER_VOICES_RESOURCE = "character_voices.yaml"

#: The schema word a voices file must carry.
CHARACTER_VOICES_SCHEMA = "mythic.character_voices/1"

#: The registers a voice can stand in: plain
#: speech, a warm telling, a wry telling, or a
#: grim one. The register is data about the
#: voice's framing, never a fact.
VOICE_REGISTERS = ("plain", "warm", "wry", "grim")

_REGISTER_READINGS = {
    "plain": "plain",
    "flat": "plain",
    "neutral": "plain",
    "unadorned": "plain",
    "bare": "plain",
    "warm": "warm",
    "hearty": "warm",
    "lyrical": "warm",
    "fireside": "warm",
    "wry": "wry",
    "dry": "wry",
    "ironic": "wry",
    "deadpan": "wry",
    "grim": "grim",
    "stern": "grim",
    "grave": "grim",
    "stark": "grim",
}

_PROFILE_KEYS = frozenset({
    "profile_id", "id", "member", "member_id", "voice_name",
    "name", "voice", "register", "tone", "markers", "phrases",
    "greeting", "opening", "sign_off", "closing",
})

_REPORT_KEYS = frozenset({
    "report_id", "id", "member", "member_id", "title", "name",
    "facts", "source_facts", "flavour_open", "opening",
    "greeting", "flavour_close", "closing", "sign_off",
})

_BOOK_KEYS = frozenset({"title", "name"})

_VOICES_KEYS = frozenset({
    "schema", "slice", "part", "part_title",
    "voices_note", "guide", "profiles", "reports",
})

#: The shipped example book's title, held to this
#: by the loader's example check.
_EXAMPLE_TITLE = "Character voices at the M-135 slice boundary"

#: The shipped example's member ids in each
#: register, in book order, pinned by the loader.
_EXAMPLE_REGISTERS = {
    "plain": ("auditor",),
    "warm": ("skald",),
    "wry": ("scribe",),
    "grim": ("guardian",),
}

#: The shipped example's one report: the skald
#: telling the crew-sizing result, its facts
#: pinned byte-for-byte by the loader.
_EXAMPLE_REPORT_ID = "sizing-told-at-the-fire"

_EXAMPLE_REPORT_FACTS = (
    "The sizing book held four task shapes at the "
    "M-134 slice boundary.",
    "The tangled single-file fix derived one pair of "
    "hands, because the work was tightly coupled.",
    "The wide census sweep derived six pairs of "
    "hands, the honest crew's cap.",
)

PLAIN_EXPLANATION = (
    "Agent character voices: the house cast keep "
    "their written characters in how they report - "
    "flavour in the reporting, never in the code "
    "or the facts. A voice profile holds one "
    "member's voice as data - its register, its "
    "signature markers, the greeting that opens a "
    "report and the sign-off that closes one - and "
    "a report carries its facts verbatim, framed "
    "by the voice's flavour and never mixed into "
    "it. This layer holds voices and renderings "
    "as data only; it calls no model, generates "
    "nothing live and alters no member's code or "
    "facts itself."
)

USAGE = (
    "Usage: /voices, /voices show, "
    "/voices profile <member-id>, "
    "/voices report <report-id>, /voices plain, "
    "/voices warm, /voices wry, /voices grim, "
    "/voices registers"
)


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _check_short_text(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if len(text) > 200 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"200 characters, got {len(text)} characters")
    return text


def _check_long_text(value: Any, what: str) -> str:
    text = _clean_text(value, what)
    if len(text) > 2000 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"2000 characters, got {len(text)} characters")
    return text


def _check_flavour_text(value: Any, what: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{what} must be text, got {value!r}")
    text = value.strip()
    if len(text) > 2000 or "\x00" in text:
        raise ValueError(
            f"{what} must be plain text of at most "
            f"2000 characters, got {len(text)} characters")
    return text


def _check_markers(value: Any) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a voice's markers must be a list of phrases, "
            f"got {value!r}")
    markers = tuple(
        _check_short_text(m, "a voice marker") for m in value)
    if not markers:
        raise ValueError("a voice names at least one marker")
    if len(markers) > 8:
        raise ValueError(
            f"a voice names at most 8 markers, got {len(markers)}")
    if len(set(markers)) != len(markers):
        raise ValueError("a voice names one marker twice")
    return markers


def _check_facts(value: Any) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"a report's facts must be a list of statements, "
            f"got {value!r}")
    facts = tuple(_check_long_text(f, "a fact") for f in value)
    if not facts:
        raise ValueError("a report carries at least one fact")
    if len(facts) > 99:
        raise ValueError(
            f"a report carries at most 99 facts, got {len(facts)}")
    return facts


def normalize_register(value: Any) -> str:
    """The canonical register a word names.

    Register words read case-insensitively, with
    dashes read as underscores: ``flat`` and
    ``neutral`` read as plain, ``hearty`` and
    ``fireside`` as warm, ``dry`` and ``deadpan``
    as wry, and ``stern`` and ``stark`` as grim.
    Anything else raises - a voice stands in one
    of the four, never a maybe.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted in _REGISTER_READINGS:
            return _REGISTER_READINGS[wanted]
    raise ValueError(
        "a voice register must be one of %s, got %r"
        % ("/".join(VOICE_REGISTERS), value))


def _pick_any(mapping: Dict[str, Any], spellings: Tuple[str, ...],
              what: str) -> Any:
    values = [mapping[s] for s in spellings if s in mapping]
    if not values:
        return None
    if any(value != values[0] for value in values[1:]):
        raise ValueError(f"a record names two different {what}")
    return values[0]


# ---------------------------------------------------------------------
# The profile: one member's written voice, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class VoiceProfile:
    """One house-cast member's character voice, as data.

    ``member`` is the M-121 member whose voice
    this is; ``voice_name`` names the voice;
    ``register`` is the register the voice stands
    in; ``markers`` are the voice's signature
    phrases - flavour, held as data; ``greeting``
    is the flavour that opens the member's
    reports and ``sign_off`` the flavour that
    closes them. A profile holds no facts: a
    voice frames facts, it never owns them.
    Constructing one validates its shape only:
    whether its member already stands in its
    book is the book's concern.
    """

    profile_id: Optional[str] = None
    member: str = ""
    voice_name: str = ""
    register: str = ""
    markers: Tuple[str, ...] = ()
    greeting: str = ""
    sign_off: str = ""

    def __post_init__(self) -> None:
        if self.profile_id is not None:
            object.__setattr__(
                self, "profile_id",
                normalize_member_id(self.profile_id))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "voice_name",
            _check_short_text(self.voice_name, "a voice name"))
        object.__setattr__(
            self, "register", normalize_register(self.register))
        object.__setattr__(
            self, "markers", _check_markers(self.markers))
        object.__setattr__(
            self, "greeting",
            _check_long_text(self.greeting, "a greeting"))
        object.__setattr__(
            self, "sign_off",
            _check_long_text(self.sign_off, "a sign-off"))

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "character_voice_profile",
            "slice": CHARACTER_VOICES_SLICE,
            "profile_id": self.profile_id,
            "member": self.member,
            "voice_name": self.voice_name,
            "register": self.register,
            "markers": list(self.markers),
            "greeting": self.greeting,
            "sign_off": self.sign_off,
        }


def validate_profile(profile: Any) -> VoiceProfile:
    """Validate one profile into a VoiceProfile.

    Accepts a VoiceProfile or a mapping naming a
    ``member`` (or ``member_id``), a
    ``voice_name`` (or ``name`` / ``voice``), a
    ``register`` (or ``tone``), ``markers`` (or
    ``phrases``), a ``greeting`` (or ``opening``),
    a ``sign_off`` (or ``closing``) and an
    optional ``profile_id`` (or ``id``). A
    profile naming facts refuses - a voice
    frames facts, it does not own them - naming
    two spellings of one field with different
    values refuses, and unknown keys refuse.
    """
    if isinstance(profile, VoiceProfile):
        return profile
    if not isinstance(profile, dict):
        raise ValueError(f"a profile must be a mapping, got {profile!r}")
    unknown = set(profile) - _PROFILE_KEYS
    if unknown:
        raise ValueError(
            "unknown profile keys: %s" % ", ".join(sorted(unknown)))
    member = _pick_any(profile, ("member", "member_id"), "members")
    if member is None:
        raise ValueError("a profile is missing its member")
    voice_name = _pick_any(
        profile, ("voice_name", "name", "voice"), "voice names")
    if voice_name is None:
        raise ValueError("a profile is missing its voice name")
    register = _pick_any(profile, ("register", "tone"), "registers")
    if register is None:
        raise ValueError("a profile is missing its register")
    markers = _pick_any(profile, ("markers", "phrases"), "markers")
    if markers is None:
        raise ValueError("a profile is missing its markers")
    greeting = _pick_any(profile, ("greeting", "opening"), "greetings")
    if greeting is None:
        raise ValueError("a profile is missing its greeting")
    sign_off = _pick_any(profile, ("sign_off", "closing"), "sign-offs")
    if sign_off is None:
        raise ValueError("a profile is missing its sign-off")
    kwargs: Dict[str, Any] = {
        "member": member, "voice_name": voice_name,
        "register": register, "markers": markers,
        "greeting": greeting, "sign_off": sign_off}
    profile_id = _pick_any(profile, ("profile_id", "id"), "profile ids")
    if profile_id is not None:
        kwargs["profile_id"] = profile_id
    return VoiceProfile(**kwargs)


def build_profile(profile: Any = None, **kwargs: Any) -> VoiceProfile:
    """Build one validated profile, from a mapping or field words."""
    if isinstance(profile, VoiceProfile) and not kwargs:
        return profile
    if isinstance(profile, dict) or profile is None:
        merged: Dict[str, Any] = {}
        if isinstance(profile, dict):
            merged.update(profile)
        merged.update(kwargs)
        return validate_profile(merged)
    raise ValueError(f"a profile must be a mapping, got {profile!r}")


# ---------------------------------------------------------------------
# The report: facts verbatim, framed by the voice's flavour.
# ---------------------------------------------------------------------


def _check_facts_against_profile(
        facts: Tuple[str, ...], profile: VoiceProfile) -> None:
    """Refuse any fact carrying its teller's flavour.

    A fact that names one of the teller's voice
    markers has flavour inside it, and flavour
    inside a fact would let the voice bend what
    it reports - so it refuses, always.
    """
    for fact in facts:
        folded = fact.casefold()
        for marker in profile.markers:
            if marker.casefold() in folded:
                raise ValueError(
                    f"a fact carries its teller's marker "
                    f"{marker!r} - flavour lives in the "
                    f"reporting, never inside a fact")


@dataclass(frozen=True)
class VoicedReport:
    """One report: facts carried verbatim, framed by flavour.

    ``member`` is the M-121 member telling the
    report; ``title`` names it; ``facts`` are
    the report's facts, carried byte for byte
    from their source, unalterable by the voice;
    ``flavour_open`` and ``flavour_close`` are
    the teller's greeting and sign-off framing
    them. The facts and the flavour are separate
    fields here and in the record: the flavour
    stands around the facts, never inside them.
    A report is normally rendered from its
    teller's profile (see :func:`render_report`);
    constructing one directly validates its
    shape only.
    """

    report_id: Optional[str] = None
    member: str = ""
    title: str = ""
    facts: Tuple[str, ...] = ()
    flavour_open: str = ""
    flavour_close: str = ""

    def __post_init__(self) -> None:
        if self.report_id is not None:
            object.__setattr__(
                self, "report_id", normalize_member_id(self.report_id))
        object.__setattr__(
            self, "member", normalize_member_id(self.member))
        object.__setattr__(
            self, "title", _check_short_text(self.title, "a title"))
        object.__setattr__(self, "facts", _check_facts(self.facts))
        object.__setattr__(
            self, "flavour_open",
            _check_flavour_text(self.flavour_open, "an opening flavour"))
        object.__setattr__(
            self, "flavour_close",
            _check_flavour_text(self.flavour_close, "a closing flavour"))

    def rendered_text(self) -> str:
        """The report as told: flavour, facts verbatim, flavour.

        Every fact stands in the text exactly as
        it stands in ``facts`` - byte for byte -
        with the voice's flavour before and after
        it, never inside it.
        """
        parts = []
        if self.flavour_open:
            parts.append(self.flavour_open)
        parts.extend(self.facts)
        if self.flavour_close:
            parts.append(self.flavour_close)
        return "\n".join(parts)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "character_voice_report",
            "slice": CHARACTER_VOICES_SLICE,
            "report_id": self.report_id,
            "member": self.member,
            "title": self.title,
            "facts": list(self.facts),
            "flavour_open": self.flavour_open,
            "flavour_close": self.flavour_close,
        }


def render_report(profile: Any, facts: Any, title: Any = "",
                  report_id: Any = None) -> VoicedReport:
    """Render one report from a profile and source facts.

    The flavour is read off the profile - its
    greeting opens the report, its sign-off
    closes it - and the facts are carried
    verbatim, exactly as given. A fact carrying
    one of the teller's markers refuses:
    flavour inside a fact is the one thing a
    voice may never do to what it reports.
    """
    prof = profile if isinstance(profile, VoiceProfile) \
        else build_profile(profile)
    checked = _check_facts(facts)
    _check_facts_against_profile(checked, prof)
    return VoicedReport(
        report_id=report_id, member=prof.member, title=title,
        facts=checked, flavour_open=prof.greeting,
        flavour_close=prof.sign_off)


def validate_report(report: Any, profile: Any = None,
                      facts: Any = None) -> VoicedReport:
    """Validate one report into a VoicedReport.

    Accepts a VoicedReport or a mapping naming a
    ``member`` (or ``member_id``), a ``title``
    (or ``name``), ``facts`` (or
    ``source_facts``) and optionally a
    ``flavour_open`` (or ``opening`` / ``greeting``)
    and a ``flavour_close`` (or ``closing`` /
    ``sign_off``). When *profile* is given, the
    report is judged against its teller: the
    member must be the profile's, any stored
    flavour must equal the profile's greeting
    and sign-off exactly (missing flavour is
    read off the profile), and no fact may carry
    a marker. When *facts* is given, the
    report's facts must equal those source facts
    byte for byte. Any disagreement refuses,
    because flavour is rendered off the profile
    and facts are carried verbatim, never stored
    loose. A stored report naming no flavour of
    its own and judged against no profile
    refuses for the same reason.
    """
    prof = None
    if profile is not None:
        prof = profile if isinstance(profile, VoiceProfile) \
            else build_profile(profile)
    if isinstance(report, VoicedReport):
        current = report
    elif isinstance(report, dict):
        unknown = set(report) - _REPORT_KEYS
        if unknown:
            raise ValueError(
                "unknown report keys: %s" % ", ".join(sorted(unknown)))
        member = _pick_any(report, ("member", "member_id"), "members")
        if member is None:
            if prof is None:
                raise ValueError("a report is missing its member")
            member = prof.member
        title = _pick_any(report, ("title", "name"), "titles")
        if title is None:
            raise ValueError("a report is missing its title")
        named_facts = _pick_any(
            report, ("facts", "source_facts"), "facts")
        if named_facts is None:
            raise ValueError("a report is missing its facts")
        open_ = _pick_any(
            report, ("flavour_open", "opening", "greeting"), "openings")
        close = _pick_any(
            report, ("flavour_close", "closing", "sign_off"), "closings")
        if prof is not None:
            if open_ is None:
                open_ = prof.greeting
            if close is None:
                close = prof.sign_off
        elif open_ is None or close is None:
            raise ValueError(
                "a stored report names no flavour of its own - "
                "judge it against its teller's profile")
        report_id = _pick_any(report, ("report_id", "id"), "report ids")
        current = VoicedReport(
            report_id=report_id, member=member, title=title,
            facts=named_facts, flavour_open=open_,
            flavour_close=close)
    else:
        raise ValueError(f"a report must be a mapping, got {report!r}")
    if prof is not None:
        if current.member != prof.member:
            raise ValueError(
                "a report's member disagrees with its teller's "
                "profile - a report is told by its own member")
        if current.flavour_open != prof.greeting \
                or current.flavour_close != prof.sign_off:
            raise ValueError(
                "a stored report's flavour disagrees with its "
                "teller's profile - flavour is rendered off the "
                "profile, never stored loose")
        _check_facts_against_profile(current.facts, prof)
    if facts is not None and _check_facts(facts) != current.facts:
        raise ValueError(
            "a stored report's facts disagree with their source "
            "facts - facts are carried verbatim, never rewritten")
    return current


def build_report(report: Any = None, profile: Any = None,
                   facts: Any = None, **kwargs: Any) -> VoicedReport:
    """Build one validated report, from a mapping or field words."""
    if isinstance(report, VoicedReport) and not kwargs \
            and profile is None and facts is None:
        return report
    if isinstance(report, dict) or report is None:
        merged: Dict[str, Any] = {}
        if isinstance(report, dict):
            merged.update(report)
        merged.update(kwargs)
        return validate_report(merged, profile, facts)
    return validate_report(report, profile, facts)


# ---------------------------------------------------------------------
# The book: the house cast's voices whole, under a title.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class VoiceBook:
    """One voice book, whole, as data.

    ``title`` names the book; ``profiles`` are
    the voices, in file order, one per member -
    a member holds one voice in a book;
    ``reports`` are example reports, each judged
    against its teller's profile as the book is
    built, so a held report's flavour is always
    its profile's and its facts are always
    verbatim.
    """

    title: str = ""
    profiles: Tuple[VoiceProfile, ...] = ()
    reports: Tuple[VoicedReport, ...] = ()
    voices_note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "title", _check_short_text(self.title, "a title"))
        profiles = tuple(
            p if isinstance(p, VoiceProfile) else validate_profile(p)
            for p in self.profiles)
        members = [p.member for p in profiles]
        if len(set(members)) != len(members):
            raise ValueError("a book holds two voices for one member")
        ids = [p.profile_id for p in profiles if p.profile_id is not None]
        if len(set(ids)) != len(ids):
            raise ValueError("a book holds one profile id twice")
        object.__setattr__(self, "profiles", profiles)
        by_member = {p.member: p for p in profiles}
        held = []
        for raw in self.reports:
            member = raw.member if isinstance(raw, VoicedReport) \
                else _pick_any(raw, ("member", "member_id"), "members")
            if member is None or normalize_member_id(member) \
                    not in by_member:
                raise ValueError(
                    "a report names a member the book holds "
                    "no voice for")
            held.append(validate_report(
                raw, profile=by_member[normalize_member_id(member)]))
        report_ids = [r.report_id for r in held if r.report_id is not None]
        if len(set(report_ids)) != len(report_ids):
            raise ValueError("a book holds one report id twice")
        object.__setattr__(self, "reports", tuple(held))
        if not isinstance(self.voices_note, str):
            raise ValueError("a voice book's note must be text")
        object.__setattr__(self, "voices_note", self.voices_note.strip())

    def profile_for(self, member: Any) -> VoiceProfile:
        """The voice one member holds in this book; unknown raises."""
        wanted = normalize_member_id(member)
        for profile in self.profiles:
            if profile.member == wanted:
                return profile
        raise KeyError(f"no voice in the book for member: {wanted!r}")

    def profiles_for(self, register: Any) -> Tuple[VoiceProfile, ...]:
        """Every voice standing in one register, in book order."""
        wanted = normalize_register(register)
        return tuple(p for p in self.profiles if p.register == wanted)

    def member_ids(self) -> Tuple[str, ...]:
        """Every member holding a voice, in book order."""
        return tuple(p.member for p in self.profiles)

    def profile_ids(self) -> Tuple[str, ...]:
        """Every held profile id, in book order (id-less skipped)."""
        return tuple(p.profile_id for p in self.profiles if p.profile_id)

    def report_for(self, report_id: Any) -> VoicedReport:
        """The report one id names in this book; unknown raises."""
        wanted = normalize_member_id(report_id)
        for report in self.reports:
            if report.report_id == wanted:
                return report
        raise KeyError(f"no report in the voice book: {wanted!r}")

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "character_voice_book",
            "slice": CHARACTER_VOICES_SLICE,
            "title": self.title,
            "member_ids": list(self.member_ids()),
            "profile_count": len(self.profiles),
            "report_count": len(self.reports),
        }


def validate_book(data: Any, *, require_example: bool = False) -> VoiceBook:
    """Validate one voices mapping into a VoiceBook.

    The mapping names a ``schema`` (the voices
    schema word), a ``guide`` mapping (its
    ``title``), a ``profiles`` list and an
    optional ``reports`` list. Every profile is
    validated, then the whole is judged: one
    voice per member, profile ids unique, and
    every report judged against its teller's
    profile. With ``require_example`` the shipped
    example is held to its pinned shape: the
    pinned title, the pinned member in each of
    the four registers, and the pinned example
    report carrying its pinned facts
    byte-for-byte under its teller's flavour.
    Problems raise :class:`ValidationError` or
    ``ValueError`` naming the problem.
    """
    if isinstance(data, VoiceBook):
        return data
    if not isinstance(data, dict):
        raise ValidationError(f"a voice book must be a mapping, got {data!r}")
    unknown = set(data) - _VOICES_KEYS
    if unknown:
        raise ValidationError(
            "unknown voices keys: %s" % ", ".join(sorted(unknown)))
    if data.get("schema") != CHARACTER_VOICES_SCHEMA:
        raise ValidationError(
            f"a voice book must carry schema {CHARACTER_VOICES_SCHEMA!r}, "
            f"got {data.get('schema')!r}")
    if "profiles" not in data:
        raise ValidationError("a voice book is missing its profiles")
    raw = data["profiles"]
    if not isinstance(raw, (list, tuple)):
        raise ValidationError("a voice book's profiles must be a list")
    raw_reports = data.get("reports") or []
    if not isinstance(raw_reports, (list, tuple)):
        raise ValidationError("a voice book's reports must be a list")
    head = data.get("guide") or {}
    if not isinstance(head, dict):
        raise ValidationError("a voice book's guide must be a mapping")
    unknown_head = set(head) - _BOOK_KEYS
    if unknown_head:
        raise ValidationError(
            "unknown guide keys: %s" % ", ".join(sorted(unknown_head)))
    try:
        title = _pick_any(head, ("title", "name"), "titles")
        if title is None:
            raise ValidationError("a voice book is missing its title")
        profiles = tuple(validate_profile(p) for p in raw)
        note = data.get("voices_note") or ""
        if not isinstance(note, str):
            raise ValidationError("a voice book's note must be text")
        book = VoiceBook(
            title=title, profiles=profiles, reports=tuple(raw_reports),
            voices_note=note)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    if require_example:
        if book.title != _EXAMPLE_TITLE:
            raise ValidationError(
                "the shipped example voice book's title is not "
                "the pinned title")
        for register in VOICE_REGISTERS:
            ids = tuple(p.member for p in book.profiles_for(register))
            if ids != _EXAMPLE_REGISTERS[register]:
                raise ValidationError(
                    f"the shipped example voice book's {register} "
                    "register is not the pinned shape")
        report = book.report_for(_EXAMPLE_REPORT_ID)
        if report.facts != _EXAMPLE_REPORT_FACTS:
            raise ValidationError(
                "the shipped example report does not carry its "
                "pinned facts byte-for-byte")
        rendered = render_report(
            book.profile_for(report.member), report.facts,
            title=report.title, report_id=report.report_id)
        if rendered != report:
            raise ValidationError(
                "the shipped example report is not the rendering "
                "of its teller's profile over its facts")
    return book


def build_book(book: Any = None, **kwargs: Any) -> VoiceBook:
    """Build one validated book, from a mapping or field words."""
    if isinstance(book, VoiceBook) and not kwargs:
        return book
    if isinstance(book, (list, tuple)) and not kwargs:
        raise ValueError("a book needs its title")
    if isinstance(book, dict):
        if "profiles" in book or "schema" in book:
            return validate_book(book)
        merged: Dict[str, Any] = dict(book)
        merged.update(kwargs)
        return VoiceBook(**merged)
    if book is None:
        return VoiceBook(**kwargs)
    raise ValueError(f"a voice book is needed, got {book!r}")


def _book_from(data: Any, *, require_example: bool) -> VoiceBook:
    try:
        return validate_book(data, require_example=require_example)
    except ValidationError:
        raise
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def load_character_voices(data: Optional[Dict[str, Any]] = None) -> VoiceBook:
    """Load and validate the shipped example voice book (or *data*).

    The shipped file is held to the example check:
    the pinned title, the pinned member in each
    of the four registers, and the pinned example
    report - the skald's telling of the
    crew-sizing result, its facts carried
    byte-for-byte under the skald's warm framing -
    so the shipped book covers the boundary this
    slice exists to hold.
    """
    raw = data if data is not None else load_resource(
        CHARACTER_VOICES_RESOURCE)
    return _book_from(raw, require_example=True)


def load_character_voices_file(path: Any) -> VoiceBook:
    """Load and validate a voice book from a file at *path*.

    Any file in the voices shape, anywhere on
    disk, validated whole - a malformed file
    raises :class:`ValidationError` naming the
    problem, and a missing file raises
    ``FileNotFoundError``. The example check is
    not held: a real voice book stands on its own
    voices.
    """
    from ..data.data_loader import RobustDataLoader
    raw = RobustDataLoader.load_yaml(Path(path), strict=True)
    return _book_from(raw, require_example=False)


# ---------------------------------------------------------------------
# The registry model: one book held voice by voice, in order.
# ---------------------------------------------------------------------


class VoiceRegistry:
    """One session's voice book, held profile by profile.

    The registry holds voices, never reports: a
    report is a rendering, derived at call time
    from a held profile and the facts it is
    given, so nothing here can hold a fact or a
    flavour stale.
    """

    def __init__(self, book: Any = None) -> None:
        self._title: Optional[str] = None
        self._profiles: Dict[str, VoiceProfile] = {}
        self._order: list = []
        self._next_voice = 1
        if book is not None:
            self.register_book(book)

    def _fresh_profile_id(self, held_ids: Any) -> str:
        while f"voice-{self._next_voice}" in held_ids:
            self._next_voice += 1
        fresh = f"voice-{self._next_voice}"
        self._next_voice += 1
        return fresh

    def register_profile(self, profile: Any) -> VoiceProfile:
        """Register one voice into the held book.

        A profile with no id is given a
        deterministic ``voice-N`` id. A second
        voice for a member already holding one
        refuses, as does a profile id already
        standing here.
        """
        validated = build_profile(profile)
        if validated.member in self._profiles:
            raise ValueError(
                f"a voice for {validated.member!r} already exists")
        held_ids = {
            p.profile_id for p in self._profiles.values() if p.profile_id}
        if validated.profile_id is not None \
                and validated.profile_id in held_ids:
            raise ValueError(
                f"a profile named {validated.profile_id!r} "
                "already exists")
        if validated.profile_id is None:
            validated = replace(
                validated,
                profile_id=self._fresh_profile_id(held_ids))
        self._profiles[validated.member] = validated
        self._order.append(validated.member)
        return validated

    def register_book(self, book: Any) -> VoiceBook:
        """Register every voice of one book, in order.

        The first book held sets the title; a
        later book under a different title
        refuses, as does a book holding a voice
        for a member already standing here. The
        book's reports are renderings, not
        holdings, and are not held.
        """
        validated = build_book(book)
        if self._title is not None and validated.title != self._title:
            raise ValueError(
                "this registry already holds a voice book under "
                "a different title")
        for profile in validated.profiles:
            if profile.member in self._profiles:
                raise ValueError(
                    f"a voice for {profile.member!r} already exists")
        self._title = validated.title
        for profile in validated.profiles:
            self.register_profile(profile)
        return self.book()

    def get_profile(self, member: Any) -> VoiceProfile:
        """The voice one member holds among the held voices."""
        wanted = normalize_member_id(member)
        if wanted not in self._profiles:
            raise KeyError(f"unknown member: {wanted!r}")
        return self._profiles[wanted]

    def list_profiles(self) -> Tuple[VoiceProfile, ...]:
        """Every held voice, in the order they were held."""
        return tuple(self._profiles[m] for m in self._order)

    def profiles_for(self, register: Any) -> Tuple[VoiceProfile, ...]:
        """Every held voice in one register, in held order."""
        wanted = normalize_register(register)
        return tuple(
            p for p in self.list_profiles() if p.register == wanted)

    def book(self) -> VoiceBook:
        """The held voices as one validated voice book."""
        if self._title is None:
            raise ValueError("no voice book is held yet")
        return VoiceBook(
            title=self._title, profiles=self.list_profiles())

    def render_report(self, member: Any, facts: Any, title: Any = "",
                      report_id: Any = None) -> VoicedReport:
        """Render one report in a held member's voice.

        The facts are carried verbatim and the
        flavour is the held profile's, at call
        time - the registry holds voices, and
        this rendering is derived from them.
        """
        return render_report(
            self.get_profile(member), facts, title=title,
            report_id=report_id)


# ---------------------------------------------------------------------
# Voice news, shaped as session records.
# ---------------------------------------------------------------------


def profile_record(profile: Any) -> Dict[str, Any]:
    """The session-news record of one voice profile."""
    current = profile if isinstance(profile, VoiceProfile) \
        else build_profile(profile)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.member} speaks in {current.voice_name} "
        f"({current.register}): {current.greeting}")
    return record


def book_record(book: Any) -> Dict[str, Any]:
    """The session-news record of one voice book."""
    current = book if isinstance(book, VoiceBook) else build_book(book)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"Voice book {current.title}: {record['profile_count']} "
        f"voice(s) stand cast.")
    return record


def report_record(report: Any, profile: Any = None,
                    facts: Any = None) -> Dict[str, Any]:
    """The session-news record of one report.

    With *profile* or *facts* given, the report
    is first judged against its teller's profile
    or its source facts. The record holds the
    facts and the flavour in separate fields,
    exactly as the report does.
    """
    current = validate_report(report, profile, facts)
    record = current.to_record()
    record["news"] = True
    record["headline"] = (
        f"{current.title}, told by {current.member} in their "
        f"own voice: {len(current.facts)} fact(s) carried whole.")
    return record


def plain_words(profile: Any) -> str:
    """One voice, in one plain sentence."""
    current = profile if isinstance(profile, VoiceProfile) \
        else build_profile(profile)
    return (
        f"{current.member} - {current.voice_name} "
        f"({current.register}): {'; '.join(current.markers)}")


def report_plain_words(source: Any) -> str:
    """Reports in plain words: every report, in full.

    Accepts a VoicedReport or a VoiceBook. Each
    report is told whole - its teller's flavour
    around its facts, the facts themselves
    verbatim - so nothing is hidden and nothing
    is invented.
    """
    if isinstance(source, VoicedReport):
        reports = (source,)
        title = None
    elif isinstance(source, VoiceBook):
        reports = source.reports
        title = source.title
    else:
        raise ValueError(f"a voices source is needed, got {source!r}")
    lines = []
    if title is not None:
        lines.append(title)
    for report in reports:
        lines.append(
            f"{report.title} - told by {report.member}")
        lines.append(report.rendered_text())
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Screens: the formatters and the shared /voices grammar.
# ---------------------------------------------------------------------


def _source_book(source: Any) -> VoiceBook:
    if source is None:
        return load_character_voices()
    if isinstance(source, VoiceRegistry):
        return source.book()
    if isinstance(source, VoiceBook):
        return source
    raise ValueError(f"a voice book is needed, got {source!r}")


def format_profile(profile: Any) -> str:
    """One voice as a screen line, with its register."""
    current = profile if isinstance(profile, VoiceProfile) \
        else build_profile(profile)
    return (
        f"{current.member} / {current.profile_id or '-'} "
        f"[{current.register}]: {current.voice_name} - "
        f"{'; '.join(current.markers)}")


def format_profiles(source: Any = None, register: Any = None) -> str:
    """Voices of one book, in book order.

    With *register* given, only the voices
    standing in that register are shown.
    """
    book = _source_book(source)
    profiles = book.profiles if register is None \
        else book.profiles_for(register)
    lines = [format_profile(profile) for profile in profiles]
    if not lines:
        lines.append("No voices stand cast.")
    return "\n".join(lines)


def format_report(source: Any = None) -> str:
    """Reports as screen blocks: flavour around verbatim facts.

    Accepts a VoicedReport or a VoiceBook; a book
    shows every report it holds, in book order.
    """
    if isinstance(source, VoicedReport):
        reports = (source,)
        lines: list = []
    else:
        book = _source_book(source)
        reports = book.reports
        lines = [f"Reports in {book.title}:"]
    for report in reports:
        lines.append(
            f"{report.title} - told by {report.member}")
        lines.append(report.rendered_text())
    if isinstance(source, VoicedReport):
        return "\n".join(lines)
    if len(lines) == 1:
        lines.append("Nothing here.")
    return "\n".join(lines)


def format_registers() -> str:
    """The four voice registers, in order, as one line."""
    return "Voice registers: " + ", ".join(VOICE_REGISTERS)


def format_character_voices_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /voices.

    With nothing named, the shipped example voice
    book is shown - the example this slice ships -
    so the screen is never empty.
    """
    book = _source_book(source)
    lines = ["Agent character voices (M-136) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_profiles(book))
    lines.append("")
    lines.append(format_report(book))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_voice_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /voices grammar both surfaces share.

    No words (or ``show`` / ``list``) shows the
    voice book; ``profile <member-id>`` shows one
    member's voice; ``report <report-id>`` shows
    one report; a register word (``plain`` /
    ``warm`` / ``wry`` / ``grim``) shows that
    register's voices; ``registers`` lists the
    four registers. Anything else is a usage
    error naming the grammar. Returns
    ``(action, value-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("show", "list"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head == "registers" and len(words) == 1:
        return ("registers", None)
    if head in ("profile", "report") and len(words) == 2:
        try:
            return (head, normalize_member_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if len(words) == 1:
        try:
            return ("register", normalize_register(words[0]))
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
