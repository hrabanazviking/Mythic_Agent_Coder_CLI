"""M-199 Accessibility Verification - pure-layer tests.

TIER: integration

The pure layer is the accessibility verification,
held as data: M-016's tests re-run as gates -
keyboard-only completion, contrast, reduced
motion, no-colour play - one record per gate,
held whole as a card - under its title, its kind
in the closed vocabulary (keyboard, contrast,
motion, colour), its measure held honestly
(unknown stays empty, never invented), the
evidence it carries, named as data, and its
detail - the notes held as data beside them,
each naming its gate, its stance and its target,
and the verification index derived at call time
from the held gates alone, never stored where it
could drift. A gate naming no held evidence
stands incomplete, named in its gaps; two gates
standing for one gate id refuse by name, and one
stance record stands per gate stance. A record
claiming a check was actually run, a gate
actually passed live, or a reader actually
launched, refuses by name, and a stored index or
verdict refuses by name. The panel is derived for
one held view and the verdict is derived for the
whole book under one view. The shipped example
book is held in a data file, and a loader reads a
book from any file. The M-171 charter names NO
row for this slice - and the tests pin that
live. This layer runs no check, measures nothing
live, launches no reader, opens no network and
writes nothing: it holds the gates as data and
tells them.
"""



from pathlib import Path

import pytest
import yaml

