"""Middleware-related type definitions."""

from typing import Callable, Any, Union, Type, Coroutine

# Import all middleware types from base.py to consolidate
    BaseMiddleware,
    HTTPMiddleware,
    WebSocketMiddleware,
    MiddlewareScope,
    MiddlewareContext,
)

# Consolidated middleware types (merged from base.py)

MiddlewareCallable = Callable[[Request, Callable], Coroutine[Any, Any, Response]]
MiddlewareClass = Union[MiddlewareCallable, type[HTTPMiddleware], type[WebSocketMiddleware]]

# Unified middleware type that supports all middleware forms
MiddlewareType = Union[
    MiddlewareCallable,     # Function middleware
    Type[BaseMiddleware],   # Class middleware (not callable)
    str                     # String aliases
]

# Alias for backward compatibility
Middleware = BaseMiddleware

# Middleware registration and resolution types
MiddlewareAlias = str  # String alias like 'auth', 'throttle:100,10'
MiddlewareGroup = list[MiddlewareAlias]  # Group of middleware aliases

__all__ = [
    # Core middleware types
    'BaseMiddleware', 'HTTPMiddleware', 'WebSocketMiddleware',
    'MiddlewareCallable', 'MiddlewareType', 'MiddlewareClass',

    # Enums and contexts
    'MiddlewareScope', 'MiddlewareContext',

    # Registration types
    'MiddlewareAlias', 'MiddlewareGroup'
]
