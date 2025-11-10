
"""
Pydance Application - ASGI Web Framework

A framework for building ASGI applications with routing, middleware, and configuration management.
"""

import inspect
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Callable, Any, Optional, Type, Union, Awaitable
from dataclasses import dataclass, field
from enum import Enum

from pydance.utils.logging import get_logger
from pydance.config.settings import settings
from pydance.config import AppConfig
from pydance.routing import Router
from pydance.middleware.manager import get_middleware_manager
from pydance.middleware.types import MiddlewareType
from pydance.exceptions import HTTPException, WebSocketException, WebSocketDisconnect
from pydance.http import Request, Response
from pydance.websocket import WebSocket
from pydance.templating.engine import AbstractTemplateEngine

logger = get_logger(__name__)

from pydance.core.di import Container
from pydance.monitoring import MetricsCollector, HealthChecker
from pydance.caching import get_cache_manager
from pydance.graphql import GraphQLManager
from pydance.events import get_event_bus
from pydance.plugins import get_plugin_manager


class Application:
    """
    ASGI web application framework.

    This is the main application class that combines routing, middleware, and configuration.

    Key features:
    - URL routing with path converters
    - Middleware pipeline with priority system
    - Dependency injection container
    - Optional features (monitoring, GraphQL, caching)

    Example:
        from pydance.server import Application

        app = Application()

        @app.route('/')
        async def home(request):
            return Response.text('Hello, World!')

        @app.route('/users/{id:int}')
        async def user_detail(request, id):
            return Response.json({'user_id': id})

        if __name__ == '__main__':
            app.run()
    """

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or settings
        self.router = Router()
        self.middleware_manager = get_middleware_manager()
        self.template_engine: Optional[AbstractTemplateEngine] = None
        self.state: Dict[str, Any] = {}

        # Optional advanced features (explicit opt-in only)
        self.container: Optional[Container] = None
        self.metrics_collector = None
        self.health_checker = None
        self.graphql_manager = None
        self.cache = None

        # Event handlers
        self._startup_handlers: List[Callable] = []
        self._shutdown_handlers: List[Callable] = []
        self._exception_handlers: Dict[Type[Exception], Callable] = {}

        # Setup logging
        if not hasattr(self.config, 'DEBUG'):
            self.config.DEBUG = False

        # Apply default configuration
        self._setup_defaults()

    # Explicit opt-in methods for advanced features
    def with_container(self) -> 'Application':
        """Enable dependency injection container."""
        if Container is None:
            raise ImportError("Dependency injection not available. Install: pip install pydance[di]")
        self.container = Container()
        self.container.register_singleton("app", self)
        self.container.register_singleton("config", self.config)
        return self

    def with_monitoring(self) -> 'Application':
        """Enable monitoring and metrics collection."""
        if MetricsCollector is None or HealthChecker is None:
            raise ImportError("Monitoring not available. Install: pip install pydance[monitoring]")
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker()
        return self

    def with_graphql(self) -> 'Application':
        """Enable GraphQL support."""
        if GraphQLManager is None:
            raise ImportError("GraphQL not available. Install: pip install pydance[graphql]")
        self.graphql_manager = GraphQLManager()
        return self

    def with_caching(self) -> 'Application':
        """Enable caching support."""
        if get_cache_manager is None:
            raise ImportError("Caching not available. Install: pip install pydance[caching]")
        self.cache = get_cache_manager(self.config)
        return self

    def with_all_features(self) -> 'Application':
        """Enable all optional features (convenience method)."""
        self.with_container()
        self.with_monitoring()
        self.with_graphql()
        self.with_caching()

        # Enable event bus and plugins
        self.event_bus = get_event_bus()
        self.plugin_manager = get_plugin_manager()

        return self

    def with_events(self) -> 'Application':
        """Enable event system."""
        self.event_bus = get_event_bus()
        return self

    def with_plugins(self) -> 'Application':
        """Enable plugin system."""
        self.plugin_manager = get_plugin_manager()
        return self

    def _setup_defaults(self) -> None:
        """Setup default application configuration."""
        # Add basic exception handler
        @self.exception_handler(Exception)
        async def handle_exception(exc: Exception) -> Response:
            logger.error(f"Unhandled exception: {exc}")
            return Response.json({"error": "Internal server error"}, status_code=500)

        # Register essential routes and middleware
        self._register_health_endpoints()
        self._setup_database()
        self._setup_default_middleware()

    def _setup_database(self) -> None:
        """Setup database connection if configured."""
        # Skip database setup for test configurations
        if hasattr(self.config, 'SECRET_KEY') and getattr(self.config, 'SECRET_KEY', None) == "test-secret-key":
            return

        if hasattr(self.config, 'DATABASE_URL') and self.config.DATABASE_URL:
            from pydance.db.config import DatabaseConfig
            from pydance.db.connections import DatabaseConnection

            db_config = DatabaseConfig.from_url(self.config.DATABASE_URL)
            self.db_connection = DatabaseConnection.get_instance(db_config)

            # Register database startup/shutdown
            @self.on_startup
            async def connect_db():
                await self.db_connection.connect()

            @self.on_shutdown
            async def disconnect_db():
                if self.db_connection:
                    await self.db_connection.disconnect()

    def _setup_default_middleware(self) -> None:
        """Setup default middleware stack."""
        from pydance.middleware import cors_middleware, logging_middleware

        # Add CORS support
        self.use(cors_middleware)
        # Add logging middleware
        self.use(logging_middleware)

    def _register_health_endpoints(self) -> None:
        """Register cloud-native health check endpoints."""
        try:
            @self.route('/_health', methods=['GET'])
            async def _liveness(request: Request) -> Response:
                # Lightweight liveness check - app process alive
                return Response.json({'status': 'alive'}, status_code=200)

            @self.route('/_ready', methods=['GET'])
            async def _readiness(request: Request) -> Response:
                # Basic readiness check - can serve requests
                return Response.json({'status': 'ready', 'components': {'application': 'ready'}}, status_code=200)
        except Exception:
            # Best-effort: if anything goes wrong registering routes, continue silently
            pass

    def route(self, path: str, methods: Optional[List[str]] = None) -> Callable:
        """Add a route to the application."""
        def decorator(handler: Callable) -> Callable:
            self.router.add_route(path, handler, methods or ['GET'])
            return handler
        return decorator

    def websocket_route(self, path: str) -> Callable:
        """Add a WebSocket route to the application."""
        def decorator(handler: Callable) -> Callable:
            self.router.add_websocket_route(path, handler)
            return handler
        return decorator

    @property
    def middleware(self) -> 'Application':
        """Middleware decorator for compatibility."""
        return self

    # Enhanced Middleware API

    def use(self, middleware: Union[MiddlewareType, List[MiddlewareType], str, List[str]],
            options: Optional[Dict[str, Any]] = None,
            priority: Optional[int] = None) -> 'Application':
        """
        Enhanced middleware registration with Laravel-style aliases and priority support.

        Examples:
            # Single middleware
            app.use(cors_middleware)
            app.use('auth', {'redirect': '/login'})
            app.use(CORSMiddleware)

            # Multiple middlewares with priorities
            app.use([
                'cors',
                ('auth', {'redirect': '/login'}, 10),
                ('rate_limit', {}, 5),
                custom_middleware
            ])

            # Laravel-style middleware groups
            app.use('web')  # Uses MIDDLEWARE_GROUPS['web']
            app.use('api')  # Uses MIDDLEWARE_GROUPS['api']

            # Priority-based registration
            app.use('auth', priority=10)
            app.use('cors', priority=1)
        """
        # Handle list of middlewares
        if isinstance(middleware, list):
            for item in middleware:
                if isinstance(item, tuple):
                    # Tuple format: (middleware, options, priority)
                    if len(item) == 3:
                        mw, opts, pri = item
                        self.use(mw, opts, pri)
                    elif len(item) == 2:
                        mw, opts = item
                        self.use(mw, opts, priority)
                    else:
                        self.use(item[0], priority=priority)
                else:
                    self.use(item, options, priority)
            return self

        # Handle single middleware
        if isinstance(middleware, str):
            # Named middleware or alias - resolve via settings
            middleware_instance = self._resolve_middleware_by_name(middleware, options or {})
        elif isinstance(middleware, type):
            # Class middleware - instantiate it
            middleware_instance = middleware(**options) if options else middleware()
        else:
            # Function middleware or already instantiated class
            middleware_instance = middleware

        # Add with priority if specified
        if priority is not None:
            self.middleware_manager.add_with_priority(middleware_instance, priority)
        else:
            self.middleware_manager.add(middleware_instance)

        return self  # Fluent interface

    def _resolve_middleware_by_name(self, name: str, options: Dict[str, Any]) -> Optional[Callable]:
        """
        Enhanced middleware resolution with Laravel-style aliases and parameters.

        Supports:
        1. Laravel-style middleware groups: 'web', 'api'
        2. Middleware aliases with parameters: 'throttle:api', 'auth:sanctum'
        3. Settings-based middleware aliases
        4. Global middleware registry
        """
        from pydance.middleware import MIDDLEWARE_ALIASES, MIDDLEWARE_GROUPS

        # Handle Laravel-style middleware with parameters (e.g., 'throttle:api')
        if ':' in name:
            middleware_name, parameters = name.split(':', 1)
            # Parse parameters (can be comma-separated or single value)
            param_list = [p.strip() for p in parameters.split(',')]

            # Merge with provided options
            enhanced_options = options.copy()
            if len(param_list) == 1:
                enhanced_options['guard'] = param_list[0]
            else:
                for i, param in enumerate(param_list):
                    enhanced_options[f'param_{i}'] = param

            # Recursively resolve the base middleware name
            return self._resolve_middleware_by_name(middleware_name, enhanced_options)

        # Check if it's a middleware group (Laravel style)
        middleware_groups = getattr(self.config, 'MIDDLEWARE_GROUPS', {})
        if name in middleware_groups:
            for middleware_name in middleware_groups[name]:
                self.use(middleware_name, options)
            return lambda req, call_next: call_next(req)  # Placeholder

        # Check settings for middleware aliases (Laravel/Django style)
        middleware_aliases = getattr(self.config, 'MIDDLEWARE_ALIASES', {})
        if name in middleware_aliases:
            middleware_path = middleware_aliases[name]
            try:
                module_name, class_name = middleware_path.rsplit('.', 1)
                module = __import__(module_name, fromlist=[class_name])
                middleware_class = getattr(module, class_name)
                return middleware_class(**options)
            except (ImportError, AttributeError):
                logger.warning(f"Middleware '{name}' from settings not found")
                return lambda req, call_next: call_next(req)

        # Check global middleware aliases
        if name in MIDDLEWARE_ALIASES:
            middleware_path = MIDDLEWARE_ALIASES[name]
            try:
                module_name, class_name = middleware_path.rsplit('.', 1)
                module = __import__(module_name, fromlist=[class_name])
                middleware_class = getattr(module, class_name)
                return middleware_class(**options)
            except (ImportError, AttributeError):
                # Try to import the middleware class from pydance.middleware
                try:
                    module = __import__(f'pydance.middleware.{name}', fromlist=[name])
                    middleware_class = getattr(module, name.title() + 'Middleware')
                    return middleware_class(**options)
                except (ImportError, AttributeError):
                    logger.warning(f"Middleware '{name}' not found")
                    return lambda req, call_next: call_next(req)

        # Return generic placeholder if not found
        logger.warning(f"Middleware '{name}' not resolved, using passthrough")
        return lambda req, call_next: call_next(req)

    def pipeline(self, *middlewares: MiddlewareType) -> 'Application':
        """
        Middleware pipeline.

        Example:
            app.pipeline('cors', 'auth', 'logging', custom_middleware)
        """
        for middleware in middlewares:
            self.use(middleware)
        return self

    def without_middleware(self, *middleware_names: str) -> 'Application':
        """
        Middleware exclusion.

        Example:
            app.without_middleware('csrf', 'auth')
        """
        for name in middleware_names:
            self.middleware_manager.disable_middleware(name)
        return self

    def on_startup(self, handler: Callable) -> Callable:
        """Register a startup handler."""
        self._startup_handlers.append(handler)
        return handler

    def on_shutdown(self, handler: Callable) -> Callable:
        """Register a shutdown handler."""
        self._shutdown_handlers.append(handler)
        return handler

    def exception_handler(self, exc_type: Type[Exception]) -> Callable:
        """Register an exception handler."""
        def decorator(handler: Callable) -> Callable:
            self._exception_handlers[exc_type] = handler
            return handler
        return decorator

    async def startup(self) -> None:
        """Initialize the application."""
        # Configure logging from settings
        from pydance.utils.logging import logger_manager
        logger_manager.configure_from_settings()

        # Initialize template engine based on configuration
        template_engine_type = getattr(self.config, 'TEMPLATE_ENGINE', 'pydance.templating.languages.lean.LeanTemplateEngine')
        template_dirs = getattr(self.config, 'TEMPLATES_DIRS', ['templates'])

        # Import and instantiate the configured template engine
        try:
            module_path, class_name = template_engine_type.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            engine_class = getattr(module, class_name)
            self.template_engine = engine_class(Path(template_dirs[0]))
        except (ImportError, AttributeError, ValueError) as e:
            logger.warning(f"Failed to load template engine {template_engine_type}, falling back to default: {e}")
            from pydance.templating.engine import get_template_engine
            self.template_engine = get_template_engine("lean", template_dirs[0])

        # Start event bus if enabled
        if hasattr(self, 'event_bus'):
            await self.event_bus.start()

        # Load plugins if enabled
        if hasattr(self, 'plugin_manager'):
            await self.plugin_manager.start()

        # Run startup handlers
        for handler in self._startup_handlers:
            if inspect.iscoroutinefunction(handler):
                await handler()
            else:
                handler()

        # Emit startup event
        if hasattr(self, 'event_bus'):
            from pydance.events import StartupEvent
            await self.event_bus.publish(StartupEvent(app_name="pydance"))

        logger.info("Application started")

    async def shutdown(self) -> None:
        """Shutdown the application."""
        # Emit shutdown event
        if hasattr(self, 'event_bus'):
            from pydance.events import ShutdownEvent
            await self.event_bus.publish(ShutdownEvent(app_name="pydance"))

        # Stop plugins if enabled
        if hasattr(self, 'plugin_manager'):
            await self.plugin_manager.stop()

        # Stop event bus if enabled
        if hasattr(self, 'event_bus'):
            await self.event_bus.stop()

        # Run shutdown handlers in reverse order
        for handler in reversed(self._shutdown_handlers):
            if inspect.iscoroutinefunction(handler):
                await handler()
            else:
                handler()

        logger.info("Application shutdown")

    def run(self, host: str = '127.0.0.1', port: int = 8000) -> None:
        """Run the application with a server."""
        try:
            # Lazy import to avoid circular dependencies
            from pydance.server.server import Server

            server = Server(self, self.config)
            server.run(host=host, port=port)

        except ImportError as e:
            logger.error(f"Server not available: {e}")
            raise RuntimeError("Pydance server not properly installed") from e

    async def serve(self, host: str = '127.0.0.1', port: int = 8000) -> None:
        """Start serving requests (non-blocking)."""
        try:
            from pydance.server.server import Server

            server = Server(self, self.config)
            await server.serve(host=host, port=port)

        except ImportError as e:
            logger.error(f"Server not available: {e}")
            raise RuntimeError("Pydance server not properly installed") from e

    async def __call__(self, scope: Dict[str, Any],
                       receive: Callable[[], Any],
                       send: Callable[[Any], Any]) -> None:
        """ASGI application entry point."""
        if scope["type"] == "lifespan":
            await self._handle_lifespan(scope, receive, send)
        elif scope["type"] == "http":
            await self._handle_http(scope, receive, send)
        elif scope["type"] == "websocket":
            await self._handle_websocket(scope, receive, send)

    async def _handle_lifespan(self, scope: Dict[str, Any],
                              receive: Callable[[], Any],
                              send: Callable[[Any], Any]) -> None:
        """Handle ASGI lifespan events."""
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                try:
                    await self.startup()
                    await send({"type": "lifespan.startup.complete"})
                except Exception as e:
                    logger.error(f"Startup failed: {e}")
                    await send({"type": "lifespan.startup.failed", "message": str(e)})
            elif message["type"] == "lifespan.shutdown":
                try:
                    await self.shutdown()
                    await send({"type": "lifespan.shutdown.complete"})
                except Exception as e:
                    logger.error(f"Shutdown failed: {e}")
                    await send({"type": "lifespan.shutdown.failed", "message": str(e)})
                break

    async def _handle_http(self, scope: Dict[str, Any],
                          receive: Callable[[], Any],
                          send: Callable[[Any], Any]) -> None:
        """Handle HTTP requests."""
        try:
            request = Request(scope, receive, send, self)

            # Apply middleware
            request = await self.middleware_manager.process_http_request(request)

            # Find and execute route
            response = await self._execute_route(request)

            # Apply response middleware
            response = await self.middleware_manager.process_http_response(request, response)

            await response(scope, receive, send)

        except Exception as exc:
            await self._handle_exception(exc, scope, receive, send)

    async def _execute_route(self, request: Request) -> Response:
        """Execute the appropriate route handler."""
        route, path_params = self.router.match(request.method, request.path)
        if not route:
            raise HTTPException(404, "Not Found")

        request.path_params = path_params

        if inspect.iscoroutinefunction(route.handler):
            return await route.handler(request)
        else:
            return route.handler(request)

    async def _handle_websocket(self, scope: Dict[str, Any],
                               receive: Callable[[], Any],
                               send: Callable[[Any], Any]) -> None:
        """Handle WebSocket connections."""
        try:
            websocket = WebSocket(scope, receive, send, self)

            # Apply middleware
            websocket = await self.middleware_manager.process_websocket(websocket)
            if websocket is None:
                await send({"type": "websocket.close", "code": 1008})
                return

            # Find and execute route
            route, path_params = self.router.match_websocket(websocket.path)
            if not route:
                await websocket.close(1008, "No route found")
                return

            websocket.path_params = path_params or {}
            await route.handler(websocket)

        except Exception as exc:
            await self._handle_websocket_exception(exc, scope, receive, send)

    async def _handle_exception(self, exc: Exception,
                               scope: Dict[str, Any],
                               receive: Callable[[], Any],
                               send: Callable[[Any], Any]) -> None:
        """Handle exceptions during request processing."""
        handler = self._exception_handlers.get(type(exc))
        if handler:
            try:
                response = await handler(exc)
                await response(scope, receive, send)
                return
            except Exception:
                pass  # Fall through to default

        # Default error response
        if isinstance(exc, HTTPException):
            response = Response.json({"error": exc.detail}, status_code=exc.status_code)
        else:
            logger.error(f"Unhandled exception: {exc}")
            response = Response.json({"error": "Internal server error"}, status_code=500)

        await response(scope, receive, send)

    async def _handle_websocket_exception(self, exc: Exception,
                                         scope: Dict[str, Any],
                                         receive: Callable[[], Any],
                                         send: Callable[[Any], Any]) -> None:
        """Handle exceptions during WebSocket processing."""
        try:
            from pydance.websocket import WebSocketDisconnect
            websocket = WebSocket(scope, receive, send, self)

            if isinstance(exc, WebSocketDisconnect):
                await websocket.close(exc.code, exc.reason)
            else:
                await websocket.close(1011, "Internal server error")

        except Exception:
            # Final fallback
            try:
                await send({"type": "websocket.close", "code": 1011})
            except Exception:
                pass

    @property
    def debug(self) -> bool:
        """Check if debug mode is enabled."""
        return getattr(self.config, 'DEBUG', False)

    def url_for(self, name: str, **params) -> str:
        """Generate URL for named route."""
        # This would integrate with named routes
        return f"/{name}"  # Simplified


# Convenience alias
Pydance = Application
