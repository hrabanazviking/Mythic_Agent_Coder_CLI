"""M-182 The Plain-Language Skin - pure-layer tests.

TIER: integration

The pure layer is the register, held as data: a
report held whole (its title, its technical lines
and the one next step it names), an approval ask
held whole (its title, its ask, its context lines
and exactly the one action that matters), a
stand-up held whole (its person, what they have
done, what they are doing and what stands
blocked), and a plain-words lexicon held as data
(a technical term and the plain everyday words it
is spoken with). The plain rendering is DERIVED
from the held item's own fields at call time,
through the lexicon alone - the plain line is the
technical line with each listed term spoken
plainly, so every number and name stands in both
registers and the facts cannot drift. A watched
term with no lexicon entry is a MISS: it passes
through unchanged, stands named in the item's
misses, and keeps the item from standing whole -
no plain words are invented for it. The register
(jarl or technical) is DERIVED from session or
config state at call time, never stored on any
item, and Jarl mode stands default: in Jarl mode
the technical lines stand FOLDED as data behind
the one named unfold action, never deleted; in
the technical register nothing stands folded. The
panel is derived for one held view and the
verdict is derived for the whole book under one
view. The shipped example book is held in a data
file, and a loader reads a book from any file.
Two rows of the M-171 charter name M-182 - the
setup wizard (S-02) and the subagent editor panel
(S-07), both calling for plain words first - and
this slice is the register those rows call for.
This layer renders words only: it approves
nothing, sends nothing and invents no plain words.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.plain_language_skin import (
    DEFAULT_REGISTER,
    ITEM_KINDS,
    JARL_IS_THE_DEFAULT_REGISTER,
    PLAIN_EXPLANATION,
    PLAIN_LANGUAGE_SKIN_RESOURCE,
    PLAIN_LANGUAGE_SKIN_SCHEMA,
    PLAIN_LANGUAGE_SKIN_SLICE,
    REGISTERS,
    UNFOLD_ACTION,
    USAGE,
    VERDICT_WORDS,
    VIEW_KINDS,
    SkinApproval,
    SkinBook,
    SkinPanel,
    SkinRegistry,
    SkinRendering,
    SkinReport,
    SkinStandup,
    SkinTerm,
    SkinVerdict,
    SkinView,
    approval_plain_words,
    approval_record,
    book_record,
    build_approval,
    build_book,
    build_item,
    build_panel,
    build_report,
    build_row,
    build_standup,
    build_term,
    build_verdict,
    build_view,
    derive_panel,
    derive_register,
    derive_verdict,
    format_approval,
    format_book,
    format_panel,
    format_plain_language_skin_screen,
    format_rendering,
    format_report,
    format_standup,
    format_term,
    format_verdict,
    format_view,
    inspect_item_source,
    item_misses,
    item_passes,
    item_record,
    items_for_kind,
    lexicon_misses,
    load_plain_language_skin,
    load_plain_language_skin_file,
    normalize_kind,
    normalize_kind_filter,
    normalize_register,
    normalize_term,
    panel_plain_words,
    panel_record,
    passing_items,
    plain_for_term,
    plain_lines,
    plain_words,
    render_item,
    rendering_record,
    report_plain_words,
    report_record,
    segment_of,
    shown_items,
    standup_plain_words,
    standup_record,
    technical_lines,
    term_plain_words,
    term_record,
    total_items,
    translate_text,
    unfold_rendering,
    validate_approval,
    validate_book,
    validate_panel,
    validate_report,
    validate_row,
    validate_standup,
    validate_term,
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

EXAMPLE_TITLE = "Plain language at the M-181 slice boundary"

BY = "the coordinator"
ON = "2026-11-09"


def _report(**overrides):
    fields = {
        "report_id": "report-test",
        "seq": 1,
        "title": "Test report",
        "lines": [
            "We will deploy the build once the checkpoint stands."],
        "action": "read the numbers",
        "detail": "A report held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_report(fields)


def _stored_report(report):
    stored = report.to_record()
    for key in ("type", "slice", "kind", "misses", "passes", "segment"):
        stored.pop(key)
    return stored


def _approval(**overrides):
    fields = {
        "approval_id": "approval-test",
        "seq": 1,
        "title": "Test approval",
        "ask": "Shall we deploy the build today?",
        "action": "deploy the build",
        "lines": ["The checkpoint stands ready."],
        "detail": "An approval held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_approval(fields)


def _stored_approval(approval):
    stored = approval.to_record()
    for key in ("type", "slice", "kind", "misses", "passes", "segment"):
        stored.pop(key)
    return stored


def _standup(**overrides):
    fields = {
        "standup_id": "standup-test",
        "seq": 1,
        "person": "yrsa",
        "done": ["The checkpoint notes are filed."],
        "doing": ["Walking the crew through the deploy."],
        "blocked": [],
        "detail": "A stand-up held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_standup(fields)


def _stored_standup(standup):
    stored = standup.to_record()
    for key in ("type", "slice", "kind", "misses", "passes", "segment"):
        stored.pop(key)
    return stored


def _term(**overrides):
    fields = {
        "term_id": "term-test",
        "seq": 1,
        "term": "deploy",
        "plain": "send out",
        "detail": "A lexicon term held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_term(fields)


def _stored_term(term):
    stored = term.to_record()
    for key in ("type", "slice", "kind", "passes", "segment"):
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


def _stored_panel(panel):
    stored = panel.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    return stored


def _stored_verdict(verdict):
    stored = verdict.to_record()
    for key in ("type", "slice"):
        stored.pop(key)
    return stored


def _book(reports=None, approvals=None, standups=None,
          terms=None, views=None, watched=None, **overrides):
    fields = {
        "schema": PLAIN_LANGUAGE_SKIN_SCHEMA,
        "slice": "M-182",
        "guide": {"title": "A test skin book"},
        "reports": [_stored_report(item) for item in (
            reports if reports is not None else [_report()])],
        "approvals": [_stored_approval(item) for item in (
            approvals if approvals is not None else [_approval()])],
        "standups": [_stored_standup(item) for item in (
            standups if standups is not None else [_standup()])],
        "terms": [_stored_term(item) for item in (
            terms if terms is not None else [
                _term(),
                _term(term_id="term-checkpoint", seq=2,
                      term="checkpoint",
                      plain="saved stopping point")])],
        "watched": (watched if watched is not None else [
            "deploy", "checkpoint", "quorum"]),
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(
        reports=[
            _report(),
            _report(
                report_id="report-held", seq=2,
                lines=["The quorum check passed."]),
        ],
        approvals=[_approval()],
        standups=[_standup()],
        terms=[
            _term(),
            _term(term_id="term-checkpoint", seq=2,
                  term="checkpoint", plain="saved stopping point"),
        ])


# ---------------------------------------------------------------------
# The shipped example book, the roadmap and the charter.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_plain_language_skin()
    assert book.title == EXAMPLE_TITLE
    assert book.report_ids() == (
        "report-morning-build", "report-usage")
    assert book.approval_ids() == (
        "approval-release", "approval-wipe")
    assert book.standup_ids() == ("standup-yrsa", "standup-tess")
    assert book.term_ids() == (
        "term-checkpoint", "term-deploy", "term-idempotent",
        "term-latency", "term-rollback", "term-throughput")
    assert book.watched == (
        "checkpoint", "deploy", "idempotent", "latency",
        "quorum", "rollback", "throughput")
    assert [v.view_id for v in book.views] == [
        "view-all", "view-report"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m181-boundary"
    assert panel.as_of == "2026-11-09"
    assert [row.item_id for row in panel.rows] == [
        "report-morning-build", "report-usage",
        "approval-release", "approval-wipe",
        "standup-yrsa", "standup-tess",
        "term-checkpoint", "term-deploy", "term-idempotent",
        "term-latency", "term-rollback", "term-throughput"]
    derived = derive_panel(book, "view-all")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 12
    assert panel.total_shown == derived.total_shown == 12
    assert {c.kind: c.items for c in panel.kind_counts} == {
        "report": 2, "approval": 2, "standup": 2, "term": 6}
    assert derive_verdict(book, "view-all").verdict == "strained"
    assert derive_verdict(book, "view-all").passing_shown == 9
    assert derive_verdict(book, "view-report").verdict == "strained"
    assert derive_verdict(book, "view-report").passing_shown == 1
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / PLAIN_LANGUAGE_SKIN_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == PLAIN_LANGUAGE_SKIN_SCHEMA
    assert raw["slice"] == "M-182"
    assert "verdict" not in raw
    assert "register" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-182")]
    assert slice_.title == "The plain-language skin"
    assert slice_.part == 8
    assert "Jarl mode" in slice_.summary
    assert "plain everyday words" in slice_.summary
    assert "folded behind a keypress" in slice_.summary
    assert PLAIN_LANGUAGE_SKIN_SLICE == "M-182"


def test_charter_names_m182_on_two_rows():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-182" in owners
    assert "M-182" in charter.screen("setup_wizard").owning_slices
    assert "M-182" in charter.screen(
        "subagent_editor").owning_slices


def test_closed_vocabularies():
    assert ITEM_KINDS == ("report", "approval", "standup", "term")
    assert VIEW_KINDS == ("all",) + ITEM_KINDS
    assert REGISTERS == ("jarl", "technical")
    assert DEFAULT_REGISTER == "jarl"
    assert JARL_IS_THE_DEFAULT_REGISTER is True
    assert UNFOLD_ACTION == "unfold"
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert normalize_kind("REPORTS") == "report"
    assert normalize_kind("ask") == "approval"
    assert normalize_kind("stand-up") == "standup"
    assert normalize_kind("lexicon") == "term"
    assert normalize_kind_filter("ALL") == "all"
    assert normalize_kind_filter("terms") == "term"
    assert normalize_term("Latency") == "latency"
    assert normalize_register("everyday") == "jarl"
    assert normalize_register("plain") == "jarl"
    assert normalize_register("tech") == "technical"
    assert normalize_register("full") == "technical"
    assert normalize_register(True) == "jarl"
    assert normalize_register(False) == "technical"
    with pytest.raises(ValueError):
        normalize_kind("whenever")
    with pytest.raises(ValueError):
        normalize_register("loud")
    assert "Jarl mode" in PLAIN_EXPLANATION
    assert "folded" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /skin")


def test_shipped_book_judged_honestly_as_data():
    book = load_plain_language_skin()
    morning = book.report_for("report-morning-build")
    assert item_passes(morning, book) is True
    assert item_misses(morning, book) == ()
    assert plain_lines(morning, book)[0] == (
        "We will send out the build once the saved "
        "stopping point stands.")
    assert plain_lines(morning, book)[1] == (
        "The build held waiting time steady at 42 and "
        "work rate steady at 18 slices an hour.")
    assert technical_lines(morning)[-1] == (
        "next step: read the morning numbers")
    usage = book.report_for("report-usage")
    assert item_misses(usage, book) == ("quorum",)
    assert item_passes(usage, book) is False
    assert plain_lines(usage, book)[0] == technical_lines(usage)[0]
    release = book.approval_for("approval-release")
    assert item_passes(release, book) is True
    wipe = book.approval_for("approval-wipe")
    assert item_misses(wipe, book) == ("quorum",)
    assert item_passes(wipe, book) is False
    yrsa = book.standup_for("standup-yrsa")
    assert item_passes(yrsa, book) is True
    tess = book.standup_for("standup-tess")
    assert item_misses(tess, book) == ("quorum",)
    assert item_passes(tess, book) is False
    for term in book.terms:
        assert item_passes(term, book) is True
    assert [i.item_id for i in passing_items(book)] == [
        "report-morning-build", "approval-release", "standup-yrsa",
        "term-checkpoint", "term-deploy", "term-idempotent",
        "term-latency", "term-rollback", "term-throughput"]
    assert total_items(book) == 12
    assert lexicon_misses(book) == ("quorum",)
    assert plain_for_term("quorum", book) is None
    assert plain_for_term("deploy", book) == "send out"
    assert segment_of(morning, book) == (
        "report-morning-build: report says 'We will deploy "
        "the build once the checkpoint stands.' - plainly: "
        "'We will send out the build once the saved stopping "
        "point stands.' - misses: none")


# ---------------------------------------------------------------------
# The held items: judged whole, their renderings derived.
# ---------------------------------------------------------------------


def test_report_record_round_trips():
    report = _report()
    assert validate_report(_stored_report(report)) == report
    record = report_record(report, {"deploy": "send out"})
    assert record["type"] == "plain_language_report"
    assert record["slice"] == "M-182"
    assert record["passes"] is True
    assert record["misses"] == []
    assert "send out" in record["segment"]
    with pytest.raises(ValueError) as excinfo:
        _report(lines=[])
    assert "names no lines" in str(excinfo.value)


def test_items_refuse_stored_judgements():
    stored = _stored_report(_report())
    stored["register"] = "jarl"
    with pytest.raises(ValueError) as excinfo:
        validate_report(stored)
    assert "stored judgements" in str(excinfo.value)
    stored = _stored_report(_report())
    stored["mode"] = "technical"
    with pytest.raises(ValueError):
        validate_report(stored)
    stored = _stored_report(_report())
    stored["plain"] = "written by hand"
    with pytest.raises(ValueError):
        validate_report(stored)
    stored = _stored_report(_report())
    stored["surprise"] = "x"
    with pytest.raises(ValueError) as excinfo:
        validate_report(stored)
    assert "unknown fields" in str(excinfo.value)


def test_approval_names_exactly_one_action_or_refuses():
    approval = _approval()
    assert validate_approval(_stored_approval(approval)) == approval
    assert approval.action == "deploy the build"
    stored = _stored_approval(approval)
    del stored["action"]
    with pytest.raises(ValueError) as excinfo:
        validate_approval(stored)
    assert "names no action" in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        _approval(action=["deploy the build", "wipe the shelf"])
    assert "exactly the one" in str(excinfo.value)
    record = approval_record(approval)
    assert record["type"] == "plain_language_approval"
    assert record["action"] == "deploy the build"


def test_standup_record_round_trips_and_needs_work_in_hand():
    standup = _standup()
    assert validate_standup(_stored_standup(standup)) == standup
    assert standup.person == "yrsa"
    with pytest.raises(ValueError) as excinfo:
        _standup(doing=[])
    assert "names nothing doing" in str(excinfo.value)
    record = standup_record(standup)
    assert record["type"] == "plain_language_standup"
    assert record["doing"] == ["Walking the crew through the deploy."]


def test_term_record_round_trips_and_the_lexicon_is_data():
    term = _term()
    assert validate_term(_stored_term(term)) == term
    assert term.term == "deploy"
    assert term.plain == "send out"
    record = term_record(term)
    assert record["type"] == "plain_language_term"
    assert record["passes"] is True
    assert plain_for_term("deploy", {"deploy": "send out"}) == (
        "send out")
    assert plain_for_term("quorum", {"deploy": "send out"}) is None
    assert term_plain_words(term) == "deploy in plain words: send out"


def test_translation_derives_plain_from_technical_alone():
    lexicon = {"deploy": "send out", "latency": "waiting time"}
    line = "We will deploy 3 builds and hold latency at 42."
    plain = translate_text(line, lexicon)
    assert plain == "We will send out 3 builds and hold waiting time at 42."
    assert translate_text(line, {}) == line
    assert translate_text(line, None) == line
    report = _report()
    assert plain_lines(report, lexicon)[0] == (
        "We will send out the build once the checkpoint stands.")
    assert plain_words(report, lexicon) == plain_lines(report, lexicon)[0]
    assert report_plain_words(report, lexicon).startswith(
        "Report 'Test report':")


def test_register_is_derived_never_stored():
    assert derive_register() == "jarl"
    assert derive_register(None) == "jarl"
    assert derive_register("technical") == "technical"
    assert derive_register({}) == "jarl"
    assert derive_register({"register": "technical"}) == "technical"
    assert derive_register({"mode": "plain"}) == "jarl"
    assert derive_register({"jarl_mode": False}) == "technical"
    assert derive_register({"jarl_mode": True}) == "jarl"

    class _Cfg:
        config = {"register": "technical"}
    assert derive_register(_Cfg()) == "technical"

    class _Named:
        register = "technical"
    assert derive_register(_Named()) == "technical"
    assert derive_register(object()) == "jarl"


def test_rendering_folds_in_jarl_and_unfolds_whole():
    book = load_plain_language_skin()
    morning = book.report_for("report-morning-build")
    rendering = render_item(morning, book)
    assert rendering.register == "jarl"
    assert rendering.shown == plain_lines(morning, book)
    assert rendering.folded == technical_lines(morning)
    assert rendering.misses == ()
    assert rendering.action == "read the morning numbers"
    unfolded = unfold_rendering(rendering)
    assert unfolded.folded == ()
    assert unfolded.shown == rendering.shown + rendering.folded
    assert unfold_rendering(unfolded) == unfolded
    technical = render_item(morning, book, register="technical")
    assert technical.register == "technical"
    assert technical.shown == technical_lines(morning)
    assert technical.folded == ()
    assert unfold_rendering(technical) == technical
    usage = book.report_for("report-usage")
    missed = render_item(usage, book)
    assert missed.misses == ("quorum",)
    assert missed.shown[0] == technical_lines(usage)[0]
    record = rendering_record(rendering)
    assert record["type"] == "plain_language_rendering"
    assert record["register"] == "jarl"
    text = format_rendering(rendering)
    assert "Folded detail: 3 technical line(s) stand folded" in text
    assert "unfold unfolds them" in text


def test_view_record_round_trips():
    view = _view()
    assert validate_view(_stored_view(view)) == view
    assert view_plain_words(view) == "View view-test shows kind 'all'."
    record = view_record(view)
    assert record["type"] == "plain_language_view"
    assert record["kind_filter"] == "all"


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert panel.panel_id == "panel-view-test"
    assert panel.total_items == 6
    assert panel.total_shown == 6
    assert {c.kind: c.items for c in panel.kind_counts} == {
        "report": 2, "approval": 1, "standup": 1, "term": 2}
    assert panel.rows[0].segment == segment_of(_report(), book)
    built = build_panel(_stored_panel(panel), book)
    assert built.rows == panel.rows
    assert built.account == panel.account
    stored = _stored_panel(panel)
    stored["rows"][0]["segment"] = "written by hand"
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    row = build_row(item=_report(), source=book)
    assert row.item_id == "report-test"
    assert row.label == "Test report"
    assert validate_row(row.to_record(), _report(), book) == row
    shipped = load_plain_language_skin()
    pinned = _stored_panel(shipped.panels[0])
    assert pinned["panel_id"] == "panel-m181-boundary"
    judged = validate_panel(pinned, shipped)
    assert judged.rows == shipped.panels[0].rows


def test_verdict_is_derived_from_the_shown_items():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.total_items == 6
    assert verdict.total_shown == 6
    assert verdict.passing_shown == 5
    assert verdict.distinct_kinds == 4
    assert verdict.verdict == "strained"
    assert build_verdict(_stored_verdict(verdict), book) == verdict
    stored = _stored_verdict(verdict)
    stored["verdict"] = "open"
    with pytest.raises(ValueError):
        validate_verdict(stored, book)
    reports_only = derive_verdict(book, "view-test")
    assert reports_only.total_shown == 6
    book2 = _book(views=[
        _view(), _view(view_id="view-reports", seq=2,
                       kind_filter="report")])
    only = derive_verdict(book2, "view-reports")
    assert only.total_shown == 1
    assert only.passing_shown == 1
    assert only.verdict == "open"


def test_verdict_open_and_shut_edges():
    whole = _book()
    assert derive_verdict(whole).verdict == "open"
    broken = _book(reports=[
        _report(lines=["The quorum check passed."])])
    assert derive_verdict(broken).verdict == "strained"
    shut = _book(
        reports=[_report(lines=["The quorum check passed."])],
        approvals=[], standups=[], terms=[])
    assert derive_verdict(shut).verdict == "shut"
    empty = _book(reports=[], approvals=[], standups=[], terms=[])
    verdict = derive_verdict(empty)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"
    assert verdict.earliest_on is None


def test_shown_and_kind_readings():
    book = _mixed_book()
    assert [i.item_id for i in shown_items(book)] == [
        "report-test", "report-held", "approval-test",
        "standup-test", "term-test", "term-checkpoint"]
    assert [i.item_id for i in items_for_kind(book, "reports")] == [
        "report-test", "report-held"]
    assert [i.item_id for i in items_for_kind(book, "ask")] == [
        "approval-test"]
    assert [i.item_id for i in items_for_kind(book, "lexicon")] == [
        "term-test", "term-checkpoint"]
    assert [i.item_id for i in passing_items(book)] == [
        "report-test", "approval-test", "standup-test",
        "term-test", "term-checkpoint"]
    assert total_items(book) == 6


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(reports=[_report(), _report(seq=2)])
    with pytest.raises(ValueError):
        _book(reports=[_report(), _report(report_id="report-two")])
    with pytest.raises(ValueError):
        _book(terms=[
            _term(),
            _term(term_id="term-two", seq=2)])
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / PLAIN_LANGUAGE_SKIN_RESOURCE
    ).read_text(encoding="utf-8"))
    raw["verdict"] = "strained"
    with pytest.raises(ValueError):
        load_plain_language_skin(raw)
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / PLAIN_LANGUAGE_SKIN_RESOURCE
    ).read_text(encoding="utf-8"))
    raw["schema"] = "mythic.other/9"
    with pytest.raises(ValueError):
        load_plain_language_skin(raw)
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / PLAIN_LANGUAGE_SKIN_RESOURCE
    ).read_text(encoding="utf-8"))
    raw["guide"]["title"] = "Another title"
    with pytest.raises(ValueError):
        validate_book(raw, require_example=True)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "plain_language_skin.yaml").read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    data["guide"]["title"] = "A skin book from a file"
    data["reports"][0]["report_id"] = "report-from-file"
    data["panels"][0]["rows"][0]["item_id"] = "report-from-file"
    data["panels"][0]["rows"][0]["segment"] = (
        "report-from-file: report says 'We will deploy the "
        "build once the checkpoint stands.' - plainly: 'We "
        "will send out the build once the saved stopping "
        "point stands.' - misses: none")
    path = tmp_path / "skin.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    book = load_plain_language_skin_file(path)
    assert book.title == "A skin book from a file"
    assert book.report_ids()[0] == "report-from-file"


def test_registry_holds_items_and_views_one_by_one():
    registry = SkinRegistry()
    registry.register_report(_report())
    registry.register_approval(_approval())
    registry.register_standup(_standup())
    registry.register_term(_term())
    view = registry.register_view({
        "seq": 1, "kind_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON, "actor": BY,
        "source": "test source", "origin_session": "session-test"})
    assert view.view_id == "view-1"
    assert registry.get_report("report-test").title == "Test report"
    assert registry.get_approval("approval-test").action == (
        "deploy the build")
    assert registry.get_standup("standup-test").person == "yrsa"
    assert registry.get_term("term-test").term == "deploy"
    assert registry.get_item("approval-test").kind == "approval"
    assert registry.watched() == ()
    with pytest.raises(ValueError):
        registry.register_report(_report(seq=9))
    with pytest.raises(ValueError):
        registry.register_term(_term(term_id="term-two", seq=2))
    with pytest.raises(KeyError):
        registry.get_report("report-nope")
    book = registry.book()
    assert book.title == "An unheld skin book"
    assert len(book.items()) == 4
    assert derive_verdict(book, view).verdict == "open"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = SkinRegistry()
    book = _book()
    held = registry.register_book(book)
    assert held.title == "A test skin book"
    assert len(registry.list_items()) == 5
    assert len(registry.list_views()) == 1
    assert registry.watched() == ("deploy", "checkpoint", "quorum")
    other = _book(views=[_view(view_id="view-two", seq=2)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_records_are_session_news():
    report = report_record(_report())
    assert report["type"] == "plain_language_report"
    assert report["report_id"] == "report-test"
    approval = approval_record(_approval())
    assert approval["type"] == "plain_language_approval"
    standup = standup_record(_standup())
    assert standup["type"] == "plain_language_standup"
    term = term_record(_term())
    assert term["type"] == "plain_language_term"
    book = _mixed_book()
    panel = panel_record(derive_panel(book))
    assert panel["type"] == "plain_language_panel"
    verdict = verdict_record(derive_verdict(book))
    assert verdict["type"] == "plain_language_verdict"
    assert verdict["verdict"] == "strained"
    whole = book_record(book)
    assert whole["type"] == "plain_language_book"
    assert len(whole["reports"]) == 2
    assert whole["watched"] == ["deploy", "checkpoint", "quorum"]
    one = item_record(_approval(), book)
    assert one["type"] == "plain_language_approval"


def test_plain_words_and_formatters():
    book = load_plain_language_skin()
    morning = book.report_for("report-morning-build")
    assert plain_words(morning, book) == (
        "We will send out the build once the saved "
        "stopping point stands.")
    release = book.approval_for("approval-release")
    assert approval_plain_words(release, book) == (
        "Approval asks plainly: Shall we send out the build "
        "to the live shelf today? The one action: send out "
        "the build.")
    yrsa = book.standup_for("standup-yrsa")
    assert standup_plain_words(yrsa, book) == (
        "yrsa is doing: Walking the crew through how we "
        "send out the build.")
    assert "Report: report-morning-build" in format_report(morning, book)
    assert "Next step: read the morning numbers" in format_report(
        morning, book)
    assert "The one action: send out the build" in format_approval(
        release, book)
    assert "Doing: Walking the crew through how we send out" in (
        format_standup(yrsa, book))
    assert "In plain words: send out" in format_term(
        book.term_for("term-deploy"))
    assert "kind 'all'" in format_view(book.view_for("view-all"))
    assert "report-morning-build" in format_book(book)
    assert "report-morning-build" in format_book(book, "report")
    assert "standup-yrsa" not in format_book(book, "report")
    assert "Panel in Plain language" in format_panel(book)
    assert "strained" in format_verdict(book)
    screen = format_plain_language_skin_screen(book)
    assert "The Plain-Language Skin (M-182)" in screen
    assert "Lexicon misses: quorum." in screen
    assert "Verdict: strained." in screen
    assert "Register: jarl" in screen
    assert "12 of 12 items" in panel_plain_words(book)
    assert "9 of 12" in verdict_plain_words(book)
    assert "strained" in verdict_plain_words(book)


def test_parse_args_grammar():
    from mythic_agent.core.plain_language_skin import (
        parse_plain_language_skin_args)
    assert parse_plain_language_skin_args("") == ("show", None)
    assert parse_plain_language_skin_args(None) == ("show", None)
    assert parse_plain_language_skin_args("list") == ("show", None)
    assert parse_plain_language_skin_args("report report-x") == (
        "report", "report-x")
    assert parse_plain_language_skin_args("approval approval-x") == (
        "approval", "approval-x")
    assert parse_plain_language_skin_args("standup standup-x") == (
        "standup", "standup-x")
    assert parse_plain_language_skin_args("term term-x") == (
        "term", "term-x")
    assert parse_plain_language_skin_args("view view-x") == (
        "view", "view-x")
    assert parse_plain_language_skin_args("kind reports") == (
        "kind", "report")
    assert parse_plain_language_skin_args("panel") == ("panel", None)
    assert parse_plain_language_skin_args("verdict") == ("verdict", None)
    assert parse_plain_language_skin_args("unfold report-x") == (
        "unfold", "report-x")
    assert parse_plain_language_skin_args("register") == (
        "register", None)
    with pytest.raises(ValueError) as excinfo:
        parse_plain_language_skin_args("dance party")
    assert str(excinfo.value) == USAGE


def test_inspect_item_source_names_pieces():
    assert inspect_item_source(
        {"report_id": "report-x"})["kind"] == "report"
    assert inspect_item_source(
        {"lines": ["a line"]})["kind"] == "report"
    assert inspect_item_source(
        {"approval_id": "approval-x"})["kind"] == "approval"
    assert inspect_item_source(
        {"ask": "shall we?"})["kind"] == "approval"
    assert inspect_item_source(
        {"standup_id": "standup-x"})["kind"] == "standup"
    assert inspect_item_source(
        {"doing": ["a line"]})["kind"] == "standup"
    assert inspect_item_source(
        {"term": "deploy", "plain": "send out"})["kind"] == "term"
    assert build_item({"term": "deploy", "plain": "send out",
                       "term_id": "term-x", "seq": 1,
                       "detail": "A term, for the tests.",
                       "recorded_on": ON, "actor": BY,
                       "source": "test source",
                       "origin_session": "session-test"}).term == (
        "deploy")
    refused = inspect_item_source(
        {"lines": ["a line"], "passes": True})
    assert refused["kind"] is None
    assert "stored judgements" in refused["reason"]
    assert inspect_item_source("nope")["kind"] is None
    assert inspect_item_source({})["kind"] is None


# ---------------------------------------------------------------------
# M-182 agent layer: the agent holds a skin book
# for the session, items and views are published
# as session news through the checkpoint road
# (journal first, deduped per shape), the panel
# and verdict are derived at call time from the
# whole book under a view, never held, the
# register is derived from the agent's config at
# call time, and the render/unfold roads speak
# the pure layer's renderings. This layer calls
# no model, approves nothing, sends nothing and
# persists nothing beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _skin_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "plain_language_skin.yaml").read_text(encoding="utf-8")
    path = tmp_path / "plain_language_skin.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestPlainLanguageSkinAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.plain_language_skin_status()
        assert status["reports"] == []
        assert status["approvals"] == []
        assert status["standups"] == []
        assert status["terms"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["plain_language_skin"]["title"] == EXAMPLE_TITLE
        assert len(status["plain_language_skin"]["reports"]) == 2
        assert len(status["plain_language_skin"]["approvals"]) == 2
        assert len(status["plain_language_skin"]["standups"]) == 2
        assert len(status["plain_language_skin"]["terms"]) == 6
        assert len(status["plain_language_skin"]["views"]) == 2
        assert status["panel"]["total_items"] == 12
        assert status["panel"]["total_shown"] == 12
        assert status["panels"][0]["panel_id"] == "panel-m181-boundary"
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["passing_shown"] == 9
        assert status["register"] == "jarl"
        assert status["lexicon_misses"] == ["quorum"]
        assert "work rate" in status["plain_words"]
        assert "The Plain-Language Skin (M-182)" in status["screen"]
        assert "12 of 12 items show" in status["screen"] or (
            "12 of 12" in status["screen"])
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._plain_language_skin_registry()
        assert agent._plain_language_skin_registry() is first
        assert agent._plain_language_skin_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.plain_language_skin_status()
        assert agent.get_skin_report(
            "report-morning-build").title == "Morning build report"
        assert agent.get_skin_approval(
            "approval-release").action == "deploy the build"
        assert agent.get_skin_standup("standup-yrsa").person == "yrsa"
        assert agent.get_skin_term("term-deploy").plain == "send out"
        assert agent.get_skin_view("view-all").kind_filter == "all"
        assert [i.item_id for i in agent.plain_language_skin_with_kind(
            "report")] == ["report-morning-build", "report-usage"]
        assert len(agent.plain_language_skin_with_kind(
            "lexicon")) == 6
        assert [i.item_id for i in agent.plain_language_skin_passing()] == [
            "report-morning-build", "approval-release", "standup-yrsa",
            "term-checkpoint", "term-deploy", "term-idempotent",
            "term-latency", "term-rollback", "term-throughput"]
        agent.plain_language_skin_panel()
        agent.plain_language_skin_verdict()
        agent.report_plain_language_skin()
        agent.render_plain_language_skin_item("report-morning-build")
        agent.unfold_plain_language_skin_item("report-morning-build")
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("plain_language")] == []
        with pytest.raises(KeyError):
            agent.get_skin_report("report-nope")
        with pytest.raises(KeyError):
            agent.get_skin_view("view-nope")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_skin_report(_report())
        status = agent.plain_language_skin_status()
        assert [d["report_id"] for d in status["reports"]] == [
            "report-test"]
        assert status["book"]["title"] == "An unheld skin book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert "report-test" in status["screen"]

    def test_held_item_never_falls_back_to_the_example(
            self, agent):
        agent.register_skin_report(_report())
        with pytest.raises(KeyError):
            agent.get_skin_report("report-morning-build")
        with pytest.raises(KeyError):
            agent.get_skin_view("view-all")
        report = agent.get_skin_report("report-test")
        assert report.title == "Test report"
        assert agent.plain_language_skin_book().title == (
            "An unheld skin book")


class TestPlainLanguageSkinAgentHolding:
    def test_register_report_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_skin_report(_report())
        assert result["report"]["report_id"] == "report-test"
        assert result["record_news"]["type"] == "plain_language_report"
        assert "report-test" in result["screen"]
        agent.register_skin_approval(_approval())
        events = _skin_events(store, session_id, "plain_language_report")
        assert len(events) == 1
        agent.close()

    def test_duplicate_report_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_skin_report(_report())
        with pytest.raises(ValueError):
            agent.register_skin_report(_report(seq=9))
        events = _skin_events(store, session_id, "plain_language_report")
        assert len(events) == 1
        agent.close()

    def test_register_approval_standup_and_term_hold_and_publish(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        approval = agent.register_skin_approval(_approval())
        assert approval["approval"]["action"] == "deploy the build"
        standup = agent.register_skin_standup(_standup())
        assert standup["standup"]["person"] == "yrsa"
        term = agent.register_skin_term(_term())
        assert term["term"]["term"] == "deploy"
        with pytest.raises(ValueError):
            agent.register_skin_term(
                _term(term_id="term-two", seq=2))
        assert len(_skin_events(
            store, session_id, "plain_language_approval")) == 1
        assert len(_skin_events(
            store, session_id, "plain_language_standup")) == 1
        assert len(_skin_events(
            store, session_id, "plain_language_term")) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_skin_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_skin_events(
            store, session_id, "plain_language_view")) == 1
        agent.close()

    def test_view_road_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_skin_report(_report())
        result = agent.view_plain_language_skin("report")
        assert result["view"]["kind_filter"] == "report"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "plain_language_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_skin_events(
            store, session_id, "plain_language_view")) == 1
        assert len(_skin_events(
            store, session_id, "plain_language_panel")) == 1
        assert len(_skin_events(
            store, session_id, "plain_language_verdict")) == 1
        agent.close()

    def test_view_road_over_an_unshown_kind_is_shut(self, agent):
        agent.register_skin_report(_report())
        result = agent.view_plain_language_skin("term")
        assert result["verdict_record"]["verdict"] == "shut"

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_plain_language_skin_book(
            _book(views=[_view()]))
        assert result["count"] == 5
        assert [r["type"] for r in result["records_news"]] == [
            "plain_language_report",
            "plain_language_approval",
            "plain_language_standup",
            "plain_language_term",
            "plain_language_term",
            "plain_language_view"]
        assert len(_skin_events(
            store, session_id, "plain_language_report")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_plain_language_skin_book()
        assert result["count"] == 12
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "plain_language_panel"
        with pytest.raises(ValueError):
            agent.record_plain_language_skin_book()
        assert len(_skin_events(
            store, session_id, "plain_language_report")) == 2
        assert len(_skin_events(
            store, session_id, "plain_language_term")) == 6
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_book_file(tmp_path)
        book = load_plain_language_skin_file(path)
        result = agent.record_plain_language_skin_book(book)
        assert result["count"] == 12
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_plain_language_skin()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert report["register"] == "jarl"
        assert "report-morning-build" in report["book_text"]
        agent.register_skin_report(_report())
        report = agent.report_plain_language_skin()
        assert report["book"]["title"] == "An unheld skin book"
        assert report["panel"] is None
        assert report["verdict"] is None

    def test_register_is_derived_from_the_agent_config(self, agent):
        assert agent.plain_language_skin_register() == "jarl"
        agent.config["register"] = "technical"
        assert agent.plain_language_skin_register() == "technical"
        assert agent.plain_language_skin_status()["register"] == (
            "technical")
        del agent.config["register"]
        agent.config["jarl_mode"] = False
        assert agent.plain_language_skin_register() == "technical"
        agent.config["jarl_mode"] = True
        assert agent.plain_language_skin_register() == "jarl"

    def test_render_and_unfold_roads(self, agent):
        result = agent.render_plain_language_skin_item(
            "report-morning-build")
        rendering = result["rendering"]
        assert rendering["type"] == "plain_language_rendering"
        assert rendering["register"] == "jarl"
        assert rendering["shown"][0] == (
            "We will send out the build once the saved "
            "stopping point stands.")
        assert len(rendering["folded"]) == 3
        assert rendering["misses"] == []
        technical = agent.render_plain_language_skin_item(
            "report-morning-build", register="technical")
        assert technical["rendering"]["folded"] == []
        assert technical["rendering"]["shown"][0] == (
            "We will deploy the build once the checkpoint stands.")
        unfolded = agent.unfold_plain_language_skin_item(
            "report-morning-build")
        assert unfolded["rendering"]["folded"] == []
        assert unfolded["rendering"]["shown"] == (
            rendering["shown"] + rendering["folded"])
        assert "Folded detail" not in unfolded["text"]
        missed = agent.render_plain_language_skin_item("report-usage")
        assert missed["rendering"]["misses"] == ["quorum"]
        with pytest.raises(KeyError):
            agent.render_plain_language_skin_item("report-nope")


class TestPlainLanguageSkinTerminalSurface:
    def test_show_report_approval_standup_term_view_kind_panel(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/skin")
        assert "The Plain-Language Skin (M-182)" in text
        _, _, text = _slash(agent, "/skin report report-morning-build")
        assert "Morning build report" in text
        assert "send out" in text
        _, _, text = _slash(agent, "/skin approval approval-release")
        assert "The one action: send out the build" in text
        _, _, text = _slash(agent, "/skin standup standup-yrsa")
        assert "Doing: Walking the crew through how we send out" in text
        _, _, text = _slash(agent, "/skin term term-deploy")
        assert "In plain words: send out" in text
        _, _, text = _slash(agent, "/skin view view-all")
        assert "kind 'all'" in text
        _, _, text = _slash(agent, "/skin kind report")
        assert "report-usage" in text
        assert "standup-yrsa" not in text
        _, _, text = _slash(agent, "/skin panel")
        assert "Panel in Plain language at the M-181 slice boundary" in text
        _, _, text = _slash(agent, "/skin verdict")
        assert "strained" in text
        _, _, text = _slash(agent, "/skin unfold report-morning-build")
        assert "We will deploy the build once the checkpoint" in text
        assert "Folded detail" not in text
        _, _, text = _slash(agent, "/skin register")
        assert "jarl" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/skin [show|report <report-id>"
                "|approval <approval-id>|standup <standup-id>"
                "|term <term-id>|view <view-id>|kind <kind>"
                "|panel|verdict|unfold <item-id>|register]") in text
        _, _, text = _slash(agent, "/skin dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/skin report report-nope")
        assert "no report named" in text


@pytest.fixture()
def skin_handler(agent, monkeypatch):
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


def _skin_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestPlainLanguageSkinCommand:
    def test_show_is_default(self, skin_handler, agent):
        skin_handler._handle_skin("")
        assert "The Plain-Language Skin (M-182)" in (
            _skin_published_text(skin_handler))

    def test_report_approval_standup_term_view_kind_panel_verdict(
            self, skin_handler, agent):
        skin_handler._handle_skin("report report-morning-build")
        assert "Morning build report" in _skin_published_text(
            skin_handler)
        skin_handler._handle_skin("approval approval-release")
        assert "send out the build" in _skin_published_text(skin_handler)
        skin_handler._handle_skin("standup standup-yrsa")
        assert "yrsa" in _skin_published_text(skin_handler)
        skin_handler._handle_skin("term term-deploy")
        assert "send out" in _skin_published_text(skin_handler)
        skin_handler._handle_skin("view view-all")
        assert "kind 'all'" in _skin_published_text(skin_handler)
        skin_handler._handle_skin("kind term")
        assert "term-deploy" in _skin_published_text(skin_handler)
        skin_handler._handle_skin("panel")
        assert "Panel in Plain language" in _skin_published_text(
            skin_handler)
        skin_handler._handle_skin("verdict")
        assert "strained" in _skin_published_text(skin_handler)
        skin_handler._handle_skin("unfold report-morning-build")
        assert "We will deploy" in _skin_published_text(skin_handler)
        skin_handler._handle_skin("register")
        assert "jarl" in _skin_published_text(skin_handler)

    def test_bad_grammar_is_published(
            self, skin_handler, agent):
        skin_handler._handle_skin("dance party")
        assert USAGE in _skin_published_text(skin_handler)
        skin_handler._handle_skin("report report-nope")
        assert "no report named" in _skin_published_text(skin_handler)


class TestChatScreenRoutingPlainLanguageSkin:
    def test_skin_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/skin panel", _FakeLog())
        assert calls == [("/skin", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/skin[/green] - show the plain-language skin (M-182)" in (
            text)
        assert ('"/skin": "Usage: /skin | '
                '/skin report <report-id>') in text
