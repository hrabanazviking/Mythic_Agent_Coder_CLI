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
