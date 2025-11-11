
from pydance.utils.logging import get_logger
"""
Pydance Router - Simple ASGI router for web applications.

Features:
- Basic pattern matching
- Route registration
- WebSocket support
- Simple middleware per route
"""

from typing import Callable, List, Optional, Dict, Any, Tuple, Union, Set
import logging
from dataclasses import dataclass, field
import re
from collections import defaultdict
from functools import lru_cache
import asyncio

logger = get_logger(__name__)

from pydance.routing.route import Route
from pydance.middleware.base import MiddlewareType
from pydance.core.events import get_event_bus


@dataclass
class RouteMatch:
    """Route match result"""
    handler: Callable
    params: Dict[str, Any]
    route: 'Route'
    middleware: List[MiddlewareType]


class Router:
    """
    High-performance ASGI router with advanced features.

    Features:
    - Fast pattern matching with caching
    - Type-safe parameter extraction
    - Middleware support per route
    - Route groups and prefixes
    - WebSocket route handling
    - Performance monitoring
    - Named routes and URL reversal
    - Redirect support (301/302)
    - View-based routes
    - Fallback routes
    """

    def __init__(self):
        self.routes: List[Route] = []
        self.websocket_routes: List[Route] = []
        self.mounted_routers: Dict[str, 'Router'] = {}
        self.named_routes: Dict[str, Route] = {}
        self._route_cache: Dict[str, Tuple[Optional[Route], Optional[Dict[str, str]]]] = {}
        self._cache_enabled = True
        self.fallback_route: Optional[Route] = None
        self.intended_url: Optional[str] = None
        self._redirects: Dict[str, str] = {}
        self._reverse_redirects: Dict[str, str] = {}

    def add_route(
        self,
        path: str,
        handler: Callable,
        methods: Optional[Union[List[str], Set[str]]] = None,
        name: Optional[str] = None,
        middleware: Optional[List[MiddlewareType]] = None,
        **kwargs
    ) -> Route:
        """Add HTTP route to router."""
        route = Route(path, handler, methods, name, middleware, **kwargs)
        self.routes.append(route)

        if name:
            self.named_routes[name] = route

        # Clear cache when routes change
        self._route_cache.clear()
        return route

    def add_websocket_route(
        self,
        path: str,
        handler: Callable,
        name: Optional[str] = None,
        middleware: Optional[List[MiddlewareType]] = None,
        **kwargs
    ) -> Route:
        """Add WebSocket route to router."""
        route = Route(path, handler, ["GET"], name, middleware, **kwargs)
        self.websocket_routes.append(route)

        if name:
            self.named_routes[name] = route

        self._route_cache.clear()
        return route

    def add(self, path: str, handler: Callable, methods: Optional[List[str]] = None) -> None:
        """Add route to router."""
        route = Route(path, handler, methods)
        self.routes.append(route)
        self._route_cache.clear()  # Clear cache when routes change

    def match(self, method: str, path: str) -> Optional[RouteMatch]:
        """
        Match HTTP request to route with caching.

        Returns:
            RouteMatch object or None if no match
        """
        cache_key = f"{method}:{path}"

        # Check cache first
        if cache_key in self._route_cache:
            cached = self._route_cache[cache_key]
            if cached:
                return cached
            return None

        # Check mounted routers first
        for mount_path, router in self.mounted_routers.items():
            if path.startswith(mount_path):
                remaining_path = path[len(mount_path):]
                match_result = router.match(method, remaining_path)
                if match_result:
                    if self._cache_enabled:
                        self._route_cache[cache_key] = match_result
                    return match_result

        # Find matching route (sorted by priority)
        for route in sorted(self.routes, key=lambda r: r.config.get('priority', 0), reverse=True):
            params = route.match(path, method)
            if params is not None:
                # Create RouteMatch object
                route_match = RouteMatch(
                    handler=route.handler,
                    params=params,
                    route=route,
                    middleware=route.middleware
                )
                # Cache positive result
                self._route_cache[cache_key] = route_match
                return route_match

        # Cache negative result
        self._route_cache[cache_key] = None
        return None

    def match_websocket(self, path: str) -> Optional[RouteMatch]:
        """Match WebSocket connection."""
        cache_key = f"WS:{path}"

        if cache_key in self._route_cache:
            cached = self._route_cache[cache_key]
            if cached:
                return cached
            return None

        for route in self.websocket_routes:
            params = route.match(path, "GET")
            if params is not None:
                # Create RouteMatch object for WebSocket
                route_match = RouteMatch(
                    handler=route.handler,
                    params=params,
                    route=route,
                    middleware=route.middleware
                )
                self._route_cache[cache_key] = route_match
                return route_match

        self._route_cache[cache_key] = None
        return None

    def find_websocket_route(self, path: str) -> Optional[RouteMatch]:
        """Find WebSocket route (alias for match_websocket)."""
        return self.match_websocket(path)

    def get_route_by_name(self, name: str) -> Optional[Route]:
        """Get route by name."""
        return self.named_routes.get(name)

    def reverse(self, name: str, **kwargs) -> Optional[str]:
        """Reverse route by name with parameters."""
        route = self.get_route_by_name(name)
        if not route:
            return None

        path = route.path
        for param_name, param_value in kwargs.items():
            placeholder = f"<{param_name}>"
            if placeholder in path:
                path = path.replace(placeholder, str(param_value))

        return path

    def group(self, prefix: str = "", middleware: Optional[List] = None, name_prefix: str = "") -> 'RouteGroup':
        """Create route group with prefix."""
        return RouteGroup(self, prefix, middleware or [], name_prefix)

    def mount(self, path: str, other_router: 'Router') -> None:
        """Mount another router at the given path."""
        self.mounted_routers[path] = other_router

    def clear_cache(self) -> None:
        """Clear route matching cache."""
        self._route_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        return {
            "total_routes": len(self.routes),
            "websocket_routes": len(self.websocket_routes),
            "mounted_routers": len(self.mounted_routers),
            "cache_size": len(self._route_cache),
            "named_routes": len(self.named_routes)
        }

    def add_permanent_redirect(self, from_path: str, to_path: str, name: Optional[str] = None):
        """Add a permanent redirect (301)."""
        def redirect_handler(request, **kwargs):
            from pydance.http.response import Response
            redirect_url = to_path
            # Replace parameters in redirect URL
            for key, value in kwargs.items():
                redirect_url = redirect_url.replace(f'{{{key}}}', str(value))
            return Response.redirect(redirect_url, 301)

        self.add_route(from_path, redirect_handler, name=name)

    def add_temporary_redirect(self, from_path: str, to_path: str, name: Optional[str] = None):
        """Add a temporary redirect (302)."""
        def redirect_handler(request, **kwargs):
            from pydance.http.response import Response
            redirect_url = to_path
            # Replace parameters in redirect URL
            for key, value in kwargs.items():
                redirect_url = redirect_url.replace(f'{{{key}}}', str(value))
            return Response.redirect(redirect_url, 302)

        self.add_route(from_path, redirect_handler, name=name)

    def find_route(self, path: str, method: str) -> tuple[Optional[Route], Optional[Dict[str, str]]]:
        """Find a route that matches the given path and method (alias for match)."""
        match_result = self.match(method, path)
        if match_result:
            return match_result.route, match_result.params
        return None, None

    def url_for(self, name: str, **kwargs) -> Optional[str]:
        """Generate URL for a named route."""
        route = self.get_route_by_name(name)
        if not route:
            return None

        url = route.path
        for key, value in kwargs.items():
            url = url.replace(f'{{{key}}}', str(value))
        return url

    def add_view_route(self, path: str, view_class: Any, methods: Optional[List[str]] = None,
                      name: Optional[str] = None, middleware: Optional[List] = None,
                      view_kwargs: Optional[Dict[str, Any]] = None):
        """Add a view-based route"""
        def view_handler(request, **kwargs):
            view_instance = view_class(**view_kwargs or {})
            return view_instance.dispatch(request, **kwargs)

        self.add_route(path, view_handler, methods, name, middleware)

    def add_fallback_route(self, path: str, handler: Callable, methods: Optional[List[str]] = None,
                          name: Optional[str] = None, middleware: Optional[List] = None):
        """Add a fallback route that catches unmatched requests"""
        self.add_route(path, handler, methods, name, middleware)

    def set_intended_url(self, url: str) -> None:
        """Set the intended URL for post-login redirects"""
        self.intended_url = url

    def get_intended_url(self, default: str = "/") -> str:
        """Get the intended URL, clearing it after retrieval"""
        url = self.intended_url or default
        self.intended_url = None
        return url

    def remember_intended_url(self, request) -> None:
        """Remember the current URL as intended for post-login redirect"""
        if hasattr(request, 'url'):
            self.intended_url = str(request.url)

    def resource(self, resource_name: str, controller: Any, only: Optional[List[str]] = None,
                 except_: Optional[List[str]] = None) -> None:
        """Add resource routes (RESTful routes) like Laravel's Route::resource()"""
        routes = {
            'index': {'path': '', 'method': 'GET'},
            'create': {'path': '/create', 'method': 'GET'},
            'store': {'path': '', 'method': 'POST'},
            'show': {'path': '/{id}', 'method': 'GET'},
            'edit': {'path': '/{id}/edit', 'method': 'GET'},
            'update': {'path': '/{id}', 'method': 'PUT'},
            'patch': {'path': '/{id}', 'method': 'PATCH'},
            'destroy': {'path': '/{id}', 'method': 'DELETE'}
        }

        # Filter routes based on 'only' and 'except'
        if only:
            routes = {k: v for k, v in routes.items() if k in only}
        if except_:
            routes = {k: v for k, v in routes.items() if k not in except_}

        for action, config in routes.items():
            path = f'/{resource_name}{config["path"]}'
            method = config['method']
            handler = getattr(controller, action, None)

            if handler:
                self.add_route(path, handler, [method], name=f'{resource_name}.{action}')

    def api_resource(self, resource_name: str, controller: Any, only: Optional[List[str]] = None,
                     except_: Optional[List[str]] = None) -> None:
        """Add API resource routes (without create/edit views)"""
        api_routes = ['index', 'store', 'show', 'update', 'patch', 'destroy']
        self.resource(resource_name, controller, only or api_routes, except_)

    def prefix(self, prefix: str, routes: List[Tuple[str, Callable, Optional[List[str]]]]) -> None:
        """Add multiple routes with a common prefix"""
        for path, handler, methods in routes:
            full_path = f'{prefix}{path}'
            self.add_route(full_path, handler, methods)

    def middleware(self, middleware: List[MiddlewareType], routes: List[Tuple[str, Callable, Optional[List[str]]]]) -> None:
        """Add multiple routes with common middleware"""
        for path, handler, methods in routes:
            self.add_route(path, handler, methods, middleware=middleware)

    def subdomain(self, subdomain: str, routes: List[Tuple[str, Callable, Optional[List[str]]]]) -> None:
        """Add routes for a specific subdomain"""
        for path, handler, methods in routes:
            # Note: Subdomain routing would need additional implementation in the server
            self.add_route(path, handler, methods, subdomain=subdomain)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get router performance metrics"""
        return {
            'cache_hit_rate': self._calculate_cache_hit_rate(),
            'total_matches': getattr(self, '_total_matches', 0),
            'average_match_time': getattr(self, '_average_match_time', 0),
            'routes_by_method': self._get_routes_by_method(),
            'most_frequent_routes': self._get_most_frequent_routes(),
            'cache_size': len(self._route_cache),
            'optimization_level': getattr(self, '_optimization_level', 'none')
        }

    def optimize_routes(self) -> None:
        """Optimize routes for better performance"""
        # Sort routes by specificity (more specific first)
        self.routes.sort(key=lambda r: len(r.path.split('/')), reverse=True)

        # Pre-compile regex patterns
        for route in self.routes:
            if hasattr(route, 'regex'):
                route.compiled_regex = re.compile(route.regex)

        # Clear cache after optimization
        self._route_cache.clear()

        # Set optimization level
        self._optimization_level = 'compiled'

        # Emit optimization event
        event_bus = get_event_bus()
        if event_bus:
            from pydance.core.events import Event
            asyncio.create_task(event_bus.publish(Event('router_optimized', {'router': self.__class__.__name__})))

    def enable_advanced_caching(self) -> None:
        """Enable advanced caching with LRU"""
        self._cache_enabled = True
        self._route_cache = {}  # Clear existing cache

        # Use LRU cache for match method
        self.match = lru_cache(maxsize=512)(self._match_uncached)

    def _match_uncached(self, method: str, path: str) -> Optional[RouteMatch]:
        """Uncachable version of match method"""
        # Implementation without caching
        for route in sorted(self.routes, key=lambda r: r.config.get('priority', 0), reverse=True):
            params = route.match(path, method)
            if params is not None:
                return RouteMatch(
                    handler=route.handler,
                    params=params,
                    route=route,
                    middleware=route.middleware
                )
        return None

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if not hasattr(self, '_cache_hits'):
            self._cache_hits = 0
        if not hasattr(self, '_cache_misses'):
            self._cache_misses = 0

        total = self._cache_hits + self._cache_misses
        return self._cache_hits / total if total > 0 else 0

    def _get_routes_by_method(self) -> Dict[str, int]:
        """Get count of routes by HTTP method"""
        method_counts = defaultdict(int)
        for route in self.routes:
            if route.methods:
                for method in route.methods:
                    method_counts[method] += 1
        return dict(method_counts)

    def _get_most_frequent_routes(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most frequently matched routes"""
        if not hasattr(self, '_route_frequency'):
            self._route_frequency = defaultdict(int)

        sorted_routes = sorted(self._route_frequency.items(), key=lambda x: x[1], reverse=True)
        return sorted_routes[:limit]

    async def optimize_routes(self) -> None:
        """Optimize routes for better performance"""
        # Sort routes by specificity (more specific first)
        self.routes.sort(key=lambda r: len(r.path.split('/')), reverse=True)

        # Pre-compile regex patterns
        for route in self.routes:
            if hasattr(route, 'regex'):
                route.compiled_regex = re.compile(route.regex)

        # Clear cache after optimization
        self._route_cache.clear()

        # Emit optimization event
        event_bus = get_event_bus()
        if event_bus:
            from pydance.events import Event
            await event_bus.publish(Event('router_optimized', {'router': self.__class__.__name__}))


