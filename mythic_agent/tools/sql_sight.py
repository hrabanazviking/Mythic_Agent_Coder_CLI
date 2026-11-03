"""SQL and data sight (M-065).

Part III — Code Intelligence. The roadmap's words for
this slice: "SQL and data sight: schema reading, query
explain, migration files understood as code (the Muse
DB pattern, productised)."

What ships here, in ``mythic_agent/tools/sql_sight.py``:

* **Workspace-local databases only, read-only.** SQLite
  database files found under the workspace (``.db`` /
  ``.sqlite`` / ``.sqlite3``) are opened through a
  read-only URI connection (``mode=ro``). This module
  never writes to a database: the connection itself
  refuses writes, and the slice's tests prove a database
  file's bytes and mtime are unchanged across every
  road.
* **Schema reading.** Tables, views and indexes are
  read from ``sqlite_master``; columns (name, declared
  type, nullability, default, primary-key position)
  from ``PRAGMA table_info``; foreign keys from
  ``PRAGMA foreign_key_list``; index columns from
  ``PRAGMA index_list`` / ``index_info``. Row counts
  come from ``SELECT COUNT(*)`` — an exact count, cheap
  on the local files this road serves, and named as
  such; a count that fails is ``None``, never guessed.
* **Query explain without effects.** A supplied query
  is explained with ``EXPLAIN`` and ``EXPLAIN QUERY
  PLAN`` on the read-only connection — explaining never
  executes the query's effects. Only SELECT-shaped
  statements (``SELECT`` / ``WITH ... SELECT``) are
  explained; a write-shaped statement (INSERT, UPDATE,
  DELETE, DDL, PRAGMA, anything else) is refused
  plainly and never run, not even to explain it.
* **Migration files understood as code.** Migration
  files are recognised by layout — SQL files under a
  ``migrations`` (or alembic-style ``versions``)
  directory, numbered SQL files, and alembic ``.py``
  revisions under ``versions`` — and parsed
  structurally as code: version/order from the file
  name, up/down sections split on their markers (SQL
  comment markers, or alembic's ``upgrade()`` /
  ``downgrade()``), and the tables each section
  creates, alters or drops extracted from its
  statements. Migrations are read, never applied.
* **The surfaces.** ``Agent.sql_sight(...)`` and
  ``/sql [show | <db> | explain <db> <query> |
  migrations]`` on the terminal and TUI system-command
  roads, sharing this module's parser and formatter.
  The setting ``sql_sight`` (on by default) closes the
  road plainly.

Honesty rules, pinned by the slice's tests:

* **Read-only is the connection, not a promise.** Every
  database is opened ``mode=ro``; a write attempt
  through such a connection fails in SQLite itself.
* **Writes are never explained into existence.** A
  non-SELECT statement is refused before any connection
  runs it.
* **Absence is named.** A workspace with no databases
  or no migrations says so; an unreadable database is
  named with its error, never dressed as an empty one.
* **This road never edits or applies.** It reads
  schemas, explains queries and reads migrations as
  code; changing data or applying a migration is a
  separate act.
"""

from __future__ import annotations

__all__ = [
    "PLAIN_EXPLANATION",
    "SQL_SLICE",
    "USAGE",
    "DB_EXTENSIONS",
    "ColumnInfo",
    "ForeignKeyInfo",
    "IndexInfo",
    "TableSchema",
    "DatabaseSchema",
    "ExplainResult",
    "MigrationInfo",
    "SqlReport",
    "enabled_from_config",
    "find_databases",
    "read_schema",
    "is_explainable",
    "explain_query",
    "find_migration_files",
    "parse_migration",
    "sql_sight",
    "parse_sql_args",
    "format_sql_report",
    "render_markdown",
]

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

SQL_SLICE = "M-065"

PLAIN_EXPLANATION = (
    "SQL sight reads the workspace's own SQLite "
    "databases without ever writing to them: every "
    "database is opened read-only, so /sql show lists "
    "each database's tables, columns, indexes and "
    "foreign keys, /sql explain <db> <query> shows how "
    "SQLite would run a SELECT — explained, never "
    "executed, and write-shaped statements are refused "
    "outright — and /sql migrations reads the project's "
    "migration files as code: their order, their up and "
    "down sections, and the tables they create, alter "
    "or drop. Migrations are read, never applied."
)

USAGE = "Usage: /sql [show | <db> | explain <db> <query> | migrations]"

