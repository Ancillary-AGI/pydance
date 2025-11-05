
from pydance.utils.logging import get_logger
"""
Consolidated built-in middleware implementations for Pydance.

This module contains all the standard middleware implementations,
consolidating duplicates and providing a single source of truth for
common middleware functionality.
"""

import asyncio
import logging
import time
import gzip
import secrets
import gc
from typing import Dict, Any, Optional, Union, Callable, List
from datetime import datetime
import json

from pydance.middleware.base import HTTPMiddleware, WebSocketMiddleware
from pydance.http.request import Request
from pydance.http.response import Response


# ==================== CORE HTTP MIDDLEWARE ====================

class CORSMiddleware(HTTPMiddleware):
    """CORS (Cross-Origin Resource Sharing) middleware"""

    def __init__(self,
                 allow_origins: Optional[List[str]] = None,
                 allow_credentials: bool = True,
                 allow_methods: Optional[List[str]] = None,
                 allow_headers: Optional[List[str]] = None,
                 max_age: int = 86400,
                 expose_headers: Optional[List[str]] = None):
        super().__init__("CORSMiddleware")
        self.allow_origins = allow_origins or ["*"]
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
        self.max_age = max_age
        self.expose_headers = expose_headers or []

    async def process_request(self, request: Request) -> Request:
        """Handle preflight CORS requests"""
        if request.method == "OPTIONS" and "origin" in request.headers:
            return await self._handle_preflight_request(request)
        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        """Add CORS headers to response"""
        origin = request.headers.get("origin")
        if origin and (origin in self.allow_origins or "*" in self.allow_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = str(self.allow_credentials).lower()
            response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
            response.headers["Access-Control-Max-Age"] = str(self.max_age)

            if self.expose_headers:
                response.headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)

        return response

    async def _handle_preflight_request(self, request: Request) -> Request:
        """Handle preflight OPTIONS request"""
        from pydance.http.response import Response as HTTPResponse
        response = HTTPResponse(200)
        response.headers.update({
            "Access-Control-Allow-Origin": request.headers.get("origin"),
            "Access-Control-Allow-Credentials": str(self.allow_credentials).lower(),
            "Access-Control-Allow-Methods": ", ".join(self.allow_methods),
            "Access-Control-Allow-Headers": ", ".join(self.allow_headers),
            "Access-Control-Max-Age": str(self.max_age)
        })
        request._preflight_response = response
        return request


class SecurityHeadersMiddleware(HTTPMiddleware):
    """Security headers middleware"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("SecurityHeadersMiddleware")
        self.config = config or {}
        self.headers = self.config.get('headers', {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'Content-Security-Policy': "default-src 'self'"
        })

    async def process_request(self, request: Request) -> Request:
        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        if hasattr(response, 'headers'):
            response.headers.update(self.headers)
        return response


class RequestLoggingMiddleware(HTTPMiddleware):
    """Request logging middleware"""

    def __init__(self, log_level: str = "INFO", logger_name: str = "pydance.middleware"):
        super().__init__("RequestLoggingMiddleware")
        self.logger = get_logger(logger_name)
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    async def process_request(self, request: Request) -> Request:
        context = getattr(request, 'context', None)
        request_id = context.request_id if context else 'unknown'
        self.logger.info(f"[{request_id}] {request.method} {request.path}")
        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        context = getattr(request, 'context', None)
        request_id = context.request_id if context else 'unknown'
        status_code = getattr(response, 'status_code', 200)
        self.logger.info(f"[{request_id}] Completed with status {status_code}")
        return response


class PerformanceMonitoringMiddleware(HTTPMiddleware):
    """Performance monitoring middleware"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("PerformanceMonitoringMiddleware")
        self.config = config or {}
        self.enable_memory_monitoring = self.config.get('enable_memory_monitoring', True)
        self.enable_gc_monitoring = self.config.get('enable_gc_monitoring', True)
        # Initialize metrics collector (will be None if not available)
        try:
            from pydance.monitoring import get_metrics_collector
            self.metrics_collector = get_metrics_collector()
        except ImportError:
            self.metrics_collector = None

    async def process_request(self, request: Request) -> Request:
        """Monitor request start"""
        request._perf_start_time = time.time()
        request._perf_start_memory = self._get_memory_usage() if self.enable_memory_monitoring else 0
        request._perf_start_gc = gc.get_stats() if self.enable_gc_monitoring else {}
        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        """Monitor request completion and collect metrics"""
        if hasattr(request, '_perf_start_time'):
            execution_time = time.time() - request._perf_start_time

            # Add execution time header
            if hasattr(response, 'headers'):
                response.headers['X-Execution-Time'] = f"{execution_time:.4f}s"

            # Record metrics
            try:
                # Request duration histogram
                if hasattr(self.metrics_collector, 'create_histogram'):
                    duration_metric = self.metrics_collector.get_metric('http_request_duration_seconds')
                    if duration_metric:
                        duration_metric.observe(execution_time)

                # Memory usage if enabled
                if self.enable_memory_monitoring and hasattr(request, '_perf_start_memory'):
                    end_memory = self._get_memory_usage()
                    memory_diff = end_memory - request._perf_start_memory

                    memory_metric = self.metrics_collector.get_metric('http_request_memory_delta_mb')
                    if memory_metric:
                        memory_metric.set(memory_diff)

                # GC stats if enabled
                if self.enable_gc_monitoring and hasattr(request, '_perf_start_gc'):
                    end_gc = gc.get_stats()
                    for i, (start, end) in enumerate(zip(request._perf_start_gc.values(), end_gc.values())):
                        gc_diff = end - start
                        if gc_diff > 0:
                            gc_metric = self.metrics_collector.get_metric(f'gc_collections_{i}')
                            if gc_metric:
                                gc_metric.increment(gc_diff)

            except Exception as e:
                # Don't let metrics collection break the request
                logger.debug(f"Metrics collection error: {e}")

        return response

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            return self.process.memory_info().rss / 1024 / 1024  # MB
        except Exception:
            return 0.0


