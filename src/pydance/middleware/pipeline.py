"""
Enhanced middleware pipeline system for Pydance Framework.

This module provides a flexible middleware pipeline with advanced features
inspired by Express.js, FastAPI, and Django patterns but adapted for Pydance.
"""

import time
import asyncio
import inspect
from typing import List, Dict, Any, Optional, Callable, Union, Awaitable
from functools import wraps
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum

from pydance.middleware.base import MiddlewareContext, MiddlewareType, MiddlewareScope


class PipelineStage(Enum):
    """Pipeline execution stages"""
    PRE_PROCESSING = "pre_processing"
    REQUEST_HANDLING = "request_handling"
    POST_PROCESSING = "post_processing"
    ERROR_HANDLING = "error_handling"
    CLEANUP = "cleanup"


@dataclass
class PipelineConfig:
    """Configuration for middleware pipeline"""
    enable_context_tracking: bool = True
    enable_error_recovery: bool = True
    enable_performance_monitoring: bool = True
    max_execution_time: float = 30.0
    context_timeout: float = 60.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class MiddlewarePipeline:
    """Advanced middleware pipeline with comprehensive features"""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.stages: Dict[PipelineStage, List[Callable]] = {
            stage: [] for stage in PipelineStage
        }
        self.context_var: ContextVar = ContextVar('pipeline_context')
        self._active_contexts: Dict[str, MiddlewareContext] = {}

    def use(self, middleware: Callable, stage: PipelineStage = PipelineStage.REQUEST_HANDLING) -> 'MiddlewarePipeline':
        """Add middleware to specific pipeline stage (Express.js style)"""
        self.stages[stage].append(middleware)
        return self

    def pre_processing(self, middleware: Callable) -> 'MiddlewarePipeline':
        """Add pre-processing middleware"""
        return self.use(middleware, PipelineStage.PRE_PROCESSING)

    def post_processing(self, middleware: Callable) -> 'MiddlewarePipeline':
        """Add post-processing middleware"""
        return self.use(middleware, PipelineStage.POST_PROCESSING)

    def error_handling(self, middleware: Callable) -> 'MiddlewarePipeline':
        """Add error handling middleware"""
        return self.use(middleware, PipelineStage.ERROR_HANDLING)

    def cleanup(self, middleware: Callable) -> 'MiddlewarePipeline':
        """Add cleanup middleware"""
        return self.use(middleware, PipelineStage.CLEANUP)

    def add_middleware_class(self, middleware_class: type, stage: PipelineStage = PipelineStage.REQUEST_HANDLING, **kwargs) -> 'MiddlewarePipeline':
        """Add middleware class instance"""
        middleware_instance = middleware_class(**kwargs)
        return self.use(middleware_instance, stage)

    async def execute(self, request: Any, handler: Callable) -> Any:
        """Execute the complete pipeline"""
        context = MiddlewareContext(
            request_id=self._generate_request_id(),
            start_time=time.time(),
            request=request
        )

        # Set context in contextvar
        token = self.context_var.set(context)
        self._active_contexts[context.request_id] = context

        try:
            # Execute pipeline stages
            result = await self._execute_stages(request, handler, context)
            return result

        except Exception as e:
            # Handle errors through error handling stage
            if self.stages[PipelineStage.ERROR_HANDLING]:
                try:
                    await self._execute_error_handlers(e, context)
                except Exception as error_handler_exception:
                    # If error handler fails, log and use original error
                    print(f"Error handler failed: {error_handler_exception}")

            # Re-raise original error if error recovery is disabled
            if not self.config.enable_error_recovery:
                raise

            # Return error response for error recovery
            return self._create_error_response(e, context)

        finally:
            # Cleanup
            await self._execute_cleanup(context)
            self.context_var.reset(token)

            # Remove from active contexts after timeout
            if context.request_id in self._active_contexts:
                del self._active_contexts[context.request_id]

    async def _execute_stages(self, request: Any, handler: Callable, context: MiddlewareContext) -> Any:
        """Execute all pipeline stages"""

        # Pre-processing stage
        processed_request = await self._execute_stage(
            PipelineStage.PRE_PROCESSING, request, context
        )

        # Main request handling
        try:
            # Execute main handler with request/response middleware
            result = await self._execute_request_handling(processed_request, handler, context)

            # Post-processing stage
            result = await self._execute_stage(
                PipelineStage.POST_PROCESSING, result, context
            )

            return result

        except Exception as e:
            context.errors.append(e)
            raise

    async def _execute_request_handling(self, request: Any, handler: Callable, context: MiddlewareContext) -> Any:
        """Execute request handling stage with middleware chain"""

        # Create the middleware chain
        middleware_chain = self._build_middleware_chain(handler)

        # Execute the chain
        result = await middleware_chain(request)

        return result

    def _build_middleware_chain(self, handler: Callable) -> Callable:
        """Build the middleware chain with proper call_next handling"""

        # Get request handling middleware
        request_middlewares = self.stages[PipelineStage.REQUEST_HANDLING]

        if not request_middlewares:
            return handler

        # Build chain in reverse order (last middleware first)
        current_handler = handler

        for middleware in reversed(request_middlewares):
            current_handler = self._wrap_middleware(middleware, current_handler)

        return current_handler

    def _wrap_middleware(self, middleware: Callable, next_handler: Callable) -> Callable:
        """Wrap middleware with next_handler"""
        if inspect.iscoroutinefunction(middleware):
            async def wrapped(request):
                return await middleware(request, next_handler)
        else:
            def wrapped(request):
                return middleware(request, next_handler)

        return wrapped

    async def _execute_stage(self, stage: PipelineStage, payload: Any, context: MiddlewareContext) -> Any:
        """Execute a specific pipeline stage"""
        for middleware in self.stages[stage]:
            try:
                if inspect.iscoroutinefunction(middleware):
                    payload = await middleware(payload, context)
                else:
                    payload = middleware(payload, context)
            except Exception as e:
                context.errors.append(e)
                if not self.config.enable_error_recovery:
                    raise
                print(f"Error in {stage.value} middleware: {e}")

        return payload

    async def _execute_error_handlers(self, error: Exception, context: MiddlewareContext):
        """Execute error handling middleware"""
        for middleware in self.stages[PipelineStage.ERROR_HANDLING]:
            try:
                if inspect.iscoroutinefunction(middleware):
                    await middleware(error, context)
                else:
                    middleware(error, context)
            except Exception as e:
                print(f"Error in error handler: {e}")

    async def _execute_cleanup(self, context: MiddlewareContext):
        """Execute cleanup middleware"""
        for middleware in self.stages[PipelineStage.CLEANUP]:
            try:
                if inspect.iscoroutinefunction(middleware):
                    await middleware(context)
                else:
                    middleware(context)
            except Exception as e:
                print(f"Error in cleanup middleware: {e}")

    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        return f"req_{int(time.time() * 1000)}_{hash(str(time.time()))}"

    def _create_error_response(self, error: Exception, context: MiddlewareContext) -> Dict[str, Any]:
        """Create error response"""
        return {
            "error": "Internal Server Error",
            "message": str(error) if self.config.enable_error_recovery else "An error occurred",
            "request_id": context.request_id,
            "timestamp": time.time()
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        return {
            "active_contexts": len(self._active_contexts),
            "stages": {
                stage.value: len(middlewares)
                for stage, middlewares in self.stages.items()
            },
            "config": {
                "enable_context_tracking": self.config.enable_context_tracking,
                "enable_error_recovery": self.config.enable_error_recovery,
                "enable_performance_monitoring": self.config.enable_performance_monitoring,
                "max_execution_time": self.config.max_execution_time
            }
        }


# Decorator utilities
def middleware(stage: PipelineStage = PipelineStage.REQUEST_HANDLING):
    """Decorator for creating middleware functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Handle different middleware signatures
            if len(args) == 2:  # (request, call_next) pattern
                request, call_next = args
                return await func(request, call_next)
            elif len(args) == 1:  # (request,) pattern
                request = args[0]
                return await func(request)
            else:
                return await func(*args, **kwargs)

        # Mark as middleware
        wrapper._middleware_stage = stage
        wrapper._is_middleware = True
        return wrapper
    return decorator


def use_middleware(middleware_func: Callable, stage: PipelineStage = PipelineStage.REQUEST_HANDLING):
    """Decorator to apply middleware to specific functions"""
    def decorator(handler: Callable) -> Callable:
        # Store middleware info on handler
        if not hasattr(handler, '_applied_middlewares'):
            handler._applied_middlewares = []

        handler._applied_middlewares.append({
            'middleware': middleware_func,
            'stage': stage
        })

        return handler
    return decorator


class ConditionalMiddleware:
    """Middleware that executes based on conditions"""

    def __init__(self, middleware: Callable, condition: Callable[[Any], bool]):
        self.middleware = middleware
        self.condition = condition

    async def __call__(self, request, call_next=None):
        if self.condition(request):
            if call_next is not None:
                return await self.middleware(request, call_next)
            else:
                return await self.middleware(request)
        else:
            if call_next is not None:
                return await call_next(request)
            else:
                return request


def conditional(condition: Callable[[Any], bool]):
    """Decorator to make middleware conditional"""
    def decorator(middleware: Callable) -> ConditionalMiddleware:
        return ConditionalMiddleware(middleware, condition)
    return decorator


# Utility functions for common middleware patterns
def create_timing_middleware(name: str = "timing"):
    """Create middleware that tracks execution time"""
    @middleware(PipelineStage.PRE_PROCESSING)
    async def timing_middleware(request, call_next):
        start_time = time.time()
        request._start_time = start_time

        if call_next:
            response = await call_next(request)
        else:
            response = request

        execution_time = time.time() - start_time
        print(f"{name}: {execution_time:.3f}s")

        return response

    return timing_middleware


def create_logging_middleware(logger_name: str = "pipeline"):
    """Create middleware that logs requests"""
    import logging

    logger = logging.getLogger(logger_name)

    @middleware(PipelineStage.REQUEST_HANDLING)
    async def logging_middleware(request, call_next):
        logger.info(f"Processing request: {getattr(request, 'method', 'UNKNOWN')} {getattr(request, 'path', '/')}")

        if call_next:
            response = await call_next(request)
            logger.info(f"Request completed with status: {getattr(response, 'status_code', 200)}")
            return response
        else:
            return request

    return logging_middleware


def create_validation_middleware(validators: Dict[str, Callable]):
    """Create middleware that validates requests"""
    @middleware(PipelineStage.PRE_PROCESSING)
    async def validation_middleware(request, call_next):
        for field, validator in validators.items():
            value = getattr(request, field, None)
            if value is not None:
                if inspect.iscoroutinefunction(validator):
                    is_valid = await validator(value)
                else:
                    is_valid = validator(value)

                if not is_valid:
                    raise ValueError(f"Validation failed for field: {field}")

        if call_next:
            return await call_next(request)
        else:
            return request

    return validation_middleware


# Global pipeline instance
_global_pipeline: Optional[MiddlewarePipeline] = None

def get_pipeline() -> MiddlewarePipeline:
    """Get the global pipeline instance"""
    global _global_pipeline
    if _global_pipeline is None:
        _global_pipeline = MiddlewarePipeline()
    return _global_pipeline


def configure_pipeline(**kwargs) -> MiddlewarePipeline:
    """Configure and return the global pipeline"""
    global _global_pipeline
    _global_pipeline = MiddlewarePipeline(PipelineConfig(**kwargs))
    return _global_pipeline


__all__ = [
    'MiddlewarePipeline', 'PipelineConfig', 'PipelineStage',
    'middleware', 'use_middleware', 'conditional',
    'create_timing_middleware', 'create_logging_middleware', 'create_validation_middleware',
    'get_pipeline', 'configure_pipeline'
]
