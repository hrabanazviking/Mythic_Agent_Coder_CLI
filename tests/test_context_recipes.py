"""M-158 Context recipes - pure-layer tests.

TIER: integration

The pure layer is the saved bundle itself, held as
data: one named bundle ("the auth stack", "the Mojo
build") carried with its provenance whole (the
session it was saved in, the day, and where it was
read from), whose pieces are the shipped memory
holdings' own pieces (M-150, M-153, M-154, M-155,
M-156, M-133) read onto this layer by import and
judged by each holding's own validation, a recipe
panel derived from the whole book in settled order,
the shipped example book held in a data file, and a
loader that reads a book from any file. No name in a
book names two recipes. Nothing here calls a model,
assembles any live context, edits any code or writes
any project's files: holding and summoning the
bundle by name is the whole road.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.cross_project_memory import (
    load_cross_project_memory,
)
from mythic_agent.core.decision_records import load_decision_records
from mythic_agent.core.project_memory_map import (
    build_entry as build_map_entry,
    load_project_memory_map,
)
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.self_improving_ledger import (
    load_self_improving_ledger,
)
from mythic_agent.core.session_memory import load_session_memory
from mythic_agent.core.validation import ValidationError
from mythic_agent.core.context_recipes import (
    CONTEXT_RECIPES_RESOURCE,
    CONTEXT_RECIPES_SCHEMA,
    CONTEXT_RECIPES_SLICE,
    PLAIN_EXPLANATION,
    RECIPE_ITEM_KINDS,
    USAGE,
    ContextRecipe,
    ContextRecipeBook,
    ContextRecipePanel,
    ContextRecipeRegistry,
    RecipeItem,
    RecipeKindCount,
    RecipePanelRow,
    book_record,
    build_book,
    build_item,
    build_panel,
    build_recipe,
    build_row,
    derive_panel,
    format_context_recipes_screen,
    format_panel,
    format_recipe,
    format_recipes,
    format_summon,
    inspect_piece,
    item_from_cross_project,
    item_from_decision_record,
    item_from_ledger_candidate,
    item_from_memory_map,
    item_from_session_memory,
    items_from_memory_map,
    items_from_session_memory,
    load_context_recipes,
    load_context_recipes_file,
    normalize_item_kind,
    panel_plain_words,
    panel_record,
    parse_recipe_args,
    plain_words,
    recipe_record,
    validate_book,
    validate_item,
    validate_panel,
    validate_recipe,
    validate_row,
)

ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_TITLE = "Context recipes at the M-157 slice boundary"

WHY = "It belongs in the test bundle."


def _item(**overrides):
    fields = {"kind": "session-memory", "ref": "note-test", "why": WHY}
    fields.update(overrides)
    return build_item(fields)


def _recipe(**overrides):
    fields = {
        "recipe_id": "recipe-test",
        "name": "the test bundle",
        "purpose": "Everything a session needs for the test work.",
        "items": [_item()],
        "session_ref": "session-test",
        "created_on": "2026-11-08",
        "source": "test source",
    }
    fields.update(overrides)
    return build_recipe(fields)


def _stored_recipe(recipe):
    stored = recipe.to_record()
    stored.pop("type")
    stored.pop("slice")
    return stored


def _stored_panel(panel):
    stored = panel.to_record()
    stored.pop("type")
    stored.pop("slice")
    for row in stored["rows"]:
        row.pop("type")
        row.pop("slice")
    return stored


def _book(recipes=None, **overrides):
    fields = {
        "title": "A test recipe book",
        "recipes": [_stored_recipe(item) for item in (
            recipes if recipes is not None else [_recipe()])],
    }
    fields.update(overrides)
    return build_book(fields)


def _shipped_raw():
    path = ROOT / "mythic_agent" / "data" / "context_recipes.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_constants_and_usage():
    assert CONTEXT_RECIPES_SLICE == "M-158"
    assert CONTEXT_RECIPES_SCHEMA == "mythic.context_recipes/1"
    assert CONTEXT_RECIPES_RESOURCE == "context_recipes.yaml"
    assert RECIPE_ITEM_KINDS == (
        "session-memory", "cross-project", "ledger-candidate",
        "decision-record", "memory-map", "crew-memory")
    assert "summonable by name" in PLAIN_EXPLANATION
    assert "assembles no live context" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /recipes")
    assert "summon <recipe name>" in USAGE


def test_roadmap_boundary_is_derived_from_the_shipped_roadmap():
    road = load_roadmap()
    ids = [item.id for item in road.slices]
    assert "M-158" in ids
    mine = road.slices[ids.index("M-158")]
    assert mine.title == "Context recipes"
    assert mine.part == 7
    assert "summonable by name" in mine.summary
    for earlier in road.slices[:ids.index("M-158")]:
        assert earlier.status == "done", earlier.id


def test_shipped_example_shape():
    book = load_context_recipes()
    assert isinstance(book, ContextRecipeBook)
    assert book.title == EXAMPLE_TITLE
    assert book.recipe_ids() == (
        "recipe-auth-stack", "recipe-mojo-build",
        "recipe-provider-ocean")
    assert book.total_recipes == 3
    first = book.recipes[0]
    assert first.name == "the auth stack"
    assert first.piece_count == 3
    assert first.session_ref == "session-auth-work"
    assert first.created_on == "2026-11-08"
    assert len(book.panels) == 1


def test_shipped_panel_is_pinned_and_derived():
    book = load_context_recipes()
    panel = book.panel_for("panel-m157-boundary")
    derived = derive_panel(book)
    assert panel.rows == derived.rows
    assert panel.account == derived.account
    assert [row.recipe_id for row in panel.rows] == [
        "recipe-auth-stack", "recipe-mojo-build",
        "recipe-provider-ocean"]
    assert panel.total_items == 3
    assert panel.total_pieces == 8


def test_normalizers_and_aliases():
    assert normalize_item_kind("Session") == "session-memory"
    assert normalize_item_kind("crossmemory") == "cross-project"
    assert normalize_item_kind("ledger") == "ledger-candidate"
    assert normalize_item_kind("DECISIONS") == "decision-record"
    assert normalize_item_kind("map") == "memory-map"
    assert normalize_item_kind("crew") == "crew-memory"
    with pytest.raises(ValueError):
        normalize_item_kind("vault")


def test_recipe_validation_and_alias_spellings():
    recipe = _recipe()
    assert isinstance(recipe, ContextRecipe)
    assert recipe.piece_count == 1
    aliased = build_recipe({
        "title": "the aliased bundle", "why": "A purpose.",
        "pieces": [{"class": "map", "memory_ref": "entry-x",
                    "note": "It belongs."}],
        "session": "session-x", "day": "2026-11-08",
        "source": "the map"})
    assert aliased.name == "the aliased bundle"
    assert aliased.items[0].kind == "memory-map"
    assert aliased.items[0].ref == "entry-x"
    with pytest.raises(ValueError):
        build_recipe({"name": "the bare bundle"})
    with pytest.raises(ValueError):
        _recipe(created_on="08/11/2026")
    with pytest.raises(ValueError):
        _recipe(created_on="2026-13-01")


def test_recipe_refuses_duplicate_piece_and_empty_bundle():
    with pytest.raises(ValueError, match="already named"):
        _recipe(items=[_item(), _item()])
    # The same piece may stand in many recipes: bundles overlap.
    book = _book([_recipe(), _recipe(
        recipe_id="recipe-other", name="the other bundle")])
    assert book.total_recipes == 2
    with pytest.raises(ValueError, match="at least one piece"):
        _recipe(items=[])
    fields = _stored_recipe(_recipe())
    fields["surprise"] = "x"
    with pytest.raises(ValueError, match="unknown recipe keys"):
        build_recipe(fields)
    fields = _stored_recipe(_recipe())
    fields["session"] = "session-test"
    fields["session_ref"] = "session-other"
    with pytest.raises(ValueError, match="two different"):
        build_recipe(fields)


def test_name_uniqueness_in_book_and_registry():
    # The honesty heart of the slice: one name summons
    # one bundle, never two - in any letter case.
    with pytest.raises(ValueError, match="one bundle, never two"):
        _book([_recipe(), _recipe(recipe_id="recipe-copy")])
    with pytest.raises(ValueError, match="one bundle, never two"):
        _book([_recipe(), _recipe(
            recipe_id="recipe-copy", name="THE TEST BUNDLE")])
    registry = ContextRecipeRegistry()
    registry.register_recipe(_recipe())
    with pytest.raises(ValueError, match="one bundle, never two"):
        registry.register_recipe(_recipe(recipe_id="recipe-copy"))
    assert registry.recipe_named("The Test Bundle").recipe_id == (
        "recipe-test")
    with pytest.raises(KeyError):
        registry.recipe_named("the missing bundle")


def test_composition_from_session_memory():
    book = load_session_memory()
    notes = [n for s in book.situations for n in s.memory if n.note_id]
    assert notes
    item = item_from_session_memory(notes[0], why=WHY)
    assert item.kind == "session-memory"
    assert item.ref == notes[0].note_id
    items = items_from_session_memory(book, why=WHY)
    assert len(items) == len(notes)
    assert {i.kind for i in items} == {"session-memory"}


def test_composition_from_cross_project_and_ledger():
    lessons = [item for item in load_cross_project_memory().lessons
               if item.lesson_id]
    assert lessons
    item = item_from_cross_project(lessons[0], why=WHY)
    assert item.kind == "cross-project"
    assert item.ref == lessons[0].lesson_id
    candidates = [c for c in load_self_improving_ledger().candidates
                  if c.candidate_id]
    assert candidates
    item = item_from_ledger_candidate(candidates[0], why=WHY)
    assert item.kind == "ledger-candidate"
    assert item.ref == candidates[0].candidate_id


def test_composition_from_decision_record():
    record = load_decision_records().record_for("record-httpx-client")
    item = item_from_decision_record(record, why=WHY)
    assert item.kind == "decision-record"
    assert item.ref == "record-httpx-client"
    recipe = _recipe(items=[item])
    assert recipe.items[0].ref == "record-httpx-client"


def test_composition_from_memory_map_and_inspection():
    shipped = load_project_memory_map()
    first = shipped.entries[0]
    item = item_from_memory_map(first, why=WHY)
    assert item.kind == "memory-map"
    assert item.ref == first.entry_id
    items = items_from_memory_map(shipped, why=WHY)
    assert len(items) == len(shipped.entries)
    seen = inspect_piece(first)
    assert seen == {"kind": "memory-map", "ref": first.entry_id}
    seen = inspect_piece(load_decision_records().records[0])
    assert seen["kind"] == "decision-record"
    with pytest.raises(ValueError):
        inspect_piece(object())
    bare = build_map_entry({
        "section": "gotcha", "title": "A bare fact",
        "detail": "A fact with no standing reference.",
        "source": "test", "ref": "nowhere"})
    with pytest.raises(ValueError):
        item_from_memory_map(bare, why=WHY)


def test_composition_requires_the_reason():
    note_book = load_session_memory()
    note = [n for s in note_book.situations for n in s.memory][0]
    with pytest.raises(ValueError, match="reason"):
        item_from_session_memory(note, why=None)
    with pytest.raises(ValueError, match="missing its"):
        validate_item({"kind": "map", "ref": "entry-x"})
    direct = validate_item({"kind": "map", "ref": "entry-x", "why": WHY})
    assert direct == _item(kind="memory-map", ref="entry-x")


def test_book_validation_refusals():
    with pytest.raises(ValueError):
        _book([_recipe(), _recipe(name="the second bundle")])
    raw = _shipped_raw()
    raw["schema"] = "mythic.other/1"
    with pytest.raises(ValidationError):
        validate_book(raw)
    raw = _shipped_raw()
    raw["panels"][0]["total_pieces"] = 9
    with pytest.raises(ValidationError):
        validate_book(raw)
    raw = _shipped_raw()
    raw["recipes"][1]["name"] = "the auth stack"
    with pytest.raises(ValidationError):
        validate_book(raw)
    raw = _shipped_raw()
    raw["guide"]["title"] = "A different title"
    with pytest.raises(ValidationError):
        validate_book(raw, require_example=True)


def test_load_context_recipes_file_roundtrip(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "context_recipes.yaml").read_text(encoding="utf-8")
    path = tmp_path / "context_recipes.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_context_recipes_file(path)
    assert book.title == EXAMPLE_TITLE
    assert book.recipe_ids()[0] == "recipe-auth-stack"
    with pytest.raises(FileNotFoundError):
        load_context_recipes_file(tmp_path / "nope.yaml")


def test_registry_holds_recipes_one_by_one():
    registry = ContextRecipeRegistry()
    held = registry.register_recipe({
        "name": "the held bundle", "purpose": "A purpose.",
        "items": [{"kind": "map", "ref": "entry-x", "why": WHY}],
        "session_ref": "session-x", "created_on": "2026-11-08",
        "source": "the map"})
    assert held.recipe_id == "recipe-1"
    second = registry.register_recipe(_recipe())
    assert second.recipe_id == "recipe-test"
    assert registry.latest_recipe().recipe_id == "recipe-test"
    assert [r.recipe_id for r in registry.list_recipes()] == [
        "recipe-1", "recipe-test"]
    with pytest.raises(ValueError):
        registry.register_recipe(_recipe())
    with pytest.raises(KeyError):
        registry.get_recipe("recipe-nope")
    named = ContextRecipeRegistry()
    named.register_book(_book())
    assert named.book().title == "A test recipe book"
    assert named.panel().total_items == 1
    assert named.recipe_named("the test bundle").recipe_id == (
        "recipe-test")
    with pytest.raises(ValueError):
        named.register_book(_book(title="Another title"))


def test_panel_row_judged_against_its_recipe():
    recipe = _recipe()
    panel = derive_panel(_book([recipe]))
    row = panel.rows[0]
    assert isinstance(row, RecipePanelRow)
    assert validate_row(row, recipe) == row
    bad = build_row({
        "recipe_id": "recipe-test", "name": "the test bundle",
        "purpose": "A different purpose.",
        "session_ref": "session-test", "piece_count": 1,
        "kinds": ["session-memory"]})
    with pytest.raises(ValueError, match="disagrees"):
        validate_row(bad, recipe)
    counts = panel.kind_counts
    assert counts == (RecipeKindCount(kind="session-memory", items=1),)


def test_panel_validation_refusals():
    book = _book()
    panel = derive_panel(book)
    stored = _stored_panel(panel)
    assert validate_panel(stored, book) == panel
    bad = _stored_panel(panel)
    bad["total_items"] = 9
    with pytest.raises(ValueError):
        validate_panel(bad)
    bad = _stored_panel(panel)
    bad["account"] = ["A different account."]
    with pytest.raises(ValueError, match="disagrees"):
        validate_panel(bad, book)
    built = build_panel(_stored_panel(panel))
    assert built == panel


def test_records_and_plain_words():
    recipe = _recipe()
    record = recipe_record(recipe)
    assert record["type"] == "context_recipe"
    assert record["news"] is True
    assert "the test bundle" in record["headline"]
    assert set(record) == {
        "type", "slice", "recipe_id", "name", "purpose", "items",
        "session_ref", "created_on", "source", "news", "headline"}
    words = plain_words(recipe)
    assert "the test bundle" in words and "session-memory" in words
    book = load_context_recipes()
    panel_rec = panel_record(derive_panel(book), book)
    assert panel_rec["headline"].startswith("Recipe panel: 3 recipes")
    book_rec = book_record(book)
    assert book_rec["recipe_count"] == 3
    told = panel_plain_words(book)
    assert "recipe-mojo-build" in told
    assert "never ambiguous" in told


def test_formatters_and_screen():
    book = load_context_recipes()
    text = format_recipe(book.recipes[0])
    assert "recipe-auth-stack" in text
    assert "record-httpx-client" in text
    assert "the auth stack" in format_recipes(book)
    summoned = format_summon(book.recipe_named("the Mojo build"))
    assert "Summoned" in summoned
    assert "map-tests" in summoned
    assert "assembles no live context" in summoned
    panel_text = format_panel(book)
    assert "Recipe panel in Context recipes" in panel_text
    screen = format_context_recipes_screen()
    assert "Context Recipes (M-158)" in screen
    assert USAGE in screen


def test_parse_recipe_args_grammar():
    assert parse_recipe_args("") == ("show", None)
    assert parse_recipe_args("show") == ("show", None)
    assert parse_recipe_args("list") == ("show", None)
    assert parse_recipe_args("recipe recipe-test") == (
        "recipe", "recipe-test")
    assert parse_recipe_args("summon the auth stack") == (
        "summon", "the auth stack")
    assert parse_recipe_args("summon the Mojo build") == (
        "summon", "the Mojo build")
    assert parse_recipe_args("panel") == ("panel", None)
    for bad in ("dance", "recipe", "recipe a b", "summon", 5):
        with pytest.raises(ValueError):
            parse_recipe_args(bad)


def test_honest_boundary_module_imports_no_live_roads():
    source = (ROOT / "mythic_agent" / "core"
              / "context_recipes.py").read_text(encoding="utf-8")
    assert "from .session_memory import" in source
    assert "from .cross_project_memory import" in source
    assert "from .self_improving_ledger import" in source
    assert "from .decision_records import" in source
    assert "from .project_memory_map import" in source
    assert "from ..agents" not in source
    assert "from ..ui" not in source
    assert "from ..terminal" not in source
    assert "import agents" not in source


def test_composition_from_crew_memory_and_direct_validate():
    from mythic_agent.core.crew_memory import (
        build_entry as build_crew_entry,
    )
    crew_entry = build_crew_entry({
        "entry_id": "crew-note-1", "member": "cartographer",
        "title": "A crew fact held in a notebook",
        "fact": "The crew fact's own words.",
        "tags": ["roads"], "provenance": "test source"})
    seen = inspect_piece(crew_entry)
    assert seen == {"kind": "crew-memory", "ref": "crew-note-1"}
    direct = validate_recipe(_stored_recipe(_recipe()))
    assert direct == _recipe()
    assert isinstance(validate_item(_item()), RecipeItem)


def test_registry_constructor_and_titleless_book_refusal():
    registry = ContextRecipeRegistry(load_context_recipes())
    assert registry.book().title == EXAMPLE_TITLE
    assert registry.panel().total_pieces == 8
    bare = ContextRecipeRegistry()
    bare.register_recipe(_recipe())
    with pytest.raises(ValueError, match="no recipe book is held"):
        bare.book()
    # The panel still derives from what stands held,
    # title or no title: derivation needs no book.
    assert bare.panel().total_items == 1


def test_summon_by_name_from_the_book():
    book = load_context_recipes()
    recipe = book.recipe_named("THE AUTH STACK")
    assert recipe.recipe_id == "recipe-auth-stack"
    assert isinstance(book.recipe_for("recipe-mojo-build"),
                      ContextRecipe)
    assert isinstance(derive_panel(book), ContextRecipePanel)
    with pytest.raises(KeyError):
        book.recipe_named("the missing bundle")
    with pytest.raises(KeyError):
        book.recipe_for("recipe-nope")


# -- agent layer -----------------------------------------------------------
#
# M-158 agent layer: the agent holds a
# ContextRecipeRegistry for the session (session state
# only, no new setting), recipes are held by being
# registered - published as their recipe_record session
# news with the derived panel_record, through the
# checkpoint road, deduped per shape - the report road
# renders the held book (or the shipped example when
# unheld) through the pure formatters, a bundle road
# reads the session's carried memory onto items and
# holds them as one recipe (mutating no live memory),
# a summon road reads one recipe by name and publishes
# its news, and the /recipes surface rides both roads
# on the pure parser + formatters. Status, get, panel
# and report reads register and publish nothing, answer
# from the held registry first and from the shipped
# example only while nothing is held - a held session
# never falls back to the example. The panel derives at
# call time from the whole book, never held. This layer
# calls no model, assembles no live context and
# persists nothing beyond the session journal news, and
# there is no Part VIII board yet, so the screen is
# where the book is visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _recipe_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_recipe_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "context_recipes.yaml").read_text(encoding="utf-8")
    path = tmp_path / "context_recipes.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestContextRecipesAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.context_recipes_status()
        assert status["recipes"] == []
        assert status["book"] is None
        assert status["bundling"]["title"] == EXAMPLE_TITLE
        assert len(status["bundling"]["recipes"]) == 3
        assert status["panel"]["total_items"] == 3
        assert status["panel"]["total_pieces"] == 8
        assert status["panels"][0]["panel_id"] == "panel-m157-boundary"
        assert status["book_record"]["recipe_count"] == 3
        assert "Context Recipes (M-158)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        first = agent._context_recipes_registry()
        assert agent._context_recipes_registry() is first
        assert agent._context_recipes_store is first

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.context_recipes_status()
        agent.get_context_recipe("recipe-auth-stack")
        agent.context_recipes_panel()
        agent.report_context_recipes()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("context_recipe")] == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_context_recipe("recipe-nope")
        with pytest.raises(KeyError):
            agent.summon_context_recipe("the missing bundle")

    def test_status_after_register_shows_the_held_pieces(
            self, agent):
        agent.register_context_recipe(_recipe())
        status = agent.context_recipes_status()
        assert [item["recipe_id"] for item in status["recipes"]] == [
            "recipe-test"]
        assert status["book"]["title"] == "Context recipes"

    def test_held_session_never_falls_back_to_the_example(
            self, agent):
        agent.register_context_recipe(_recipe())
        with pytest.raises(KeyError):
            agent.get_context_recipe("recipe-auth-stack")
        recipe = agent.get_context_recipe("recipe-test")
        assert recipe.name == "the test bundle"
        assert agent.context_recipes_book().title == (
            "Context recipes")


class TestContextRecipesAgentHolding:
    def test_register_recipe_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_context_recipe(_recipe())
        assert outcome["recipe"]["recipe_id"] == "recipe-test"
        assert outcome["recipe_news"]["type"] == "context_recipe"
        events = _recipe_events(store, session_id, "context_recipe")
        assert len(events) == 1
        assert events[0]["recipe_id"] == "recipe-test"
        agent._publish_context_recipe_record(outcome["recipe_news"])
        assert len(_recipe_events(
            store, session_id, "context_recipe")) == 1
        agent._publish_context_recipe_record(
            {"type": "mentions_mention", "mention_id": "mention-x"})
        agent._publish_context_recipe_record(
            book_record(load_context_recipes()))
        for kind in ("mentions_mention", "context_recipe_book"):
            assert _recipe_events(store, session_id, kind) == []
        agent.close()

    def test_duplicate_recipe_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_context_recipe(_recipe())
        with pytest.raises(ValueError):
            agent.register_context_recipe(_recipe())
        with pytest.raises(ValueError):
            agent.register_context_recipe(
                _recipe(recipe_id="recipe-copy"))
        assert len(_recipe_events(
            store, session_id, "context_recipe")) == 1
        agent.close()

    def test_bundle_from_session_memory_carries_ids_only(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        memory_book = load_session_memory()
        notes = [n for s in memory_book.situations for n in s.memory
                 if n.note_id]
        expected = len(notes)
        outcome = agent.bundle_context_recipe_from_session_memory(
            name="the carried bundle", purpose="A test bundle.",
            why="It was carried in the session.",
            session_ref="session-test", created_on="2026-11-08")
        assert outcome["count"] == expected
        events = _recipe_events(store, session_id, "context_recipe")
        assert len(events) == 1
        blob = str(events) + str(outcome["recipe"])
        for note in notes:
            assert note.title not in blob
            assert note.detail not in blob
        # Bundling mutated no live memory: the session's
        # carried memory stands whole.
        assert agent.session_memory_book().situations == (
            memory_book.situations)
        assert agent.context_recipes_panel().total_items == 1
        assert agent.context_recipes_panel().total_pieces == expected
        with pytest.raises(ValueError):
            agent.bundle_context_recipe_from_session_memory(
                name="the carried bundle", purpose="Again.",
                why="Again.", session_ref="session-test",
                created_on="2026-11-08")
        agent.close()

    def test_summon_by_name_publishes_the_recipe_news(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.summon_context_recipe("the Mojo build")
        assert outcome["recipe"]["recipe_id"] == "recipe-mojo-build"
        assert "map-tests" in outcome["summon_text"]
        events = _recipe_events(store, session_id, "context_recipe")
        assert len(events) == 1
        assert events[0]["name"] == "the Mojo build"
        agent.summon_context_recipe("THE MOJO BUILD")
        assert len(_recipe_events(
            store, session_id, "context_recipe")) == 1
        agent.close()

    def test_register_book_holds_and_publishes_in_order(
            self, agent):
        book = _book()
        outcome = agent.register_context_recipe_book(book)
        assert outcome["count"] == 1
        assert [item["type"] for item in outcome["recipes_news"]] == [
            "context_recipe"]
        assert agent.context_recipes_book().title == (
            "A test recipe book")

    def test_register_book_twice_refuses(self, agent):
        agent.register_context_recipe_book(load_context_recipes())
        with pytest.raises(ValueError):
            agent.register_context_recipe_book(load_context_recipes())

    def test_record_book_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_context_recipe_book()
        assert outcome["count"] == 3
        assert outcome["book"]["title"] == EXAMPLE_TITLE
        assert len(_recipe_events(
            store, session_id, "context_recipe")) == 3
        assert agent.context_recipes_book().panels[0].panel_id == (
            "panel-m157-boundary")
        agent.close()

    def test_record_same_book_twice_refuses(self, agent):
        agent.record_context_recipe_book()
        with pytest.raises(ValueError):
            agent.record_context_recipe_book()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_recipe_book(tmp_path)
        book = load_context_recipes_file(path)
        outcome = agent.record_context_recipe_book(book)
        assert outcome["count"] == 3
        assert agent.get_context_recipe(
            "recipe-auth-stack").name == "the auth stack"

    def test_report_renders_the_example_when_unheld(self, agent):
        report = agent.report_context_recipes()
        assert report["book"]["recipe_count"] == 3
        assert "recipe-auth-stack" in report["recipes_text"]
        assert "Recipe panel in Context recipes" in (
            report["panel_text"])

    def test_report_renders_the_held_book_only(self, agent):
        agent.register_context_recipe(_recipe())
        report = agent.report_context_recipes()
        assert report["book"]["title"] == "Context recipes"
        assert "recipe-auth-stack" not in report["recipes_text"]
        assert "recipe-test" in report["recipes_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_context_recipes()
        assert [e for e in store.export(session_id)["events"]
                if e["type"].startswith("context_recipe")] == []
        agent.close()

    def test_no_live_assemble_or_persist_road(
            self, agent, tmp_path):
        # This layer holds recipes as data: it calls no
        # model, assembles no live context, edits no
        # code, writes no project files and persists
        # nothing - and there is no Part VIII board yet.
        # Holding, recording, bundling or summoning
        # changes no workspace file and no live context.
        assert not hasattr(agent, "apply_context_recipes")
        assert not hasattr(agent, "assemble_context_recipes")
        assert not hasattr(agent, "persist_context_recipes")
        assert not hasattr(agent, "context_recipes_board")
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
        agent.register_context_recipe(_recipe())
        agent.record_context_recipe_book()
        agent.summon_context_recipe("the auth stack")
        assert builder.build() == built_before
        assert {
            p.name: p.read_bytes()
            for p in tmp_path.glob("*.py")} == before


class TestContextRecipesTerminalSurface:
    def test_show_recipe_summon_panel(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/recipes")
        assert "Context Recipes (M-158)" in text
        _, _, text = _slash(agent, "/recipes recipe recipe-auth-stack")
        assert "record-httpx-client" in text
        _, _, text = _slash(agent, "/recipes summon the Mojo build")
        assert "Summoned" in text
        assert "map-tests" in text
        _, _, text = _slash(agent, "/recipes panel")
        assert "Recipe panel in Context recipes" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/recipes [show|recipe <recipe-id>"
                "|summon <recipe name>|panel]") in text
        _, _, text = _slash(agent, "/recipes dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/recipes recipe recipe-nope")
        assert "no recipe in the book" in text


@pytest.fixture()
def recipes_handler(agent, monkeypatch):
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


def _recipes_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestContextRecipesCommand:
    def test_show_is_default(self, recipes_handler, agent):
        recipes_handler._handle_recipes("")
        assert "Context Recipes (M-158)" in (
            _recipes_published_text(recipes_handler))

    def test_recipe_summon_panel(self, recipes_handler, agent):
        recipes_handler._handle_recipes("recipe recipe-auth-stack")
        assert "record-httpx-client" in (
            _recipes_published_text(recipes_handler))
        recipes_handler._handle_recipes("summon the Mojo build")
        assert "map-tests" in (
            _recipes_published_text(recipes_handler))
        recipes_handler._handle_recipes("panel")
        assert "Recipe panel in Context recipes" in (
            _recipes_published_text(recipes_handler))

    def test_bad_grammar_is_published(self, recipes_handler, agent):
        recipes_handler._handle_recipes("dance party")
        assert USAGE in _recipes_published_text(recipes_handler)


class TestChatScreenRoutingRecipes:
    def test_recipes_routes_as_system_command(self, monkeypatch):
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
            "/recipes recipe recipe-auth-stack", _FakeLog())
        assert calls == [("/recipes", "recipe recipe-auth-stack")]