DB_EXTENSIONS = (".db", ".sqlite", ".sqlite3")

#: Directories the workspace scan never enters.
_SKIP_DIRS = {".git", ".hg", ".svn", "__pycache__",
              "node_modules", "dist", "build",
              ".venv", ".venv-baseline", "venv"}

#: Caps for the workspace scan; every cut is named.
MAX_SCAN_DBS = 100
MAX_SCAN_MIGRATIONS = 500
MAX_MIGRATION_BYTES = 256_000


def enabled_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """SQL sight is on unless config says so."""
    if not config:
        return True
    return config.get("sql_sight", True) is not False


# ---------------------------------------------------------------------------
# Schema reading — read-only connections only
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ColumnInfo:
    """One column, from PRAGMA table_info."""

    name: str
    type: str = ""
    notnull: bool = False
    default: Optional[str] = None
    pk: int = 0

    def record(self) -> Dict[str, Any]:
        return {"name": self.name, "type": self.type,
                "notnull": self.notnull, "default": self.default,
                "pk": self.pk}


@dataclass(frozen=True)
class ForeignKeyInfo:
    """One foreign key, from PRAGMA foreign_key_list."""

    table: str
    from_column: str
    to_column: str

    def record(self) -> Dict[str, Any]:
        return {"table": self.table, "from": self.from_column,
                "to": self.to_column}


@dataclass(frozen=True)
class IndexInfo:
    """One index, from PRAGMA index_list / index_info."""

    name: str
    unique: bool = False
    columns: Tuple[str, ...] = ()

    def record(self) -> Dict[str, Any]:
        return {"name": self.name, "unique": self.unique,
                "columns": list(self.columns)}


@dataclass
class TableSchema:
    """One table's (or view's) whole structural account."""

    name: str
    kind: str = "table"  # table | view
    columns: List[ColumnInfo] = field(default_factory=list)
    foreign_keys: List[ForeignKeyInfo] = field(default_factory=list)
    indexes: List[IndexInfo] = field(default_factory=list)
    row_count: Optional[int] = None

    def column_names(self) -> Tuple[str, ...]:
        return tuple(c.name for c in self.columns)

    def record(self) -> Dict[str, Any]:
        return {"name": self.name, "kind": self.kind,
                "columns": [c.record() for c in self.columns],
                "foreign_keys": [f.record() for f in self.foreign_keys],
                "indexes": [i.record() for i in self.indexes],
                "row_count": self.row_count}


@dataclass
class DatabaseSchema:
    """One database file's whole schema account."""

    path: str
    tables: List[TableSchema] = field(default_factory=list)
    note: str = ""

    def table_names(self) -> Tuple[str, ...]:
        return tuple(t.name for t in self.tables)

    def record(self) -> Dict[str, Any]:
        return {"path": self.path,
                "tables": [t.record() for t in self.tables],
                "note": self.note}


def _connect_readonly(path: Path) -> sqlite3.Connection:
    """Open *path* read-only — SQLite itself refuses writes."""
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def read_schema(path: Path, display: str = "") -> DatabaseSchema:
    """One database's schema, read through a ro connection.

    An unreadable or non-SQLite file is an honest schema
    carrying its error in ``note``, never an empty bill.
    """
    schema = DatabaseSchema(path=display or str(path))
    try:
        conn = _connect_readonly(path)
    except sqlite3.Error as exc:
        schema.note = f"the database could not be opened: {exc}"
        return schema
    try:
        rows = conn.execute(
            "SELECT type, name FROM sqlite_master "
            "WHERE type IN ('table', 'view') "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
        for kind, name in rows:
            table = TableSchema(name=name, kind=kind)
            for cid, cname, ctype, notnull, dflt, pk in conn.execute(
                    f"PRAGMA table_info({_quote_ident(name)})"):
                table.columns.append(ColumnInfo(
                    name=cname, type=ctype or "",
                    notnull=bool(notnull),
                    default=None if dflt is None else str(dflt),
                    pk=int(pk or 0)))
            for fk in conn.execute(
                    f"PRAGMA foreign_key_list({_quote_ident(name)})"):
                # (id, seq, table, from, to, on_update, ...)
                table.foreign_keys.append(ForeignKeyInfo(
                    table=fk[2], from_column=fk[3],
                    to_column=fk[4] or ""))
            for idx in conn.execute(
                    f"PRAGMA index_list({_quote_ident(name)})"):
                # (seq, name, unique, origin, partial)
                cols = tuple(
                    r[2] for r in conn.execute(
                        f"PRAGMA index_info({_quote_ident(idx[1])})"))
                table.indexes.append(IndexInfo(
                    name=idx[1], unique=bool(idx[2]), columns=cols))
            try:
                table.row_count = int(conn.execute(
                    f"SELECT COUNT(*) FROM {_quote_ident(name)}"
                ).fetchone()[0])
            except sqlite3.Error:
                table.row_count = None
            schema.tables.append(table)
    except sqlite3.Error as exc:
        schema.note = f"the schema could not be read: {exc}"
    finally:
        conn.close()
    return schema


def find_databases(workspace: Any) -> Tuple[List[Path], List[str]]:
    """Every workspace-local database file, caps named."""
    root = Path(workspace)
    found: List[Path] = []
    warnings: List[str] = []
    if not root.is_dir():
        return found, warnings
    candidates = sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in DB_EXTENSIONS)
    for candidate in candidates:
        if any(part in _SKIP_DIRS or part.startswith(".venv")
               for part in candidate.parts):
            continue
        if len(found) >= MAX_SCAN_DBS:
            warnings.append(
                f"scan capped at {MAX_SCAN_DBS} database files; "
                "further files were not read")
            break
        found.append(candidate)
    return found, warnings


