"""
Comprehensive examples demonstrating the improved Pydance middleware system.

This file shows how to use the enhanced middleware features including:
- Enhanced context management
- Advanced pipeline system
- Multiple middleware patterns
- Error handling and recovery
- Performance monitoring
- Conditional middleware
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional

from pydance.middleware.base import MiddlewareContext, MiddlewareType, MiddlewareScope
from pydance.middleware.builtin import (
    CORSMiddleware, RequestLoggingMiddleware, SecurityHeadersMiddleware,
    PerformanceMonitoringMiddleware, CompressionMiddleware, AuthenticationMiddleware,
    CSRFMiddleware, CachingMiddleware, ValidationMiddleware, ErrorHandlingMiddleware
)
from pydance.middleware.pipeline import (
    MiddlewarePipeline, PipelineConfig, PipelineStage, middleware, use_middleware,
    conditional, create_timing_middleware, create_logging_middleware, create_validation_middleware,
    get_pipeline
)
from pydance.middleware.manager import MiddlewareManager, MiddlewarePriority, get_middleware_manager


# Example 1: Using the enhanced base middleware with context
class CustomAnalyticsMiddleware:
    """Example of creating custom middleware with enhanced context tracking"""

    def __init__(self, analytics_key: str = "default"):
        self.analytics_key = analytics_key
        self.name = "CustomAnalyticsMiddleware"

    async def __call__(self, request, call_next):
        """Enhanced middleware with context tracking"""
        # Get context from request
        context = getattr(request, 'context', None)

        # Track analytics data
        if context:
            context.metadata['analytics'] = {
                'key': self.analytics_key,
                'user_agent': getattr(request, 'headers', {}).get('User-Agent', 'Unknown'),
                'path': getattr(request, 'path', '/'),
                'method': getattr(request, 'method', 'GET'),
                'timestamp': time.time()
            }

            # Store middleware-specific data
            context.set_middleware_data(self.name, 'tracked', True)
            context.set_middleware_data(self.name, 'start_time', time.time())

        # Process request
        if call_next:
            response = await call_next(request)
        else:
            response = request

        # Track response analytics
        if context:
            end_time = time.time()
            start_time = context.get_middleware_data(self.name, 'start_time', end_time)
            execution_time = end_time - start_time

            context.set_middleware_data(self.name, 'execution_time', execution_time)
            context.metadata['analytics']['execution_time'] = execution_time
            context.metadata['analytics']['status_code'] = getattr(response, 'status_code', 200)

        return response


# Example 2: Using the pipeline system
async def example_pipeline_usage():
    """Example of using the advanced pipeline system"""

    # Configure pipeline with custom settings
    config = PipelineConfig(
        enable_context_tracking=True,
        enable_error_recovery=True,
        enable_performance_monitoring=True,
        max_execution_time=30.0
    )

    pipeline = MiddlewarePipeline(config)

    # Add middleware to different stages
    pipeline.pre_processing(create_timing_middleware("pre_processing"))
    pipeline.pre_processing(create_validation_middleware({
        'method': lambda m: m in ['GET', 'POST', 'PUT', 'DELETE'],
        'path': lambda p: isinstance(p, str) and len(p) > 0
    }))

    # Add request handling middleware
    pipeline.use(CustomAnalyticsMiddleware("main_app"), PipelineStage.REQUEST_HANDLING)
    pipeline.use(RequestLoggingMiddleware(), PipelineStage.REQUEST_HANDLING)

    # Add post-processing middleware
    pipeline.post_processing(create_timing_middleware("post_processing"))

    # Add error handling
    @middleware(PipelineStage.ERROR_HANDLING)
    async def error_handler(error, context):
        print(f"Pipeline error in request {context.request_id}: {error}")
        context.metadata['error_handled'] = True

    pipeline.error_handling(error_handler)

    # Example request handler
    async def sample_handler(request):
        return {"message": "Hello from pipeline!", "request_id": request.context.request_id}

    # Create mock request
    class MockRequest:
        def __init__(self):
            self.method = "GET"
            self.path = "/api/test"
            self.headers = {"User-Agent": "Test/1.0"}

    # Execute pipeline
    request = MockRequest()
    try:
        result = await pipeline.execute(request, sample_handler)
        print(f"Pipeline result: {result}")

        # Show pipeline stats
        stats = pipeline.get_stats()
        print(f"Pipeline stats: {stats}")

    except Exception as e:
        print(f"Pipeline error: {e}")


# Example 3: Using the middleware manager
async def example_manager_usage():
    """Example of using the advanced middleware manager"""

    manager = MiddlewareManager()

    # Add middleware with different priorities
    manager.add(
        CORSMiddleware(allow_origins=["*"]),
        priority=MiddlewarePriority.HIGH,
        name="cors_middleware"
    )

    manager.add(
        SecurityHeadersMiddleware(),
        priority=MiddlewarePriority.HIGHEST,
        name="security_middleware"
    )

    manager.add(
        PerformanceMonitoringMiddleware(),
        priority=MiddlewarePriority.NORMAL,
        name="performance_middleware"
    )

    manager.add(
        CustomAnalyticsMiddleware("manager_test"),
        priority=MiddlewarePriority.NORMAL,
        name="analytics_middleware"
    )

    # Add conditional middleware
    @conditional(lambda request: getattr(request, 'requires_auth', False))
    async def conditional_auth_middleware(request, call_next):
        print("Authentication middleware executed!")
        return await call_next(request)

    manager.add(
        conditional_auth_middleware,
        priority=MiddlewarePriority.NORMAL,
        name="conditional_auth"
    )

    # Example handler
    async def api_handler(request):
        return {
            "data": "API response",
            "context": {
                "request_id": request.context.request_id,
                "middleware_data": request.context.middleware_data
            }
        }

    # Create mock request
    class MockRequest:
        def __init__(self):
            self.method = "GET"
            self.path = "/api/data"
            self.headers = {"User-Agent": "Test/1.0"}
            self.requires_auth = True  # This will trigger conditional middleware

    # Execute through manager
    request = MockRequest()

    try:
        # Process request through middleware
        processed_request = await manager.process_http_request(request)

        # Execute handler
        response = await api_handler(processed_request)

        # Process response through middleware
        final_response = await manager.process_http_response(processed_request, response)

        print(f"Manager result: {final_response}")

        # Show manager stats
        stats = manager.get_stats()
        print(f"Manager stats: {stats}")

    except Exception as e:
        print(f"Manager error: {e}")


# Example 4: Advanced middleware composition
class CompositeMiddleware:
    """Example of composing multiple middleware features"""

    def __init__(self, name: str, features: List[str]):
        self.name = name
        self.features = features

    async def __call__(self, request, call_next):
        """Composite middleware that applies multiple features"""
        print(f"Executing composite middleware: {self.name}")

        # Apply features based on configuration
        for feature in self.features:
            await self._apply_feature(feature, request)

        # Continue to next middleware
        if call_next:
            response = await call_next(request)
        else:
            response = request

        # Post-process features
        for feature in reversed(self.features):
            response = await self._post_process_feature(feature, request, response)

        return response

    async def _apply_feature(self, feature: str, request):
        """Apply a specific feature"""
        if feature == "rate_limiting":
            # Simple rate limiting logic
            client_ip = getattr(request, 'client_ip', 'unknown')
            print(f"Rate limiting for {client_ip}")

        elif feature == "caching":
            # Simple caching logic
            cache_key = f"{request.method}:{request.path}"
            print(f"Cache check for {cache_key}")

        elif feature == "validation":
            # Simple validation logic
            if not hasattr(request, 'validated'):
                request.validated = True
                print("Request validated")

    async def _post_process_feature(self, feature: str, request, response):
        """Post-process a specific feature"""
        if feature == "caching":
            # Cache the response
            cache_key = f"{request.method}:{request.path}"
            print(f"Caching response for {cache_key}")

        return response


# Example 5: Error handling and recovery
class RobustErrorHandlingMiddleware:
    """Example of robust error handling with recovery"""

    def __init__(self, fallback_responses: Optional[Dict[str, Any]] = None):
        self.fallback_responses = fallback_responses or {}
        self.name = "RobustErrorHandlingMiddleware"

    async def __call__(self, request, call_next):
        """Error handling with fallback responses"""
        try:
            return await call_next(request)
        except Exception as e:
            print(f"Error caught in {self.name}: {e}")

            # Check if we have a fallback response
            path = getattr(request, 'path', '/')
            if path in self.fallback_responses:
                return self.fallback_responses[path]

            # Generic error response
            return {
                "error": "Service temporarily unavailable",
                "message": "Please try again later",
                "request_id": getattr(request, 'context', {}).request_id if hasattr(request, 'context') else None,
                "timestamp": time.time()
            }


# Example 6: Performance monitoring middleware
class DetailedPerformanceMiddleware:
    """Example of detailed performance monitoring"""

    def __init__(self, enable_detailed_tracking: bool = True):
        self.enable_detailed_tracking = enable_detailed_tracking
        self.name = "DetailedPerformanceMiddleware"

    async def __call__(self, request, call_next):
        """Detailed performance tracking"""
        start_time = time.time()

        # Pre-execution tracking
        context = getattr(request, 'context', None)
        if context:
            context.set_middleware_data(self.name, 'start_time', start_time)
            context.metadata['performance'] = {
                'middleware_start': start_time,
                'memory_before': self._get_memory_usage()
            }

        # Execute next middleware
        if call_next:
            response = await call_next(request)
        else:
            response = request

        # Post-execution tracking
        end_time = time.time()
        execution_time = end_time - start_time

        if context:
            context.set_middleware_data(self.name, 'execution_time', execution_time)
            context.set_middleware_data(self.name, 'end_time', end_time)
            context.metadata['performance'].update({
                'execution_time': execution_time,
                'memory_after': self._get_memory_usage(),
                'memory_delta': self._get_memory_usage() - context.metadata['performance']['memory_before']
            })

        return response

    def _get_memory_usage(self) -> float:
        """Get current memory usage (simplified)"""
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB


# Example 7: Complete application setup
async def setup_complete_middleware_stack():
    """Example of setting up a complete middleware stack"""

    # Configure global pipeline
    pipeline = configure_pipeline(
        enable_context_tracking=True,
        enable_error_recovery=True,
        enable_performance_monitoring=True,
        max_execution_time=30.0
    )

    # Add comprehensive middleware stack
    pipeline.pre_processing(DetailedPerformanceMiddleware())
    pipeline.pre_processing(create_validation_middleware({
        'method': lambda m: m in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
        'path': lambda p: p.startswith('/api/') or p == '/'
    }))

    # Add security middleware
    pipeline.use(CORSMiddleware(allow_origins=["http://localhost:3000", "https://myapp.com"]))
    pipeline.use(SecurityHeadersMiddleware())
    pipeline.use(CSRFMiddleware("your-secret-key"))

    # Add performance middleware
    pipeline.use(PerformanceMonitoringMiddleware())
    pipeline.use(CompressionMiddleware())

    # Add business logic middleware
    pipeline.use(CompositeMiddleware("api_features", ["rate_limiting", "caching", "validation"]))
    pipeline.use(CustomAnalyticsMiddleware("business_logic"))

    # Add error handling
    pipeline.error_handling(RobustErrorHandlingMiddleware({
        "/api/health": {"status": "ok", "message": "Service is healthy"},
        "/api/fallback": {"data": "Fallback response"}
    }))

    # Add cleanup
    @middleware(PipelineStage.CLEANUP)
    async def cleanup_middleware(context):
        print(f"Cleaning up request {context.request_id}")
        # Perform cleanup operations
        if hasattr(context, 'temp_files'):
            for file in context.temp_files:
                print(f"Cleaning up temp file: {file}")

    pipeline.cleanup(cleanup_middleware)

    return pipeline


# Example 8: Route-specific middleware
def create_route_middleware(route_patterns: Dict[str, List[callable]]):
    """Create middleware that applies to specific routes"""

    def route_middleware(request, call_next):
        """Route-specific middleware dispatcher"""
        path = getattr(request, 'path', '/')

        # Find matching route pattern
        for pattern, middlewares in route_patterns.items():
            if pattern == path or path.startswith(pattern):
                # Apply route-specific middleware
                for middleware_func in middlewares:
                    if asyncio.iscoroutinefunction(middleware_func):
                        result = asyncio.run(middleware_func(request, call_next))
                    else:
                        result = middleware_func(request, call_next)
                    if result:
                        return result

        # No route-specific middleware, continue
        if call_next:
            return call_next(request)
        return request

    return route_middleware


# Example usage functions
async def run_all_examples():
    """Run all middleware examples"""

    print("=== Running Pipeline Example ===")
    await example_pipeline_usage()

    print("\n=== Running Manager Example ===")
    await example_manager_usage()

    print("\n=== Setting up Complete Stack ===")
    pipeline = await setup_complete_middleware_stack()
    print("Complete middleware stack configured!")
    print(f"Pipeline stats: {pipeline.get_stats()}")

    print("\n=== All examples completed ===")


# Utility functions for testing
def create_test_request(method: str = "GET", path: str = "/api/test", **kwargs):
    """Create a test request object"""
    class TestRequest:
        def __init__(self):
            self.method = method
            self.path = path
            self.headers = kwargs.get('headers', {"User-Agent": "Test/1.0"})
            self.client_ip = kwargs.get('client_ip', '127.0.0.1')
            for key, value in kwargs.items():
                setattr(self, key, value)

    return TestRequest()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Run examples
    asyncio.run(run_all_examples())
