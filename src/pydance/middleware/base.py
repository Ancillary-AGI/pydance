"""
Pydance Middleware Base Classes

This module provides the foundation for middleware in the Pydance framework.
Middleware allows you to intercept and modify HTTP requests and responses,
WebSocket connections, and add cross-cutting concerns like authentication,
logging, rate limiting, and security.

Classes:
    - BaseMiddleware: Abstract base class for all middleware
    - HTTPMiddleware: Base class for HTTP request/response middleware
    - WebSocketMiddleware: Base class for WebSocket connection middleware
    - MiddlewareContext: Context object passed through middleware chain
    - MiddlewareType: Enum for middleware execution types
    - MiddlewareScope: Enum for middleware application scope
    - MiddlewarePriority: Enum for middleware execution priority

Example:
    >>> from pydance.middleware.base import HTTPMiddleware
    >>> from pydance.http.request import Request
    >>> from pydance.http.response import Response
    >>>
    >>> class LoggingMiddleware(HTTPMiddleware):
    ...     async def process_request(self, request: Request) -> Request:
    ...         print(f"Request: {request.method} {request.path}")
    ...         return request
    ...
    ...     async def process_response(self, request: Request, response: Response) -> Response:
    ...         print(f"Response: {response.status_code}")
    ...         return response
    >>>
    >>> # Use in application
    >>> app.use(LoggingMiddleware())
"""

import time
from abc import ABC, abstractmethod
from typing import Callable, Any, Optional, Union, Coroutine, Dict, List
from dataclasses import dataclass, field
from enum import Enum
from pydance.utils.logging import get_logger

# Forward declarations to avoid circular imports
try:
    from pydance.http.request import Request
    from pydance.http.response import Response
    from pydance.websocket.websocket import WebSocket
except ImportError:
    # Fallback for type hints during import
    Request = Any
    Response = Any
    WebSocket = Any



class MiddlewareType(Enum):
    """
    Types of middleware based on execution order.

    This enum defines when middleware should execute in the request lifecycle:
    - PRE_PROCESSING: Execute before request handling (e.g., logging, rate limiting)
    - REQUEST_HANDLING: Execute during request processing (e.g., authentication)
    - POST_PROCESSING: Execute after request handling (e.g., response modification)
    - ERROR_HANDLING: Execute only on errors (e.g., error logging, recovery)
    """
    PRE_PROCESSING = "pre_processing"
    REQUEST_HANDLING = "request_handling"
    POST_PROCESSING = "post_processing"
    ERROR_HANDLING = "error_handling"


class MiddlewareScope(Enum):
    """
    Scope of middleware application.

    Defines where middleware should be applied:
    - GLOBAL: Applied to all routes in the application
    - ROUTE_SPECIFIC: Applied only to specific routes
    - GROUP_SPECIFIC: Applied to route groups
    """
    GLOBAL = "global"
    ROUTE_SPECIFIC = "route_specific"
    GROUP_SPECIFIC = "group_specific"


class MiddlewarePriority(Enum):
    """
    Middleware execution priority.

    Determines the order in which middleware executes:
    - HIGHEST: Execute first (e.g., security middleware)
    - HIGH: Execute early (e.g., authentication)
    - NORMAL: Default priority
    - LOW: Execute later (e.g., caching)
    - LOWEST: Execute last (e.g., response compression)
    """
    HIGHEST = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    LOWEST = 5


