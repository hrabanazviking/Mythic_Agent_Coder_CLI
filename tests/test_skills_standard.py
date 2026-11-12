"""M-236 Cross-app method - pure-layer tests.

TIER: integration

The pure layer is the tracker, held as data: one
record per pack, held whole - the skill it
answers for, found by skill id, its title, the
steps it walked in walk pack and the evidence
it carries, held by skill. The question walk is
explicit - found, opened, vetted, loaded,
held, with their legal steps held as data -
and a pack's standing is derived at call
time: a pack that opens anywhere but found, steps where the sequence does not allow,
carries a bare claim in place of held evidence,
or has not yet found held stands open,
found in its gaps. A pack stands only for
an active skill: a pack naming no held
skill, or one that is not active, refuses by
name. The pack's trace - its walked steps
as one line - is derived at call time, and a held
trace record stands current only while it agrees
with the derived trace. The index, panel,
verdict, ledger, trace, pack and current
pack are derived at call time, never
stored where they could drift, and a stored one
refuses by name, as does a record claiming a
question was actually answered, loaded or
held live. The shipped example book is held
in a data file, and a loader reads a book from
any file. No charter row names this skill: the
M-171 TUI charter binds Part VIII alone, and the
M-005 method charter names the whole of Part X
as the part that executes it, both pinned live
below.
"""


from pathlib import Path

import pytest
import yaml

