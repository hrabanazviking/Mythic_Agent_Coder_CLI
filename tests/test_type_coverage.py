"""Tests for mythic_agent.core.type_coverage (R-007).

The fixture-package tests are hermetic (built in tmp_path) so they are immune
to concurrent work in the real repo.  The package-total gate at the bottom is
the R-007 ratchet: annotated counts must meet or exceed the real measured
post-improvement baseline documented in docs/TYPE_COVERAGE.md.
"""

from pathlib import Path

import pytest

from mythic_agent.core.type_coverage import (
    CoverageReport,
    ModuleCoverage,
    measure,
    measure_module,
    mypy_available,
    mypy_check,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

# Post-improvement baseline, measured 2026-10-10 (docs/TYPE_COVERAGE.md).
# Compared with >= so the gate stays green as the package grows; it fails only
# on a real regression below the R-007 floor.
BASELINE_PARAMS_ANNOTATED = 901
BASELINE_RETURNS_ANNOTATED = 712

_ALPHA_SRC = '''\
def plain(a, b: int) -> str:
    return str(b)


def bare(x, y):
    return x


class Widget:
    def __init__(self, name: str) -> None:
        self.name = name

    def describe(self, loud: bool = False):
        return self.name.upper() if loud else self.name


async def fetch(url: str, *, timeout: float = 1.0) -> bytes:
    return b""


def varargs(first: str, *rest: int, flag: bool = False, **opts: str) -> None:
    pass
'''

# Expected counts for _ALPHA_SRC:
#   plain:    params 1/2,  returns 1/1
#   bare:     params 0/2,  returns 0/1
#   __init__: params 1/1 (self excluded), returns 1/1
#   describe: params 1/1 (self excluded), returns 0/1
#   fetch:    params 2/2,  returns 1/1
#   varargs:  params 4/4,  returns 1/1
EXPECTED_FUNCTIONS = 6
EXPECTED_PARAMS_TOTAL = 12
EXPECTED_PARAMS_ANNOTATED = 9
EXPECTED_RETURNS_TOTAL = 6
EXPECTED_RETURNS_ANNOTATED = 4


@pytest.fixture
def sample_pkg(tmp_path):
    """A tiny mythic_agent-shaped package with known annotation counts."""
    pkg = tmp_path / "mythic_agent"
    pkg.mkdir()
    # __init__.py files are excluded from the gate even when they define functions.
    (pkg / "__init__.py").write_text("def hidden():\n    pass\n", encoding="utf-8")
    (pkg / "alpha.py").write_text(_ALPHA_SRC, encoding="utf-8")
    # Test files are excluded from the gate.
    (pkg / "test_alpha.py").write_text(
        "def test_something(a, b, c):\n    pass\n", encoding="utf-8"
    )
    return tmp_path


def test_fixture_yields_exact_expected_counts(sample_pkg):
    report = measure(sample_pkg)
    assert report.module_count == 1
    assert report.functions_total == EXPECTED_FUNCTIONS
    assert report.params_total == EXPECTED_PARAMS_TOTAL
    assert report.params_annotated == EXPECTED_PARAMS_ANNOTATED
    assert report.returns_total == EXPECTED_RETURNS_TOTAL
    assert report.returns_annotated == EXPECTED_RETURNS_ANNOTATED
    module = report.module_named("mythic_agent.alpha")
    assert module is not None
    assert module.path == "mythic_agent/alpha.py"


def test_measure_is_deterministic_across_two_runs(sample_pkg):
    first = measure(sample_pkg)
    second = measure(sample_pkg)
    assert first.to_dict() == second.to_dict()


def test_measure_accepts_package_dir_directly(sample_pkg):
    from_package_dir = measure(sample_pkg / "mythic_agent")
    from_repo_root = measure(sample_pkg)
    assert from_package_dir.to_dict() == from_repo_root.to_dict()


def test_measure_rejects_directory_without_package(tmp_path):
    with pytest.raises(ValueError):
        measure(tmp_path / "no_such_package")


def test_self_and_cls_are_excluded_but_other_first_params_count(tmp_path):
    pkg = tmp_path / "mythic_agent"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "beta.py").write_text(
        "class A:\n"
        "    def m(self, x: int) -> None:\n"
        "        pass\n"
        "    @classmethod\n"
        "    def c(cls, y) -> None:\n"
        "        pass\n"
        "    @staticmethod\n"
        "    def s(z: str) -> None:\n"
        "        pass\n",
        encoding="utf-8",
    )
    module = measure_module(pkg / "beta.py", package_dir=pkg, repo_root=tmp_path)
    # self/cls excluded; staticmethod's first param counts (no self/cls to drop).
    assert module.params_total == 3
    assert module.params_annotated == 2  # x and z annotated, y not
    assert module.returns_annotated == 3


def test_excluded_files_return_none_from_measure_module(sample_pkg):
    pkg = sample_pkg / "mythic_agent"
    assert measure_module(pkg / "__init__.py", package_dir=pkg, repo_root=sample_pkg) is None
    assert measure_module(pkg / "test_alpha.py", package_dir=pkg, repo_root=sample_pkg) is None


def test_report_round_trips_through_dict(sample_pkg):
    report = measure(sample_pkg)
    clone = CoverageReport.from_dict(report.to_dict())
    assert clone.to_dict() == report.to_dict()
    assert isinstance(clone.modules[0], ModuleCoverage)


def test_percentages_handle_empty_modules():
    empty = ModuleCoverage(
        module="x", path="x.py", functions=0,
        params_total=0, params_annotated=0,
        returns_total=0, returns_annotated=0,
    )
    assert empty.params_pct == 100.0
    assert empty.returns_pct == 100.0


def test_mypy_available_returns_bool():
    assert isinstance(mypy_available(), bool)


def test_mypy_check_returns_none_when_mypy_missing(monkeypatch):
    import mythic_agent.core.type_coverage as tc
    monkeypatch.setattr(tc, "mypy_available", lambda: False)
    assert mypy_check(["mythic_agent/core/engine.py"]) is None


def test_package_total_gate_meets_post_improvement_baseline():
    """R-007 ratchet: real package annotated totals must meet the floor."""
    report = measure(REPO_ROOT)
    assert report.skipped == []
    assert report.params_annotated >= BASELINE_PARAMS_ANNOTATED, (
        f"params annotated regressed: {report.params_annotated} "
        f"< {BASELINE_PARAMS_ANNOTATED}"
    )
    assert report.returns_annotated >= BASELINE_RETURNS_ANNOTATED, (
        f"returns annotated regressed: {report.returns_annotated} "
        f"< {BASELINE_RETURNS_ANNOTATED}"
    )