class CompressionMiddleware(HTTPMiddleware):
    """Response compression middleware"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("CompressionMiddleware")
        self.config = config or {}
        self.compression_enabled = self.config.get('enabled', True)
        self.min_size = self.config.get('min_size', 1024)

    async def process_request(self, request: Request) -> Request:
        request._accepts_gzip = 'gzip' in request.headers.get('Accept-Encoding', '')
        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        if not self.compression_enabled or not getattr(request, '_accepts_gzip', False):
            return response

        if hasattr(response, 'body'):
            body_size = len(response.body.encode('utf-8') if isinstance(response.body, str) else response.body)
            if body_size < self.min_size:
                return response

            if isinstance(response.body, str):
                compressed = gzip.compress(response.body.encode('utf-8'))
            else:
                compressed = gzip.compress(response.body)

            response.body = compressed
            response.headers['Content-Encoding'] = 'gzip'

        return response


class AuthenticationMiddleware(HTTPMiddleware):
    """Authentication middleware"""

    def __init__(self, auth_backends: Optional[List[Callable]] = None, optional: bool = False):
        super().__init__("AuthenticationMiddleware")
        self.auth_backends = auth_backends or []
        self.optional = optional

    async def process_request(self, request: Request) -> Request:
        user = None

        for backend in self.auth_backends:
            if asyncio.iscoroutinefunction(backend):
                user = await backend(request)
            else:
                user = backend(request)

            if user:
                break

        if not user and not self.optional:
            from pydance.exceptions import HTTPException
            raise HTTPException(401, "Authentication required")

        request.user = user
        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        if hasattr(request, 'user') and request.user:
            response.headers['X-Authenticated-User'] = str(request.user)
        return response


class CSRFMiddleware(HTTPMiddleware):
    """CSRF protection middleware"""

    def __init__(self, secret: str, cookie_name: str = "csrftoken", header_name: str = "X-CSRFToken"):
        super().__init__("CSRFMiddleware")
        self.secret = secret
        self.cookie_name = cookie_name
        self.header_name = header_name

    async def process_request(self, request: Request) -> Request:
        if request.method in ['GET', 'HEAD', 'OPTIONS', 'TRACE']:
            return request

        token = request.headers.get(self.header_name)
        if not token:
            token = self._get_token_from_request(request)

        if not token or not self._validate_token(token):
            from pydance.exceptions import HTTPException
            raise HTTPException(403, "CSRF token validation failed")

        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        if request.method in ['GET', 'HEAD']:
            token = self._generate_token()
            response.set_cookie(self.cookie_name, token, httponly=True, samesite='Strict')
        return response

    def _get_token_from_request(self, request: Request) -> Optional[str]:
        return None

    def _validate_token(self, token: str) -> bool:
        return len(token) > 10

    def _generate_token(self) -> str:
        return secrets.token_urlsafe(32)


class CachingMiddleware(HTTPMiddleware):
    """Response caching middleware"""

    def __init__(self, cache_duration: int = 300, cache_store: Optional[Any] = None):
        super().__init__("CachingMiddleware")
        self.cache_duration = cache_duration
        self.cache_store = cache_store or {}

    async def process_request(self, request: Request) -> Request:
        if request.method != 'GET':
            return request

        cache_key = self._generate_cache_key(request)
        cached_response = self._get_cached_response(cache_key)

        if cached_response:
            request._cached_response = cached_response

        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        if (request.method == 'GET' and
            getattr(response, 'status_code', 200) == 200 and
            not hasattr(request, '_cached_response')):

            cache_key = self._generate_cache_key(request)
            self._set_cached_response(cache_key, response, self.cache_duration)

        return response

    def _generate_cache_key(self, request: Request) -> str:
        key_parts = [
            request.method,
            request.path,
            str(getattr(request, 'query_params', {}))
        ]
        return hash(":".join(key_parts))

    def _get_cached_response(self, key: str) -> Optional[Response]:
        if key in self.cache_store:
            response_data, timestamp = self.cache_store[key]
            if time.time() - timestamp < self.cache_duration:
                return response_data
            else:
                del self.cache_store[key]
        return None

    def _set_cached_response(self, key: str, response: Response, duration: int):
        self.cache_store[key] = (response, time.time())


class ValidationMiddleware(HTTPMiddleware):
    """Request validation middleware"""

    def __init__(self, validators: Optional[Dict[str, Callable]] = None):
        super().__init__("ValidationMiddleware")
        self.validators = validators or {}

    async def process_request(self, request: Request) -> Request:
        validation_errors = []

        for field, validator in self.validators.items():
            value = self._get_field_value(request, field)
            if value is not None:
                try:
                    if asyncio.iscoroutinefunction(validator):
                        result = await validator(value)
                    else:
                        result = validator(value)

                    if result is False:
                        validation_errors.append(f"Validation failed for {field}")
                except Exception as e:
                    validation_errors.append(f"Validation error for {field}: {str(e)}")

        if validation_errors:
            from pydance.exceptions import HTTPException
            raise HTTPException(400, {"validation_errors": validation_errors})

        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        """Pass-through response processing for validation middleware."""
        return response

    def _get_field_value(self, request: Request, field: str) -> Any:
        return getattr(request, field, None)


class ErrorHandlingMiddleware(HTTPMiddleware):
    """Error handling middleware"""

    def __init__(self, debug: bool = False, error_handlers: Optional[Dict[type, Callable]] = None):
        super().__init__("ErrorHandlingMiddleware")
        self.debug = debug
        self.error_handlers = error_handlers or {}

    async def process_request(self, request: Request) -> Request:
        request.error_context = []
        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        if hasattr(request, 'error_context') and request.error_context:
            response.headers['X-Error-Count'] = str(len(request.error_context))
        return response

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        try:
            return await super().__call__(request, call_next)
        except Exception as e:
            if hasattr(request, 'error_context'):
                request.error_context.append(e)

            if type(e) in self.error_handlers:
                handler = self.error_handlers[type(e)]
                if asyncio.iscoroutinefunction(handler):
                    return await handler(e, request)
                else:
                    return handler(e, request)

            return await self._handle_error(e, request)

    async def _handle_error(self, error: Exception, request: Request) -> Response:
        from pydance.http.response import Response as HTTPResponse

        status_code = self._get_status_code(error)
        error_response = {
            "error": type(error).__name__,
            "message": str(error) if self.debug else "Internal server error"
        }

        if self.debug:
            import traceback
            error_response["traceback"] = traceback.format_exc()

        response = HTTPResponse(status_code)
        response.headers["Content-Type"] = "application/json"
        response.body = json.dumps(error_response)
        return response

    def _get_status_code(self, error: Exception) -> int:
        status_map = {
            'ValidationError': 400,
            'AuthenticationError': 401,
            'PermissionError': 403,
            'NotFoundError': 404,
            'RateLimitError': 429,
        }
        return status_map.get(type(error).__name__, 500)


class RateLimitingMiddleware(HTTPMiddleware):
    """Rate limiting middleware"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("RateLimitingMiddleware")
        self.config = config or {}
        self.requests_per_minute = self.config.get('requests_per_minute', 60)
        self.burst_limit = self.config.get('burst_limit', 10)

    async def process_request(self, request: Request) -> Request:
        client_key = self._get_client_key(request)

        if self._is_rate_limited(client_key):
            from pydance.exceptions import HTTPException
            raise HTTPException(429, "Too Many Requests")

        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        """Pass-through response processing for rate limiting middleware."""
        return response

    def _get_client_key(self, request: Request) -> str:
        if hasattr(request, 'remote_addr'):
            return request.remote_addr or 'unknown'
        elif hasattr(request, 'client_ip'):
            return request.client_ip or 'unknown'
        else:
            return 'unknown'

    def _is_rate_limited(self, client_key: str) -> bool:
        return False


