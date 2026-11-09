"""M-175 The Fuzzy Everything Picker - pure-layer tests.

TIER: integration

The pure layer is the picker candidate, held as
data: one findable thing with its kind in the
closed kind set (file, symbol, command, session,
model, theme - the roadmap's own order), its
label, its own detail line and its tags, with its
provenance whole (the day it was recorded, who
recorded it, its source and the session it was
recorded in). One query grammar judges every kind
the same way: the query text is read into word
tokens by the one token road, and a candidate's
score is derived from those tokens against the
candidate's own label, tags and detail - never
stored, never ranked by hand. A search is held as
its own record, its kind filter narrowing which
candidates stand in the search and never how they
are judged. Candidates are composed by import
from the shipped rooms the picker ranges over,
the panel is derived for one held search and the
verdict is derived for the whole book under one
search. The shipped example book is held in a
data file, and a loader reads a book from any
file. Nothing here opens a file, runs a command,
loads a model, applies a theme, joins a session,
renders a live UI, sends, posts, schedules, calls
a model or persists anything: a match held here
is a finding, never the act of opening the thing
found, and a search commits no choice at all.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.fuzzy_picker import (
    FUZZY_PICKER_RESOURCE,
    FUZZY_PICKER_SCHEMA,
    FUZZY_PICKER_SLICE,
    KIND_FILTERS,
    KINDS,
    PLAIN_EXPLANATION,
    USAGE,
    VERDICT_WORDS,
    FuzzyPanel,
    FuzzyPickerBook,
    FuzzyPickerRegistry,
    FuzzyVerdict,
    KindCount,
    PickerCandidate,
    PickerPanelRow,
    PickerSearch,
    book_record,
    build_book,
    build_candidate,
    build_panel,
    build_row,
    build_search,
    build_verdict,
    candidate_from_command,
    candidate_from_instruction_file,
    candidate_from_model,
    candidate_from_screen_review,
    candidate_from_session,
    candidate_from_theme,
    candidate_record,
    candidates_with_kind,
    derive_panel,
    derive_verdict,
    format_book,
    format_candidate,
    format_fuzzy_picker_screen,
    format_panel,
    format_search,
    format_verdict,
    inspect_candidate_source,
    line_of,
    load_fuzzy_picker,
    load_fuzzy_picker_file,
    normalize_kind,
    normalize_kind_filter,
    panel_plain_words,
    panel_record,
    parse_fuzzy_picker_args,
    parse_query,
    plain_words,
    rank_candidates,
    score_of,
    search_plain_words,
    search_record,
    total_candidates,
    validate_candidate,
    validate_panel,
    validate_row,
    validate_search,
    validate_verdict,
    verdict_plain_words,
    verdict_record,
)
from mythic_agent.core.instruction_files import build_entry
from mythic_agent.core.multi_session_projects import build_session
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.tui_redesign_charter import load_charter

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Fuzzy Picker at the M-174 slice boundary"

BY = "the coordinator"
ON = "2026-11-09"


def _candidate(**overrides):
    fields = {
        "candidate_id": "cand-test",
        "kind": "file",
        "label": "tests/test_thing.py",
        "detail": "The thing tests, standing for the tests.",
        "tags": ["tests", "file"],
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_candidate(fields)


def _stored_candidate(candidate):
    stored = candidate.to_record()
    for key in ("type", "slice", "line"):
        stored.pop(key)
    return stored


def _search(**overrides):
    fields = {
        "search_id": "search-test",
        "seq": 1,
        "text": "thing",
        "kind_filter": "all",
        "detail": "Find the thing for the tests.",
        "recorded_on": ON,
        "actor": BY,
        "source": "test source",
        "origin_session": "session-test",
    }
    fields.update(overrides)
    return build_search(fields)


def _stored_search(search):
    stored = search.to_record()
    for key in ("type", "slice", "tokens"):
        stored.pop(key)
    return stored


def _book(candidates=None, searches=(), **overrides):
    fields = {
        "title": "A test picker book",
        "candidates": [_stored_candidate(item) for item in (
            candidates if candidates is not None else [_candidate()])],
        "searches": [_stored_search(item) for item in searches],
    }
    fields.update(overrides)
    return build_book(fields)


def _mixed_book():
    return _book(
        candidates=[
            _candidate(),
            _candidate(candidate_id="cand-second", kind="command",
                       label="/thing",
                       detail="The thing command, for the tests.",
                       tags=["thing", "command"]),
            _candidate(candidate_id="cand-other", kind="theme",
                       label="other_theme",
                       detail="An unrelated theme, for the tests.",
                       tags=["theme"]),
        ],
        searches=[_search()])


# ---------------------------------------------------------------------
# The shipped example book, the roadmap and the charter.
# ---------------------------------------------------------------------


def test_shipped_book_loads_with_pinned_shape():
    book = load_fuzzy_picker()
    assert book.title == EXAMPLE_TITLE
    assert book.candidate_ids() == (
        "cand-approval-file", "cand-approval-symbol",
        "cand-approval-command", "cand-approval-tests",
        "cand-sliceboard-command", "cand-m174-session",
        "cand-sonnet-model", "cand-viking-theme")
    first = book.candidates[0]
    assert first.label == "mythic_agent/core/approval_cards.py"
    assert first.kind == "file"
    assert book.search_ids() == (
        "search-approval", "search-viking-theme")
    assert len(book.panels) == 1
    panel = book.panels[0]
    assert panel.panel_id == "panel-m174-boundary"
    assert panel.as_of == "2026-11-09"
    assert [row.candidate_id for row in panel.rows] == [
        "cand-approval-symbol", "cand-approval-file",
        "cand-approval-tests", "cand-approval-command",
        "cand-m174-session"]
    derived = derive_panel(book, "search-approval")
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert panel.total_candidates == derived.total_candidates == 8
    assert panel.total_matched == derived.total_matched == 5
    assert {c.kind: c.items for c in panel.kind_counts} == {
        "file": 2, "symbol": 1, "command": 1, "session": 1}
    assert derive_verdict(book, "search-approval").verdict == "matched"
    assert derive_verdict(book, "search-viking-theme").verdict == (
        "focused")
    raw = yaml.safe_load((
        ROOT / "mythic_agent" / "data" / FUZZY_PICKER_RESOURCE
    ).read_text(encoding="utf-8"))
    assert raw["schema"] == FUZZY_PICKER_SCHEMA
    assert raw["slice"] == "M-175"


def test_roadmap_names_the_slice():
    roadmap = load_roadmap()
    ids = [item.id for item in roadmap.slices]
    slice_ = roadmap.slices[ids.index("M-175")]
    assert slice_.title == "The fuzzy everything picker"
    assert slice_.part == 8
    assert "fuzzy finder grammar" in slice_.summary
    assert "files" in slice_.summary
    assert "themes" in slice_.summary
    assert FUZZY_PICKER_SLICE == "M-175"


def test_charter_s06_names_m175():
    charter = load_charter()
    screen = charter.screen("subagent_picker")
    assert screen.id == "S-06"
    assert screen.verdict == "keep"
    assert "M-175" in screen.owning_slices
    assert screen.judgement("K-01").standing == "strains"
    assert screen.judgement("K-09").standing == "strains"
    assert "fuzzy picker" in screen.direction
    assert "auto-dismiss" in screen.direction
    assert "plain words first" in screen.direction


def test_closed_vocabularies():
    assert KINDS == (
        "file", "symbol", "command", "session", "model", "theme")
    assert KIND_FILTERS == ("all",) + KINDS
    assert VERDICT_WORDS == ("matched", "focused", "empty")
    assert normalize_kind("files") == "file"
    assert normalize_kind("Themes") == "theme"
    assert normalize_kind_filter("everything") == "all"
    assert normalize_kind_filter("models") == "model"
    with pytest.raises(ValueError):
        normalize_kind("whenever")
    with pytest.raises(ValueError):
        normalize_kind_filter("whenever")
    assert "one fuzzy finder grammar" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /fuzzypicker")


# ---------------------------------------------------------------------
# The candidate: judged whole, its score derived by the one grammar.
# ---------------------------------------------------------------------


def test_candidate_record_round_trips():
    candidate = _candidate()
    assert build_candidate(_stored_candidate(candidate)) == candidate
    record = candidate.to_record()
    assert record["line"] == "tests/test_thing.py - file"
    assert record["type"] == "fuzzy_picker_candidate"
    assert record["tags"] == ["tests", "file"]
    assert candidate.line == line_of(candidate)


def test_candidate_provenance_is_whole_and_required():
    candidate = _candidate()
    assert candidate.actor == BY
    assert candidate.origin_session == "session-test"
    for missing in ("candidate_id", "kind", "label", "detail",
                    "tags", "recorded_on", "actor", "source",
                    "origin_session"):
        fields = _stored_candidate(candidate)
        fields.pop(missing)
        with pytest.raises(ValueError):
            build_candidate(fields)
    with pytest.raises(ValueError):
        _candidate(tags=[])


def test_candidate_refuses_unknown_keys_and_derived_keys():
    for derived_key, value in (
            ("score", 75), ("rank", 1),
            ("line", "tests/test_thing.py - file"),
            ("results", ["one"])):
        fields = _stored_candidate(_candidate())
        fields[derived_key] = value
        with pytest.raises(ValueError):
            build_candidate(fields)
    fields = _stored_candidate(_candidate())
    fields["surprise"] = "x"
    with pytest.raises(ValueError):
        build_candidate(fields)
    with pytest.raises(ValueError):
        _candidate(kind="whatever")


def test_candidate_alias_spellings_read_onto_the_fields():
    candidate = build_candidate({
        "id": "cand-alias", "type_of": "commands",
        "name": "/alias",
        "description": "An alias-spelled candidate for the tests.",
        "keywords": ["alias"], "day": ON, "by": BY,
        "source": "alias source", "session": "session-alias"})
    assert candidate.kind == "command"
    assert candidate.label == "/alias"
    assert candidate.detail == (
        "An alias-spelled candidate for the tests.")
    assert candidate.tags == ("alias",)


def test_score_and_line_are_derived_by_the_one_grammar():
    exact = _candidate(
        candidate_id="cand-alpha", label="alpha",
        detail="alpha stands here.", tags=["alpha"])
    assert score_of(exact, "alpha") == 225
    assert line_of(exact) == "alpha - file"
    opening = _candidate(
        candidate_id="cand-opening", label="alphabet",
        detail="nothing here.", tags=["zzz"])
    assert score_of(opening, "alpha") == 50
    holding = _candidate(
        candidate_id="cand-holding", label="xalpha",
        detail="nothing here.", tags=["zzz"])
    assert score_of(holding, "alpha") == 30
    threaded = _candidate(
        candidate_id="cand-threaded", label="axlxpxhxa",
        detail="nothing here.", tags=["zzz"])
    assert score_of(threaded, "alpha") == 10
    assert score_of(exact, {"text": "alpha", "kind_filter": "theme"}) == 0
    assert parse_query("Hello, World! 42") == ("hello", "world", "42")
    assert exact.to_record().get("score") is None


def test_one_grammar_for_every_kind():
    # The same query is parsed by the one token road
    # whatever kind it ranges over, and a kind filter
    # narrows which candidates stand - never the score.
    book = _mixed_book()
    search = _search(text="thing")
    ranked = rank_candidates(book.candidates, search)
    assert [c.candidate_id for c in ranked] == [
        "cand-second", "cand-test"]
    scores = {c.candidate_id: score_of(c, search) for c in ranked}
    assert scores["cand-second"] > scores["cand-test"] > 0
    only_files = _search(
        search_id="search-files", seq=2, text="thing",
        kind_filter="file")
    assert [c.candidate_id for c in rank_candidates(
        book.candidates, only_files)] == ["cand-test"]
    assert score_of(book.candidate_for("cand-test"), only_files) == (
        scores["cand-test"])


# ---------------------------------------------------------------------
# Composition: the shipped rooms, by import.
# ---------------------------------------------------------------------


def test_candidate_from_instruction_file_by_import():
    entry = build_entry({
        "filename": "CLAUDE.md", "origin": "foreign",
        "path": "docs/CLAUDE.md", "source": "docs directory",
        "layer": "dir",
        "reason": "A foreign tool's file for the docs directory.",
        "file_id": "instr-test-claude"})
    candidate = candidate_from_instruction_file(
        entry, candidate_id="cand-instr")
    assert candidate.kind == "file"
    assert candidate.label == "docs/CLAUDE.md"
    assert "CLAUDE.md" in candidate.detail
    with pytest.raises(ValueError):
        candidate_from_instruction_file(None, candidate_id="cand-x")


def test_candidate_from_screen_review_by_import():
    charter = load_charter()
    review = charter.screen("subagent_picker")
    candidate = candidate_from_screen_review(
        review, candidate_id="cand-screen")
    assert candidate.kind == "symbol"
    assert candidate.label == "SubagentSelectionModal"
    assert "keep" in candidate.detail
    with pytest.raises(ValueError):
        candidate_from_screen_review(
            {"symbol": "Fake"}, candidate_id="cand-x")


def test_candidate_from_model_by_import():
    candidate = candidate_from_model(
        {"model": "claude-3-5-sonnet"}, candidate_id="cand-model")
    assert candidate.kind == "model"
    assert candidate.label == "claude-3-5-sonnet"
    with pytest.raises(ValueError):
        candidate_from_model(42, candidate_id="cand-x")


def test_candidate_from_session_by_import():
    session = build_session({
        "session_id": "multisession-test",
        "title": "the test session, wiring the parser",
        "project": "mythic-agent-coder",
        "branch": "work/parser-wiring",
        "session_ref": "session-test",
        "journal_ref": "journal-test",
        "state": "active",
        "journal_entries": ["entry-test-1", "entry-test-2"],
        "shared_reads": 3,
        "recorded_by": "Volmarr",
        "recorded_on": "2026-11-08",
        "source": "test source"})
    candidate = candidate_from_session(
        session, candidate_id="cand-session")
    assert candidate.kind == "session"
    assert candidate.label == "the test session, wiring the parser"
    assert "mythic-agent-coder" in candidate.detail
    with pytest.raises(ValueError):
        candidate_from_session(None, candidate_id="cand-x")


def test_candidate_from_theme_by_import():
    candidate = candidate_from_theme(
        "viking_dark", candidate_id="cand-theme")
    assert candidate.kind == "theme"
    assert candidate.label == "viking_dark"
    assert "accessibility baseline" in candidate.detail
    with pytest.raises(ValueError):
        candidate_from_theme("no_such_theme", candidate_id="cand-x")


def test_candidate_from_command_shape():
    candidate = candidate_from_command(
        "/fuzzypicker", candidate_id="cand-cmd",
        detail="Shows the fuzzy everything picker.")
    assert candidate.kind == "command"
    assert candidate.label == "/fuzzypicker"
    with pytest.raises(ValueError):
        candidate_from_command(
            "fuzzypicker", candidate_id="cand-x",
            detail="No slash, no command.")
    with pytest.raises(ValueError):
        candidate_from_command(
            "/Fuzzy Picker", candidate_id="cand-x",
            detail="Not one lowercase word.")


def test_inspect_candidate_source_names_what_a_piece_is():
    found = inspect_candidate_source(
        {"kind": "files", "label": "docs/CLAUDE.md"})
    assert found["kind"] == "file"
    assert found["label"] == "docs/CLAUDE.md"
    bad = inspect_candidate_source({"kind": "nope", "label": "x"})
    assert bad["kind"] is None
    assert inspect_candidate_source({"label": "x"})["kind"] is None
    assert inspect_candidate_source("nope")["kind"] is None


# ---------------------------------------------------------------------
# The search record and the ranking: judged whole, derived order.
# ---------------------------------------------------------------------


def test_search_is_judged_whole():
    search = _search()
    assert search.tokens == ("thing",)
    assert build_search(_stored_search(search)) == search
    assert validate_search(_stored_search(search)) == search
    with pytest.raises(ValueError):
        _search(text="!!!")
    fields = _stored_search(search)
    fields["results"] = ["cand-test"]
    with pytest.raises(ValueError):
        build_search(fields)
    fields = _stored_search(search)
    fields["tokens"] = ["thing"]
    with pytest.raises(ValueError):
        build_search(fields)
    fields = _stored_search(search)
    fields.pop("detail")
    with pytest.raises(ValueError):
        build_search(fields)


def test_rank_candidates_orders_by_score_kind_label():
    book = load_fuzzy_picker()
    ranked = rank_candidates(
        book.candidates, book.search_for("search-approval"))
    assert [c.candidate_id for c in ranked] == [
        "cand-approval-symbol", "cand-approval-file",
        "cand-approval-tests", "cand-approval-command",
        "cand-m174-session"]
    assert [score_of(c, book.search_for("search-approval"))
            for c in ranked] == [75, 55, 55, 55, 50]


# ---------------------------------------------------------------------
# The panel and the verdict: derived, never chosen.
# ---------------------------------------------------------------------


def test_panel_is_derived_for_one_search():
    book = _mixed_book()
    panel = derive_panel(book, "search-test")
    assert panel.total_candidates == 3
    assert panel.total_matched == 2
    assert [row.candidate_id for row in panel.rows] == [
        "cand-second", "cand-test"]
    assert {c.kind: c.items for c in panel.kind_counts} == {
        "file": 1, "command": 1}
    assert panel.rows[0].line == "/thing - command"
    assert panel.search_id == "search-test"
    assert KindCount(kind="files", items=2).to_record() == {
        "kind": "file", "items": 2}
    assert isinstance(panel, FuzzyPanel)


def test_panel_refuses_a_stored_panel_that_disagrees():
    book = _mixed_book()
    stored = derive_panel(book, "search-test").to_record()
    stored.pop("type")
    stored.pop("slice")
    stored["total_matched"] = 3
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    stored = derive_panel(book, "search-test").to_record()
    stored.pop("type")
    stored.pop("slice")
    stored["rows"][0]["score"] = 999
    with pytest.raises(ValueError):
        validate_panel(stored, book)
    panel = build_panel(
        derive_panel(book, "search-test").to_record(), book)
    assert panel.total_matched == 2


def test_row_is_judged_against_its_candidate_and_search():
    candidate = _candidate()
    search = _search(text="thing")
    row = build_row(candidate=candidate, search=search)
    assert row.score == score_of(candidate, search)
    assert row.line == "tests/test_thing.py - file"
    assert validate_row(row.to_record(), candidate, search) == row
    bad = row.to_record()
    bad["score"] = row.score + 1
    with pytest.raises(ValueError):
        validate_row(bad, candidate, search)
    bad = row.to_record()
    bad["line"] = "a chosen line"
    with pytest.raises(ValueError):
        validate_row(bad, candidate, search)
    assert isinstance(row, PickerPanelRow)


def test_verdict_words_matched_focused_empty():
    book = load_fuzzy_picker()
    assert derive_verdict(book, "search-approval").verdict == "matched"
    assert derive_verdict(
        book, "search-viking-theme").verdict == "focused"
    empty_search = _search(
        search_id="search-empty", seq=9, text="zzzz",
        detail="Find nothing, for the tests.")
    empty = derive_verdict(book, empty_search)
    assert empty.verdict == "empty"
    assert empty.total_matched == 0
    assert build_verdict(empty.to_record(), book, empty_search) == empty
    with pytest.raises(ValueError):
        FuzzyVerdict(
            total_candidates=8, total_matched=5, distinct_kinds=4,
            earliest_on=ON, latest_on=ON, verdict="focused")
    with pytest.raises(ValueError):
        validate_verdict(empty.to_record(), book, "search-approval")
    assert isinstance(empty, FuzzyVerdict)


# ---------------------------------------------------------------------
# The book, the file loader and the registry.
# ---------------------------------------------------------------------


def test_book_laws_one_candidate_per_id_and_searches_in_order():
    with pytest.raises(ValueError):
        _book(candidates=[_candidate(), _candidate(label="another.py")])
    with pytest.raises(ValueError):
        _book(searches=[
            _search(), _search(search_id="search-two", text="other")])
    book = _mixed_book()
    assert book.candidate_for("cand-second").label == "/thing"
    assert book.search_for("search-test").text == "thing"
    with pytest.raises(KeyError):
        book.candidate_for("cand-nope")
    with pytest.raises(KeyError):
        book.search_for("search-nope")
    assert total_candidates(book) == 3
    assert [c.candidate_id for c in candidates_with_kind(
        book, "commands")] == ["cand-second"]
    assert isinstance(book, FuzzyPickerBook)


def test_book_file_loader_reads_any_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "fuzzy_picker.yaml").read_text(encoding="utf-8")
    path = tmp_path / "fuzzy_picker.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_fuzzy_picker_file(path)
    assert book.title == EXAMPLE_TITLE
    assert total_candidates(book) == 8


def test_registry_holds_candidates_and_searches_one_by_one():
    registry = FuzzyPickerRegistry()
    registry.register_candidate(_candidate())
    registry.register_candidate(_candidate(
        candidate_id="cand-second", kind="command", label="/thing",
        detail="The thing command, for the tests.",
        tags=["thing", "command"]))
    held = registry.register_search(_search(search_id=None))
    assert held.search_id == "search-1"
    assert registry.latest_search().search_id == "search-1"
    assert registry.book().title == "Fuzzy Picker"
    assert registry.panel("search-1").total_matched == 2
    assert registry.verdict("search-1").verdict == "matched"
    with pytest.raises(ValueError):
        registry.register_candidate(_candidate(label="another.py"))
    with pytest.raises(ValueError):
        registry.register_search(_search(search_id="search-1", seq=2))
    with pytest.raises(ValueError):
        registry.register_search(_search(search_id="search-two"))
    assert [s.search_id for s in registry.list_searches()] == ["search-1"]
    with pytest.raises(KeyError):
        registry.get_candidate("cand-nope")
    with pytest.raises(KeyError):
        registry.get_search("search-nope")


def test_registry_register_book_and_refusals():
    registry = FuzzyPickerRegistry()
    book = registry.register_book(_mixed_book())
    assert total_candidates(book) == 3
    assert registry.title() == "A test picker book"
    with pytest.raises(ValueError):
        registry.register_book(_book())
    other = FuzzyPickerRegistry(_book())
    assert other.get_candidate("cand-test").candidate_id == "cand-test"
    assert isinstance(other.book(), FuzzyPickerBook)
    assert isinstance(_candidate(), PickerCandidate)
    assert isinstance(_search(), PickerSearch)


# ---------------------------------------------------------------------
# News, plain words, formatters and the grammar.
# ---------------------------------------------------------------------


def test_news_records_carry_headlines():
    candidate = _candidate()
    news = candidate_record(candidate)
    assert news["news"] is True
    assert news["type"] == "fuzzy_picker_candidate"
    assert "tests/test_thing.py - file" in news["headline"]
    search_news = search_record(_search())
    assert search_news["type"] == "fuzzy_picker_search"
    assert "thing" in search_news["headline"]
    panel_news = panel_record(derive_panel(_mixed_book(), "search-test"))
    assert "Fuzzy picker panel" in panel_news["headline"]
    verdict_news = verdict_record(
        derive_verdict(_mixed_book(), "search-test"))
    assert "matched" in verdict_news["headline"]
    book_news = book_record(_mixed_book())
    assert book_news["candidate_count"] == 3
    assert book_news["search_count"] == 1


def test_formatters_and_screen():
    book = load_fuzzy_picker()
    text = format_candidate(book.candidate_for("cand-viking-theme"))
    assert "Kind: theme" in text
    assert "Label: viking_dark" in text
    search_text = format_search(book.search_for("search-approval"))
    assert "Tokens: approval" in search_text
    listed = format_book(book)
    assert "cand-approval-file: mythic_agent/core/approval_cards.py" in (
        listed)
    commands = format_book(book, kind="command")
    assert "cand-approval-command" in commands
    assert "cand-sonnet-model" not in commands
    assert "Panel in Fuzzy Picker at the M-174 slice boundary" in (
        format_panel(book))
    assert format_verdict(book).startswith(
        "Verdict in Fuzzy Picker over")
    assert "matched" in format_verdict(book)
    screen = format_fuzzy_picker_screen()
    assert "Fuzzy Picker (M-175)" in screen
    assert "commits" in screen
    assert "viking_dark - theme" in plain_words(
        book.candidate_for("cand-viking-theme"))
    assert "commits no choice" in search_plain_words(
        book.search_for("search-approval"))
    assert "Matches, in ranked order" in panel_plain_words(book)
    assert "matched" in verdict_plain_words(book)


def test_parse_fuzzy_picker_args_grammar():
    assert parse_fuzzy_picker_args("") == ("show", None)
    assert parse_fuzzy_picker_args(None) == ("show", None)
    assert parse_fuzzy_picker_args("show") == ("show", None)
    assert parse_fuzzy_picker_args("list") == ("show", None)
    assert parse_fuzzy_picker_args("candidate cand-test") == (
        "candidate", "cand-test")
    assert parse_fuzzy_picker_args("search search-approval") == (
        "search", "search-approval")
    assert parse_fuzzy_picker_args("find approval cards") == (
        "find", "approval cards")
    assert parse_fuzzy_picker_args("kind files") == ("kind", "file")
    assert parse_fuzzy_picker_args("panel") == ("panel", None)
    assert parse_fuzzy_picker_args("verdict") == ("verdict", None)
    for bad in ("candidate", "search", "find", "kind whenever",
                "panel now", "dance", 42):
        with pytest.raises(ValueError):
            parse_fuzzy_picker_args(bad)


def test_pure_layer_imports_no_agent_or_ui():
    text = (ROOT / "mythic_agent" / "core"
            / "fuzzy_picker.py").read_text(encoding="utf-8")
    assert "mythic_agent.agents" not in text
    assert "import textual" not in text
    assert "from ..agents" not in text


# -- agent layer -----------------------------------------------------------
#
# M-175 agent layer: the agent holds a
# FuzzyPickerRegistry for the session (session
# state only, no new setting), candidates and
# search records are held by being registered -
# each judged whole before it is held - published
# as their candidate_record / search_record session
# news through the checkpoint road, deduped per
# shape - a candidate composed from a shipped room
# by import stands on the register road exactly as
# the pure layer composed it, the finding road
# composes one search record at the held book's
# next sequence and publishes the derived panel
# and verdict news with it, whole-book register
# and record roads hold a book judged whole first,
# the report road renders the held book (or the
# shipped example when unheld) through the pure
# formatters, and the /fuzzypicker surface rides
# both roads on the pure parser + formatters.
# Status, get, kind, panel, verdict and report
# reads register and publish nothing, answer from
# the held registry first and from the shipped
# example only while nothing is held - a held
# candidate never falls back to the example. The
# panel and the verdict derive at call time from
# the whole book under a search, never held. This
# layer sends nothing, posts nothing, schedules
# nothing, calls no model, persists nothing beyond
# the session journal news, opens nothing the
# picker finds, executes nothing, renders no live
# UI and banks nothing - a match held here is a
# finding, never the act of opening the thing
# found, and a search commits no choice at all.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _picker_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_book_file(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "fuzzy_picker.yaml").read_text(encoding="utf-8")
    path = tmp_path / "fuzzy_picker.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestFuzzyPickerAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.fuzzy_picker_status()
        assert status["candidates"] == []
        assert status["searches"] == []
        assert status["book"] is None
        assert status["fuzzy_picker"]["title"] == EXAMPLE_TITLE
        assert len(status["fuzzy_picker"]["candidates"]) == 8
        assert len(status["fuzzy_picker"]["searches"]) == 2
        assert status["panel"]["total_candidates"] == 8
        assert status["panel"]["total_matched"] == 5
        assert status["panels"][0]["panel_id"] == "panel-m174-boundary"
        assert status["book_record"]["candidate_count"] == 8
        assert status["book_record"]["search_count"] == 2
        assert status["verdict"]["verdict"] == "matched"
        assert "viking_dark - theme" in status["plain_words"]
        assert "Fuzzy Picker (M-175)" in status["screen"]
        assert "5 of 8 candidates match" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._fuzzy_picker_registry()
        assert agent._fuzzy_picker_registry() is first
        assert agent._fuzzy_picker_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.fuzzy_picker_status()
        assert agent.get_fuzzy_candidate(
            "cand-viking-theme").kind == "theme"
        assert agent.get_fuzzy_search(
            "search-approval").text == "approval"
        assert [c.candidate_id for c in agent.fuzzy_picker_with_kind(
            "command")] == [
                "cand-approval-command", "cand-sliceboard-command"]
        assert [c.candidate_id for c in agent.fuzzy_picker_with_kind(
            "files")] == ["cand-approval-file", "cand-approval-tests"]
        agent.fuzzy_picker_panel()
        agent.fuzzy_picker_verdict()
        agent.report_fuzzy_picker()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("fuzzy_picker")] == []
        with pytest.raises(KeyError):
            agent.get_fuzzy_candidate("cand-nope")
        with pytest.raises(KeyError):
            agent.get_fuzzy_search("search-nope")
        agent.close()

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_fuzzy_candidate(_candidate())
        status = agent.fuzzy_picker_status()
        assert [item["candidate_id"] for item in status["candidates"]] == [
            "cand-test"]
        assert status["book"]["title"] == "Fuzzy Picker"
        assert status["panel"] is None
        assert status["verdict"] is None

    def test_held_candidate_never_falls_back_to_the_example(
            self, agent):
        agent.register_fuzzy_candidate(_candidate())
        with pytest.raises(KeyError):
            agent.get_fuzzy_candidate("cand-approval-file")
        with pytest.raises(KeyError):
            agent.get_fuzzy_search("search-approval")
        candidate = agent.get_fuzzy_candidate("cand-test")
        assert candidate.label == "tests/test_thing.py"
        assert agent.fuzzy_picker_book().title == "Fuzzy Picker"


class TestFuzzyPickerAgentHolding:
    def test_register_candidate_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_fuzzy_candidate(_candidate())
        assert outcome["candidate"]["candidate_id"] == "cand-test"
        assert outcome["record_news"]["news"] is True
        assert outcome["record_news"]["type"] == "fuzzy_picker_candidate"
        assert "cand-test" in outcome["screen"]
        agent.register_fuzzy_candidate(_candidate(
            candidate_id="cand-second", kind="command", label="/thing",
            detail="The thing command, for the tests.",
            tags=["thing", "command"]))
        events = _picker_events(store, session_id, "fuzzy_picker_candidate")
        assert len(events) == 2
        agent._publish_fuzzy_picker_record(candidate_record(_candidate()))
        agent._publish_fuzzy_picker_record(
            {"type": "slice_board_card", "news": True})
        events = _picker_events(store, session_id, "fuzzy_picker_candidate")
        assert len(events) == 2
        agent.close()

    def test_duplicate_candidate_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_fuzzy_candidate(_candidate())
        with pytest.raises(ValueError):
            agent.register_fuzzy_candidate(_candidate())
        with pytest.raises(ValueError):
            agent.register_fuzzy_candidate(
                _candidate(label="another.py"))
        events = _picker_events(store, session_id, "fuzzy_picker_candidate")
        assert len(events) == 1
        agent.close()

    def test_composed_candidates_hold_by_import(self, agent):
        entry = build_entry({
            "filename": "CLAUDE.md", "origin": "foreign",
            "path": "docs/CLAUDE.md", "source": "docs directory",
            "layer": "dir",
            "reason": "A foreign tool's file for the docs directory.",
            "file_id": "instr-test-claude"})
        composed = candidate_from_instruction_file(
            entry, candidate_id="cand-instr")
        outcome = agent.register_fuzzy_candidate(composed)
        assert outcome["candidate"]["label"] == "docs/CLAUDE.md"
        theme = candidate_from_theme(
            "viking_dark", candidate_id="cand-theme")
        agent.register_fuzzy_candidate(theme)
        command = candidate_from_command(
            "/fuzzypicker", candidate_id="cand-cmd",
            detail="Shows the fuzzy everything picker.")
        agent.register_fuzzy_candidate(command)
        assert [c.candidate_id for c in agent.fuzzy_picker_with_kind(
            "theme")] == ["cand-theme"]
        assert agent.get_fuzzy_candidate(
            "cand-cmd").label == "/fuzzypicker"

    def test_register_search_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_fuzzy_candidate(_candidate())
        outcome = agent.register_fuzzy_search(_search())
        assert outcome["search"]["search_id"] == "search-test"
        assert outcome["record_news"]["type"] == "fuzzy_picker_search"
        with pytest.raises(ValueError):
            agent.register_fuzzy_search(_search(seq=2))
        with pytest.raises(ValueError):
            agent.register_fuzzy_search(
                _search(search_id="search-two"))
        assert [s.search_id for s in
                agent._fuzzy_picker_registry().list_searches()] == [
                    "search-test"]
        events = _picker_events(store, session_id, "fuzzy_picker_search")
        assert len(events) == 1
        agent.close()

    def test_find_road_derives_sequence_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_fuzzy_candidate(_candidate())
        agent.register_fuzzy_candidate(_candidate(
            candidate_id="cand-second", kind="command", label="/thing",
            detail="The thing command, for the tests.",
            tags=["thing", "command"]))
        outcome = agent.find_fuzzy_search("thing")
        assert outcome["search"]["seq"] == 1
        assert outcome["search"]["search_id"] == "search-1"
        assert outcome["record_news"]["type"] == "fuzzy_picker_search"
        assert outcome["panel_record"]["type"] == "fuzzy_picker_panel"
        assert outcome["panel_record"]["total_matched"] == 2
        assert outcome["verdict_record"]["type"] == (
            "fuzzy_picker_verdict")
        assert outcome["verdict_record"]["verdict"] == "matched"
        second = agent.find_fuzzy_search(
            "thing", kind_filter="file",
            detail="Find the thing file alone, for the tests.")
        assert second["search"]["seq"] == 2
        assert second["verdict_record"]["verdict"] == "focused"
        assert agent.fuzzy_picker_verdict().verdict == "matched"
        assert len(_picker_events(
            store, session_id, "fuzzy_picker_search")) == 2
        assert len(_picker_events(
            store, session_id, "fuzzy_picker_verdict")) == 2
        agent.close()

    def test_find_road_refuses_an_empty_query(self, agent):
        agent.register_fuzzy_candidate(_candidate())
        with pytest.raises(ValueError):
            agent.find_fuzzy_search("!!!")
        assert agent._fuzzy_picker_registry().list_searches() == ()

    def test_register_book_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_fuzzy_picker_book(_mixed_book())
        assert outcome["count"] == 3
        assert [c["candidate_id"] for c in outcome["candidates"]] == [
            "cand-test", "cand-second", "cand-other"]
        assert [r["type"] for r in outcome["records_news"]] == [
            "fuzzy_picker_candidate", "fuzzy_picker_candidate",
            "fuzzy_picker_candidate", "fuzzy_picker_search"]
        events = _picker_events(store, session_id, "fuzzy_picker_candidate")
        assert [e["candidate_id"] for e in events] == [
            "cand-test", "cand-second", "cand-other"]
        assert agent.fuzzy_picker_book().title == (
            "A test picker book")
        with pytest.raises(ValueError):
            agent.register_fuzzy_picker_book(_mixed_book())
        agent.close()

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_fuzzy_picker_book()
        assert outcome["count"] == 8
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_picker_events(
            store, session_id, "fuzzy_picker_candidate")) == 8
        assert len(_picker_events(
            store, session_id, "fuzzy_picker_search")) == 2
        status = agent.fuzzy_picker_status()
        assert status["panels"][0]["panel_id"] == "panel-m174-boundary"
        with pytest.raises(ValueError):
            agent.record_fuzzy_picker_book()
        agent.close()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_book_file(tmp_path)
        book = load_fuzzy_picker_file(path)
        outcome = agent.record_fuzzy_picker_book(book)
        assert outcome["count"] == 8
        assert agent.fuzzy_picker_book().title == EXAMPLE_TITLE

    def test_report_renders_example_then_held_book_only(self, agent):
        report = agent.report_fuzzy_picker()
        assert report["book"]["title"] == EXAMPLE_TITLE
        assert len(report["candidates"]) == 8
        assert report["verdict"]["verdict"] == "matched"
        assert "cand-viking-theme: viking_dark - theme" in (
            report["book_text"])
        agent.register_fuzzy_candidate(_candidate())
        report = agent.report_fuzzy_picker()
        assert [c["candidate_id"] for c in report["candidates"]] == [
            "cand-test"]
        assert "cand-test: tests/test_thing.py - file" in (
            report["book_text"])
        assert report["verdict"] is None

    def test_holding_and_finding_execute_nothing(self, agent):
        for name in (
                "run_fuzzy_picker", "execute_fuzzy_picker",
                "open_fuzzy_candidate", "apply_fuzzy_theme",
                "load_fuzzy_model", "join_fuzzy_session",
                "run_fuzzy_command", "bank_fuzzy_picker",
                "persist_fuzzy_picker", "send_fuzzy_picker",
                "schedule_fuzzy_picker", "render_fuzzy_picker_ui",
                "delete_fuzzy_candidate"):
            assert not hasattr(agent, name), name
        agent.register_fuzzy_candidate(_candidate())
        agent.find_fuzzy_search("thing")
        # A search held here only ever looks: nothing
        # was opened, executed or applied, and the
        # picker's standing lives in no setting.
        assert agent.fuzzy_picker_book().title == "Fuzzy Picker"
        assert agent.config.get("fuzzy_picker") is None


class TestFuzzyPickerTerminalSurface:
    def test_show_candidate_search_find_kind_panel_verdict(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/fuzzypicker")
        assert "Fuzzy Picker (M-175)" in text
        _, _, text = _slash(
            agent, "/fuzzypicker candidate cand-viking-theme")
        assert "Kind: theme" in text
        assert "Label: viking_dark" in text
        _, _, text = _slash(agent, "/fuzzypicker search search-approval")
        assert "Tokens: approval" in text
        _, _, text = _slash(agent, "/fuzzypicker find viking")
        assert "cand-viking-theme" in text
        _, _, text = _slash(agent, "/fuzzypicker kind theme")
        assert "cand-viking-theme" in text
        assert "cand-sonnet-model" not in text
        _, _, text = _slash(agent, "/fuzzypicker panel")
        assert "Panel in Fuzzy Picker at the M-174 slice boundary" in (
            text)
        _, _, text = _slash(agent, "/fuzzypicker verdict")
        assert "matched" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/fuzzypicker [show|candidate <candidate-id>"
                "|search <search-id>|find <words>|kind <kind>"
                "|panel|verdict]") in text
        _, _, text = _slash(agent, "/fuzzypicker dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/fuzzypicker candidate cand-nope")
        assert "no candidate named" in text


@pytest.fixture()
def picker_handler(agent, monkeypatch):
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


def _picker_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestFuzzyPickerCommand:
    def test_show_is_default(self, picker_handler, agent):
        picker_handler._handle_fuzzypicker("")
        assert "Fuzzy Picker (M-175)" in (
            _picker_published_text(picker_handler))

    def test_candidate_search_panel_verdict(
            self, picker_handler, agent):
        picker_handler._handle_fuzzypicker("candidate cand-viking-theme")
        assert "Label: viking_dark" in (
            _picker_published_text(picker_handler))
        picker_handler._handle_fuzzypicker("search search-approval")
        assert "Tokens: approval" in _picker_published_text(
            picker_handler)
        picker_handler._handle_fuzzypicker("panel")
        assert "Panel in Fuzzy Picker" in (
            _picker_published_text(picker_handler))
        picker_handler._handle_fuzzypicker("verdict")
        assert "matched" in _picker_published_text(picker_handler)

    def test_bad_grammar_is_published(
            self, picker_handler, agent):
        picker_handler._handle_fuzzypicker("dance party")
        assert USAGE in _picker_published_text(picker_handler)
        picker_handler._handle_fuzzypicker("candidate cand-nope")
        assert "no candidate named" in _picker_published_text(
            picker_handler)


class TestChatScreenRoutingFuzzyPicker:
    def test_fuzzypicker_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/fuzzypicker panel", _FakeLog())
        assert calls == [("/fuzzypicker", "panel")]

    def test_chat_screen_help_and_usage_name_the_picker(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert "/fuzzypicker[/green] - show the fuzzy everything picker (M-175)" in (
            text)
        assert ('"/fuzzypicker": "Usage: /fuzzypicker | '
                '/fuzzypicker candidate <candidate-id>') in text
