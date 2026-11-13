"""The platform-matrix-final book (roadmap slice M-259) - pure layer.

Part XI - Proof. The roadmap words: **M-013's
table re-proven cell by cell; unproven cells
ship labelled NOT PROVEN, not silent.**

What this layer holds, as data:

* A **cell registry** held as data - one entry
  per cell of M-013's table: the twelve
  platform x surface pairs (linux, windows and
  macos, each against install, run, TUI and
  voice, P-01..P-12 in the M-013 order), its
  plain standing, and why the entry stands, in
  plain words. Every entry arrives as listed
  data (standing 'listed'); a cell the registry
  does not hold refuses BY NAME; a duplicated,
  half-written, or published entry refuses
  whole. A new cell needs no code change.
* A **matrix record** holds, for one cell, that
  cell's re-proof as a supplied fact: the run
  that re-proved it, the date it was re-proven,
  the verdict it carries (PROVEN or NOT PROVEN),
  the kind of proof it rests on
  (local-measured, historical-only, or none),
  the stages it has walked, and the claims it
  rests on, by kind. Its standing is DERIVED at
  call time against the explicit stage walk held
  as data (STAGES, TRANSITIONS): named, reproven,
  judged, labelled, held. A PROVEN record stands
  held only when its proof is local-measured
  and rests on held evidence (a local_run_ref
  among held evidence - local_run_ref, ci_run_ref,
  report_ref, journal_ref - never a bare claim:
  feeling, memory, assertion, summary), and the
  walk is complete: no inheritance, so a PROVEN
  verdict resting on historical or no evidence
  stands open, named in its gaps. A NOT PROVEN
  record stands held when the walk is complete,
  its date is named, and its unproven standing
  is recorded openly - the cell ships labelled
  NOT PROVEN, never silent; an unproven cell
  with nothing recorded stands open as silent.
* A **matrix verdict** is DERIVED over a whole
  book of records: the matrix stands ready only
  when every cell carries a held record - a
  missing cell, an open record, or a silent
  cell anywhere stops the matrix, and the
  verdict names what stopped it, beside the
  proven and not-proven cells it holds.
* A **matrix report** is the only shape a book
  may produce as a report, prepared only through
  the prepare road. A report stands at state
  "ready" by default, may be marked "shared" by
  a human, and reports the cells exactly as they
  were re-proven. A report asking to be sealed
  or locked instead of ready/shared, to be
  inflated instead of reported, to dress a bare
  claim up as a proof, or to claim the matrix
  final while any cell stands unanswered,
  refuses BY NAME.

Honesty rule, made code: a cell counts PROVEN
only on evidence measured locally, on the
current tree. Everything else ships labelled
NOT PROVEN, in the open - never inherited,
never silent, never inflated.

Honest boundary: this layer holds registry
entries, matrix records, derived standings,
derived matrix verdicts and matrix reports as
data. It runs no installer, launches no TUI,
records no voice and writes nothing outside
the session; the agent layer owns holding a
session's records and speaking for them.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date as _date
from typing import Dict, Iterable, Optional, Tuple
from .validation import ValidationError

__all__ = [
    "BARE_CLAIMS",
    "EVIDENCE_KINDS",
    "HELD_EVIDENCE",
    "PLAIN_EXPLANATION",
    "PLATFORMS",
    "STAGES",
    "TRANSITIONS",
    "USAGE",
    "CELLS",
    "PLATFORM_MATRIX_FINAL_SCHEMA",
    "PLATFORM_MATRIX_FINAL_SLICE",
    "RecordStanding",
    "MatrixVerdict",
    "MatrixRecord",
    "MatrixReport",
    "CellEntry",
    "CellRegistry",
    "default_registry",
    "derive_standing",
    "derive_verdict",
    "format_record",
    "format_records",
    "format_cell",
    "format_cells",
    "prepare_report",
]

PLATFORM_MATRIX_FINAL_SLICE = "M-259"
PLATFORM_MATRIX_FINAL_SCHEMA = "mythic.platform_matrix_final/1"

PLAIN_EXPLANATION = (
    "The platform matrix, finished honestly: "
    "M-013's twelve cells are re-proven cell by "
    "cell on the current tree, and a cell counts "
    "PROVEN only on evidence measured locally. "
    "Every other cell ships labelled NOT PROVEN, "
    "in the open - an unproven cell is named, "
    "never silent, and no historical run is "
    "inherited as proof."
)
USAGE = (
    "Record each cell's re-proof against its "
    "cell; read the derived matrix verdict before "
    "letting any report claim the matrix final; "
    "prepare a report only as a report, with "
    "every cell answered - proven on local "
    "evidence or labelled NOT PROVEN - and let a "
    "human share it. The whole table, answered "
    "cell by cell, as data first."
)

STAGES = ("named", "reproven", "judged", "labelled", "held")
TRANSITIONS = {
    "named": ("reproven",),
    "reproven": ("judged",),
    "judged": ("labelled",),
    "labelled": ("held",),
    "held": (),
}
HELD_EVIDENCE = ("local_run_ref", "ci_run_ref", "report_ref", "journal_ref")
BARE_CLAIMS = ("feeling", "memory", "assertion", "summary")
EVIDENCE_KINDS = HELD_EVIDENCE + BARE_CLAIMS
REPORT_STATES = ("ready", "shared")
PLATFORMS = ("linux", "windows", "macos")
SURFACES = ("install", "run", "tui", "voice")
VERDICTS = ("PROVEN", "NOT PROVEN")
PROOF_KINDS = ("local-measured", "historical-only", "none")


def _check_date(value: str) -> None:
    ok = (isinstance(value, str) and len(value) == 10
          and value[4] == "-" and value[7] == "-")
    if ok:
        try:
            _date.fromisoformat(value)
        except ValueError:
            ok = False
    if not ok:
        raise ValidationError(f"unknown re-proof date: {value}")


@dataclass(frozen=True)
class CellEntry:
    id: str
    platform: str
    surface: str
    standing: str
    reason: str

    def validate(self) -> None:
        for name in ("id", "platform", "surface", "standing", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValidationError(f"cell entry missing {name}")
        if self.platform not in PLATFORMS:
            raise ValidationError(f"unknown cell platform: {self.platform}")
        if self.surface not in SURFACES:
            raise ValidationError(f"unknown cell surface: {self.surface}")
        if self.standing != "listed":
            raise ValidationError(
                "cell entries are listed data "
                "only, never a published verdict here; "
                f"refused standing: {self.standing}")


CELLS = (
    CellEntry("P-01", "linux", "install", "listed",
              "the M-013 cell for linux install, re-proven cell by cell in the final matrix"),
    CellEntry("P-02", "linux", "run", "listed",
              "the M-013 cell for linux run, re-proven cell by cell in the final matrix"),
    CellEntry("P-03", "linux", "tui", "listed",
              "the M-013 cell for linux tui, re-proven cell by cell in the final matrix"),
    CellEntry("P-04", "linux", "voice", "listed",
              "the M-013 cell for linux voice, re-proven cell by cell in the final matrix"),
    CellEntry("P-05", "windows", "install", "listed",
              "the M-013 cell for windows install, re-proven cell by cell in the final matrix"),
    CellEntry("P-06", "windows", "run", "listed",
              "the M-013 cell for windows run, re-proven cell by cell in the final matrix"),
    CellEntry("P-07", "windows", "tui", "listed",
              "the M-013 cell for windows tui, re-proven cell by cell in the final matrix"),
    CellEntry("P-08", "windows", "voice", "listed",
              "the M-013 cell for windows voice, re-proven cell by cell in the final matrix"),
    CellEntry("P-09", "macos", "install", "listed",
              "the M-013 cell for macos install, re-proven cell by cell in the final matrix"),
    CellEntry("P-10", "macos", "run", "listed",
              "the M-013 cell for macos run, re-proven cell by cell in the final matrix"),
    CellEntry("P-11", "macos", "tui", "listed",
              "the M-013 cell for macos tui, re-proven cell by cell in the final matrix"),
    CellEntry("P-12", "macos", "voice", "listed",
              "the M-013 cell for macos voice, re-proven cell by cell in the final matrix"),
)


class CellRegistry:
    def __init__(self, entries: Iterable[CellEntry] = CELLS):
        self._entries: Dict[str, CellEntry] = {}
        for entry in entries:
            entry.validate()
            if entry.id in self._entries:
                raise ValidationError(f"duplicate cell: {entry.id}")
            self._entries[entry.id] = entry

    def get(self, cell_id: str) -> CellEntry:
        try:
            return self._entries[cell_id]
        except KeyError:
            raise ValidationError(
                f"unknown cell: {cell_id}") from None

    def ids(self) -> Tuple[str, ...]:
        return tuple(self._entries)

    def entries(self) -> Tuple[CellEntry, ...]:
        return tuple(self._entries.values())

    def combinations(self) -> Tuple[str, ...]:
        return tuple(self._entries)


def default_registry() -> CellRegistry:
    return CellRegistry()


@dataclass(frozen=True)
class MatrixRecord:
    cell: str
    run: str
    date: str
    verdict: str
    proof_kind: str
    stages: Tuple[str, ...]
    claims: Tuple[str, ...]

    def validate(self, registry: Optional[CellRegistry] = None) -> None:
        (registry or default_registry()).get(self.cell)
        if not self.run.strip():
            raise ValidationError("record names no re-proof run")
        if self.date:
            _check_date(self.date)
        if self.verdict not in VERDICTS:
            raise ValidationError(f"unknown record verdict: {self.verdict}")
        if self.proof_kind not in PROOF_KINDS:
            raise ValidationError(f"unknown record proof kind: {self.proof_kind}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown record evidence kind: {kind}")


@dataclass(frozen=True)
class RecordStanding:
    held: bool
    stage: str
    grade: str
    gaps: Tuple[str, ...]


def derive_standing(record: MatrixRecord,
                    registry: Optional[CellRegistry] = None) -> RecordStanding:
    record.validate(registry)
    gaps = []
    stages = record.stages
    if not stages or stages[0] != STAGES[0]:
        gaps.append("record does not open at named")
        stages = stages or ()
    else:
        for prev, nxt in zip(stages, stages[1:]):
            if nxt not in TRANSITIONS.get(prev, ()):
                gaps.append(f"stage step {prev} -> {nxt} not in the walk")
    stage = stages[-1] if stages else "unseen"
    if stage != "held":
        gaps.append(f"record stands at {stage}, not held")
    held_kinds = [c for c in record.claims if c in HELD_EVIDENCE]
    bare = [c for c in record.claims if c in BARE_CLAIMS]
    if not record.date:
        gaps.append("record names no re-proof date")
    if record.verdict == "PROVEN":
        if record.proof_kind != "local-measured":
            gaps.append(
                f"a PROVEN cell rests on {record.proof_kind} "
                "evidence, not local-measured: no inheritance")
        if "local_run_ref" not in record.claims:
            gaps.append(
                "the proof rests on no held "
                "local evidence")
        if not held_kinds:
            gaps.append("record rests on no held evidence")
        if bare and not held_kinds:
            gaps.append("record rests on bare claims only: " + ", ".join(bare))
    else:
        if not record.claims:
            gaps.append(
                "an unproven cell with nothing "
                "recorded stands silent, not labelled")
    return RecordStanding(held=not gaps, stage=stage,
                          grade="held" if not gaps else "open",
                          gaps=tuple(gaps))


@dataclass(frozen=True)
class MatrixVerdict:
    ready: bool
    gaps: Tuple[str, ...]
    proven_cells: Tuple[str, ...]
    not_proven_cells: Tuple[str, ...]
    missing_cells: Tuple[str, ...]


def derive_verdict(records: Iterable[MatrixRecord],
                   registry: Optional[CellRegistry] = None) -> MatrixVerdict:
    reg = registry or default_registry()
    by_cell: Dict[str, MatrixRecord] = {}
    gaps = []
    for record in records:
        record.validate(reg)
        if record.cell in by_cell:
            gaps.append(
                f"cell {record.cell} carries two re-proofs")
        else:
            by_cell[record.cell] = record
    missing = tuple(cid for cid in reg.combinations()
                    if cid not in by_cell)
    for cell_id in missing:
        gaps.append(f"cell {cell_id} has no re-proof in the book")
    proven = []
    not_proven = []
    for cell_id, record in by_cell.items():
        standing = derive_standing(record, reg)
        if standing.held and record.verdict == "PROVEN":
            proven.append(cell_id)
        if standing.held and record.verdict == "NOT PROVEN":
            not_proven.append(cell_id)
        if not standing.held:
            gaps.append(
                f"cell {cell_id} stands open: "
                + "; ".join(standing.gaps))
    return MatrixVerdict(ready=not gaps, gaps=tuple(gaps),
                         proven_cells=tuple(proven),
                         not_proven_cells=tuple(not_proven),
                         missing_cells=missing)


@dataclass(frozen=True)
class MatrixReport:
    book: str
    entry: str
    report: str
    date: str
    proven_count: int
    not_proven_count: int
    total_cells: int
    claims: Tuple[str, ...]
    state: str = "ready"
    certified: bool = False
    inflated: bool = False

    def validate(self, registry: Optional[CellRegistry] = None) -> None:
        reg = registry or default_registry()
        if not self.book.strip():
            raise ValidationError("report names no book")
        if not self.entry.strip():
            raise ValidationError("report names no entry")
        if not self.report.strip():
            raise ValidationError("matrix report reports nothing")
        if not self.date:
            raise ValidationError(
                "report names no date: a matrix "
                "report is reported with its date")
        _check_date(self.date)
        expected = len(reg.combinations())
        if self.total_cells != expected:
            raise ValidationError(
                f"report book holds {self.total_cells} "
                f"cells, not the road's {expected}")
        if self.proven_count < 0 or self.not_proven_count < 0:
            raise ValidationError(
                "unknown cell count: "
                f"{self.proven_count}/{self.not_proven_count}")
        if self.proven_count + self.not_proven_count > self.total_cells:
            raise ValidationError(
                "answered cells exceed the book: "
                f"{self.proven_count} + {self.not_proven_count} "
                f"of {self.total_cells}")
        for kind in self.claims:
            if kind not in EVIDENCE_KINDS:
                raise ValidationError(f"unknown report evidence kind: {kind}")
        if not [c for c in self.claims if c in HELD_EVIDENCE]:
            raise ValidationError(
                "matrix reports report held re-proofs "
                "only; a report dressing a bare claim "
                "as a proof refuses here")
        if self.state not in REPORT_STATES:
            raise ValidationError(
                "matrix reports stand ready or shared "
                "only, never sealed or locked; refused "
                f"state: {self.state}")
        if self.certified and \
                self.proven_count + self.not_proven_count < self.total_cells:
            raise ValidationError(
                "an unanswered cell anywhere stops "
                "the final claim: this report may not "
                "claim the matrix final short of "
                "every cell answered")
        if self.inflated:
            raise ValidationError(
                "matrix reports report the cells "
                "exactly as they were re-proven; a "
                "report is never inflated here")


def prepare_report(book: str, entry: str, report: str,
                   date: str, proven_count: int, not_proven_count: int,
                   total_cells: int,
                   claims: Tuple[str, ...] = (),
                   state: str = "ready",
                   certified: bool = False) -> MatrixReport:
    made = MatrixReport(book=book, entry=entry,
                        report=report, date=date,
                        proven_count=proven_count,
                        not_proven_count=not_proven_count,
                        total_cells=total_cells,
                        claims=tuple(claims),
                        state=state, certified=certified)
    made.validate()
    return made


def format_cell(entry: CellEntry) -> str:
    return (f"{entry.id} {entry.platform}/{entry.surface}: "
            f"standing {entry.standing} "
            f"- {entry.reason}")


def format_cells(registry: Optional[CellRegistry] = None) -> str:
    reg = registry or default_registry()
    return "\n".join(format_cell(e) for e in reg.entries())


def format_record(record: MatrixRecord,
                  registry: Optional[CellRegistry] = None) -> str:
    reg = registry or default_registry()
    entry = reg.get(record.cell)
    standing = derive_standing(record, reg)
    state = "held as answered" if standing.held else "open: " + "; ".join(standing.gaps)
    return (f"{record.cell} {entry.platform}/{entry.surface}: "
            f"verdict {record.verdict} "
            f"({record.proof_kind}), date "
            f"{record.date or '(no date)'} - {state}")


def format_records(records: Iterable[MatrixRecord],
                   registry: Optional[CellRegistry] = None) -> str:
    return "\n".join(format_record(r, registry) for r in records)
