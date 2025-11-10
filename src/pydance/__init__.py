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
    >>> from pydance.server.application import Application
    >>> from pydance.http.response import Response
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
logger_manager.configure_from_settings()

# Core framework components
from pydance.server.application import Application, Pydance
from pydance.config import AppConfig
from pydance.http import Request, Response
from pydance.config.settings import settings
from pydance.exceptions import HTTPException, ValidationError

# Database components
from pydance.db import DatabaseConfig
from pydance.db.connections import DatabaseConnection

# Event system
from pydance.core.events import get_event_bus

# Plugin system
from pydance.core.plugins import get_plugin_manager

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

    # Database
    'DatabaseConfig',
    'DatabaseConnection',
    'BaseModel',

    # Utilities
    'EventBus', 'Event', 'get_event_bus',
    'PluginManager', 'Plugin', 'get_plugin_manager',
    # 'get_storage_manager',  # Temporarily disabled
    # 'get_cache_manager',  # Temporarily disabled

    # Exceptions
    'HTTPException', 'ValidationError',
]
