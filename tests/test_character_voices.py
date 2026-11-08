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

# -- agent layer -----------------------------------------------------------
#
# M-136 agent layer: the agent holds a
# VoiceRegistry for the session (session state
# only, no new setting), voices are held by being
# registered - published as their profile_record
# session news through the checkpoint road, deduped
# per member - reports are rendered in a member's
# voice and published as ONE character_voice_report
# session event, deduped per whole report shape,
# and the /voices surface rides both roads on the
# pure parser + formatters. Status, get, report and
# book reads register and publish nothing, answer
# from the held registry first and from the shipped
# example only while nothing is held - a held
# session never falls back to the example. This
# layer generates nothing live, persists nothing,
# calls no model and claims no board - Part VIII
# does not exist yet, so the screen is where the
# voices are visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _voice_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


class TestCharacterVoicesAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.character_voices_status()
        assert status["profiles"] == []
        assert status["book"] is None
        assert status["voices"]["title"] == (
            "Character voices at the M-135 slice boundary")
        assert [p["member"] for p in status["voices"]["profiles"]] == [
            "auditor", "skald", "scribe", "guardian"]
        assert [p["register"] for p in status["voices"]["profiles"]] == [
            "plain", "warm", "wry", "grim"]
        assert status["book_record"]["type"] == "character_voice_book"
        assert status["book_record"]["profile_count"] == 4
        assert [r["report_id"] for r in status["reports"]] == [
            "sizing-told-at-the-fire"]
        assert status["reports"][0]["facts"][0] == (
            "The sizing book held four task shapes at the "
            "M-134 slice boundary.")
        assert "Come and hear how it went:" in status["plain_words"]
        assert "Agent character voices (M-136)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert agent._character_voices_registry() is \
            agent._character_voices_registry()
        assert agent._character_voices_store is \
            agent._character_voices_registry()

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.character_voices_status()
        profile = agent.get_voice_profile("skald")
        assert profile.voice_name == "The Hearth Voice"
        assert profile.register == "warm"
        report = agent.voice_report("sizing-told-at-the-fire")
        assert report.member == "skald"
        assert report.facts[2] == (
            "The wide census sweep derived six pairs of "
            "hands, the honest crew's cap.")
        assert agent.character_voices().title == (
            "Character voices at the M-135 slice boundary")
        registry = agent._character_voices_registry()
        assert registry.list_profiles() == ()
        for kind in ("character_voice_profile",
                     "character_voice_report"):
            assert _voice_events(store, session_id, kind) == []
        agent.close()

    def test_unheld_get_raises_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.get_voice_profile("no-such-member")
        with pytest.raises(KeyError):
            agent.voice_report("no-such-report")

    def test_status_after_register_shows_the_held_pieces(self, agent):
        agent.register_voice_profile(_profile())
        status = agent.character_voices_status()
        assert [p["member"] for p in status["profiles"]] == ["auditor"]
        assert status["book"]["profile_count"] == 1
        # The held book answers now, not the example:
        # the session voices are the held voice alone.
        assert [p["member"] for p in status["voices"]["profiles"]] == [
            "auditor"]
        assert status["voices"]["title"] == "Session voice book"
        assert "The Plain Ledger" in status["screen"]

    def test_held_session_never_falls_back_to_the_example(self, agent):
        agent.register_voice_profile(_profile())
        with pytest.raises(KeyError):
            agent.get_voice_profile("skald")
        with pytest.raises(KeyError):
            agent.voice_report("sizing-told-at-the-fire")
        assert agent.character_voices().member_ids() == ("auditor",)
        assert agent.get_voice_profile("auditor").voice_name == (
            "The Plain Ledger")

