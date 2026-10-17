from __future__ import annotations

import os
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
# Set DATABASE_PATH to a folder on a persistent disk (e.g. /var/data) so
# saved applications survive redeploys. Defaults to the app folder.
DATABASE_PATH = Path(
    os.getenv("DATABASE_PATH") or (BASE_DIR / "applications.db")
)

DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_connection()

    try:

        connection.execute(
            """
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
        )

        connection.commit()

    finally:

        connection.close()