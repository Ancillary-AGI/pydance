"""
Security Middleware for Pydance Framework

This module provides comprehensive security middleware that implements
secure-by-default settings including:
- CSRF protection
- Content Security Policy (CSP)
- Security headers (HSTS, X-Frame-Options, etc.)
- Rate limiting
- Request validation
- Security monitoring
- Attack prevention
"""

import logging
import secrets
import time
import re
from typing import Dict, List, Callable, Any, Optional, Union, Awaitable
from dataclasses import dataclass, field
from collections import defaultdict

from pydance.http import Request, Response
from pydance.exceptions import HTTPException
from pydance.middleware import HTTPMiddleware

logger = logging.getLogger(__name__)


def add_csrf_token_to_response(response: Response, config: 'SecurityConfig', token: str) -> None:
    """Shared utility function to add CSRF token to response"""
    response.set_cookie(
        config.csrf_cookie_name,
        token,
        httponly=True,
        secure=config.session_secure,
        samesite=config.session_same_site,
        max_age=config.session_max_age
    )


@dataclass
class SecurityConfig:
    """Security middleware configuration"""

    # CSRF settings
    csrf_enabled: bool = True
    csrf_secret: str = field(default_factory=lambda: secrets.token_hex(32))
    csrf_cookie_name: str = "pydance_csrf"
    csrf_header_name: str = "X-CSRF-Token"
    csrf_safe_methods: List[str] = field(default_factory=lambda: ["GET", "HEAD", "OPTIONS", "TRACE"])

    # Session/Cookie settings for CSRF
    session_secure: bool = True
    session_same_site: str = "Lax"
    session_max_age: int = 3600

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    rate_limit_by: str = "ip"  # ip, user, or combined

    # Content Security Policy
    csp_enabled: bool = True
    csp_policy: str = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';"

    # Security headers
    security_headers_enabled: bool = True
    hsts_enabled: bool = True
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True

    # Request validation
    validate_headers: bool = True
    validate_content_type: bool = True
    max_content_length: int = 10 * 1024 * 1024  # 10MB
    allowed_content_types: List[str] = field(default_factory=lambda: [
        "application/json", "application/x-www-form-urlencoded",
        "multipart/form-data", "text/plain"
    ])

    # Security monitoring
    log_security_events: bool = True
    suspicious_activity_threshold: int = 5
    block_suspicious_ips: bool = True

    # Attack prevention
    prevent_sql_injection: bool = True
    prevent_xss: bool = True
    prevent_path_traversal: bool = True
    prevent_command_injection: bool = True

    # Advanced security
    enable_waf: bool = True
    waf_rules: Dict[str, Any] = field(default_factory=dict)


class SecurityEvent:
    """Security event for monitoring"""

    def __init__(self, event_type: str, details: Dict[str, Any], severity: str = "medium"):
        self.event_type = event_type
        self.details = details
        self.severity = severity
        self.timestamp = time.time()
        self.ip_address = details.get('ip_address', 'unknown')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type,
            'details': self.details,
            'severity': self.severity,
            'timestamp': self.timestamp,
            'ip_address': self.ip_address
        }


class RateLimiter:
    """Rate limiter for security middleware"""

    def __init__(self, requests: int = 100, window: int = 60):
        self.requests = requests
        self.window = window
        self.requests_by_key: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for the given key"""
        now = time.time()
        # Remove old requests outside the window
        self.requests_by_key[key] = [
            req_time for req_time in self.requests_by_key[key]
            if now - req_time < self.window
        ]

        # Check if under limit
        if len(self.requests_by_key[key]) < self.requests:
            self.requests_by_key[key].append(now)
            return True

        return False

    def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests for the key"""
        now = time.time()
        self.requests_by_key[key] = [
            req_time for req_time in self.requests_by_key[key]
            if now - req_time < self.window
        ]
        return max(0, self.requests - len(self.requests_by_key[key]))


