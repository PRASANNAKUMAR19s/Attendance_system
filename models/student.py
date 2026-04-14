"""
models/student.py — Student model (thin wrapper around FirebaseService)
========================================================================
Provides a model-layer interface for student operations.
The actual data is stored in CSV files (or Firebase when enabled) via
firebase_service.FirebaseService.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from firebase_service import FirebaseService

_svc = FirebaseService()


class Student:
    """Represents a student record."""

    def __init__(self, data: Dict[str, Any]) -> None:
        self.reg_no: str    = data.get("reg_no", "")
        self.name: str      = data.get("name", "")
        self.department: str = data.get("department", "AI&DS")
        self.year: int      = int(data.get("year", 1))
        self.email: str     = data.get("email", "")
        self.phone: str     = data.get("phone", "")

    # ------------------------------------------------------------------
    # Class methods
    # ------------------------------------------------------------------

    @classmethod
    def get_all(cls) -> List["Student"]:
        """Return all registered students."""
        return [cls(s) for s in _svc.get_students()]

    @classmethod
    def get_by_reg_no(cls, reg_no: str) -> Optional["Student"]:
        """Return a student by register number, or None."""
        data = _svc.get_student(reg_no)
        return cls(data) if data else None

    @classmethod
    def register(
        cls,
        reg_no: str,
        name: str,
        department: str = "AI&DS",
        year: int = 1,
        email: str = "",
        phone: str = "",
    ) -> "Student":
        """Register a new student.  Raises ValueError if already exists."""
        existing = _svc.get_student(reg_no)
        if existing:
            raise ValueError(f"Student {reg_no!r} already registered.")
        _svc.add_student(reg_no, name, department, year)
        return cls({"reg_no": reg_no, "name": name, "department": department,
                    "year": year, "email": email, "phone": phone})

    @classmethod
    def delete(cls, reg_no: str) -> bool:
        """Delete a student.  Returns True on success."""
        return _svc.delete_student(reg_no)

    @classmethod
    def update(cls, reg_no: str, data: Dict[str, Any]) -> bool:
        """Update student data.  Returns True on success."""
        return _svc.update_student(reg_no, data)

    @classmethod
    def count(cls) -> int:
        """Return total number of registered students."""
        return len(_svc.get_students())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reg_no": self.reg_no,
            "name": self.name,
            "department": self.department,
            "year": self.year,
            "email": self.email,
            "phone": self.phone,
        }

    def __repr__(self) -> str:
        return f"<Student reg_no={self.reg_no!r} name={self.name!r}>"
