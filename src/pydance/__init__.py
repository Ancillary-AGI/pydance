"""
Pydance - Enterprise-grade Python web framework

A high-performance, secure web framework with optional C/C++ extensions
for building scalable web applications and microservices.

Features:
- ASGI-compliant application server
- High-performance routing and middleware
- Enterprise security features
- Database ORM with multiple backends
- Template engine with Jinja2 support
- WebSocket and SSE support
- Internationalization (i18n)
- Microservices and IoT support
- AI/ML integration (NeuralForge)
- Comprehensive monitoring and observability
- Advanced logging system with customizable configuration

Example:
    >>> from pydance.utils.logging import get_logger
    >>>
    >>> app = Application()
    >>> logger = get_logger('myapp')
    >>>
    >>> @app.route('/')
    >>> async def hello(request):
    ...     logger.info('Hello endpoint called')
    ...     return Response.text('Hello, World!')
    >>>
    >>> if __name__ == '__main__':
    ...     app.run()
"""

__version__ = "0.1.0"
__author__ = "Pydance Team"
__email__ = "team@pydance.dev"

# Initialize logging system
from pydance.utils.logging import (
    get_logger, configure_logging, setup_request_logging,
    log_request_start, log_request_end, log_database_query,
    log_auth_event, log_error, db_logger, auth_logger,
    request_logger, error_logger, graphql_logger, cache_logger,
    logger_manager
)

# Configure logging from settings
if logger_manager:
    logger_manager.configure_from_settings()

# Core framework components
from pydance.server.application import Application, Pydance
from pydance.http import Request, Response
from pydance.core.exceptions import HTTPException, ValidationError
from pydance.config import AppConfig, default_config as settings

# Database components

# Event system

# Plugin system

# Caching system
from pydance.caching import get_cache_manager, CacheManager, CacheConfig

# Storage system
from pydance.storage import get_storage_manager, StorageManager

# Advanced modules (local framework modules)
from pydance.neuralforge import LLMEngine, NeuralAgent
from pydance.microservices import Service
from pydance.iot import DeviceManager
from pydance.payment import PaymentProcessor
from pydance.security import SecurityManager
from pydance.monitoring import MetricsCollector
from pydance.performance import PerformanceMonitor
from pydance.resilience import CircuitBreaker, AutoRecoveryManager
from pydance.deployment import DeploymentManager

__all__ = [
    # Core
    'Application', 'Pydance', 'AppConfig',
    'Request', 'Response',
    'settings',

    # Logging System
    'get_logger', 'configure_logging', 'setup_request_logging',
    'log_request_start', 'log_request_end', 'log_database_query',
    'log_auth_event', 'log_error', 'db_logger', 'auth_logger',
    'request_logger', 'error_logger', 'graphql_logger', 'cache_logger',
    'logger_manager',

    # Database
    'DatabaseConfig',
    'DatabaseConnection',

    # Caching & Storage
    'get_cache_manager', 'CacheManager', 'CacheConfig',
    'get_storage_manager', 'StorageManager',

    # Advanced Modules
    'LLMEngine', 'NeuralAgent',
    'Service',
    'DeviceManager',
    'PaymentProcessor',
    'SecurityManager',
    'MetricsCollector',
    'PerformanceMonitor',
    'CircuitBreaker', 'AutoRecoveryManager',
    'DeploymentManager',

    # Core Systems

    # Exceptions
    'HTTPException', 'ValidationError',
]
