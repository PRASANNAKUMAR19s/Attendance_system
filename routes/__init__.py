"""routes package — Flask Blueprints for the web application."""
from .auth import auth_bp
from .admin import admin_bp

__all__ = ["auth_bp", "admin_bp"]
