"""
Authentication Middleware for Pydance Framework

Middleware for handling authentication, sessions, and authorization.
"""

from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime, timedelta

from pydance.exceptions import HTTPException, Unauthorized, Forbidden

from pydance.auth.core import auth_manager, get_current_user


class AuthMiddleware(HTTPMiddleware):
    """Authentication middleware for handling user authentication"""

    def __init__(self, exclude_paths: Optional[list] = None):
        self.exclude_paths = exclude_paths or ['/login', '/register', '/health']
        self.session_timeout = timedelta(hours=24)

    async def process_request(self, request: Request) -> Request:
        """Process incoming request for authentication"""
        # Skip authentication for excluded paths
        if any(request.path.startswith(path) for path in self.exclude_paths):
            return request

        # Try to get current user
        user = get_current_user(request)
        if user:
            request.user = user
            request.authenticated = True
        else:
            request.user = None
            request.authenticated = False

        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        """Process response (can be used for logging, etc.)"""
        return response


class AdminAuthMiddleware(HTTPMiddleware):
    """Middleware requiring admin privileges"""

    def __init__(self, exclude_paths: Optional[list] = None):
        self.exclude_paths = exclude_paths or ['/login', '/register', '/health', '/admin/login']

    async def process_request(self, request: Request) -> Request:
        """Check for admin authentication"""
        # Skip for excluded paths
        if any(request.path.startswith(path) for path in self.exclude_paths):
            return request

        # Get current user
        user = get_current_user(request)
        if not user:
            raise Unauthorized("Authentication required")

        # Check admin role
        if 'admin' not in user.get('roles', []):
            raise Forbidden("Admin privileges required")

        request.user = user
        request.authenticated = True
        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        """Process response"""
        return response


class SessionMiddleware(HTTPMiddleware):
    """Middleware for handling user sessions"""

    def __init__(self, cookie_name: str = 'session_id', max_age: int = 86400):
        self.cookie_name = cookie_name
        self.max_age = max_age

    async def process_request(self, request: Request) -> Request:
        """Extract session from cookies"""
        session_id = request.cookies.get(self.cookie_name)
        if session_id:
            request.session_id = session_id
            # Get user from session
            user = auth_manager.get_user_from_session(session_id)
            if user:
                request.user = user
                request.authenticated = True
            else:
                request.user = None
                request.authenticated = False
        else:
            request.session_id = None
            request.user = None
            request.authenticated = False

        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        """Set session cookie if needed"""
        if hasattr(request, 'session_id') and request.session_id:
            response.set_cookie(
                self.cookie_name,
                request.session_id,
                max_age=self.max_age,
                httponly=True,
                secure=True,
                samesite='Strict'
            )
        return response


# Convenience middleware instances
auth_middleware = AuthMiddleware()
admin_auth_middleware = AdminAuthMiddleware()
session_middleware = SessionMiddleware()


__all__ = [
    'AuthMiddleware',
    'AdminAuthMiddleware',
    'SessionMiddleware',
    'auth_middleware',
    'admin_auth_middleware',
    'session_middleware'
]
