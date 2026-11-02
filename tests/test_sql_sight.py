"""Tests for M-065 — SQL and data sight.

TIER: integration

Workspace-local SQLite databases are read through
read-only (mode=ro) connections: schemas from
sqlite_master + PRAGMA introspection, EXPLAIN for
SELECT-shaped queries only (explained, never executed;
write-shaped statements refused before anything runs),
and migration files read structurally as code, never
applied. Every test builds a real throwaway SQLite
database with sqlite3 or a real migration fixture tree.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from mythic_agent.tools import sql_sight as ss
from mythic_agent.tools.sql_sight import (
    PLAIN_EXPLANATION,
    SQL_SLICE,
    USAGE,
    explain_query,
    find_databases,
    find_migration_files,
    format_sql_report,
    is_explainable,
    parse_migration,
    parse_sql_args,
    read_schema,
    render_markdown,
    sql_sight,
)


def _make_db(path: Path) -> Path:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE authors (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            pen_name TEXT DEFAULT 'anon'
        );
        CREATE TABLE books (
            id INTEGER PRIMARY KEY,
            author_id INTEGER NOT NULL REFERENCES authors(id),
            title TEXT NOT NULL
        );
        CREATE UNIQUE INDEX idx_books_title ON books(title);
        CREATE INDEX idx_books_author ON books(author_id);
        CREATE VIEW book_titles AS SELECT title FROM books;
        INSERT INTO authors (id, name) VALUES (1, 'Volmarr');
        INSERT INTO books (id, author_id, title)
            VALUES (1, 1, 'Rune-Keys'), (2, 1, 'The Guide');
        """)
    conn.commit()
    conn.close()
    return path


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    _make_db(tmp_path / "library.db")
    data = tmp_path / "data"
    data.mkdir()
    _make_db(data / "extra.sqlite3")
    mig = tmp_path / "migrations"
    mig.mkdir()
    (mig / "001_create_users.sql").write_text(
        "-- migrate:up\n"
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);\n"
        "CREATE INDEX idx_users_name ON users(name);\n"
        "-- migrate:down\n"
        "DROP TABLE users;\n", encoding="utf-8")
    (mig / "002_add_books.sql").write_text(
        "CREATE TABLE books (id INTEGER PRIMARY KEY);\n"
        "ALTER TABLE users ADD COLUMN email TEXT;\n",
        encoding="utf-8")
    versions = tmp_path / "alembic" / "versions"
    versions.mkdir(parents=True)
    (versions / "a1b2_add_tags.py").write_text(
        '"""Add tags."""\n\n'
        "def upgrade():\n"
        "    op.create_table('tags', sa.Column('id', sa.Integer))\n\n"
        "def downgrade():\n"
        "    op.drop_table('tags')\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("not sql", encoding="utf-8")
    return tmp_path


def _db_bytes(path: Path) -> tuple[bytes, int]:
    return path.read_bytes(), path.stat().st_mtime_ns


# -- schema reading ------------------------------------------------------------

def test_find_databases_by_extension(project: Path):
    found, warnings = find_databases(project)
    assert {p.name for p in found} == {"library.db", "extra.sqlite3"}
    assert warnings == []


def test_schema_reads_tables_columns_types_and_pk(project: Path):
    schema = read_schema(project / "library.db", "library.db")
    assert schema.note == ""
    by_name = {t.name: t for t in schema.tables}
    assert set(by_name) == {"authors", "books", "book_titles"}
    authors = by_name["authors"]
    cols = {c.name: c for c in authors.columns}
    assert cols["id"].type == "INTEGER" and cols["id"].pk == 1
    assert cols["name"].notnull is True
    assert cols["pen_name"].default == "'anon'"
    assert authors.row_count == 1
    assert by_name["books"].row_count == 2
    assert by_name["book_titles"].kind == "view"


def test_schema_reads_foreign_keys_and_indexes(project: Path):
    schema = read_schema(project / "library.db", "library.db")
    books = {t.name: t for t in schema.tables}["books"]
    assert len(books.foreign_keys) == 1
    fk = books.foreign_keys[0]
    assert (fk.table, fk.from_column, fk.to_column) == \
        ("authors", "author_id", "id")
    by_index = {i.name: i for i in books.indexes}
    assert by_index["idx_books_title"].unique is True
    assert by_index["idx_books_title"].columns == ("title",)
    assert by_index["idx_books_author"].unique is False


def test_schema_of_a_non_database_is_honest(tmp_path: Path):
    fake = tmp_path / "fake.db"
    fake.write_text("this is not sqlite", encoding="utf-8")
    schema = read_schema(fake, "fake.db")
    assert schema.tables == []
    assert "could not" in schema.note


def test_readonly_connection_itself_refuses_writes(project: Path):
    db = project / "library.db"
    conn = ss._connect_readonly(db)
    with pytest.raises(sqlite3.OperationalError):
        conn.execute(
            "INSERT INTO authors (id, name) VALUES (9, 'X')")
    conn.close()


# -- explain -------------------------------------------------------------------

def test_is_explainable_accepts_select_shapes():
    assert is_explainable("SELECT * FROM books")[0] is True
    assert is_explainable("select title from books")[0] is True
    assert is_explainable(
        "WITH x AS (SELECT 1) SELECT * FROM x")[0] is True


def test_is_explainable_refuses_writes_and_friends():
    for sql in ("INSERT INTO books VALUES (3, 1, 'X')",
                "UPDATE books SET title = 'X'",
                "DELETE FROM books",
                "DROP TABLE books",
                "CREATE TABLE x (id INTEGER)",
                "PRAGMA table_info(books)",
                "WITH x AS (SELECT 1) DELETE FROM books",
                ""):
        ok, reason = is_explainable(sql)
        assert ok is False and reason


def test_explain_returns_a_plan_without_executing(project: Path):
    db = project / "library.db"
    result = explain_query(
        db, "SELECT title FROM books WHERE author_id = 1",
        "library.db")
    assert result.status == "ok"
    assert result.plan  # EXPLAIN QUERY PLAN rows
    assert result.detail  # EXPLAIN opcode rows
    assert "never executed" in result.note
    schema = read_schema(db, "library.db")
    assert {t.name: t for t in schema.tables}["books"].row_count == 2


def test_explain_refuses_a_write_and_changes_nothing(project: Path):
    db = project / "library.db"
    before = _db_bytes(db)
    result = explain_query(db, "DELETE FROM books", "library.db")
    assert result.status == "refused"
    assert "refused" in result.note
    assert _db_bytes(db) == before


def test_explain_names_a_bad_query(project: Path):
    result = explain_query(
        project / "library.db", "SELECT nope FROM nowhere",
        "library.db")
    assert result.status == "error"
    assert "could not be explained" in result.note


# -- migrations ------------------------------------------------------------------

def test_find_migrations_recognises_layouts_in_order(project: Path):
    found, _ = find_migration_files(project)
    names = [p.name for p, _ in found]
    assert names == ["001_create_users.sql", "002_add_books.sql",
                     "a1b2_add_tags.py"]
    layouts = {p.name: layout for p, layout in found}
    assert layouts["001_create_users.sql"] == "migrations-dir"
    assert layouts["a1b2_add_tags.py"] == "alembic"


def test_parse_sql_migration_up_down_and_tables(project: Path):
    info = parse_migration(
        project / "migrations" / "001_create_users.sql",
        "migrations/001_create_users.sql", "migrations-dir")
    assert info.version == "001" and info.order == 1
    assert info.has_up is True and info.has_down is True
    assert info.creates == ["users"]
    assert info.indexes == ["idx_users_name"]
    assert info.down_drops == ["users"]


def test_parse_markerless_migration_is_all_up(project: Path):
    info = parse_migration(
        project / "migrations" / "002_add_books.sql",
        "migrations/002_add_books.sql", "migrations-dir")
    assert info.version == "002" and info.order == 2
    assert info.has_up is True and info.has_down is False
    assert info.creates == ["books"]
    assert info.alters == ["users"]
    assert info.drops == []


def test_parse_alembic_revision(project: Path):
    info = parse_migration(
        project / "alembic" / "versions" / "a1b2_add_tags.py",
        "alembic/versions/a1b2_add_tags.py", "alembic")
    assert info.version == "a1b2_add_tags"
    assert info.order is None
    assert info.has_up is True and info.has_down is True
    assert info.creates == ["tags"]
    assert info.down_drops == ["tags"]


# -- the report roads ----------------------------------------------------------

def test_show_reads_every_database_schema(project: Path):
    report = sql_sight(project)
    assert report.status == "ok" and report.kind == "show"
    n_dbs, n_tables, _ = report.totals()
    assert n_dbs == 2 and n_tables == 6
    assert "read-only" in report.note


def test_show_on_a_database_less_workspace_says_so(tmp_path: Path):
    report = sql_sight(tmp_path)
    assert report.databases == []
    assert "no SQLite databases" in report.note


def test_schema_road_reads_one_database(project: Path):
    report = sql_sight(project, "schema", db="library.db")
    assert len(report.databases) == 1
    assert report.databases[0].table_names() == \
        ("authors", "book_titles", "books")


def test_schema_road_names_missing_and_non_db(project: Path):
    missing = sql_sight(project, "schema", db="gone.db")
    assert missing.status == "error"
    assert "no database file" in missing.note
    not_db = sql_sight(project, "schema", db="notes.txt")
    assert not_db.status == "error"
    assert "not a database file" in not_db.note


def test_explain_road(project: Path):
    report = sql_sight(
        project, "explain", db="library.db",
        query="SELECT * FROM authors")
    assert report.explain is not None
    assert report.explain.status == "ok"
    assert report.explain.plan


def test_migrations_road(project: Path):
    report = sql_sight(project, "migrations")
    assert len(report.migrations) == 3
    assert [m.version for m in report.migrations] == \
        ["001", "002", "a1b2_add_tags"]
    assert "never applied" not in report.note  # wording: 'none was applied'
    assert "none was applied" in report.note


def test_migrations_road_on_a_migration_less_workspace(tmp_path: Path):
    report = sql_sight(tmp_path, "migrations")
    assert report.migrations == []
    assert "no migration files" in report.note


def test_disabled_road_reads_nothing(project: Path):
    report = sql_sight(project, enabled=False)
    assert report.status == "disabled"
    assert report.databases == []
    assert "no project file was read" in report.note


def test_missing_workspace_and_unknown_mode(tmp_path: Path):
    report = sql_sight(tmp_path / "nope")
    assert report.status == "error"
    assert "no workspace" in report.note
    with pytest.raises(ValueError):
        sql_sight(tmp_path, "sideways")


def test_sql_sight_never_writes_anything(project: Path):
    db = project / "library.db"
    before_hash = hashlib.sha256(db.read_bytes()).hexdigest()
    before = {p: p.read_bytes()
              for p in project.rglob("*") if p.is_file()}
    sql_sight(project)
    sql_sight(project, "schema", db="library.db")
    sql_sight(project, "explain", db="library.db",
              query="SELECT * FROM books")
    sql_sight(project, "explain", db="library.db",
              query="DROP TABLE books")
    sql_sight(project, "migrations")
    after = {p: p.read_bytes()
             for p in project.rglob("*") if p.is_file()}
    assert before == after
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before_hash
    for forbidden in ("apply_migration", "execute_query",
                      "write_schema", "run_migration"):
        assert not hasattr(ss, forbidden)


# -- surfaces ------------------------------------------------------------------

def test_parse_sql_args_grammar():
    assert parse_sql_args("") == {"action": "show"}
    assert parse_sql_args("show") == {"action": "show"}
    assert parse_sql_args("library.db") == {
        "action": "schema", "db": "library.db"}
    assert parse_sql_args("show library.db") == {
        "action": "schema", "db": "library.db"}
    assert parse_sql_args("migrations") == {"action": "migrations"}
    assert parse_sql_args("explain library.db SELECT * FROM books") == {
        "action": "explain", "db": "library.db",
        "query": "SELECT * FROM books"}
    for bad in ("show a.db b.db", "migrations extra",
                "explain onlydb", "a.db b.db"):
        with pytest.raises(ValueError) as excinfo:
            parse_sql_args(bad)
        assert "Usage" in str(excinfo.value)


def test_format_report_names_schema_explain_and_migrations(
        project: Path):
    report = sql_sight(project)
    text = format_sql_report({
        "report": report.record(),
        "plain_explanation": PLAIN_EXPLANATION})
    assert SQL_SLICE in text
    assert "authors" in text
    assert "FK author_id -> authors.id" in text
    assert PLAIN_EXPLANATION in text
    mig = format_sql_report({
        "report": sql_sight(project, "migrations").record(),
        "plain_explanation": PLAIN_EXPLANATION})
    assert "001_create_users.sql" in mig
    assert "users" in mig


def test_render_markdown_uses_the_reports_own_totals(project: Path):
    report = sql_sight(project)
    page = render_markdown(report)
    n_dbs, n_tables, _ = report.totals()
    assert f"**{n_dbs} database(s)**" in page
    assert f"**{n_tables} table(s)/view(s)**" in page
    assert "authors" in page
    assert USAGE.split(":")[0] == "Usage"


def _bare_agent(root: Path, config=None):
    from mythic_agent.agents.llm import Agent

    agent = Agent.__new__(Agent)
    agent.project_root = root
    agent.config = config or {}
    agent._session_store = None
    agent.session_id = None
    return agent


def test_agent_surfaces(project: Path):
    agent = _bare_agent(project)
    status = agent.sql_sight()
    assert status["report"]["status"] == "ok"
    assert len(status["report"]["databases"]) == 2
    one = agent.sql_sight("schema", db="library.db")
    assert len(one["report"]["databases"][0]["tables"]) == 3
    mig = agent.sql_sight("migrations")
    assert len(mig["report"]["migrations"]) == 3


def test_agent_respects_the_config_switch(project: Path):
    agent = _bare_agent(project, {"sql_sight": False})
    status = agent.sql_sight()
    assert status["report"]["status"] == "disabled"
    assert status["report"]["databases"] == []


def test_terminal_road(project: Path):
    from mythic_agent.terminal import _slash

    agent = _bare_agent(project)
    handled, _, text = _slash(agent, "/sql")
    assert handled and "SQL sight (M-065)" in text
    handled, _, text = _slash(agent, "/sql library.db")
    assert handled and "authors" in text
    handled, _, text = _slash(
        agent, "/sql explain library.db SELECT * FROM books")
    assert handled and "plan:" in text
    handled, _, text = _slash(agent, "/sql migrations")
    assert handled and "001_create_users.sql" in text
    handled, _, text = _slash(agent, "/sql a.db b.db")
    assert handled and "Usage" in text


def test_setting_lives_in_defaults_and_catalogue():
    import yaml

    root = Path(__file__).resolve().parents[1]
    defaults = yaml.safe_load(
        (root / "mythic_agent/data/config_defaults.yaml").read_text(
            encoding="utf-8"))
    assert defaults["sql_sight"] is True
    catalogue = yaml.safe_load(
        (root / "mythic_agent/data/config_catalog.yaml").read_text(
            encoding="utf-8"))
    entries = [s for s in catalogue["settings"]
               if s["name"] == "sql_sight"]
    assert len(entries) == 1
    assert entries[0]["id"] == "S-55"
    assert ss.enabled_from_config({}) is True
    assert ss.enabled_from_config({"sql_sight": False}) is False
    assert ss.enabled_from_config(None) is True


def test_config_catalogue_carries_the_setting():
    from mythic_agent.core.config_catalog import load_catalog

    catalog = load_catalog()
    entry = [s for s in catalog.settings
             if s.name == "sql_sight"]
    assert len(entry) == 1
    assert entry[0].id == "S-55"


def test_gap_audit_has_no_m065_row_recorded():
    # Checked at build time (M-064's pattern): no census
    # gap row is owned by M-065, so no module_kind flip
    # exists to make for this slice.
    import yaml

    root = Path(__file__).resolve().parents[1]
    audit = yaml.safe_load(
        (root / "mythic_agent/data/gap_audit.yaml").read_text(
            encoding="utf-8"))
    assert [r for r in audit["rows"] if r["slice"] == "M-065"] == []
