"""
models/user.py — Admin / Tutor user model
==========================================
Wraps the SQLite `users` table.  All password operations use bcrypt.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

import bcrypt

from database import get_db


class User:
    """Represents an admin/tutor user stored in the SQLite database."""

    def __init__(self, row) -> None:
        self.id: int = row["id"]
        self.username: str = row["username"]
        self.role: str = row["role"]
        self.full_name: str = row["full_name"]
        self.email: str = row["email"]
        self.must_reset_password: bool = bool(row["must_reset_password"])
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
    def get_by_email(cls, email: str) -> Optional["User"]:
        """Return a User by email, or None if not found."""
        db = get_db()
        row = db.execute(
            "SELECT * FROM users WHERE email = ? AND is_active = 1",
            (email,),
        ).fetchone()
        return cls(row) if row else None

    @classmethod
    def get_by_identifier(cls, identifier: str) -> Optional["User"]:
        """Return a User by username or email."""
        return cls.get_by_username(identifier) or cls.get_by_email(identifier)

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
    def set_password(cls, user_id: int, plain_password: str) -> bool:
        """Update a user's password hash."""
        password_hash = bcrypt.hashpw(
            plain_password.encode(), bcrypt.gensalt()
        ).decode()
        db = get_db()
        db.execute(
            "UPDATE users SET password_hash = ?, must_reset_password = 0 WHERE id = ?",
            (password_hash, user_id),
        )
        db.commit()
        return True

    @classmethod
    def set_password_reset_required(cls, user_id: int, required: bool = True) -> bool:
        """Mark whether a user must reset their password on next login."""
        db = get_db()
        db.execute(
            "UPDATE users SET must_reset_password = ? WHERE id = ?",
            (1 if required else 0, user_id),
        )
        db.commit()
        return True

    @classmethod
    def create_password_reset_token(
        cls, identifier: str, expires_hours: int = 24
    ) -> tuple[Optional["User"], Optional[str]]:
        """Create a one-time password reset token for a user."""
        user = cls.get_by_identifier(identifier)
        if user is None:
            return None, None

        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = (datetime.utcnow() + timedelta(hours=expires_hours)).isoformat()

        db = get_db()
        db.execute(
            "INSERT INTO password_reset_tokens (user_id, token_hash, expires_at) "
            "VALUES (?, ?, ?)",
            (user.id, token_hash, expires_at),
        )
        db.commit()
        return user, token

    @classmethod
    def consume_password_reset_token(cls, token: str) -> Optional["User"]:
        """Validate and consume a one-time password reset token."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        now = datetime.utcnow().isoformat()
        db = get_db()
        row = db.execute(
            "SELECT u.* FROM password_reset_tokens prt "
            "JOIN users u ON u.id = prt.user_id "
            "WHERE prt.token_hash = ? AND prt.used_at IS NULL AND prt.expires_at > ? "
            "AND u.is_active = 1 "
            "ORDER BY prt.id DESC LIMIT 1",
            (token_hash, now),
        ).fetchone()
        if row is None:
            return None

        db.execute(
            "UPDATE password_reset_tokens SET used_at = ? WHERE token_hash = ? AND used_at IS NULL",
            (now, token_hash),
        )
        db.commit()
        return cls(row)

    @classmethod
    def create(
        cls,
        username: str,
        plain_password: str,
        role: str = "admin",
        full_name: str = "",
        email: str = "",
        must_reset_password: bool = False,
    ) -> "User":
        """Create a new user and return the User object."""
        password_hash = bcrypt.hashpw(
            plain_password.encode(), bcrypt.gensalt()
        ).decode()
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, role, full_name, email, must_reset_password) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (username, password_hash, role, full_name, email, 1 if must_reset_password else 0),
        )
        db.commit()
        return cls.get_by_username(username)  # type: ignore[return-value]

    @classmethod
    def get_all(cls) -> list["User"]:
        """Return all users."""
        db = get_db()
        rows = db.execute("SELECT * FROM users WHERE is_active = 1").fetchall()
        return [cls(row) for row in rows]

    @classmethod
    def delete(cls, username: str) -> bool:
        """Soft-delete a user (set is_active = 0)."""
        db = get_db()
        db.execute("UPDATE users SET is_active = 0 WHERE username = ?", (username,))
        db.commit()
        return True

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} role={self.role!r}>"
