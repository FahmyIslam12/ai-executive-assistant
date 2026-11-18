"""The SQLite database: one file (data/assistant.db) that holds all our data.

SQLite is built into Python. There is no server: the whole database is a
single file on this computer, ignored by Git so it never goes online.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_FILE = Path("data/assistant.db")

# The old JSON files. Their data is moved into the database once, and
# then they are renamed (not deleted) so a backup always remains.
OLD_TASKS_FILE = Path("data/tasks.json")
OLD_MEMORY_FILE = Path("data/memory.json")

# CREATE TABLE IF NOT EXISTS: create each table only the first time.
SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE  -- 'BJIT' and 'bjit' are the same
);

CREATE TABLE IF NOT EXISTS applications (
    id             INTEGER PRIMARY KEY,
    company_id     INTEGER NOT NULL REFERENCES companies(id),  -- foreign key
    role           TEXT NOT NULL,
    status         TEXT NOT NULL CHECK (status IN
                   ('saved', 'applied', 'interview', 'offer', 'rejected', 'no response')),
    source         TEXT NOT NULL CHECK (source IN ('Email', 'BDJobs', 'LinkedIn', 'Other')),
    applied_date   TEXT,          -- dates are stored as text: 2026-11-18
    contact_email  TEXT,
    job_link       TEXT,
    notes          TEXT,
    follow_up_date TEXT,
    created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS status_history (
    id             INTEGER PRIMARY KEY,
    application_id INTEGER NOT NULL REFERENCES applications(id),
    old_status     TEXT,          -- empty for the very first status
    new_status     TEXT NOT NULL,
    changed_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id             TEXT PRIMARY KEY,
    title          TEXT NOT NULL,
    completed      INTEGER NOT NULL DEFAULT 0,   -- SQLite has no True/False: 0 or 1
    due_date       TEXT,
    application_id INTEGER REFERENCES applications(id)  -- optional link
);

CREATE TABLE IF NOT EXISTS messages (
    id            INTEGER PRIMARY KEY,
    role          TEXT NOT NULL,
    content       TEXT NOT NULL,
    email_related INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL
);

-- Links a Gmail draft to the job it applies for, so pressing Send can
-- record the application. Removed when the draft is sent or cancelled.
CREATE TABLE IF NOT EXISTS draft_links (
    draft_id      TEXT PRIMARY KEY,
    company       TEXT NOT NULL,
    role          TEXT NOT NULL,
    contact_email TEXT,
    job_link      TEXT
);
"""

_ready = False


def now() -> str:
    """The current date and time as text, e.g. 2026-11-18T14:30:00."""
    return datetime.now().isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    """Open the database (creating it and its tables the first time)."""
    global _ready
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row  # rows can be read like row["title"]
    connection.execute("PRAGMA foreign_keys = ON")  # enforce the ID links

    if not _ready:
        connection.executescript(SCHEMA)
        _move_old_json_data(connection)
        _ready = True

    return connection


def _table_is_empty(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def _move_old_json_data(connection: sqlite3.Connection) -> None:
    """Move tasks and memory from the old JSON files, once, safely.

    Safety rules:
    - only if the table is still empty (so it can never run twice)
    - all rows are added in one transaction: everything or nothing
    - the JSON file is renamed to *.migrated, never deleted
    """
    if OLD_TASKS_FILE.exists() and _table_is_empty(connection, "tasks"):
        tasks = json.loads(OLD_TASKS_FILE.read_text(encoding="utf-8"))
        with connection:  # a transaction: commit all, or undo all on error
            for task in tasks:
                connection.execute(
                    "INSERT INTO tasks (id, title, completed, due_date) "
                    "VALUES (?, ?, ?, ?)",
                    (task["id"], task["title"], int(task["completed"]), task.get("due_date")),
                )
        moved = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if moved == len(tasks):  # check the counts before renaming
            OLD_TASKS_FILE.rename(OLD_TASKS_FILE.with_suffix(".json.migrated"))

    if OLD_MEMORY_FILE.exists() and _table_is_empty(connection, "messages"):
        try:
            old = json.loads(OLD_MEMORY_FILE.read_text(encoding="utf-8"))
        except ValueError:
            old = []
        conversation = [m for m in old if m.get("role") in ("user", "assistant")]
        with connection:
            for message in conversation:
                connection.execute(
                    "INSERT INTO messages (role, content, email_related, created_at) "
                    "VALUES (?, ?, 0, ?)",
                    (message["role"], message.get("content") or "", now()),
                )
        OLD_MEMORY_FILE.rename(OLD_MEMORY_FILE.with_suffix(".json.migrated"))
