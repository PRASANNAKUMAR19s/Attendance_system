"""
database.py — SQLite database setup and initialisation
=======================================================
Manages the SQLite database used by the Flask web application for:
  - Admin user accounts

Student / attendance data continues to use the existing CSV / Firebase
backend via firebase_service.FirebaseService.

Usage:
    from database import init_db, get_db
    init_db(app)          # called once at app startup
    db = get_db()         # returns a sqlite3.Connection for the current request
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Optional

import bcrypt
from flask import Flask, g

import config as _config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'admin',
    full_name     TEXT    NOT NULL DEFAULT '',
    email         TEXT    NOT NULL DEFAULT '',
    must_reset_password INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    is_active     INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    token_hash TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    expires_at  TEXT    NOT NULL,
    used_at    TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_hash
    ON password_reset_tokens (token_hash);
"""


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------


def get_db() -> sqlite3.Connection:
    """Return the per-request SQLite connection (creates it if needed)."""
    if "db" not in g:
        g.db = sqlite3.connect(
            _config.DATABASE_PATH,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception: Optional[Exception] = None) -> None:
    """Close the per-request SQLite connection."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------


def _create_default_tutor(db: sqlite3.Connection) -> None:
    """Create the default tutor account if no users exist yet."""
    cursor = db.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    if count > 0:
        return

    username = _config.TUTOR_USERNAME
    # Use the hashed password from config if provided; otherwise hash the plain default.
    stored_hash: str = _config.TUTOR_PASSWORD_HASH
    if not stored_hash:
        plain = _config.TUTOR_PASSWORD
        stored_hash = bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

    db.execute(
        "INSERT INTO users (username, password_hash, role, full_name, must_reset_password) "
        "VALUES (?, ?, ?, ?, 0)",
        (username, stored_hash, "tutor", "Administrator"),
    )
    db.commit()
    logger.info("Created default tutor user: %s with role: tutor", username)


def _ensure_user_columns(db: sqlite3.Connection) -> None:
    """Add new columns to legacy users tables when needed."""
    columns = {row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()}
    if "must_reset_password" not in columns:
        db.execute(
            "ALTER TABLE users ADD COLUMN must_reset_password INTEGER NOT NULL DEFAULT 0"
        )
        db.commit()


def init_db(app: Flask) -> None:
    """Initialise the database schema and register teardown handlers."""
    app.teardown_appcontext(close_db)

    with app.app_context():
        db = sqlite3.connect(_config.DATABASE_PATH)
        db.row_factory = sqlite3.Row
        try:
            db.executescript(_SCHEMA)
            db.commit()
            _ensure_user_columns(db)
            _create_default_tutor(db)
        finally:
            db.close()

    logger.info("Database initialised at %s", _config.DATABASE_PATH)
