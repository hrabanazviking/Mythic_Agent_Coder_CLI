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
