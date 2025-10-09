"""
Core Authentication Module for Pydance Framework

Provides authentication management, user sessions, and security decorators.
"""

import asyncio
import hashlib
import hmac
import secrets
import time
from typing import Dict, Any, Optional, Callable, Awaitable
from functools import wraps
from datetime import datetime, timedelta

from pydance.http.request import Request
from pydance.http.response import Response
from pydance.exceptions import HTTPException, Unauthorized, Forbidden


class AuthManager:
    """Authentication manager for user authentication and session handling"""

    def __init__(self):
        self.users = {}
        self.sessions = {}
        self.tokens = {}
        self.secret_key = secrets.token_hex(32)

    def hash_password(self, password: str) -> str:
        """Hash password using SHA3"""
        salt = secrets.token_hex(16)
        pwdhash = hashlib.sha3_256((password + salt).encode()).hexdigest()
        return f"{salt}:{pwdhash}"

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            salt, pwdhash = hashed.split(':')
            return pwdhash == hashlib.sha3_256((password + salt).encode()).hexdigest()
        except:
            return False

    def create_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Create a new user"""
        if username in self.users:
            raise ValueError("User already exists")

        user = {
            'id': len(self.users) + 1,
            'username': username,
            'email': email,
            'password_hash': self.hash_password(password),
            'created_at': datetime.utcnow(),
            'is_active': True,
            'roles': ['user']
        }

        self.users[username] = user
        return user

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username and password"""
        user = self.users.get(username)
        if not user or not user['is_active']:
            return None

        if not self.verify_password(password, user['password_hash']):
            return None

        return user

    def create_session(self, user_id: int) -> str:
        """Create a new session for user"""
        session_id = secrets.token_hex(32)
        self.sessions[session_id] = {
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=24)
        }
        return session_id

    def get_user_from_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user from session ID"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        if datetime.utcnow() > session['expires_at']:
            del self.sessions[session_id]
            return None

        user_id = session['user_id']
        for user in self.users.values():
            if user['id'] == user_id:
                return user

        return None

    def create_token(self, user_id: int, expires_in: int = 3600) -> str:
        """Create JWT-like token"""
        import jwt
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            import jwt
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except:
            return None

    def get_current_user(self, request: Request) -> Optional[Dict[str, Any]]:
        """Get current user from request"""
        # Try token first
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = self.verify_token(token)
            if payload:
                user_id = payload.get('user_id')
                for user in self.users.values():
                    if user['id'] == user_id:
                        return user

        # Try session
        session_id = request.cookies.get('session_id')
        if session_id:
            return self.get_user_from_session(session_id)

        return None

    def login_required(self, func: Callable) -> Callable:
        """Decorator to require authentication"""
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user = self.get_current_user(request)
            if not user:
                raise Unauthorized("Authentication required")
            request.user = user
            return await func(request, *args, **kwargs)
        return wrapper

    def require_role(self, role: str) -> Callable:
        """Decorator to require specific role"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(request: Request, *args, **kwargs):
                user = self.get_current_user(request)
                if not user:
                    raise Unauthorized("Authentication required")

                if role not in user.get('roles', []):
                    raise Forbidden("Insufficient permissions")

                request.user = user
                return await func(request, *args, **kwargs)
            return wrapper
        return decorator


# Global auth manager instance
auth_manager = AuthManager()


def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get current authenticated user"""
    return auth_manager.get_current_user(request)


def login_required(func: Callable) -> Callable:
    """Decorator to require authentication for a route"""
    return auth_manager.login_required(func)


def permission_required(permission: str) -> Callable:
    """Decorator to require specific permission"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user = get_current_user(request)
            if not user:
                raise Unauthorized("Authentication required")

            # Simple permission check - in real app, this would be more sophisticated
            if permission not in ['read', 'write', 'admin']:
                raise Forbidden("Unknown permission")

            if permission == 'admin' and 'admin' not in user.get('roles', []):
                raise Forbidden("Admin permission required")

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def role_required(role: str) -> Callable:
    """Decorator to require specific role"""
    return auth_manager.require_role(role)


# Convenience functions
def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with username and password"""
    return auth_manager.authenticate_user(username, password)


def create_user(username: str, email: str, password: str) -> Dict[str, Any]:
    """Create a new user"""
    return auth_manager.create_user(username, email, password)


def create_session(user_id: int) -> str:
    """Create a new session"""
    return auth_manager.create_session(user_id)


def create_token(user_id: int) -> str:
    """Create authentication token"""
    return auth_manager.create_token(user_id)

