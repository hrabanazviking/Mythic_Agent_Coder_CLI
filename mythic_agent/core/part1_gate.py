"""The Part I gate (All-Features roadmap slice M-018).

Part I — The Census & The Charter — closes here. Its seventeen
slices produced the census, the Concordance, the audits, the
charters, the baseline freeze, and the roadmap-as-data; this gate
records them as one validated artefact list and proves the road's
closing claims:

* Census + concordance + audits are published in-repo: every
  artefact M-001..M-017 is named here with its location in the
  repository — a data resource the app ships, or the Concordance
  document under ``docs/`` — and the gate's tests re-load every
  data artefact through its own shipped loader, so "published"
  means "present and loadable", never merely "listed".
* Baseline evidence is banked: the full-suite totals recorded
  here must equal the frozen baseline's own totals (M-007) —
  the gate cannot quietly re-state the "before" numbers.
* Volmarr's 500-slice Mimisbrunnr file is untouched: it is pinned
  here by sha256, byte count, and line count, and the gate's tests
  compare the live file against that pin on every run.

Data lives in ``mythic_agent/data/part1_gate.yaml``. The verdict
is ``PASS`` and the validator accepts no other verdict: a gate
that has failed is not a gate record at all — it is a defect to
fix in the slice that broke it.
"""

from __future__ import annotations

__all__ = [
    "GATE_RESOURCE",
    "GATE_SCHEMA",
    "GATE_SLICE",
    "KINDS",
    "Any",
    "Artefact",
    "Dict",
    "Gate",
    "List",
    "Optional",
    "Tuple",
    "load_gate",
    "render_markdown",
    "validate_gate",
]

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..resources import load_resource
from .validation import ValidationError

#: Resource name of the gate data file inside ``mythic_agent/data``.
GATE_RESOURCE = "part1_gate.yaml"

#: The only schema this loader accepts.
GATE_SCHEMA = "mythic.part1_gate/1"

#: The slice that owns this gate.
GATE_SLICE = "M-018"

#: The artefact kinds the gate knows: shipped data, or an in-repo doc.
KINDS = ("data", "doc")

_ID_RE = re.compile(r"^M-\d{3}$")
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_LOADER_RE = re.compile(r"^[a-z_][a-z0-9_.]*:[a-z_][a-z0-9_]*$")


@dataclass(frozen=True)
class Artefact:
    """One Part I artefact, published in-repo."""

    slice: str
    title: str
    kind: str
    location: str
    loader: str
    evidence: str


@dataclass(frozen=True)
class Gate:
    """The validated Part I gate record."""

    gate_slice: str
    part: int
    part_title: str
    verdict: str
    gate_note: str
    artefacts: Tuple[Artefact, ...]
    baseline: Tuple[int, int, int, int]  # collected, passed, failed, skipped
    mimis_path: str
    mimis_sha256: str
    mimis_bytes: int
    mimis_lines: int
    mimis_note: str

    def artefact_ids(self) -> Tuple[str, ...]:
        """The gated slices, in road order."""
        return tuple(a.slice for a in self.artefacts)

    def loaders(self) -> Tuple[str, ...]:
        """Every non-empty loader reference, in road order."""
        return tuple(a.loader for a in self.artefacts if a.loader)

    def baseline_totals(self) -> Tuple[int, int, int, int]:
        """(collected, passed, failed, skipped) from the frozen baseline."""
        return self.baseline

    def by_kind(self, kind: str) -> Tuple[Artefact, ...]:
        """Every artefact of *kind* (``data`` or ``doc``)."""
        return tuple(a for a in self.artefacts if a.kind == kind)