class SecurityMonitor:
    """Security event monitoring"""

    def __init__(self):
        self.suspicious_activity: Dict[str, List[SecurityEvent]] = defaultdict(list)
        self.blocked_ips: set = set()
        self.event_handlers: List[Callable[[SecurityEvent], Awaitable[None]]] = []

    def log_event(self, event: SecurityEvent) -> None:
        """Log a security event"""
        self.suspicious_activity[event.ip_address].append(event)

        # Check for suspicious activity threshold
        recent_events = [
            e for e in self.suspicious_activity[event.ip_address]
            if time.time() - e.timestamp < 300  # Last 5 minutes
        ]

        if len(recent_events) >= 5:  # Threshold reached
            self.blocked_ips.add(event.ip_address)
            logger.warning(f"IP {event.ip_address} blocked due to suspicious activity")

    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked"""
        return ip_address in self.blocked_ips

    def add_event_handler(self, handler: Callable[[SecurityEvent], Awaitable[None]]) -> None:
        """Add event handler"""
        self.event_handlers.append(handler)

    async def process_event(self, event: SecurityEvent) -> None:
        """Process security event asynchronously"""
        self.log_event(event)

        # Notify handlers
        for handler in self.event_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in security event handler: {e}")


class SecurityMiddleware(HTTPMiddleware):
    """
    Comprehensive security middleware with secure-by-default settings.

    This middleware provides:
    - CSRF protection
    - Rate limiting
    - Security headers
    - Request validation
    - Attack prevention
    - Security monitoring
    - XSS protection
    - SQL injection prevention
    - Path traversal protection
    - Command injection prevention
    """

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.rate_limiter = RateLimiter(
            self.config.rate_limit_requests,
            self.config.rate_limit_window
        )
        self.security_monitor = SecurityMonitor()
        self.csrf_tokens: Dict[str, str] = {}

        # Setup security monitoring
        self._setup_monitoring()

    def _setup_monitoring(self) -> None:
        """Setup security monitoring"""
        if self.config.log_security_events:
            async def log_handler(event: SecurityEvent) -> None:
                logger.info(f"Security event: {event.event_type} - {event.details}")

            self.security_monitor.add_event_handler(log_handler)

    async def __call__(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process request through security middleware"""

        # Check if IP is blocked
        if self.security_monitor.is_ip_blocked(request.client_ip):
            logger.warning(f"Blocked request from {request.client_ip}")
            raise HTTPException(403, "Access denied")

        # Rate limiting
        if self.config.rate_limit_enabled:
            rate_limit_key = self._get_rate_limit_key(request)
            if not self.rate_limiter.is_allowed(rate_limit_key):
                remaining = self.rate_limiter.get_remaining_requests(rate_limit_key)
                logger.warning(f"Rate limit exceeded for {rate_limit_key}")

                # Log security event
                await self.security_monitor.process_event(
                    SecurityEvent("rate_limit_exceeded", {
                        "ip_address": request.client_ip,
                        "path": request.path,
                        "user_agent": request.headers.get("User-Agent", ""),
                        "remaining_requests": remaining
                    }, "medium")
                )

                raise HTTPException(429, "Rate limit exceeded")

        # CSRF protection
        if self.config.csrf_enabled:
            await self._check_csrf_token(request)

        # Request validation
        if self.config.validate_headers:
            self._validate_headers(request)

        if self.config.validate_content_type:
            self._validate_content_type(request)

        # Attack prevention
        if self.config.prevent_sql_injection:
            self._check_sql_injection(request)

        if self.config.prevent_xss:
            self._check_xss(request)

        if self.config.prevent_path_traversal:
            self._check_path_traversal(request)

        if self.config.prevent_command_injection:
            self._check_command_injection(request)

        # Process request
        response = await call_next(request)

        # Add security headers
        if self.config.security_headers_enabled:
            self._add_security_headers(response)

        # Add CSRF token to response
        if self.config.csrf_enabled and request.method in ["GET", "HEAD"]:
            self._add_csrf_token(response, request)

        return response

    def _get_rate_limit_key(self, request: Request) -> str:
        """Get rate limit key for request"""
        if self.config.rate_limit_by == "ip":
            return request.client_ip
        elif self.config.rate_limit_by == "user":
            # Use session or user ID if available
            return request.session.get("user_id", request.client_ip) if hasattr(request, 'session') else request.client_ip
        else:  # combined
            user_id = request.session.get("user_id", "anonymous") if hasattr(request, 'session') else "anonymous"
            return f"{request.client_ip}:{user_id}"

    async def _check_csrf_token(self, request: Request) -> None:
        """Check CSRF token for state-changing requests"""
        if request.method in self.config.csrf_safe_methods:
            return

        # Get token from header or form data
        token = None
        if self.config.csrf_header_name in request.headers:
            token = request.headers[self.config.csrf_header_name]
        elif hasattr(request, 'form') and request.form:
            token = request.form.get('csrf_token')

        if not token:
            logger.warning(f"Missing CSRF token for {request.method} {request.path}")
            await self.security_monitor.process_event(
                SecurityEvent("missing_csrf_token", {
                    "ip_address": request.client_ip,
                    "method": request.method,
                    "path": request.path
                }, "high")
            )
            raise HTTPException(403, "CSRF token required")

        # Validate token
        session_id = request.session.session_id if hasattr(request, 'session') else None
        if session_id and token != self.csrf_tokens.get(session_id):
            logger.warning(f"Invalid CSRF token for {request.method} {request.path}")
            await self.security_monitor.process_event(
                SecurityEvent("invalid_csrf_token", {
                    "ip_address": request.client_ip,
                    "method": request.method,
                    "path": request.path
                }, "high")
            )
            raise HTTPException(403, "Invalid CSRF token")

    def _validate_headers(self, request: Request) -> None:
        """Validate request headers for security"""
        # Check for suspicious headers
        suspicious_headers = [
            'X-Forwarded-For',  # Can be spoofed
            'X-Real-IP',        # Can be spoofed
            'X-Originating-IP', # Can be spoofed
        ]

        for header in suspicious_headers:
            if header in request.headers:
                logger.debug(f"Suspicious header detected: {header}")

        # Check content length
        if 'Content-Length' in request.headers:
            try:
                content_length = int(request.headers['Content-Length'])
                if content_length > self.config.max_content_length:
                    raise HTTPException(413, "Content too large")
            except ValueError:
                raise HTTPException(400, "Invalid Content-Length header")

    def _validate_content_type(self, request: Request) -> None:
        """Validate content type"""
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get('Content-Type', '').split(';')[0].strip()

            if content_type and content_type not in self.config.allowed_content_types:
                logger.warning(f"Disallowed content type: {content_type}")
                raise HTTPException(415, "Unsupported content type")

    def _check_sql_injection(self, request: Request) -> None:
        """Check for SQL injection patterns"""
        sql_patterns = [
            r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b',
            r'(--|#|/\*|\*/)',
            r'(\bUNION\b\s+\bSELECT\b)',
            r'(\bor\b\s+\d+\s*=\s*\d+)',
            r'(\band\b\s+\d+\s*=\s*\d+)',
        ]

        # Check URL path and query parameters
        check_strings = [request.path, request.query_string]
        if hasattr(request, 'form') and request.form:
            check_strings.extend(request.form.values())

        for check_string in check_strings:
            if isinstance(check_string, str):
                for pattern in sql_patterns:
                    if re.search(pattern, check_string, re.IGNORECASE):
                        logger.warning(f"Potential SQL injection detected: {check_string}")
                        raise HTTPException(400, "Invalid request parameters")

    def _check_xss(self, request: Request) -> None:
        """Check for XSS patterns"""
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>',
        ]

        # Check form data and query parameters
        check_strings = []
        if hasattr(request, 'form') and request.form:
            check_strings.extend(request.form.values())

        if request.query_params:
            check_strings.extend(request.query_params.values())

        for check_string in check_strings:
            if isinstance(check_string, str):
                for pattern in xss_patterns:
                    if re.search(pattern, check_string, re.IGNORECASE | re.DOTALL):
                        logger.warning(f"Potential XSS detected: {check_string}")
                        raise HTTPException(400, "Invalid request parameters")

    def _check_path_traversal(self, request: Request) -> None:
        """Check for path traversal attacks"""
        traversal_patterns = [
            r'\.\./',
            r'\.\.\\',
            r'%2e%2e%2f',
            r'%2e%2e%5c',
        ]

        for pattern in traversal_patterns:
            if re.search(pattern, request.path, re.IGNORECASE):
                logger.warning(f"Path traversal detected: {request.path}")
                raise HTTPException(403, "Access denied")

    def _check_command_injection(self, request: Request) -> None:
        """Check for command injection patterns"""
        command_patterns = [
            r'\b(sudo|su|exec|eval|system|popen|shell_exec|passthru)\b',
            r'(\||&|;|\$\(|\`|\$\{)',
            r'(\.\.|/etc/passwd|/etc/shadow|/bin/sh|/bin/bash)',
            r'(rm\s+(-rf|-f)|del\s+(/q|/f))',
            r'(format|fdisk|mkfs)',
        ]

        # Check form data and query parameters
        check_strings = []
        if hasattr(request, 'form') and request.form:
            check_strings.extend(request.form.values())

        if request.query_params:
            check_strings.extend(request.query_params.values())

        # Check headers that might be used for command injection
        headers_to_check = ['User-Agent', 'Referer', 'X-Forwarded-For']
        for header in headers_to_check:
            if header in request.headers:
                check_strings.append(request.headers[header])

        for check_string in check_strings:
            if isinstance(check_string, str):
                for pattern in command_patterns:
                    if re.search(pattern, check_string, re.IGNORECASE):
                        logger.warning(f"Potential command injection detected: {check_string}")
                        raise HTTPException(400, "Invalid request parameters")

    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response"""
        if self.config.csp_enabled:
            response.headers['Content-Security-Policy'] = self.config.csp_policy

        if self.config.hsts_enabled:
            hsts_value = f"max-age={self.config.hsts_max_age}"
            if self.config.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.config.hsts_preload:
                hsts_value += "; preload"
            response.headers['Strict-Transport-Security'] = hsts_value

        # Additional security headers
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

    def _add_csrf_token(self, response: Response, request: Request) -> None:
        """Add CSRF token to response"""
        session_id = request.session.session_id if hasattr(request, 'session') else None
        if session_id:
            token = secrets.token_hex(32)
            self.csrf_tokens[session_id] = token
            add_csrf_token_to_response(response, self.config, token)

    async def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        return {
            "rate_limited_requests": len(self.rate_limiter.requests_by_key),
            "blocked_ips": len(self.security_monitor.blocked_ips),
            "suspicious_activities": len(self.security_monitor.suspicious_activity),
            "csrf_tokens_active": len(self.csrf_tokens)
        }




# Convenience functions for easy setup
def create_security_middleware(config: Optional[SecurityConfig] = None) -> SecurityMiddleware:
    """Create security middleware with configuration"""
    return SecurityMiddleware(config)

__all__ = [
    'SecurityMiddleware', 'SecurityConfig', 'SecurityEvent',
    'RateLimiter', 'SecurityMonitor', 'create_security_middleware'
]
