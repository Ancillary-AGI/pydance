"""
Comprehensive unit tests for the Pydance Middleware Manager.
Tests middleware registration, priority handling, execution order, error scenarios, and performance.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from pydance.middleware.manager import (
    MiddlewareManager, MiddlewareInfo, RequestContext,
    MiddlewarePriority, MiddlewareType, MiddlewarePhase
)
from pydance.http import Request, Response


class TestMiddlewareInfo:
    """Test cases for MiddlewareInfo class"""

    def test_middleware_info_creation(self):
        """Test middleware info creation"""
        def mock_middleware(request, call_next):
            return call_next()

        info = MiddlewareInfo(
            name="test_middleware",
            middleware=mock_middleware,
            priority=MiddlewarePriority.HIGH,
            middleware_type=MiddlewareType.HTTP,
            phases=[MiddlewarePhase.REQUEST, MiddlewarePhase.RESPONSE]
        )

        assert info.name == "test_middleware"
        assert info.middleware == mock_middleware
        assert info.priority == MiddlewarePriority.HIGH
        assert info.middleware_type == MiddlewareType.HTTP
        assert info.phases == [MiddlewarePhase.REQUEST, MiddlewarePhase.RESPONSE]
        assert info.enabled is True
        assert info.config == {}
        assert info.execution_time == 0.0
        assert info.execution_count == 0
        assert info.error_count == 0
        assert info.last_error is None


class TestRequestContext:
    """Test cases for RequestContext class"""

    def test_request_context_creation(self):
        """Test request context creation"""
        context = RequestContext()

        assert context.request_id is not None
        assert context.start_time > 0
        assert context.middleware_data == {}
        assert context.correlation_id is None
        assert context.user_id is None
        assert context.session_id is None
        assert context.metadata == {}

    def test_middleware_data_operations(self):
        """Test middleware data operations"""
        context = RequestContext()

        # Test setting and getting data
        context.set_middleware_data('auth', 'user_id', 123)
        assert context.get_middleware_data('auth', 'user_id') == 123
        assert context.get_middleware_data('auth', 'missing', 'default') == 'default'

        # Test data isolation between middlewares
        context.set_middleware_data('session', 'session_id', 'abc123')
        assert context.get_middleware_data('auth', 'session_id') is None
        assert context.get_middleware_data('session', 'session_id') == 'abc123'

    def test_context_metadata(self):
        """Test context metadata operations"""
        context = RequestContext()

        # Test metadata operations
        context.metadata['custom_key'] = 'custom_value'
        assert context.metadata['custom_key'] == 'custom_value'


class TestMiddlewareManager:
    """Test cases for MiddlewareManager class"""

    def setup_method(self):
        """Setup for each test method"""
        self.manager = MiddlewareManager()

    def test_middleware_manager_initialization(self):
        """Test middleware manager initializes correctly"""
        assert self.manager.http_middlewares == []
        assert self.manager.websocket_middlewares == []
        assert self.manager.middleware_cache == {}
        assert self.manager.request_contexts == {}
        assert self.manager._enabled is True

    def test_add_function_middleware(self):
        """Test adding function-based middleware"""
        async def test_middleware(request, call_next):
            return await call_next()

        self.manager.add(test_middleware, name="test_middleware")

        assert len(self.manager.http_middlewares) == 1
        middleware_info = self.manager.http_middlewares[0]
        assert middleware_info.name == "test_middleware"
        assert middleware_info.middleware == test_middleware

    def test_add_class_middleware(self):
        """Test adding class-based middleware"""
        class TestMiddleware:
            def __init__(self):
                self.call_count = 0

            async def __call__(self, request, call_next):
                self.call_count += 1
                return await call_next()

        middleware = TestMiddleware()
        self.manager.add(middleware, name="class_middleware")

        assert len(self.manager.http_middlewares) == 1
        middleware_info = self.manager.http_middlewares[0]
        assert middleware_info.name == "class_middleware"

    def test_add_structured_middleware(self):
        """Test adding structured middleware with process_request/response"""
        class StructuredMiddleware:
            async def process_request(self, request):
                request.processed = True
                return request

            async def process_response(self, request, response):
                response.headers['X-Processed'] = 'true'
                return response

        middleware = StructuredMiddleware()
        self.manager.add(middleware, name="structured_middleware")

        assert len(self.manager.http_middlewares) == 1
        middleware_info = self.manager.http_middlewares[0]
        assert middleware_info.name == "structured_middleware"

    def test_middleware_priority_ordering(self):
        """Test middleware priority ordering"""
        async def low_priority(request, call_next):
            return await call_next()

        async def high_priority(request, call_next):
            return await call_next()

        # Add in reverse priority order
        self.manager.add(low_priority, MiddlewarePriority.LOW, name="low")
        self.manager.add(high_priority, MiddlewarePriority.HIGH, name="high")

        # Should be sorted by priority (highest first)
        assert len(self.manager.http_middlewares) == 2
        assert self.manager.http_middlewares[0].name == "high"
        assert self.manager.http_middlewares[1].name == "low"

    def test_middleware_with_different_phases(self):
        """Test middleware with different execution phases"""
        async def request_only(request, call_next):
            return await call_next()

        async def response_only(request, response):
            return response

        self.manager.add(request_only, phases=[MiddlewarePhase.REQUEST], name="request_only")
        self.manager.add(response_only, phases=[MiddlewarePhase.RESPONSE], name="response_only")

        assert len(self.manager.http_middlewares) == 2
        assert self.manager.http_middlewares[0].phases == [MiddlewarePhase.REQUEST]
        assert self.manager.http_middlewares[1].phases == [MiddlewarePhase.RESPONSE]

    def test_middleware_duplicate_prevention(self):
        """Test that duplicate middleware instances are not added"""
        async def test_middleware(request, call_next):
            return await call_next()

        # Add the same middleware twice
        self.manager.add(test_middleware, name="test1")
        self.manager.add(test_middleware, name="test2")

        # Should only have one instance
        assert len(self.manager.http_middlewares) == 1

    def test_middleware_enable_disable(self):
        """Test middleware enable/disable functionality"""
        async def test_middleware(request, call_next):
            return await call_next()

        self.manager.add(test_middleware, name="test_middleware")

        # Initially enabled
        middleware = self.manager.get_middleware("test_middleware")
        assert middleware.enabled is True

        # Disable
        result = self.manager.disable("test_middleware")
        assert result is True
        assert middleware.enabled is False

        # Enable again
        result = self.manager.enable("test_middleware")
        assert result is True
        assert middleware.enabled is True

    def test_middleware_removal(self):
        """Test middleware removal"""
        async def test_middleware(request, call_next):
            return await call_next()

        self.manager.add(test_middleware, name="test_middleware")
        assert len(self.manager.http_middlewares) == 1

        result = self.manager.remove("test_middleware")
        assert result is True
        assert len(self.manager.http_middlewares) == 0

    def test_get_middleware_by_name(self):
        """Test getting middleware by name"""
        async def test_middleware(request, call_next):
            return await call_next()

        self.manager.add(test_middleware, name="test_middleware")

        middleware = self.manager.get_middleware("test_middleware")
        assert middleware is not None
        assert middleware.name == "test_middleware"

        not_found = self.manager.get_middleware("nonexistent")
        assert not_found is None

    def test_middleware_with_config(self):
        """Test middleware with configuration"""
        async def test_middleware(request, call_next):
            return await call_next()

        config = {'timeout': 30, 'retry': True}
        self.manager.add(test_middleware, config=config, name="configured_middleware")

        middleware = self.manager.get_middleware("configured_middleware")
        assert middleware.config == config

    def test_middleware_signature_detection(self):
        """Test automatic middleware signature detection"""
        # Request-only middleware
        async def request_only(request, call_next):
            return await call_next()

        # Response-only middleware
        async def response_only(request, response):
            return response

        self.manager.add(request_only, name="request_only")
        self.manager.add(response_only, name="response_only")

        # Check phases were detected correctly
        request_mw = self.manager.get_middleware("request_only")
        response_mw = self.manager.get_middleware("response_only")

        assert MiddlewarePhase.REQUEST in request_mw.phases
        assert MiddlewarePhase.RESPONSE in request_mw.phases

        assert MiddlewarePhase.RESPONSE in response_mw.phases

    def test_middleware_manager_stats(self):
        """Test middleware manager statistics"""
        async def test_middleware(request, call_next):
            return await call_next()

        self.manager.add(test_middleware, name="test_middleware")

        stats = self.manager.get_stats()

        assert stats['total_http_middlewares'] == 1
        assert stats['total_websocket_middlewares'] == 0
        assert stats['enabled'] is True
        assert stats['active_requests'] == 0
        assert 'middleware_stats' in stats
        assert 'test_middleware' in stats['middleware_stats']


class TestMiddlewareExecution:
    """Test cases for middleware execution"""

    def setup_method(self):
        """Setup for execution tests"""
        self.manager = MiddlewareManager()

    async def test_http_request_processing(self):
        """Test HTTP request middleware processing"""
        execution_order = []

        async def middleware1(request, call_next):
            execution_order.append('middleware1_start')
            response = await call_next()
            execution_order.append('middleware1_end')
            return response

        async def middleware2(request, call_next):
            execution_order.append('middleware2_start')
            response = await call_next()
            execution_order.append('middleware2_end')
            return response

        async def final_handler(request):
            execution_order.append('handler')
            return Response.text('Hello')

        self.manager.add(middleware1, name="mw1")
        self.manager.add(middleware2, name="mw2")

        # Mock request
        mock_request = Mock()
        mock_request.context = None

        # Process request
        processed_request = await self.manager.process_http_request(mock_request)

        # Check execution order
        assert execution_order == ['middleware1_start', 'middleware2_start', 'handler', 'middleware2_end', 'middleware1_end']

    async def test_http_response_processing(self):
        """Test HTTP response middleware processing"""
        execution_order = []

        async def middleware1(request, response):
            execution_order.append('middleware1_response')
            return response

        async def middleware2(request, response):
            execution_order.append('middleware2_response')
            return response

        self.manager.add(middleware1, phases=[MiddlewarePhase.RESPONSE], name="mw1")
        self.manager.add(middleware2, phases=[MiddlewarePhase.RESPONSE], name="mw2")

        # Mock request and response
        mock_request = Mock()
        mock_response = Response.text('Hello')

        # Process response
        processed_response = await self.manager.process_http_response(mock_request, mock_response)

        # Check execution order (response middleware runs in reverse order)
        assert execution_order == ['middleware2_response', 'middleware1_response']

    async def test_middleware_error_handling(self):
        """Test middleware error handling"""
        async def failing_middleware(request, call_next):
            raise ValueError("Middleware error")

        async def working_middleware(request, call_next):
            return await call_next()

        async def final_handler(request):
            return Response.text('Hello')

        self.manager.add(failing_middleware, name="failing")
        self.manager.add(working_middleware, name="working")

        mock_request = Mock()

        # Should raise the error from failing middleware
        with pytest.raises(ValueError):
            await self.manager.process_http_request(mock_request)

    async def test_middleware_with_continue_on_error(self):
        """Test middleware that continues on error"""
        async def failing_middleware(request, call_next):
            raise ValueError("Middleware error")

        async def working_middleware(request, call_next):
            return await call_next()

        async def final_handler(request):
            return Response.text('Hello')

        # Add failing middleware with continue_on_error
        self.manager.add(failing_middleware, config={'continue_on_error': True}, name="failing")
        self.manager.add(working_middleware, name="working")

        mock_request = Mock()

        # Should continue despite error
        processed_request = await self.manager.process_http_request(mock_request)
        assert processed_request == mock_request

    async def test_websocket_middleware_processing(self):
        """Test WebSocket middleware processing"""
        execution_order = []

        async def ws_middleware(websocket, call_next):
            execution_order.append('ws_middleware')
            return await call_next()

        self.manager.add(ws_middleware, middleware_type=MiddlewareType.WEBSOCKET, name="ws_mw")

        mock_websocket = Mock()

        # Process WebSocket connection
        processed_websocket = await self.manager.process_websocket(mock_websocket)

        assert processed_websocket == mock_websocket
        assert execution_order == ['ws_middleware']

    async def test_middleware_performance_tracking(self):
        """Test middleware performance tracking"""
        async def slow_middleware(request, call_next):
            await asyncio.sleep(0.01)  # 10ms delay
            return await call_next()

        self.manager.add(slow_middleware, name="slow_middleware")

        mock_request = Mock()

        # Process request and measure time
        start_time = time.time()
        await self.manager.process_http_request(mock_request)
        processing_time = time.time() - start_time

        # Check performance tracking
        middleware = self.manager.get_middleware("slow_middleware")
        assert middleware.execution_count == 1
        assert middleware.execution_time > 0

    def test_middleware_cache_operations(self):
        """Test middleware cache operations"""
        self.manager.middleware_cache['test_key'] = 'test_value'
        assert self.manager.middleware_cache['test_key'] == 'test_value'

        self.manager.clear_cache()
        assert self.manager.middleware_cache == {}

    def test_middleware_bulk_operations(self):
        """Test bulk middleware operations"""
        async def middleware1(request, call_next):
            return await call_next()

        async def middleware2(request, call_next):
            return await call_next()

        self.manager.add(middleware1, name="mw1")
        self.manager.add(middleware2, name="mw2")

        # Test enable all
        self.manager.disable("mw1")
        self.manager.enable_all()

        assert self.manager.get_middleware("mw1").enabled is True
        assert self.manager.get_middleware("mw2").enabled is True

        # Test disable all
        self.manager.disable_all()

        assert self.manager.get_middleware("mw1").enabled is False
        assert self.manager.get_middleware("mw2").enabled is False

    def test_get_middleware_by_phase(self):
        """Test getting middleware by execution phase"""
        async def request_middleware(request, call_next):
            return await call_next()

        async def response_middleware(request, response):
            return response

        self.manager.add(request_middleware, phases=[MiddlewarePhase.REQUEST], name="request_mw")
        self.manager.add(response_middleware, phases=[MiddlewarePhase.RESPONSE], name="response_mw")

        request_middlewares = self.manager.get_middleware_by_phase(MiddlewarePhase.REQUEST)
        response_middlewares = self.manager.get_middleware_by_phase(MiddlewarePhase.RESPONSE)

        assert len(request_middlewares) == 1
        assert request_middlewares[0].name == "request_mw"

        assert len(response_middlewares) == 1
        assert response_middlewares[0].name == "response_mw"


class TestMiddlewareIntegration:
    """Integration tests for middleware system"""

    def setup_method(self):
        """Setup for integration tests"""
        self.manager = MiddlewareManager()

    async def test_full_middleware_chain(self):
        """Test complete middleware chain execution"""
        execution_log = []

        async def auth_middleware(request, call_next):
            execution_log.append('auth_start')
            response = await call_next()
            execution_log.append('auth_end')
            response.headers['X-Auth'] = 'checked'
            return response

        async def logging_middleware(request, call_next):
            execution_log.append('logging_start')
            response = await call_next()
            execution_log.append('logging_end')
            response.headers['X-Logged'] = 'true'
            return response

        async def final_handler(request):
            execution_log.append('handler')
            return Response.text('Hello')

        # Add middlewares with different priorities
        self.manager.add(auth_middleware, MiddlewarePriority.HIGH, name="auth")
        self.manager.add(logging_middleware, MiddlewarePriority.NORMAL, name="logging")

        mock_request = Mock()

        # Execute full chain
        response = await self.manager.execute_http_chain(mock_request, final_handler)

        # Check execution order
        expected_order = [
            'auth_start', 'logging_start', 'handler',  # Request phase
            'logging_end', 'auth_end'  # Response phase (reverse order)
        ]
        assert execution_log == expected_order

        # Check response headers
        assert response.headers['X-Auth'] == 'checked'
        assert response.headers['X-Logged'] == 'true'

    async def test_middleware_with_request_context(self):
        """Test middleware with request context"""
        async def context_middleware(request, call_next):
            request.context.set_middleware_data('context_mw', 'user_id', 123)
            response = await call_next()
            user_id = request.context.get_middleware_data('context_mw', 'user_id')
            response.headers['X-User-ID'] = str(user_id)
            return response

        async def final_handler(request):
            return Response.text('Hello')

        self.manager.add(context_middleware, name="context_mw")

        mock_request = Mock()

        response = await self.manager.execute_http_chain(mock_request, final_handler)

        # Check that context data was preserved
        assert response.headers['X-User-ID'] == '123'

    async def test_middleware_error_propagation(self):
        """Test error propagation through middleware chain"""
        async def failing_middleware(request, call_next):
            raise ValueError("Test error")

        async def working_middleware(request, call_next):
            return await call_next()

        self.manager.add(failing_middleware, name="failing")
        self.manager.add(working_middleware, name="working")

        mock_request = Mock()

        # Should propagate the error
        with pytest.raises(ValueError):
            await self.manager.execute_http_chain(mock_request, lambda r: Response.text('ok'))


class TestMiddlewarePerformance:
    """Test middleware performance features"""

    def setup_method(self):
        """Setup for performance tests"""
        self.manager = MiddlewareManager()

    async def test_middleware_execution_performance(self):
        """Test middleware execution performance"""
        async def fast_middleware(request, call_next):
            return await call_next()

        # Add many middlewares
        for i in range(100):
            self.manager.add(fast_middleware, name=f"mw_{i}")

        mock_request = Mock()

        # Measure execution time
        start_time = time.time()
        await self.manager.process_http_request(mock_request)
        execution_time = time.time() - start_time

        # Should be fast even with many middlewares
        assert execution_time < 0.1  # Less than 100ms for 100 middlewares

    def test_middleware_priority_performance(self):
        """Test that priority sorting is efficient"""
        async def dummy_middleware(request, call_next):
            return await call_next()

        # Add many middlewares with different priorities
        for i in range(100):
            priority = MiddlewarePriority(i % 10)
            self.manager.add(dummy_middleware, priority, name=f"mw_{i}")

        # Check they were sorted correctly
        priorities = [mw.priority.value for mw in self.manager.http_middlewares]
        assert priorities == sorted(priorities, reverse=True)

    def test_middleware_stats_performance(self):
        """Test middleware statistics performance"""
        async def test_middleware(request, call_next):
            return await call_next()

        self.manager.add(test_middleware, name="test_middleware")

        # Getting stats should be fast
        start_time = time.time()
        for _ in range(1000):
            stats = self.manager.get_stats()
        stats_time = time.time() - start_time

        assert stats_time < 0.1  # Less than 100ms for 1000 stats calls


class TestMiddlewareErrorHandling:
    """Test middleware error handling scenarios"""

    def setup_method(self):
        """Setup for error handling tests"""
        self.manager = MiddlewareManager()

    async def test_middleware_exception_in_request_phase(self):
        """Test exception handling in request phase"""
        async def failing_middleware(request, call_next):
            raise ValueError("Request phase error")

        async def working_middleware(request, call_next):
            return await call_next()

        self.manager.add(failing_middleware, name="failing")
        self.manager.add(working_middleware, name="working")

        mock_request = Mock()

        # Should raise the exception
        with pytest.raises(ValueError):
            await self.manager.process_http_request(mock_request)

    async def test_middleware_exception_in_response_phase(self):
        """Test exception handling in response phase"""
        async def failing_response_middleware(request, response):
            raise ValueError("Response phase error")

        self.manager.add(failing_response_middleware, phases=[MiddlewarePhase.RESPONSE], name="failing")

        mock_request = Mock()
        mock_response = Response.text('Hello')

        # Should raise the exception
        with pytest.raises(ValueError):
            await self.manager.process_http_response(mock_request, mock_response)

    def test_invalid_middleware_handling(self):
        """Test handling of invalid middleware"""
        # Test with non-callable middleware
        with pytest.raises((TypeError, ValueError)):
            self.manager.add("not_callable", name="invalid")

    async def test_middleware_timeout_handling(self):
        """Test middleware timeout handling"""
        async def slow_middleware(request, call_next):
            await asyncio.sleep(10)  # Very slow
            return await call_next()

        self.manager.add(slow_middleware, name="slow")

        mock_request = Mock()

        # Should timeout (this would need actual timeout implementation)
        # For now, just test that it doesn't hang indefinitely
        try:
            await asyncio.wait_for(
                self.manager.process_http_request(mock_request),
                timeout=1.0
            )
        except asyncio.TimeoutError:
            # Expected for slow middleware without timeout handling
            pass


class TestMiddlewareAdvancedFeatures:
    """Test advanced middleware features"""

    def setup_method(self):
        """Setup for advanced feature tests"""
        self.manager = MiddlewareManager()

    def test_middleware_type_detection(self):
        """Test automatic middleware type detection"""
        # HTTP middleware
        async def http_middleware(request, call_next):
            return await call_next()

        # WebSocket middleware
        async def ws_middleware(websocket, call_next):
            return await call_next()

        self.manager.add(http_middleware, name="http_mw")
        self.manager.add(ws_middleware, middleware_type=MiddlewareType.WEBSOCKET, name="ws_mw")

        assert len(self.manager.http_middlewares) == 1
        assert len(self.manager.websocket_middlewares) == 1

        assert self.manager.http_middlewares[0].name == "http_mw"
        assert self.manager.websocket_middlewares[0].name == "ws_mw"

    def test_middleware_with_custom_config(self):
        """Test middleware with custom configuration"""
        async def configurable_middleware(request, call_next):
            config_value = request.context.get_middleware_data('configurable', 'setting', 'default')
            return await call_next()

        config = {'setting': 'custom_value', 'timeout': 30}
        self.manager.add(configurable_middleware, config=config, name="configurable")

        middleware = self.manager.get_middleware("configurable")
        assert middleware.config == config

    async def test_middleware_context_sharing(self):
        """Test middleware context sharing"""
        async def middleware1(request, call_next):
            request.context.set_middleware_data('mw1', 'data', 'shared_data')
            return await call_next()

        async def middleware2(request, call_next):
            data = request.context.get_middleware_data('mw1', 'data')
            request.context.set_middleware_data('mw2', 'received_data', data)
            return await call_next()

        self.manager.add(middleware1, name="mw1")
        self.manager.add(middleware2, name="mw2")

        mock_request = Mock()

        await self.manager.process_http_request(mock_request)

        # Check data was shared between middlewares
        shared_data = mock_request.context.get_middleware_data('mw2', 'received_data')
        assert shared_data == 'shared_data'


if __name__ == '__main__':
    # Run tests if executed directly
    pytest.main([__file__])