@dataclass
class MiddlewareContext:
    """
    Enhanced context passed through middleware chain.

    This context object contains information about the current request,
    response, user, timing data, and other metadata that middleware
    can use and modify.

    Attributes:
        request_id: Unique identifier for the request
        start_time: Timestamp when request processing began
        request: The HTTP request object
        response: The HTTP response object (set after request handling)
        user: Authenticated user object (if any)
        metadata: Additional key-value metadata
        errors: List of exceptions that occurred during processing
        middleware_chain: List of middleware names that processed this request
        timing: Execution times for each middleware
        skipped_middlewares: List of middleware that were skipped
    """
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
    """
    Abstract base class for all middleware with enhanced features.

    This class provides the foundation for all middleware in Pydance.
    It includes features like conditional execution, priority management,
    timing measurement, and error handling.

    Attributes:
        name: Unique name for this middleware instance
        middleware_type: Type of middleware (pre-processing, request handling, etc.)
        middleware_scope: Scope of application (global, route-specific, etc.)
        priority: Execution priority (higher numbers execute later)
        enabled: Whether this middleware is enabled
        conditions: List of conditions that must be met for execution
        logger: Logger instance for this middleware

    Example:
        >>> class CustomMiddleware(BaseMiddleware):
        ...     async def __call__(self, request, call_next):
        ...         # Pre-processing
        ...         print(f"Processing {request.path}")
        ...
        ...         # Call next middleware/route handler
        ...         response = await call_next(request)
        ...
        ...         # Post-processing
        ...         response.headers['X-Custom'] = 'processed'
        ...         return response
    """

    def __init__(self, name: str = None):
        """
        Initialize middleware with default settings.

        Args:
            name: Optional custom name for this middleware instance.
                 Defaults to the class name.
        """
        self.name = name or self.__class__.__name__
        self.middleware_type = MiddlewareType.REQUEST_HANDLING
        self.middleware_scope = MiddlewareScope.GLOBAL
        self.priority = MiddlewarePriority.NORMAL
        self.enabled = True
        self.conditions: List[Callable] = []
        self.logger = get_logger(f"middleware.{self.name}")

    def set_priority(self, priority: MiddlewarePriority) -> 'BaseMiddleware':
        """
        Set middleware execution priority.

        Args:
            priority: The priority level for execution order.

        Returns:
            Self for method chaining.
        """
        self.priority = priority
        return self

    def set_enabled(self, enabled: bool) -> 'BaseMiddleware':
        """
        Enable or disable middleware execution.

        Args:
            enabled: Whether this middleware should execute.

        Returns:
            Self for method chaining.
        """
        self.enabled = enabled
        return self

    def add_condition(self, condition: Callable[[Request], bool]) -> 'BaseMiddleware':
        """
        Add conditional execution condition.

        The middleware will only execute if all conditions return True.

        Args:
            condition: Function that takes a Request and returns bool.

        Returns:
            Self for method chaining.

        Example:
            >>> middleware.add_condition(lambda req: req.method == 'POST')
        """
        self.conditions.append(condition)
        return self

    def should_execute(self, request: Request) -> bool:
        """
        Check if middleware should execute based on conditions.

        Args:
            request: The incoming HTTP request.

        Returns:
            True if middleware should execute, False otherwise.
        """
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
        """
        Execute the middleware.

        This is the main entry point for middleware execution. Implement
        this method to define what the middleware does.

        Args:
            request: The incoming HTTP request.
            call_next: Function to call the next middleware or route handler.

        Returns:
            The HTTP response.

        Note:
            This method must be implemented by subclasses.
        """
        pass

    async def execute_with_timing(self, request: Request, call_next: Callable) -> Response:
        """
        Execute middleware with timing measurement.

        This method wraps the middleware execution with performance timing
        and logging. It also handles conditional execution.

        Args:
            request: The incoming HTTP request.
            call_next: Function to call the next middleware or route handler.

        Returns:
            The HTTP response.
        """
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
    """
    Abstract base class for HTTP middleware.

    This class provides a structured approach to HTTP middleware by separating
    request processing from response processing. Subclasses must implement
    both process_request and process_response methods.

    Example:
        >>> class CORSMiddleware(HTTPMiddleware):
        ...     async def process_request(self, request):
        ...         # Add CORS headers to request if needed
        ...         return request
        ...
        ...     async def process_response(self, request, response):
        ...         # Add CORS headers to response
        ...         response.headers['Access-Control-Allow-Origin'] = '*'
        ...         return response
    """

    @abstractmethod
    async def process_request(self, request: Request) -> Request:
        """
        Process the incoming request.

        Args:
            request: The incoming HTTP request.

        Returns:
            The (possibly modified) request object.
        """
        pass

    @abstractmethod
    async def process_response(self, request: Request, response: Response) -> Response:
        """
        Process the outgoing response.

        Args:
            request: The original HTTP request.
            response: The HTTP response to be sent.

        Returns:
            The (possibly modified) response object.
        """
        pass

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Execute the HTTP middleware.

        This method calls process_request, then the next middleware/route handler,
        then process_response in sequence.

        Args:
            request: The incoming HTTP request.
            call_next: Function to call the next middleware or route handler.

        Returns:
            The HTTP response.
        """
        request = await self.process_request(request)
        response = await call_next(request)
        return await self.process_response(request, response)


class WebSocketMiddleware(BaseMiddleware):
    """
    Abstract base class for WebSocket middleware.

    This class provides the foundation for middleware that handles WebSocket
    connections. Subclasses must implement the process_websocket method.

    Example:
        >>> class WebSocketAuthMiddleware(WebSocketMiddleware):
        ...     async def process_websocket(self, websocket):
        ...         # Check authentication for WebSocket connection
        ...         if not websocket.user:
        ...             await websocket.close(1008, "Unauthorized")
        ...             return None
        ...         return websocket
    """

    @abstractmethod
    async def process_websocket(self, websocket: WebSocket) -> Optional[WebSocket]:
        """
        Process the WebSocket connection.

        Args:
            websocket: The WebSocket connection object.

        Returns:
            The WebSocket object if connection should proceed,
            None if connection should be rejected.
        """
        pass
