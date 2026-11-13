"""M-181 Notifications with Manners - pure-layer tests.

TIER: integration

The pure layer is manners, held as data: a job
held whole (its outcome - running, completed or
failed - how long it ran, the bell and OS
backends it names, and the one failure action a
failure carries), a notification channel held
whole (its name and the backend it names), and a
manners rule held whole (the standing law itself,
as data). Whether a job announces is derived
from its outcome and duration - silence is the
default posture: a running job and a short
completed job announce nothing, a long completed
job announces, and a failure announces whatever
its length, each at most once under a key derived
from the job's own identity. Availability is
derived from the backends a record names -
available, unavailable by a named reason, or
honestly unknown - never stored and never faked.
The panel is derived for one held view and the
verdict is derived for the whole book under one
view. The shipped example book is held in a data
file, and a loader reads a book from any file. No
row of the M-171 charter names M-181, so the slice
is built to the roadmap words alone, as M-177,
M-179 and M-180 were. Live roads stand behind
seams a test can fake: nothing here rings a real
bell, posts a real notification, needs a desktop
or sends anything.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.notifications_manners import (
    AVAILABILITY_WORDS,
    BACKEND_UNKNOWN,
    CHANNEL_NAMES,
    DECISION_WORDS,
    ITEM_KINDS,
    LONG_JOB_THRESHOLD_SECONDS,
    NOTIFICATIONS_MANNERS_RESOURCE,
    NOTIFICATIONS_MANNERS_SCHEMA,
    NOTIFICATIONS_MANNERS_SLICE,
    OUTCOMES,
    PLAIN_EXPLANATION,
    RULE_NAMES,
    SILENCE_IS_THE_DEFAULT_POSTURE,
    USAGE,
    VERDICT_WORDS,
    VIEW_KINDS,
    Announcement,
    ChannelNotice,
    JobNotice,
    MannersRule,
    NoticeBook,
    NoticePanel,
    NoticeRegistry,
    NoticeVerdict,
    NoticeView,
    announcement_decision,
    announcement_for,
    announcement_key,
    announcement_plain_words,
    availability_of,
    book_record,
    build_book,
    build_channel,
    build_job,
    build_panel,
    build_row,
    build_rule,
    build_verdict,
    build_view,
    channel_availability,
    channel_of,
    channel_plain_words,
    channel_record,
    complete_job,
    decision_of,
    deliver_announcement,
    derive_panel,
    derive_verdict,
    due_announcements,
    fail_job,
    format_book,
    format_channel,
    format_job,
    format_notifications_manners_screen,
    format_panel,
    format_rule,
    format_verdict,
    format_view,
    inspect_item_source,
    is_long_job,
    item_passes,
    items_for_kind,
    job_availability,
    job_passes,
    job_plain_words,
    job_record,
    load_notifications_manners,
    load_notifications_manners_file,
    normalize_channel_name,
    normalize_kind,
    normalize_kind_filter,
    normalize_outcome,
    normalize_rule_name,
    panel_plain_words,
    panel_record,
    parse_notifications_manners_args,
    passing_items,
    plain_words,
    rule_plain_words,
    rule_record,
    segment_of,
    shown_items,
    total_items,
    validate_channel,
    validate_job,
    validate_row,
    validate_panel,
    validate_rule,
    validate_verdict,
    validate_view,
    verdict_plain_words,
    verdict_record,
    view_plain_words,
    view_record,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Notifications at the M-180 slice boundary"

BY = "the coordinator"
ON = "2026-11-09"


def _job(**overrides):
    fields = {
        "job_id": "job-test",
        "seq": 1,
        "outcome": "completed",
        "duration_seconds": 900,
        "bell_backend": "terminal_bell",
        "os_backend": "notify_send",
        "detail": "A job held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_job(fields)


def _stored_job(job):
    stored = job.to_record()
    for key in ("type", "slice", "decision",
                "decision_reason", "channel", "availability",
                "availability_reason", "announcement_key",
                "passes", "segment"):
        stored.pop(key)
    return stored


def _channel(**overrides):
    fields = {
        "channel_id": "channel-test",
        "seq": 1,
        "name": "terminal_bell",
        "backend": "terminal_bell",
        "detail": "A channel held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_channel(fields)


def _stored_channel(channel):
    stored = channel.to_record()
    for key in ("type", "slice", "availability",
                "availability_reason", "passes", "segment"):
        stored.pop(key)
    return stored


def _rule(**overrides):
    fields = {
        "rule_id": "rule-test",
        "seq": 1,
        "name": "silence_by_default",
        "statement": "announce nothing unless the derivation says otherwise",
        "detail": "A manners rule held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_rule(fields)


def _stored_rule(rule):
    stored = rule.to_record()
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


def _book(jobs=None, channels=None, rules=None,
          views=(), **overrides):
    fields = {
        "title": "A test manners book",
        "jobs": [_stored_job(item) for item in (
            jobs if jobs is not None else [_job()])],
        "channels": [_stored_channel(item) for item in (
            channels if channels is not None else [_channel()])],
        "rules": [_stored_rule(item) for item in (
            rules if rules is not None else [_rule()])],
        "views": [_stored_view(item) for item in views],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(
        jobs=[
            _job(),
            _job(
                job_id="job-held", seq=2,
                outcome="running", duration_seconds=30),
            _job(
                job_id="job-broken", seq=3,
                outcome="failed", duration_seconds=45,
                os_backend="unknown", bell_backend=None,
                failure_action="check the named log first"),
        ],
        channels=[
            _channel(),
            _channel(
                channel_id="channel-dark", seq=2,
                name="os_notification", backend=None),
        ],
        rules=[_rule()],
        views=[_view()])


# ---------------------------------------------------------------------
# The shipped example book, the roadmap and the charter.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_notifications_manners()
    assert book.title == EXAMPLE_TITLE
    assert book.job_ids() == (
        "job-morning-build", "job-quick-check",
        "job-night-export")
    assert book.channel_ids() == (
        "channel-terminal-bell", "channel-os-notification")
    assert book.rule_ids() == (
        "rule-silence-by-default",
        "rule-failure-names-one-action")
    assert book.view_ids() == ("view-all", "view-job")
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m180-boundary"
    assert panel.as_of == "2026-11-09"
    assert [row.item_id for row in panel.rows] == [
        "job-morning-build", "job-quick-check",
        "job-night-export", "channel-terminal-bell",
        "channel-os-notification", "rule-silence-by-default",
        "rule-failure-names-one-action"]
    derived = derive_panel(book, "view-all")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 7
    assert panel.total_shown == derived.total_shown == 7
    assert {c.kind: c.items for c in panel.kind_counts} == {
        "job": 3, "channel": 2, "rule": 2}
    assert derive_verdict(book, "view-all").verdict == "strained"
    assert derive_verdict(book, "view-job").verdict == "strained"
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / NOTIFICATIONS_MANNERS_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == NOTIFICATIONS_MANNERS_SCHEMA
    assert raw["slice"] == "M-181"
    assert "verdict" not in raw
    assert "segment" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-181")]
    assert slice_.title == "Notifications with manners"
    assert slice_.part == 8
    assert "long jobs announce completion" in slice_.summary
    assert "failures announce once" in slice_.summary
    assert "one action that matters" in slice_.summary
    assert "silence is the default posture" in slice_.summary
    assert NOTIFICATIONS_MANNERS_SLICE == "M-181"


def test_charter_names_no_row_for_m181():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-181" not in owners


def test_closed_vocabularies():
    assert ITEM_KINDS == ("job", "channel", "rule")
    assert VIEW_KINDS == ("all",) + ITEM_KINDS
    assert OUTCOMES == ("running", "completed", "failed")
    assert CHANNEL_NAMES == ("terminal_bell", "os_notification")
    assert RULE_NAMES == (
        "silence_by_default", "announce_once",
        "failure_names_one_action")
    assert DECISION_WORDS == ("announce", "silence")
    assert AVAILABILITY_WORDS == (
        "available", "unavailable", "unknown")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert BACKEND_UNKNOWN == "unknown"
    assert LONG_JOB_THRESHOLD_SECONDS == 60
    assert SILENCE_IS_THE_DEFAULT_POSTURE is True
    assert normalize_kind("TASK") == "job"
    assert normalize_kind("law") == "rule"
    assert normalize_kind_filter("ALL") == "all"
    assert normalize_kind_filter("road") == "channel"
    assert normalize_outcome("done") == "completed"
    assert normalize_outcome("errored") == "failed"
    assert normalize_channel_name("bell") == "terminal_bell"
    assert normalize_channel_name("desktop") == "os_notification"
    assert normalize_rule_name("once") == "announce_once"
    with pytest.raises(ValueError):
        normalize_kind("whenever")
    with pytest.raises(ValueError):
        normalize_outcome("announced")
    with pytest.raises(ValueError):
        normalize_rule_name("shout_loudly")
    assert "silence is the default posture" in PLAIN_EXPLANATION
    assert "at most once" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /manners")


def test_shipped_book_judged_honestly_as_data():
    book = load_notifications_manners()
    morning = book.job_for("job-morning-build")
    assert morning.outcome == "completed"
    assert morning.decision == "announce"
    assert morning.channel == "os_notification"
    assert morning.availability == "available"
    assert job_passes(morning) is True
    quick = book.job_for("job-quick-check")
    assert quick.decision == "silence"
    assert "silence is the default posture" in quick.decision_reason
    assert job_passes(quick) is True
    night = book.job_for("job-night-export")
    assert night.outcome == "failed"
    assert night.decision == "announce"
    assert night.failure_action == (
        "rerun the export after checking the disk space")
    assert night.channel is None
    assert night.availability == "unknown"
    assert "unknown" in night.availability_reason
    assert job_passes(night) is False
    bell = book.channel_for("channel-terminal-bell")
    assert bell.availability == "available"
    assert item_passes(bell) is True
    dark = book.channel_for("channel-os-notification")
    assert dark.backend is None
    assert dark.availability == "unavailable"
    assert "no backend is named" in dark.availability_reason
    assert item_passes(dark) is False
    for rule in book.rules:
        assert rule.statement
        assert item_passes(rule) is True
    assert [i.item_id for i in passing_items(book)] == [
        "job-morning-build", "job-quick-check",
        "channel-terminal-bell", "rule-silence-by-default",
        "rule-failure-names-one-action"]
    assert total_items(book) == 7
    assert [a.key for a in due_announcements(book)] == [
        "job-morning-build:completed", "job-night-export:failed"]


# ---------------------------------------------------------------------
# The job: judged whole, its manners derived.
# ---------------------------------------------------------------------


def test_job_record_round_trips():
    job = _job()
    assert validate_job(_stored_job(job)) == job
    record = job.to_record()
    assert record["decision"] == "announce"
    assert record["channel"] == "os_notification"
    assert record["availability"] == "available"
    assert record["announcement_key"] == "job-test:completed"
    assert record["passes"] is True
    assert segment_of(job) == (
        "job-test: job completed after 900s, decision "
        "announce, channel os_notification")


def test_silence_is_the_default_posture():
    short = _job(duration_seconds=20)
    word, reason = announcement_decision(short)
    assert word == "silence"
    assert "default posture" in reason
    assert announcement_for(short) is None
    running = _job(outcome="running", duration_seconds=9999)
    assert announcement_decision(running)[0] == "silence"
    assert announcement_for(running) is None
    assert job_passes(running) is False


def test_long_job_threshold_is_a_boundary():
    assert is_long_job(_job(duration_seconds=59)) is False
    assert is_long_job(_job(duration_seconds=60)) is True
    assert announcement_decision(
        _job(duration_seconds=59))[0] == "silence"
    assert announcement_decision(
        _job(duration_seconds=60))[0] == "announce"
    named = _job(duration_seconds=30)
    assert is_long_job(named, threshold=30) is True
    assert announcement_decision(named, threshold=30)[0] == "announce"
    assert decision_of(named) == announcement_decision(named)


def test_failure_announces_at_any_length_with_one_action():
    failed = _job(
        outcome="failed", duration_seconds=5,
        failure_action="restart the worker")
    assert announcement_decision(failed)[0] == "announce"
    found = announcement_for(failed)
    assert found is not None
    assert found.action == "restart the worker"
    assert "restart the worker" in found.message
    assert found.key == "job-test:failed"
    assert announcement_key(failed) == "job-test:failed"
    assert "one action" in announcement_plain_words(found)


def test_failure_names_exactly_one_action_or_refuses():
    with pytest.raises(ValueError) as excinfo:
        _job(outcome="failed", duration_seconds=5)
    assert "names no failure action" in str(excinfo.value)
    stored = _stored_job(_job())
    stored["outcome"] = "failed"
    stored["duration_seconds"] = 5
    stored["failure_actions"] = ["do this", "do that"]
    with pytest.raises(ValueError) as excinfo:
        validate_job(stored)
    assert "the one action that matters" in str(excinfo.value)
    stored["failure_actions"] = []
    with pytest.raises(ValueError):
        validate_job(stored)
    stored["failure_actions"] = ["restart the worker"]
    judged = validate_job(stored)
    assert judged.failure_action == "restart the worker"
    with pytest.raises(ValueError) as excinfo:
        _job(failure_action="not a failure")
    assert "stands on a failure alone" in str(excinfo.value)


def test_job_refuses_stored_judgements():
    stored = _stored_job(_job())
    stored["announced"] = True
    with pytest.raises(ValueError) as excinfo:
        validate_job(stored)
    assert "no stored" in str(excinfo.value)
    stored = _stored_job(_job())
    stored["decision"] = "announce"
    with pytest.raises(ValueError):
        validate_job(stored)
    stored = _stored_job(_job())
    stored["surprise"] = "x"
    with pytest.raises(ValueError) as excinfo:
        validate_job(stored)
    assert "unknown keys" in str(excinfo.value)


def test_channel_choice_is_derived_from_named_backends():
    both = _job()
    assert channel_of(both) == (
        "os_notification", "available", channel_of(both)[2])
    bell_only = _job(os_backend=None)
    assert channel_of(bell_only)[0] == "terminal_bell"
    assert job_availability(bell_only)[0] == "available"
    unknown_only = _job(os_backend="unknown", bell_backend=None)
    channel, word, reason = channel_of(unknown_only)
    assert channel is None
    assert word == "unknown"
    assert "not proven" in reason
    unnamed = _job(os_backend=None, bell_backend=None)
    channel, word, reason = channel_of(unnamed)
    assert channel is None
    assert word == "unavailable"
    assert "no bell backend and no OS backend" in reason
    unknown_os_good_bell = _job(
        os_backend="unknown", bell_backend="terminal_bell")
    assert channel_of(unknown_os_good_bell)[0] == "terminal_bell"
    assert availability_of(both)[0] == "available"


def test_channel_notice_availability_is_derived():
    channel = _channel()
    assert validate_channel(_stored_channel(channel)) == channel
    assert channel_availability(channel)[0] == "available"
    assert segment_of(channel) == (
        "channel-test: channel terminal_bell, availability "
        "available, backend terminal_bell")
    dark = _channel(backend=None)
    assert channel_availability(dark)[0] == "unavailable"
    assert "no backend is named" in channel_availability(dark)[1]
    murky = _channel(backend="unknown")
    assert channel_availability(murky)[0] == "unknown"
    assert item_passes(murky) is False
    stored = _stored_channel(channel)
    stored["availability"] = "available"
    with pytest.raises(ValueError):
        validate_channel(stored)
    assert "terminal_bell" in channel_plain_words(channel)


def test_rule_record_round_trips_and_law_is_data():
    rule = _rule()
    assert validate_rule(_stored_rule(rule)) == rule
    assert rule.passes is True
    assert segment_of(rule) == (
        "silence_by_default: manners rule stands - announce "
        "nothing unless the derivation says otherwise")
    assert availability_of(rule)[0] == "available"
    assert "stands as data" in rule_plain_words(rule)
    with pytest.raises(ValueError):
        _rule(name="shout_loudly")
    stored = _stored_rule(rule)
    stored["passes"] = True
    with pytest.raises(ValueError):
        validate_rule(stored)


def test_announce_once_under_the_derived_key():
    book = load_notifications_manners()
    first = due_announcements(book)
    assert [a.key for a in first] == [
        "job-morning-build:completed", "job-night-export:failed"]
    ledger = [a.key for a in first]
    assert due_announcements(book, ledger) == ()
    assert due_announcements(book, ledger) == ()
    job = book.job_for("job-morning-build")
    assert announcement_for(job, ledger) is None
    assert announcement_for(job) is not None
    assert announcement_key(job) == announcement_key(job)
    short = book.job_for("job-quick-check")
    assert due_announcements([short]) == ()
    failed = book.job_for("job-night-export")
    found = announcement_for(failed)
    assert found.action == (
        "rerun the export after checking the disk space")
    assert found.channel is None
    assert found.availability == "unknown"


def test_job_transitions_finish_once():
    running = _job(outcome="running", duration_seconds=10)
    finished = complete_job(running, 900)
    assert finished.outcome == "completed"
    assert finished.duration_seconds == 900
    assert announcement_decision(finished)[0] == "announce"
    failed = fail_job(running, "restart the worker")
    assert failed.outcome == "failed"
    assert failed.failure_action == "restart the worker"
    with pytest.raises(ValueError):
        complete_job(finished)
    with pytest.raises(ValueError):
        fail_job(finished, "too late")
    with pytest.raises(ValueError):
        fail_job(running, "")


def test_announcement_gates_hold():
    with pytest.raises(ValueError):
        Announcement(
            job_id="job-x", outcome="running", channel=None,
            availability="unknown", message="m", action=None)
    with pytest.raises(ValueError):
        Announcement(
            job_id="job-x", outcome="failed",
            channel="terminal_bell", availability="available",
            message="m", action=None)
    with pytest.raises(ValueError):
        Announcement(
            job_id="job-x", outcome="completed", channel=None,
            availability="available", message="m", action=None)
    made = announcement_for(_job())
    assert made.channel == "os_notification"
    assert made.action is None
    assert "finished after 900 seconds" in made.message


def test_delivery_travels_fakeable_seams():
    bells = []
    notes = []
    bell_ann = announcement_for(_job(os_backend=None))
    delivered = deliver_announcement(
        bell_ann, bell=lambda a: bells.append(a) or True)
    assert delivered.delivered is True
    assert delivered.outcome == "delivered"
    assert bells == [bell_ann]
    os_ann = announcement_for(_job())
    delivered = deliver_announcement(
        os_ann, notify=lambda t, m: notes.append((t, m)) or True)
    assert delivered.delivered is True
    assert notes == [("Mythic: job-test", os_ann.message)]
    assert delivered.to_record()["channel"] == "os_notification"


def test_delivery_never_fakes_an_untravelled_road():
    calls = []
    unknown_ann = announcement_for(_job(
        outcome="failed", duration_seconds=5,
        os_backend="unknown", bell_backend=None,
        failure_action="check the named log first"))
    delivered = deliver_announcement(
        unknown_ann,
        bell=lambda a: calls.append(a) or True,
        notify=lambda t, m: calls.append((t, m)) or True)
    assert delivered.outcome == "unknown"
    assert delivered.delivered is False
    assert calls == []
    os_ann = announcement_for(_job())
    refused = deliver_announcement(
        os_ann, notify=lambda t, m: False)
    assert refused.outcome == "unavailable"
    assert "posted nothing" in refused.reason
    bell_ann = announcement_for(_job(os_backend=None))
    refused = deliver_announcement(bell_ann, bell=lambda a: False)
    assert refused.outcome == "unavailable"
    assert "rang nothing" in refused.reason


def test_view_record_round_trips_and_shows():
    view = _view()
    assert validate_view(_stored_view(view)) == view
    assert view.shows(_job()) is True
    job_view = _view(view_id="view-jobs", seq=2, kind_filter="job")
    assert job_view.shows(_job()) is True
    assert job_view.shows(_channel()) is False
    assert "only ever looks" in view_plain_words(view)
    record = view_record(view)
    assert record["news"] is True
    assert record["type"] == "notifications_manners_view"


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert panel.total_items == 6
    assert panel.total_shown == 6
    assert {c.kind: c.items for c in panel.kind_counts} == {
        "job": 3, "channel": 2, "rule": 1}
    assert panel.row_for("job-test").segment == segment_of(_job())
    built = build_panel(panel.to_record(), book)
    assert built.rows == panel.rows
    stored = panel.to_record()
    stored["rows"][0]["segment"] = "written by hand"
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    row = build_row(item=_job())
    assert row.item_id == "job-test"
    assert validate_row(row.to_record(), _job()) == row


def test_verdict_is_derived_from_the_shown_items():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.total_items == 6
    assert verdict.total_shown == 6
    assert verdict.passing_shown == 3
    assert verdict.distinct_kinds == 3
    assert verdict.verdict == "strained"
    assert build_verdict(verdict.to_record(), book) == verdict
    stored = verdict.to_record()
    stored["verdict"] = "open"
    with pytest.raises(ValueError):
        validate_verdict(stored, book)
    jobs_only = derive_verdict(book, _view(kind_filter="job"))
    assert jobs_only.total_shown == 3
    assert jobs_only.passing_shown == 1


def test_verdict_open_and_shut_edges():
    whole = _book()
    assert derive_verdict(whole).verdict == "open"
    broken = _book(
        jobs=[_job(outcome="running", duration_seconds=1)],
        channels=[_channel(backend=None)], rules=[])
    assert derive_verdict(broken).verdict == "shut"
    empty = _book(jobs=[], channels=[], rules=[])
    verdict = derive_verdict(empty)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"


def test_shown_and_kind_readings():
    book = _mixed_book()
    assert [i.item_id for i in shown_items(book)] == [
        "job-test", "job-held", "job-broken",
        "channel-test", "channel-dark", "rule-test"]
    assert [i.item_id for i in items_for_kind(book, "task")] == [
        "job-test", "job-held", "job-broken"]
    assert [i.item_id for i in items_for_kind(book, "law")] == [
        "rule-test"]
    assert [i.item_id for i in passing_items(book)] == [
        "job-test", "channel-test", "rule-test"]
    assert total_items(book) == 6
    assert [i.item_id for i in shown_items(
        book, _view(kind_filter="channel"))] == [
            "channel-test", "channel-dark"]


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(jobs=[_job(), _job(seq=2)])
    with pytest.raises(ValueError):
        _book(rules=[
            _rule(),
            _rule(rule_id="rule-two", seq=2)])
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / NOTIFICATIONS_MANNERS_RESOURCE
    ).read_text(encoding="utf-8"))
    raw["verdict"] = "strained"
    with pytest.raises(ValueError):
        load_notifications_manners(raw)
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / NOTIFICATIONS_MANNERS_RESOURCE
    ).read_text(encoding="utf-8"))
    raw["schema"] = "mythic.other/9"
    with pytest.raises(ValueError):
        load_notifications_manners(raw)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "notifications_manners.yaml").read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    data["guide"]["title"] = "A manners book from a file"
    data["jobs"][0]["job_id"] = "job-from-file"
    data["panels"][0]["rows"][0]["item_id"] = "job-from-file"
    data["panels"][0]["rows"][0]["label"] = "job-from-file"
    data["panels"][0]["rows"][0]["segment"] = (
        "job-from-file: job completed after 1500s, decision "
        "announce, channel os_notification")
    path = tmp_path / "manners.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    book = load_notifications_manners_file(path)
    assert book.title == "A manners book from a file"
    assert book.job_ids()[0] == "job-from-file"


def test_registry_holds_items_and_views_one_by_one():
    registry = NoticeRegistry()
    registry.register_job(_job())
    registry.register_channel(_channel())
    registry.register_rule(_rule())
    view = registry.register_view(_view(view_id=None))
    assert view.view_id == "view-1"
    assert registry.get_job("job-test").outcome == "completed"
    assert registry.get_channel("channel-test").name == "terminal_bell"
    assert registry.get_rule("rule-test").name == "silence_by_default"
    assert registry.latest_view() is view
    with pytest.raises(ValueError):
        registry.register_job(_job(seq=9))
    with pytest.raises(ValueError):
        registry.register_rule(_rule(rule_id="rule-two", seq=2))
    with pytest.raises(KeyError):
        registry.get_job("job-nope")
    book = registry.book()
    assert book.title == "Notifications with Manners"
    assert len(book.items()) == 3
    assert registry.panel().total_shown == 3
    assert registry.verdict().verdict == "open"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = NoticeRegistry()
    book = _book(views=[_view()])
    held = registry.register_book(book)
    assert held.title == "A test manners book"
    assert len(registry.list_items()) == 3
    assert len(registry.list_views()) == 1
    other = _book(views=[_view(view_id="view-two", seq=2)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_records_are_session_news():
    job = job_record(_job())
    assert job["news"] is True
    assert job["type"] == "notifications_manners_job"
    assert "job-test" in job["headline"]
    channel = channel_record(_channel())
    assert channel["type"] == "notifications_manners_channel"
    rule = rule_record(_rule())
    assert rule["type"] == "notifications_manners_rule"
    book = _mixed_book()
    panel = panel_record(derive_panel(book), book)
    assert panel["type"] == "notifications_manners_panel"
    verdict = verdict_record(derive_verdict(book), book)
    assert verdict["type"] == "notifications_manners_verdict"
    whole = book_record(book)
    assert whole["type"] == "notifications_manners_book"
    assert whole["item_count"] == 6


def test_plain_words_and_formatters():
    job = _job()
    assert plain_words(job) == job_plain_words(job)
    assert "announcing once" in plain_words(job)
    short = _job(duration_seconds=3)
    assert "standing silent" in plain_words(short)
    assert "Outcome: completed" in format_job(job)
    assert "Decision: announce" in format_job(job)
    assert "Name: terminal_bell" in format_channel(_channel())
    assert "Statement:" in format_rule(_rule())
    assert "kind 'all'" in format_view(_view())
    book = load_notifications_manners()
    assert "job-morning-build" in format_book(book)
    assert "job-morning-build" in format_book(book, "job")
    assert "channel-terminal-bell" not in format_book(book, "job")
    assert "Panel in Notifications" in format_panel(book)
    assert "strained" in format_verdict(book)
    screen = format_notifications_manners_screen(book)
    assert "Notifications with Manners (M-181)" in screen
    assert "Due announcements: 2" in screen
    assert "strained" in verdict_plain_words(book)
    assert "job-morning-build" in panel_plain_words(book)


def test_parse_args_grammar():
    assert parse_notifications_manners_args("") == ("show", None)
    assert parse_notifications_manners_args(None) == ("show", None)
    assert parse_notifications_manners_args("job job-x") == (
        "job", "job-x")
    assert parse_notifications_manners_args("channel channel-x") == (
        "channel", "channel-x")
    assert parse_notifications_manners_args("rule rule-x") == (
        "rule", "rule-x")
    assert parse_notifications_manners_args("view view-x") == (
        "view", "view-x")
    assert parse_notifications_manners_args("kind task") == (
        "kind", "job")
    assert parse_notifications_manners_args("panel") == ("panel", None)
    assert parse_notifications_manners_args("verdict") == (
        "verdict", None)
    with pytest.raises(ValueError) as excinfo:
        parse_notifications_manners_args("dance party")
    assert str(excinfo.value) == USAGE


def test_inspect_item_source_names_pieces():
    assert inspect_item_source(
        {"outcome": "completed"})["kind"] == "job"
    assert inspect_item_source(
        {"channel_id": "channel-x"})["kind"] == "channel"
    assert inspect_item_source(
        {"statement": "be quiet"})["kind"] == "rule"
    refused = inspect_item_source(
        {"outcome": "completed", "announced": True})
    assert refused["kind"] is None
    assert "derived from identity" in refused["reason"]
    assert inspect_item_source("nope")["kind"] is None
    assert inspect_item_source({})["kind"] is None


# ---------------------------------------------------------------------
# M-181 agent layer: the agent holds a manners
# book for the session, items and views are
# published as session news through the
# checkpoint road (journal first, deduped per
# shape), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, and the announcements that stand
# due are polled and delivered through the seams
# at most once each. This layer rings no real
# bell, posts no real notification, calls no
# model, persists nothing beyond the session
# journal news and banks nothing.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _manners_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "notifications_manners.yaml").read_text(encoding="utf-8")
    path = tmp_path / "notifications_manners.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestNotificationsMannersAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.notifications_manners_status()
        assert status["jobs"] == []
        assert status["channels"] == []
        assert status["rules"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["notifications_manners"]["title"] == EXAMPLE_TITLE
        assert len(status["notifications_manners"]["jobs"]) == 3
        assert len(status["notifications_manners"]["channels"]) == 2
        assert len(status["notifications_manners"]["rules"]) == 2
        assert len(status["notifications_manners"]["views"]) == 2
        assert status["panel"]["total_items"] == 7
        assert status["panel"]["total_shown"] == 7
        assert status["panels"][0]["panel_id"] == "panel-m180-boundary"
        assert status["book_record"]["item_count"] == 7
        assert status["book_record"]["view_count"] == 2
        assert status["verdict"]["verdict"] == "strained"
        assert [a["announcement_key"] for a in status["due"]] == [
            "job-morning-build:completed", "job-night-export:failed"]
        assert "stands as data" in status["plain_words"]
        assert "Notifications with Manners (M-181)" in status["screen"]
        assert "7 of 7 items show" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._notifications_manners_registry()
        assert agent._notifications_manners_registry() is first
        assert agent._notifications_manners_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.notifications_manners_status()
        assert agent.get_job_notice(
            "job-morning-build").outcome == "completed"
        assert agent.get_channel_notice(
            "channel-terminal-bell").name == "terminal_bell"
        assert agent.get_manners_rule(
            "rule-silence-by-default").name == "silence_by_default"
        assert agent.get_notifications_view(
            "view-all").kind_filter == "all"
        assert [i.item_id for i in agent.notifications_manners_with_kind(
            "job")] == [
                "job-morning-build", "job-quick-check",
                "job-night-export"]
        assert [i.item_id for i in agent.notifications_manners_with_kind(
            "road")] == [
                "channel-terminal-bell", "channel-os-notification"]
        assert [i.item_id for i in agent.notifications_manners_passing()] == [
            "job-morning-build", "job-quick-check",
            "channel-terminal-bell", "rule-silence-by-default",
            "rule-failure-names-one-action"]
        agent.notifications_manners_panel()
        agent.notifications_manners_verdict()
        agent.report_notifications_manners()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("notifications_manners")] == []
        with pytest.raises(KeyError):
            agent.get_job_notice("job-nope")
        with pytest.raises(KeyError):
            agent.get_notifications_view("view-nope")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_job_notice(_job())
        status = agent.notifications_manners_status()
        assert [d["job_id"] for d in status["jobs"]] == ["job-test"]
        assert status["book"]["title"] == "Notifications with Manners"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert "job completed after 900s, decision announce" in (
            status["screen"])

    def test_held_item_never_falls_back_to_the_example(
            self, agent):
        agent.register_job_notice(_job())
        with pytest.raises(KeyError):
            agent.get_job_notice("job-morning-build")
        with pytest.raises(KeyError):
            agent.get_notifications_view("view-all")
        job = agent.get_job_notice("job-test")
        assert job.outcome == "completed"
        assert agent.notifications_manners_book().title == (
            "Notifications with Manners")


class TestNotificationsMannersAgentHolding:
    def test_register_job_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_job_notice(_job())
        assert result["job"]["job_id"] == "job-test"
        assert result["record_news"]["type"] == (
            "notifications_manners_job")
        assert "job-test: job completed after 900s" in result["screen"]
        agent.register_channel_notice(_channel())
        events = _manners_events(
            store, session_id, "notifications_manners_job")
        assert len(events) == 1
        agent.close()

    def test_duplicate_job_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_job_notice(_job())
        with pytest.raises(ValueError):
            agent.register_job_notice(_job(seq=9))
        events = _manners_events(
            store, session_id, "notifications_manners_job")
        assert len(events) == 1
        agent.close()

    def test_register_channel_and_rule_hold_and_publish(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        channel = agent.register_channel_notice(_channel())
        assert channel["channel"]["name"] == "terminal_bell"
        rule = agent.register_manners_rule(_rule())
        assert rule["rule"]["name"] == "silence_by_default"
        assert len(_manners_events(
            store, session_id, "notifications_manners_channel")) == 1
        assert len(_manners_events(
            store, session_id, "notifications_manners_rule")) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_notifications_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_manners_events(
            store, session_id, "notifications_manners_view")) == 1
        agent.close()

    def test_view_road_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_job_notice(_job())
        result = agent.view_notifications_manners("job")
        assert result["view"]["kind_filter"] == "job"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == (
            "notifications_manners_panel")
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_manners_events(
            store, session_id, "notifications_manners_view")) == 1
        assert len(_manners_events(
            store, session_id, "notifications_manners_panel")) == 1
        assert len(_manners_events(
            store, session_id, "notifications_manners_verdict")) == 1
        agent.close()

    def test_view_road_over_an_unshown_kind_is_shut(self, agent):
        agent.register_job_notice(_job())
        result = agent.view_notifications_manners("channel")
        assert result["verdict_record"]["verdict"] == "shut"

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_notifications_manners_book(
            _book(views=[_view()]))
        assert result["count"] == 3
        assert [r["type"] for r in result["records_news"]] == [
            "notifications_manners_job",
            "notifications_manners_channel",
            "notifications_manners_rule",
            "notifications_manners_view"]
        assert len(_manners_events(
            store, session_id, "notifications_manners_job")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_notifications_manners_book()
        assert result["count"] == 7
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == (
            "notifications_manners_panel")
        with pytest.raises(ValueError):
            agent.record_notifications_manners_book()
        assert len(_manners_events(
            store, session_id, "notifications_manners_job")) == 3
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_book_file(tmp_path)
        book = load_notifications_manners_file(path)
        result = agent.record_notifications_manners_book(book)
        assert result["count"] == 7
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_notifications_manners()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert "job-morning-build" in report["book_text"]
        agent.register_job_notice(_job())
        report = agent.report_notifications_manners()
        assert report["book"]["title"] == "Notifications with Manners"
        assert report["panel"] is None
        assert report["verdict"] is None

    def test_announce_road_delivers_once_through_fake_seams(
            self, agent):
        agent.register_job_notice(_job(os_backend=None))
        bells = []
        result = agent.announce_notifications(
            bell=lambda a: bells.append(a) or True)
        assert result["count"] == 1
        assert result["deliveries"][0]["outcome"] == "delivered"
        assert [a.key for a in bells] == ["job-test:completed"]
        again = agent.announce_notifications(
            bell=lambda a: bells.append(a) or True)
        assert again["count"] == 0
        assert again["announcements"] == []
        assert len(bells) == 1

    def test_announce_road_on_the_example_book(self, agent):
        notes = []
        result = agent.announce_notifications(
            notify=lambda t, m: notes.append((t, m)) or True)
        assert result["count"] == 2
        outcomes = {d["job_id"]: d["outcome"]
                    for d in result["deliveries"]}
        assert outcomes == {
            "job-morning-build": "delivered",
            "job-night-export": "unknown"}
        assert len(notes) == 1
        assert "job-morning-build" in notes[0][1]
        again = agent.announce_notifications(
            notify=lambda t, m: notes.append((t, m)) or True)
        assert again["count"] == 0
        assert len(notes) == 1


class TestNotificationsMannersTerminalSurface:
    def test_show_job_channel_rule_view_kind_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/manners")
        assert "Notifications with Manners (M-181)" in text
        _, _, text = _slash(agent, "/manners job job-morning-build")
        assert "Outcome: completed" in text
        _, _, text = _slash(
            agent, "/manners channel channel-terminal-bell")
        assert "Backend: terminal_bell" in text
        _, _, text = _slash(
            agent, "/manners rule rule-silence-by-default")
        assert "announce nothing unless" in text
        _, _, text = _slash(agent, "/manners view view-all")
        assert "kind 'all'" in text
        _, _, text = _slash(agent, "/manners kind job")
        assert "job-morning-build" in text
        assert "channel-terminal-bell" not in text
        _, _, text = _slash(agent, "/manners panel")
        assert "Panel in Notifications at the M-180 slice boundary" in text
        _, _, text = _slash(agent, "/manners verdict")
        assert "strained" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/manners [show|job <job-id>"
                "|channel <channel-id>|rule <rule-id>"
                "|view <view-id>|kind <kind>|panel|verdict]") in text
        _, _, text = _slash(agent, "/manners dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/manners job job-nope")
        assert "no job named" in text


@pytest.fixture()
def manners_handler(agent, monkeypatch):
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


def _manners_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestNotificationsMannersCommand:
    def test_show_is_default(self, manners_handler, agent):
        manners_handler._handle_manners("")
        assert "Notifications with Manners (M-181)" in (
            _manners_published_text(manners_handler))

    def test_job_channel_rule_view_kind_panel_verdict(
            self, manners_handler, agent):
        manners_handler._handle_manners("job job-morning-build")
        assert "Outcome: completed" in (
            _manners_published_text(manners_handler))
        manners_handler._handle_manners("channel channel-terminal-bell")
        assert "terminal_bell" in _manners_published_text(
            manners_handler)
        manners_handler._handle_manners("rule rule-silence-by-default")
        assert "silence_by_default" in _manners_published_text(
            manners_handler)
        manners_handler._handle_manners("view view-all")
        assert "kind 'all'" in _manners_published_text(manners_handler)
        manners_handler._handle_manners("kind rule")
        assert "rule-silence-by-default" in _manners_published_text(
            manners_handler)
        manners_handler._handle_manners("panel")
        assert "Panel in Notifications" in (
            _manners_published_text(manners_handler))
        manners_handler._handle_manners("verdict")
        assert "strained" in _manners_published_text(manners_handler)

    def test_bad_grammar_is_published(
            self, manners_handler, agent):
        manners_handler._handle_manners("dance party")
        assert USAGE in _manners_published_text(manners_handler)
        manners_handler._handle_manners("job job-nope")
        assert "no job named" in _manners_published_text(
            manners_handler)


class TestChatScreenRoutingNotificationsManners:
    def test_manners_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/manners panel", _FakeLog())
        assert calls == [("/manners", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/manners[/green] - show notifications with manners (M-181)" in (
            text)
        assert ('"/manners": "Usage: /manners | '
                '/manners job <job-id>') in text
