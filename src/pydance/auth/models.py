"""
Authentication Models for Pydance Framework

Database models for users, permissions, roles, and sessions.
"""

from typing import Dict, Any, List, Optional
from pydance.db.models.base import BaseModel, Field


class User(BaseModel):
    """User model for authentication"""

    username = Field(str, unique=True, required=True)
    email = Field(str, unique=True, required=True)
    password_hash = Field(str, required=True)
    first_name = Field(str, required=False)
    last_name = Field(str, required=False)
    is_active = Field(bool, default=True)
    is_superuser = Field(bool, default=False)
    created_at = Field(datetime, default=datetime.utcnow)
    updated_at = Field(datetime, default=datetime.utcnow, auto_update=True)
    last_login = Field(datetime, required=False)

    class Meta:
        table_name = "auth_users"

    def __str__(self):
        return f"User({self.username})"

    def set_password(self, password: str):
        """Set user password (will be hashed)"""
        import hashlib
        import secrets
        salt = secrets.token_hex(16)
        self.password_hash = f"{salt}:{hashlib.sha3_256((password + salt).encode()).hexdigest()}"

    def check_password(self, password: str) -> bool:
        """Check if password is correct"""
        try:
            salt, pwdhash = self.password_hash.split(':')
            return pwdhash == hashlib.sha3_256((password + salt).encode()).hexdigest()
        except:
            return False

    def get_full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username


class Permission(BaseModel):
    """Permission model"""

    name = Field(str, unique=True, required=True)
    codename = Field(str, unique=True, required=True)
    description = Field(str, required=False)

    class Meta:
        table_name = "auth_permissions"

    def __str__(self):
        return f"Permission({self.codename})"


class Role(BaseModel):
    """Role model"""

    name = Field(str, unique=True, required=True)
    description = Field(str, required=False)

    class Meta:
        table_name = "auth_roles"

    def __str__(self):
        return f"Role({self.name})"


class UserRole(BaseModel):
    """Many-to-many relationship between users and roles"""

    user_id = Field(int, required=True)
    role_id = Field(int, required=True)

    class Meta:
        table_name = "auth_user_roles"
        unique_together = ["user_id", "role_id"]


class UserPermission(BaseModel):
    """Many-to-many relationship between users and permissions"""

    user_id = Field(int, required=True)
    permission_id = Field(int, required=True)

    class Meta:
        table_name = "auth_user_permissions"
        unique_together = ["user_id", "permission_id"]


class RolePermission(BaseModel):
    """Many-to-many relationship between roles and permissions"""

    role_id = Field(int, required=True)
    permission_id = Field(int, required=True)

    class Meta:
        table_name = "auth_role_permissions"
        unique_together = ["role_id", "permission_id"]


class UserSession(BaseModel):
    """User session model"""

    user_id = Field(int, required=True)
    session_key = Field(str, unique=True, required=True)
    ip_address = Field(str, required=False)
    user_agent = Field(str, required=False)
    expires_at = Field(datetime, required=True)
    created_at = Field(datetime, default=datetime.utcnow)
    is_active = Field(bool, default=True)

    class Meta:
        table_name = "auth_user_sessions"

    def __str__(self):
        return f"Session({self.session_key[:8]}...)"

    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at


class AuthToken(BaseModel):
    """Authentication token model"""

    user_id = Field(int, required=True)
    token_key = Field(str, unique=True, required=True)
    token_type = Field(str, default="access")  # access, refresh
    expires_at = Field(datetime, required=True)
    created_at = Field(datetime, default=datetime.utcnow)
    is_active = Field(bool, default=True)
    scope = Field(str, required=False)  # JSON string of scopes

    class Meta:
        table_name = "auth_tokens"

    def __str__(self):
        return f"Token({self.token_key[:8]}...)"

    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.utcnow() > self.expires_at

    def has_scope(self, scope: str) -> bool:
        """Check if token has specific scope"""
        if not self.scope:
            return False
        try:
            scopes = self.scope.split(',')
            return scope in scopes
        except:
            return False


# Convenience instances for type hints
__all__ = [
    'User',
    'Permission',
    'Role',
    'UserRole',
    'UserPermission',
    'RolePermission',
    'UserSession',
    'AuthToken'
]

