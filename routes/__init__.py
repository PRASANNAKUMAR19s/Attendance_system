"""routes package — Flask Blueprints for the web application."""
from .auth import auth_bp
from .faculty import faculty_bp
from .student_portal import student_portal_bp
from .api_routes import api_bp

__all__ = ["auth_bp", "faculty_bp", "student_portal_bp", "api_bp"]
