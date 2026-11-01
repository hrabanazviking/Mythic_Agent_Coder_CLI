"""M-043 — Tree-sitter foundation.

TIER: integration

Part III (Code Intelligence) opens here: grammar-backed
parsing for the major languages, Python first, then
JavaScript/TypeScript, Rust, Go, and Mojo-aware, vendored
cleanly with licences noticed.

These tests do not take the catalogue's word for any of it:

* the catalogue loads and validates, its languages are exactly
  the roadmap languages in roadmap order, every
  grammar-declared entry names a package declared in the live
  ``pyproject.toml`` code-intelligence extra with its licence
  noticed, extensions never collide, and Mojo honestly
  declares no grammar,
* availability is probed live: in this environment (the extra
  installed in the baseline venv) every grammar-backed
  language parses through ``backend="tree_sitter"`` — a real
  parse per language, root type, no-error truth, and
  definitions extracted from the grammar's own node types,
* Python's fallback is honest: with the tree-sitter path
  forced off, Python parses through ``backend="python_ast"``
  with the same definitions, a broken file raises SyntaxError,
  and every non-Python language without its grammar refuses
  with ParseUnavailableError naming the install remedy,
* Mojo refuses in every environment — no grammar is invented,
* syntax errors are truth, not failure: a tree-sitter parse of
  broken code returns ``has_error`` true.
"""

from __future__ import annotations

import copy
import tomllib
from pathlib import Path

import pytest