from mythic_agent.core.accessibility_verification import (
    KINDS,
    EXAMPLE_EVIDENCE,
    STANCES,
    INDEX_ACTION,
    ACCESSIBILITY_VERIFICATION_RESOURCE,
    ACCESSIBILITY_VERIFICATION_SCHEMA,
    ACCESSIBILITY_VERIFICATION_SLICE,
    VERIFY_RULE,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    READY_WORDS,
    GateCard,
    NoteRecord,
    AccessBook,
    AccessPanel,
    AccessVerifyRegistry,
    AccessVerdict,
    AccessView,
    book_record,
    build_book,
    build_gate,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    derive_index,
    derive_panel,
    derive_verdict,
    first_note,
    format_book,
    format_gate,
    format_index,
    format_note,
    format_verify_screen,
    format_panel,
    format_evidence,
    format_verdict,
    format_view,
    gate_for_evidence,
    gate_gaps,
    gate_passes,
    gate_plain_words,
    gate_record,
    gates_for_kind,
    index_plain_words,
    index_record,
    inspect_gate_source,
    note_for_gate,
    note_plain_words,
    note_record,
    load_accessibility_verification,
    load_accessibility_verification_file,
    normalize_kind,
    normalize_stance,
    normalize_view_filter,
    panel_plain_words,
    panel_record,
    parse_verify_args,
    passing_gates,
    plain_lines,
    plain_words,
    shown_gates,
    total_gates,
    validate_book,
    validate_gate,
    validate_note,
    validate_panel,
    validate_row,
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
ON = "2026-11-09"
BY = "the coordinator"
EXAMPLE_TITLE = "Accessibility verification at the M-198 slice boundary"


def _gate(**overrides):
    fields = {
        "gate_id": "gate-test",
        "seq": 1,
        "title": "A test gate",
        "kind": "keyboard",
        "measure": "ctrl+k",
        "evidence": "the task completed by keyboard alone",
        "detail": "A test gate held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "verify-test",
    }
    fields.update(overrides)
    return build_gate(fields)


def _stored_gate(gate):
    return gate.to_record()


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "verify-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _stored_view(view):
    return view.to_record()


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "gate_id": "gate-test",
        "stance": "note",
        "target": "the user",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "verify-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _book(gates=None, views=None, notes=None, **overrides):
    fields = {
        "schema": ACCESSIBILITY_VERIFICATION_SCHEMA,
        "slice": "M-199",
        "accessibility_verification": {"title": "A test verification book"},
        "gates": [_stored_gate(item) for item in (
            gates if gates is not None else [_gate()])],
        "views": [_stored_view(item) for item in (
            views if views is not None else [_view()])],
        "notes": [item.to_record() for item in (notes or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(gates=[
        _gate(),
        _gate(gate_id="gate-reader-only", seq=2,
              title="A quiet gate", kind="contrast",
              measure="", evidence=""),
    ])


def test_shipped_book_loads_with_pinned_shape():
    book = load_accessibility_verification()
    assert book.title == EXAMPLE_TITLE
    assert book.gate_ids() == (
        "gate-keyboard-main", "gate-contrast-main",
        "gate-motion-main", "gate-colour-main",
        "gate-reader-main", "gate-focus-main")
    assert [v.view_id for v in book.views] == [
        "view-verify", "view-ready"]
    assert [m.gate_id for m in book.notes] == [
        "gate-keyboard-main",
        "gate-focus-main"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m198-boundary"
    assert panel.as_of == "2026-11-10"
    assert [row.item_id for row in panel.rows] == list(book.gate_ids())
    derived = derive_panel(book, "view-verify")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 6
    assert panel.total_shown == derived.total_shown == 6
    assert {c.standing: c.items for c in panel.target_counts} == {
        "ready": 5, "unready": 1}
    assert derive_verdict(book, "view-verify").verdict == "strained"
    assert derive_verdict(book, "view-verify").passing_shown == 5
    assert derive_verdict(book, "view-ready").verdict == "open"
    assert derive_verdict(book, "view-ready").passing_shown == 5
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / ACCESSIBILITY_VERIFICATION_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == ACCESSIBILITY_VERIFICATION_SCHEMA
    assert raw["slice"] == "M-199"
    assert "verdict" not in raw
    assert "verify_index" not in raw


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-199")]
    assert slice_.title == "Accessibility verification"
    assert slice_.part == 8
    assert "M-016's tests re-run as gates" in slice_.summary
    assert "keyboard-only completion" in slice_.summary
    assert "contrast" in slice_.summary
    assert "reduced motion" in slice_.summary
    assert "no-colour" in slice_.summary
    assert ACCESSIBILITY_VERIFICATION_SLICE == "M-199"

def test_charter_does_not_name_m199():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert owners.count("M-187") == 1
    assert owners.count("M-199") == 0


def test_closed_vocabularies():
    assert READY_WORDS == ("ready", "unready")
    assert KINDS == ("keyboard", "contrast", "motion", "colour")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "ready", "unready")
    assert VERDICT_WORDS == ("open", "strained", "shut")
    assert INDEX_ACTION == "index"
    assert EXAMPLE_EVIDENCE == "the task completed by keyboard alone"
    assert normalize_kind("KEYBOARD") == "keyboard"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    with pytest.raises(ValueError):
        normalize_kind("the void")
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    assert "held as data alone" in VERIFY_RULE
    assert "runs no check" in VERIFY_RULE
    assert "opens no network" in VERIFY_RULE
    assert "M-199" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /accessverify")


def test_shipped_book_judged_honestly_as_data():
    book = load_accessibility_verification()
    opener = book.gate_for("gate-keyboard-main")
    assert gate_passes(opener) is True
    assert gate_gaps(opener) == ()
    assert plain_lines(opener) == (
        "Gate: The keyboard-only task",
        "Kind: keyboard",
        "Measure: full tab order",
        "Evidence: the task completed by keyboard alone")
    save = book.gate_for("gate-contrast-main")
    assert save.measure == ""
    assert "Measure: unknown" in plain_lines(save)
    model = book.gate_for("gate-colour-main")
    assert model.kind == "colour"
    assert "Kind: colour" in plain_lines(model)
    quiet = book.gate_for("gate-reader-main")
    assert gate_gaps(quiet) == ("no held evidence",)
    assert gate_passes(quiet) is False
    assert [g.gate_id for g in passing_gates(book)] == [
        "gate-keyboard-main", "gate-contrast-main",
        "gate-motion-main", "gate-colour-main",
        "gate-focus-main"]
    assert total_gates(book) == 6
    index = derive_index(book)
    assert [e.evidence for e in index.gates] == [
        "the task completed by keyboard alone", "body text clears the AA bar",
        "the face stands still on request", "meaning survives without colour",
        "focus stays visible throughout"]
    assert index.gaps == ("gate-reader-main",)
    assert gate_for_evidence(book, "the task completed by keyboard alone").gate_id == (
        "gate-keyboard-main")
    assert gate_for_evidence(book, "triple resume") is None
    assert first_note(book).note_id == "note-note-keyboard"
    assert note_for_gate(
        book, "gate-keyboard-main", "note").note_id == (
            "note-note-keyboard")
    assert note_for_gate(book, "gate-nope") is None

# ---------------------------------------------------------------------
# The held gate: judged whole, its telling derived.
# ---------------------------------------------------------------------


def test_gate_record_round_trips():
    gate = _gate()
    assert validate_gate(gate) is gate
    rebuilt = build_gate(_stored_gate(gate))
    assert rebuilt == gate
    assert rebuilt.item_id == "gate-test"
    assert rebuilt.evidence == "the task completed by keyboard alone"
    record = gate_record(gate)
    assert record["type"] == "verify_gate"
    assert record["passes"] is True
    assert record["gaps"] == []


def test_gate_refuses_stored_judgements():
    for key in ("standing", "ready", "gaps", "segment", "verdict",
                "index", "gates", "coverage"):
        fields = _stored_gate(_gate())
        fields[key] = "stored"
        with pytest.raises(ValueError):
            build_gate(fields)
    fields = _stored_gate(_gate())
    fields["surprise"] = "stored"
    with pytest.raises(ValueError):
        build_gate(fields)


def test_gate_refuses_a_live_execution_claim():
    for key in ("runs_check", "ran_check", "verifies_now",
                "verified_live", "passes_gate", "passed_gate", "measures_live"):
        fields = _stored_gate(_gate())
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_gate(fields)
        assert "held as data alone" in str(caught.value)
    for key in ("posts_note", "shows_gate"):
        fields = _note().to_record()
        fields[key] = True
        with pytest.raises(ValueError) as caught:
            build_note(fields)
        assert "held as data alone" in str(caught.value)
    record = _note(gate_id="gate-test")
    assert validate_note(record) is record
    assert record.gate_id == "gate-test"
    assert note_record(record)["type"] == "verify_note"


def test_gate_vocabularies_are_closed():
    assert _gate(kind="KEYBOARD").kind == "keyboard"
    assert _gate(measure="").measure == ""
    assert _gate(measure=None).measure == ""
    with pytest.raises(ValueError):
        _gate(kind="a hunch")
    with pytest.raises(ValueError):
        _gate(title="   ")
    with pytest.raises(ValueError):
        _gate(seq=0)
    with pytest.raises(ValueError):
        _gate(evidence=5)
    with pytest.raises(ValueError):
        _gate(measure=5)
    with pytest.raises(ValueError):
        _gate(detail="   ")


def test_plain_telling_derives_from_the_gates_own_fields():
    gate = _gate(
        title="Test Gate", kind="contrast", measure="", evidence="",
        detail="The words wait on a held gate.")
    lines = plain_lines(gate)
    assert lines[0] == "Gate: Test Gate"
    assert lines[1] == "Kind: contrast"
    assert lines[2] == "Measure: unknown"
    assert lines[3] == "Evidence: none"
    assert plain_words(gate) == gate_plain_words(gate)
    assert "Test Gate" in plain_words(gate)
    assert "held gate" in plain_words(gate)


def test_incomplete_gate_stands_named_in_its_gaps():
    gate = _gate(evidence="")
    assert gate_gaps(gate) == ("no held evidence",)
    assert gate_passes(gate) is False
    text = format_gate(gate)
    assert "stands unready" in text
    current_text = format_gate(_gate())
    assert "stands ready" in current_text


def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(_stored_view(view)) == view
    record = view_record(view)
    assert record["type"] == "verify_view"
    assert record["view_filter"] == "all"
    assert "shows all gates" in view_plain_words(view)
    assert "filter all" in format_view(view)
    with pytest.raises(ValueError):
        _view(view_filter="some")
    stance = _note()
    assert build_note(stance.to_record()) == stance
    assert "Verify note note gate-test" in format_note(stance)
    assert "executes no command" in format_note(stance)
    assert "toward the user" in note_plain_words(stance)
    with pytest.raises(ValueError):
        _note(stance="dance")

# ---------------------------------------------------------------------
# The index and the stance targets: derived at call time, never held.
# ---------------------------------------------------------------------


def test_index_is_derived_from_the_held_gates_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.gate_id for e in index.gates] == ["gate-test"]
    assert index.gates[0].evidence == "the task completed by keyboard alone"
    assert index.gaps == ("gate-reader-only",)
    assert index_record(index)["type"] == "verify_index"
    assert index_record(book)["gaps"] == ["gate-reader-only"]
    assert "1 held evidence" in index_plain_words(book)
    text = format_index(book)
    assert "Verify index" in text
    assert "the task completed by keyboard alone - A test gate (gate-test)" in text
    assert "gate-reader-only" in text
    assert "executes no command" in text


def test_target_reaches_its_gate_and_an_unheld_target_reaches_nothing():
    book = _mixed_book()
    assert gate_for_evidence(book, "the task completed by keyboard alone").gate_id == "gate-test"
    assert gate_for_evidence(book, "triple resume") is None
    assert gate_for_evidence(book, "") is None
    assert "A test gate" in format_evidence(book, "the task completed by keyboard alone")
    assert "reaches nothing in this book" in format_evidence(
        book, "triple resume")


def test_first_note_is_held_as_data():
    book = _book(notes=[_note(), _note(
        note_id="note-two", seq=2, gate_id="gate-other",
        stance="question", title="The second stance")])
    assert first_note(book).note_id == "note-test"
    assert note_for_gate(book, "gate-other").note_id == (
        "note-two")
    assert note_for_gate(
        book, "gate-other", "question").note_id == "note-two"
    assert note_for_gate(book, "gate-other", "praise") is None
    bare = _book()
    assert first_note(bare) is None
    assert note_for_gate(bare, "gate-other") is None
    text = format_note(first_note(book))
    assert "held as data alone" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    stance = _note(
        gate_id="gate-x", stance="concern",
        target="a branched session")
    assert stance.stance == "concern"
    rebuilt = build_note(stance.to_record())
    assert rebuilt == stance
    assert rebuilt.gate_id == "gate-x"
    assert rebuilt.target == "a branched session"
    with pytest.raises(ValueError):
        _note(gate_id="   ")
    with pytest.raises(ValueError):
        _note(target="   ")
    with pytest.raises(ValueError):
        _note(stance="teleport")


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert isinstance(panel, AccessPanel)
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book).rows == panel.rows
    assert build_row(panel.rows[0], book.gates[0]) == panel.rows[0]
    assert validate_row(panel.rows[0], book.gates[0]) == panel.rows[0]
    tampered = dict(panel.to_record())
    tampered["total_shown"] = 99
    with pytest.raises(ValueError):
        build_panel(tampered, book)
    renamed = dict(panel.to_record())
    renamed["panel_id"] = "panel-renamed"
    assert build_panel(renamed, book).panel_id == "panel-renamed"
    record = panel_record(panel, book)
    assert record["type"] == "verify_panel"
    assert record["panel_id"] == panel.panel_id


def test_verdict_is_derived_from_the_shown_gates():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert isinstance(verdict, AccessVerdict)
    assert verdict.verdict == "strained"
    assert verdict.total_shown == 2
    assert verdict.passing_shown == 1
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    record = verdict_record(verdict, book)
    assert record["type"] == "verify_verdict"
    assert "strained" in verdict_plain_words(book)
    assert "strained" in format_verdict(book)


def test_verdict_open_and_shut_edges():
    whole = _book(gates=[_gate()])
    assert derive_verdict(whole).verdict == "open"
    absent_book = _book(gates=[_gate(evidence="")])
    assert derive_verdict(absent_book).verdict == "shut"
    none_shown = _book(
        gates=[_gate(evidence="")],
        views=[_view(view_filter="ready")])
    verdict = derive_verdict(none_shown)
    assert verdict.total_shown == 0
    assert verdict.verdict == "shut"


def test_shown_and_kind_readings():
    book = _mixed_book()
    assert [g.gate_id for g in shown_gates(book)] == [
        "gate-test", "gate-reader-only"]
    ready_view = _view(
        view_id="view-r", seq=2, view_filter="ready")
    book2 = _book(
        gates=[_gate(), _gate(
            gate_id="gate-reader-only", seq=2, title="A quiet gate",
            kind="contrast", measure="", evidence="")],
        views=[_view(), ready_view])
    assert [g.gate_id for g in shown_gates(book2, ready_view)] == [
        "gate-test"]
    assert [g.gate_id for g in gates_for_kind(book2, "contrast")] == [
        "gate-reader-only"]
    assert [g.gate_id for g in passing_gates(book2)] == [
        "gate-test"]
    assert total_gates(book2) == 2
    with pytest.raises(ValueError):
        gates_for_kind(book2, "the void")


def test_book_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(gates=[_gate(), _gate(seq=2)])
    with pytest.raises(ValueError):
        _book(gates=[_gate(), _gate(gate_id="gate-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(view_filter="ready")])
    with pytest.raises(ValueError) as caught:
        _book(notes=[_note(), _note(note_id="note-two", seq=2)])
    assert "one stance stands per gate target" in str(caught.value)
    fields = {
        "schema": ACCESSIBILITY_VERIFICATION_SCHEMA, "slice": "M-199",
        "accessibility_verification": {"title": "A test verification book"},
        "gates": [_stored_gate(_gate())],
        "views": [_stored_view(_view())], "notes": [],
        "panels": [], "verdict": "open",
    }
    with pytest.raises(ValueError):
        build_book(fields)
    del fields["verdict"]
    fields["verify_index"] = "stored"
    with pytest.raises(ValueError):
        build_book(fields)
    raw = {
        "schema": ACCESSIBILITY_VERIFICATION_SCHEMA, "slice": "M-199",
        "accessibility_verification": {"title": "A test verification book"},
        "gates": [], "views": [], "notes": [], "panels": [],
        "runs_check": True,
    }
    with pytest.raises(ValueError) as caught:
        build_book(raw)
    assert "held as data alone" in str(caught.value)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ACCESSIBILITY_VERIFICATION_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "accessibility_verification.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_accessibility_verification_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_gates(book) == 6


def test_registry_holds_gates_and_views_one_by_one():
    registry = AccessVerifyRegistry()
    assert registry.list_items() == ()
    held = registry.register_gate(_gate())
    assert held.gate_id == "gate-test"
    registry.register_view(_view())
    assert [i.item_id if hasattr(i, "item_id") else i.view_id
            for i in registry.list_items()] == ["gate-test", "view-test"]
    assert registry.get_gate("gate-test").title == "A test gate"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.book().title == "An unheld verification book"
    with pytest.raises(ValueError):
        registry.register_gate(_gate(seq=2))
    with pytest.raises(ValueError):
        registry.register_gate(_gate(gate_id="gate-two"))
    with pytest.raises(KeyError):
        registry.get_gate("gate-nope")


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = AccessVerifyRegistry()
    book = _mixed_book()
    held = registry.register_book(book)
    assert held.title == "A test verification book"
    assert len(registry.list_gates()) == 2
    other = _book(gates=[_gate(
        gate_id="gate-x", seq=9, title="Other", evidence="the task completed by keyboard alone")],
        views=[_view(view_id="view-x", seq=9)])
    object.__setattr__(other, "title", "Another title")
    with pytest.raises(ValueError):
        registry.register_book(other)


def test_plain_words_and_formatters():
    book = _mixed_book()
    assert "kind: 'keyboard'" in format_book(book)
    assert "gate-reader-only" in format_book(book, "contrast")
    assert "gate-test" not in format_book(book, "contrast")
    assert "Undo panel under view view-test" in format_panel(book)
    assert panel_plain_words(book).startswith(
        "The Accessibility verification book holds 2 gates")
    screen = format_verify_screen(book)
    assert "Accessibility Verification (M-199)" in screen
    assert PLAIN_EXPLANATION in screen
    assert "gate-reader-sweep" not in screen
    assert "gate-reader-only" in screen
    record = book_record(book)
    assert record["type"] == "verify_book"
    assert record["title"] == "A test verification book"
    assert len(record["gates"]) == 2
    panel = derive_panel(book)
    assert panel_record(panel, book)["rows"][0]["item_id"] == "gate-test"
    assert verdict_record(derive_verdict(book), book)["verdict"] == (
        "strained")
    gate_text = format_gate(book.gates[0])
    assert "Gate: A test gate" in gate_text
    assert "Evidence: the task completed by keyboard alone" in gate_text


def test_parse_args_inspect_and_loader_targets():
    assert parse_verify_args("") == ("show", None)
    assert parse_verify_args("show") == ("show", None)
    assert parse_verify_args(None) == ("show", None)
    assert parse_verify_args("gate gate-test") == (
        "gate", "gate-test")
    assert parse_verify_args("evidence the task completed by keyboard alone") == (
        "evidence", "the task completed by keyboard alone")
    assert parse_verify_args("kind keyboard") == (
        "kind", "keyboard")
    assert parse_verify_args("view view-test") == ("view", "view-test")
    assert parse_verify_args("note note-test") == (
        "note", "note-test")
    assert parse_verify_args("index") == ("index", None)
    assert parse_verify_args("panel") == ("panel", None)
    assert parse_verify_args("verdict") == ("verdict", None)
    for bad in ("dance", "gate", "evidence", "kind", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_verify_args(bad)
    gate = _gate()
    assert inspect_gate_source(gate) == {
        "kind": "gate", "gate_id": "gate-test"}
    assert inspect_gate_source(_stored_gate(gate))["kind"] == (
        "gate")
    assert inspect_gate_source(_stored_view(_view()))["kind"] == (
        "view")
    assert inspect_gate_source(_note().to_record())["kind"] == (
        "note")
    assert inspect_gate_source(42)["kind"] == "unknown"
    book = load_accessibility_verification({
        "schema": ACCESSIBILITY_VERIFICATION_SCHEMA, "slice": "M-199",
        "accessibility_verification": {"title": "A judged book"},
        "gates": [_stored_gate(_gate())],
        "views": [_stored_view(_view())], "notes": [], "panels": []})
    assert isinstance(book, AccessBook)
    assert book.title == "A judged book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_accessibility_verification({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_accessibility_verification({"slice": "M-999"})
    built = build_gate(
        gate_id="gate-kw", seq=3, title="Kw Gate",
        kind="keyboard", measure="ctrl+k",
        evidence="the task completed by keyboard alone", detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="verify-test")
    assert built.gate_id == "gate-kw"
    assert gate_passes(built) is True


# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-199 agent layer: the agent holds a verification book
# for the session, gates and views are published
# as session news through the checkpoint target
# (journal first, deduped per shape), the panel
# and verdict are derived at call time from the
# whole book under a view, never held, the index
# is derived from the book's held gates, and the
# stance targets are held as data beside them -
# holding one executes no command. This layer
# executes nothing, runs no action, navigates
# nowhere, opens no network and persists nothing
# beyond the session journal news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _verify_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_verify_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / ACCESSIBILITY_VERIFICATION_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "accessibility_verification.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestVerifyAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.access_verify_status()
        assert status["gates"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["accessibility_verification"]["title"] == EXAMPLE_TITLE
        assert len(status["accessibility_verification"]["gates"]) == 6
        assert len(status["accessibility_verification"]["views"]) == 2
        assert len(status["accessibility_verification"]["notes"]) == 2
        assert status["panel"]["total_items"] == 6
        assert status["panel"]["total_shown"] == 6
        assert status["panels"][0]["panel_id"] == "panel-m198-boundary"
        assert status["verdict"]["verdict"] == "strained"
        assert status["verdict"]["passing_shown"] == 5
        assert [e["evidence"] for e in status["index"]["gates"]] == ["the task completed by keyboard alone", "body text clears the AA bar", "the face stands still on request", "meaning survives without colour", "focus stays visible throughout"]
        assert status["index"]["gaps"] == ["gate-reader-main"]
        assert status["first_note"]["note_id"] == "note-note-keyboard"
        assert "held as data alone" in status["rule"]
        assert "focus stays visible throughout" in status["plain_words"]
        assert "Accessibility Verification (M-199)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._access_verify_registry()
        assert agent._access_verify_registry() is first
        assert agent._access_verify_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "evidence")
        session_id = agent.attach_session(store)
        agent.access_verify_status()
        assert agent.get_verify_gate(
            "gate-keyboard-main").title == "The keyboard-only task"
        assert agent.get_verify_view("view-verify").view_filter == "all"
        assert agent.get_verify_note(
            "note-note-keyboard").note_id == "note-note-keyboard"
        assert [a.gate_id for a in agent.verify_gates_for_kind(
            "keyboard")] == ["gate-keyboard-main", "gate-focus-main"]
        assert [a.gate_id for a in agent.verify_gates_for_kind(
            "colour")] == ["gate-colour-main"]
        assert [a.gate_id for a in agent.verify_gates_passing()] == [
            "gate-keyboard-main", "gate-contrast-main",
            "gate-motion-main", "gate-colour-main",
            "gate-focus-main"]
        agent.access_verify_panel()
        agent.access_verify_verdict()
        agent.verify_index()
        agent.report_access_verify()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("verify")] == []
        with pytest.raises(KeyError):
            agent.get_verify_gate("gate-nope")
        with pytest.raises(KeyError):
            agent.get_verify_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_verify_note("note-nope")
        with pytest.raises(ValueError):
            agent.verify_gates_for_kind("the void")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_verify_gate(_gate())
        status = agent.access_verify_status()
        assert [a["gate_id"] for a in status["gates"]] == ["gate-test"]
        assert status["book"]["title"] == "An unheld verification book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["evidence"] for e in status["index"]["gates"]] == [
            "the task completed by keyboard alone"]
        assert status["first_note"] is None
        assert "gate-test" in status["screen"]

    def test_held_gate_never_falls_back_to_the_example(
            self, agent):
        agent.register_verify_gate(_gate())
        with pytest.raises(KeyError):
            agent.get_verify_gate("gate-keyboard-main")
        with pytest.raises(KeyError):
            agent.get_verify_view("view-verify")
        with pytest.raises(KeyError):
            agent.get_verify_note("modal")
        gate = agent.get_verify_gate("gate-test")
        assert gate.title == "A test gate"
        assert agent.access_verify_book().title == (
            "An unheld verification book")

    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_verify_note("note-note-keyboard")
        assert first.note_id == "note-note-keyboard"
        assert first.gate_id == "gate-keyboard-main"
        status = agent.access_verify_status()
        assert status["index"]["gaps"] == ["gate-reader-main"]
        assert status["first_note"]["gate_id"] == (
            "gate-keyboard-main")
        assert status["first_note"]["stance"] == "note"


class TestVerifyAgentHolding:
    def test_register_gate_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "evidence")
        session_id = agent.attach_session(store)
        result = agent.register_verify_gate(_gate())
        assert result["gate"]["gate_id"] == "gate-test"
        assert result["record_news"]["type"] == "verify_gate"
        assert "gate-test" in result["screen"]
        events = _verify_events(store, session_id, "verify_gate")
        assert len(events) == 1
        agent.close()

    def test_duplicate_gate_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "evidence")
        session_id = agent.attach_session(store)
        agent.register_verify_gate(_gate())
        with pytest.raises(ValueError):
            agent.register_verify_gate(_gate(seq=9))
        with pytest.raises(ValueError):
            agent.register_verify_gate(_gate(gate_id="gate-two"))
        events = _verify_events(store, session_id, "verify_gate")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "evidence")
        session_id = agent.attach_session(store)
        result = agent.register_verify_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_verify_events(
            store, session_id, "verify_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "evidence")
        session_id = agent.attach_session(store)
        agent.register_verify_gate(_gate())
        result = agent.view_verify("ready")
        assert result["view"]["view_filter"] == "ready"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "verify_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "open"
        assert len(_verify_events(
            store, session_id, "verify_view")) == 1
        assert len(_verify_events(
            store, session_id, "verify_panel")) == 1
        assert len(_verify_events(
            store, session_id, "verify_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "evidence")
        session_id = agent.attach_session(store)
        result = agent.register_verify_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "verify_gate", "verify_view"]
        assert len(_verify_events(
            store, session_id, "verify_gate")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "evidence")
        session_id = agent.attach_session(store)
        result = agent.record_verify_book()
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "verify_panel"
        assert result["index_record"]["gaps"] == [
            "gate-reader-main"]
        with pytest.raises(ValueError):
            agent.record_verify_book()
        assert len(_verify_events(
            store, session_id, "verify_gate")) == 6
        assert len(_verify_events(
            store, session_id, "verify_view")) == 2
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_verify_book_file(tmp_path)
        book = load_accessibility_verification_file(path)
        result = agent.record_verify_book(book)
        assert result["count"] == 6
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_access_verify()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert report["verdict"]["verdict"] == "strained"
        assert report["index"]["gaps"] == ["gate-reader-main"]
        assert "gate-keyboard-main" in report["book_text"]
        assert "the task completed by keyboard alone - The keyboard-only task (gate-keyboard-main)" in report["index_text"]
        agent.register_verify_gate(_gate())
        report = agent.report_access_verify()
        assert report["book"]["title"] == "An unheld verification book"
        assert report["panel"] is None
        assert report["verdict"] is None


class TestVerifyTerminalHeading:
    def test_show_gate_evidence_kind_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/accessverify")
        assert "Accessibility Verification (M-199)" in text
        _, _, text = _slash(agent, "/accessverify gate gate-keyboard-main")
        assert "Gate: The keyboard-only task" in text
        _, _, text = _slash(agent, "/accessverify evidence the task completed by keyboard alone")
        assert "the task completed by keyboard alone" in text
        _, _, text = _slash(agent, "/accessverify evidence triple resume")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/accessverify kind keyboard")
        assert "gate-keyboard-main" in text
        assert "gate-colour-main" not in text
        _, _, text = _slash(agent, "/accessverify view view-verify")
        assert "filter all" in text
        _, _, text = _slash(agent, "/accessverify note note-note-keyboard")
        assert "Verify note note gate-keyboard-main" in text
        _, _, text = _slash(agent, "/accessverify index")
        assert "Verify index" in text
        assert "gate-colour-main" in text
        _, _, text = _slash(agent, "/accessverify panel")
        assert "Undo panel under view view-verify" in text
        _, _, text = _slash(agent, "/accessverify verdict")
        assert "strained" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/accessverify [show|gate <gate-id>"
                "|evidence <evidence>|kind <kind>|view <view-id>"
                "|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/accessverify dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/accessverify gate gate-nope")
        assert "no gate named" in text


@pytest.fixture()
def verify_handler(agent, monkeypatch):
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


def _verify_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestVerifyCommand:
    def test_show_is_default(self, verify_handler, agent):
        verify_handler._handle_accessverify("")
        assert "Accessibility Verification (M-199)" in (
            _verify_published_text(verify_handler))

    def test_gate_evidence_kind_view_note_index_panel_verdict(
            self, verify_handler, agent):
        verify_handler._handle_accessverify("gate gate-keyboard-main")
        assert "Gate: The keyboard-only task" in _verify_published_text(
            verify_handler)
        verify_handler._handle_accessverify("evidence the task completed by keyboard alone")
        assert "the task completed by keyboard alone" in _verify_published_text(
            verify_handler)
        verify_handler._handle_accessverify("kind keyboard")
        assert "gate-keyboard-main" in _verify_published_text(verify_handler)
        verify_handler._handle_accessverify("view view-verify")
        assert "filter all" in _verify_published_text(verify_handler)
        verify_handler._handle_accessverify("note note-note-keyboard")
        assert "Verify note note gate-keyboard-main" in _verify_published_text(verify_handler)
        verify_handler._handle_accessverify("index")
        assert "Verify index" in _verify_published_text(verify_handler)
        verify_handler._handle_accessverify("panel")
        assert "Undo panel under view" in _verify_published_text(
            verify_handler)
        verify_handler._handle_accessverify("verdict")
        assert "strained" in _verify_published_text(verify_handler)

    def test_bad_grammar_is_published(
            self, verify_handler, agent):
        verify_handler._handle_accessverify("dance party")
        assert USAGE in _verify_published_text(verify_handler)
        verify_handler._handle_accessverify("gate gate-nope")
        assert "no gate named" in _verify_published_text(verify_handler)


class TestChatScreenRoutingVerify:
    def test_undo_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/accessverify panel", _FakeLog())
        assert calls == [("/accessverify", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/accessverify[/green] - show Accessibility verification (M-199)" in (
            text)
        assert ('"/accessverify": "Usage: /accessverify | '
                '/accessverify gate <gate-id>') in text


class TestVerifyDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.access_verify_panel()
        assert panel.total_shown == 6
        assert panel.panel_id == "panel-view-verify"
        verdict = agent.access_verify_verdict()
        assert verdict.verdict == "strained"
        found = agent.access_verify_verdict("view-ready")
        assert found.verdict == "open"
        assert found.passing_shown == 5
        agent.register_verify_gate(_gate())
        with pytest.raises(ValueError):
            agent.access_verify_panel()
        with pytest.raises(ValueError):
            agent.access_verify_verdict()

    def test_view_target_over_an_unshown_filter_is_shut(self, agent):
        agent.register_verify_gate(_gate(evidence=""))
        result = agent.view_verify("ready")
        assert result["verdict_record"]["verdict"] == "shut"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "evidence")
        session_id = agent.attach_session(store)
        result = agent.verify_index()
        assert [e["evidence"] for e in result["index"]["gates"]] == ["the task completed by keyboard alone", "body text clears the AA bar", "the face stands still on request", "meaning survives without colour", "focus stays visible throughout"]
        assert result["index"]["gaps"] == ["gate-reader-main"]
        assert "the task completed by keyboard alone - The keyboard-only task (gate-keyboard-main)" in (
            result["index_text"])
        gate = agent.get_verify_gate("gate-reader-main")
        assert gate_gaps(gate) == ("no held evidence",)
        assert gate_passes(gate) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("verify")] == []
        agent.close()
