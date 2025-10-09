"""Middleware-related type definitions."""

from typing import Callable, Any, Union, Coroutine
from pydance.http.types import Handler, AsyncHandler

# Middleware types
Middleware = Callable[[Handler], Handler]
AsyncMiddleware = Callable[[AsyncHandler], AsyncHandler]
MiddlewareCallable = Callable[[Any, Callable], Coroutine[Any, Any, Any]]
MiddlewareType = Union[MiddlewareCallable, type]

__all__ = [
    'Middleware', 'AsyncMiddleware',
    'MiddlewareCallable', 'MiddlewareType'
]
