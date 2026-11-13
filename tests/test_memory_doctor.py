"""M-168 Memory Doctor - pure-layer tests.

TIER: integration

The pure layer is the memory finding, held as
data: one finding standing over one stored memory
- named by the kind of holding it stands in and
the shipped piece's id alone, the piece's own
words never crossing - carrying its provenance
whole (the check that raised it - a corrupt store,
an orphaned vector, or map drift; the store the
memory lives in, the workspace store or the user
store; what the check saw; how far the trouble
reaches - one contained piece, or the store as a
whole; who ran the check, the session it ran in
and where the finding was read from), composed by
import from the shipped holdings it stands over
(the project memory map M-150, session memory
M-153, cross-project memory M-154, the
self-improving ledger M-155, crew memory M-133,
the subconscious v2 M-165, the contradiction watch
M-166 and private by architecture M-167), each
judged by its own layer's validation, ids and refs
only across the seams. The repair is derived,
never chosen: quarantine a contained corrupt
piece, drop an orphaned vector, realign a drifted
map entry - and a store-wide trouble derives no
repair at all and stands referred to the user. One
check stands once over one stored memory in a
book, so a check's word never forks. A doctor
panel is derived from the whole book (every
finding carried whole, in a settled order, its
derived repair shown on every row), a doctor
verdict is derived for the whole book - a book
with referred trouble is named ailing or critical
plainly, never smoothed - the repairs are derived
from the whole book, the shipped example book is
held in a data file, and a loader reads a book
from any file. Nothing here sends, posts,
schedules, calls a model, persists anything or
writes any live memory: a repair applied here
marks a held finding repaired in the registry's
own book, and no live store is rewritten.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.contradiction_watch import load_contradiction_watch
from mythic_agent.core.crew_memory import load_crew_memory
from mythic_agent.core.cross_project_memory import (
    load_cross_project_memory)
from mythic_agent.core.private_by_architecture import (
    load_private_by_architecture)
from mythic_agent.core.project_memory_map import load_project_memory_map
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.self_improving_ledger import (
    load_self_improving_ledger)
from mythic_agent.core.session_memory import load_session_memory
from mythic_agent.core.subconscious_v2 import load_subconscious_v2
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.memory_doctor import (
    CHECKS,
    DISPOSITIONS,
    EXTENTS,
    MEMORY_KINDS,
    PLAIN_EXPLANATION,
    MEMORY_DOCTOR_RESOURCE,
    MEMORY_DOCTOR_SCHEMA,
    MEMORY_DOCTOR_SLICE,
    REFERRED_ACTION,
    REPAIR_ACTIONS,
    STORES,
    USAGE,
    VERDICT_WORDS,
    CheckCount,
    DoctorBook,
    DoctorPanel,
    DoctorRegistry,
    DoctorRepair,
    DoctorVerdict,
    MemoryFinding,
    book_record,
    build_book,
    build_finding,
    build_panel,
    build_repair,
    build_row,
    build_verdict,
    derive_panel,
    derive_repairs,
    derive_verdict,
    disposition_of,
    finding_for,
    finding_from_contradiction_watch,
    finding_from_corrupt_piece,
    finding_from_crew_entry,
    finding_from_cross_project_lesson,
    finding_from_drifted_map_entry,
    finding_from_ledger_candidate,
    finding_from_map_entry,
    finding_from_orphaned_vector,
    finding_from_privacy_posting,
    finding_from_session_note,
    finding_from_subconscious_memory,
    finding_record,
    finding_refs,
    format_finding,
    format_findings,
    format_memory_doctor_screen,
    format_panel,
    format_repairs,
    format_verdict,
    inspect_finding_source,
    load_memory_doctor,
    load_memory_doctor_file,
    normalize_check,
    normalize_extent,
    normalize_memory_kind,
    normalize_store,
    panel_plain_words,
    panel_record,
    parse_memory_doctor_args,
    plain_words,
    repair_action_of,
    repair_line,
    repair_record,
    repairs_plain_words,
    total_findings,
    validate_book,
    validate_finding,
    validate_panel,
    validate_repair,
    validate_row,
    validate_verdict,
    verdict_plain_words,
    verdict_record,
)

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Memory Doctor at the M-167 slice boundary"

BY = "Volmarr"
ON = "2026-11-09"


def _finding(**overrides):
    fields = {
        "finding_id": "finding-test",
        "title": "the test finding, raised by hand",
        "check": "corrupt-store",
        "memory_kind": "manual",
        "memory_ref": "ref-test",
        "store": "workspace",
        "detail": "the test piece fails its own validation",
        "found_on": ON,
        "recorded_by": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_finding(fields)


def _referred_finding(**overrides):
    fields = {"extent": "store-wide"}
    fields.update(overrides)
    return _finding(**fields)


def _stored_finding(finding):
    stored = finding.to_record()
    for key in ("type", "slice", "disposition", "action", "repair"):
        stored.pop(key)
    return stored


def _clean(record):
    cleaned = dict(record)
    for key in ("type", "slice"):
        cleaned.pop(key, None)
    return cleaned


# ---------------------------------------------------------------------
# The shipped example book and the roadmap.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_memory_doctor()
    assert book.title == EXAMPLE_TITLE
    assert book.finding_ids() == (
        "finding-verify-remote-corrupt", "finding-archival-alpha-orphan",
        "finding-no-docker-drift", "finding-samtal-wal-store",
        "finding-campaign-home-drift")
    assert book.total_findings == 5
    assert len(book.panels) == 1
    panel = book.panel_for("panel-m167-boundary")
    assert panel.as_of == ON
    assert panel.total_findings == 5
    assert panel.total_ready == 4
    assert panel.total_referred == 1
    assert panel.distinct_memories == 5
    first = book.findings[0]
    assert first.finding_id == "finding-verify-remote-corrupt"
    assert first.title == (
        "the verify-remote candidate fails its own ledger validation")
    assert book.finding_for_check(
        "map-drift", "session-note", "note-campaign-home").finding_id == (
            "finding-campaign-home-drift")
    referred = book.finding_for("finding-samtal-wal-store")
    assert referred.extent == "store-wide"
    assert disposition_of(referred) == "referred"
    assert repair_action_of(referred) == REFERRED_ACTION


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-168")]
    assert slice_.title == "Memory Doctor"
    assert "mythic doctor" in slice_.summary
    assert "corrupt stores" in slice_.summary
    assert "orphaned vectors" in slice_.summary
    assert "map drift" in slice_.summary
    assert "safe" in slice_.summary
    assert MEMORY_DOCTOR_SLICE == "M-168"
    assert MEMORY_DOCTOR_SCHEMA == "mythic.memory_doctor/1"
    assert MEMORY_DOCTOR_RESOURCE == "memory_doctor.yaml"


def test_closed_vocabularies():
    assert CHECKS == ("corrupt-store", "orphaned-vector", "map-drift")
    assert MEMORY_KINDS == (
        "memory-map", "session-note", "cross-project-lesson",
        "ledger-candidate", "crew-fact", "subconscious-memory",
        "contradiction-watch", "vector-record", "manual")
    assert STORES == ("workspace", "user")
    assert EXTENTS == ("contained", "store-wide")
    assert DISPOSITIONS == ("repair-ready", "referred")
    assert REPAIR_ACTIONS == (
        "quarantine-piece", "drop-orphan-vector",
        "realign-map-entry", "none-referred")
    assert VERDICT_WORDS == ("sound", "ailing", "critical")
    assert REFERRED_ACTION == "none-referred"
    assert normalize_check("CORRUPT") == "corrupt-store"
    assert normalize_check("drift") == "map-drift"
    assert normalize_memory_kind("MAP") == "memory-map"
    assert normalize_memory_kind("watch") == "contradiction-watch"
    assert normalize_store("workspace-store") == "workspace"
    assert normalize_store("USER") == "user"
    assert normalize_extent("whole-store") == "store-wide"
    assert normalize_extent("single") == "contained"
    with pytest.raises(ValueError):
        normalize_check("lint")
    with pytest.raises(ValueError):
        normalize_memory_kind("dream")
    with pytest.raises(ValueError):
        normalize_store("cloud")
    with pytest.raises(ValueError):
        normalize_extent("everywhere")


# ---------------------------------------------------------------------
# The finding record: provenance whole, judged whole.
# ---------------------------------------------------------------------


def test_finding_record_round_trips():
    finding = _finding()
    assert validate_finding(_stored_finding(finding)) == finding
    record = finding.to_record()
    assert record["type"] == "memory_doctor_finding"
    assert record["slice"] == "M-168"
    assert record["disposition"] == "repair-ready"
    assert record["action"] == "quarantine-piece"
    assert record["repair"] == repair_line(finding)
    referred = _referred_finding()
    assert referred.to_record()["disposition"] == "referred"
    assert referred.to_record()["action"] == "none-referred"


def test_finding_provenance_is_whole_and_required():
    for field in ("title", "check", "memory_kind", "memory_ref",
                  "store", "detail", "found_on", "recorded_by",
                  "source", "origin_session"):
        fields = _stored_finding(_finding())
        fields.pop(field)
        with pytest.raises(ValueError):
            build_finding(fields)


def test_finding_refuses_unknown_keys_and_split_spellings():
    fields = _stored_finding(_finding())
    fields["dream"] = "x"
    with pytest.raises(ValueError):
        build_finding(fields)
    fields = _stored_finding(_finding())
    fields["disposition"] = "referred"
    with pytest.raises(ValueError):
        build_finding(fields)
    fields = _stored_finding(_finding())
    fields["home"] = "user"
    with pytest.raises(ValueError):
        build_finding(fields)


def test_finding_alias_spellings_read_onto_the_fields():
    finding = build_finding({
        "name": "an alias finding", "check_kind": "corrupt",
        "kind": "map", "ref": "ref-alias", "home": "user-store",
        "evidence": "the alias piece fails", "reach": "single",
        "day": ON, "by": BY, "source": "test source",
        "session": "session-test", "id": "finding-alias"})
    assert finding.check == "corrupt-store"
    assert finding.memory_kind == "memory-map"
    assert finding.memory_ref == "ref-alias"
    assert finding.store == "user"
    assert finding.extent == "contained"
    assert finding.finding_id == "finding-alias"
    assert finding.origin_session == "session-test"


def test_repair_is_always_derived():
    corrupt = _finding()
    assert disposition_of(corrupt) == "repair-ready"
    assert repair_action_of(corrupt) == "quarantine-piece"
    orphan = _finding(check="orphaned-vector",
                      memory_kind="vector-record")
    assert repair_action_of(orphan) == "drop-orphan-vector"
    drift = _finding(check="map-drift", memory_kind="memory-map")
    assert repair_action_of(drift) == "realign-map-entry"
    line = repair_line(drift)
    assert "realign-map-entry" in line
    assert "no live store is rewritten" in line
    referred = _referred_finding(check="map-drift")
    assert disposition_of(referred) == "referred"
    assert repair_action_of(referred) == "none-referred"
    line = repair_line(referred)
    assert "reaches the whole workspace store" in line
    assert "the doctor will not repair it" in line
    with pytest.raises(ValueError):
        _finding(found_on="Nov 9 2026")
    with pytest.raises(ValueError):
        _finding(memory_ref="two words")
    with pytest.raises(ValueError):
        _finding(store="cloud")


# ---------------------------------------------------------------------
# Composition by import: ids only across the seams.
# ---------------------------------------------------------------------


def test_finding_from_map_entry_carries_id_only():
    entry = load_project_memory_map().entries[0]
    finding = finding_from_map_entry(
        entry, check="map-drift", store="workspace",
        detail="the named path moved", found_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert finding.memory_kind == "memory-map"
    assert finding.memory_ref == entry.entry_id
    assert finding.finding_id == f"finding-map-drift-{entry.entry_id}"
    assert disposition_of(finding) == "repair-ready"
    assert entry.detail not in finding.title
    assert entry.detail not in finding.detail


def test_finding_from_session_note_and_cross_project_lesson():
    note = load_session_memory().situations[0].memory[0]
    finding = finding_from_session_note(
        note, check="map-drift", store="user",
        detail="the note drifted", found_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert finding.memory_kind == "session-note"
    assert finding.memory_ref == note.note_id
    lesson = load_cross_project_memory().lessons[0]
    carried = finding_from_cross_project_lesson(
        lesson, check="corrupt-store", store="workspace",
        detail="the lesson record fails", found_on=ON, recorded_by=BY,
        origin_session="session-test", extent="store-wide")
    assert carried.memory_kind == "cross-project-lesson"
    assert carried.memory_ref == lesson.lesson_id
    assert disposition_of(carried) == "referred"


def test_finding_from_ledger_candidate_and_crew_entry():
    candidate = load_self_improving_ledger().candidates[0]
    finding = finding_from_ledger_candidate(
        candidate, check="corrupt-store", store="workspace",
        detail="the candidate record fails", found_on=ON,
        recorded_by=BY, origin_session="session-test")
    assert finding.memory_kind == "ledger-candidate"
    assert finding.memory_ref == candidate.candidate_id
    entry = load_crew_memory().notebooks[0].entries[0]
    fact = finding_from_crew_entry(
        entry, check="corrupt-store", store="user",
        detail="the crew record fails", found_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert fact.memory_kind == "crew-fact"
    assert fact.memory_ref == entry.entry_id
    assert entry.fact not in fact.title


def test_finding_from_subconscious_memory_carries_id_only():
    memory = load_subconscious_v2().memories[0]
    finding = finding_from_subconscious_memory(
        memory, check="corrupt-store", store="workspace",
        detail="the v2 record fails", found_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert finding.memory_kind == "subconscious-memory"
    assert finding.memory_ref == memory.memory_id
    assert memory.title not in finding.title


def test_finding_from_contradiction_watch_carries_id_only():
    watch = load_contradiction_watch().watches[0]
    finding = finding_from_contradiction_watch(
        watch, check="corrupt-store", store="workspace",
        detail="the watch record fails", found_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert finding.memory_kind == "contradiction-watch"
    assert finding.memory_ref == watch.watch_id
    assert finding.finding_id == (
        f"finding-corrupt-store-{watch.watch_id}")
    assert watch.stored_claim not in finding.title
    assert watch.evidence_claim not in finding.title


def test_finding_from_privacy_posting_carries_memory_only():
    posting = load_private_by_architecture().postings[0]
    finding = finding_from_privacy_posting(
        posting, check="map-drift",
        detail="the posted memory drifted", found_on=ON,
        recorded_by=BY, origin_session="session-test")
    assert finding.memory_kind == posting.memory_kind
    assert finding.memory_ref == posting.memory_ref
    assert finding.store == posting.home
    vector = finding_from_privacy_posting(
        {"title": "a vector posting", "memory_kind": "vector-record",
         "memory_ref": "archival-alpha", "home": "user",
         "posted_on": ON, "recorded_by": BY,
         "source": "test", "origin_session": "session-test"},
        check="orphaned-vector", detail="no store holds it",
        found_on=ON, recorded_by=BY, origin_session="session-test")
    assert vector.memory_kind == "vector-record"
    assert vector.store == "user"


def test_composition_refuses_a_piece_with_no_id():
    entry = {"section": "architecture", "title": "an unnamed entry",
             "detail": "a detail", "source": "test", "ref": "ref-x"}
    with pytest.raises(ValueError, match="with no id"):
        finding_from_map_entry(
            entry, check="map-drift", store="workspace",
            detail="the named path moved", found_on=ON,
            recorded_by=BY, origin_session="session-test")
    watch = {"title": "an unnamed watch", "memory_kind": "manual",
             "memory_ref": "ref-x", "stored_claim": "the stored words",
             "evidence_claim": "the newer words",
             "evidence_source": "the check", "found_on": ON,
             "recorded_by": BY, "source": "test",
             "origin_session": "session-test"}
    with pytest.raises(ValueError, match="with no id"):
        finding_from_contradiction_watch(
            watch, check="corrupt-store", store="workspace",
            detail="the watch record fails", found_on=ON,
            recorded_by=BY, origin_session="session-test")


# ---------------------------------------------------------------------
# The checks themselves: run by import, findings only on failure.
# ---------------------------------------------------------------------


def test_corrupt_check_finds_a_refused_piece_and_refuses_a_sound_one():
    raw = {"candidate_id": "candidate-broken"}
    finding = finding_from_corrupt_piece(
        "ledger-candidate", raw, store="workspace", found_on=ON,
        recorded_by=BY, origin_session="session-test")
    assert finding.check == "corrupt-store"
    assert finding.memory_kind == "ledger-candidate"
    assert finding.memory_ref == "candidate-broken"
    assert "fails its own layer's validation" in finding.detail
    sound = load_self_improving_ledger().candidates[0]
    with pytest.raises(ValueError, match="no corruption found"):
        finding_from_corrupt_piece(
            "ledger-candidate", sound, store="workspace",
            found_on=ON, recorded_by=BY,
            origin_session="session-test")
    with pytest.raises(ValueError, match="knows no holding road"):
        finding_from_corrupt_piece(
            "manual", raw, store="workspace", found_on=ON,
            recorded_by=BY, origin_session="session-test")


def test_orphan_check_finds_an_unheld_vector_and_refuses_a_held_one():
    record = {"text": "the archived words themselves",
              "vector": [0.1, 0.2, 0.3],
              "metadata": {"name": "archival-alpha"}}
    finding = finding_from_orphaned_vector(
        record, {"note-connected-code", "map-package"},
        store="workspace", found_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert finding.check == "orphaned-vector"
    assert finding.memory_kind == "vector-record"
    assert finding.memory_ref == "archival-alpha"
    assert repair_action_of(finding) == "drop-orphan-vector"
    with pytest.raises(ValueError, match="no orphan found"):
        finding_from_orphaned_vector(
            record, {"archival-alpha"}, store="workspace",
            found_on=ON, recorded_by=BY,
            origin_session="session-test")
    with pytest.raises(ValueError, match="judges vector records"):
        finding_from_orphaned_vector(
            load_project_memory_map().entries[0], set(),
            store="workspace", found_on=ON, recorded_by=BY,
            origin_session="session-test")


def test_drift_check_finds_a_moved_path_and_refuses_a_present_one():
    entry = load_project_memory_map().entries[0]
    finding = finding_from_drifted_map_entry(
        entry, {"some/other/path.py"}, store="workspace",
        found_on=ON, recorded_by=BY, origin_session="session-test")
    assert finding.check == "map-drift"
    assert finding.memory_kind == "memory-map"
    assert finding.memory_ref == entry.entry_id
    assert entry.ref in finding.detail
    assert repair_action_of(finding) == "realign-map-entry"
    with pytest.raises(ValueError, match="no drift found"):
        finding_from_drifted_map_entry(
            entry, {entry.ref}, store="workspace", found_on=ON,
            recorded_by=BY, origin_session="session-test")


def test_inspect_finding_source_judges_by_owning_layer():
    entry = load_project_memory_map().entries[0]
    assert inspect_finding_source(entry) == {
        "memory_kind": "memory-map", "memory_ref": entry.entry_id}
    memory = load_subconscious_v2().memories[0]
    assert inspect_finding_source(memory) == {
        "memory_kind": "subconscious-memory",
        "memory_ref": memory.memory_id}
    watch = load_contradiction_watch().watches[0]
    assert inspect_finding_source(watch) == {
        "memory_kind": "contradiction-watch",
        "memory_ref": watch.watch_id}
    assert inspect_finding_source(_finding()) == {
        "memory_kind": "manual", "memory_ref": "ref-test"}
    record = {"text": "the archived words themselves",
              "vector": [0.1, 0.2, 0.3],
              "metadata": {"name": "archival-alpha"}}
    assert inspect_finding_source(record) == {
        "memory_kind": "vector-record", "memory_ref": "archival-alpha"}
    with pytest.raises(ValueError):
        inspect_finding_source(42)


# ---------------------------------------------------------------------
# The panel, the verdict and the repairs: derived, judged.
# ---------------------------------------------------------------------


def test_panel_is_derived_in_panel_order():
    book = load_memory_doctor()
    panel = derive_panel(book)
    assert [r.finding_id for r in panel.rows] == [
        "finding-samtal-wal-store", "finding-verify-remote-corrupt",
        "finding-archival-alpha-orphan", "finding-campaign-home-drift",
        "finding-no-docker-drift"]
    assert panel.total_findings == 5
    assert panel.total_ready == 4
    assert panel.total_referred == 1
    assert panel.distinct_memories == 5
    assert panel.as_of == ON
    counts = {c.check: c.items for c in panel.check_counts}
    assert counts == {
        "corrupt-store": 2, "orphaned-vector": 1, "map-drift": 2}
    row = panel.row_for("finding-samtal-wal-store")
    assert row.disposition == "referred"
    assert row.action == "none-referred"
    assert row.store == "user"
    stored = book.panel_for("panel-m167-boundary")
    assert validate_panel(stored, book) == stored
    assert stored.rows == panel.rows
    assert stored.account == panel.account


def test_panel_refuses_a_stored_panel_that_disagrees():
    book = load_memory_doctor()
    panel = derive_panel(book)
    stored = _clean(panel.to_record())
    stored["rows"] = [_clean(row) for row in stored["rows"]]
    stored["rows"][0]["title"] = "a tampered title"
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    with pytest.raises(ValueError):
        build_panel({**_clean(panel.to_record()),
                     "rows": [_clean(r) for r in
                              panel.to_record()["rows"]],
                     "total_findings": 99})


def test_panel_account_and_check_counts_are_its_own():
    book = load_memory_doctor()
    panel = derive_panel(book)
    assert panel.account[0].startswith(
        "The memory doctor panel holds 5 findings as of 2026-11-09")
    stored = _clean(panel.to_record())
    stored["rows"] = [_clean(row) for row in stored["rows"]]
    stored["account"] = ["A foreign account of the panel."]
    with pytest.raises(ValueError, match="disagrees"):
        validate_panel(stored, book)
    one = DoctorBook(title="a one-finding book", findings=(_finding(),))
    single = derive_panel(one)
    cleaned = _clean(single.to_record())
    cleaned["rows"] = [_clean(row) for row in cleaned["rows"]]
    with pytest.raises(ValueError):
        build_panel({**cleaned, "check_counts": [
            {"check": "corrupt-store", "items": 99}]})


def test_row_is_judged_against_its_finding():
    book = load_memory_doctor()
    finding = book.findings[0]
    row = derive_panel(book).row_for(finding.finding_id)
    cleaned = _clean(row.to_record())
    assert validate_row(cleaned, finding) == row
    assert build_row(cleaned, finding) == row
    with pytest.raises(ValueError, match="disagrees"):
        validate_row({**cleaned, "title": "a tampered title"}, finding)
    with pytest.raises(ValueError, match="its own extent derives"):
        build_row({**cleaned, "disposition": "referred"})
    with pytest.raises(ValueError, match="its own check and extent derive"):
        build_row({**cleaned, "action": "drop-orphan-vector"})


def test_repairs_are_derived_and_judged_against_their_findings():
    book = load_memory_doctor()
    repairs = derive_repairs(book)
    assert [r.action for r in repairs] == [
        "quarantine-piece", "drop-orphan-vector",
        "realign-map-entry", "none-referred", "realign-map-entry"]
    assert repairs[0].repair_id == "repair-finding-verify-remote-corrupt"
    finding = book.findings[0]
    cleaned = _clean(repairs[0].to_record())
    assert validate_repair(cleaned, finding) == repairs[0]
    assert build_repair(cleaned, finding) == repairs[0]
    with pytest.raises(ValueError, match="disagrees"):
        validate_repair({**cleaned, "memory_ref": "ref-other"},
                        finding)
    with pytest.raises(ValueError, match="its own check"):
        build_repair({**cleaned, "action": "drop-orphan-vector"})
    with pytest.raises(ValueError, match="repair-<finding-id>"):
        build_repair({**cleaned, "repair_id": "repair-someone-else"})


def test_verdict_bands_and_the_ailing_example():
    book = load_memory_doctor()
    verdict = derive_verdict(book)
    assert verdict.verdict == "ailing"
    assert verdict.total_findings == 5
    assert verdict.total_ready == 4
    assert verdict.total_referred == 1
    assert verdict.distinct_memories == 5
    assert verdict.distinct_kinds == 5
    assert verdict.earliest_on == "2026-11-07"
    assert verdict.latest_on == "2026-11-09"
    stored_verdict = _clean(verdict.to_record())
    assert validate_verdict(stored_verdict, book) == verdict
    one = DoctorBook(title="a one-finding book", findings=(_finding(),))
    assert derive_verdict(one).verdict == "sound"
    two = DoctorBook(title="a two-finding book", findings=(
        _finding(), _referred_finding(
            finding_id="finding-two", memory_ref="ref-two",
            title="a second finding")))
    assert derive_verdict(two).verdict == "ailing"
    three = DoctorBook(title="a three-finding book", findings=(
        _referred_finding(), _referred_finding(
            finding_id="finding-two", memory_ref="ref-two",
            title="a second finding"),
        _referred_finding(
            finding_id="finding-three", memory_ref="ref-three",
            title="a third finding")))
    assert derive_verdict(three).verdict == "critical"
    with pytest.raises(ValueError):
        build_verdict({**stored_verdict, "verdict": "sound"})
    with pytest.raises(ValueError):
        build_verdict({
            "total_findings": 1, "total_ready": 1,
            "total_referred": 0, "distinct_memories": 2,
            "distinct_kinds": 1, "earliest_on": ON,
            "latest_on": ON, "verdict": "sound"})
    with pytest.raises(ValueError):
        build_verdict({
            "total_findings": 2, "total_ready": 1,
            "total_referred": 1, "distinct_memories": 2,
            "distinct_kinds": 2, "earliest_on": "2026-11-09",
            "latest_on": "2026-11-01", "verdict": "ailing"})


def test_book_laws_one_finding_per_check_per_memory():
    first = _finding()
    forked = _finding(finding_id="finding-fork",
                      title="a forking finding")
    with pytest.raises(ValueError, match="checked twice"):
        DoctorBook(title="a forked book", findings=(first, forked))
    with pytest.raises(ValueError, match="already exists"):
        DoctorBook(title="a doubled book", findings=(first, first))
    other_check = _finding(finding_id="finding-drift",
                           check="map-drift",
                           title="the same memory, drifted")
    book = DoctorBook(
        title="a sound book", findings=(first, other_check))
    assert book.finding_for("finding-test") == first
    assert book.finding_for_check(
        "corrupt-store", "manual", "ref-test") == first
    assert book.finding_for_check(
        "map-drift", "manual", "ref-test") == other_check
    assert total_findings(book) == 2
    assert finding_refs(book) == (
        ("corrupt-store", "manual", "ref-test"),
        ("map-drift", "manual", "ref-test"))
    assert finding_for(
        book, "map-drift", "manual", "ref-test") == other_check
    with pytest.raises(KeyError):
        book.finding_for("finding-nope")
    with pytest.raises(KeyError):
        book.finding_for_check("orphaned-vector", "manual", "ref-test")


def test_book_file_loader_reads_any_file(tmp_path):
    book = load_memory_doctor()
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data"
         / "memory_doctor.yaml").read_text())
    raw["guide"]["title"] = "A copied doctor book"
    path = tmp_path / "copy.yaml"
    path.write_text(yaml.safe_dump(raw))
    copied = load_memory_doctor_file(path)
    assert copied.title == "A copied doctor book"
    assert copied.finding_ids() == book.finding_ids()
    raw["schema"] = "mythic.other/9"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValidationError):
        load_memory_doctor_file(path)
    with pytest.raises(ValidationError):
        validate_book({"schema": MEMORY_DOCTOR_SCHEMA})
    with pytest.raises(ValidationError):
        validate_book({**yaml.safe_load(
            (ROOT / "mythic_agent" / "data"
             / "memory_doctor.yaml").read_text()),
            "dream": "x"})


def test_registry_holds_findings_one_by_one_and_applies_repairs():
    registry = DoctorRegistry()
    held = registry.register_finding(_finding(finding_id=None))
    assert held.finding_id == "finding-1"
    with pytest.raises(ValueError, match="checked twice"):
        registry.register_finding(_finding(finding_id="finding-other"))
    assert registry.latest_finding() == held
    assert registry.panel().total_findings == 1
    assert registry.verdict().verdict == "sound"
    applied = registry.apply_repairs()
    assert [r.action for r in applied] == ["quarantine-piece"]
    assert registry.is_repaired("finding-1")
    assert registry.apply_repairs() == ()
    registry.register_book(load_memory_doctor())
    assert registry.book().total_findings == 6
    assert registry.get_finding(
        "finding-campaign-home-drift").memory_kind == "session-note"
    assert registry.finding_for_check(
        "corrupt-store", "manual", "ref-test").finding_id == "finding-1"
    applied = registry.apply_repairs()
    assert len(applied) == 4
    assert not registry.is_repaired("finding-samtal-wal-store")
    assert len(registry.applied_repairs()) == 5
    with pytest.raises(ValueError):
        registry.register_book(load_memory_doctor())
    with pytest.raises(KeyError):
        registry.get_finding("finding-nope")


# ---------------------------------------------------------------------
# News records, plain words, screens and the shared grammar.
# ---------------------------------------------------------------------


def test_news_records_carry_headlines():
    book = load_memory_doctor()
    record = finding_record(book.findings[0])
    assert record["news"] is True
    assert "safe repair derived: quarantine-piece" in record["headline"]
    referred = finding_record(book.finding_for("finding-samtal-wal-store"))
    assert "referred to the user" in referred["headline"]
    assert "no repair derived" in referred["headline"]
    panel = panel_record(derive_panel(book), book)
    assert panel["type"] == "memory_doctor_panel"
    assert "5 findings" in panel["headline"]
    verdict = verdict_record(derive_verdict(book), book)
    assert verdict["type"] == "memory_doctor_verdict"
    assert "ailing" in verdict["headline"]
    repair = repair_record(derive_repairs(book)[0])
    assert repair["type"] == "memory_doctor_repair"
    assert "quarantine-piece" in repair["headline"]
    referred_repair = repair_record(derive_repairs(book)[3])
    assert "the doctor will not repair it" in referred_repair["headline"]
    assert book_record(book)["finding_count"] == 5
    assert "quarantine-piece" in plain_words(book.findings[0])
    assert "finding-samtal-wal-store" in panel_plain_words(book)
    assert "ailing" in verdict_plain_words(book)
    assert "no repair: the finding stands referred" in (
        repairs_plain_words(book))


def test_formatters_and_screen():
    book = load_memory_doctor()
    block = format_finding(book.findings[0])
    assert "finding-verify-remote-corrupt" in block
    assert "The repair stands:" in block
    assert "quarantine-piece" in block
    drifts = format_findings(book, check="map-drift")
    assert "finding-no-docker-drift" in drifts
    assert "finding-verify-remote-corrupt" not in drifts
    user = format_findings(book, store="user")
    assert "finding-campaign-home-drift" in user
    assert "finding-no-docker-drift" not in user
    assert "ailing" in format_verdict(book)
    assert "panel-m167-boundary" not in format_panel(book)
    assert "Panel in Memory Doctor" in format_panel(book)
    repairs = format_repairs(book)
    assert "no repair will be applied" in repairs
    assert "drop-orphan-vector" in repairs
    screen = format_memory_doctor_screen(book)
    assert "Memory Doctor (M-168)" in screen
    assert PLAIN_EXPLANATION in screen
    assert USAGE in screen
    assert "finding-campaign-home-drift" in format_memory_doctor_screen()


def test_parse_memory_doctor_args_grammar():
    assert parse_memory_doctor_args("") == ("show", None)
    assert parse_memory_doctor_args("show") == ("show", None)
    assert parse_memory_doctor_args("list") == ("show", None)
    assert parse_memory_doctor_args("finding finding-x") == (
        "finding", "finding-x")
    assert parse_memory_doctor_args("check drift") == (
        "check", "map-drift")
    assert parse_memory_doctor_args("check corrupt") == (
        "check", "corrupt-store")
    assert parse_memory_doctor_args("store workspace-store") == (
        "store", "workspace")
    assert parse_memory_doctor_args("store user") == ("store", "user")
    assert parse_memory_doctor_args("panel") == ("panel", None)
    assert parse_memory_doctor_args("verdict") == ("verdict", None)
    assert parse_memory_doctor_args("repairs") == ("repairs", None)
    for bad in ("finding", "check lint", "store cloud", "panel now",
                "dance", None.__class__ and 42):
        with pytest.raises(ValueError):
            parse_memory_doctor_args(bad)


def test_doctor_cli_memory_check_loads_the_shipped_stores():
    from mythic_agent.doctor import run_checks
    results = run_checks(["memory"])
    assert len(results) == 1
    assert results[0].name == "memory"
    assert results[0].status.value == "ok"
    assert "memory stores load whole" in results[0].message


# -- agent layer -----------------------------------------------------------
#
# M-168 agent layer: the agent holds a
# DoctorRegistry for the session (session state
# only, no new setting), findings are held by being
# registered - published as their finding_record
# session news through the checkpoint road, deduped
# per shape - the report road renders the held book
# (or the shipped example when unheld) through the
# pure formatters, a corrupt-store road judges one
# raw store piece by its own layer's validator (its
# id alone crossing, the piece itself never held),
# a check-run road runs the orphaned-vector and
# map-drift checks over the session's own held
# memory books by import, a repair road applies
# ONLY the derived safe repairs to the held book
# and states plainly what it will not repair, and
# the /memorydoctor surface rides both roads on the
# pure parser + formatters. Status, get, panel,
# verdict and report reads register and publish
# nothing, answer from the held registry first and
# from the shipped example only while nothing is
# held - a held finding never falls back to the
# example. The panel, the verdict and the repairs
# derive at call time from the whole book, never
# held. This layer sends nothing, posts nothing,
# schedules nothing, calls no model, persists
# nothing beyond the session journal news and
# writes no live memory - a repair applied here
# marks a held finding repaired in the session's
# own book and rewrites no live store, and there is
# no Part VIII board yet, so the screen is where
# the book is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _doctor_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _book(findings=None, **overrides):
    fields = {
        "title": "A test doctor book",
        "findings": [_stored_finding(item) for item in (
            findings if findings is not None else [_finding()])],
    }
    fields.update(overrides)
    return build_book(fields)


def _write_doctor_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "memory_doctor.yaml").read_text(encoding="utf-8")
    path = tmp_path / "memory_doctor.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestMemoryDoctorAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.memory_doctor_status()
        assert status["findings"] == []
        assert status["book"] is None
        assert status["doctor"]["title"] == EXAMPLE_TITLE
        assert len(status["doctor"]["findings"]) == 5
        assert status["panel"]["total_findings"] == 5
        assert status["panel"]["total_ready"] == 4
        assert status["panel"]["total_referred"] == 1
        assert status["panels"][0]["panel_id"] == "panel-m167-boundary"
        assert status["book_record"]["finding_count"] == 5
        assert status["verdict"]["verdict"] == "ailing"
        assert status["verdict"]["distinct_kinds"] == 5
        assert len(status["repairs"]) == 5
        assert status["applied"] == []
        assert "note-campaign-home" in status["plain_words"]
        assert "ailing" in status["verdict_plain_words"]
        assert "Memory Doctor (M-168)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._memory_doctor_registry()
        assert agent._memory_doctor_registry() is first
        assert agent._memory_doctor_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.memory_doctor_status()
        agent.get_memory_finding("finding-campaign-home-drift")
        agent.memory_finding_for(
            "map-drift", "session-note", "note-campaign-home")
        agent.memory_doctor_panel()
        agent.memory_doctor_verdict()
        agent.report_memory_doctor()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("memory_doctor")] == []
        with pytest.raises(KeyError):
            agent.get_memory_finding("finding-nope")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_memory_finding(_finding())
        status = agent.memory_doctor_status()
        assert [item["finding_id"] for item in status["findings"]] == [
            "finding-test"]
        assert status["book"]["title"] == "Memory Doctor"
        assert status["panel"]["total_findings"] == 1
        assert status["verdict"]["verdict"] == "sound"

    def test_held_finding_never_falls_back_to_the_example(
            self, agent):
        agent.register_memory_finding(_finding())
        with pytest.raises(KeyError):
            agent.get_memory_finding("finding-campaign-home-drift")
        finding = agent.get_memory_finding("finding-test")
        assert finding.title == "the test finding, raised by hand"
        assert agent.memory_finding_for(
            "corrupt-store", "manual", "ref-test").finding_id == (
                "finding-test")
        assert agent.memory_doctor_book().title == (
            "Memory Doctor")


class TestMemoryDoctorAgentHolding:
    def test_register_finding_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_memory_finding(_finding())
        assert outcome["finding"]["finding_id"] == "finding-test"
        assert outcome["record_news"]["type"] == (
            "memory_doctor_finding")
        events = _doctor_events(
            store, session_id, "memory_doctor_finding")
        assert len(events) == 1
        assert events[0]["finding_id"] == "finding-test"
        agent._publish_memory_doctor_record(outcome["record_news"])
        assert len(_doctor_events(
            store, session_id, "memory_doctor_finding")) == 1
        agent._publish_memory_doctor_record(
            {"type": "mentions_mention", "mention_id": "mention-x"})
        agent._publish_memory_doctor_record(
            book_record(load_memory_doctor()))
        for kind in ("mentions_mention", "memory_doctor_book"):
            assert _doctor_events(store, session_id, kind) == []
        agent.close()

    def test_duplicate_finding_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_memory_finding(_finding())
        with pytest.raises(ValueError):
            agent.register_memory_finding(_finding())
        with pytest.raises(ValueError, match="checked twice"):
            agent.register_memory_finding(_finding(
                finding_id="finding-copy"))
        assert len(_doctor_events(
            store, session_id, "memory_doctor_finding")) == 1
        agent.close()

    def test_corrupt_road_raises_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.check_memory_store_piece(
            "ledger-candidate", {"candidate_id": "candidate-broken"},
            store="workspace", found_on=ON, recorded_by=BY,
            origin_session="session-test")
        assert outcome["finding"]["check"] == "corrupt-store"
        assert outcome["finding"]["memory_kind"] == (
            "ledger-candidate")
        assert outcome["finding"]["memory_ref"] == "candidate-broken"
        assert outcome["finding"]["finding_id"] == (
            "finding-corrupt-store-candidate-broken")
        assert outcome["record_news"]["type"] == (
            "memory_doctor_finding")
        assert outcome["panel_record"]["type"] == (
            "memory_doctor_panel")
        assert outcome["verdict_record"]["type"] == (
            "memory_doctor_verdict")
        for kind in ("memory_doctor_finding",
                     "memory_doctor_panel",
                     "memory_doctor_verdict"):
            assert len(_doctor_events(
                store, session_id, kind)) == 1
        sound = load_self_improving_ledger().candidates[0]
        with pytest.raises(ValueError, match="no corruption found"):
            agent.check_memory_store_piece(
                "ledger-candidate", sound, store="workspace",
                found_on=ON, recorded_by=BY,
                origin_session="session-test")
        assert len(agent.memory_doctor_status()["findings"]) == 1
        agent.close()

    def test_run_memory_doctor_finds_orphans_and_drift(
            self, agent, tmp_path):
        from mythic_agent.core.private_by_architecture import (
            build_posting)
        agent.register_privacy_posting(build_posting({
            "title": "the archival alpha vector, posted private",
            "memory_kind": "vector-record",
            "memory_ref": "archival-alpha", "home": "workspace",
            "posted_on": ON, "recorded_by": BY,
            "source": "test source", "origin_session": "session-test",
            "posting_id": "posting-archival-alpha"}))
        outcome = agent.run_memory_doctor(
            found_on=ON, recorded_by=BY,
            origin_session="session-test")
        assert outcome["count"] >= 2
        orphan = agent.memory_finding_for(
            "orphaned-vector", "vector-record", "archival-alpha")
        assert orphan.finding_id == (
            "finding-orphaned-vector-archival-alpha")
        drift = agent.memory_finding_for(
            "map-drift", "memory-map", "map-package")
        assert drift.check == "map-drift"
        assert outcome["panel_record"]["type"] == (
            "memory_doctor_panel")
        assert outcome["verdict_record"]["type"] == (
            "memory_doctor_verdict")
        second = agent.run_memory_doctor(
            found_on=ON, recorded_by=BY,
            origin_session="session-test")
        assert second["count"] == 0
        assert second["skipped"] >= 2

    def test_run_memory_doctor_touches_no_held_book(
            self, agent):
        contradiction_before = agent.contradiction_book()
        subconscious_before = agent.subconscious_book()
        privacy_before = agent.privacy_book()
        agent.run_memory_doctor(
            found_on=ON, recorded_by=BY,
            origin_session="session-test")
        assert agent.contradiction_book().watch_ids() == (
            contradiction_before.watch_ids())
        assert agent.subconscious_book().memory_ids() == (
            subconscious_before.memory_ids())
        assert agent.privacy_book().posting_ids() == (
            privacy_before.posting_ids())

    def test_apply_memory_repairs_applies_only_the_derived(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.record_memory_doctor_book()
        outcome = agent.apply_memory_repairs()
        assert outcome["count"] == 4
        assert [item["action"] for item in outcome["applied"]] == [
            "quarantine-piece", "drop-orphan-vector",
            "realign-map-entry", "realign-map-entry"]
        assert len(outcome["will_not_repair"]) == 1
        refused = outcome["will_not_repair"][0]
        assert refused["repair"]["finding_id"] == (
            "finding-samtal-wal-store")
        assert "the doctor will not repair it" in refused["line"]
        assert len(_doctor_events(
            store, session_id, "memory_doctor_repair")) == 4
        registry = agent._memory_doctor_registry()
        assert registry.is_repaired("finding-no-docker-drift")
        assert not registry.is_repaired("finding-samtal-wal-store")
        second = agent.apply_memory_repairs()
        assert second["count"] == 0
        assert len(second["will_not_repair"]) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent):
        book = _book()
        outcome = agent.register_memory_doctor_book(book)
        assert outcome["count"] == 1
        assert [item["type"] for item in outcome["records_news"]] == [
            "memory_doctor_finding"]
        assert outcome["panel_record"]["type"] == (
            "memory_doctor_panel")
        assert agent.memory_doctor_book().title == (
            "A test doctor book")
        with pytest.raises(ValueError):
            agent.register_memory_doctor_book(book)
        with pytest.raises(ValueError, match="different title"):
            agent.register_memory_doctor_book(_book(
                title="Another title",
                findings=[_finding(
                    finding_id="finding-other",
                    memory_ref="ref-other")]))
        broken = {"title": "A broken book",
                  "findings": [{"finding_id": "finding-x"}]}
        with pytest.raises(ValueError, match="missing its"):
            agent.register_memory_doctor_book(broken)
        assert [item["finding_id"] for item in
                agent.memory_doctor_status()["findings"]] == [
            "finding-test"]

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_memory_doctor_book()
        assert outcome["count"] == 5
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_doctor_events(
            store, session_id, "memory_doctor_finding")) == 5
        assert len(_doctor_events(
            store, session_id, "memory_doctor_panel")) == 1
        assert agent.memory_doctor_book().panels[0].panel_id == (
            "panel-m167-boundary")
        with pytest.raises(ValueError, match="already recorded"):
            agent.record_memory_doctor_book()
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_doctor_book(tmp_path)
        book = load_memory_doctor_file(path)
        outcome = agent.record_memory_doctor_book(book)
        assert outcome["count"] == 5
        assert agent.get_memory_finding(
            "finding-campaign-home-drift").memory_kind == "session-note"

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_memory_doctor()
        assert report["book"]["finding_count"] == 5
        assert "finding-campaign-home-drift" in report["findings_text"]
        assert "Panel in Memory Doctor" in report["panel_text"]
        assert "ailing" in report["verdict_text"]
        assert "no repair will be applied" in report["repairs_text"]
        agent.register_memory_finding(_finding())
        report = agent.report_memory_doctor()
        assert report["book"]["title"] == "Memory Doctor"
        assert "finding-campaign-home-drift" not in (
            report["findings_text"])
        assert "finding-test" in report["findings_text"]
        assert "sound" in report["verdict_text"]

    def test_holding_and_repairing_touch_no_live_store(
            self, agent, tmp_path):
        # HONEST BOUNDARY: holding a finding and
        # applying its derived repair touch no live
        # store - the session's own held memory books
        # stand exactly as they stood, no memory is
        # deleted or rewritten, and there is no road
        # here that repairs a live store on disk,
        # wipes a store, or carries a finding
        # anywhere.
        assert not hasattr(agent, "repair_live_memory_store")
        assert not hasattr(agent, "delete_memory_store")
        assert not hasattr(agent, "wipe_memory_store")
        assert not hasattr(agent, "persist_memory_doctor")
        assert not hasattr(agent, "memory_doctor_board")
        assert not hasattr(agent, "send_memory_finding")
        assert not hasattr(agent, "sync_memory_store")
        assert not hasattr(agent, "schedule_memory_doctor")
        assert not hasattr(agent, "drop_orphaned_vector_live")
        assert not hasattr(agent, "erase_corrupt_memory")
        contradiction_before = agent.contradiction_book()
        subconscious_before = agent.subconscious_book()
        privacy_before = agent.privacy_book()
        (tmp_path / "alpha.py").write_text(
            "def greet(name):\n    return name\n", encoding="utf-8")
        before = {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")}
        from mythic_agent.agents.context import ContextBuilder
        builder = ContextBuilder(max_tokens=4000)
        builder.add_system("You are the coder.")
        builder.add_turn("user", "Build the slice.")
        built_before = builder.build()
        agent.register_memory_finding(_finding())
        agent.run_memory_doctor(
            found_on=ON, recorded_by=BY,
            origin_session="session-test")
        outcome = agent.apply_memory_repairs()
        assert outcome["count"] >= 1
        assert agent.contradiction_book().watch_ids() == (
            contradiction_before.watch_ids())
        assert agent.subconscious_book().memory_ids() == (
            subconscious_before.memory_ids())
        assert agent.privacy_book().posting_ids() == (
            privacy_before.posting_ids())
        assert builder.build() == built_before
        assert {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")} == before


class TestMemoryDoctorTerminalSurface:
    def test_show_finding_check_store_panel_verdict_repairs(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/memorydoctor")
        assert "Memory Doctor (M-168)" in text
        _, _, text = _slash(
            agent, "/memorydoctor finding finding-campaign-home-drift")
        assert "the campaign home note drifted" in text
        _, _, text = _slash(agent, "/memorydoctor check map-drift")
        assert "finding-no-docker-drift" in text
        assert "finding-verify-remote-corrupt" not in text
        _, _, text = _slash(agent, "/memorydoctor store user")
        assert "finding-campaign-home-drift" in text
        assert "finding-no-docker-drift" not in text
        _, _, text = _slash(agent, "/memorydoctor panel")
        assert "Panel in Memory Doctor" in text
        _, _, text = _slash(agent, "/memorydoctor verdict")
        assert "ailing" in text
        _, _, text = _slash(agent, "/memorydoctor repairs")
        assert "no repair will be applied" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/memorydoctor [show|finding <finding-id>"
                "|check <check>|store <store>|panel|verdict"
                "|repairs]") in text
        _, _, text = _slash(agent, "/memorydoctor dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/memorydoctor finding finding-nope")
        assert "no finding in the book" in text


@pytest.fixture()
def doctor_handler(agent, monkeypatch):
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


def _doctor_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestMemoryDoctorCommand:
    def test_show_is_default(self, doctor_handler, agent):
        doctor_handler._handle_memorydoctor("")
        assert "Memory Doctor (M-168)" in (
            _doctor_published_text(doctor_handler))

    def test_finding_check_store_panel_verdict_repairs(
            self, doctor_handler, agent):
        doctor_handler._handle_memorydoctor(
            "finding finding-campaign-home-drift")
        assert "finding-campaign-home-drift" in (
            _doctor_published_text(doctor_handler))
        doctor_handler._handle_memorydoctor("check map-drift")
        assert "finding-no-docker-drift" in _doctor_published_text(
            doctor_handler)
        doctor_handler._handle_memorydoctor("store user")
        assert "finding-campaign-home-drift" in _doctor_published_text(
            doctor_handler)
        doctor_handler._handle_memorydoctor("panel")
        assert "Panel in Memory Doctor" in (
            _doctor_published_text(doctor_handler))
        doctor_handler._handle_memorydoctor("verdict")
        assert "ailing" in _doctor_published_text(
            doctor_handler)
        doctor_handler._handle_memorydoctor("repairs")
        assert "no repair will be applied" in _doctor_published_text(
            doctor_handler)

    def test_bad_grammar_is_published(
            self, doctor_handler, agent):
        doctor_handler._handle_memorydoctor("dance party")
        assert USAGE in _doctor_published_text(
            doctor_handler)
        doctor_handler._handle_memorydoctor("finding finding-nope")
        assert "no finding in the book" in _doctor_published_text(
            doctor_handler)


class TestChatScreenRoutingMemoryDoctor:
    def test_memorydoctor_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command(
            "/memorydoctor check map-drift", _FakeLog())
        assert calls == [("/memorydoctor", "check map-drift")]