# ---------------------------------------------------------------------------
# Query explain — SELECT-shaped only, explained never executed
# ---------------------------------------------------------------------------

_WRITE_HEADS = {
    "insert", "update", "delete", "drop", "create", "alter",
    "replace", "pragma", "attach", "detach", "vacuum",
    "reindex", "analyze", "truncate", "grant", "revoke",
}


def _first_keyword(sql: str) -> str:
    match = re.match(r"\s*(?:--[^\n]*\n\s*)*([A-Za-z]+)",
                     sql or "")
    return match.group(1).lower() if match else ""


def is_explainable(query: str) -> Tuple[bool, str]:
    """(explainable, reason) for one supplied query.

    Only SELECT-shaped statements are explainable: a
    ``SELECT``, or a ``WITH`` whose body is a SELECT.
    Everything else — writes, DDL, PRAGMA, empty input —
    is refused with its reason, before anything runs.
    """
    sql = (query or "").strip()
    if not sql:
        return False, "no query was given to explain"
    head = _first_keyword(sql)
    if head == "select":
        return True, ""
    if head == "with":
        if re.search(r"\)\s*select\b", sql, re.IGNORECASE):
            return True, ""
        return False, ("only a WITH ... SELECT can be explained; "
                       "this WITH does not end in a SELECT")
    if head in _WRITE_HEADS:
        return False, (f"{head.upper()} statements change data or "
                       "schema, so they are refused here — explain "
                       "covers SELECT queries only, and nothing on "
                       "this road is ever executed")
    return False, (f"only SELECT queries can be explained; "
                   f"{head.upper() or 'this statement'} is not one")


@dataclass
class ExplainResult:
    """One explained query's account."""

    db: str = ""
    query: str = ""
    status: str = "ok"  # ok | refused | error
    plan: List[str] = field(default_factory=list)
    detail: List[str] = field(default_factory=list)
    note: str = ""

    def record(self) -> Dict[str, Any]:
        return {"db": self.db, "query": self.query,
                "status": self.status, "plan": list(self.plan),
                "detail": list(self.detail), "note": self.note}


def explain_query(path: Path, query: str,
                  display: str = "") -> ExplainResult:
    """Explain *query* against *path*, read-only.

    ``EXPLAIN`` / ``EXPLAIN QUERY PLAN`` prepare the
    statement without executing its effects; the
    read-only connection is the second lock. A refused
    query is refused before any connection opens.
    """
    result = ExplainResult(db=display or str(path), query=query)
    ok, reason = is_explainable(query)
    if not ok:
        result.status = "refused"
        result.note = reason
        return result
    sql = query.strip().rstrip(";")
    try:
        conn = _connect_readonly(path)
    except sqlite3.Error as exc:
        result.status = "error"
        result.note = f"the database could not be opened: {exc}"
        return result
    try:
        result.plan = [
            " ".join(str(cell) for cell in row[1:])
            if len(row) > 1 else str(row[0])
            for row in conn.execute(f"EXPLAIN QUERY PLAN {sql}")]
        result.detail = [
            ", ".join(str(cell) for cell in row)
            for row in conn.execute(f"EXPLAIN {sql}")]
    except sqlite3.Error as exc:
        result.status = "error"
        result.note = f"the query could not be explained: {exc}"
        result.plan = []
        result.detail = []
    finally:
        conn.close()
    if result.status == "ok":
        result.note = ("explained on a read-only connection — "
                       "the query itself was never executed")
    return result


