from __future__ import annotations

import os
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

# ----------------------------------------------------------------------
# Which database?
#
#   DATABASE_URL set  -> PostgreSQL (e.g. a free Neon database). Data
#                        survives restarts and redeploys.
#   not set           -> SQLite file (fine for running on your laptop;
#                        wiped on free hosts whenever they restart).
# ----------------------------------------------------------------------
DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip()

# Some providers hand out "postgres://", but drivers want "postgresql://".
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]

USE_POSTGRES = DATABASE_URL.startswith("postgresql://")

# SQLite only: set DATABASE_PATH to a folder on a persistent disk.
DATABASE_PATH = Path(
    os.getenv("DATABASE_PATH") or (BASE_DIR / "applications.db")
)

if not USE_POSTGRES:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


class _PostgresCursor:
    """Thin wrapper so a psycopg2 cursor offers sqlite-style `lastrowid`."""

    def __init__(self, cursor, lastrowid=None):
        self._cursor = cursor
        self.lastrowid = lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()


class _PostgresConnection:
    """
    Makes a psycopg2 connection behave like the sqlite3 one the rest of the
    tracker code was written for: `?` placeholders, `execute()` on the
    connection, `lastrowid`, and rows that work as dicts.
    """

    def __init__(self, raw):
        self._raw = raw

    def execute(self, sql, params=()):
        import psycopg2.extras

        sql = sql.replace("?", "%s")
        sql = sql.replace(
            "updated_at = CURRENT_TIMESTAMP",
            "updated_at = CURRENT_TIMESTAMP::text",
        )

        is_insert = sql.lstrip().upper().startswith("INSERT")
        if is_insert and "RETURNING" not in sql.upper():
            sql = sql.rstrip().rstrip(";") + " RETURNING id"

        cursor = self._raw.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        cursor.execute(sql, params)

        if is_insert:
            returned = cursor.fetchone()
            return _PostgresCursor(
                cursor, returned["id"] if returned else None
            )

        return _PostgresCursor(cursor)

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()

    def close(self):
        self._raw.close()


def get_connection():
    if USE_POSTGRES:
        import psycopg2

        return _PostgresConnection(
            psycopg2.connect(DATABASE_URL, connect_timeout=15)
        )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    job_url TEXT,
    status TEXT NOT NULL DEFAULT 'Applied',
    applied_date TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

_POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    job_url TEXT,
    status TEXT NOT NULL DEFAULT 'Applied',
    applied_date TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
    updated_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
)
"""


def initialize_database():

    connection = get_connection()

    try:

        connection.execute(
            _POSTGRES_SCHEMA if USE_POSTGRES else _SQLITE_SCHEMA
        )

        connection.commit()

    finally:

        connection.close()
