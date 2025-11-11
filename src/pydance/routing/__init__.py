"""
Pydance Routing System - Named routes with Laravel-style middleware and resourceful routing.

Ultra-high-performance routing with advanced features:
- Named routes with Laravel-style route() helper
- Middleware groups and aliases (Laravel-style)
- Resourceful routes (Route::resource() style)
- Route caching for maximum performance
- Parameter binding with type casting
- Route model binding
"""

from typing import Any
from pydance.routing.route import Route, WebSocketRoute
from pydance.routing.router import Router
from pydance.routing.types import RouteType, RouteMatch, RouteConfig

# Import middleware aliases and groups from middleware module to avoid duplication
from pydance.middleware import MIDDLEWARE_ALIASES, MIDDLEWARE_GROUPS

# Global router instance for named routes
# All named routes are stored in a single global router instance
# accessible throughout the application via the functions below

def route(name: str, parameters: dict = None) -> str:
    """
    Laravel-style route() helper for generating URLs from named routes.

    Uses the global router instance to resolve named routes.

    Args:
        name: Route name
        parameters: Route parameters

    Returns:
        URL string with parameters replaced

    Raises:
        ValueError: If route name not found
    """
    from .router import get_router
    router = get_router()
    return router.reverse(name, **(parameters or {}))

def register_route(name: str, pattern: str) -> None:
    """Register a named route pattern."""
    from .router import get_router
    router = get_router()
    # Create a dummy route for the pattern
    from .route import Route
    dummy_route = Route(pattern, lambda: None, name=name)
    router.named_routes[name] = dummy_route

def has_route(name: str) -> bool:
    """Check if a named route exists."""
    from .router import get_router
    router = get_router()
    return router.get_route_by_name(name) is not None

def list_routes() -> dict:
    """List all registered named routes."""
    from .router import get_router
    router = get_router()
    return {name: route.path for name, route in router.named_routes.items()}

def url(name: str, **parameters) -> str:
    """Alternative to route() function for URL generation."""
    return route(name, parameters)

def resource(resource_name: str, controller: Any, name: str = None) -> 'ResourceRoutes':
    """
    Create resourceful routes for a given resource.

    Similar to Laravel's Route::resource()
    """
    return ResourceRoutes(resource_name, controller, name)

class ResourceRoutes:
    """Resourceful route builder similar to Laravel."""

    def __init__(self, resource: str, controller: Any, name: str = None):
        self.resource = resource
        self.controller = controller
        self.name = name or resource

    def register(self, router: Router) -> None:
        """Register all resourceful routes."""
        base_url = f'/{self.resource}'
        base_name = self.name

        # Standard resourceful routes
        routes = [
            ('GET', base_url, f'{base_name}.index', 'index'),  # Index
            ('GET', f'{base_url}/create', f'{base_name}.create', 'create'),  # Create form
            ('POST', base_url, f'{base_name}.store', 'store'),  # Store
            ('GET', f'{base_url}/{{id}}', f'{base_name}.show', 'show'),  # Show
            ('GET', f'{base_url}/{{id}}/edit', f'{base_name}.edit', 'edit'),  # Edit form
            ('PUT', f'{base_url}/{{id}}', f'{base_name}.update', 'update'),  # Update
            ('PATCH', f'{base_url}/{{id}}', f'{base_name}.update', 'update'),  # Update (alternative)
            ('DELETE', f'{base_url}/{{id}}', f'{base_name}.destroy', 'destroy'),  # Destroy
        ]

        for method, path, route_name, action in routes:
            handler = getattr(self.controller, action, None)
            if handler:
                router.add_route(path, handler, [method], name=route_name)

def routes_from_app(app, prefix: str = ""):
    """Auto-discover routes from app views/controllers."""
    router = Router()

    # This would scan for route decorators in app modules
    # Implementation depends on how views/controllers are structured
    return router

class RouteServiceProvider:
    """Service provider for route management (Laravel-style)."""

    def __init__(self):
        self.router = Router()

    def register(self) -> None:
        """Register routes - override in subclasses."""
        pass

    def boot(self) -> None:
        """Boot routes - override in subclasses."""
        pass

    def map(self) -> Router:
        """Map all routes and return router."""
        self.register()
        self.boot()
        return self.router

__all__ = [
    'Route',
    'WebSocketRoute',
    'Router',
    'RouteType',
    'RouteGroup',
    'ResourceRoutes',
    'RouteServiceProvider',
    'MIDDLEWARE_ALIASES',
    'MIDDLEWARE_GROUPS',
    'route',
    'url',
    'resource',
    'register_route',
    'has_route',
    'list_routes',
    'routes_from_app',
]