import mythic_agent.core.tree_sitter_foundation as foundation
from mythic_agent.core.tree_sitter_foundation import (
    BACKENDS,
    CATALOG_SLICE,
    ROADMAP_LANGUAGES,
    ParseUnavailableError,
    availability_for,
    detect_language,
    extract_definitions,
    load_catalog,
    parse_source,
    probe_availability,
    render_markdown,
    validate_catalog,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource

REPO_ROOT = Path(__file__).resolve().parent.parent

SOURCES = {
    "python": (
        "class Greeter:\n    def greet(self):\n        return 'hi'\n\n"
        "def main():\n    return Greeter()\n",
        {("Greeter", "class"), ("greet", "function"), ("main", "function")},
        "module",
    ),
    "javascript": (
        "class Greeter { greet() { return 'hi'; } }\n"
        "function main() { return new Greeter(); }\n",
        {("Greeter", "class"), ("greet", "function"), ("main", "function")},
        "program",
    ),
    "typescript": (
        "interface Shape { area(): number; }\n"
        "class Square implements Shape { area(): number { return 1; } }\n"
        "function main(): number { return 1; }\n"
        "type Alias = number;\n",
        {("Shape", "interface"), ("Square", "class"),
         ("area", "function"), ("main", "function"), ("Alias", "type")},
        "program",
    ),
    "rust": (
        "struct Point { x: i32 }\nenum Shape { Round }\n"
        "trait Draw { fn draw(&self); }\n"
        "impl Point { fn new() -> Self { Point { x: 0 } } }\n"
        "fn main() {}\n",
        {("Point", "struct"), ("Shape", "enum"), ("Draw", "trait"),
         ("main", "function")},
        "source_file",
    ),
    "go": (
        "package main\n\ntype Point struct { X int }\n"
        "func (p Point) Area() int { return 0 }\n"
        "func main() {}\n",
        {("Point", "type"), ("Area", "function"), ("main", "function")},
        "source_file",
    ),
}


@pytest.fixture(scope="module")
def catalog():
    return load_catalog()


def test_shipped_catalog_loads_and_validates(catalog):
    assert validate_catalog(load_resource("tree_sitter_languages.yaml")) == []
    assert catalog.names() == ROADMAP_LANGUAGES
    assert foundation.CATALOG_SLICE == "M-043" == CATALOG_SLICE


def test_grammar_entries_are_declared_in_the_live_extra(catalog):
    data = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    extra = data["project"]["optional-dependencies"]["code-intelligence"]
    declared = {
        req.split(">")[0].split("<")[0].split("=")[0].strip()
        for req in extra
    }
    assert catalog.core_package in declared
    for entry in catalog.languages_with("grammar-declared"):
        assert entry.grammar_package in declared, entry.language
        assert entry.licence == "MIT"
        assert entry.licence_notice and entry.licence in entry.licence_notice
        assert entry.upstream and entry.grammar_package in entry.upstream


def test_extensions_map_back_to_their_language(catalog):
    for entry in catalog.languages:
        for ext in entry.extensions:
            assert catalog.for_extension(ext) is entry
    assert detect_language("x.py") == "python"
    assert detect_language("x.ts") == "typescript"
    assert detect_language("x.rs") == "rust"
    assert detect_language("x.go") == "go"
    assert detect_language("x.mojo") == "mojo"
    assert detect_language("x.unknownext") is None
    assert detect_language("noextension") is None


def test_mojo_is_honestly_grammarless(catalog):
    mojo = catalog.language("mojo")
    assert mojo.status == "no-grammar-package"
    assert mojo.grammar_package is None and mojo.licence is None
    avail = availability_for("mojo", catalog)
    assert avail.available is False
    assert "no grammar" in avail.detail
    with pytest.raises(ParseUnavailableError):
        parse_source("mojo", "fn main():\n    pass\n", catalog=catalog)


def test_unknown_language_is_keyerror(catalog):
    with pytest.raises(KeyError):
        catalog.language("cobol")
    with pytest.raises(KeyError):
        parse_source("cobol", "x", catalog=catalog)


def test_probe_matches_this_environment(catalog):
    probed = {a.language: a for a in probe_availability(catalog)}
    assert tuple(probed) == ROADMAP_LANGUAGES
    # The baseline venv carries the code-intelligence extra
    # (installed by the M-043 tick and declared in pyproject);
    # the probe must agree with a direct import, either way.
    try:
        import tree_sitter  # noqa: F401
        core_present = True
    except ImportError:
        core_present = False
    for name in ROADMAP_LANGUAGES[:-1]:
        assert probed[name].available is core_present, probed[name].detail
    assert probed["mojo"].available is False


@pytest.mark.parametrize("language", list(SOURCES))
def test_grammar_backed_parse_per_language(catalog, language):
    source, expected_defs, expected_root = SOURCES[language]
    if not availability_for(language, catalog).available:
        pytest.skip(f"{language} grammar not installed in this environment")
    parsed = parse_source(language, source, catalog=catalog)
    assert parsed.backend == "tree_sitter" and parsed.backend in BACKENDS
    assert parsed.root.type == expected_root
    assert parsed.has_error is False
    got = {(d.name, d.kind) for d in parsed.definitions}
    assert expected_defs <= got, (language, got)
    for definition in parsed.definitions:
        assert definition.language == language
        assert definition.start_point[0] >= 0
    # the tree really spans the source
    assert parsed.root.start_byte == 0
    assert parsed.root.end_byte == len(source.encode("utf-8"))
    walked = parsed.root.walk()
    assert walked[0] is parsed.root and len(walked) > 3
    assert extract_definitions(language, source, catalog=catalog) == \
        parsed.definitions


def test_tree_sitter_reports_syntax_errors_as_truth(catalog):
    if not availability_for("python", catalog).available:
        pytest.skip("python grammar not installed in this environment")
    parsed = parse_source("python", "def broken(:\n", catalog=catalog)
    assert parsed.backend == "tree_sitter"
    assert parsed.has_error is True


def test_python_ast_fallback_is_labelled_and_equivalent(catalog, monkeypatch):
    monkeypatch.setattr(foundation, "_tree_sitter", None)
    source, expected_defs, _root = SOURCES["python"]
    parsed = parse_source("python", source, catalog=catalog)
    assert parsed.backend == "python_ast"
    assert parsed.has_error is False
    assert {(d.name, d.kind) for d in parsed.definitions} == expected_defs
    with pytest.raises(SyntaxError):
        parse_source("python", "def broken(:\n", catalog=catalog)


def test_non_python_without_grammar_refuses_with_remedy(catalog, monkeypatch):
    monkeypatch.setattr(foundation, "_tree_sitter", None)
    for language in ("javascript", "typescript", "rust", "go"):
        with pytest.raises(ParseUnavailableError) as excinfo:
            parse_source(language, SOURCES[language][0], catalog=catalog)
        assert "code-intelligence" in str(excinfo.value), language
    probed = {a.language: a for a in probe_availability(catalog)}
    assert all(not probed[name].available
               for name in ROADMAP_LANGUAGES)


def test_parse_source_rejects_non_string_source(catalog):
    with pytest.raises(ValidationError):
        parse_source("python", b"def f(): pass\n", catalog=catalog)  # type: ignore[arg-type]


def test_render_covers_every_language_and_licence(catalog):
    text = render_markdown(catalog)
    for entry in catalog.languages:
        assert entry.language in text
    for entry in catalog.languages_with("grammar-declared"):
        assert entry.grammar_package in text and entry.licence_notice in text
    assert "mojo" in text.lower()


def _tampered(mutator):
    data = copy.deepcopy(load_resource("tree_sitter_languages.yaml"))
    mutator(data)
    return data


def test_validation_rejects_an_invented_mojo_grammar():
    data = _tampered(lambda d: d["languages"][5].update(
        grammar_package="tree-sitter-mojo"))
    problems = validate_catalog(data)
    assert any("invented" in p or "null" in p for p in problems)
    with pytest.raises(ValidationError):
        load_catalog(data)


def test_validation_rejects_a_grammar_without_licence_notice():
    data = _tampered(lambda d: d["languages"][0].update(licence_notice=None))
    problems = validate_catalog(data)
    assert any("licence_notice" in p for p in problems)


def test_validation_rejects_a_dropped_roadmap_language():
    data = _tampered(lambda d: d["languages"].pop())
    problems = validate_catalog(data)
    assert any("roadmap" in p for p in problems)


def test_validation_rejects_an_extension_collision():
    data = _tampered(lambda d: d["languages"][1].update(extensions=[".py"]))
    problems = validate_catalog(data)
    assert any("already claimed" in p for p in problems)
