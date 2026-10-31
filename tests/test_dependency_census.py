"""
TIER: unit
Dependency Census gate (All-Features roadmap slice M-012).

The shipped census (``mythic_agent/data/dependency_census.yaml``)
weighs every dependency the project declares. It is not a hand list:
these tests cross-check it against the live ``pyproject.toml``
(parsed with stdlib ``tomllib`` — names, and the core/extra/build
group each name is declared in) and against the dependency audit's
live third-party import scan, so a new dependency cannot land
uncensused and a removed one cannot linger in the census.
"""

import copy
import re
import tomllib
from pathlib import Path

import pytest

from mythic_agent.core.dependency_census import (
    DependencyCensus,
    load_census,
    render_markdown,
    validate_census,
    weight_class_for,
)
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"

# The extras the baseline venv does not install (voice-cloning pulls
# torch; dev/build are tooling), so these carry an honest unmeasured.
UNMEASURED = {"pydub", "chatterbox-tts", "torch", "torchaudio", "build", "hatchling"}


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _req_name(req: str) -> str:
    return _normalize(
        req.split(";")[0].split("[")[0].split(">")[0]
        .split("<")[0].split("=")[0].split("!")[0].strip()
    )


def _live_declared() -> dict:
    """Normalized requirement name -> set of groups declaring it."""
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    groups: dict[str, set] = {}
    for req in data["build-system"]["requires"]:
        groups.setdefault(_req_name(req), set()).add("build-system")
    for req in data["project"].get("dependencies", []):
        groups.setdefault(_req_name(req), set()).add("core")
    for extra, reqs in data["project"].get("optional-dependencies", {}).items():
        for req in reqs:
            groups.setdefault(_req_name(req), set()).add(extra)
    return groups


@pytest.fixture(scope="module")
def census() -> DependencyCensus:
    return load_census()


def test_shipped_census_loads_and_validates(census):
    assert isinstance(census, DependencyCensus)
    assert validate_census(load_resource("dependency_census.yaml")) == []
    n_deps, n_reps = census.counts()
    assert n_deps == 29
    assert n_reps >= 5


def test_every_declared_dependency_is_censused(census):
    live = _live_declared()
    censused = set(census.names())
    assert censused == set(live), (
        f"uncensused: {sorted(set(live) - censused)}; "
        f"stale: {sorted(censused - set(live))}"
    )


def test_declared_in_groups_match_pyproject(census):
    live = _live_declared()
    for dep in census.dependencies:
        assert set(dep.declared_in) == live[dep.name], dep.name


def test_every_live_third_party_import_is_censused(census):
    from tests.test_dependency_audit import IMPORT_TO_REQUIREMENT
    censused = set(census.names())
    for import_name, req in IMPORT_TO_REQUIREMENT.items():
        assert _normalize(req) in censused, import_name
    import_names = {d.name: d.import_name for d in census.dependencies}
    for import_name, req in IMPORT_TO_REQUIREMENT.items():
        assert import_names[_normalize(req)] == import_name


def test_ids_are_sequential(census):
    assert [d.id for d in census.dependencies] == [
        f"D-{n:02d}" for n in range(1, len(census.dependencies) + 1)]
    assert [r.id for r in census.replacements] == [
        f"R-{n:02d}" for n in range(1, len(census.replacements) + 1)]


def test_weights_match_measured_sizes(census):
    for dep in census.dependencies:
        assert dep.weight == weight_class_for(dep.measured_kb), dep.name
    unmeasured = {d.name for d in census.dependencies if d.measured_kb == 0}
    assert unmeasured == UNMEASURED
    # the core seven are all installed and measured in the baseline venv
    core = [d for d in census.dependencies if "core" in d.declared_in]
    assert len(core) == 7 and all(d.measured_kb > 0 for d in core)


def test_copyleft_rides_only_in_optional_extras(census):
    copyleft = set(census.copyleft_names())
    assert copyleft == {"textual-image", "psycopg", "piper-tts"}
    for dep in census.dependencies:
        if dep.name in copyleft:
            assert "core" not in dep.declared_in, dep.name


def test_replacement_list_is_honest(census):
    names = set(census.names())
    for rep in census.replacements:
        assert rep.dependency in names, rep.id
    wins = [r for r in census.replacements if r.verdict != "no-real-win"]
    assert wins, "the roadmap promises a replacement list where the win is real"
    scipy = [r for r in census.replacements if r.dependency == "scipy"]
    assert len(scipy) == 1
    assert scipy[0].verdict == "stdlib-win" and "wave" in scipy[0].candidate
    requests = [r for r in census.replacements if r.dependency == "requests"]
    assert len(requests) == 1 and requests[0].verdict == "already-core-win"


def test_render_covers_every_entry(census):
    text = render_markdown(census)
    for name in census.names():
        assert f"`{name}`" in text
    for rep in census.replacements:
        assert rep.id in text and rep.candidate in text
    for name in census.copyleft_names():
        assert name in text
    for win_id in census.replacement_wins():
        assert win_id in text


def _tampered(mutator):
    data = copy.deepcopy(load_resource("dependency_census.yaml"))
    mutator(data)
    return data


def test_validation_rejects_a_dropped_dependency():
    data = _tampered(lambda d: d["dependencies"].pop(0))
    problems = validate_census(data)
    assert any("sequential" in p or "non-empty" in p for p in problems)
    with pytest.raises(ValidationError):
        load_census(data)


def test_validation_rejects_a_weight_that_lies_about_size():
    data = _tampered(lambda d: d["dependencies"][0].update(weight="light"))
    problems = validate_census(data)
    assert any("weight" in p for p in problems)


def test_validation_rejects_an_unknown_necessity():
    data = _tampered(lambda d: d["dependencies"][0].update(necessity="vibes"))
    problems = validate_census(data)
    assert any("necessity" in p for p in problems)


def test_validation_rejects_a_replacement_for_an_uncensused_dependency():
    data = _tampered(
        lambda d: d["replacements"][0].update(dependency="not-a-dependency"))
    problems = validate_census(data)
    assert any("not censused" in p for p in problems)