class TestCharacterVoicesAgentRegister:
    def test_register_profile_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_voice_profile(_profile())
        assert outcome["profile"]["member"] == "auditor"
        assert outcome["record"]["type"] == "character_voice_profile"
        events = _voice_events(store, session_id, "character_voice_profile")
        assert len(events) == 1
        assert events[0]["member"] == "auditor"
        # The same record is never published twice.
        agent._publish_character_voices_record(outcome["record"])
        assert len(_voice_events(
            store, session_id, "character_voice_profile")) == 1
        # Foreign record types are refused on this road.
        from mythic_agent.core.crew_members import (
            casting_record,
            load_casting,
        )
        from mythic_agent.core.crew_memory import (
            entry_record as _memory_entry_record,
            load_crew_memory,
        )
        from mythic_agent.core.crew_sizing import (
            case_record as _sizing_case_record,
            load_crew_sizing,
        )
        from mythic_agent.core.review_panels import (
            load_review_panel,
            review_record,
        )
        from mythic_agent.core.stand_ups import (
            entry_record as _stand_up_entry_record,
            load_stand_up,
        )
        agent._publish_character_voices_record(_sizing_case_record(
            load_crew_sizing().cases[0]))
        agent._publish_character_voices_record({
            "type": "crew_sizing_recommendation_set"})
        agent._publish_character_voices_record(_stand_up_entry_record(
            load_stand_up().entries[0]))
        memory = load_crew_memory()
        agent._publish_character_voices_record(_memory_entry_record(
            memory.entry_for("broken-checkpoint-chain")))
        panel = load_review_panel()
        agent._publish_character_voices_record(review_record(
            panel.reviews[0]))
        agent._publish_character_voices_record(casting_record(
            load_casting().members[0]))
        for kind in ("crew_sizing_case",
                     "crew_sizing_recommendation_set", "stand_up_entry",
                     "crew_memory_entry", "panel_review", "crew_member"):
            assert _voice_events(store, session_id, kind) == []
        assert len(_voice_events(
            store, session_id, "character_voice_profile")) == 1
        agent.close()

    def test_duplicate_member_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_voice_profile(_profile())
        with pytest.raises(ValueError):
            agent.register_voice_profile(_profile(
                profile_id="voice-other", voice_name="Another Voice"))
        assert len(_voice_events(
            store, session_id, "character_voice_profile")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_voice_book()
        assert outcome["count"] == 4
        assert outcome["book"]["profile_count"] == 4
        events = _voice_events(store, session_id, "character_voice_profile")
        assert [e["member"] for e in events] == [
            "auditor", "skald", "scribe", "guardian"]
        assert agent.character_voices().title == (
            "Character voices at the M-135 slice boundary")
        assert agent.get_voice_profile(
            "guardian").voice_name == "The Watch Voice"
        # The recorded book stands whole: its example
        # report still answers on the report road.
        assert agent.voice_report(
            "sizing-told-at-the-fire").member == "skald"
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_voice_book()
        with pytest.raises(ValueError):
            agent.record_voice_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_voices(tmp_path, _book_data())
        book = load_character_voices_file(path)
        outcome = agent.record_voice_book(book)
        assert outcome["count"] == 4
        assert agent.get_voice_profile(
            "scribe").voice_name == "The Dry Quill"
        assert agent.voice_report("night-count").facts == _FACTS

    def test_one_by_one_voices_stand_under_a_session_book(
            self, agent):
        agent.register_voice_profile(_profile(
            profile_id="voice-cartographer", member="cartographer",
            voice_name="The Map Voice", markers=["as mapped"],
            greeting="The map:", sign_off="Mapped."))
        # Held one by one, the voices stand under a
        # session voice book composed in the agent
        # layer - never under a recorded book's title.
        assert agent.character_voices().title == "Session voice book"
        # A later whole book under its own title is
        # never refused by the shim title.
        book = build_book(_book_data_mapped())
        outcome = agent.record_voice_book(book)
        assert outcome["count"] == 4
        assert agent.character_voices().title == "A voice book"


def _book_data_mapped():
    data = _book_data()
    data["schema"] = CHARACTER_VOICES_SCHEMA
    return {
        "schema": data["schema"], "slice": CHARACTER_VOICES_SLICE,
        "guide": data["guide"], "profiles": data["profiles"],
        "reports": data["reports"]}

class TestCharacterVoicesAgentReport:
    def test_report_publishes_one_event_with_facts_verbatim(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.report_character_voices(
            "skald", list(_FACTS), "A short count")
        assert outcome["record"]["type"] == "character_voice_report"
        # The facts published are the facts given,
        # byte for byte, in their own field.
        assert outcome["record"]["facts"] == list(_FACTS)
        assert outcome["record"]["flavour_open"] == (
            "Come and hear how it went:")
        assert outcome["record"]["flavour_close"] == (
            "And the fire keeps the tale.")
        assert outcome["report"]["facts"] == list(_FACTS)
        events = _voice_events(store, session_id, "character_voice_report")
        # ONE event holds the whole report.
        assert len(events) == 1
        assert events[0]["facts"] == list(_FACTS)
        assert events[0]["member"] == "skald"
        # Reporting the same report again publishes
        # nothing new.
        agent.report_character_voices("skald", list(_FACTS), "A short count")
        assert len(_voice_events(
            store, session_id, "character_voice_report")) == 1
        agent.close()

    def test_changed_report_announces_again(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_character_voices("skald", list(_FACTS), "A short count")
        assert len(_voice_events(
            store, session_id, "character_voice_report")) == 1
        # A changed report is a new report shape: it
        # announces again as the new report it is.
        agent.report_character_voices(
            "skald", ["The count stood at five."], "A short count")
        events = _voice_events(store, session_id, "character_voice_report")
        assert len(events) == 2
        assert events[1]["facts"] == ["The count stood at five."]
        agent.close()

    def test_report_in_a_held_voice_and_marker_fact_refuses(
            self, agent):
        agent.register_voice_profile(_profile(
            profile_id="voice-skald", member="skald",
            voice_name="The Hearth Voice", register="warm",
            markers=["by the fire"], greeting="Hear this:",
            sign_off="The fire keeps it."))
        outcome = agent.report_character_voices(
            "skald", ["A plain fact."], "One fact")
        assert outcome["report"]["flavour_open"] == "Hear this:"
        # A held session answers for its own book
        # alone: the example's auditor is not held.
        with pytest.raises(KeyError):
            agent.report_character_voices(
                "auditor", ["A plain fact."], "One fact")
        # A fact carrying the teller's marker refuses
        # at the agent layer too.
        with pytest.raises(ValueError):
            agent.report_character_voices(
                "skald", ["Told by the fire tonight."], "One fact")

    def test_no_generate_persist_or_model_road(self, agent):
        # This layer holds the voices as data: it
        # generates nothing live, persists nothing and
        # calls no model - and there is no Part VIII
        # board yet.
        assert not hasattr(agent, "generate_voice_report")
        assert not hasattr(agent, "render_voice_live")
        assert not hasattr(agent, "persist_character_voices")
        assert not hasattr(agent, "character_voices_board")

class TestCharacterVoicesTerminalSurface:
    def test_show_profile_report_register_and_registers(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/voices")
        assert "Agent character voices (M-136)" in text
        _, _, text = _slash(agent, "/voices profile skald")
        assert "The Hearth Voice" in text
        _, _, text = _slash(
            agent, "/voices report sizing-told-at-the-fire")
        assert "Come and hear how it went:" in text
        assert "The wide census sweep derived six pairs of" in text
        _, _, text = _slash(agent, "/voices warm")
        assert "skald" in text
        assert "guardian" not in text
        _, _, text = _slash(agent, "/voices registers")
        assert text == "Voice registers: plain, warm, wry, grim"

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/voices [show|profile <member-id>|report <report-id>|"
                "plain|warm|wry|grim|registers]") in text
        _, _, text = _slash(agent, "/voices dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/voices profile missing-member")
        assert "no voice in the book for member" in text


@pytest.fixture()
def voices_handler(agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY
    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _voices_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCharacterVoicesCommand:
    def test_show_is_default(self, voices_handler, agent):
        voices_handler._handle_voices("")
        assert "Agent character voices (M-136)" in \
            _voices_published_text(voices_handler)

    def test_profile_report_register_and_registers(
            self, voices_handler, agent):
        voices_handler._handle_voices("profile skald")
        assert "The Hearth Voice" in _voices_published_text(voices_handler)
        voices_handler._handle_voices("report sizing-told-at-the-fire")
        assert "Come and hear how it went:" in \
            _voices_published_text(voices_handler)
        voices_handler._handle_voices("warm")
        assert "skald" in _voices_published_text(voices_handler)
        voices_handler._handle_voices("registers")
        assert "Voice registers: plain, warm, wry, grim" in \
            _voices_published_text(voices_handler)

    def test_bad_grammar_is_published(self, voices_handler, agent):
        voices_handler._handle_voices("dance party")
        assert USAGE in _voices_published_text(voices_handler)


class TestChatScreenRoutingVoices:
    def test_voices_routes_as_system_command(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import MainChatScreen

        class _FakeLog:
            def __init__(self):
                self.lines = []

            def write(self, *args, **kwargs):
                self.lines.append(" ".join(str(a) for a in args))

        calls = []
        monkeypatch.setattr(
            chat_screen.SecureAPI, "publish_system_command",
            staticmethod(lambda cmd, args: calls.append((cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        screen.handle_command("/voices registers", _FakeLog())
        assert calls == [("/voices", "registers")]
