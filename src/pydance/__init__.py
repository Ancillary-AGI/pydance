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
try:
    from pydance.utils.logging import (
        get_logger, configure_logging, setup_request_logging,
        log_request_start, log_request_end, log_database_query,
        log_auth_event, log_error, db_logger, auth_logger,
        request_logger, error_logger, graphql_logger, cache_logger,
        logger_manager
    )
except ImportError:
    # Fallback if logging module not available
    get_logger = None
    configure_logging = None
    setup_request_logging = None
    log_request_start = None
    log_request_end = None
    log_database_query = None
    log_auth_event = None
    log_error = None
    db_logger = None
    auth_logger = None
    request_logger = None
    error_logger = None
    graphql_logger = None
    cache_logger = None
    logger_manager = None

# Configure logging from settings
if logger_manager:
    logger_manager.configure_from_settings()

# Core framework components
from pydance.server.application import Application, Pydance
from pydance.http import Request, Response
from pydance.core.exceptions import HTTPException, ValidationError

# Database components

# Event system

# Plugin system

# Caching system
try:
    from pydance.caching import get_cache_manager, CacheManager, CacheConfig
except ImportError:
    get_cache_manager = None
    CacheManager = None
    CacheConfig = None

# Storage system
try:
    from pydance.storage import get_storage_manager, StorageManager
except ImportError:
    get_storage_manager = None
    StorageManager = None

# Advanced modules (optional imports)
try:
    from pydance.neuralforge import NeuralForge, LLMEngine, NeuralAgent
except ImportError:
    NeuralForge = None
    LLMEngine = None
    NeuralAgent = None

try:
    from pydance.microservices import Service, MicroserviceManager
except ImportError:
    Service = None
    MicroserviceManager = None

try:
    from pydance.iot import IoTManager, DeviceManager
except ImportError:
    IoTManager = None
    DeviceManager = None

try:
    from pydance.payment import PaymentProcessor, PaymentManager
except ImportError:
    PaymentProcessor = None
    PaymentManager = None

try:
    from pydance.streaming import StreamManager, StreamingServer
except ImportError:
    StreamManager = None
    StreamingServer = None

try:
    from pydance.security import SecurityManager, QuantumSecurity
except ImportError:
    SecurityManager = None
    QuantumSecurity = None

try:
    from pydance.monitoring import MonitoringManager, MetricsCollector
except ImportError:
    MonitoringManager = None
    MetricsCollector = None

try:
    from pydance.performance import PerformanceMonitor, PerformanceOptimizer
except ImportError:
    PerformanceMonitor = None
    PerformanceOptimizer = None

try:
    from pydance.resilience import CircuitBreaker, AutoRecoveryManager
except ImportError:
    CircuitBreaker = None
    AutoRecoveryManager = None

try:
    from pydance.deployment import DeploymentManager, KubernetesManager
except ImportError:
    DeploymentManager = None
    KubernetesManager = None

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
    'NeuralForge', 'LLMEngine', 'NeuralAgent',
    'Service', 'MicroserviceManager',
    'IoTManager', 'DeviceManager',
    'PaymentProcessor', 'PaymentManager',
    'StreamManager', 'StreamingServer',
    'SecurityManager', 'QuantumSecurity',
    'MonitoringManager', 'MetricsCollector',
    'PerformanceMonitor', 'PerformanceOptimizer',
    'CircuitBreaker', 'AutoRecoveryManager',
    'DeploymentManager', 'KubernetesManager',

    # Core Systems
    'EventBus', 'Event', 'get_event_bus',
    'PluginManager', 'Plugin', 'get_plugin_manager',

    # Exceptions
    'HTTPException', 'ValidationError',
]
