"""
Middleware components for Pydance Framework.

This package provides a unified middleware system with consistent inheritance.
All middleware classes inherit from the proper base classes in base.py.

Features:
- HTTP middleware with process_request/process_response pattern
- WebSocket middleware with process_websocket pattern
- Laravel/Django style middleware registration
- Throttle/rate limiting middleware
- Security, CORS, logging middleware
- Middleware resolver for dynamic loading
- Maintenance mode middleware
"""

from pydance.middleware.base import HTTPMiddleware, WebSocketMiddleware, MiddlewareCallable, MiddlewareType
from pydance.middleware.manager import MiddlewareManager, get_middleware_manager

# Throttle middleware (specialized)
from pydance.middleware.throttle import (
    ThrottleMiddleware,
    ThrottleConfig,
    throttle_per_ip,
    throttle_per_user,
    DEFAULT_THROTTLE_CONFIGS
)

# Unified middleware implementations (all inherit from proper base classes)
from pydance.middleware.builtin import (
    # HTTP Middleware Classes
    CORSMiddleware,
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    PerformanceMonitoringMiddleware,
    CompressionMiddleware,
    AuthenticationMiddleware,
    CSRFMiddleware,
    CachingMiddleware,
    ValidationMiddleware,
    ErrorHandlingMiddleware,
    RateLimitingMiddleware,

    # WebSocket Middleware Classes
    WebSocketSecurityMiddleware,
    WebSocketLoggingMiddleware,

    # Convenience instances
    cors_middleware,
    logging_middleware,
    security_middleware,
    performance_middleware,
    compression_middleware,
    auth_middleware,
    csrf_middleware,
    caching_middleware,
    validation_middleware,
    error_handling_middleware,
    rate_limiting_middleware,
    websocket_security_middleware,
    websocket_logging_middleware
)

# Maintenance middleware (inherits from HTTPMiddleware via direct __call__ pattern)
from pydance.middleware.maintenance import (
    MaintenanceMiddleware,
    MaintenanceManager,
    get_maintenance_manager,
    enable_maintenance,
    disable_maintenance
)

# Resolver for dynamic middleware loading
from pydance.middleware.resolver import MiddlewareResolver, middleware_resolver

# Enhanced pipeline system
from pydance.middleware.pipeline import (
    MiddlewarePipeline, PipelineConfig, PipelineStage,
    middleware, use_middleware, conditional,
    create_timing_middleware, create_logging_middleware, create_validation_middleware,
    get_pipeline, configure_pipeline
)

# Laravel-style middleware aliases (now using unified implementations)
MIDDLEWARE_ALIASES = {
    'auth': 'pydance.auth.middleware.AuthenticationMiddleware',
    'guest': 'pydance.auth.middleware.GuestMiddleware',
    'throttle': 'pydance.middleware.throttle.ThrottleMiddleware',
    'cors': 'pydance.middleware.builtin.CORSMiddleware',
    'csrf': 'pydance.security.middleware.CSRFMiddleware',
    'security': 'pydance.middleware.builtin.SecurityHeadersMiddleware',
    'logging': 'pydance.middleware.builtin.RequestLoggingMiddleware',
    'performance': 'pydance.middleware.builtin.PerformanceMonitoringMiddleware',
    'compression': 'pydance.middleware.builtin.CompressionMiddleware',
    'rate_limit': 'pydance.middleware.builtin.RateLimitingMiddleware',
    'maintenance': 'pydance.middleware.maintenance.MaintenanceMiddleware',
    'session': 'pydance.server.session.SessionMiddleware',
    'cache': 'pydance.caching.middleware.CacheMiddleware',
    'caching': 'pydance.middleware.builtin.CachingMiddleware',
    'validation': 'pydance.middleware.builtin.ValidationMiddleware',
    'error_handling': 'pydance.middleware.builtin.ErrorHandlingMiddleware',
    'authentication': 'pydance.middleware.builtin.AuthenticationMiddleware',
}

# Middleware groups (Laravel style) - using unified implementations
MIDDLEWARE_GROUPS = {
    'web': [
        'cors',
        'security',
        'performance',
        'compression',
        'pydance.server.session.SessionMiddleware',
        'pydance.security.middleware.CSRFMiddleware',
        'logging',
    ],
    'api': [
        'rate_limit',
        'throttle:100,10',
        'cors',
        'logging',
        'compression',
    ],
    'secure': [
        'security',
        'performance',
        'compression',
    ],
    'websocket': [
        'pydance.middleware.builtin.WebSocketSecurityMiddleware',
        'pydance.middleware.builtin.WebSocketLoggingMiddleware',
    ]
}

__all__ = [
    # Base middleware classes
    'HTTPMiddleware', 'WebSocketMiddleware',
    'MiddlewareCallable', 'MiddlewareType',

    # Middleware manager
    'MiddlewareManager', 'get_middleware_manager',

    # Throttle middleware (specialized)
    'ThrottleMiddleware', 'ThrottleConfig',
    'throttle_per_ip', 'throttle_per_user', 'DEFAULT_THROTTLE_CONFIGS',

    # HTTP Middleware Classes
    'CORSMiddleware', 'SecurityHeadersMiddleware', 'RequestLoggingMiddleware',
    'PerformanceMonitoringMiddleware', 'CompressionMiddleware', 'AuthenticationMiddleware',
    'CSRFMiddleware', 'CachingMiddleware', 'ValidationMiddleware', 'ErrorHandlingMiddleware',
    'RateLimitingMiddleware',

    # WebSocket Middleware Classes
    'WebSocketSecurityMiddleware', 'WebSocketLoggingMiddleware',

    # Convenience middleware instances
    'cors_middleware', 'logging_middleware', 'security_middleware',
    'performance_middleware', 'compression_middleware', 'auth_middleware',
    'csrf_middleware', 'caching_middleware', 'validation_middleware',
    'error_handling_middleware', 'rate_limiting_middleware',
    'websocket_security_middleware', 'websocket_logging_middleware',

    # Maintenance middleware
    'MaintenanceMiddleware', 'MaintenanceManager',
    'get_maintenance_manager', 'enable_maintenance', 'disable_maintenance',

    # Middleware resolver
    'MiddlewareResolver', 'middleware_resolver',

    # Laravel-style system
    'MIDDLEWARE_ALIASES', 'MIDDLEWARE_GROUPS',
]
