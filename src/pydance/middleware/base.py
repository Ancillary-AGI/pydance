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

class MiddlewarePriority(Enum):
    """Middleware execution priority"""
    HIGHEST = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    LOWEST = 5

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
    timing: Dict[str, float] = field(default_factory=dict)
    skipped_middlewares: List[str] = field(default_factory=list)

class BaseMiddleware(ABC):
    """Abstract base class for all middleware with enhanced features"""

    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.middleware_type = MiddlewareType.REQUEST_HANDLING
        self.middleware_scope = MiddlewareScope.GLOBAL
        self.priority = MiddlewarePriority.NORMAL
        self.enabled = True
        self.conditions: List[Callable] = []
        self.logger = logging.getLogger(f"middleware.{self.name}")

    def set_priority(self, priority: MiddlewarePriority):
        """Set middleware execution priority"""
        self.priority = priority
        return self

    def set_enabled(self, enabled: bool):
        """Enable or disable middleware"""
        self.enabled = enabled
        return self

    def add_condition(self, condition: Callable[[Request], bool]):
        """Add conditional execution condition"""
        self.conditions.append(condition)
        return self

    def should_execute(self, request: Request) -> bool:
        """Check if middleware should execute based on conditions"""
        if not self.enabled:
            return False

        for condition in self.conditions:
            try:
                if not condition(request):
                    return False
            except Exception as e:
                self.logger.warning(f"Condition check failed for {self.name}: {e}")
                return False

        return True

    @abstractmethod
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        pass

    async def execute_with_timing(self, request: Request, call_next: Callable) -> Response:
        """Execute middleware with timing measurement"""
        if not self.should_execute(request):
            self.logger.debug(f"Skipping middleware {self.name}")
            return await call_next(request)

        start_time = time.time()
        try:
            response = await self.__call__(request, call_next)
            execution_time = time.time() - start_time

            self.logger.debug(f"Middleware {self.name} executed in {execution_time:.4f}s")
            return response

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Middleware {self.name} failed after {execution_time:.4f}s: {e}")
            raise

class HTTPMiddleware(BaseMiddleware):
    """Abstract base class for HTTP middleware"""
    
    @abstractmethod
    async def process_request(self, request: Request) -> Request:
        """Process the incoming request"""
        pass

    @abstractmethod
    async def process_response(self, request: Request, response: Response) -> Response:
        """Process the outgoing response"""
        pass
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        request = await self.process_request(request)
        response = await call_next(request)
        return await self.process_response(request, response)

class WebSocketMiddleware(BaseMiddleware):
    """Abstract base class for WebSocket middleware"""
    
    @abstractmethod
    async def process_websocket(self, websocket: WebSocket) -> Optional[WebSocket]:
        """Process the WebSocket connection"""
        pass
