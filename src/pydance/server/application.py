"""
Pydance Application - Enterprise ASGI Web Framework
A high-performance framework combining modern patterns from Express, Django, and Laravel.
"""

import inspect
from typing import Dict, List, Callable, Any, Optional, Type, Union
import logging

from pydance.config.settings import settings
from pydance.config import AppConfig
from pydance.routing import Router
from pydance.middleware.manager import MiddlewareManager, get_middleware_manager
from pydance.exceptions import HTTPException, WebSocketException, WebSocketDisconnect
from pydance.http import Request, Response
from pydance.websocket import WebSocket
from pydance.templating import TemplateEngine

logger = logging.getLogger(__name__)

from pydance.utils.di import Container
from pydance.monitoring import MetricsCollector, HealthChecker
from pydance.caching import get_cache_manager
from pydance.graphql import GraphQLManager


class Application:
    """
    Modern ASGI web application framework.

    Example:
        from pydance.server import Application

        app = Application()

        @app.route('/')
        async def home(request):
            return Response.text('Hello, World!')

        if __name__ == '__main__':
            app.run()
    """

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or settings
        self.router = Router()
        self.middleware_manager = MiddlewareManager()
        self.template_engine: Optional[TemplateEngine] = None
        self.state: Dict[str, Any] = {}

        # Optional advanced features (explicit opt-in only)
        self.container: Optional[Container] = None
        self.metrics_collector = None
        self.health_checker = None
        self.graphql_manager = None
        self.cache = None

        # Event handlers (Express style)
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
        """Enable dependency injection container (Laravel/Django style)."""
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
        try:
            self.with_container()
        except ImportError:
            pass

        try:
            self.with_monitoring()
        except ImportError:
            pass

        try:
            self.with_graphql()
        except ImportError:
            pass

        try:
            self.with_caching()
        except ImportError:
            pass

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
        if hasattr(self.config, 'DATABASE_URL') and self.config.DATABASE_URL:
            try:
                from pydance.db import DatabaseConfig
                from pydance.db.connections import DatabaseConnection

                db_config = DatabaseConfig(self.config.DATABASE_URL)
                self.db_connection = DatabaseConnection.get_instance(db_config)

                # Register database startup/shutdown
                @self.on_startup
                async def connect_db():
                    await self.db_connection.connect()

                @self.on_shutdown
                async def disconnect_db():
                    if self.db_connection:
                        await self.db_connection.disconnect()

            except ImportError:
                logger.warning("Database modules not available, continuing without database support")

    def _setup_default_middleware(self) -> None:
        """Setup default middleware stack."""
        try:
            from pydance.middleware import CORSMiddleware, LoggingMiddleware

            # Add CORS support
            self.add_middleware(CORSMiddleware())
            # Add logging middleware
            self.add_middleware(LoggingMiddleware())

        except ImportError:
            # Best-effort: if middleware not available, continue silently
            pass

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

    # Middleware API - combining Express, Django, and Laravel patterns

    def use(self, middleware: Union[Callable, str], options: Optional[Dict[str, Any]] = None) -> 'Application':
        """
        Express.js style middleware registration.

        Examples:
            app.use(cors_middleware)
            app.use('auth', {'redirect': '/login'})
            app.use(lambda req, call_next: call_next(req))
        """
        if isinstance(middleware, str):
            # Laravel-style named middleware
            middleware_instance = self._resolve_middleware_by_name(middleware, options or {})
        else:
            middleware_instance = middleware

        self.middleware_manager.add(middleware_instance)
        return self  # Fluent interface

    def middleware(self, *middleware_list: Union[str, Callable], **options) -> 'Application':
        """
        Laravel-style middleware registration with groups.

        Examples:
            app.middleware('auth', 'throttle:60,1', cors_middleware)
            app.middleware('web')  # Group
        """
        for middleware in middleware_list:
            if isinstance(middleware, str):
                if ':' in middleware:
                    # Laravel-style with parameters (throttle:60,1)
                    name, params = middleware.split(':', 1)
                    middleware_instance = self._resolve_middleware_by_name(name, {'params': params})
                else:
                    # Named middleware or group
                    middleware_instance = self._resolve_middleware_by_name(middleware, options)
            else:
                middleware_instance = middleware

            self.middleware_manager.add(middleware_instance)

        return self  # Fluent interface

    def add_middleware(self, middleware: Union[Callable, Type], priority: Optional[int] = None) -> None:
        """
        Django-style middleware registration.

        Example:
            app.add_middleware(CORSMiddleware)
            app.add_middleware('django.middleware.security.SecurityMiddleware')
        """
        if priority is not None:
            # Handle priority if middleware manager supports it
            if hasattr(self.middleware_manager, 'add_with_priority'):
                self.middleware_manager.add_with_priority(middleware, priority)
            else:
                self.middleware_manager.add(middleware)
        else:
            self.middleware_manager.add(middleware)

    def _resolve_middleware_by_name(self, name: str, options: Dict[str, Any]) -> Optional[Callable]:
        """
        Laravel-style middleware resolution by name or group.

        Looks up middleware in:
        1. Application middleware aliases
        2. Global middleware registry
        3. Middleware groups
        """
        from pydance.middleware import MIDDLEWARE_ALIASES, MIDDLEWARE_GROUPS

        # Check if it's a middleware group
        if name in MIDDLEWARE_GROUPS:
            for middleware_name in MIDDLEWARE_GROUPS[name]:
                self.use(middleware_name, options)
            return lambda req, call_next: call_next(req)  # Placeholder

        # Check middleware aliases
        if name in MIDDLEWARE_ALIASES:
            middleware_path = MIDDLEWARE_ALIASES[name]
            try:
                module_name, class_name = middleware_path.rsplit('.', 1)
                module = __import__(module_name, fromlist=[class_name])
                middleware_class = getattr(module, class_name)
                return middleware_class(**options)
            except (ImportError, AttributeError):
                # Try to import the middleware class
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

    # Pipeline method for chaining (Express.js style)
    def pipeline(self, *middlewares: Union[str, Callable]) -> 'Application':
        """
        Express.js style middleware pipeline.

        Example:
            app.pipeline('cors', 'auth', 'logging', custom_middleware)
        """
        for middleware in middlewares:
            self.use(middleware)
        return self

    # Django-style middleware exclusion
    def without_middleware(self, *middleware_names: str) -> 'Application':
        """
        Laravel/Django style middleware exclusion.

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
        # Initialize template engine
        template_dir = getattr(self.config, 'template_dir', 'templates')
        self.template_engine = TemplateEngine(template_dir)

        # Run startup handlers
        for handler in self._startup_handlers:
            if inspect.iscoroutinefunction(handler):
                await handler()
            else:
                handler()

        logger.info("Application started")

    async def shutdown(self) -> None:
        """Shutdown the application."""
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
