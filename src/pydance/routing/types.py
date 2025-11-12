from typing import Callable, Any, Awaitable
from enum import Enum

class HandlerType(Enum):
    """Handler type enumeration."""
    HTTP = "http"
    WEBSOCKET = "websocket"
    MIDDLEWARE = "middleware"
    ASYNC = "async"
    SYNC = "sync"


# Type aliases for better code readability
RouteHandler = Callable[['Request'], 'Response']
AsyncRouteHandler = Callable[['Request'], Awaitable['Response']]
WebSocketHandler = Callable[[Any], Any]
MiddlewareHandler = Callable[[Any, Callable], Any]
ErrorHandler = Callable[[Exception], 'Response']

# Additional routing types
RouteMiddleware = Callable[[Any, Callable], Awaitable[Any]]
RouteDecorator = Callable[[Callable], Callable]
RouteCondition = Callable[['Request'], bool]

# Route configuration and matching types
class RouteType(Enum):
    """Route type enumeration."""
    HTTP = "http"
    WEBSOCKET = "websocket"
    STATIC = "static"
    REDIRECT = "redirect"

class RouteMatch:
    """Route match result."""
    def __init__(self, route_handler: Callable, params: dict = None, route_type: RouteType = RouteType.HTTP):
        self.route_handler = route_handler
        self.params = params or {}
        self.route_type = route_type

class RouteConfig:
    """Route configuration."""
    def __init__(self,
                 path: str,
                 handler: Callable,
                 methods: list = None,
                 name: str = None,
                 middleware: list = None,
                 route_type: RouteType = RouteType.HTTP):
        self.path = path
        self.handler = handler
        self.methods = methods or ['GET']
        self.name = name
        self.middleware = middleware or []
        self.route_type = route_type

__all__ = [
    'HandlerType',
    'RouteHandler',
    'AsyncRouteHandler',
    'WebSocketHandler',
    'MiddlewareHandler',
    'ErrorHandler',
    'RouteMiddleware',
    'RouteDecorator',
    'RouteCondition',
    'RouteType',
    'RouteMatch',
    'RouteConfig'
]