# ==================== WEBSOCKET MIDDLEWARE ====================

class WebSocketSecurityMiddleware(WebSocketMiddleware):
    """WebSocket security middleware"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("WebSocketSecurityMiddleware")
        self.config = config or {}
        self.allowed_origins = self.config.get('allowed_origins', [])
        self.max_connections = self.config.get('max_connections', 1000)

    async def __call__(self, websocket, call_next):
        """WebSocket middleware call interface."""
        return await self.process_websocket(websocket)

    async def process_websocket(self, websocket) -> Optional[Any]:
        origin = websocket.headers.get('origin')
        if self.allowed_origins and origin not in self.allowed_origins:
            return None
        return websocket


class WebSocketLoggingMiddleware(WebSocketMiddleware):
    """WebSocket logging middleware"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("WebSocketLoggingMiddleware")
        self.config = config or {}
        self.log_level = getattr(logging, self.config.get('level', 'INFO').upper(), logging.INFO)
        self.logger = get_logger("pydance.middleware.websocket")
        self.logger.setLevel(self.log_level)

    async def __call__(self, websocket, call_next):
        """WebSocket middleware call interface."""
        return await self.process_websocket(websocket)

    async def process_websocket(self, websocket) -> Optional[Any]:
        client_ip = getattr(websocket, 'client_ip', 'unknown')
        self.logger.info(f"WebSocket connection from {client_ip}")
        return websocket


