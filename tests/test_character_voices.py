"""M-136 Agent character voices - pure-layer tests.

TIER: integration

The pure layer is the house cast's written
voices as data: a voice book of profiles (one
per member - the voice's name, its register,
its signature markers, the greeting that opens
the member's reports and the sign-off that
closes them), the shipped example voice book
held in a data file, a loader that reads a
voice book from any file, report rendering that
carries facts verbatim under the voice's
flavour framing, records shaped as session
news, and a registry. Nothing here calls a
model, generates anything live, or alters any
member's code or facts: flavour lives in the
reporting, never in the facts, and a fact
carrying its teller's marker - or a stored
report disagreeing with its profile or its
source facts - is refused.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.crew_members import load_casting
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.character_voices import (
    CHARACTER_VOICES_RESOURCE,
    CHARACTER_VOICES_SCHEMA,
    CHARACTER_VOICES_SLICE,
    PLAIN_EXPLANATION,
    USAGE,
    VOICE_REGISTERS,
    VoiceBook,
    VoiceProfile,
    VoiceRegistry,
    VoicedReport,
    book_record,
    build_book,
    build_profile,
    build_report,
    format_character_voices_screen,
    format_profile,
    format_profiles,
    format_registers,
    format_report,
    load_character_voices,
    load_character_voices_file,
    normalize_register,
    parse_voice_args,
    plain_words,
    profile_record,
    render_report,
    report_plain_words,
    report_record,
    validate_book,
    validate_profile,
    validate_report,
)

ROOT = Path(__file__).resolve().parents[1]

_FACTS = (
    "The count stood at four.",
    "Nothing moved in the night.",
)


def _profile(**kwargs):
    kwargs.setdefault("profile_id", "voice-auditor")
    kwargs.setdefault("member", "auditor")
    kwargs.setdefault("voice_name", "The Plain Ledger")
    kwargs.setdefault("register", "plain")
    kwargs.setdefault("markers", ["as counted", "no more, no less"])
    kwargs.setdefault("greeting", "The count, as it stands:")
    kwargs.setdefault("sign_off", "That is the whole of it.")
    return VoiceProfile(**kwargs)


def _book_data():
    return {
        "schema": CHARACTER_VOICES_SCHEMA, "slice": CHARACTER_VOICES_SLICE,
        "guide": {"title": "A voice book"},
        "profiles": [
            {"profile_id": "voice-auditor", "member": "auditor",
             "voice_name": "The Plain Ledger", "register": "plain",
             "markers": ["as counted"], "greeting": "The count:",
             "sign_off": "That is all."},
            {"profile_id": "voice-skald", "member": "skald",
             "voice_name": "The Hearth Voice", "register": "warm",
             "markers": ["by the fire"], "greeting": "Hear this:",
             "sign_off": "The fire keeps it."},
            {"profile_id": "voice-scribe", "member": "scribe",
             "voice_name": "The Dry Quill", "register": "wry",
             "markers": ["for the record"], "greeting": "Noted:",
             "sign_off": "Ink dries."},
            {"profile_id": "voice-guardian", "member": "guardian",
             "voice_name": "The Watch Voice", "register": "grim",
             "markers": ["the wall holds"], "greeting": "The watch:",
             "sign_off": "The wall holds."},
        ],
        "reports": [
            {"report_id": "night-count", "member": "auditor",
             "title": "The night count",
             "facts": ["The count stood at four.",
                       "Nothing moved in the night."]},
        ]}


def _write_voices(tmp_path, data):
    path = tmp_path / "voices.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_constants_and_usage():
    assert CHARACTER_VOICES_SLICE == "M-136"
    assert CHARACTER_VOICES_RESOURCE == "character_voices.yaml"
    assert CHARACTER_VOICES_SCHEMA == "mythic.character_voices/1"
    assert VOICE_REGISTERS == ("plain", "warm", "wry", "grim")
    assert USAGE.startswith("Usage: /voices")
    assert "flavour in the reporting" in PLAIN_EXPLANATION
    assert "calls no model" in PLAIN_EXPLANATION


def test_shipped_example_book_shape():
    book = load_character_voices()
    assert book.title == "Character voices at the M-135 slice boundary"
    assert len(book.profiles) == 4
    assert book.member_ids() == ("auditor", "skald", "scribe", "guardian")
    assert [p.member for p in book.profiles_for("plain")] == ["auditor"]
    assert [p.member for p in book.profiles_for("warm")] == ["skald"]
    assert [p.member for p in book.profiles_for("wry")] == ["scribe"]
    assert [p.member for p in book.profiles_for("grim")] == ["guardian"]
    report = book.report_for("sizing-told-at-the-fire")
    assert report.member == "skald"
    assert report.facts == (
        "The sizing book held four task shapes at the "
        "M-134 slice boundary.",
        "The tangled single-file fix derived one pair of "
        "hands, because the work was tightly coupled.",
        "The wide census sweep derived six pairs of "
        "hands, the honest crew's cap.")


def test_example_members_are_the_shipped_casting():
    casting = load_casting()
    ids = [member.member_id for member in casting.members]
    for profile in load_character_voices().profiles:
        assert profile.member in ids


def test_rendering_carries_facts_byte_for_byte():
    book = load_character_voices()
    held = book.report_for("sizing-told-at-the-fire")
    rendered = render_report(
        book.profile_for("skald"), held.facts, title=held.title,
        report_id=held.report_id)
    assert rendered == held
    text = rendered.rendered_text()
    for fact in held.facts:
        assert fact in text
    assert text.startswith("Come and hear how it went:\n")
    assert text.endswith("\nAnd the fire keeps the tale.")
    assert rendered.flavour_open == "Come and hear how it went:"
    assert rendered.flavour_close == "And the fire keeps the tale."


def test_facts_are_verbatim_under_every_voice():
    book = load_character_voices()
    tellings = [
        render_report(profile, _FACTS, title="The night count")
        for profile in book.profiles]
    for telling in tellings:
        assert telling.facts == _FACTS
        for fact in _FACTS:
            assert fact in telling.rendered_text()
    flavours = {(t.flavour_open, t.flavour_close) for t in tellings}
    assert len(flavours) == 4


def test_flavour_never_inside_a_fact_record():
    report = render_report(_profile(), _FACTS, title="The night count")
    record = report.to_record()
    assert record["facts"] == list(_FACTS)
    assert record["flavour_open"] == "The count, as it stands:"
    assert record["flavour_close"] == "That is the whole of it."
    for fact in record["facts"]:
        for marker in ("as counted", "no more, no less"):
            assert marker not in fact


def test_flavour_inside_a_fact_refuses():
    skald = load_character_voices().profile_for("skald")
    with pytest.raises(ValueError):
        render_report(skald, ("It ended, by the fire, at last.",),
                      title="A telling")
    with pytest.raises(ValueError):
        validate_report(
            {"member": "skald", "title": "A telling",
             "facts": ["Hear this: the count stood at four."]}, skald)
    data = _book_data()
    data["reports"] = [{
        "report_id": "bent", "member": "skald", "title": "Bent",
        "facts": ["The tale, by the fire, was long."]}]
    with pytest.raises(ValidationError):
        validate_book(data)


def test_a_profile_holding_facts_refuses():
    with pytest.raises(ValueError):
        validate_profile({
            "member": "auditor", "voice_name": "V",
            "register": "plain", "markers": ["as counted"],
            "greeting": "G:", "sign_off": "S.",
            "facts": ["A fact the voice would own."]})
    data = _book_data()
    data["profiles"][0]["facts"] = ["Owned."]
    with pytest.raises(ValidationError):
        validate_book(data)


def test_stored_report_must_agree_with_profile_and_source():
    profile = _profile()
    stored = {"report_id": "night-count", "member": "auditor",
              "title": "The night count", "facts": list(_FACTS)}
    assert validate_report(stored, profile) == render_report(
        profile, _FACTS, title="The night count",
        report_id="night-count")
    assert build_report(stored, profile) is not None
    bent_flavour = dict(stored, flavour_open="A bent opening:")
    with pytest.raises(ValueError):
        validate_report(bent_flavour, profile)
    bent_fact = dict(stored, facts=[_FACTS[0], "Nothing moved."])
    with pytest.raises(ValueError):
        validate_report(bent_fact, profile, facts=_FACTS)
    rendered = render_report(profile, _FACTS, title="The night count")
    with pytest.raises(ValueError):
        validate_report(rendered, facts=(_FACTS[0], "Nothing moved."))
    assert validate_report(rendered, facts=_FACTS) == rendered
    assert build_report(rendered) is rendered


def test_report_member_must_match_its_profile():
    profile = _profile()
    stored = {"member": "scribe", "title": "The night count",
              "facts": list(_FACTS), "flavour_open": "Noted:",
              "flavour_close": "Ink dries."}
    with pytest.raises(ValueError):
        validate_report(stored, profile)
    with pytest.raises(ValueError):
        validate_report(
            {"member": "auditor", "title": "T", "facts": list(_FACTS)})
    with pytest.raises(ValueError):
        validate_report(
            {"member": "auditor", "title": "T", "facts": list(_FACTS),
             "flavour_open": "G:", "bogus": 1}, profile)


def test_normalize_register_readings_and_refusals():
    assert normalize_register("Plain") == "plain"
    assert normalize_register("flat") == "plain"
    assert normalize_register("Fireside") == "warm"
    assert normalize_register("hearty") == "warm"
    assert normalize_register("DRY") == "wry"
    assert normalize_register("Deadpan") == "wry"
    assert normalize_register("Stern") == "grim"
    assert normalize_register("stark") == "grim"
    with pytest.raises(ValueError):
        normalize_register("cheerful")
    with pytest.raises(ValueError):
        normalize_register("")
    with pytest.raises(ValueError):
        normalize_register(None)


def test_profile_validation_and_two_spellings_refusal():
    profile = validate_profile(
        {"member_id": "guardian", "voice": "The Watch Voice",
         "tone": "Stern", "phrases": ["the wall holds"],
         "opening": "The watch:", "closing": "The wall holds."})
    assert profile.member == "guardian"
    assert profile.voice_name == "The Watch Voice"
    assert profile.register == "grim"
    assert profile.markers == ("the wall holds",)
    with pytest.raises(ValueError):
        validate_profile({"member": "guardian", "member_id": "auditor",
                          "voice_name": "V", "register": "grim",
                          "markers": ["m"], "greeting": "G:",
                          "sign_off": "S."})
    with pytest.raises(ValueError):
        validate_profile({"member": "guardian", "voice_name": "V",
                          "register": "grim", "markers": ["m"],
                          "greeting": "G:", "sign_off": "S.",
                          "bogus": 1})
    with pytest.raises(ValueError):
        validate_profile({"voice_name": "V", "register": "grim",
                          "markers": ["m"], "greeting": "G:",
                          "sign_off": "S."})
    assert build_profile(member="scribe", voice_name="Built",
                         register="wry", markers=["for the record"],
                         greeting="Noted:",
                         sign_off="Ink dries.").member == "scribe"
    assert plain_words(_profile()).startswith(
        "auditor - The Plain Ledger (plain): as counted")


def test_profile_refusals():
    with pytest.raises(ValueError):
        _profile(voice_name="")
    with pytest.raises(ValueError):
        _profile(greeting="  ")
    with pytest.raises(ValueError):
        _profile(sign_off="")
    with pytest.raises(ValueError):
        _profile(member="two words")
    with pytest.raises(ValueError):
        _profile(register="cheerful")
    with pytest.raises(ValueError):
        _profile(markers=[])
    with pytest.raises(ValueError):
        _profile(markers=["as counted", "as counted"])
    with pytest.raises(ValueError):
        _profile(markers="as counted")
    with pytest.raises(ValueError):
        render_report(_profile(), (), title="Empty")
    with pytest.raises(ValueError):
        render_report(_profile(), ("One fact.", ""), title="Blank")
    with pytest.raises(ValueError):
        VoicedReport(member="auditor", title="T", facts=("F.",),
                     flavour_open=3)


def test_book_validation_and_shared_view():
    book = validate_book(_book_data())
    assert book.title == "A voice book"
    assert book.member_ids() == ("auditor", "skald", "scribe", "guardian")
    assert book.profile_for("skald").voice_name == "The Hearth Voice"
    assert [p.member for p in book.profiles_for("wry")] == ["scribe"]
    report = book.report_for("night-count")
    assert report.flavour_open == "The count:"
    assert report.facts == _FACTS
    assert build_book(book) is book
    with pytest.raises(KeyError):
        book.profile_for("missing")
    with pytest.raises(KeyError):
        book.report_for("missing")


def test_book_refusals():
    data = _book_data()
    data["schema"] = "mythic.other/1"
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    data["bogus"] = 1
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    data["profiles"][1]["member"] = "auditor"
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    data["profiles"][1]["profile_id"] = "voice-auditor"
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    data["reports"][0]["member"] = "polymath"
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    del data["profiles"]
    with pytest.raises(ValidationError):
        validate_book(data)
    data = _book_data()
    del data["guide"]["title"]
    with pytest.raises(ValidationError):
        validate_book(data)
    with pytest.raises(ValueError):
        VoiceBook(title="T", profiles=(
            _profile(), _profile(voice_name="Second")))


def test_file_loader_round_trip_and_missing_file(tmp_path):
    path = _write_voices(tmp_path, _book_data())
    book = load_character_voices_file(path)
    assert book.title == "A voice book"
    assert book.profile_for("scribe").register == "wry"
    assert book.report_for("night-count").facts == _FACTS
    with pytest.raises(FileNotFoundError):
        load_character_voices_file(tmp_path / "nope.yaml")


def test_registry_hold_and_rendering():
    registry = VoiceRegistry()
    registry.register_book(validate_book(_book_data()))
    assert registry.get_profile("skald").voice_name == "The Hearth Voice"
    assert [p.member for p in registry.list_profiles()] == [
        "auditor", "skald", "scribe", "guardian"]
    assert [p.member for p in registry.profiles_for("grim")] == [
        "guardian"]
    assert registry.book().title == "A voice book"
    assert registry.book().reports == ()
    report = registry.render_report("guardian", _FACTS,
                                    title="The night count")
    assert report.facts == _FACTS
    assert report.flavour_open == "The watch:"
    assert report.flavour_close == "The wall holds."
    with pytest.raises(KeyError):
        registry.get_profile("missing")
    with pytest.raises(KeyError):
        registry.render_report("missing", _FACTS, title="T")


def test_registry_auto_ids_and_refusals():
    registry = VoiceRegistry(VoiceBook(title="T"))
    first = registry.register_profile(_profile(profile_id=None))
    assert first.profile_id == "voice-1"
    second = registry.register_profile(_profile(
        profile_id=None, member="scribe", voice_name="The Dry Quill",
        register="wry", markers=["for the record"],
        greeting="Noted:", sign_off="Ink dries."))
    assert second.profile_id == "voice-2"
    with pytest.raises(ValueError):
        registry.register_profile(_profile())
    with pytest.raises(ValueError):
        registry.register_book(validate_book(_book_data()))
    with pytest.raises(ValueError):
        VoiceRegistry().book()
    fresh = VoiceRegistry(load_character_voices())
    assert len(fresh.list_profiles()) == 4
    with pytest.raises(ValueError):
        fresh.register_book(load_character_voices())


def test_records_are_session_news():
    profile = profile_record(_profile())
    assert profile["type"] == "character_voice_profile"
    assert profile["slice"] == "M-136"
    assert profile["news"] is True
    assert "auditor" in profile["headline"]
    book = book_record(load_character_voices())
    assert book["type"] == "character_voice_book"
    assert book["profile_count"] == 4
    assert book["report_count"] == 1
    report = report_record(render_report(_profile(), _FACTS,
                                         title="The night count"))
    assert report["type"] == "character_voice_report"
    assert report["facts"] == list(_FACTS)
    assert "2 fact(s) carried whole" in report["headline"]
    with pytest.raises(ValueError):
        report_record({"member": "auditor", "title": "T",
                       "facts": [_FACTS[0], "Bent."]},
                      _profile(), facts=_FACTS)


def test_report_plain_words_cover_the_example():
    words = report_plain_words(load_character_voices())
    assert "Character voices at the M-135 slice boundary" in words
    assert "The sizing of four tasks, told warm" in words
    assert "Come and hear how it went:" in words
    for fact in (
            "The sizing book held four task shapes at the "
            "M-134 slice boundary.",
            "The wide census sweep derived six pairs of "
            "hands, the honest crew's cap."):
        assert fact in words
    assert "And the fire keeps the tale." in words
    single = report_plain_words(
        render_report(_profile(), _FACTS, title="The night count"))
    assert "The count, as it stands:" in single
    assert _FACTS[0] in single
    assert report_plain_words(VoiceBook(title="T")) == "T"
    with pytest.raises(ValueError):
        report_plain_words(42)


def test_formatters_and_screen():
    book = load_character_voices()
    assert "auditor / voice-auditor [plain]" in format_profile(
        book.profile_for("auditor"))
    assert "guardian" in format_profiles(book)
    assert "guardian" not in format_profiles(book, "warm")
    assert "skald" in format_profiles(book, "warm")
    report_text = format_report(book)
    assert "Reports in Character voices at the " in report_text
    assert "Come and hear how it went:" in report_text
    assert "The wide census sweep derived six pairs of" in report_text
    single = format_report(book.report_for("sizing-told-at-the-fire"))
    assert single.startswith("The sizing of four tasks, told warm")
    assert format_registers() == (
        "Voice registers: plain, warm, wry, grim")
    screen = format_character_voices_screen(book)
    assert "Agent character voices (M-136)" in screen
    assert USAGE in screen
    assert format_profiles(VoiceBook(
        title="T")) == "No voices stand cast."


def test_parse_voice_args_grammar():
    assert parse_voice_args("") == ("show", None)
    assert parse_voice_args("show") == ("show", None)
    assert parse_voice_args("list") == ("show", None)
    assert parse_voice_args("profile skald") == ("profile", "skald")
    assert parse_voice_args("report sizing-told-at-the-fire") == (
        "report", "sizing-told-at-the-fire")
    assert parse_voice_args("warm") == ("register", "warm")
    assert parse_voice_args("Stern") == ("register", "grim")
    assert parse_voice_args("registers") == ("registers", None)
    with pytest.raises(ValueError):
        parse_voice_args("profile")
    with pytest.raises(ValueError):
        parse_voice_args("bogus words here")
    with pytest.raises(ValueError):
        parse_voice_args(42)


def test_no_live_roads_in_pure_layer():
    import mythic_agent.core.character_voices as module
    source = Path(module.__file__).read_text(encoding="utf-8")
    for banned in ("import subprocess", "requests.", "openai",
                   "anthropic", "AgentManager", "mythic_agent.agents",
                   "mythic_agent.ui", "def spawn", "def persist",
                   "def schedule", "def generate"):
        assert banned not in source
    record = render_report(_profile(), _FACTS, title="T").to_record()
    assert "generated" not in record
    assert record["facts"] == list(_FACTS)
