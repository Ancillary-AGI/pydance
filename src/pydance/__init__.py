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

# Database components
from pydance.db import DatabaseConfig
from pydance.db.connections import DatabaseConnection
from pydance.db.models import BaseModel

# Utility components
from pydance.events import EventBus, Event, get_event_bus
from pydance.plugins import PluginManager, Plugin, get_plugin_manager
from pydance.storage import get_storage_manager
from pydance.caching import get_cache_manager

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
    'get_storage_manager',
    'get_cache_manager',

    # Exceptions
    'HTTPException', 'ValidationError',
]
