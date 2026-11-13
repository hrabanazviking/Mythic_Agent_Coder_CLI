"""M-180 Voice In and Out - pure-layer tests.

TIER: integration

The pure layer is voice, held as data: a
push-to-talk dictation session held whole (its
state - recording, landed or drafted - its
transcript, and the capture and transcriber
backends it names), a spoken stand-up held whole
(its speaker, its text, the catalog voice cast
for it and the TTS backend it names), and a
voice action held whole (its spoken phrase and
the text equivalent that stands beside it).
Availability is derived from the backends and
voices a record names - available, unavailable
by a named reason, or honestly unknown - never
stored and never faked. A dictation's
transcript lands as a prompt draft and is never
auto-sent. Every voice action has a text
equivalent: a voice-only action refuses by
name, because voice is an extra door, never the
only door. The panel is derived for one held
view and the verdict is derived for the whole
book under one view. The shipped example book
is held in a data file, and a loader reads a
book from any file. No row of the M-171 charter
names M-180, so the slice is built to the
roadmap words alone, as M-177 and M-179 were.
Live roads stand behind seams a test can fake:
nothing here captures live audio, needs a
microphone or PortAudio, builds a TTS engine,
clones a voice or sends a prompt.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.voice_in_out import (
    AVAILABILITY_WORDS,
    BACKEND_UNKNOWN,
    EVERY_VOICE_ACTION_HAS_A_TEXT_EQUIVALENT,
    ITEM_KINDS,
    PLAIN_EXPLANATION,
    STATES,
    USAGE,
    VERDICT_WORDS,
    VIEW_KINDS,
    VOICE_IN_OUT_RESOURCE,
    VOICE_IN_OUT_SCHEMA,
    VOICE_IN_OUT_SLICE,
    DictationSession,
    SpeechRender,
    SpokenStandup,
    VoiceAction,
    VoiceBook,
    VoicePanel,
    VoiceRegistry,
    VoiceVerdict,
    VoiceView,
    action_plain_words,
    action_record,
    availability_of,
    book_record,
    build_action,
    build_book,
    build_dictation,
    build_panel,
    build_row,
    build_standup,
    build_verdict,
    build_view,
    derive_panel,
    derive_verdict,
    dictation_availability,
    dictation_passes,
    dictation_record,
    draft_dictation,
    draft_text_of,
    format_action,
    format_book,
    format_dictation,
    format_panel,
    format_standup,
    format_verdict,
    format_view,
    format_voice_in_out_screen,
    inspect_item_source,
    item_passes,
    items_for_kind,
    load_voice_in_out,
    load_voice_in_out_file,
    normalize_kind,
    normalize_kind_filter,
    normalize_state,
    panel_plain_words,
    panel_record,
    parse_voice_in_out_args,
    passing_items,
    plain_words,
    segment_of,
    shown_items,
    speak_standup,
    standup_availability,
    standup_passes,
    standup_plain_words,
    standup_record,
    start_dictation,
    stop_dictation,
    total_items,
    transcribe_dictation,
    validate_action,
    validate_dictation,
    validate_panel,
    validate_standup,
    validate_verdict,
    validate_view,
    verdict_plain_words,
    verdict_record,
    view_plain_words,
    view_record,
)
from mythic_agent.core.prompt_craft import ITEM_KINDS as PROMPT_KINDS
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Voice at the M-179 slice boundary"

BY = "the coordinator"
ON = "2026-11-09"


def _dictation(**overrides):
    fields = {
        "dictation_id": "dictation-test",
        "seq": 1,
        "state": "drafted",
        "transcript": "Fix the parser tests first.",
        "capture_backend": "existing_audio",
        "transcriber_backend": "existing_whisper",
        "detail": "A dictation session held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_dictation(fields)


def _stored_dictation(session):
    stored = session.to_record()
    for key in ("type", "slice", "availability",
                "availability_reason", "draft_text", "sent",
                "passes", "segment"):
        stored.pop(key)
    return stored


def _standup(**overrides):
    fields = {
        "standup_id": "standup-test",
        "seq": 1,
        "speaker": "Primary",
        "text": "The parser tests stand next, for the tests.",
        "voice_name": "en_US-lessac-high",
        "tts_backend": "existing_tts",
        "detail": "A spoken stand-up held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_standup(fields)


def _stored_standup(standup):
    stored = standup.to_record()
    for key in ("type", "slice", "availability",
                "availability_reason", "passes", "segment"):
        stored.pop(key)
    return stored


def _action(**overrides):
    fields = {
        "action_id": "action-test",
        "seq": 1,
        "name": "test_action",
        "voice_phrase": "test the thing",
        "text_equivalent": "type the test command",
        "detail": "A voice action held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_action(fields)


def _stored_action(action):
    stored = action.to_record()
    for key in ("type", "slice", "passes", "segment"):
        stored.pop(key)
    return stored


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "kind_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    stored = view.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    return stored


def _book(dictations=None, standups=None, actions=None,
          views=(), **overrides):
    fields = {
        "title": "A test voice book",
        "dictations": [_stored_dictation(item) for item in (
            dictations if dictations is not None else [_dictation()])],
        "standups": [_stored_standup(item) for item in (
            standups if standups is not None else [_standup()])],
        "actions": [_stored_action(item) for item in (
            actions if actions is not None else [_action()])],
        "views": [_stored_view(item) for item in views],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(
        dictations=[
            _dictation(),
            _dictation(
                dictation_id="dictation-held", seq=2,
                state="recording", transcript="",
                transcriber_backend="unknown"),
        ],
        standups=[
            _standup(),
            _standup(
                standup_id="standup-unspoken", seq=2,
                voice_name=None),
        ],
        actions=[_action()],
        views=[_view()])


# ---------------------------------------------------------------------
# The shipped example book, the roadmap and the charter.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_voice_in_out()
    assert book.title == EXAMPLE_TITLE
    assert book.dictation_ids() == (
        "dictation-morning-prompt", "dictation-evening-note")
    assert book.standup_ids() == (
        "standup-morning", "standup-evening")
    assert book.action_ids() == (
        "action-dictate-prompt", "action-speak-standup",
        "action-mute-speech")
    assert book.view_ids() == ("view-all", "view-dictation")
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m179-boundary"
    assert panel.as_of == "2026-11-09"
    assert [row.item_id for row in panel.rows] == [
        "dictation-morning-prompt", "dictation-evening-note",
        "standup-morning", "standup-evening",
        "action-dictate-prompt", "action-speak-standup",
        "action-mute-speech"]
    derived = derive_panel(book, "view-all")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 7
    assert panel.total_shown == derived.total_shown == 7
    assert {c.kind: c.items for c in panel.kind_counts} == {
        "dictation": 2, "standup": 2, "action": 3}
    assert derive_verdict(book, "view-all").verdict == "strained"
    assert derive_verdict(book, "view-dictation").verdict == (
        "strained")
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / VOICE_IN_OUT_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == VOICE_IN_OUT_SCHEMA
    assert raw["slice"] == "M-180"
    assert "verdict" not in raw
    assert "segment" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-180")]
    assert slice_.title == "Voice in and out"
    assert slice_.part == 8
    assert "push-to-talk dictation" in slice_.summary
    assert "spoken stand-ups via the existing TTS" in slice_.summary
    assert "direct catalog casting" in slice_.summary
    assert "never the only door" in slice_.summary
    assert VOICE_IN_OUT_SLICE == "M-180"


def test_charter_names_no_row_for_m180():
    # No M-171 charter row names M-180 as an owning
    # slice, so the slice is built to the roadmap
    # words alone, as M-177 and M-179 were - proven
    # live against every charter row.
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-180" not in owners


def test_closed_vocabularies():
    assert ITEM_KINDS == ("dictation", "standup", "action")
    assert VIEW_KINDS == ("all",) + ITEM_KINDS
    assert STATES == ("recording", "landed", "drafted")
    assert AVAILABILITY_WORDS == (
        "available", "unavailable", "unknown")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert BACKEND_UNKNOWN == "unknown"
    assert EVERY_VOICE_ACTION_HAS_A_TEXT_EQUIVALENT is True
    assert normalize_kind("PTT") == "dictation"
    assert normalize_kind("stand-up") == "standup"
    assert normalize_kind_filter("ALL") == "all"
    assert normalize_kind_filter("spoken") == "standup"
    assert normalize_state("stopped") == "landed"
    with pytest.raises(ValueError):
        normalize_kind("whenever")
    with pytest.raises(ValueError):
        normalize_state("sent")
    assert "never the only door" in PLAIN_EXPLANATION
    assert "never auto-sent" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /voiceinout")


def test_prompt_craft_kind_set_stays_closed_without_dictation():
    # M-177's pinned behaviour stands untouched:
    # its kind set is closed without dictation,
    # and dictation lives here, in M-180's module.
    assert PROMPT_KINDS == ("draft", "history", "image", "file")
    assert "dictation" not in PROMPT_KINDS
    assert "dictation" in ITEM_KINDS


def test_shipped_book_judged_honestly_as_data():
    book = load_voice_in_out()
    morning = book.dictation_for("dictation-morning-prompt")
    assert morning.state == "drafted"
    assert morning.availability == "available"
    assert morning.draft_text == morning.transcript
    assert morning.sent is False
    assert dictation_passes(morning) is True
    evening = book.dictation_for("dictation-evening-note")
    assert evening.state == "recording"
    assert evening.transcript == ""
    assert evening.availability == "unknown"
    assert "unknown" in evening.availability_reason
    assert dictation_passes(evening) is False
    spoken = book.standup_for("standup-morning")
    assert spoken.voice_name == "en_US-lessac-high"
    assert spoken.availability == "available"
    assert standup_passes(spoken) is True
    unspoken = book.standup_for("standup-evening")
    assert unspoken.voice_name is None
    assert unspoken.availability == "unavailable"
    assert "no catalog voice is cast" in (
        unspoken.availability_reason)
    for action in book.actions:
        assert action.text_equivalent
        assert item_passes(action) is True
    assert [i.item_id for i in passing_items(book)] == [
        "dictation-morning-prompt", "standup-morning",
        "action-dictate-prompt", "action-speak-standup",
        "action-mute-speech"]
    assert total_items(book) == 7


# ---------------------------------------------------------------------
# The dictation session: judged whole, its roads walked in order.
# ---------------------------------------------------------------------


def test_dictation_record_round_trips():
    session = _dictation()
    assert validate_dictation(_stored_dictation(session)) == session
    record = session.to_record()
    assert record["availability"] == "available"
    assert record["draft_text"] == "Fix the parser tests first."
    assert record["sent"] is False
    assert record["passes"] is True
    assert segment_of(session) == (
        "dictation-test: dictation drafted, availability "
        "available, draft never sent")
    assert session.segment == segment_of(session)


def test_dictation_provenance_is_whole_and_required():
    session = _dictation()
    assert session.recorded_on == ON
    assert session.actor == BY
    assert session.source == "test source"
    assert session.origin_session == "session-test"
    for missing in ("recorded_on", "actor", "source",
                    "origin_session", "dictation_id", "seq",
                    "state", "detail"):
        fields = _stored_dictation(session)
        fields.pop(missing)
        with pytest.raises(ValueError):
            build_dictation(fields)


def test_dictation_refuses_stored_derived_and_unknown_keys():
    fields = _stored_dictation(_dictation())
    for derived in ("availability", "draft_text", "segment",
                    "passes"):
        bad = dict(fields)
        bad[derived] = "available"
        with pytest.raises(ValueError):
            build_dictation(bad)
    sent = dict(fields)
    sent["sent"] = True
    with pytest.raises(ValueError):
        build_dictation(sent)
    auto = dict(fields)
    auto["auto_sent"] = True
    with pytest.raises(ValueError):
        build_dictation(auto)
    unknown = dict(fields)
    unknown["whenever"] = "x"
    with pytest.raises(ValueError):
        build_dictation(unknown)


def test_dictation_states_hold_their_cargo():
    with pytest.raises(ValueError):
        _dictation(state="recording")
    with pytest.raises(ValueError):
        _dictation(state="landed", transcript="")
    with pytest.raises(ValueError):
        _dictation(state="drafted", transcript="")
    recording = _dictation(state="recording", transcript="")
    assert recording.draft_text == ""
    assert recording.sent is False


def test_push_to_talk_walks_recording_landed_drafted():
    session = start_dictation(
        "dictation-walk", seq=3,
        capture_backend="existing_audio",
        transcriber_backend="existing_whisper")
    assert session.state == "recording"
    assert session.transcript == ""
    assert draft_text_of(session) == ""
    with pytest.raises(ValueError):
        draft_dictation(session)
    landed = stop_dictation(session, "Name the failing test first.")
    assert landed.state == "landed"
    assert landed.transcript == "Name the failing test first."
    assert draft_text_of(landed) == ""
    with pytest.raises(ValueError):
        stop_dictation(landed, "again")
    drafted = draft_dictation(landed)
    assert drafted.state == "drafted"
    assert drafted.draft_text == "Name the failing test first."
    assert drafted.sent is False
    assert dictation_passes(drafted) is True
    assert session.state == "recording"


def test_transcribe_dictation_travels_the_seam_only():
    session = start_dictation(
        "dictation-seam", capture_backend="existing_audio",
        transcriber_backend="existing_whisper")
    calls = []

    def fake_transcribe(path):
        calls.append(path)
        return "Words from the seam."

    landed = transcribe_dictation(
        session, "/tmp/voice-test.wav", transcribe=fake_transcribe)
    assert calls == ["/tmp/voice-test.wav"]
    assert landed.state == "landed"
    assert landed.transcript == "Words from the seam."
    quiet = transcribe_dictation
    with pytest.raises(ValueError):
        quiet(session, "/tmp/voice-test.wav",
              transcribe=lambda path: "")
    with pytest.raises(ValueError):
        transcribe_dictation(landed, "/tmp/voice-test.wav",
                             transcribe=fake_transcribe)


def test_dictation_availability_is_derived_and_named():
    word, reason = dictation_availability(_dictation())
    assert word == "available"
    assert "existing_audio" in reason
    word, reason = dictation_availability(
        _dictation(capture_backend=None))
    assert word == "unavailable"
    assert "no capture backend is named" in reason
    word, reason = dictation_availability(
        _dictation(transcriber_backend=None))
    assert word == "unavailable"
    assert "no transcriber backend is named" in reason
    word, reason = dictation_availability(
        _dictation(transcriber_backend=BACKEND_UNKNOWN))
    assert word == "unknown"
    assert availability_of(_dictation())[0] == "available"


# ---------------------------------------------------------------------
# The spoken stand-up: held whole, spoken only through the seam.
# ---------------------------------------------------------------------


def test_standup_record_round_trips():
    standup = _standup()
    assert validate_standup(_stored_standup(standup)) == standup
    record = standup.to_record()
    assert record["availability"] == "available"
    assert record["voice_name"] == "en_US-lessac-high"
    assert record["passes"] is True
    assert segment_of(standup) == (
        "standup-test: standup by Primary, availability "
        "available, voice en_US-lessac-high")


def test_standup_refuses_stored_derived_and_unknown_keys():
    fields = _stored_standup(_standup())
    for derived in ("availability", "spoken", "segment"):
        bad = dict(fields)
        bad[derived] = "available"
        with pytest.raises(ValueError):
            build_standup(bad)
    unknown = dict(fields)
    unknown["whenever"] = "x"
    with pytest.raises(ValueError):
        build_standup(unknown)
    for missing in ("speaker", "text", "detail", "recorded_on"):
        bad = dict(fields)
        bad.pop(missing)
        with pytest.raises(ValueError):
            build_standup(bad)


def test_standup_availability_is_derived_and_named():
    word, reason = standup_availability(_standup())
    assert word == "available"
    assert "en_US-lessac-high" in reason
    word, reason = standup_availability(_standup(tts_backend=None))
    assert word == "unavailable"
    assert "no TTS backend is named" in reason
    word, reason = standup_availability(_standup(voice_name=None))
    assert word == "unavailable"
    assert "no catalog voice is cast" in reason
    word, _reason = standup_availability(
        _standup(tts_backend=BACKEND_UNKNOWN))
    assert word == "unknown"
    assert standup_passes(_standup()) is True
    assert standup_passes(_standup(voice_name=None)) is False


def test_speak_standup_travels_the_seam_only_when_available():
    calls = []

    def fake_speak(agent_name, text):
        calls.append((agent_name, text))
        return True

    render = speak_standup(_standup(), speak=fake_speak)
    assert isinstance(render, SpeechRender)
    assert render.outcome == "spoken"
    assert render.spoken is True
    assert calls == [("Primary", _standup().text)]
    stopped = speak_standup(
        _standup(), speak=lambda agent_name, text: False)
    assert stopped.outcome == "unavailable"
    assert stopped.spoken is False
    calls.clear()
    uncast = speak_standup(_standup(voice_name=None), speak=fake_speak)
    assert uncast.outcome == "unavailable"
    assert "no catalog voice is cast" in uncast.reason
    assert calls == []
    unknown = speak_standup(
        _standup(tts_backend=BACKEND_UNKNOWN), speak=fake_speak)
    assert unknown.outcome == "unknown"
    assert calls == []


# ---------------------------------------------------------------------
# The voice action: the standing law, enforced by name.
# ---------------------------------------------------------------------


def test_action_record_round_trips():
    action = _action()
    assert validate_action(_stored_action(action)) == action
    record = action.to_record()
    assert record["voice_only"] is False
    assert record["passes"] is True
    assert segment_of(action) == (
        "test_action: text equivalent 'type the test "
        "command' stands - never voice-only")
    assert availability_of(action)[0] == "available"


def test_voice_only_action_refuses_by_name():
    fields = _stored_action(_action())
    fields["voice_only"] = True
    with pytest.raises(ValueError) as caught:
        build_action(fields)
    assert "test_action" in str(caught.value)
    assert "voice-only" in str(caught.value)
    assert "never the only door" in str(caught.value)
    fields = _stored_action(_action())
    fields.pop("text_equivalent")
    with pytest.raises(ValueError) as caught:
        build_action(fields)
    assert "test_action" in str(caught.value)
    with pytest.raises(ValueError):
        _action(text_equivalent="")
    with pytest.raises(ValueError):
        _action(text_equivalent=None)


def test_action_refuses_stored_derived_and_unknown_keys():
    fields = _stored_action(_action())
    bad = dict(fields)
    bad["segment"] = "written by hand"
    with pytest.raises(ValueError):
        build_action(bad)
    bad = dict(fields)
    bad["whenever"] = "x"
    with pytest.raises(ValueError):
        build_action(bad)


# ---------------------------------------------------------------------
# Views, panels and verdicts: derived, never stored loose.
# ---------------------------------------------------------------------


def test_view_record_round_trips_and_shows():
    view = _view()
    assert validate_view(_stored_view(view)) == view
    assert view.shows(_dictation()) is True
    assert view.shows(_standup()) is True
    narrowed = _view(view_id="view-dict", seq=2,
                     kind_filter="dictation")
    assert narrowed.shows(_dictation()) is True
    assert narrowed.shows(_standup()) is False
    assert narrowed.shows(_action()) is False


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book, "view-test")
    assert panel.total_items == 5
    assert panel.total_shown == 5
    assert {c.kind: c.items for c in panel.kind_counts} == {
        "dictation": 2, "standup": 2, "action": 1}
    assert panel.rows[0].segment == segment_of(book.dictations[0])
    assert validate_panel(panel.to_record(), book) == panel
    assert build_panel(source=book) == panel
    stored = panel.to_record()
    stored["rows"] = [dict(row) for row in stored["rows"]]
    stored["rows"][0]["segment"] = "softened by hand"
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    narrowed = derive_panel(book, _view(
        view_id="view-dict", seq=2, kind_filter="dictation"))
    assert narrowed.total_shown == 2
    assert [row.item_id for row in narrowed.rows] == [
        "dictation-test", "dictation-held"]
    row = build_row(item=book.dictations[0])
    assert row.item_id == "dictation-test"
    assert build_row(row.to_record(), book.dictations[0]) == row


def test_verdict_is_derived_from_the_shown_items():
    book = _mixed_book()
    verdict = derive_verdict(book, "view-test")
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 5
    assert verdict.passing_shown == 3
    assert verdict.distinct_kinds == 3
    assert validate_verdict(verdict.to_record(), book, "view-test") == (
        verdict)
    assert build_verdict(source=book) == verdict
    open_book = _book()
    assert derive_verdict(open_book).verdict == "open"
    shut_book = _book(
        dictations=[_dictation(state="recording", transcript="")],
        standups=[_standup(voice_name=None)], actions=[])
    assert derive_verdict(shut_book).verdict == "shut"
    empty = VoiceBook(title="An empty voice book")
    empty_verdict = derive_verdict(empty)
    assert empty_verdict.verdict == "shut"
    assert empty_verdict.total_shown == 0
    assert empty_verdict.earliest_on is None
    with pytest.raises(ValueError):
        VoiceVerdict(
            total_items=5, total_shown=5, passing_shown=3,
            distinct_kinds=3, earliest_on=ON, latest_on=ON,
            verdict="open")


def test_shown_and_kind_readings():
    book = _mixed_book()
    assert [i.item_id for i in shown_items(book, "view-test")] == [
        "dictation-test", "dictation-held", "standup-test",
        "standup-unspoken", "action-test"]
    assert [i.item_id for i in items_for_kind(book, "standup")] == [
        "standup-test", "standup-unspoken"]
    assert [i.item_id for i in items_for_kind(book, "PTT")] == [
        "dictation-test", "dictation-held"]
    with pytest.raises(KeyError):
        book.dictation_for("dictation-nope")
    with pytest.raises(KeyError):
        book.view_for("view-nope")


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(dictations=[_dictation(), _dictation(seq=2)])
    with pytest.raises(ValueError):
        _book(actions=[_action(), _action(action_id="action-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_id="view-two")])
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / VOICE_IN_OUT_RESOURCE
    ).read_text(encoding="utf-8"))
    raw["verdict"] = "strained"
    with pytest.raises(ValueError):
        load_voice_in_out(raw)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / VOICE_IN_OUT_RESOURCE).read_text(encoding="utf-8")
    path = tmp_path / "voice_in_out.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_voice_in_out_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_items(book) == 7


# ---------------------------------------------------------------------
# The registry: items and views held one by one.
# ---------------------------------------------------------------------


def test_registry_holds_items_and_views_one_by_one():
    registry = VoiceRegistry()
    held = registry.register_dictation(_dictation())
    assert held.dictation_id == "dictation-test"
    registry.register_standup(_standup())
    registry.register_action(_action())
    view = registry.register_view(_view(view_id=None))
    assert view.view_id == "view-1"
    assert registry.get_dictation("dictation-test") == held
    assert registry.get_standup("standup-test").speaker == "Primary"
    assert registry.get_action("action-test").name == "test_action"
    assert registry.latest_view() == view
    book = registry.book()
    assert book.title == "Voice In and Out"
    assert total_items(book) == 3
    assert registry.panel().total_shown == 3
    assert registry.verdict().verdict == "open"
    with pytest.raises(ValueError):
        registry.register_dictation(_dictation(seq=9))
    with pytest.raises(ValueError):
        registry.register_action(_action(action_id="action-two"))
    with pytest.raises(KeyError):
        registry.get_dictation("dictation-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = VoiceRegistry()
    book = registry.register_book(_mixed_book())
    assert total_items(book) == 5
    assert book.title == "A test voice book"
    with pytest.raises(ValueError):
        registry.register_book(_mixed_book())
    other = VoiceRegistry()
    other.register_dictation(_dictation())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


# ---------------------------------------------------------------------
# News, plain words, screens and the command grammar.
# ---------------------------------------------------------------------


def test_records_are_session_news():
    session = _dictation()
    record = dictation_record(session)
    assert record["news"] is True
    assert record["type"] == "voice_in_out_dictation"
    assert "dictation-test" in record["headline"]
    assert standup_record(_standup())["type"] == (
        "voice_in_out_standup")
    assert action_record(_action())["type"] == "voice_in_out_action"
    assert view_record(_view())["type"] == "voice_in_out_view"
    book = _mixed_book()
    panel_news = panel_record(derive_panel(book, "view-test"), book)
    assert panel_news["type"] == "voice_in_out_panel"
    assert panel_news["news"] is True
    verdict_news = verdict_record(
        derive_verdict(book, "view-test"), book, "view-test")
    assert verdict_news["type"] == "voice_in_out_verdict"
    assert verdict_news["verdict"] == "strained"
    whole = book_record(book)
    assert whole["type"] == "voice_in_out_book"
    assert whole["item_count"] == 5


def test_plain_words_and_formatters():
    session = _dictation()
    assert "never auto-sent" in plain_words(session)
    assert "existing TTS seam" in standup_plain_words(_standup())
    assert "never the only door" in action_plain_words(_action())
    assert "kind 'all'" in view_plain_words(_view())
    book = _mixed_book()
    assert "strained" in verdict_plain_words(book)
    panel_words = panel_plain_words(book)
    assert "A test voice book" in panel_words
    assert "dictation-test" in panel_words
    text = format_dictation(session)
    assert "State: drafted" in text
    assert "Availability: available" in text
    assert "never auto-sent" in text
    text = format_standup(_standup())
    assert "Catalog voice: en_US-lessac-high" in text
    text = format_action(_action())
    assert "Text equivalent: type the test command" in text
    assert "never the only door" in text
    assert "mode" not in format_view(_view())
    assert "kind 'all'" in format_view(_view())
    assert "dictation-test: dictation-test:" in format_book(book)
    assert "Panel in A test voice book" in format_panel(book)
    assert "strained" in format_verdict(book)
    screen = format_voice_in_out_screen()
    assert "Voice In and Out (M-180)" in screen
    assert "7 of 7 items show" in screen
    assert "standup-evening" in screen


def test_parse_args_grammar():
    assert parse_voice_in_out_args("") == ("show", None)
    assert parse_voice_in_out_args(None) == ("show", None)
    assert parse_voice_in_out_args(
        "dictation dictation-test") == ("dictation", "dictation-test")
    assert parse_voice_in_out_args(
        "standup standup-test") == ("standup", "standup-test")
    assert parse_voice_in_out_args(
        "action action-test") == ("action", "action-test")
    assert parse_voice_in_out_args("view view-test") == (
        "view", "view-test")
    assert parse_voice_in_out_args("kind ptt") == ("kind", "dictation")
    assert parse_voice_in_out_args("panel") == ("panel", None)
    assert parse_voice_in_out_args("verdict") == ("verdict", None)
    with pytest.raises(ValueError) as caught:
        parse_voice_in_out_args("dance party")
    assert str(caught.value) == USAGE
    with pytest.raises(ValueError):
        parse_voice_in_out_args("kind whenever")


def test_inspect_item_source_names_pieces():
    assert inspect_item_source(
        {"transcript": "words"})["kind"] == "dictation"
    assert inspect_item_source(
        {"speaker": "Primary"})["kind"] == "standup"
    assert inspect_item_source(
        {"voice_phrase": "say it",
         "text_equivalent": "type it"})["kind"] == "action"
    refused = inspect_item_source(
        {"voice_phrase": "say it", "voice_only": True})
    assert refused["kind"] is None
    assert "never the only door" in refused["reason"]
    assert inspect_item_source("nope")["kind"] is None
    assert inspect_item_source({})["kind"] is None


# ---------------------------------------------------------------------
# M-180 agent layer: the agent holds a voice
# book for the session, items and views are
# published as session news through the
# checkpoint road (journal first, deduped per
# shape), and the panel and verdict are derived
# at call time from the whole book under a view,
# never held. This layer captures no live audio,
# builds no TTS engine, speaks nothing live,
# calls no model, persists nothing beyond the
# session journal news and banks nothing - and
# it sends no prompt: a dictation held here is a
# draft, never a send.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _voice_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "voice_in_out.yaml").read_text(encoding="utf-8")
    path = tmp_path / "voice_in_out.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestVoiceInOutAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.voice_in_out_status()
        assert status["dictations"] == []
        assert status["standups"] == []
        assert status["actions"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["voice_in_out"]["title"] == EXAMPLE_TITLE
        assert len(status["voice_in_out"]["dictations"]) == 2
        assert len(status["voice_in_out"]["standups"]) == 2
        assert len(status["voice_in_out"]["actions"]) == 3
        assert len(status["voice_in_out"]["views"]) == 2
        assert status["panel"]["total_items"] == 7
        assert status["panel"]["total_shown"] == 7
        assert status["panels"][0]["panel_id"] == "panel-m179-boundary"
        assert status["book_record"]["item_count"] == 7
        assert status["book_record"]["view_count"] == 2
        assert status["verdict"]["verdict"] == "strained"
        assert "never the only door" in status["plain_words"]
        assert "Voice In and Out (M-180)" in status["screen"]
        assert "7 of 7 items show" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._voice_in_out_registry()
        assert agent._voice_in_out_registry() is first
        assert agent._voice_in_out_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.voice_in_out_status()
        assert agent.get_dictation_session(
            "dictation-morning-prompt").state == "drafted"
        assert agent.get_spoken_standup(
            "standup-morning").voice_name == "en_US-lessac-high"
        assert agent.get_voice_action(
            "action-dictate-prompt").name == "dictate_prompt"
        assert agent.get_voice_view(
            "view-all").kind_filter == "all"
        assert [i.item_id for i in agent.voice_in_out_with_kind(
            "dictation")] == [
                "dictation-morning-prompt", "dictation-evening-note"]
        assert [i.item_id for i in agent.voice_in_out_with_kind(
            "spoken")] == ["standup-morning", "standup-evening"]
        assert [i.item_id for i in agent.voice_in_out_passing()] == [
            "dictation-morning-prompt", "standup-morning",
            "action-dictate-prompt", "action-speak-standup",
            "action-mute-speech"]
        agent.voice_in_out_panel()
        agent.voice_in_out_verdict()
        agent.report_voice_in_out()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("voice_in_out")] == []
        with pytest.raises(KeyError):
            agent.get_dictation_session("dictation-nope")
        with pytest.raises(KeyError):
            agent.get_voice_view("view-nope")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_dictation_session(_dictation())
        status = agent.voice_in_out_status()
        assert [d["dictation_id"] for d in status["dictations"]] == [
            "dictation-test"]
        assert status["book"]["title"] == "Voice In and Out"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert "dictation drafted, availability available" in (
            status["screen"])

    def test_held_item_never_falls_back_to_the_example(
            self, agent):
        agent.register_dictation_session(_dictation())
        with pytest.raises(KeyError):
            agent.get_dictation_session("dictation-morning-prompt")
        with pytest.raises(KeyError):
            agent.get_voice_view("view-all")
        session = agent.get_dictation_session("dictation-test")
        assert session.state == "drafted"
        assert agent.voice_in_out_book().title == "Voice In and Out"


class TestVoiceInOutAgentHolding:
    def test_register_dictation_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_dictation_session(_dictation())
        assert outcome["dictation"]["dictation_id"] == "dictation-test"
        assert outcome["record_news"]["news"] is True
        assert outcome["record_news"]["type"] == (
            "voice_in_out_dictation")
        assert "dictation-test" in outcome["screen"]
        agent.register_dictation_session(_dictation(
            dictation_id="dictation-two", seq=2,
            state="recording", transcript="",
            transcriber_backend="unknown"))
        events = _voice_events(
            store, session_id, "voice_in_out_dictation")
        assert len(events) == 2
        agent._publish_voice_in_out_record(dictation_record(_dictation()))
        agent._publish_voice_in_out_record(
            {"type": "slice_board_card", "news": True})
        events = _voice_events(
            store, session_id, "voice_in_out_dictation")
        assert len(events) == 2
        agent.close()

    def test_duplicate_dictation_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_dictation_session(_dictation())
        with pytest.raises(ValueError):
            agent.register_dictation_session(_dictation())
        with pytest.raises(ValueError):
            agent.register_dictation_session(_dictation(seq=2))
        events = _voice_events(
            store, session_id, "voice_in_out_dictation")
        assert len(events) == 1
        agent.close()

    def test_register_standup_and_action_hold_and_publish(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_spoken_standup(_standup())
        assert outcome["standup"]["standup_id"] == "standup-test"
        assert outcome["record_news"]["type"] == (
            "voice_in_out_standup")
        with pytest.raises(ValueError):
            agent.register_spoken_standup(_standup(seq=2))
        outcome = agent.register_voice_action(_action())
        assert outcome["action"]["name"] == "test_action"
        assert outcome["record_news"]["type"] == "voice_in_out_action"
        with pytest.raises(ValueError):
            agent.register_voice_action(
                _action(action_id="action-two", seq=2))
        assert len(_voice_events(
            store, session_id, "voice_in_out_standup")) == 1
        assert len(_voice_events(
            store, session_id, "voice_in_out_action")) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_dictation_session(_dictation())
        outcome = agent.register_voice_view(_view())
        assert outcome["view"]["view_id"] == "view-test"
        assert outcome["record_news"]["type"] == "voice_in_out_view"
        with pytest.raises(ValueError):
            agent.register_voice_view(_view(seq=2))
        with pytest.raises(ValueError):
            agent.register_voice_view(
                _view(view_id="view-two"))
        assert [v.view_id for v in
                agent._voice_in_out_registry().list_views()] == [
                    "view-test"]
        events = _voice_events(
            store, session_id, "voice_in_out_view")
        assert len(events) == 1
        agent.close()

    def test_view_road_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_dictation_session(_dictation())
        agent.register_spoken_standup(_standup(voice_name=None))
        outcome = agent.view_voice_in_out("all")
        assert outcome["view"]["seq"] == 1
        assert outcome["view"]["view_id"] == "view-1"
        assert outcome["record_news"]["type"] == "voice_in_out_view"
        assert outcome["panel_record"]["type"] == (
            "voice_in_out_panel")
        assert outcome["panel_record"]["total_shown"] == 2
        assert outcome["verdict_record"]["type"] == (
            "voice_in_out_verdict")
        assert outcome["verdict_record"]["verdict"] == "strained"
        second = agent.view_voice_in_out(
            "standup",
            detail="See the stand-ups alone, for the tests.")
        assert second["view"]["seq"] == 2
        assert second["verdict_record"]["verdict"] == "shut"
        assert agent.voice_in_out_verdict().verdict == "strained"
        assert len(_voice_events(
            store, session_id, "voice_in_out_view")) == 2
        assert len(_voice_events(
            store, session_id, "voice_in_out_verdict")) == 2
        agent.close()

    def test_view_road_over_an_unshown_kind_is_shut(self, agent):
        agent.register_dictation_session(_dictation())
        outcome = agent.view_voice_in_out("standup")
        assert outcome["panel_record"]["total_shown"] == 0
        assert outcome["verdict_record"]["verdict"] == "shut"
        assert agent.voice_in_out_panel(
            outcome["view"]["view_id"]).total_shown == 0

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_voice_in_out_book(_mixed_book())
        assert outcome["count"] == 5
        assert [d["dictation_id"] for d in outcome["dictations"]] == [
            "dictation-test", "dictation-held"]
        assert [r["type"] for r in outcome["records_news"]] == [
            "voice_in_out_dictation", "voice_in_out_dictation",
            "voice_in_out_standup", "voice_in_out_standup",
            "voice_in_out_action", "voice_in_out_view"]
        events = _voice_events(
            store, session_id, "voice_in_out_dictation")
        assert [e["dictation_id"] for e in events] == [
            "dictation-test", "dictation-held"]
        assert agent.voice_in_out_book().title == (
            "A test voice book")
        with pytest.raises(ValueError):
            agent.register_voice_in_out_book(_mixed_book())
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_voice_in_out_book()
        assert outcome["count"] == 7
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_voice_events(
            store, session_id, "voice_in_out_dictation")) == 2
        assert len(_voice_events(
            store, session_id, "voice_in_out_standup")) == 2
        assert len(_voice_events(
            store, session_id, "voice_in_out_action")) == 3
        assert len(_voice_events(
            store, session_id, "voice_in_out_view")) == 2
        status = agent.voice_in_out_status()
        assert status["panels"][0]["panel_id"] == "panel-m179-boundary"
        with pytest.raises(ValueError):
            agent.record_voice_in_out_book()
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_book_file(tmp_path)
        book = load_voice_in_out_file(path)
        outcome = agent.record_voice_in_out_book(book)
        assert outcome["count"] == 7
        assert agent.voice_in_out_book().title == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_voice_in_out()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert len(report["dictations"]) == 2
        assert len(report["actions"]) == 3
        assert report["verdict"]["verdict"] == "strained"
        assert "standup-morning: standup-morning: standup by" in (
            report["book_text"])
        agent.register_dictation_session(_dictation())
        report = agent.report_voice_in_out()
        assert [d["dictation_id"] for d in report["dictations"]] == [
            "dictation-test"]
        assert "dictation-test: dictation-test: dictation drafted" in (
            report["book_text"])
        assert report["verdict"] is None

    def test_holding_and_viewing_execute_nothing(self, agent):
        for name in (
                "capture_live_audio", "record_live_audio",
                "speak_live_tts", "send_dictated_prompt",
                "transcribe_live_audio", "clone_catalog_voice",
                "persist_voice_in_out", "bank_voice_in_out",
                "run_voice_in_out", "delete_dictation"):
            assert not hasattr(agent, name), name
        agent.register_dictation_session(_dictation())
        agent.view_voice_in_out("all")
        # A view held here only ever looks: no audio was
        # captured, no stand-up was spoken live, no
        # prompt was sent, and the book's standing lives
        # in no setting.
        assert agent.voice_in_out_book().title == "Voice In and Out"
        assert agent.config.get("voice_in_out") is None


class TestVoiceInOutTerminalSurface:
    def test_show_dictation_standup_action_view_kind_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/voiceinout")
        assert "Voice In and Out (M-180)" in text
        _, _, text = _slash(
            agent, "/voiceinout dictation dictation-morning-prompt")
        assert "State: drafted" in text
        _, _, text = _slash(agent, "/voiceinout standup standup-morning")
        assert "Catalog voice: en_US-lessac-high" in text
        _, _, text = _slash(
            agent, "/voiceinout action action-dictate-prompt")
        assert "Text equivalent: type the prompt as a draft" in text
        _, _, text = _slash(agent, "/voiceinout view view-all")
        assert "kind 'all'" in text
        _, _, text = _slash(agent, "/voiceinout kind standup")
        assert "standup-morning" in text
        assert "dictation-morning-prompt" not in text
        _, _, text = _slash(agent, "/voiceinout panel")
        assert "Panel in Voice at the M-179 slice boundary" in text
        _, _, text = _slash(agent, "/voiceinout verdict")
        assert "strained" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/voiceinout [show|dictation <dictation-id>"
                "|standup <standup-id>|action <action-id>"
                "|view <view-id>|kind <kind>|panel|verdict]") in text
        _, _, text = _slash(agent, "/voiceinout dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/voiceinout dictation dictation-nope")
        assert "no dictation named" in text


@pytest.fixture()
def voice_handler(agent, monkeypatch):
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


def _voice_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestVoiceInOutCommand:
    def test_show_is_default(self, voice_handler, agent):
        voice_handler._handle_voiceinout("")
        assert "Voice In and Out (M-180)" in (
            _voice_published_text(voice_handler))

    def test_dictation_standup_action_view_kind_panel_verdict(
            self, voice_handler, agent):
        voice_handler._handle_voiceinout(
            "dictation dictation-morning-prompt")
        assert "State: drafted" in (
            _voice_published_text(voice_handler))
        voice_handler._handle_voiceinout("standup standup-morning")
        assert "en_US-lessac-high" in _voice_published_text(
            voice_handler)
        voice_handler._handle_voiceinout("action action-mute-speech")
        assert "use the typed mute toggle" in _voice_published_text(
            voice_handler)
        voice_handler._handle_voiceinout("view view-all")
        assert "kind 'all'" in _voice_published_text(voice_handler)
        voice_handler._handle_voiceinout("kind action")
        assert "action-mute-speech" in _voice_published_text(
            voice_handler)
        voice_handler._handle_voiceinout("panel")
        assert "Panel in Voice" in (
            _voice_published_text(voice_handler))
        voice_handler._handle_voiceinout("verdict")
        assert "strained" in _voice_published_text(voice_handler)

    def test_bad_grammar_is_published(
            self, voice_handler, agent):
        voice_handler._handle_voiceinout("dance party")
        assert USAGE in _voice_published_text(voice_handler)
        voice_handler._handle_voiceinout("dictation dictation-nope")
        assert "no dictation named" in _voice_published_text(
            voice_handler)


class TestChatScreenRoutingVoiceInOut:
    def test_voiceinout_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/voiceinout panel", _FakeLog())
        assert calls == [("/voiceinout", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/voiceinout[/green] - show voice in and out (M-180)" in (
            text)
        assert ('"/voiceinout": "Usage: /voiceinout | '
                '/voiceinout dictation <dictation-id>') in text
