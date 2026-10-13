"""API dependencies package."""
from api.dependencies.auth import (
    Role,
    AuthContext,
    get_current_auth,
    require_modify_permission,
)

__all__ = [
    "Role",
    "AuthContext",
    "get_current_auth",
    "require_modify_permission",
]
