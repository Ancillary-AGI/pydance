"""HTTP-related type definitions."""

from typing import Dict, List, Any, Callable, Awaitable, Union
from dataclasses import dataclass, field

# ASGI types
Scope = Dict[str, Any]
Message = Dict[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

# Handler types
Handler = Callable[..., Any]
AsyncHandler = Callable[..., Awaitable[Any]]
RouteHandler = Union[Handler, AsyncHandler]

# HTTP types
PathParams = Dict[str, Any]
QueryParams = Dict[str, str]
Headers = Dict[str, str]
Cookies = Dict[str, str]
RequestBody = Union[str, bytes, Dict[str, Any], List[Any], None]
ResponseBody = Union[str, bytes, Dict[str, Any], List[Any], None]

__all__ = [
    'Scope', 'Message', 'Receive', 'Send', 'ASGIApp',
    'Handler', 'AsyncHandler', 'RouteHandler',
    'PathParams', 'QueryParams', 'Headers', 'Cookies',
    'RequestBody', 'ResponseBody'
]
