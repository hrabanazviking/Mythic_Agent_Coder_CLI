"""M-149 Instruction files unified - pure-layer tests.

TIER: integration

The pure layer is the instruction-files canon as
data: one book of entry records (one instruction
file in force - its filename in the closed canon
this slice names, the origin that filename truly
carries, its path, its source, its layer and the
plain-words reason it stands), the shipped example
book held in a data file, a loader that reads a
book from any file, ONE precedence order across
every filename (the layer ranks first, in the
shipped elder order, and inside one layer the
filenames rank in the canon's order), a panel
derived from the whole book, a scan road that
reads a real workspace through the shipped
instruction resolver composed by import, records
shaped as session news, and a registry. The rank
is derived from the filename and layer, never
stored: a stored rank disagreeing with the derived
rank is refused, and a stored panel disagreeing
with the panel derived from its book is refused.
A foreign file is honoured on its own turf: its
origin is the origin its filename carries, and
naming it as ours refuses at construction. Nothing
here writes, renames or applies a file: holding
the account changes no file, and a scan leaves
every workspace file byte-identical.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.validation import ValidationError
from mythic_agent.core.instruction_files import (
    PLAIN_EXPLANATION,
    INSTRUCTION_FILES_RESOURCE,
    INSTRUCTION_FILES_SCHEMA,
    INSTRUCTION_FILES_SLICE,
    INSTRUCTION_FILENAMES,
    INSTRUCTION_LAYERS,
    INSTRUCTION_ORIGINS,
    INSTRUCTION_PRECEDENCE,
    ORIGIN_KINDS,
    USAGE,
    InstructionFileEntry,
    InstructionFilesBook,
    InstructionFilesRegistry,
    InstructionOriginCount,
    InstructionPanel,
    InstructionPanelRow,
    book_record,
    build_book,
    build_entry,
    build_panel,
    build_row,
    derive_panel,
    entry_record,
    format_entries,
    format_entry,
    format_instruction_files_screen,
    format_panel,
    load_instruction_files,
    load_instruction_files_file,
    normalize_filename,
    normalize_layer,
    normalize_origin,
    origin_for,
    panel_plain_words,
    panel_record,
    parse_instruction_files_args,
    plain_words,
    precedence_rank,
    scan_workspace,
    validate_book,
    validate_entry,
    validate_panel,
    validate_row,
)

ROOT = Path(__file__).resolve().parents[1]


def _entry(**overrides):
    fields = {
        "filename": "CLAUDE.md", "origin": "foreign",
        "path": "docs/CLAUDE.md", "source": "docs directory",
        "layer": "dir",
        "reason": "A foreign tool's file for the docs directory.",
        "file_id": "instr-test-claude",
    }
    fields.update(overrides)
    return build_entry(fields)


def test_constants_and_usage():
    assert INSTRUCTION_FILES_SLICE == "M-149"
    assert INSTRUCTION_FILES_SCHEMA == "mythic.instruction_files/1"
    assert INSTRUCTION_FILES_RESOURCE.endswith("instruction_files.yaml")
    assert INSTRUCTION_PRECEDENCE == (
        "RULES.AI.md", "AGENTS.md", ".mythic.md", ".mythic",
        "CLAUDE.md", ".muserules", ".cursorrules", ".aider.rules.md")
    assert INSTRUCTION_FILENAMES == INSTRUCTION_PRECEDENCE
    assert INSTRUCTION_LAYERS == ("system", "repo", "dir", "file")
    assert ORIGIN_KINDS == ("ours", "standard", "foreign")
    assert INSTRUCTION_ORIGINS == {
        "RULES.AI.md": "ours", "AGENTS.md": "standard",
        ".mythic.md": "ours", ".mythic": "ours",
        "CLAUDE.md": "foreign", ".muserules": "foreign",
        ".cursorrules": "foreign", ".aider.rules.md": "foreign"}
    assert "/instructionfiles" in USAGE
    assert "foreign" in PLAIN_EXPLANATION


def test_elder_resolver_gap_is_exactly_rules_ai():
    # The shipped instruction resolver's own filename
    # set lacks exactly one canon filename: ours.
    from mythic_agent.context.instructions import (
        INSTRUCTION_FILENAMES as ELDER_FILENAMES)
    assert set(INSTRUCTION_PRECEDENCE) == (
        set(ELDER_FILENAMES) | {"RULES.AI.md"})
    assert "RULES.AI.md" not in ELDER_FILENAMES


def test_shipped_example_shape():
    book = load_instruction_files()
    assert book.title == "Instruction files at the M-148 slice boundary"
    assert [e.file_id for e in book.entries] == [
        "instr-rules-root", "instr-agents-root", "instr-claude-root",
        "instr-mythic-package", "instr-cursor-package",
        "instr-mythic-plain"]
    assert [e.filename for e in book.entries] == [
        "RULES.AI.md", "AGENTS.md", "CLAUDE.md",
        ".mythic.md", ".cursorrules", ".mythic"]
    assert [e.origin for e in book.entries] == [
        "ours", "standard", "foreign", "ours", "foreign", "ours"]
    assert book.entry_for("instr-claude-root").layer == "repo"
    with pytest.raises(KeyError):
        book.entry_for("instr-nope")
    assert [e.file_id for e in book.entries_for_origin("foreign")] == [
        "instr-claude-root", "instr-cursor-package"]
    assert [e.file_id for e in book.entries_for_layer("dir")] == [
        "instr-mythic-package", "instr-cursor-package",
        "instr-mythic-plain"]


def test_shipped_panel_is_pinned_and_derived():
    book = load_instruction_files()
    assert len(book.panels) == 1
    stored = book.panels[0]
    assert stored.panel_id == "panel-m148-boundary"
    assert [(r.file_id, r.rank) for r in stored.rows] == [
        ("instr-rules-root", 10), ("instr-agents-root", 11),
        ("instr-claude-root", 14), ("instr-mythic-package", 22),
        ("instr-mythic-plain", 23), ("instr-cursor-package", 26)]
    assert stored.total_files == 6
    assert [(c.origin, c.files) for c in stored.origin_counts] == [
        ("ours", 3), ("standard", 1), ("foreign", 2)]
    assert stored.account[0] == (
        "The panel holds 6 instruction file(s) in force: "
        "ours 3, standard 1, foreign 2.")
    derived = derive_panel(book)
    assert derived.rows == stored.rows
    assert derived.origin_counts == stored.origin_counts
    assert derived.account == stored.account
    assert validate_panel(stored, book) == stored


def test_origin_for_and_rank_derivation():
    assert origin_for("RULES.AI.md") == "ours"
    assert origin_for("AGENTS.md") == "standard"
    assert origin_for("CLAUDE.md") == "foreign"
    assert precedence_rank("RULES.AI.md", "repo") == 10
    assert precedence_rank("AGENTS.md", "repo") == 11
    assert precedence_rank("CLAUDE.md", "repo") == 14
    assert precedence_rank(".mythic", "dir") == 23
    assert precedence_rank(".aider.rules.md", "system") == 7
    assert precedence_rank("CLAUDE.md", "file") == 34
    # Layer outranks filename: any repo file beats
    # any dir file, whatever the names say.
    assert precedence_rank(".aider.rules.md", "repo") < precedence_rank(
        "RULES.AI.md", "dir")
    with pytest.raises(ValueError):
        origin_for("README.md")
    with pytest.raises(ValueError):
        precedence_rank("RULES.AI.md", "attic")


def test_foreign_file_is_never_claimed_as_ours():
    with pytest.raises(ValueError) as caught:
        _entry(origin="ours")
    assert "never claimed as ours" in str(caught.value)
    with pytest.raises(ValueError):
        build_entry(filename="AGENTS.md", origin="foreign",
                    path="AGENTS.md", source="workspace root",
                    layer="repo", reason="Not the standard.")
    with pytest.raises(ValueError):
        build_entry(filename="RULES.AI.md", origin="standard",
                    path="RULES.AI.md", source="workspace root",
                    layer="repo", reason="Not a standard file.")
    # And a foreign entry, honestly named, keeps its
    # own origin through every record it makes.
    entry = _entry()
    assert entry.origin == "foreign"
    assert entry.to_record()["origin"] == "foreign"
    assert "foreign" in plain_words(entry)


def test_entry_validation_and_aliases():
    entry = build_entry({
        "name": "AGENTS.md", "origin": "standard",
        "path": "AGENTS.md", "origin_source": "workspace root",
        "layer": "repo", "why": "The standard file.",
        "id": "instr-alias-agents"})
    assert entry.file_id == "instr-alias-agents"
    assert entry.source == "workspace root"
    assert entry.reason == "The standard file."
    with pytest.raises(ValueError):
        build_entry({"filename": "AGENTS.md", "origin": "standard",
                     "path": "AGENTS.md", "source": "workspace root",
                     "layer": "repo", "reason": "x", "bogus": 1})
    with pytest.raises(ValueError):
        build_entry({"origin": "ours", "path": "RULES.AI.md",
                     "source": "workspace root", "layer": "repo",
                     "reason": "No filename named."})
    with pytest.raises(ValueError):
        build_entry({"filename": "RULES.AI.md", "name": "AGENTS.md",
                     "origin": "ours", "path": "RULES.AI.md",
                     "source": "workspace root", "layer": "repo",
                     "reason": "Two spellings disagree."})
    with pytest.raises(ValueError):
        _entry(path="a path with spaces.md")
    with pytest.raises(ValueError):
        _entry(path="x" * 301)


def test_stored_rank_is_judged_against_the_derived_rank():
    entry = validate_entry({
        "filename": "RULES.AI.md", "origin": "ours",
        "path": "RULES.AI.md", "source": "workspace root",
        "layer": "repo", "reason": "Ours.", "rank": 10})
    assert entry.rank == 10
    with pytest.raises(ValueError) as caught:
        validate_entry({
            "filename": "RULES.AI.md", "origin": "ours",
            "path": "RULES.AI.md", "source": "workspace root",
            "layer": "repo", "reason": "Ours.", "rank": 99})
    assert "disagrees with the rank derived" in str(caught.value)


def test_normalize_functions():
    assert normalize_filename("AGENTS.md") == "AGENTS.md"
    assert normalize_origin("foreign") == "foreign"
    assert normalize_layer("repo") == "repo"
    with pytest.raises(ValueError):
        normalize_filename("README.md")
    with pytest.raises(ValueError):
        normalize_origin("theirs")
    with pytest.raises(ValueError):
        normalize_layer("attic")


def test_row_is_derived_and_judged():
    entry = _entry()
    row = build_row(entry)
    assert row.rank == 24
    assert row.file_id == "instr-test-claude"
    assert validate_row(row, entry) == row
    with pytest.raises(ValueError):
        build_row({"filename": "CLAUDE.md", "origin": "foreign",
                   "path": "docs/CLAUDE.md", "source": "docs directory",
                   "layer": "dir", "rank": 3,
                   "file_id": "instr-test-claude"})
    with pytest.raises(ValueError):
        validate_row(build_row({
            "filename": "AGENTS.md", "origin": "standard",
            "path": "AGENTS.md", "source": "workspace root",
            "layer": "repo", "rank": 11,
            "file_id": "instr-other"}), entry)


def test_derive_panel_orders_and_counts():
    book = build_book({
        "title": "A small turf",
        "entries": [
            {"filename": "CLAUDE.md", "origin": "foreign",
             "path": "CLAUDE.md", "source": "workspace root",
             "layer": "repo", "reason": "Foreign.", "file_id": "e-claude"},
            {"filename": "RULES.AI.md", "origin": "ours",
             "path": "RULES.AI.md", "source": "workspace root",
             "layer": "repo", "reason": "Ours.", "file_id": "e-rules"},
            {"filename": "AGENTS.md", "origin": "standard",
             "path": "sub/AGENTS.md", "source": "sub directory",
             "layer": "dir", "reason": "Standard.", "file_id": "e-agents"},
        ]})
    panel = derive_panel(book)
    assert [(r.file_id, r.rank) for r in panel.rows] == [
        ("e-rules", 10), ("e-claude", 14), ("e-agents", 21)]
    assert panel.total_files == 3
    assert [(c.origin, c.files) for c in panel.origin_counts] == [
        ("ours", 1), ("foreign", 1), ("standard", 1)]
    assert panel.account[0] == (
        "The panel holds 3 instruction file(s) in force: "
        "ours 1, foreign 1, standard 1.")
    assert panel.row_for("e-claude").filename == "CLAUDE.md"
    with pytest.raises(KeyError):
        panel.row_for("e-nope")
    with pytest.raises(ValueError):
        derive_panel([])


def test_panel_internal_inconsistency_refuses():
    row = build_row(_entry())
    with pytest.raises(ValueError):
        InstructionPanel(
            rows=[row], total_files=5,
            origin_counts=[InstructionOriginCount(
                origin="foreign", files=1)],
            account=["A lying total."])
    later = build_row(_entry(
        filename="RULES.AI.md", origin="ours", path="RULES.AI.md",
        source="workspace root", layer="repo", file_id="instr-earlier"))
    with pytest.raises(ValueError):
        InstructionPanel(
            rows=[row, later], total_files=2,
            origin_counts=[
                InstructionOriginCount(origin="foreign", files=1),
                InstructionOriginCount(origin="ours", files=1)],
            account=["Rows out of order."])


def test_validate_panel_judged_against_its_source():
    book = load_instruction_files()
    panel = derive_panel(book)
    smaller = build_book({
        "title": "A smaller turf",
        "entries": [
            {"filename": "RULES.AI.md", "origin": "ours",
             "path": "RULES.AI.md", "source": "workspace root",
             "layer": "repo", "reason": "Ours.", "file_id": "e-rules"}]})
    with pytest.raises(ValueError):
        validate_panel(panel, smaller)
    assert validate_panel(panel, book).rows == panel.rows


def test_book_validation_refusals():
    with pytest.raises(ValueError):
        build_book({"title": "Empty", "entries": []})
    with pytest.raises(ValueError):
        build_book({"title": "Twins", "entries": [
            {"filename": "RULES.AI.md", "origin": "ours",
             "path": "RULES.AI.md", "source": "workspace root",
             "layer": "repo", "reason": "One.", "file_id": "e-same"},
            {"filename": "AGENTS.md", "origin": "standard",
             "path": "AGENTS.md", "source": "workspace root",
             "layer": "repo", "reason": "Two.", "file_id": "e-same"}]})
    with pytest.raises(ValueError):
        build_book({"title": "Same file twice", "entries": [
            {"filename": "RULES.AI.md", "origin": "ours",
             "path": "RULES.AI.md", "source": "workspace root",
             "layer": "repo", "reason": "One.", "file_id": "e-one"},
            {"filename": "RULES.AI.md", "origin": "ours",
             "path": "RULES.AI.md", "source": "workspace root",
             "layer": "repo", "reason": "Two.", "file_id": "e-two"}]})
    with pytest.raises(ValueError):
        validate_book({"title": "No entries at all"})


def test_load_instruction_files_file_roundtrip(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "instruction_files.yaml").read_text(encoding="utf-8")
    path = tmp_path / "instruction_files.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_instruction_files_file(path)
    assert book.title == load_instruction_files().title
    assert book.entry_ids() == load_instruction_files().entry_ids()
    bad = tmp_path / "bad.yaml"
    bad.write_text("schema: mythic.other/9\nentries: []\n",
                   encoding="utf-8")
    with pytest.raises((ValueError, ValidationError)):
        load_instruction_files_file(bad)


def test_registry_holds_entries_one_by_one():
    registry = InstructionFilesRegistry()
    first = registry.register_entry({
        "filename": "RULES.AI.md", "origin": "ours",
        "path": "RULES.AI.md", "source": "workspace root",
        "layer": "repo", "reason": "Ours."})
    second = registry.register_entry(_entry())
    assert first.file_id == "instruction-1"
    assert second.file_id == "instr-test-claude"
    assert [e.file_id for e in registry.list_entries()] == [
        "instruction-1", "instr-test-claude"]
    with pytest.raises(ValueError):
        registry.register_entry(_entry())
    with pytest.raises(ValueError):
        registry.register_entry({
            "filename": "CLAUDE.md", "origin": "foreign",
            "path": "docs/CLAUDE.md", "source": "docs directory",
            "layer": "dir", "reason": "The same file again.",
            "file_id": "instr-other-id"})
    assert registry.get_entry("instruction-1").filename == "RULES.AI.md"
    with pytest.raises(KeyError):
        registry.get_entry("instruction-99")


def test_registry_book_title_and_panel():
    registry = InstructionFilesRegistry()
    registry.register_book(load_instruction_files())
    assert registry.book().title == (
        "Instruction files at the M-148 slice boundary")
    assert registry.panel().total_files == 6
    other = build_book({
        "title": "Another turf",
        "entries": [
            {"filename": "AGENTS.md", "origin": "standard",
             "path": "AGENTS.md", "source": "workspace root",
             "layer": "repo", "reason": "Standard.",
             "file_id": "e-fresh"}]})
    with pytest.raises(ValueError):
        registry.register_book(other)
    fresh = InstructionFilesRegistry()
    with pytest.raises(ValueError):
        fresh.book()


def test_records_and_plain_words():
    book = load_instruction_files()
    entry = book.entry_for("instr-rules-root")
    record = entry_record(entry)
    assert record["type"] == "instruction_files_entry"
    assert record["news"] is True
    assert record["file_id"] == "instr-rules-root"
    assert record["rank"] == 10
    assert "RULES.AI.md (ours)" in record["headline"]
    panel_rec = panel_record(derive_panel(book))
    assert panel_rec["type"] == "instruction_files_panel"
    assert panel_rec["total_files"] == 6
    book_rec = book_record(book)
    assert book_rec["type"] == "instruction_files_book"
    assert book_rec["entry_count"] == 6
    assert book_rec["panel_count"] == 1
    assert plain_words(entry) == (
        "RULES.AI.md - ours, repo layer, rank 10, at RULES.AI.md "
        "from workspace root: Our own house rules for this repo, "
        "written by us for our own turf; inside the repo layer "
        "they outrank every guest file standing beside them.")
    told = panel_plain_words(book)
    assert "rank 10: RULES.AI.md (ours)" in told
    assert "The panel holds 6 instruction file(s)" in told


def test_formatters_and_screen():
    book = load_instruction_files()
    entry = book.entry_for("instr-agents-root")
    assert format_entry(entry) == (
        "instr-agents-root: AGENTS.md - standard, repo layer, "
        "rank 11 (AGENTS.md from workspace root)")
    whole = format_entries(book)
    assert whole.count("\n") == 5
    foreign = format_entries(book, "foreign")
    assert "instr-claude-root" in foreign
    assert "instr-rules-root" not in foreign
    panel_text = format_panel(book)
    assert panel_text.startswith(
        "Panel in Instruction files at the M-148 slice boundary:")
    assert "instr-cursor-package: rank 26" in panel_text
    screen = format_instruction_files_screen()
    assert screen.startswith("Instruction files unified (M-149) - ")
    assert "panel-m148-boundary" not in screen
    assert USAGE in screen


def test_parse_instruction_files_args_grammar():
    assert parse_instruction_files_args("") == ("show", None)
    assert parse_instruction_files_args("show") == ("show", None)
    assert parse_instruction_files_args("list") == ("show", None)
    assert parse_instruction_files_args("panel") == ("panel", None)
    assert parse_instruction_files_args(
        "entry instr-rules-root") == ("entry", "instr-rules-root")
    assert parse_instruction_files_args(
        "origin foreign") == ("origin", "foreign")
    assert parse_instruction_files_args(
        "layer dir") == ("layer", "dir")
    for bad in ("dance party", "entry", "origin theirs",
                "layer attic", "panel now", "entry a b"):
        with pytest.raises(ValueError) as caught:
            parse_instruction_files_args(bad)
        assert str(caught.value) == USAGE
    with pytest.raises(ValueError):
        parse_instruction_files_args(42)


def _write_workspace(tmp_path):
    (tmp_path / "RULES.AI.md").write_text(
        "Style: ours, always.\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(
        "Be kind to agents.\n", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "CLAUDE.md").write_text(
        "Foreign words stay foreign.\n", encoding="utf-8")
    return tmp_path


def _snapshot_bytes(root):
    return {str(p.relative_to(root)): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}


def test_scan_workspace_reads_the_elder_road(tmp_path):
    _write_workspace(tmp_path)
    entries = scan_workspace(tmp_path)
    by_id = {e.file_id: e for e in entries}
    assert set(by_id) == {
        "scan-rules-ai-md", "scan-agents-md", "scan-sub-claude-md"}
    # The elder resolver alone would never have
    # found RULES.AI.md: the canon's set finds it.
    assert by_id["scan-rules-ai-md"].origin == "ours"
    assert by_id["scan-rules-ai-md"].rank == 10
    assert by_id["scan-agents-md"].origin == "standard"
    assert by_id["scan-sub-claude-md"].origin == "foreign"
    assert by_id["scan-sub-claude-md"].layer == "dir"
    assert by_id["scan-sub-claude-md"].path == "sub/CLAUDE.md"
    panel = derive_panel(entries)
    assert [r.filename for r in panel.rows] == [
        "RULES.AI.md", "AGENTS.md", "CLAUDE.md"]


def test_honest_boundary_scan_mutates_nothing(tmp_path):
    _write_workspace(tmp_path)
    before = _snapshot_bytes(tmp_path)
    entries = scan_workspace(tmp_path)
    derive_panel(entries)
    assert _snapshot_bytes(tmp_path) == before
    # An entry holds no file content: a foreign
    # file's words stand nowhere in its records.
    blob = repr([e.to_record() for e in entries])
    assert "Foreign words stay foreign" not in blob
    assert "Be kind to agents" not in blob
    for entry in entries:
        assert not hasattr(entry, "content")


def test_honest_boundary_module_imports_no_live_roads():
    source = (ROOT / "mythic_agent" / "core"
              / "instruction_files.py").read_text(encoding="utf-8")
    for forbidden in ("from ..agents", "from ..ui",
                      "from ..terminal", "import requests",
                      "urlopen"):
        assert forbidden not in source
    # The one elder road it does compose is the
    # shipped instruction resolver, by import.
    assert "from ..context.instructions import" in source


# -- agent layer -----------------------------------------------------------
#
# M-149 agent layer: the agent holds an
# InstructionFilesRegistry for the session (session
# state only, no new setting), entries are held by
# being registered - published as their entry_record
# session news with the derived panel_record,
# through the checkpoint road, deduped per shape -
# the report road renders the held book (or the
# shipped example when unheld) through the pure
# formatters, and the /instructionfiles surface
# rides both roads on the pure parser + formatters.
# Status, get, origin, layer and panel reads
# register and publish nothing, answer from the
# held registry first and from the shipped example
# only while nothing is held - a held session never
# falls back to the example. The panel derives at
# call time from the held entries, never held. This
# layer writes, renames and applies no file, and
# there is no Part VIII board yet, so the screen is
# where the account is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _files_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_files_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "instruction_files.yaml").read_text(encoding="utf-8")
    path = tmp_path / "instruction_files.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestInstructionFilesAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.instruction_files_status()
        assert status["entries"] == []
        assert status["book"] is None
        assert status["instruction_files"]["title"] == (
            "Instruction files at the M-148 slice boundary")
        assert len(status["instruction_files"]["entries"]) == 6
        assert status["panel"]["total_files"] == 6
        assert status["book_record"]["entry_count"] == 6
        assert "Instruction files unified (M-149)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._instruction_files_registry()
        assert agent._instruction_files_registry() is first
        assert agent._instruction_files_store is first

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.instruction_files_status()
        agent.get_instruction_file("instr-rules-root")
        agent.instruction_files_for_origin("foreign")
        agent.instruction_files_for_layer("dir")
        agent.instruction_files_panel()
        agent.report_instruction_files()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("instruction_files")] == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_instruction_file("instr-nope")

    def test_status_after_register_shows_the_held_pieces(self, agent):
        agent.register_instruction_file(_entry())
        status = agent.instruction_files_status()
        assert [e["file_id"] for e in status["entries"]] == [
            "instr-test-claude"]
        assert status["book"]["title"] == "Session instruction files"
        assert status["panel"]["total_files"] == 1
        assert status["panel"]["rows"][0]["rank"] == 24

    def test_held_session_never_falls_back_to_the_example(self, agent):
        agent.register_instruction_file(_entry())
        with pytest.raises(KeyError):
            agent.get_instruction_file("instr-rules-root")
        assert agent.instruction_files_for_origin("standard") == ()
        assert [e.file_id for e in
                agent.instruction_files_for_origin("foreign")] == [
                    "instr-test-claude"]
        assert agent.instruction_files_book().title == (
            "Session instruction files")


class TestInstructionFilesAgentHolding:
    def test_register_entry_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_instruction_file(_entry())
        assert outcome["entry"]["file_id"] == "instr-test-claude"
        assert outcome["record"]["type"] == "instruction_files_entry"
        assert outcome["panel_record"]["type"] == (
            "instruction_files_panel")
        events = _files_events(
            store, session_id, "instruction_files_entry")
        assert len(events) == 1
        assert events[0]["file_id"] == "instr-test-claude"
        panels = _files_events(
            store, session_id, "instruction_files_panel")
        assert len(panels) == 1
        assert panels[0]["total_files"] == 1
        agent._publish_instruction_files_record(outcome["record"])
        agent._publish_instruction_files_record(outcome["panel_record"])
        assert len(_files_events(
            store, session_id, "instruction_files_entry")) == 1
        assert len(_files_events(
            store, session_id, "instruction_files_panel")) == 1
        from mythic_agent.core.context_budget import (
            book_record as _budget_book_record, load_context_budget)
        agent._publish_instruction_files_record(
            {"type": "mentions_mention", "mention_id": "mention-x"})
        agent._publish_instruction_files_record(
            _budget_book_record(load_context_budget()))
        agent._publish_instruction_files_record(
            book_record(load_instruction_files()))
        for kind in ("mentions_mention", "context_budget_book",
                     "instruction_files_book"):
            assert _files_events(store, session_id, kind) == []
        agent.close()

    def test_register_entry_without_id_gets_an_instruction_id(
            self, agent):
        outcome = agent.register_instruction_file({
            "filename": "RULES.AI.md", "origin": "ours",
            "path": "RULES.AI.md", "source": "workspace root",
            "layer": "repo", "reason": "Ours."})
        assert outcome["entry"]["file_id"] == "instruction-1"

    def test_duplicate_entry_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_instruction_file(_entry())
        with pytest.raises(ValueError):
            agent.register_instruction_file(_entry())
        assert len(_files_events(
            store, session_id, "instruction_files_entry")) == 1
        agent.close()

    def test_scan_and_register_holds_the_workspace(
            self, agent, tmp_path):
        workspace = tmp_path / "ws"
        workspace.mkdir()
        _write_workspace(workspace)
        before = _snapshot_bytes(workspace)
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.scan_and_register_instruction_files(workspace)
        assert outcome["count"] == 3
        assert [e["file_id"] for e in outcome["entries"]] == [
            "scan-agents-md", "scan-rules-ai-md", "scan-sub-claude-md"]
        assert len(_files_events(
            store, session_id, "instruction_files_entry")) == 3
        assert agent.instruction_files_panel().total_files == 3
        # Scanning and holding changed no file.
        assert _snapshot_bytes(workspace) == before
        agent.close()

    def test_register_book_holds_and_publishes_in_order(self, agent):
        book = build_book({
            "title": "A held turf",
            "entries": [
                {"filename": "RULES.AI.md", "origin": "ours",
                 "path": "RULES.AI.md", "source": "workspace root",
                 "layer": "repo", "reason": "Ours.",
                 "file_id": "held-rules"},
                {"filename": "CLAUDE.md", "origin": "foreign",
                 "path": "CLAUDE.md", "source": "workspace root",
                 "layer": "repo", "reason": "Foreign.",
                 "file_id": "held-claude"}]})
        outcome = agent.register_instruction_files_book(book)
        assert outcome["count"] == 2
        assert [r["file_id"] for r in outcome["records"]] == [
            "held-rules", "held-claude"]
        assert agent.instruction_files_book().title == "A held turf"

    def test_register_book_twice_refuses(self, agent):
        agent.register_instruction_files_book(load_instruction_files())
        with pytest.raises(ValueError):
            agent.register_instruction_files_book(
                load_instruction_files())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_instruction_files_book()
        assert outcome["count"] == 6
        assert outcome["book"]["title"] == (
            "Instruction files at the M-148 slice boundary")
        assert len(_files_events(
            store, session_id, "instruction_files_entry")) == 6
        assert agent.instruction_files_book().panels[0].panel_id == (
            "panel-m148-boundary")
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_instruction_files_book()
        with pytest.raises(ValueError):
            agent.record_instruction_files_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_files_book(tmp_path)
        book = load_instruction_files_file(path)
        outcome = agent.record_instruction_files_book(book)
        assert outcome["count"] == 6
        assert agent.get_instruction_file(
            "instr-cursor-package").origin == "foreign"

    def test_one_by_one_holdings_stand_under_a_session_book(
            self, agent):
        agent.register_instruction_file(_entry())
        agent.register_instruction_file({
            "filename": "RULES.AI.md", "origin": "ours",
            "path": "RULES.AI.md", "source": "workspace root",
            "layer": "repo", "reason": "Ours.",
            "file_id": "instr-test-rules"})
        book = agent.instruction_files_book()
        assert book.title == "Session instruction files"
        assert [e.file_id for e in book.entries] == [
            "instr-test-claude", "instr-test-rules"]
        panel = agent.instruction_files_panel()
        assert [r.file_id for r in panel.rows] == [
            "instr-test-rules", "instr-test-claude"]

    def test_report_renders_the_example_when_unheld(self, agent):
        report = agent.report_instruction_files()
        assert report["book"]["entry_count"] == 6
        assert "instr-rules-root" in report["entries_text"]
        assert "Panel in Instruction files" in report["panel_text"]

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_instruction_file(_entry())
        report = agent.report_instruction_files()
        assert report["book"]["title"] == "Session instruction files"
        assert "instr-rules-root" not in report["entries_text"]
        assert "instr-test-claude" in report["entries_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_instruction_files()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("instruction_files")] == []
        agent.close()

    def test_no_live_apply_rewrite_or_persist_road(self, agent):
        # This layer holds the account as data: it
        # writes no file, rewrites no foreign file,
        # applies no instruction itself beyond what
        # the elder road already does, persists
        # nothing - and there is no Part VIII board
        # yet. Holding a book changes no live context
        # assembly: a ContextBuilder's built messages
        # are the same before and after a book is held.
        assert not hasattr(agent, "apply_instruction_files")
        assert not hasattr(agent, "rewrite_instruction_file")
        assert not hasattr(agent, "rename_instruction_file")
        assert not hasattr(agent, "persist_instruction_files")
        assert not hasattr(agent, "instruction_files_board")
        from mythic_agent.agents.context import ContextBuilder
        builder = ContextBuilder(max_tokens=4000)
        builder.add_system("You are the coder.")
        builder.add_turn("user", "Build the slice.")
        before = builder.build()
        agent.record_instruction_files_book()
        assert builder.build() == before


class TestInstructionFilesTerminalSurface:
    def test_show_entry_origin_layer_and_panel(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/instructionfiles")
        assert "Instruction files unified (M-149)" in text
        _, _, text = _slash(
            agent, "/instructionfiles entry instr-rules-root")
        assert "instr-rules-root: RULES.AI.md" in text
        _, _, text = _slash(agent, "/instructionfiles origin foreign")
        assert "instr-claude-root" in text
        assert "instr-rules-root" not in text
        _, _, text = _slash(agent, "/instructionfiles layer dir")
        assert "instr-mythic-package" in text
        assert "instr-rules-root" not in text
        _, _, text = _slash(agent, "/instructionfiles panel")
        assert "Panel in Instruction files" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/instructionfiles [show|entry <file-id>|"
                "origin <origin>|layer <layer>|panel]") in text
        _, _, text = _slash(agent, "/instructionfiles dance party")
        assert text == USAGE
        _, _, text = _slash(
            agent, "/instructionfiles entry instr-nope")
        assert "no entry in the book" in text


@pytest.fixture()
def files_handler(agent, monkeypatch):
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


def _files_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestInstructionFilesCommand:
    def test_show_is_default(self, files_handler, agent):
        files_handler._handle_instruction_files("")
        assert "Instruction files unified (M-149)" in (
            _files_published_text(files_handler))

    def test_entry_origin_layer_and_panel(self, files_handler, agent):
        files_handler._handle_instruction_files("entry instr-rules-root")
        assert "RULES.AI.md" in _files_published_text(files_handler)
        files_handler._handle_instruction_files("origin foreign")
        text = _files_published_text(files_handler)
        assert "instr-claude-root" in text
        files_handler._handle_instruction_files("layer dir")
        assert "instr-mythic-package" in _files_published_text(
            files_handler)
        files_handler._handle_instruction_files("panel")
        assert "Panel in Instruction files" in _files_published_text(
            files_handler)

    def test_bad_grammar_is_published(self, files_handler, agent):
        files_handler._handle_instruction_files("dance party")
        assert USAGE in _files_published_text(files_handler)


class TestChatScreenRoutingInstructionFiles:
    def test_instruction_files_routes_as_system_command(
            self, monkeypatch):
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
            "/instructionfiles entry instr-rules-root", _FakeLog())
        assert calls == [
            ("/instructionfiles", "entry instr-rules-root")]
