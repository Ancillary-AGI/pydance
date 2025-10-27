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

Example:
    >>> from pydance.server.application import Application
    >>> from pydance.http.response import Response
    >>>
    >>> app = Application()
    >>>
    >>> @app.route('/')
    >>> async def hello(request):
    ...     return Response.text('Hello, World!')
    >>>
    >>> if __name__ == '__main__':
    ...     app.run()
"""

__version__ = "0.1.0"
__author__ = "Pydance Team"
__email__ = "team@pydance.dev"

# Core framework components
from pydance.server.application import Application, Pydance
from pydance.http import Request, Response
from pydance.config.settings import settings
from pydance.exceptions import HTTPException, ValidationError

# Database components (optional)
try:
    from pydance.db import DatabaseConfig
    from pydance.db.connections import DatabaseConnection
except ImportError:
    DatabaseConfig = None
    DatabaseConnection = None

# Utility components (optional)
try:
    from pydance.events import get_event_bus
except ImportError:
    get_event_bus = None

try:
    from pydance.plugins import get_plugin_manager
except ImportError:
    get_plugin_manager = None

__all__ = [
    # Core
    'Application', 'Pydance',
    'Request', 'Response',
    'settings',

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