# ---------------------------------------------------------------------------
# Migration files understood as code — read, never applied
# ---------------------------------------------------------------------------

_CREATE_RE = re.compile(
    r"\bCREATE\s+(?:TEMP\s+|TEMPORARY\s+)?TABLE\s+"
    r"(?:IF\s+NOT\s+EXISTS\s+)?[\"'`\[]?([\w\.]+)", re.IGNORECASE)
_ALTER_RE = re.compile(
    r"\bALTER\s+TABLE\s+[\"'`\[]?([\w\.]+)", re.IGNORECASE)
_DROP_RE = re.compile(
    r"\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?[\"'`\[]?([\w\.]+)",
    re.IGNORECASE)
_INDEX_RE = re.compile(
    r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+"
    r"(?:IF\s+NOT\s+EXISTS\s+)?[\"'`\[]?([\w\.]+)", re.IGNORECASE)
_UP_MARKER = re.compile(
    r"--\s*(?:migrate:\s*)?up\b|#\s*migrate:\s*up\b", re.IGNORECASE)
_DOWN_MARKER = re.compile(
    r"--\s*(?:migrate:\s*)?down\b|#\s*migrate:\s*down\b",
    re.IGNORECASE)
_VERSION_RE = re.compile(r"^(\d+)")


@dataclass
class MigrationInfo:
    """One migration file read as code."""

    path: str
    version: str = ""
    order: Optional[int] = None
    layout: str = ""  # migrations-dir | versions-dir | numbered | alembic
    has_up: bool = False
    has_down: bool = False
    creates: List[str] = field(default_factory=list)
    alters: List[str] = field(default_factory=list)
    drops: List[str] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    down_creates: List[str] = field(default_factory=list)
    down_alters: List[str] = field(default_factory=list)
    down_drops: List[str] = field(default_factory=list)
    note: str = ""

    def record(self) -> Dict[str, Any]:
        return {"path": self.path, "version": self.version,
                "order": self.order, "layout": self.layout,
                "has_up": self.has_up, "has_down": self.has_down,
                "creates": list(self.creates),
                "alters": list(self.alters),
                "drops": list(self.drops),
                "indexes": list(self.indexes),
                "down_creates": list(self.down_creates),
                "down_alters": list(self.down_alters),
                "down_drops": list(self.down_drops),
                "note": self.note}


def _tables(pattern: "re.Pattern[str]", text: str) -> List[str]:
    seen: List[str] = []
    for match in pattern.finditer(text):
        name = match.group(1).split(".")[-1]
        if name not in seen:
            seen.append(name)
    return seen


def _split_up_down(text: str) -> Tuple[str, str, bool, bool]:
    """(up text, down text, has_up, has_down) for SQL text."""
    down_match = _DOWN_MARKER.search(text)
    up_match = _UP_MARKER.search(text)
    if down_match is None and up_match is None:
        # No markers: the whole file is the up section.
        return text, "", True, False
    if down_match is not None:
        up_text = text[:down_match.start()]
        if up_match is not None and up_match.start() < down_match.start():
            up_text = text[up_match.end():down_match.start()]
        return up_text, text[down_match.end():], True, True
    return text[up_match.end():], "", True, False


def _split_alembic(text: str) -> Tuple[str, str, bool, bool]:
    """(up text, down text, has_up, has_down) for a .py revision."""
    up_match = re.search(r"def\s+upgrade\s*\(", text)
    down_match = re.search(r"def\s+downgrade\s*\(", text)
    if up_match is None and down_match is None:
        return text, "", False, False
    if up_match is not None and down_match is not None:
        if up_match.start() < down_match.start():
            return (text[up_match.start():down_match.start()],
                    text[down_match.start():], True, True)
        return (text[up_match.start():],
                text[down_match.start():up_match.start()], True, True)
    if up_match is not None:
        return text[up_match.start():], "", True, False
    return "", text[down_match.start():], False, True


