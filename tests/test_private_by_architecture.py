"""M-167 Private by architecture - pure-layer tests.

TIER: integration

The pure layer is the privacy posting, held as
data: one posting standing over one stored memory
- named by the kind of holding it stands in and
the shipped piece's id alone, the piece's own
words never crossing - carrying its provenance
whole (the store the memory lives in, the
workspace store or the user store; the one Part X
bridge the user has explicitly opened over it,
who opened it and the day, or that no bridge
stands open at all; who recorded the posting, the
session it was raised in and where it was read
from), composed by import from the shipped
holdings it stands over (the project memory map
M-150, session memory M-153, cross-project memory
M-154, the self-improving ledger M-155, crew
memory M-133, the subconscious v2 M-165 and the
contradiction watch M-166), each judged by its
own layer's validation, ids and refs only across
the seams. The standing is derived, never chosen:
sealed while no bridge stands open over a memory,
bridge-open only through the one named bridge the
user explicitly opened. One stored memory is
posted once in a book, so the privacy standing
never forks. A privacy panel is derived from the
whole book (every posting carried whole, in a
settled order, its boundary shown on every row), a
privacy verdict is derived for the whole book - a
book standing open at the user's own hand is
named guarded or bridged plainly, never smoothed
- the shipped example book is held in a data
file, and a loader reads a book from any file.
Nothing here sends, posts, schedules, calls a
model, persists anything, syncs anything or
writes any live memory: a posting moves nothing,
and the memory itself never leaves its store by
standing in this book.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.contradiction_watch import load_contradiction_watch
from mythic_agent.core.crew_memory import load_crew_memory
from mythic_agent.core.cross_project_memory import (
    load_cross_project_memory)
from mythic_agent.core.project_memory_map import load_project_memory_map
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.self_improving_ledger import (
    load_self_improving_ledger)
from mythic_agent.core.session_memory import load_session_memory
from mythic_agent.core.subconscious_v2 import load_subconscious_v2
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.private_by_architecture import (
    BRIDGES,
    HOMES,
    MEMORY_KINDS,
    PLAIN_EXPLANATION,
    PRIVATE_BY_ARCHITECTURE_RESOURCE,
    PRIVATE_BY_ARCHITECTURE_SCHEMA,
    PRIVATE_BY_ARCHITECTURE_SLICE,
    SEALED_BRIDGE,
    STANDINGS,
    USAGE,
    VERDICT_WORDS,
    HomeCount,
    PrivacyBook,
    PrivacyPanel,
    PrivacyRegistry,
    PrivacyPosting,
    PrivacyVerdict,
    boundary_line,
    book_record,
    build_book,
    build_panel,
    build_posting,
    build_row,
    build_verdict,
    derive_panel,
    derive_verdict,
    format_panel,
    format_posting,
    format_postings,
    format_privacy_screen,
    format_verdict,
    inspect_posting_source,
    load_private_by_architecture,
    load_private_by_architecture_file,
    normalize_bridge,
    normalize_home,
    normalize_memory_kind,
    panel_plain_words,
    panel_record,
    parse_privacy_args,
    plain_words,
    posting_for,
    posting_from_contradiction_watch,
    posting_from_crew_entry,
    posting_from_cross_project_lesson,
    posting_from_ledger_candidate,
    posting_from_map_entry,
    posting_from_session_note,
    posting_from_subconscious_memory,
    posting_record,
    posting_refs,
    standing_of,
    total_postings,
    validate_book,
    validate_panel,
    validate_posting,
    validate_row,
    validate_verdict,
    verdict_plain_words,
    verdict_record,
)

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Private by architecture at the M-166 slice boundary"

BY = "Volmarr"
ON = "2026-11-09"


def _posting(**overrides):
    fields = {
        "posting_id": "posting-test",
        "title": "the test posting, raised by hand",
        "memory_kind": "manual",
        "memory_ref": "ref-test",
        "home": "workspace",
        "posted_on": ON,
        "recorded_by": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_posting(fields)


def _open_posting(**overrides):
    fields = {
        "bridge": "export", "opened_by": BY, "opened_on": ON,
    }
    fields.update(overrides)
    return _posting(**fields)


def _stored_posting(posting):
    stored = posting.to_record()
    for key in ("type", "slice", "standing", "boundary"):
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
    book = load_private_by_architecture()
    assert book.title == EXAMPLE_TITLE
    assert book.posting_ids() == (
        "posting-no-docker-map", "posting-lesson-export",
        "posting-samtal-wal", "posting-campaign-home",
        "posting-verify-remote")
    assert book.total_postings == 5
    assert len(book.panels) == 1
    panel = book.panel_for("panel-m166-boundary")
    assert panel.as_of == ON
    assert panel.total_postings == 5
    assert panel.total_sealed == 4
    assert panel.total_open == 1
    assert panel.distinct_memories == 5
    first = book.postings[0]
    assert first.posting_id == "posting-no-docker-map"
    assert first.title == "the no-Docker law stays in the workspace"
    assert book.posting_for_memory(
        "crew-fact", "verify-remote-moved").posting_id == (
            "posting-verify-remote")
    opened = book.posting_for("posting-lesson-export")
    assert opened.bridge == "export"
    assert opened.opened_by == "Volmarr"
    assert opened.opened_on == "2026-11-08"


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-167")]
    assert slice_.title == "Private by architecture"
    assert "workspace" in slice_.summary
    assert "nothing syncs anywhere" in slice_.summary
    assert "explicitly opened by the user" in slice_.summary
    assert PRIVATE_BY_ARCHITECTURE_SLICE == "M-167"
    assert PRIVATE_BY_ARCHITECTURE_SCHEMA == (
        "mythic.private_by_architecture/1")
    assert PRIVATE_BY_ARCHITECTURE_RESOURCE == (
        "private_by_architecture.yaml")


def test_closed_vocabularies():
    assert MEMORY_KINDS == (
        "memory-map", "session-note", "cross-project-lesson",
        "ledger-candidate", "crew-fact", "subconscious-memory",
        "contradiction-watch", "vector-record", "manual")
    assert HOMES == ("workspace", "user")
    assert BRIDGES == (
        "none", "mcp", "samverk", "samtal", "ide",
        "forge", "ci", "tracker", "wyrd", "webhook", "export")
    assert STANDINGS == ("sealed", "bridge-open")
    assert VERDICT_WORDS == ("sealed", "guarded", "bridged")
    assert SEALED_BRIDGE == "none"
    assert normalize_memory_kind("MAP") == "memory-map"
    assert normalize_memory_kind("watch") == "contradiction-watch"
    assert normalize_home("workspace-store") == "workspace"
    assert normalize_home("USER") == "user"
    assert normalize_bridge("sealed") == "none"
    assert normalize_bridge("export-file") == "export"
    assert normalize_bridge("ide-companion") == "ide"
    with pytest.raises(ValueError):
        normalize_memory_kind("dream")
    with pytest.raises(ValueError):
        normalize_home("cloud")
    with pytest.raises(ValueError):
        normalize_bridge("carrier-pigeon")


# ---------------------------------------------------------------------
# The posting record: provenance whole, judged whole.
# ---------------------------------------------------------------------


def test_posting_record_round_trips():
    posting = _open_posting()
    assert validate_posting(_stored_posting(posting)) == posting
    record = posting.to_record()
    assert record["type"] == "private_by_architecture_posting"
    assert record["slice"] == "M-167"
    assert record["standing"] == "bridge-open"
    assert record["bridge"] == "export"
    assert record["boundary"] == boundary_line(posting)
    sealed = _posting()
    assert sealed.to_record()["standing"] == "sealed"
    assert sealed.to_record()["opened_by"] is None


def test_posting_provenance_is_whole_and_required():
    for field in ("title", "memory_kind", "memory_ref", "home",
                  "posted_on", "recorded_by", "source",
                  "origin_session"):
        fields = _stored_posting(_posting())
        fields.pop(field)
        with pytest.raises(ValueError):
            build_posting(fields)


def test_posting_refuses_unknown_keys_and_split_spellings():
    fields = _stored_posting(_posting())
    fields["dream"] = "x"
    with pytest.raises(ValueError):
        build_posting(fields)
    fields = _stored_posting(_posting())
    fields["standing"] = "sealed"
    with pytest.raises(ValueError):
        build_posting(fields)
    fields = _stored_posting(_posting())
    fields["store"] = "user"
    with pytest.raises(ValueError):
        build_posting(fields)


def test_posting_opening_laws():
    with pytest.raises(ValueError, match="names no bridge opening"):
        _posting(opened_by=BY, opened_on=ON)
    with pytest.raises(ValueError, match="explicitly opened it"):
        _posting(bridge="export")
    with pytest.raises(ValueError, match="explicitly opened it"):
        _posting(bridge="export", opened_by=BY)
    with pytest.raises(ValueError, match="explicitly opened it"):
        _posting(bridge="samtal", opened_on=ON)
    with pytest.raises(ValueError):
        _posting(posted_on="Nov 9 2026")
    with pytest.raises(ValueError):
        _posting(memory_ref="two words")
    with pytest.raises(ValueError):
        _posting(home="cloud")


def test_posting_alias_spellings_read_onto_the_fields():
    posting = build_posting({
        "name": "an alias posting", "kind": "map", "ref": "ref-alias",
        "store": "user-store", "bridge": "sealed", "day": ON,
        "by": BY, "source": "test source", "session": "session-test",
        "id": "posting-alias"})
    assert posting.memory_kind == "memory-map"
    assert posting.memory_ref == "ref-alias"
    assert posting.home == "user"
    assert posting.bridge == "none"
    assert posting.posting_id == "posting-alias"
    assert posting.origin_session == "session-test"


def test_standing_is_always_derived():
    sealed = _posting()
    assert standing_of(sealed) == "sealed"
    line = boundary_line(sealed)
    assert "lives in the workspace store" in line
    assert "syncs nowhere" in line
    opened = _open_posting(home="user")
    assert standing_of(opened) == "bridge-open"
    line = boundary_line(opened)
    assert "lives in the user store" in line
    assert "only through the export bridge" in line
    assert "opened by Volmarr on 2026-11-09" in line
    assert "every other road stays shut" in line


# ---------------------------------------------------------------------
# Composition by import: ids only across the seams.
# ---------------------------------------------------------------------


def test_posting_from_map_entry_carries_id_only():
    entry = load_project_memory_map().entries[0]
    posting = posting_from_map_entry(
        entry, home="workspace", posted_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert posting.memory_kind == "memory-map"
    assert posting.memory_ref == entry.entry_id
    assert posting.posting_id == f"posting-{entry.entry_id}"
    assert standing_of(posting) == "sealed"
    assert entry.detail not in posting.title


def test_posting_from_session_note_and_cross_project_lesson():
    note = load_session_memory().situations[0].memory[0]
    posting = posting_from_session_note(
        note, home="user", posted_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert posting.memory_kind == "session-note"
    assert posting.memory_ref == note.note_id
    lesson = load_cross_project_memory().lessons[0]
    carried = posting_from_cross_project_lesson(
        lesson, home="workspace", bridge="export", opened_by=BY,
        opened_on=ON, posted_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert carried.memory_kind == "cross-project-lesson"
    assert carried.memory_ref == lesson.lesson_id
    assert standing_of(carried) == "bridge-open"


def test_posting_from_ledger_candidate_and_crew_entry():
    candidate = load_self_improving_ledger().candidates[0]
    posting = posting_from_ledger_candidate(
        candidate, home="workspace", posted_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert posting.memory_kind == "ledger-candidate"
    assert posting.memory_ref == candidate.candidate_id
    entry = load_crew_memory().notebooks[0].entries[0]
    fact = posting_from_crew_entry(
        entry, home="user", posted_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert fact.memory_kind == "crew-fact"
    assert fact.memory_ref == entry.entry_id
    assert entry.fact not in fact.title


def test_posting_from_subconscious_memory_carries_id_only():
    memory = load_subconscious_v2().memories[0]
    posting = posting_from_subconscious_memory(
        memory, home="workspace", posted_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert posting.memory_kind == "subconscious-memory"
    assert posting.memory_ref == memory.memory_id
    assert memory.title not in posting.title


def test_posting_from_contradiction_watch_carries_id_only():
    watch = load_contradiction_watch().watches[0]
    posting = posting_from_contradiction_watch(
        watch, home="workspace", posted_on=ON, recorded_by=BY,
        origin_session="session-test")
    assert posting.memory_kind == "contradiction-watch"
    assert posting.memory_ref == watch.watch_id
    assert posting.posting_id == f"posting-{watch.watch_id}"
    assert watch.stored_claim not in posting.title
    assert watch.evidence_claim not in posting.title


def test_composition_refuses_a_piece_with_no_id():
    entry = {"section": "architecture", "title": "an unnamed entry",
             "detail": "a detail", "source": "test", "ref": "ref-x"}
    with pytest.raises(ValueError, match="with no id"):
        posting_from_map_entry(
            entry, home="workspace", posted_on=ON, recorded_by=BY,
            origin_session="session-test")
    watch = {"title": "an unnamed watch", "memory_kind": "manual",
             "memory_ref": "ref-x", "stored_claim": "the stored words",
             "evidence_claim": "the newer words",
             "evidence_source": "the check", "found_on": ON,
             "recorded_by": BY, "source": "test",
             "origin_session": "session-test"}
    with pytest.raises(ValueError, match="with no id"):
        posting_from_contradiction_watch(
            watch, home="workspace", posted_on=ON, recorded_by=BY,
            origin_session="session-test")


def test_inspect_posting_source_judges_by_owning_layer():
    entry = load_project_memory_map().entries[0]
    assert inspect_posting_source(entry) == {
        "memory_kind": "memory-map", "memory_ref": entry.entry_id}
    memory = load_subconscious_v2().memories[0]
    assert inspect_posting_source(memory) == {
        "memory_kind": "subconscious-memory",
        "memory_ref": memory.memory_id}
    watch = load_contradiction_watch().watches[0]
    assert inspect_posting_source(watch) == {
        "memory_kind": "contradiction-watch",
        "memory_ref": watch.watch_id}
    assert inspect_posting_source(_posting()) == {
        "memory_kind": "manual", "memory_ref": "ref-test"}
    record = {"text": "the archived words themselves",
              "vector": [0.1, 0.2, 0.3],
              "metadata": {"name": "archival-alpha"}}
    assert inspect_posting_source(record) == {
        "memory_kind": "vector-record", "memory_ref": "archival-alpha"}
    with pytest.raises(ValueError):
        inspect_posting_source(42)


# ---------------------------------------------------------------------
# The panel and the verdict: derived, judged against the book.
# ---------------------------------------------------------------------


def test_panel_is_derived_in_panel_order():
    book = load_private_by_architecture()
    panel = derive_panel(book)
    assert [r.posting_id for r in panel.rows] == [
        "posting-lesson-export", "posting-no-docker-map",
        "posting-samtal-wal", "posting-campaign-home",
        "posting-verify-remote"]
    assert panel.total_postings == 5
    assert panel.total_sealed == 4
    assert panel.total_open == 1
    assert panel.distinct_memories == 5
    assert panel.as_of == ON
    counts = {c.home: c.items for c in panel.home_counts}
    assert counts == {"workspace": 3, "user": 2}
    row = panel.row_for("posting-lesson-export")
    assert row.standing == "bridge-open"
    assert row.bridge == "export"
    assert row.home == "workspace"
    stored = book.panel_for("panel-m166-boundary")
    assert validate_panel(stored, book) == stored
    assert stored.rows == panel.rows
    assert stored.account == panel.account


def test_panel_refuses_a_stored_panel_that_disagrees():
    book = load_private_by_architecture()
    panel = derive_panel(book)
    stored = _clean(panel.to_record())
    stored["rows"] = [_clean(row) for row in stored["rows"]]
    stored["rows"][0]["bridge"] = "samtal"
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    with pytest.raises(ValueError):
        build_panel({**_clean(panel.to_record()),
                     "rows": [_clean(r) for r in
                              panel.to_record()["rows"]],
                     "total_postings": 99})


def test_panel_account_and_home_counts_are_its_own():
    book = load_private_by_architecture()
    panel = derive_panel(book)
    assert panel.account[0].startswith(
        "The privacy panel holds 5 postings as of 2026-11-09")
    stored = _clean(panel.to_record())
    stored["rows"] = [_clean(row) for row in stored["rows"]]
    stored["account"] = ["A foreign account of the panel."]
    with pytest.raises(ValueError, match="disagrees"):
        validate_panel(stored, book)
    one = PrivacyBook(title="a one-posting book", postings=(_posting(),))
    single = derive_panel(one)
    cleaned = _clean(single.to_record())
    cleaned["rows"] = [_clean(row) for row in cleaned["rows"]]
    with pytest.raises(ValueError):
        build_panel({**cleaned, "home_counts": [
            {"home": "workspace", "items": 99}]})


def test_row_is_judged_against_its_posting():
    book = load_private_by_architecture()
    posting = book.postings[0]
    row = derive_panel(book).row_for(posting.posting_id)
    cleaned = _clean(row.to_record())
    assert validate_row(cleaned, posting) == row
    assert build_row(cleaned, posting) == row
    with pytest.raises(ValueError, match="disagrees"):
        validate_row({**cleaned, "title": "a tampered title"}, posting)
    with pytest.raises(ValueError, match="its own bridge derives"):
        build_row({**cleaned, "standing": "bridge-open"})


def test_verdict_bands_and_the_guarded_example():
    book = load_private_by_architecture()
    verdict = derive_verdict(book)
    assert verdict.verdict == "guarded"
    assert verdict.total_postings == 5
    assert verdict.total_sealed == 4
    assert verdict.total_open == 1
    assert verdict.distinct_memories == 5
    assert verdict.distinct_kinds == 5
    assert verdict.earliest_on == "2026-11-06"
    assert verdict.latest_on == "2026-11-09"
    stored_verdict = _clean(verdict.to_record())
    assert validate_verdict(stored_verdict, book) == verdict
    one = PrivacyBook(title="a one-posting book", postings=(_posting(),))
    assert derive_verdict(one).verdict == "sealed"
    two = PrivacyBook(title="a two-posting book", postings=(
        _posting(), _open_posting(
            posting_id="posting-two", memory_ref="ref-two",
            title="a second posting")))
    assert derive_verdict(two).verdict == "guarded"
    three = PrivacyBook(title="a three-posting book", postings=(
        _open_posting(), _open_posting(
            posting_id="posting-two", memory_ref="ref-two",
            title="a second posting"),
        _open_posting(
            posting_id="posting-three", memory_ref="ref-three",
            title="a third posting")))
    assert derive_verdict(three).verdict == "bridged"
    with pytest.raises(ValueError):
        build_verdict({**stored_verdict, "verdict": "sealed"})


def test_verdict_tallies_are_judged():
    with pytest.raises(ValueError):
        build_verdict({
            "total_postings": 1, "total_sealed": 1, "total_open": 0,
            "distinct_memories": 2, "distinct_kinds": 1,
            "earliest_on": ON, "latest_on": ON,
            "verdict": "sealed"})
    with pytest.raises(ValueError):
        build_verdict({
            "total_postings": 2, "total_sealed": 1, "total_open": 1,
            "distinct_memories": 2, "distinct_kinds": 2,
            "earliest_on": "2026-11-09", "latest_on": "2026-11-01",
            "verdict": "guarded"})
    with pytest.raises(ValueError):
        build_verdict({
            "total_postings": 2, "total_sealed": 2, "total_open": 1,
            "distinct_memories": 2, "distinct_kinds": 2,
            "earliest_on": "2026-11-01", "latest_on": "2026-11-09",
            "verdict": "guarded"})


def test_book_laws_one_posting_per_memory():
    first = _posting()
    forked = _posting(posting_id="posting-fork", title="a forking posting")
    with pytest.raises(ValueError, match="posted twice"):
        PrivacyBook(title="a forked book", postings=(first, forked))
    with pytest.raises(ValueError, match="already exists"):
        PrivacyBook(title="a doubled book", postings=(first, first))
    book = PrivacyBook(title="a sound book", postings=(first,))
    assert book.posting_for("posting-test") == first
    assert book.posting_for_memory("manual", "ref-test") == first
    assert total_postings(book) == 1
    assert posting_refs(book) == (("manual", "ref-test"),)
    assert posting_for(book, "manual", "ref-test") == first
    with pytest.raises(KeyError):
        book.posting_for("posting-nope")
    with pytest.raises(KeyError):
        book.posting_for_memory("manual", "ref-nope")


def test_book_file_loader_reads_any_file(tmp_path):
    book = load_private_by_architecture()
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data"
         / "private_by_architecture.yaml").read_text())
    raw["guide"]["title"] = "A copied privacy book"
    path = tmp_path / "copy.yaml"
    path.write_text(yaml.safe_dump(raw))
    copied = load_private_by_architecture_file(path)
    assert copied.title == "A copied privacy book"
    assert copied.posting_ids() == book.posting_ids()
    raw["schema"] = "mythic.other/9"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValidationError):
        load_private_by_architecture_file(path)
    with pytest.raises(ValidationError):
        validate_book({"schema": PRIVATE_BY_ARCHITECTURE_SCHEMA})
    with pytest.raises(ValidationError):
        validate_book({**yaml.safe_load(
            (ROOT / "mythic_agent" / "data"
             / "private_by_architecture.yaml").read_text()),
            "dream": "x"})


def test_registry_holds_postings_one_by_one():
    registry = PrivacyRegistry()
    held = registry.register_posting(_posting(posting_id=None))
    assert held.posting_id == "posting-1"
    with pytest.raises(ValueError, match="posted twice"):
        registry.register_posting(_posting(posting_id="posting-other"))
    assert registry.latest_posting() == held
    assert registry.panel().total_postings == 1
    assert registry.verdict().verdict == "sealed"
    registry.register_book(load_private_by_architecture())
    assert registry.book().total_postings == 6
    assert registry.get_posting("posting-verify-remote").memory_kind == (
        "crew-fact")
    assert registry.posting_for_memory(
        "manual", "ref-test").posting_id == "posting-1"
    with pytest.raises(ValueError):
        registry.register_book(load_private_by_architecture())
    with pytest.raises(KeyError):
        registry.get_posting("posting-nope")


# ---------------------------------------------------------------------
# News records, plain words, screens and the shared grammar.
# ---------------------------------------------------------------------


def test_news_records_carry_headlines():
    book = load_private_by_architecture()
    record = posting_record(book.postings[0])
    assert record["news"] is True
    assert "sealed in the workspace store" in record["headline"]
    opened = posting_record(book.posting_for("posting-lesson-export"))
    assert "bridge-open in the workspace store" in opened["headline"]
    assert "export bridge" in opened["headline"]
    panel = panel_record(derive_panel(book), book)
    assert panel["type"] == "private_by_architecture_panel"
    assert "5 postings" in panel["headline"]
    verdict = verdict_record(derive_verdict(book), book)
    assert verdict["type"] == "private_by_architecture_verdict"
    assert "guarded" in verdict["headline"]
    assert book_record(book)["posting_count"] == 5
    assert "syncs nowhere" in plain_words(book.postings[0])
    assert "posting-lesson-export" in panel_plain_words(book)
    assert "guarded" in verdict_plain_words(book)


def test_formatters_and_screen():
    book = load_private_by_architecture()
    block = format_posting(book.postings[0])
    assert "posting-no-docker-map" in block
    assert "The boundary stands:" in block
    assert "none stands open" in block
    crew = format_postings(book, kind="crew-fact")
    assert "posting-verify-remote" in crew
    assert "posting-campaign-home" not in crew
    user = format_postings(book, home="user")
    assert "posting-campaign-home" in user
    assert "posting-no-docker-map" not in user
    assert "guarded" in format_verdict(book)
    assert "panel-m166-boundary" not in format_panel(book)
    assert "Panel in Private by architecture" in format_panel(book)
    screen = format_privacy_screen(book)
    assert "Private by Architecture (M-167)" in screen
    assert PLAIN_EXPLANATION in screen
    assert USAGE in screen
    assert "posting-verify-remote" in format_privacy_screen()


def test_parse_privacy_args_grammar():
    assert parse_privacy_args("") == ("show", None)
    assert parse_privacy_args("show") == ("show", None)
    assert parse_privacy_args("list") == ("show", None)
    assert parse_privacy_args("posting posting-x") == (
        "posting", "posting-x")
    assert parse_privacy_args("kind watch") == (
        "kind", "contradiction-watch")
    assert parse_privacy_args("kind crew") == ("kind", "crew-fact")
    assert parse_privacy_args("home workspace-store") == (
        "home", "workspace")
    assert parse_privacy_args("home user") == ("home", "user")
    assert parse_privacy_args("panel") == ("panel", None)
    assert parse_privacy_args("verdict") == ("verdict", None)
    for bad in ("posting", "kind dream", "home cloud", "panel now",
                "dance", None.__class__ and 42):
        with pytest.raises(ValueError):
            parse_privacy_args(bad)


# -- agent layer -----------------------------------------------------------
#
# M-167 agent layer: the agent holds a
# PrivacyRegistry for the session (session state
# only, no new setting), postings are held by being
# registered - published as their posting_record
# session news through the checkpoint road, deduped
# per shape - the report road renders the held book
# (or the shipped example when unheld) through the
# pure formatters, a composing road raises a
# posting over one of the session's own
# contradiction watches by import (its id alone
# crossing, the watch's own claims never crossing,
# the watch itself never touched), and the /private
# surface rides both roads on the pure parser +
# formatters. Status, get, panel, verdict and
# report reads register and publish nothing, answer
# from the held registry first and from the shipped
# example only while nothing is held - a held
# posting never falls back to the example. The
# panel and the verdict derive at call time from
# the whole book, never held. This layer sends
# nothing, posts nothing, schedules nothing, calls
# no model, persists nothing beyond the session
# journal news, syncs nothing and moves no memory
# - a posting opens no road and carries nothing
# anywhere, and there is no Part VIII board yet, so
# the screen is where the book is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _privacy_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _book(postings=None, **overrides):
    fields = {
        "title": "A test privacy book",
        "postings": [_stored_posting(item) for item in (
            postings if postings is not None else [_posting()])],
    }
    fields.update(overrides)
    return build_book(fields)


def _write_privacy_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "private_by_architecture.yaml").read_text(encoding="utf-8")
    path = tmp_path / "private_by_architecture.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestPrivacyAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.privacy_status()
        assert status["postings"] == []
        assert status["book"] is None
        assert status["privacy"]["title"] == EXAMPLE_TITLE
        assert len(status["privacy"]["postings"]) == 5
        assert status["panel"]["total_postings"] == 5
        assert status["panel"]["total_sealed"] == 4
        assert status["panel"]["total_open"] == 1
        assert status["panels"][0]["panel_id"] == "panel-m166-boundary"
        assert status["book_record"]["posting_count"] == 5
        assert status["verdict"]["verdict"] == "guarded"
        assert status["verdict"]["distinct_kinds"] == 5
        assert "verify-remote-moved" in status["plain_words"]
        assert "guarded" in status["verdict_plain_words"]
        assert "Private by Architecture (M-167)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._privacy_registry()
        assert agent._privacy_registry() is first
        assert agent._privacy_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.privacy_status()
        agent.get_privacy_posting("posting-verify-remote")
        agent.posting_for_memory("crew-fact", "verify-remote-moved")
        agent.privacy_panel()
        agent.privacy_verdict()
        agent.report_privacy()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("private_by_architecture")] == []
        with pytest.raises(KeyError):
            agent.get_privacy_posting("posting-nope")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_privacy_posting(_posting())
        status = agent.privacy_status()
        assert [item["posting_id"] for item in status["postings"]] == [
            "posting-test"]
        assert status["book"]["title"] == "Private by architecture"
        assert status["panel"]["total_postings"] == 1
        assert status["verdict"]["verdict"] == "sealed"

    def test_held_posting_never_falls_back_to_the_example(
            self, agent):
        agent.register_privacy_posting(_posting())
        with pytest.raises(KeyError):
            agent.get_privacy_posting("posting-verify-remote")
        posting = agent.get_privacy_posting("posting-test")
        assert posting.title == "the test posting, raised by hand"
        assert agent.posting_for_memory(
            "manual", "ref-test").posting_id == "posting-test"
        assert agent.privacy_book().title == (
            "Private by architecture")


class TestPrivacyAgentHolding:
    def test_register_posting_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_privacy_posting(_posting())
        assert outcome["posting"]["posting_id"] == "posting-test"
        assert outcome["record_news"]["type"] == (
            "private_by_architecture_posting")
        events = _privacy_events(
            store, session_id, "private_by_architecture_posting")
        assert len(events) == 1
        assert events[0]["posting_id"] == "posting-test"
        agent._publish_privacy_record(outcome["record_news"])
        assert len(_privacy_events(
            store, session_id, "private_by_architecture_posting")) == 1
        agent._publish_privacy_record(
            {"type": "mentions_mention", "mention_id": "mention-x"})
        agent._publish_privacy_record(
            book_record(load_private_by_architecture()))
        for kind in ("mentions_mention", "private_by_architecture_book"):
            assert _privacy_events(store, session_id, kind) == []
        agent.close()

    def test_duplicate_posting_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_privacy_posting(_posting())
        with pytest.raises(ValueError):
            agent.register_privacy_posting(_posting())
        with pytest.raises(ValueError, match="posted twice"):
            agent.register_privacy_posting(_posting(
                posting_id="posting-copy"))
        assert len(_privacy_events(
            store, session_id, "private_by_architecture_posting")) == 1
        agent.close()

    def test_post_over_contradiction_watch_raises_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        watch_before = agent.get_contradiction_watch(
            "watch-verify-on-devices")
        outcome = agent.post_over_contradiction_watch(
            "watch-verify-on-devices", home="workspace",
            posted_on=ON, recorded_by=BY,
            origin_session="session-test")
        assert outcome["posting"]["memory_kind"] == (
            "contradiction-watch")
        assert outcome["posting"]["memory_ref"] == (
            "watch-verify-on-devices")
        assert outcome["posting"]["posting_id"] == (
            "posting-watch-verify-on-devices")
        assert outcome["posting"]["standing"] == "sealed"
        assert outcome["record_news"]["type"] == (
            "private_by_architecture_posting")
        assert outcome["panel_record"]["type"] == (
            "private_by_architecture_panel")
        assert outcome["verdict_record"]["type"] == (
            "private_by_architecture_verdict")
        for kind in ("private_by_architecture_posting",
                     "private_by_architecture_panel",
                     "private_by_architecture_verdict"):
            assert len(_privacy_events(
                store, session_id, kind)) == 1
        # The posted watch stands exactly as it stood.
        assert agent.get_contradiction_watch(
            "watch-verify-on-devices") == watch_before
        with pytest.raises(ValueError, match="posted twice"):
            agent.post_over_contradiction_watch(
                "watch-verify-on-devices", home="workspace",
                posted_on=ON, recorded_by=BY,
                origin_session="session-test",
                posting_id="posting-again")
        agent.close()

    def test_post_over_contradiction_watch_unknown_id_raises(
            self, agent):
        with pytest.raises(KeyError):
            agent.post_over_contradiction_watch(
                "watch-nope", home="workspace",
                posted_on=ON, recorded_by=BY,
                origin_session="session-test")
        assert agent.privacy_status()["postings"] == []

    def test_register_book_holds_and_publishes_in_order(
            self, agent):
        book = _book()
        outcome = agent.register_privacy_book(book)
        assert outcome["count"] == 1
        assert [item["type"] for item in outcome["records_news"]] == [
            "private_by_architecture_posting"]
        assert outcome["panel_record"]["type"] == (
            "private_by_architecture_panel")
        assert agent.privacy_book().title == (
            "A test privacy book")
        with pytest.raises(ValueError):
            agent.register_privacy_book(book)
        with pytest.raises(ValueError, match="different title"):
            agent.register_privacy_book(_book(
                title="Another title",
                postings=[_posting(
                    posting_id="posting-other",
                    memory_ref="ref-other")]))
        broken = {"title": "A broken book",
                  "postings": [{"posting_id": "posting-x"}]}
        with pytest.raises(ValueError, match="missing its"):
            agent.register_privacy_book(broken)
        assert [item["posting_id"] for item in
                agent.privacy_status()["postings"]] == [
            "posting-test"]

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_privacy_book()
        assert outcome["count"] == 5
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_privacy_events(
            store, session_id, "private_by_architecture_posting")) == 5
        assert len(_privacy_events(
            store, session_id, "private_by_architecture_panel")) == 1
        assert agent.privacy_book().panels[0].panel_id == (
            "panel-m166-boundary")
        with pytest.raises(ValueError, match="already recorded"):
            agent.record_privacy_book()
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_privacy_book(tmp_path)
        book = load_private_by_architecture_file(path)
        outcome = agent.record_privacy_book(book)
        assert outcome["count"] == 5
        assert agent.get_privacy_posting(
            "posting-campaign-home").memory_kind == "session-note"

    def test_report_renders_the_example_when_unheld(self, agent):
        report = agent.report_privacy()
        assert report["book"]["posting_count"] == 5
        assert "posting-verify-remote" in report["postings_text"]
        assert "Panel in Private by architecture" in (
            report["panel_text"])
        assert "guarded" in report["verdict_text"]
        assert "posting-no-docker-map" in report["postings_text"]

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_privacy_posting(_posting())
        report = agent.report_privacy()
        assert report["book"]["title"] == "Private by architecture"
        assert "posting-verify-remote" not in report["postings_text"]
        assert "posting-test" in report["postings_text"]
        assert "sealed" in report["verdict_text"]

    def test_holding_moves_no_memory(
            self, agent, tmp_path):
        # HONEST BOUNDARY: holding a posting moves no
        # memory - the session's own contradiction and
        # subconscious holdings stand exactly as they
        # stood, the posted watch is never edited, and
        # there is no road here that carries a memory
        # anywhere, opens a bridge, or syncs a store.
        assert not hasattr(agent, "apply_privacy_posting")
        assert not hasattr(agent, "apply_privacy")
        assert not hasattr(agent, "run_privacy")
        assert not hasattr(agent, "persist_privacy")
        assert not hasattr(agent, "privacy_board")
        assert not hasattr(agent, "send_privacy_posting")
        assert not hasattr(agent, "sync_privacy_posting")
        assert not hasattr(agent, "schedule_privacy_posting")
        assert not hasattr(agent, "open_privacy_bridge")
        assert not hasattr(agent, "move_posted_memory")
        contradiction_before = agent.contradiction_book()
        subconscious_before = agent.subconscious_book()
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
        agent.register_privacy_posting(_posting())
        agent.post_over_contradiction_watch(
            "watch-verify-on-devices", home="workspace",
            posted_on=ON, recorded_by=BY,
            origin_session="session-test")
        assert agent.contradiction_book().watch_ids() == (
            contradiction_before.watch_ids())
        assert agent.subconscious_book().memory_ids() == (
            subconscious_before.memory_ids())
        assert agent.get_contradiction_watch(
            "watch-verify-on-devices").title == (
                contradiction_before.watches[0].title)
        assert builder.build() == built_before
        assert {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")} == before


class TestPrivacyTerminalSurface:
    def test_show_posting_kind_home_panel_verdict(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/private")
        assert "Private by Architecture (M-167)" in text
        _, _, text = _slash(
            agent, "/private posting posting-verify-remote")
        assert "verify the remote moved" in text
        _, _, text = _slash(agent, "/private kind crew-fact")
        assert "posting-verify-remote" in text
        assert "posting-campaign-home" not in text
        _, _, text = _slash(agent, "/private home user")
        assert "posting-campaign-home" in text
        assert "posting-no-docker-map" not in text
        _, _, text = _slash(agent, "/private panel")
        assert "Panel in Private by architecture" in text
        _, _, text = _slash(agent, "/private verdict")
        assert "guarded" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/private [show|posting <posting-id>"
                "|kind <memory-kind>|home <home>|panel|verdict]") in text
        _, _, text = _slash(agent, "/private dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/private posting posting-nope")
        assert "no posting in the book" in text


@pytest.fixture()
def privacy_handler(agent, monkeypatch):
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


def _privacy_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestPrivacyCommand:
    def test_show_is_default(self, privacy_handler, agent):
        privacy_handler._handle_private("")
        assert "Private by Architecture (M-167)" in (
            _privacy_published_text(privacy_handler))

    def test_posting_kind_home_panel_verdict(
            self, privacy_handler, agent):
        privacy_handler._handle_private(
            "posting posting-verify-remote")
        assert "posting-verify-remote" in (
            _privacy_published_text(privacy_handler))
        privacy_handler._handle_private("kind crew-fact")
        assert "posting-verify-remote" in _privacy_published_text(
            privacy_handler)
        privacy_handler._handle_private("home user")
        assert "posting-campaign-home" in _privacy_published_text(
            privacy_handler)
        privacy_handler._handle_private("panel")
        assert "Panel in Private by architecture" in (
            _privacy_published_text(privacy_handler))
        privacy_handler._handle_private("verdict")
        assert "guarded" in _privacy_published_text(
            privacy_handler)

    def test_bad_grammar_is_published(
            self, privacy_handler, agent):
        privacy_handler._handle_private("dance party")
        assert USAGE in _privacy_published_text(
            privacy_handler)
        privacy_handler._handle_private("posting posting-nope")
        assert "no posting in the book" in _privacy_published_text(
            privacy_handler)


class TestChatScreenRoutingPrivacy:
    def test_private_routes_as_system_command(self, monkeypatch):
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
            "/private kind crew-fact", _FakeLog())
        assert calls == [("/private", "kind crew-fact")]