def validate_gate(data: Any) -> List[str]:
    """Return a list of human-readable problems with gate *data*."""
    problems: List[str] = []
    if not isinstance(data, dict):
        return [f"gate root must be a mapping, got {type(data).__name__}"]
    if data.get("schema") != GATE_SCHEMA:
        problems.append(
            f"schema must be {GATE_SCHEMA!r}, got {data.get('schema')!r}"
        )
    if data.get("gate_slice") != GATE_SLICE:
        problems.append(
            f"gate_slice must be {GATE_SLICE!r}, got {data.get('gate_slice')!r}"
        )
    if data.get("part") != 1:
        problems.append(f"part must be 1, got {data.get('part')!r}")
    if data.get("verdict") != "PASS":
        problems.append(
            f"verdict must be 'PASS' (a failed gate is a defect, not a "
            f"record), got {data.get('verdict')!r}"
        )
    for key in ("part_title", "gate_note"):
        if not isinstance(data.get(key), str) or not data[key]:
            problems.append(f"{key} must be a non-empty string")

    artefacts = data.get("artefacts")
    if not isinstance(artefacts, list) or not artefacts:
        problems.append("artefacts must be a non-empty list")
        return problems
    if len(artefacts) != 17:
        problems.append(
            f"artefacts must number exactly 17 (M-001..M-017), "
            f"got {len(artefacts)}"
        )
    for position, art in enumerate(artefacts, start=1):
        if not isinstance(art, dict):
            problems.append(f"artefact is not a mapping: {art!r}")
            continue
        sid = art.get("slice")
        expected = f"M-{position:03d}"
        if not isinstance(sid, str) or not _ID_RE.match(sid):
            problems.append(f"artefact {sid!r}: slice must look like 'M-001'")
        elif sid != expected:
            problems.append(
                f"artefact {sid}: slices must be sequential, expected {expected}"
            )
        kind = art.get("kind")
        if kind not in KINDS:
            problems.append(
                f"artefact {sid}: kind must be one of {KINDS}, got {kind!r}"
            )
        location = art.get("location")
        if not isinstance(location, str) or not location:
            problems.append(f"artefact {sid}: location must be non-empty")
        elif kind == "data" and not location.endswith(".yaml"):
            problems.append(
                f"artefact {sid}: a data artefact's location must be its "
                f"resource name ending .yaml, got {location!r}"
            )
        elif kind == "doc" and not location.endswith(".md"):
            problems.append(
                f"artefact {sid}: a doc artefact's location must be an "
                f"in-repo .md path, got {location!r}"
            )
        loader = art.get("loader")
        if not isinstance(loader, str):
            problems.append(f"artefact {sid}: loader must be a string")
        elif kind == "data" and not _LOADER_RE.match(loader):
            problems.append(
                f"artefact {sid}: a data artefact needs a loader like "
                f"'mythic_agent.core.<module>:<function>', got {loader!r}"
            )
        elif kind == "doc" and loader:
            problems.append(
                f"artefact {sid}: a doc artefact carries no loader, "
                f"got {loader!r}"
            )
        for key in ("title", "evidence"):
            if not isinstance(art.get(key), str) or not art[key]:
                problems.append(f"artefact {sid}: {key} must be non-empty")

    baseline = data.get("baseline")
    if not isinstance(baseline, dict):
        problems.append("baseline must be a mapping")
    else:
        counts: Dict[str, int] = {}
        for key in ("collected", "passed", "failed", "skipped"):
            value = baseline.get(key)
            if not isinstance(value, int) or value < 0:
                problems.append(f"baseline.{key} must be a non-negative integer")
            else:
                counts[key] = value
        if len(counts) == 4 and (
            counts["passed"] + counts["failed"] + counts["skipped"]
            != counts["collected"]
        ):
            problems.append(
                "baseline arithmetic does not close: passed + failed + "
                f"skipped != collected in {counts}"
            )
        if baseline.get("resource") != "baseline_freeze.yaml":
            problems.append(
                "baseline.resource must be 'baseline_freeze.yaml', got "
                f"{baseline.get('resource')!r}"
            )

    mimis = data.get("mimisbrunnr")
    if not isinstance(mimis, dict):
        problems.append("mimisbrunnr must be a mapping")
    else:
        if not isinstance(mimis.get("path"), str) or not mimis["path"].endswith(".md"):
            problems.append("mimisbrunnr.path must be a non-empty .md path")
        sha = mimis.get("sha256")
        if not isinstance(sha, str) or not _SHA_RE.match(sha):
            problems.append("mimisbrunnr.sha256 must be 64 lowercase hex characters")
        for key in ("bytes", "lines"):
            value = mimis.get(key)
            if not isinstance(value, int) or value <= 0:
                problems.append(f"mimisbrunnr.{key} must be a positive integer")
        if not isinstance(mimis.get("note"), str) or not mimis["note"]:
            problems.append("mimisbrunnr.note must be a non-empty string")
    return problems


