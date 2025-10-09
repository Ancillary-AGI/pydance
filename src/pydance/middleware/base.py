# server_framework/core/middleware.py
import time
import logging
from abc import ABC, abstractmethod
from typing import Callable, Any, Optional, Union, Coroutine, Dict, List
from dataclasses import dataclass, field
from enum import Enum
from contextvars import ContextVar

from pydance.http.request import Request
from pydance.http.response import Response
from pydance.websocket import WebSocket

class MiddlewareType(Enum):
    """Types of middleware based on execution order"""
    PRE_PROCESSING = "pre_processing"
    REQUEST_HANDLING = "request_handling"
    POST_PROCESSING = "post_processing"
    ERROR_HANDLING = "error_handling"

class MiddlewareScope(Enum):
    """Scope of middleware application"""
    GLOBAL = "global"
    ROUTE_SPECIFIC = "route_specific"
    GROUP_SPECIFIC = "group_specific"

@dataclass
class MiddlewareContext:
    """Enhanced context passed through middleware chain"""
    request_id: str
    start_time: float
    request: Request
    response: Optional[Response] = None
    user: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[Exception] = field(default_factory=list)
    middleware_chain: List[str] = field(default_factory=list)

class BaseMiddleware(ABC):
    """Abstract base class for all middleware"""

    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.middleware_type = MiddlewareType.REQUEST_HANDLING
        self.middleware_scope = MiddlewareScope.GLOBAL

    @abstractmethod
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        pass

class HTTPMiddleware(BaseMiddleware):
    """Abstract base class for HTTP middleware"""
    
    @abstractmethod
    async def process_request(self, request: Request) -> Request:
        pass
        
    @abstractmethod
    async def process_response(self, request: Request, response: Response) -> Response:
        pass
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        request = await self.process_request(request)
        response = await call_next(request)
        return await self.process_response(request, response)

class WebSocketMiddleware(BaseMiddleware):
    """Abstract base class for WebSocket middleware"""
    
    @abstractmethod
    async def process_websocket(self, websocket: WebSocket) -> Optional[WebSocket]:
        pass

# Type aliases
MiddlewareCallable = Callable[[Request, Callable], Coroutine[Any, Any, Response]]
MiddlewareType = Union[MiddlewareCallable, type[HTTPMiddleware], type[WebSocketMiddleware]]

# Alias for backward compatibility
Middleware = BaseMiddleware
