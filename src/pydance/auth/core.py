
from pydance.utils.logging import get_logger
"""
Core Authentication Module for Pydance Framework

Provides authentication management, user sessions, and security decorators.
Enhanced with modern security features like OAuth2, MFA, and advanced session management.
"""

import asyncio
import hashlib
import hmac
import secrets
import time
import logging
from typing import Dict, Any, Optional, Callable, Awaitable, List
from functools import wraps
from datetime import datetime, timedelta
import json
import base64

from pydance.http.request import Request
from pydance.exceptions import HTTPException, Unauthorized, Forbidden, RateLimitExceeded
from pydance.config.settings import settings
from pydance.events import get_event_bus

logger = get_logger(__name__)


class AuthManager:
    """Authentication manager for user authentication and session handling"""

    def __init__(self):
        self.users = {}
        self.sessions = {}
        self.tokens = {}
        # CRITICAL FIX: Use secret key from settings instead of random
        self.secret_key = getattr(settings, 'SECRET_KEY', secrets.token_hex(32))
        # Rate limiting for authentication attempts
        self.login_attempts = {}
        self.max_login_attempts = 5
        self.lockout_duration = timedelta(minutes=15)

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt for security"""
        import bcrypt
        salt = bcrypt.gensalt(rounds=12)  # Use 12 rounds for better security
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        if hashed.startswith('$2b$'):  # bcrypt hash
            import bcrypt
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        elif hashed.startswith('pbkdf2:'):  # Custom PBKDF2 hash
            _, rounds_str, salt, pwdhash = hashed.split(':')
            rounds = int(rounds_str)
            # Verify using same parameters
            new_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), rounds)
            return new_hash.hex() == pwdhash
        else:
            # Legacy SHA3 format - still support for backward compatibility
            salt, pwdhash = hashed.split(':')
            return pwdhash == hashlib.sha3_256((password + salt).encode()).hexdigest()

    def validate_password_strength(self, password: str) -> List[str]:
        """Validate password strength"""
        errors = []

        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")

        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")

        # Check for common passwords
        common_passwords = ['password', '123456', 'password123', 'admin', 'qwerty']
        if password.lower() in common_passwords:
            errors.append("Password is too common")

        return errors

    def create_user(self, username: str, email: str, password: str, **kwargs) -> Dict[str, Any]:
        """Create a new user with enhanced validation"""
        if username in self.users:
            raise ValueError("User already exists")

        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")

        # Validate username
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValueError("Username can only contain letters, numbers, and underscores")

        # Validate password strength
        password_errors = self.validate_password_strength(password)
        if password_errors:
            raise ValueError(f"Password validation failed: {'; '.join(password_errors)}")

        user = {
            'id': len(self.users) + 1,
            'username': username,
            'email': email,
            'password_hash': self.hash_password(password),
            'created_at': datetime.utcnow(),
            'is_active': kwargs.get('is_active', True),
            'is_verified': kwargs.get('is_verified', False),
            'roles': kwargs.get('roles', ['user']),
            'profile': kwargs.get('profile', {}),
            'preferences': kwargs.get('preferences', {}),
            'last_login': None,
            'login_count': 0,
            'failed_login_count': 0,
            'locked_until': None,
            'mfa_enabled': False,
            'mfa_secret': None
        }

        self.users[username] = user

        # Audit log
        self.audit_log('user_created', user['id'], {'username': username, 'email': email})

        # Emit user created event
        asyncio.create_task(self._emit_user_event('user_created', user))

        return user

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username and password"""
        # CRITICAL FIX: Add rate limiting to prevent brute force attacks
        if not self._check_login_rate_limit(username):
            logger.warning(f"Login rate limit exceeded for user: {username}")
            raise RateLimitExceeded("Too many login attempts. Please try again later.")

        user = self.users.get(username)
        if not user or not user['is_active']:
            self._record_failed_login(username)
            return None

        if not self.verify_password(password, user['password_hash']):
            self._record_failed_login(username)
            return None

        # Successful login - reset rate limiting
        self._reset_login_attempts(username)
        logger.info(f"Successful login for user: {username}")
        return user

    def _check_login_rate_limit(self, username: str) -> bool:
        """Check if login attempts exceed rate limit"""
        current_time = datetime.utcnow()
        attempts = self.login_attempts.get(username, [])

        # Remove old attempts outside the lockout window
        attempts = [attempt for attempt in attempts if current_time - attempt < self.lockout_duration]

        # Check if user is currently locked out
        if len(attempts) >= self.max_login_attempts:
            return False

        return True

    def _record_failed_login(self, username: str):
        """Record a failed login attempt"""
        current_time = datetime.utcnow()
        if username not in self.login_attempts:
            self.login_attempts[username] = []

        self.login_attempts[username].append(current_time)
        logger.warning(f"Failed login attempt for user: {username}")

    def _reset_login_attempts(self, username: str):
        """Reset login attempts after successful login"""
        if username in self.login_attempts:
            del self.login_attempts[username]

    def create_session(self, user_id: int) -> str:
        """Create a new session for user"""
        session_id = secrets.token_hex(32)
        current_time = datetime.utcnow()

        # CRITICAL FIX: Enhanced session security
        self.sessions[session_id] = {
            'user_id': user_id,
            'created_at': current_time,
            'expires_at': current_time + timedelta(hours=getattr(settings, 'SESSION_LIFETIME', 24)),
            'ip_address': None,  # Should be set by middleware
            'user_agent': None,  # Should be set by middleware
            'last_activity': current_time
        }

        # Clean up expired sessions periodically
        self._cleanup_expired_sessions()
        return session_id

    def get_user_from_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user from session ID"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        current_time = datetime.utcnow()

        # Check if session has expired
        if current_time > session['expires_at']:
            del self.sessions[session_id]
            return None

        # Update last activity
        session['last_activity'] = current_time

        user_id = session['user_id']
        for user in self.users.values():
            if user['id'] == user_id and user['is_active']:
                return user

        # User not found or inactive
        del self.sessions[session_id]
        return None

    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session (logout)"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session invalidated: {session_id[:8]}...")
            return True
        return False

    def invalidate_user_sessions(self, user_id: int) -> int:
        """Invalidate all sessions for a user"""
        invalidated_count = 0
        sessions_to_remove = []

        for session_id, session in self.sessions.items():
            if session['user_id'] == user_id:
                sessions_to_remove.append(session_id)
                invalidated_count += 1

        for session_id in sessions_to_remove:
            del self.sessions[session_id]

        if invalidated_count > 0:
            logger.info(f"Invalidated {invalidated_count} sessions for user {user_id}")

        return invalidated_count

    def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.utcnow()
        expired_sessions = []

        for session_id, session in self.sessions.items():
            if current_time > session['expires_at']:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.sessions[session_id]

        if expired_sessions:
            logger.debug(f"Cleaned up {len(expired_sessions)} expired sessions")

    def create_token(self, user_id: int, expires_in: int = 3600) -> str:
        """Create secure JWT token"""
        import jwt
        current_time = datetime.utcnow()

        # CRITICAL FIX: Enhanced JWT payload with security features
        payload = {
            'user_id': user_id,
            'exp': current_time + timedelta(seconds=expires_in),
            'iat': current_time,
            'nbf': current_time,  # Not before
            'iss': 'pydance',    # Issuer
            'aud': 'pydance-api', # Audience
            'jti': secrets.token_hex(16)  # Unique token ID
        }

        # Use settings secret key if available
        secret_key = getattr(settings, 'SECRET_KEY', self.secret_key)
        return jwt.encode(payload, secret_key, algorithm='HS256')

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token with enhanced security"""
        import jwt

        # Use settings secret key if available
        secret_key = getattr(settings, 'SECRET_KEY', self.secret_key)

        # CRITICAL FIX: Enhanced token verification
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=['HS256'],
            audience='pydance-api',
            issuer='pydance'
        )

        # Additional validation
        current_time = datetime.utcnow()
        if payload.get('exp') and current_time > datetime.fromtimestamp(payload['exp']):
            logger.warning("Token expired")
            return None

        if payload.get('nbf') and current_time < datetime.fromtimestamp(payload['nbf']):
            logger.warning("Token not yet valid")
            return None

        return payload

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

    def enable_mfa(self, user_id: int, secret: str) -> bool:
        """Enable multi-factor authentication for user"""
        for user in self.users.values():
            if user['id'] == user_id:
                user['mfa_enabled'] = True
                user['mfa_secret'] = secret
                logger.info(f"MFA enabled for user {user_id}")
                return True
        return False

    def verify_mfa(self, user_id: int, code: str) -> bool:
        """Verify MFA code"""
        import pyotp

        for user in self.users.values():
            if user['id'] == user_id and user.get('mfa_enabled'):
                totp = pyotp.TOTP(user['mfa_secret'])
                return totp.verify(code)

        return False

    def generate_oauth2_token(self, user_id: int, client_id: str, scopes: List[str]) -> str:
        """Generate OAuth2 access token"""
        current_time = datetime.utcnow()
        expires_in = getattr(settings, 'OAUTH2_TOKEN_LIFETIME', 3600)

        payload = {
            'user_id': user_id,
            'client_id': client_id,
            'scopes': scopes,
            'exp': current_time + timedelta(seconds=expires_in),
            'iat': current_time,
            'token_type': 'access_token'
        }

        secret_key = getattr(settings, 'SECRET_KEY', self.secret_key)
        import jwt
        return jwt.encode(payload, secret_key, algorithm='HS256')

    def verify_oauth2_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify OAuth2 token"""
        import jwt
        secret_key = getattr(settings, 'SECRET_KEY', self.secret_key)

        payload = jwt.decode(token, secret_key, algorithms=['HS256'])

        if payload.get('token_type') != 'access_token':
            return None

        return payload

    def refresh_token(self, refresh_token: str) -> Optional[str]:
        """Generate new access token from refresh token"""
        import jwt
        secret_key = getattr(settings, 'SECRET_KEY', self.secret_key)

        payload = jwt.decode(refresh_token, secret_key, algorithms=['HS256'])

        if payload.get('token_type') != 'refresh_token':
            return None

        user_id = payload.get('user_id')
        if not user_id:
            return None

        # Generate new access token
        return self.generate_oauth2_token(user_id, payload.get('client_id', ''), payload.get('scopes', []))

    async def send_password_reset_email(self, email: str) -> bool:
        """Send password reset email"""
        # In a real implementation, this would integrate with an email service
        for user in self.users.values():
            if user['email'] == email:
                reset_token = secrets.token_urlsafe(32)
                user['reset_token'] = reset_token
                user['reset_expires'] = datetime.utcnow() + timedelta(hours=1)

                # Emit password reset event
                event_bus = get_event_bus()
                if event_bus:
                    from pydance.events import Event
                    await event_bus.publish(Event('password_reset_requested', {
                        'user_id': user['id'],
                        'email': email,
                        'token': reset_token
                    }))

                logger.info(f"Password reset requested for {email}")
                return True

        return False

    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using token"""
        for user in self.users.values():
            if (user.get('reset_token') == token and
                user.get('reset_expires') and
                datetime.utcnow() < user['reset_expires']):

                user['password_hash'] = self.hash_password(new_password)
                del user['reset_token']
                del user['reset_expires']

                # Invalidate all sessions for security
                self.invalidate_user_sessions(user['id'])

                logger.info(f"Password reset successful for user {user['id']}")
                return True

        return False

    def get_user_permissions(self, user_id: int) -> List[str]:
        """Get user permissions based on roles"""
        for user in self.users.values():
            if user['id'] == user_id:
                permissions = []
                for role in user.get('roles', []):
                    if role == 'admin':
                        permissions.extend(['read', 'write', 'delete', 'admin'])
                    elif role == 'moderator':
                        permissions.extend(['read', 'write', 'moderate'])
                    else:
                        permissions.append('read')
                return list(set(permissions))  # Remove duplicates
        return []

    def has_permission(self, user_id: int, permission: str) -> bool:
        """Check if user has specific permission"""
        permissions = self.get_user_permissions(user_id)
        return permission in permissions

    def audit_log(self, action: str, user_id: Optional[int] = None, details: Optional[Dict] = None):
        """Log security events for audit"""
        log_entry = {
            'timestamp': datetime.utcnow(),
            'action': action,
            'user_id': user_id,
            'details': details or {}
        }

        # In production, this would be stored in a secure audit log
        logger.info(f"AUDIT: {json.dumps(log_entry)}")

    async def _emit_user_event(self, event_type: str, user: Dict[str, Any]):
        """Emit user-related events"""
        event_bus = get_event_bus()
        if event_bus:
            from pydance.events import Event
            await event_bus.publish(Event(event_type, {
                'user_id': user['id'],
                'username': user['username'],
                'email': user['email']
            }))


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
