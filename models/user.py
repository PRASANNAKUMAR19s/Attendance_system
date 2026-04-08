"""
models/user.py — Admin / Tutor user model
==========================================
Wraps the SQLite `users` table.  All password operations use bcrypt.
"""

from __future__ import annotations

from typing import Optional

import bcrypt

from database import get_db


class User:
    """Represents an admin/tutor user stored in the SQLite database."""

    def __init__(self, row) -> None:
        self.id: int         = row["id"]
        self.username: str   = row["username"]
        self.role: str       = row["role"]
        self.full_name: str  = row["full_name"]
        self.email: str      = row["email"]
        self.created_at: str = row["created_at"]
        self.is_active: bool = bool(row["is_active"])

    # ------------------------------------------------------------------
    # Class methods (queries)
    # ------------------------------------------------------------------

    @classmethod
    def get_by_username(cls, username: str) -> Optional["User"]:
        """Return a User by username, or None if not found."""
        db = get_db()
        row = db.execute(
            "SELECT * FROM users WHERE username = ? AND is_active = 1",
            (username,),
        ).fetchone()
        return cls(row) if row else None

    @classmethod
    def get_by_id(cls, user_id: int) -> Optional["User"]:
        """Return a User by primary key, or None if not found."""
        db = get_db()
        row = db.execute(
            "SELECT * FROM users WHERE id = ? AND is_active = 1",
            (user_id,),
        ).fetchone()
        return cls(row) if row else None

    @classmethod
    def verify_password(cls, username: str, plain_password: str) -> Optional["User"]:
        """Return the User if credentials are valid, otherwise None."""
        db = get_db()
        row = db.execute(
            "SELECT * FROM users WHERE username = ? AND is_active = 1",
            (username,),
        ).fetchone()
        if row is None:
            return None
        stored = row["password_hash"].encode()
        if bcrypt.checkpw(plain_password.encode(), stored):
            return cls(row)
        return None

    @classmethod
    def create(
        cls,
        username: str,
        plain_password: str,
        role: str = "admin",
        full_name: str = "",
        email: str = "",
    ) -> "User":
        """Create a new user and return the User object."""
        password_hash = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, role, full_name, email) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, role, full_name, email),
        )
        db.commit()
        return cls.get_by_username(username)  # type: ignore[return-value]

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} role={self.role!r}>"