#: Creation spellings inside alembic Python (op.create_table etc.).
_PY_CREATE_RE = re.compile(r"create_table\(\s*[\"']([\w\.]+)[\"']")
_PY_DROP_RE = re.compile(r"drop_table\(\s*[\"']([\w\.]+)[\"']")
_PY_ALTER_RE = re.compile(
    r"(?:alter_column|add_column|drop_column)\(\s*[\"']([\w\.]+)[\"']")


def parse_migration(path: Path, display: str = "",
                    layout: str = "") -> MigrationInfo:
    """Read one migration file structurally, as code."""
    info = MigrationInfo(path=display or str(path), layout=layout)
    stem = path.stem
    version_match = _VERSION_RE.match(stem)
    if version_match:
        info.version = version_match.group(1)
        info.order = int(version_match.group(1))
    else:
        info.version = stem
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        info.note = f"the migration could not be read: {exc}"
        return info
    if path.suffix.lower() == ".py":
        up, down, info.has_up, info.has_down = _split_alembic(text)
        for section, prefix in ((up, ""), (down, "down_")):
            for pattern, attr in (
                    (_PY_CREATE_RE, "creates"),
                    (_PY_ALTER_RE, "alters"),
                    (_PY_DROP_RE, "drops"),
                    (_CREATE_RE, "creates"),
                    (_ALTER_RE, "alters"),
                    (_DROP_RE, "drops")):
                target = getattr(info, prefix + attr)
                for name in _tables(pattern, section):
                    if name not in target:
                        target.append(name)
        return info
    up, down, info.has_up, info.has_down = _split_up_down(text)
    info.creates = _tables(_CREATE_RE, up)
    info.alters = _tables(_ALTER_RE, up)
    info.drops = _tables(_DROP_RE, up)
    info.indexes = _tables(_INDEX_RE, up)
    info.down_creates = _tables(_CREATE_RE, down)
    info.down_alters = _tables(_ALTER_RE, down)
    info.down_drops = _tables(_DROP_RE, down)
    return info


def find_migration_files(
        workspace: Any) -> Tuple[List[Tuple[Path, str]], List[str]]:
    """Migration files by layout, in application order.

    Recognised: ``.sql`` files under a ``migrations``
    directory, ``.sql``/``.py`` files under a ``versions``
    directory (alembic), and numbered ``.sql`` files
    anywhere else in the workspace.
    """
    root = Path(workspace)
    found: List[Tuple[Path, str]] = []
    warnings: List[str] = []
    if not root.is_dir():
        return found, warnings
    for candidate in sorted(root.rglob("*")):
        if not candidate.is_file():
            continue
        if any(part in _SKIP_DIRS or part.startswith(".venv")
               for part in candidate.parts):
            continue
        parts = {p.lower() for p in candidate.parts}
        suffix = candidate.suffix.lower()
        layout = ""
        if suffix == ".sql" and "migrations" in parts:
            layout = "migrations-dir"
        elif suffix in (".sql", ".py") and "versions" in parts:
            layout = "alembic" if suffix == ".py" else "versions-dir"
        elif suffix == ".sql" and _VERSION_RE.match(candidate.stem):
            layout = "numbered"
        if not layout:
            continue
        if len(found) >= MAX_SCAN_MIGRATIONS:
            warnings.append(
                f"scan capped at {MAX_SCAN_MIGRATIONS} migration "
                "files; further files were not read")
            break
        found.append((candidate, layout))

    def sort_key(item: Tuple[Path, str]) -> Tuple[int, int, str]:
        candidate = item[0]
        match = _VERSION_RE.match(candidate.stem)
        return (0, int(match.group(1)), candidate.name) if match \
            else (1, 0, candidate.name)

    found.sort(key=sort_key)
    return found, warnings


# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------

@dataclass
class SqlReport:
    """One sql-sight call's whole account."""

    kind: str = "show"  # show | schema | explain | migrations
    status: str = "ok"  # ok | disabled | error
    databases: List[DatabaseSchema] = field(default_factory=list)
    explain: Optional[ExplainResult] = None
    migrations: List[MigrationInfo] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    note: str = ""

    def totals(self) -> Tuple[int, int, int]:
        """(databases, tables, migrations)."""
        return (len(self.databases),
                sum(len(d.tables) for d in self.databases),
                len(self.migrations))

    def record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "status": self.status,
                "databases": [d.record() for d in self.databases],
                "explain": self.explain.record() if self.explain else None,
                "migrations": [m.record() for m in self.migrations],
                "warnings": list(self.warnings),
                "note": self.note}