from mythic_agent.core.skills_standard import (
    EXAMPLE_STAGE,
    BARE_CLAIMS,
    HELD_EVIDENCE,
    INDEX_ACTION,
    STAGES,
    CLAIM_KINDS,
    TRANSITIONS,
    SKILL_STATES,
    STAGE_FIELDS,
    PLAIN_EXPLANATION,
    PACK_RESOURCE,
    PACK_RULE,
    PACK_SCHEMA,
    PACK_SLICE,
    COMPLETE_WORDS,
    STANCES,
    USAGE,
    VERDICT_WORDS,
    VIEW_FILTERS,
    TraceRecord,
    PackRecord,
    IndexPack,
    SkillRef,
    NoteRecord,
    PackBook,
    PackIndex,
    PackPanel,
    PackRegistry,
    PackVerdict,
    PackView,
    trace_for_pack,
    ledger_record,
    book_record,
    build_trace,
    build_book,
    build_pack,
    build_skill_ref,
    build_note,
    build_panel,
    build_row,
    build_verdict,
    build_view,
    current_pack,
    transition_breaks,
    derive_index,
    derive_panel,
    derive_verdict,
    pack_for_check,
    pack_gaps,
    pack_pack,
    pack_record,
    pack_green,
    packs_for_skill,
    first_note,
    format_book,
    format_pack,
    format_index,
    format_note,
    format_stage,
    format_panel,
    format_pack_screen,
    format_verdict,
    format_view,
    index_plain_words,
    index_record,
    skill_record,
    load_pack,
    legal_step,
    load_pack_file,
    next_stage,
    normalize_stage,
    normalize_claim_kind,
    normalize_skill_state,
    normalize_stance,
    normalize_view_filter,
    note_for_pack,
    note_plain_words,
    note_record,
    panel_plain_words,
    panel_record,
    parse_pack_args,
    green_packs,
    plain_lines,
    plain_words,
    roadmap_record,
    segment_of,
    trace_current,
    trace_of,
    shown_packs,
    validate_book,
    validate_pack,
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
from mythic_agent.core.method_charter import (
    load_charter as load_method_charter,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]
ON = "2026-11-11"
BY = "the coordinator"
EXAMPLE_TITLE = "Skills standard at the M-236 slice run"
EXAMPLE_STAGES = ["held", "held", "held"]
EXAMPLE_RUN_IDS = (
    "pack-held-pack", "pack-retried-pack",
    "pack-own-pack", "pack-bare-pack",
    "pack-leaping-pack")
EXAMPLE_TRACE = "found > opened > vetted > loaded > held"


def _ref(**overrides):
    fields = {
        "skill_id": "skill-test",
        "seq": 1,
        "title": "A test skill",
        "state": "live",
        "detail": "A test skill reference held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "pack-test",
    }
    fields.update(overrides)
    return build_skill_ref(fields)


def _pack(**overrides):
    fields = {
        "pack_id": "pack-test",
        "seq": 1,
        "skill_id": "skill-test",
        "title": "A test pack",
        "stages": ["found", "opened", "vetted", "loaded", "held"],
        "claims": [],
        "detail": "A test pack held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "pack-test",
    }
    fields.update(overrides)
    return build_pack(fields)


def _view(**overrides):
    fields = {
        "view_id": "view-test",
        "seq": 1,
        "view_filter": "all",
        "detail": "See everything, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "pack-test",
    }
    fields.update(overrides)
    return build_view(fields)


def _note(**overrides):
    fields = {
        "note_id": "note-test",
        "seq": 1,
        "pack_id": "pack-test",
        "stance": "note",
        "target": "the work ahead",
        "title": "A test note",
        "detail": "A test note held as data, for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "pack-test",
    }
    fields.update(overrides)
    return build_note(fields)


def _trace(**overrides):
    fields = {
        "trace_id": "trace-test",
        "seq": 1,
        "pack_id": "pack-test",
        "trace": "found > opened > vetted > loaded > held",
        "detail": "A test trace held as data.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "pack-test",
    }
    fields.update(overrides)
    return build_trace(fields)


def _book(skills=None, packs=None, views=None, notes=None,
          traces=None, **overrides):
    fields = {
        "schema": PACK_SCHEMA,
        "skill": "M-236",
        "skills_standard": {"title": "A test pack book"},
        "skills": [item.to_record() for item in (
            skills if skills is not None else [_ref()])],
        "pack_records": [item.to_record() for item in (
            packs if packs is not None else [_pack()])],
        "views": [item.to_record() for item in (
            views if views is not None else [_view()])],
        "notes": [item.to_record() for item in (notes or [])],
        "traces": [item.to_record() for item in (
            traces or [])],
        "panels": [],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(packs=[
        _pack(),
        _pack(pack_id="pack-hidden", seq=2,
               title="A hidden pack", stages=[]),
    ])


def test_shipped_book_loads_with_pinned_trace():
    book = load_pack()
    assert book.title == EXAMPLE_TITLE
    assert book.pack_ids() == EXAMPLE_RUN_IDS
    assert book.skill_ids() == (
        "skill-forge", "skill-second-brain",
        "skill-seidr")
    assert [v.view_id for v in book.views] == [
        "view-packs", "view-held"]
    assert [m.pack_id for m in book.notes] == [
        "pack-held-pack", "pack-bare-pack"]
    assert [a.pack_id for a in book.traces] == ["pack-held-pack"]
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-skill"
    assert panel.as_of == "2026-11-11"
    assert [row.item_id for row in panel.rows] == list(book.pack_ids())
    derived = derive_panel(book, "view-packs")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_items == derived.total_items == 5
    assert panel.total_shown == derived.total_shown == 5
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 3, "open": 2}
    assert derive_verdict(book, "view-packs").verdict == "held"
    assert derive_verdict(book, "view-packs").green_shown == 3
    assert derive_verdict(book, "view-held").verdict == "held"
    assert derive_verdict(book, "view-held").green_shown == 3
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / PACK_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == PACK_SCHEMA
    assert raw["skill"] == "M-236"
    assert "verdict" not in raw
    assert "pack_index" not in raw
    assert "ledger" not in raw
    assert "trace" not in raw

def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-236")]
    assert slice_.title == "Skills standard"
    assert slice_.part == 10
    assert "reusable skill packs (the Agent Skills form) loadable per project" in slice_.summary
    assert "Volmarr's own" in slice_.summary and "first citizen" in slice_.summary
    assert PACK_SLICE == "M-236"

def test_charter_rows_do_not_name_m236():
    charter = load_charter()
    owners = []
    for key in charter.screen_keys():
        owners.extend(charter.screen(key).owning_slices)
    assert owners
    assert "M-236" not in owners
    method = load_method_charter()
    assert "M-201" in method.source_note
    assert "M-232" in method.source_note
    assert "YRSA_CODING_JUGGERNAUT" in method.source_note

def test_closed_vocabularies():
    assert COMPLETE_WORDS == ("complete", "open")
    assert STAGE_FIELDS == ("stages", "claims")
    assert STANCES == ("note", "concern", "praise", "question")
    assert VIEW_FILTERS == ("all", "complete", "open")
    assert VERDICT_WORDS == ("held", "held", "blocked")
    assert SKILL_STATES == ("live", "dormant")
    assert STAGES == ("found", "opened", "vetted", "loaded", "held")
    assert HELD_EVIDENCE == ("instructions_ref", "resources_ref", "scripts_ref", "manifest_ref", "scope_ref")
    assert BARE_CLAIMS == ("feeling", "memory", "assertion", "summary")
    assert CLAIM_KINDS == HELD_EVIDENCE + BARE_CLAIMS
    assert TRANSITIONS["loaded"] == ("found", "held")
    assert TRANSITIONS["held"] == ()
    assert INDEX_ACTION == "index"
    assert EXAMPLE_STAGE == "held"
    assert normalize_stance("PRAISE") == "praise"
    assert normalize_view_filter("ALL") == "all"
    assert normalize_skill_state("LIVE") == "live"
    assert normalize_stage("VETTED") == "vetted"
    assert normalize_claim_kind("FEELING") == "feeling"
    with pytest.raises(ValueError):
        normalize_stance("pinch")
    with pytest.raises(ValueError):
        normalize_view_filter("some")
    with pytest.raises(ValueError):
        normalize_skill_state("blessed")
    with pytest.raises(ValueError):
        normalize_stage("polish")
    with pytest.raises(ValueError):
        normalize_claim_kind("weather")
    assert legal_step("vetted", "loaded") is True
    assert legal_step("opened", "held") is False
    assert legal_step("held", "found") is False
    assert next_stage("found") == "opened"
    assert next_stage("vetted") == "loaded"
    assert next_stage("loaded", failed=True) == "found"
    assert next_stage("loaded") == "held"
    assert next_stage("held") is None
    assert "held as data alone" in PACK_RULE
    assert "pack sequence" in PACK_RULE
    assert "M-236" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /skillsstandard")

def test_shipped_book_judged_honestly_as_data():
    book = load_pack()
    opening = book.pack_for("pack-held-pack")
    assert pack_green(opening, book) is True
    assert pack_gaps(opening, book) == ()
    assert plain_lines(opening) == (
        "Pack: The held pack",
        "Skill: skill-forge",
        "Stage: held",
        "Claims: instructions_ref")
    asking = book.pack_for("pack-bare-pack")
    assert pack_gaps(asking, book) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",)
    assert pack_green(asking, book) is False
    skipping = book.pack_for("pack-leaping-pack")
    assert pack_gaps(skipping, book) == (
        "steps from opened to held, which the pack sequence "
        "does not allow",)
    assert [g.pack_id for g in green_packs(book)] == [
        "pack-held-pack", "pack-retried-pack", "pack-own-pack"]
    index = derive_index(book)
    assert [e.stage for e in index.packs] == EXAMPLE_STAGES
    assert index.gaps == ("pack-bare-pack", "pack-leaping-pack")
    assert pack_for_check(book, EXAMPLE_STAGE).pack_id == (
        "pack-held-pack")
    assert pack_for_check(book, "triple pack") is None
    assert transition_breaks(book) == (
        "pack-leaping-pack: opened > held",)
    assert [g.pack_id for g in pack_pack(book)] == list(
        EXAMPLE_RUN_IDS)
    assert trace_of(book, "pack-held-pack") == EXAMPLE_TRACE
    assert trace_current(book, "pack-held-pack") is True
    assert trace_current(book, "pack-retried-pack") is False
    assert trace_for_pack(
        book, "pack-held-pack").trace_id == "trace-first"
    assert first_note(book).note_id == "note-note-first"
    assert note_for_pack(
        book, "pack-held-pack", "note").note_id == (
            "note-note-first")
    assert note_for_pack(book, "pack-nope") is None
    assert current_pack(book).pack_id == "pack-bare-pack"
    ledger = ledger_record(book)
    assert ledger["standings"] == [
        {"standing": "complete", "pack_records": 3},
        {"standing": "open", "pack_records": 2}]
    assert ledger["total"] == 5
    assert ledger["current_pack"] == "pack-bare-pack"
    assert ledger["traces"] == [
        {"pack_id": "pack-held-pack", "trace": "current"},
        {"pack_id": "pack-retried-pack", "trace": "unheld"},
        {"pack_id": "pack-own-pack", "trace": "unheld"},
        {"pack_id": "pack-bare-pack", "trace": "unheld"},
        {"pack_id": "pack-leaping-pack", "trace": "unheld"}]
    assert ledger["breaks"] == ["pack-leaping-pack: opened > held"]
    citizen = roadmap_record()
    assert citizen["roadmap_file"] == "roadmap_slices.yaml"
    assert citizen["parts"] == 11
    assert citizen["slices"] == 272
    assert citizen["done"] == len(load_roadmap().done())
    assert citizen["done"] == 248
    assert citizen["next_slice"] == "M-249"
    assert citizen["m236_title"] == "Skills standard"
    assert citizen["m236_part"] == 10
    assert citizen["m236_status"] == "done"

def test_pack_record_round_trips():
    pack = _pack()
    assert validate_pack(pack) is pack
    rebuilt = build_pack(pack.to_record())
    assert rebuilt == pack
    assert rebuilt.item_id == "pack-test"
    assert rebuilt.stage == "held"
    record = pack_record(pack)
    assert record["type"] == "pack_pack"
    assert record["complete"] is True
    assert record["gaps"] == []
    ref = _ref()
    assert skill_record(ref)["type"] == "pack_run"
    assert skill_record(ref)["state"] == "live"

def test_the_walk_is_derived_from_the_checks_alone():
    silent = _pack(stages=[])
    assert pack_gaps(silent) == (
        "has passed through no step: the pack has not started",)
    assert pack_green(silent) is False
    walking = _pack(stages=["found", "opened"])
    assert pack_gaps(walking) == (
        "has not reached held: the pack stands at opened",)
    assert walking.stage == "opened"
    sideways = _pack(stages=["opened", "vetted", "loaded", "held"])
    assert pack_gaps(sideways) == (
        "opens at opened, not at found: the pack opens "
        "with the reflection",)
    repaired = _pack(stages=["found", "opened", "vetted", "loaded", "found", "opened", "vetted", "loaded", "held"])
    assert pack_gaps(repaired) == ()
    assert pack_green(repaired) is True
    with pytest.raises(ValueError):
        _pack(stages=[42])
    with pytest.raises(ValueError):
        _pack(stages="inspect as a bare string")
    with pytest.raises(ValueError):
        _pack(stages=["found", "polish"])
    with pytest.raises(ValueError):
        _pack(claims=["weather"])
    with pytest.raises(ValueError):
        _pack(claims="instructions_ref")
    none_pack = _pack(stages=None, claims=None)
    assert none_pack.stages == ()
    assert none_pack.claims == ()

def test_scope_refuses_stored_judgements():
    for key in ("standing", "complete", "gaps", "segment", "verdict",
                "index", "packs", "coverage", "current_pack",
                "ledger", "pack"):
        fields = _pack().to_record()
        fields[key] = "x"
        with pytest.raises(ValueError):
            build_pack(fields)
    fields = _pack().to_record()
    fields["mystery"] = "x"
    with pytest.raises(ValueError):
        build_pack(fields)


def test_scope_refuses_a_live_claim():
    for key in ("builds_slice", "executes_slice", "banks_slice",
                "pushes_slice", "posts_note", "opens_network"):
        fields = _pack().to_record()
        fields[key] = True
        with pytest.raises(ValueError):
            build_pack(fields)


def test_pack_vocabularies_are_closed():
    with pytest.raises(ValueError):
        _pack(title="")
    with pytest.raises(ValueError):
        _pack(skill_id="   ")
    with pytest.raises(ValueError):
        _ref(state="blessed")
    with pytest.raises(ValueError):
        _note(stance="pinch")
    with pytest.raises(ValueError):
        _view(view_filter="some")
    with pytest.raises(ValueError):
        _trace(trace="")
    trace = _trace()
    assert trace.trace == "found > opened > vetted > loaded > held"
    assert trace.item_id == "trace-test"

def test_plain_telling_derives_from_the_packs_own_fields():
    pack = _pack(claims=["instructions_ref"])
    assert plain_lines(pack) == (
        "Pack: A test pack",
        "Skill: skill-test",
        "Stage: held",
        "Claims: instructions_ref")
    segment = segment_of(pack)
    assert segment.startswith("pack-test: A test pack")
    assert "stage: 'held'" in segment
    assert "gaps: none" in segment
    assert plain_words(pack).startswith(
        "A test pack - from skill-test")

def test_red_packs_stand_named_in_their_gaps():
    asking = _pack(claims=["feeling", "instructions_ref", "summary"])
    assert pack_gaps(asking) == (
        "carries a feeling claim, a bare claim with no held proof: complete stands on held proof alone",
        "carries a summary claim, a bare claim with no held proof: complete stands on held proof alone")
    assert pack_green(asking) is False
    skipping = _pack(stages=["found", "opened", "held"])
    assert pack_gaps(skipping) == (
        "steps from opened to held, which the pack sequence "
        "does not allow",)
    book = _book(packs=[
        _pack(),
        _pack(pack_id="pack-skipping", seq=2,
             stages=["found", "opened", "held"]),
    ])
    assert transition_breaks(book) == (
        "pack-skipping: opened > held",)
    assert current_pack(book).pack_id == "pack-skipping"
    assert [g.pack_id for g in pack_pack(book)] == [
        "pack-test", "pack-skipping"]

def test_view_and_note_round_trip():
    view = _view()
    assert validate_view(view) is view
    assert build_view(view.to_record()) == view
    assert view.item_id == "view-test"
    record = view_record(view)
    assert record["type"] == "pack_view"
    assert record["view_filter"] == "all"
    note = _note()
    assert validate_note(note) is note
    assert build_note(note.to_record()) == note
    assert note.item_id == "note-test"
    record = note_record(note)
    assert record["type"] == "pack_note"
    assert record["pack_id"] == "pack-test"
    assert view_plain_words(view) == "View view-test: shows all packs."
    assert "note-test" in note_plain_words(note)


def test_index_is_derived_from_the_held_packs_alone():
    book = _mixed_book()
    index = derive_index(book)
    assert [e.stage for e in index.packs] == ["held"]
    assert index.packs[0] == IndexPack(
        stage="held",
        pack_id="pack-test", title="A test pack")
    assert index.gaps == ("pack-hidden",)
    record = index_record(book)
    assert record["type"] == "pack_index"
    assert record["gaps"] == ["pack-hidden"]
    assert isinstance(book_record(book), dict)
    assert book_record(book)["type"] == "pack_book"

def test_check_target_reaches_its_pack_and_an_unheld_target_reaches_nothing():
    book = load_pack()
    assert pack_for_check(book, "held").pack_id == (
        "pack-held-pack")
    assert pack_for_check(book, "") is None
    assert pack_for_check(book, None) is None
    assert pack_for_check(book, "not held at all") is None
    text = format_stage(book, "not held at all")
    assert "reaches nothing in this book" in text

def test_first_note_is_held_as_data():
    book = load_pack()
    first = first_note(book)
    assert first.note_id == "note-note-first"
    assert first.stance == "note"
    text = format_note(first)
    assert "Pack note note pack-held-pack" in text
    assert "posts no note" in text


def test_note_targets_stand_held_whole():
    book = _book(notes=[_note()])
    assert book.note_for("note-test").pack_id == "pack-test"
    assert note_for_pack(book, "pack-test").note_id == "note-test"
    assert note_for_pack(book, "pack-test", "praise") is None
    with pytest.raises(KeyError):
        book.note_for("note-nope")
    with pytest.raises(ValueError):
        _book(notes=[_note(), _note(note_id="note-two", seq=2)])


def test_panel_is_derived_and_a_stored_panel_must_agree():
    book = _mixed_book()
    panel = derive_panel(book)
    assert panel.panel_id == "panel-view-test"
    assert panel.total_items == 2
    assert panel.total_shown == 2
    assert {c.standing: c.items for c in panel.target_counts} == {
        "complete": 1, "open": 1}
    assert validate_panel(panel, book) is panel
    assert build_panel(panel.to_record(), book) == panel
    row = build_row(None, _pack(), book)
    assert row.standing == "complete"
    assert validate_row(row, _pack(), book) is row
    bad = dict(panel.to_record())
    bad["total_shown"] = 9
    with pytest.raises(ValueError):
        build_panel(bad, book)


def test_verdict_is_derived_from_the_shown_packs():
    book = _mixed_book()
    verdict = derive_verdict(book)
    assert verdict.verdict == "held"
    assert verdict.green_shown == 1
    assert verdict.total_shown == 2
    assert validate_verdict(verdict, book) is verdict
    assert build_verdict(verdict.to_record(), book) == verdict
    assert verdict_record(verdict, book)["type"] == "pack_verdict"
    green_book = _book(views=[_view(view_filter="complete")])
    assert derive_verdict(green_book).verdict == "held"
    empty_book = _book(packs=[_pack(stages=[])],
                       views=[_view(view_filter="complete")])
    shut = derive_verdict(empty_book)
    assert shut.verdict == "blocked"
    assert shut.total_shown == 0
    with pytest.raises(ValueError):
        validate_verdict(PackVerdict(
            verdict="ajar", view_id="view-test", total_shown=1,
            green_shown=1, latest_on=ON))


def test_shown_and_slice_packs():
    book = load_pack()
    assert [g.pack_id for g in shown_packs(book)] == list(
        EXAMPLE_RUN_IDS)
    assert [g.pack_id for g in shown_packs(book, "view-held")] == [
        "pack-held-pack", "pack-retried-pack", "pack-own-pack"]
    assert [g.pack_id for g in packs_for_skill(
        book, "skill-second-brain")] == [
            "pack-own-pack", "pack-bare-pack",
            "pack-leaping-pack"]
    assert packs_for_skill(book, "skill-nope") == ()
    assert current_pack(_mixed_book()).pack_id == "pack-hidden"
    assert current_pack(_book()) is None
    stale = _book(traces=[_trace(trace="charter > build")])
    assert trace_of(stale, "pack-test") == (
        "found > opened > vetted > loaded > held")
    assert trace_current(stale, "pack-test") is False
    assert ledger_record(stale)["traces"] == [
        {"pack_id": "pack-test", "trace": "stale"}]

def test_resources_refuses_duplicates_and_stored_verdicts():
    with pytest.raises(ValueError):
        _book(packs=[_pack(), _pack(seq=2)])
    with pytest.raises(ValueError):
        _book(packs=[_pack(), _pack(pack_id="pack-two")])
    with pytest.raises(ValueError):
        _book(views=[_view(), _view(seq=2)])
    with pytest.raises(ValueError):
        _book(packs=[_pack(skill_id="skill-nope")])
    with pytest.raises(ValueError):
        _book(skills=[_ref(), _ref(
            skill_id="skill-cold", seq=2, state="dormant")],
            packs=[_pack(skill_id="skill-cold")])
    with pytest.raises(ValueError):
        _book(traces=[_trace(), _trace(
            trace_id="trace-two", seq=2)])
    with pytest.raises(ValueError):
        _book(traces=[_trace(skill_id="skill-nope")])
    fields = {
        "schema": PACK_SCHEMA, "skill": "M-236",
        "skills_standard": {"title": "A vetted book"},
        "skills": [_ref().to_record()],
        "pack_records": [_pack().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": [],
        "verdict": "held"}
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("verdict")
    fields["current_pack"] = "pack-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("current_pack")
    fields["trace"] = "pack-test"
    with pytest.raises(ValueError):
        build_book(fields)
    fields.pop("trace")
    fields["builds_slice"] = True
    with pytest.raises(ValueError):
        build_book(fields)


def test_book_from_a_file_loads_anywhere(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / PACK_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "skills_standard.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_pack_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.pack_ids() == EXAMPLE_RUN_IDS


def test_registry_holds_records_one_by_one():
    registry = PackRegistry()
    assert registry.title() is None
    registry.register_skill_ref(_ref())
    registry.register_pack(_pack())
    registry.register_view(_view())
    assert [g.pack_id for g in registry.list_packs()] == ["pack-test"]
    assert [v.view_id for v in registry.list_views()] == ["view-test"]
    assert registry.get_pack("pack-test").title == "A test pack"
    assert registry.get_slice("skill-test").state == "live"
    assert registry.get_view("view-test").view_filter == "all"
    assert registry.get_item("pack-test").pack_id == "pack-test"
    with pytest.raises(ValueError):
        registry.register_pack(_pack(seq=9))
    with pytest.raises(ValueError):
        registry.register_pack(_pack(pack_id="pack-two"))
    with pytest.raises(KeyError):
        registry.get_pack("pack-nope")
    assert registry.book().title == "An unheld pack book"


def test_registry_register_book_holds_whole_and_refuses_second_title():
    registry = PackRegistry()
    book = registry.register_book(_mixed_book())
    assert book.title == "A test pack book"
    assert registry.title() == "A test pack book"
    assert len(registry.list_packs()) == 2
    other = PackRegistry()
    other.register_book(_book())
    with pytest.raises(ValueError):
        other.register_book(_mixed_book())


def test_plain_words_and_formatters():
    pack = _pack()
    assert "A test pack" in plain_words(pack)
    assert panel_plain_words(_mixed_book()).startswith(
        "The pack book holds 2 packs")
    assert verdict_plain_words(_mixed_book()) == (
        "The packs stand held: 1 of 2 shown packs stand complete.")
    assert index_plain_words(_mixed_book()) == (
        "The index holds 1 green packs; red, "
        "found in its gaps: pack-hidden.")
    assert format_view(_view()).startswith("View view-test: filter all")
    text = format_pack(pack)
    assert "Pack: A test pack" in text
    assert "stands complete" in text
    text = format_pack(_pack(stages=[]))
    assert "stands open" in text
    assert "has passed through no step" in text
    book_text = format_book(_mixed_book())
    assert "The Skills Standard (M-236) - A test pack book" in book_text
    assert "pack-hidden" in format_book(_mixed_book(), "skill-test")
    assert "Pack panel under view view-test" in format_panel(_mixed_book())
    assert "held" in format_verdict(_mixed_book())
    index_text = format_index(_mixed_book())
    assert "held - A test pack (pack-test)" in index_text
    assert "pack-hidden" in index_text
    screen = format_pack_screen()
    assert "The Skills Standard (M-236)" in screen
    assert "pack-bare-pack" in screen

def test_parse_args_well_and_loader_targets():
    assert parse_pack_args("") == ("show", None)
    assert parse_pack_args(None) == ("show", None)
    assert parse_pack_args("show") == ("show", None)
    assert parse_pack_args("pack pack-test") == (
        "pack", "pack-test")
    assert parse_pack_args("stage held") == (
        "stage", "held")
    assert parse_pack_args("skill skill-test") == (
        "skill", "skill-test")
    assert parse_pack_args("view view-test") == ("view", "view-test")
    assert parse_pack_args("note note-test") == ("note", "note-test")
    assert parse_pack_args("index") == ("index", None)
    assert parse_pack_args("panel") == ("panel", None)
    assert parse_pack_args("verdict") == ("verdict", None)
    for bad in ("dance", "pack", "stage", "skill", "index now",
                "stance a b"):
        with pytest.raises(ValueError):
            parse_pack_args(bad)
    ledger = ledger_record()
    assert ledger["type"] == "pack_well"
    assert ledger["total"] == 5
    assert ledger["current_pack"] == "pack-bare-pack"
    book = load_pack({
        "schema": PACK_SCHEMA, "skill": "M-236",
        "skills_standard": {"title": "A vetted book"},
        "skills": [_ref().to_record()],
        "pack_records": [_pack().to_record()],
        "views": [_view().to_record()], "notes": [],
        "traces": [], "panels": []})
    assert isinstance(book, PackBook)
    assert book.title == "A vetted book"
    assert validate_book(book) is book
    with pytest.raises(ValueError):
        load_pack({"schema": "other/9"})
    with pytest.raises(ValueError):
        load_pack({"skill": "M-999"})
    built = build_pack(
        pack_id="pack-kw", seq=3, skill_id="skill-test",
        title="Kw Pack", stages=["found", "opened", "vetted", "loaded", "held"],
        claims=[], detail="Built by fields.",
        recorded_on=ON, actor=BY,
        source="test source", origin_session="pack-test")
    assert built.pack_id == "pack-kw"
    assert pack_green(built) is True

# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# M-236 agent layer: the agent holds a pack
# book for the session, packs and views are
# published as session news through the
# checkpoint target (ledger first, deduped per
# trace), the panel and verdict are derived at
# call time from the whole book under a view,
# never held, the index is derived from the
# book's held packs, the ledger is derived from
# the held packs' completeness, the roadmap standing
# is loaded from the shipped roadmap itself, and the
# stance targets are held as data beside them -
# holding one builds no skill. This layer packs
# nothing, executes nothing, banks nothing and
# persists nothing beyond the session ledger news.
# ---------------------------------------------------------------------

from mythic_agent.core.sessions import SessionStore as _SessionStore

_PACK_EVENT_TYPES = (
    "pack_pack", "pack_run", "pack_view",
    "pack_panel", "pack_verdict")


def _pack_events(store, session_id, skill):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == skill]


def _write_skillsstandard_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / PACK_RESOURCE
           ).read_text(encoding="utf-8")
    path = tmp_path / "skills_standard.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestPackAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.skillsstandard_status()
        assert status["pack_records"] == []
        assert status["skills"] == []
        assert status["views"] == []
        assert status["book"] is None
        assert status["skillsstandard_book"]["title"] == EXAMPLE_TITLE
        assert len(status["skillsstandard_book"]["skills"]) == 3
        assert len(status["skillsstandard_book"]["pack_records"]) == 5
        assert len(status["skillsstandard_book"]["views"]) == 2
        assert len(status["skillsstandard_book"]["notes"]) == 2
        assert len(status["skillsstandard_book"]["traces"]) == 1
        assert status["panel"]["total_items"] == 5
        assert status["panel"]["total_shown"] == 5
        assert status["panels"][0]["panel_id"] == "panel-skill"
        assert status["verdict"]["verdict"] == "held"
        assert status["verdict"]["green_shown"] == 3
        assert [e["stage"] for e in status["index"]["packs"]] == (
            EXAMPLE_STAGES)
        assert status["index"]["gaps"] == [
            "pack-bare-pack", "pack-leaping-pack"]
        assert status["first_note"]["note_id"] == "note-note-first"
        assert status["ledger"]["total"] == 5
        assert status["ledger"]["current_pack"] == "pack-bare-pack"
        assert status["roadmap"]["slices"] == 272
        assert status["roadmap"]["parts"] == 11
        assert status["roadmap"]["done"] == 248
        assert status["roadmap"]["next_slice"] == "M-249"
        assert status["roadmap"]["m236_title"] == "Skills standard"
        assert "held as data alone" in status["rule"]
        assert "pack-bare-pack" in status["plain_words"]
        assert "The Skills Standard (M-236)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION
    def test_registry_is_one_per_agent(self, agent):
        first = agent._skillsstandard_registry()
        assert agent._skillsstandard_registry() is first
        assert agent._skillsstandard_store is first
        for name in ("skillsstandard_book", "skillsstandard_status", "skillsstandard_panel",
                     "skillsstandard_verdict", "skillsstandard_index", "report_skillsstandard"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_skillsstandard_registry", "skillsstandard_book", "skillsstandard_status",
            "get_skillsstandard_pack", "get_skillsstandard_view", "get_skillsstandard_note",
            "packs_for_skill", "skillsstandard_green",
            "skillsstandard_panel", "skillsstandard_verdict", "skillsstandard_index",
            "register_skillsstandard_pack", "register_skillsstandard_view",
            "view_skillsstandard", "register_skillsstandard_book",
            "record_skillsstandard_book", "report_skillsstandard",
            "_publish_skillsstandard_record", "_skillsstandard_screen",
            "_skillsstandard_default_view"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.skillsstandard_status()
        assert agent.get_skillsstandard_pack(
            "pack-held-pack").title == "The held pack"
        assert agent.get_skillsstandard_view(
            "view-packs").view_filter == "all"
        assert agent.get_skillsstandard_note(
            "note-note-first").note_id == "note-note-first"
        assert [d.pack_id for d in agent.packs_for_skill(
            "skill-second-brain")] == [
            "pack-own-pack", "pack-bare-pack",
            "pack-leaping-pack"]
        assert [d.pack_id for d in agent.skillsstandard_green()] == [
            "pack-held-pack", "pack-retried-pack", "pack-own-pack"]
        agent.skillsstandard_panel()
        agent.skillsstandard_verdict()
        agent.skillsstandard_index()
        agent.report_skillsstandard()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _PACK_EVENT_TYPES] == []
        with pytest.raises(KeyError):
            agent.get_skillsstandard_pack("pack-nope")
        with pytest.raises(KeyError):
            agent.get_skillsstandard_view("view-nope")
        with pytest.raises(KeyError):
            agent.get_skillsstandard_note("note-nope")
        with pytest.raises(ValueError):
            agent.packs_for_skill("")
        agent.close()
    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_skillsstandard_pack(_pack())
        status = agent.skillsstandard_status()
        assert [d["pack_id"] for d in status["pack_records"]] == ["pack-test"]
        assert status["book"]["title"] == "An unheld pack book"
        assert status["panel"] is None
        assert status["verdict"] is None
        assert [e["stage"] for e in status["index"]["packs"]] == [
            "held"]
        assert status["first_note"] is None
        assert "pack-test" in status["screen"]
    def test_held_pack_never_falls_back_to_the_example(
            self, agent):
        agent.register_skillsstandard_pack(_pack())
        with pytest.raises(KeyError):
            agent.get_skillsstandard_pack("pack-held-pack")
        with pytest.raises(KeyError):
            agent.get_skillsstandard_view("view-packs")
        with pytest.raises(KeyError):
            agent.get_skillsstandard_note("note-note-first")
        pack = agent.get_skillsstandard_pack("pack-test")
        assert pack.title == "A test pack"
        assert agent.skillsstandard_book().title == (
            "An unheld pack book")
    def test_notes_and_index_stand_in_the_example(self, agent):
        first = agent.get_skillsstandard_note("note-note-first")
        assert first.note_id == "note-note-first"
        assert first.pack_id == "pack-held-pack"
        status = agent.skillsstandard_status()
        assert status["index"]["gaps"] == [
            "pack-bare-pack", "pack-leaping-pack"]
        assert status["first_note"]["pack_id"] == (
            "pack-held-pack")
        assert status["first_note"]["stance"] == "note"

class TestPackAgentHolding:
    def test_register_pack_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_skillsstandard_pack(_pack())
        assert result["pack"]["pack_id"] == "pack-test"
        assert result["record_news"]["type"] == "pack_pack"
        assert "pack-test" in result["screen"]
        events = _pack_events(store, session_id, "pack_pack")
        assert len(events) == 1
        agent.close()

    def test_duplicate_scope_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_skillsstandard_pack(_pack())
        with pytest.raises(ValueError):
            agent.register_skillsstandard_pack(_pack(seq=9))
        with pytest.raises(ValueError):
            agent.register_skillsstandard_pack(_pack(pack_id="pack-two"))
        events = _pack_events(store, session_id, "pack_pack")
        assert len(events) == 1
        agent.close()

    def test_register_view_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_skillsstandard_view(_view())
        assert result["view"]["view_id"] == "view-test"
        assert len(_pack_events(
            store, session_id, "pack_view")) == 1
        agent.close()

    def test_view_target_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_skillsstandard_pack(_pack())
        result = agent.view_skillsstandard("complete")
        assert result["view"]["view_filter"] == "complete"
        assert result["view"]["seq"] == 1
        assert result["panel_record"]["type"] == "pack_panel"
        assert result["panel_record"]["total_shown"] == 1
        assert result["verdict_record"]["verdict"] == "held"
        assert len(_pack_events(
            store, session_id, "pack_view")) == 1
        assert len(_pack_events(
            store, session_id, "pack_panel")) == 1
        assert len(_pack_events(
            store, session_id, "pack_verdict")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_pack(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_skillsstandard_book(_book(views=[_view()]))
        assert result["count"] == 1
        assert [r["type"] for r in result["records_news"]] == [
            "pack_run", "pack_pack", "pack_view"]
        assert len(_pack_events(
            store, session_id, "pack_pack")) == 1
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_skillsstandard_book()
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE
        assert result["panel_record"]["type"] == "pack_panel"
        assert result["index_record"]["gaps"] == [
            "pack-bare-pack", "pack-leaping-pack"]
        with pytest.raises(ValueError):
            agent.record_skillsstandard_book()
        assert len(_pack_events(
            store, session_id, "pack_run")) == 3
        assert len(_pack_events(
            store, session_id, "pack_pack")) == 5
        assert len(_pack_events(
            store, session_id, "pack_view")) == 2
        agent.close()

    def test_book_from_a_file_is_linked_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_skillsstandard_book_file(tmp_path)
        book = load_pack_file(path)
        result = agent.record_skillsstandard_book(book)
        assert result["count"] == 5
        assert result["book"]["title"] == EXAMPLE_TITLE

    def test_runrt_renders_example_then_held_book_only(self, agent):
        pack = agent.report_skillsstandard()
        assert pack["book"]["title"] == EXAMPLE_TITLE
        assert pack["verdict"]["verdict"] == "held"
        assert pack["index"]["gaps"] == [
            "pack-bare-pack", "pack-leaping-pack"]
        assert "pack-held-pack" in pack["book_text"]
        assert "held - The held pack (pack-held-pack)" in pack["index_text"]
        agent.register_skillsstandard_pack(_pack())
        pack = agent.report_skillsstandard()
        assert pack["book"]["title"] == "An unheld pack book"
        assert pack["panel"] is None
        assert pack["verdict"] is None

class TestPackTerminalHeading:
    def test_show_pack_check_slice_view_note_index_panel_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/skillsstandard")
        assert "The Skills Standard (M-236)" in text
        _, _, text = _slash(agent, "/skillsstandard pack pack-held-pack")
        assert "Pack: The held pack" in text
        _, _, text = _slash(
            agent, "/skillsstandard stage held")
        assert "Pack: The held pack" in text
        _, _, text = _slash(agent, "/skillsstandard stage triple pack")
        assert "reaches nothing in this book" in text
        _, _, text = _slash(agent, "/skillsstandard skill skill-second-brain")
        assert "pack-bare-pack" in text
        assert "pack-held-pack" not in text
        _, _, text = _slash(agent, "/skillsstandard view view-packs")
        assert "filter all" in text
        _, _, text = _slash(agent, "/skillsstandard note note-note-first")
        assert "Pack note note pack-held-pack" in text
        _, _, text = _slash(agent, "/skillsstandard index")
        assert "Pack index" in text
        assert "pack-bare-pack" in text
        _, _, text = _slash(agent, "/skillsstandard panel")
        assert "Pack panel under view view-packs" in text
        _, _, text = _slash(agent, "/skillsstandard verdict")
        assert "held" in text
    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/skillsstandard [show|pack <pack-id>"
                "|stage <stage>|skill <skill-id>"
                "|view <view-id>|note <note-id>|index|panel|verdict]") in text
        _, _, text = _slash(agent, "/skillsstandard dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/skillsstandard pack pack-nope")
        assert "no pack found" in text
@pytest.fixture()
def pack_handler(agent, monkeypatch):
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


def _pack_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestPackCommand:
    def test_show_is_default(self, pack_handler, agent):
        pack_handler._handle_skillsstandard("")
        assert "The Skills Standard (M-236)" in (
            _pack_published_text(pack_handler))

    def test_pack_check_slice_view_note_index_panel_verdict(
            self, pack_handler, agent):
        pack_handler._handle_skillsstandard("pack pack-held-pack")
        assert "Pack: The held pack" in _pack_published_text(
            pack_handler)
        pack_handler._handle_skillsstandard(
            "stage held")
        assert "Pack: The held pack" in _pack_published_text(
            pack_handler)
        pack_handler._handle_skillsstandard("skill skill-second-brain")
        assert "pack-bare-pack" in _pack_published_text(
            pack_handler)
        pack_handler._handle_skillsstandard("view view-packs")
        assert "filter all" in _pack_published_text(pack_handler)
        pack_handler._handle_skillsstandard("note note-note-first")
        assert "Pack note note pack-held-pack" in (
            _pack_published_text(pack_handler))
        pack_handler._handle_skillsstandard("index")
        assert "Pack index" in _pack_published_text(pack_handler)
        pack_handler._handle_skillsstandard("panel")
        assert "Pack panel under view" in _pack_published_text(
            pack_handler)
        pack_handler._handle_skillsstandard("verdict")
        assert "held" in _pack_published_text(pack_handler)
    def test_bad_grammar_is_published(
            self, pack_handler, agent):
        pack_handler._handle_skillsstandard("dance party")
        assert USAGE in _pack_published_text(pack_handler)
        pack_handler._handle_skillsstandard("pack pack-nope")
        assert "no pack found" in _pack_published_text(
            pack_handler)


class TestChatScreenRoutingPack:
    def test_onwell_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/skillsstandard panel", _FakeLog())
        assert calls == [("/skillsstandard", "panel")]

    def test_chat_screen_help_and_usage_name_the_book(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/skillsstandard[/green] - show the Skills standard (M-236)" in (
            text)
        assert ('"/skillsstandard": "Usage: /skillsstandard | '
                '/skillsstandard pack <pack-id>') in text

class TestPackDerivedTargets:
    def test_panel_and_verdict_are_derived_at_call_time(self, agent):
        panel = agent.skillsstandard_panel()
        assert panel.total_shown == 5
        assert panel.panel_id == "panel-view-packs"
        verdict = agent.skillsstandard_verdict()
        assert verdict.verdict == "held"
        found = agent.skillsstandard_verdict("view-held")
        assert found.verdict == "held"
        assert found.green_shown == 3
        agent.register_skillsstandard_pack(_pack())
        with pytest.raises(ValueError):
            agent.skillsstandard_panel()
        with pytest.raises(ValueError):
            agent.skillsstandard_verdict()

    def test_view_target_over_an_unshown_filter_is_blocked(self, agent):
        agent.register_skillsstandard_pack(_pack(stages=[]))
        result = agent.view_skillsstandard("complete")
        assert result["verdict_record"]["verdict"] == "blocked"
        assert result["verdict_record"]["total_shown"] == 0

    def test_index_target_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.skillsstandard_index()
        assert [e["stage"] for e in result["index"]["packs"]] == (
            EXAMPLE_STAGES)
        assert result["index"]["gaps"] == [
            "pack-bare-pack", "pack-leaping-pack"]
        assert "held - The held pack (pack-held-pack)" in (
            result["index_text"])
        pack = agent.get_skillsstandard_pack("pack-leaping-pack")
        assert pack_gaps(pack, agent.skillsstandard_book()) == (
            "steps from opened to held, which the pack sequence "
            "does not allow",)
        assert pack_green(pack, agent.skillsstandard_book()) is False
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _PACK_EVENT_TYPES] == []
        agent.close()