class RouteGroup:
    """Route group for organizing routes with common prefix and middleware."""

    def __init__(self, router: Router, prefix: str = "", middleware: List[MiddlewareType] = None, name_prefix: str = ""):
        self.router = router
        self.prefix = prefix
        self.middleware = middleware or []
        self.name_prefix = name_prefix

    def add_route(
        self,
        path: str,
        handler: Callable,
        methods: Optional[Union[List[str], Set[str]]] = None,
        name: Optional[str] = None,
        middleware: Optional[List[MiddlewareType]] = None,
        **kwargs
    ) -> Route:
        """Add route to the group."""
        full_path = f"{self.prefix}{path}"
        full_name = f"{self.name_prefix}{name}" if name else None
        all_middleware = self.middleware + (middleware or [])

        return self.router.add_route(full_path, handler, methods, full_name, all_middleware, **kwargs)

    def group(self, prefix: str = "", middleware: Optional[List] = None, name_prefix: str = "") -> 'RouteGroup':
        """Create a nested route group."""
        new_prefix = f"{self.prefix}{prefix}"
        new_middleware = self.middleware + (middleware or [])
        new_name_prefix = f"{self.name_prefix}{name_prefix}"
        return RouteGroup(self.router, new_prefix, new_middleware, new_name_prefix)


# Global router instance
_default_router = Router()

def get_router() -> Router:
    """Get the default router instance"""
    return _default_router

__all__ = ['Router', 'Route', 'RouteGroup', 'RouteMatch', 'get_router']