def _closed(kind: str) -> SqlReport:
    return SqlReport(
        kind=kind, status="disabled",
        note=("sql sight is off (the sql_sight setting), "
              "so no project file was read"))


def _resolve_db(root: Path, target: str) -> Optional[Path]:
    candidate = Path(target)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate if candidate.is_file() else None


def _display(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def sql_sight(
        workspace: Any, mode: str = "show", *,
        db: Optional[str] = None, query: str = "",
        enabled: bool = True,
) -> SqlReport:
    """One SQL account — schemas, one schema, explain, migrations.

    Read-only: databases are opened ``mode=ro`` and
    migration files are only read. A missing workspace
    is an honest ``error`` report. Raises
    :class:`ValueError` for an unknown mode.
    """
    kind = (mode or "show").strip().lower()
    if kind not in ("show", "schema", "explain", "migrations"):
        raise ValueError(f"{USAGE} — unknown mode {mode!r}")
    if not enabled:
        return _closed(kind)
    root = Path(workspace)
    if not root.is_dir():
        return SqlReport(
            kind=kind, status="error",
            note=f"no workspace at {root} — nothing was read")
    report = SqlReport(kind=kind)
    if kind == "migrations":
        files, warnings = find_migration_files(root)
        report.warnings.extend(warnings)
        for path, layout in files:
            if path.stat().st_size > MAX_MIGRATION_BYTES:
                report.warnings.append(
                    f"{_display(root, path)} skipped: over the "
                    f"{MAX_MIGRATION_BYTES}-byte scan cap")
                continue
            report.migrations.append(
                parse_migration(path, _display(root, path), layout))
        report.note = (
            "migrations read as code — none was applied"
            if report.migrations else
            "no migration files in this workspace — migrations "
            "are recognised under a migrations/ or versions/ "
            "directory, or as numbered .sql files")
        return report
    if kind in ("schema", "explain"):
        if not db:
            raise ValueError(f"{USAGE} — this road needs its database")
        target = _resolve_db(root, db)
        if target is None:
            report.status = "error"
            report.note = f"no database file at {db} — nothing was read"
            return report
        if target.suffix.lower() not in DB_EXTENSIONS:
            report.status = "error"
            report.note = (
                f"{db} is not a database file — SQL sight knows "
                "SQLite databases by their .db / .sqlite / "
                ".sqlite3 extensions")
            return report
        display = _display(root, target)
        if kind == "schema":
            report.databases = [read_schema(target, display)]
            report.note = ("read on a read-only connection — "
                           "nothing was written")
            return report
        report.explain = explain_query(target, query, display)
        report.databases = []
        return report
    paths, warnings = find_databases(root)
    report.warnings.extend(warnings)
    for path in paths:
        report.databases.append(read_schema(path, _display(root, path)))
    report.note = (
        "read on read-only connections — nothing was written"
        if report.databases else
        "no SQLite databases in this workspace — databases "
        "are recognised by their .db / .sqlite / .sqlite3 "
        "extensions wherever they land")
    return report


# ---------------------------------------------------------------------------
# Surfaces: the shared parser + formatters
# ---------------------------------------------------------------------------

def parse_sql_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/sql`` arguments into a sql request.

    Grammar::

        /sql
        /sql show
        /sql <db>
        /sql show <db>
        /sql explain <db> <query ...>
        /sql migrations

    Raises :class:`ValueError` on a usage error.
    """
    text = (arguments or "").strip()
    if not text:
        return {"action": "show"}
    tokens = text.split()
    head = tokens[0].lower()
    if head == "show":
        if len(tokens) == 1:
            return {"action": "show"}
        if len(tokens) == 2:
            return {"action": "schema", "db": tokens[1]}
        raise ValueError(f"{USAGE} — show names one database, or none")
    if head == "migrations":
        if len(tokens) != 1:
            raise ValueError(f"{USAGE} — migrations takes no argument")
        return {"action": "migrations"}
    if head == "explain":
        if len(tokens) < 3:
            raise ValueError(
                f"{USAGE} — explain needs a database and a query")
        return {"action": "explain", "db": tokens[1],
                "query": " ".join(tokens[2:])}
    if len(tokens) != 1:
        raise ValueError(f"{USAGE} — name one database, or none")
    return {"action": "schema", "db": tokens[0]}


def format_sql_report(status: Dict[str, Any]) -> str:
    """One sql call's account, from an Agent status mapping."""
    report = status["report"]
    lines = [f"SQL sight ({SQL_SLICE}): {report['kind']} — "
             "workspace databases read-only, migrations as code."]
    for database in report["databases"]:
        tables = database["tables"]
        lines.append(
            f"  {database['path']}: {len(tables)} table(s)/view(s)")
        for table in tables:
            rows = ("row count unknown"
                    if table["row_count"] is None
                    else f"{table['row_count']} row(s)")
            lines.append(
                f"    {table['name']} [{table['kind']}] — "
                f"{len(table['columns'])} column(s), {rows}")
            for column in table["columns"]:
                pk = " PK" if column["pk"] else ""
                lines.append(
                    f"      {column['name']} "
                    f"{column['type'] or '(no type)'}{pk}")
            for fk in table["foreign_keys"]:
                lines.append(
                    f"      FK {fk['from']} -> "
                    f"{fk['table']}.{fk['to']}")
            for index in table["indexes"]:
                lines.append(
                    f"      index {index['name']} on "
                    f"({', '.join(index['columns'])})"
                    f"{' unique' if index['unique'] else ''}")
        if database["note"]:
            lines.append(f"    {database['note']}")
    explain = report.get("explain")
    if explain:
        lines.append(
            f"  Explain [{explain['status']}] on {explain['db']}: "
            f"{explain['query']}")
        for step in explain["plan"]:
            lines.append(f"    plan: {step}")
        if explain["note"]:
            lines.append(f"    {explain['note']}")
    for migration in report["migrations"]:
        lines.append(
            f"  {migration['path']} [{migration['layout']}] "
            f"version {migration['version']} — "
            f"up: {migration['has_up']}, down: {migration['has_down']}; "
            f"creates {migration['creates'] or '[]'}, "
            f"alters {migration['alters'] or '[]'}, "
            f"drops {migration['drops'] or '[]'}")
        if migration["note"]:
            lines.append(f"    {migration['note']}")
    if report["note"]:
        lines.append(f"  {report['note']}")
    for warning in report["warnings"]:
        lines.append(f"  Warning: {warning}")
    lines.append(status["plain_explanation"])
    return "\n".join(lines)


def render_markdown(report: SqlReport) -> str:
    """Render *report* as a human report, from its own record.

    Built from :meth:`SqlReport.totals` and the schema /
    migration records' own accessors, so the rendered
    page is computed from the same values the tests pin.
    """
    data = report.record()
    n_dbs, n_tables, n_migrations = report.totals()
    lines = [
        "# SQL Sight — schemas, explains, migrations as code",
        "",
        f"*Slice {SQL_SLICE} of the All-Features road "
        "(Part III — Code Intelligence). Read-only — "
        "nothing is written, executed or applied by "
        "this report.*",
        "",
        f"**{n_dbs} database(s)**, **{n_tables} "
        f"table(s)/view(s)**, **{n_migrations} "
        "migration(s)**.",
        "",
    ]
    for database in report.databases:
        lines.append(f"## `{database.path}`")
        lines.append("")
        for table in database.tables:
            cols = ", ".join(table.column_names())
            lines.append(
                f"- `{table.name}` [{table.kind}] "
                f"({table.row_count} row(s)): {cols}")
        lines.append("")
    names = [name for database in report.databases
             for name in database.table_names()]
    lines.append("Tables read: " + (", ".join(names) or "none"))
    lines.append("")
    if data["migrations"]:
        lines.append("## Migrations")
        lines.append("")
        for migration in data["migrations"]:
            lines.append(
                f"- `{migration['path']}` "
                f"(version {migration['version']}, "
                f"{migration['layout']}): creates "
                f"{migration['creates']}, alters "
                f"{migration['alters']}, drops "
                f"{migration['drops']}")
        lines.append("")
    if data["explain"]:
        explain = data["explain"]
        lines.append("## Explain")
        lines.append("")
        lines.append(
            f"- [{explain['status']}] `{explain['query']}` "
            f"on `{explain['db']}`: "
            + ("; ".join(explain["plan"]) or explain["note"]))
        lines.append("")
    return "\n".join(lines)