def _to_gate(data: Dict[str, Any]) -> Gate:
    baseline = data["baseline"]
    mimis = data["mimisbrunnr"]
    return Gate(
        gate_slice=data["gate_slice"],
        part=data["part"],
        part_title=data["part_title"],
        verdict=data["verdict"],
        gate_note=data["gate_note"],
        artefacts=tuple(
            Artefact(
                slice=a["slice"],
                title=a["title"],
                kind=a["kind"],
                location=a["location"],
                loader=a["loader"],
                evidence=a["evidence"],
            )
            for a in data["artefacts"]
        ),
        baseline=(
            baseline["collected"],
            baseline["passed"],
            baseline["failed"],
            baseline["skipped"],
        ),
        mimis_path=mimis["path"],
        mimis_sha256=mimis["sha256"],
        mimis_bytes=mimis["bytes"],
        mimis_lines=mimis["lines"],
        mimis_note=mimis["note"],
    )


def load_gate(data: Optional[Dict[str, Any]] = None) -> Gate:
    """Load and validate the shipped Part I gate (or *data*).

    Raises :class:`~mythic_agent.core.validation.ValidationError`
    listing every problem when the data is not a well-formed gate.
    """
    raw = data if data is not None else load_resource(GATE_RESOURCE)
    problems = validate_gate(raw)
    if problems:
        raise ValidationError(
            "part I gate failed validation: " + "; ".join(problems)
        )
    return _to_gate(raw)  # type: ignore[arg-type]


def render_markdown(gate: Gate) -> str:
    """Render the gate as markdown: verdict, artefacts, baseline, pin.

    Built from :meth:`Gate.artefact_ids`, :meth:`Gate.loaders`,
    :meth:`Gate.baseline_totals`, and :meth:`Gate.by_kind`, so the
    rendered page itself is computed from the same accessors the
    tests pin.
    """
    collected, passed, failed, skipped = gate.baseline_totals()
    lines = [
        "# Part I Gate — The Census & The Charter (M-018)",
        "",
        f"*Gate slice {gate.gate_slice}, part {gate.part} — "
        f"{gate.part_title}. Verdict: **{gate.verdict}**.*",
        "",
        gate.gate_note,
        "",
        f"**Artefacts gated: {len(gate.artefact_ids())}** "
        f"({len(gate.by_kind('data'))} data, {len(gate.by_kind('doc'))} doc), "
        f"re-loadable through {len(gate.loaders())} shipped loaders.",
        "",
        "## Artefacts",
        "",
    ]
    for art in gate.artefacts:
        loader = f" via `{art.loader}`" if art.loader else ""
        lines.append(
            f"- **{art.slice}** {art.title} — `{art.location}`{loader}: "
            f"{art.evidence}"
        )
    lines += [
        "",
        "## Baseline evidence (banked, M-007)",
        "",
        f"- Frozen full suite: collected {collected}: **{passed} passed, "
        f"{failed} failed, {skipped} skipped**.",
        "",
        "## Volmarr's 500-slice file (untouched)",
        "",
        f"- `{gate.mimis_path}` — sha256 `{gate.mimis_sha256}`, "
        f"{gate.mimis_bytes} bytes, {gate.mimis_lines} lines.",
        f"- {gate.mimis_note}",
        "",
    ]
    return "\n".join(lines)