# ==================== CONVENIENCE INSTANCES ====================

# Create default instances for common use cases
cors_middleware = CORSMiddleware()
logging_middleware = RequestLoggingMiddleware()
security_middleware = SecurityHeadersMiddleware()
performance_middleware = PerformanceMonitoringMiddleware()
compression_middleware = CompressionMiddleware()
auth_middleware = AuthenticationMiddleware()
csrf_middleware = CSRFMiddleware("your-secret-key")
caching_middleware = CachingMiddleware()
validation_middleware = ValidationMiddleware()
error_handling_middleware = ErrorHandlingMiddleware()
rate_limiting_middleware = RateLimitingMiddleware()
websocket_security_middleware = WebSocketSecurityMiddleware()
websocket_logging_middleware = WebSocketLoggingMiddleware()


__all__ = [
    # HTTP Middleware Classes
    'CORSMiddleware', 'SecurityHeadersMiddleware', 'RequestLoggingMiddleware',
    'PerformanceMonitoringMiddleware', 'CompressionMiddleware', 'AuthenticationMiddleware',
    'CSRFMiddleware', 'CachingMiddleware', 'ValidationMiddleware', 'ErrorHandlingMiddleware',
    'RateLimitingMiddleware',

    # WebSocket Middleware Classes
    'WebSocketSecurityMiddleware', 'WebSocketLoggingMiddleware',

    # Convenience Instances
    'cors_middleware', 'logging_middleware', 'security_middleware', 'performance_middleware',
    'compression_middleware', 'auth_middleware', 'csrf_middleware', 'caching_middleware',
    'validation_middleware', 'error_handling_middleware', 'rate_limiting_middleware',
    'websocket_security_middleware', 'websocket_logging_middleware'
]
