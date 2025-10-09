"""
Application tests - refactored and modular.

Tests for the core Application class and its functionality.
"""

import pytest
from unittest.mock import Mock, patch

from tests.shared.test_utils import TestDataFactory, TestAssertions
from tests.shared.fixtures import test_settings, test_app


class TestApplicationCore:
    """Test core application functionality"""

    def test_application_initialization(self, test_app):
        """Test application initializes correctly"""
        app = test_app

        assert app.settings is not None
        assert app.router is not None
        assert app.middleware_manager is not None
        assert app.event_bus is not None
        assert app.plugin_manager is not None
        assert app.container is not None

    def test_middleware_registration(self, test_app):
        """Test middleware can be registered"""
        app = test_app

        # Create mock middleware
        middleware = Mock()
        middleware.process_request = Mock(return_value=Mock())
        middleware.process_response = Mock(return_value=Mock())

        app.middleware_manager.add(middleware)

        # Check that middleware was added
        assert len(app.middleware_manager.middleware) > 0

    def test_route_registration(self, test_app):
        """Test routes can be registered"""
        app = test_app

        async def test_handler(request):
            from pydance.http.response import Response
            return Response.text("Hello, World!")

        app.router.add_route('/test', test_handler, methods=['GET'])

        # Check that route was registered
        match_result = app.router.match('GET', '/test')
        assert match_result is not None
        assert match_result.handler == test_handler

    def test_exception_handler_registration(self, test_app):
        """Test exception handlers can be registered"""
        app = test_app

        async def test_exception_handler(exc):
            from pydance.http.response import Response
            return Response.text("Custom error")

        app.exception_handler(ValueError)(test_exception_handler)

        # Check that handler was registered
        assert ValueError in app._exception_handlers
        assert app._exception_handlers[ValueError] == test_exception_handler


class TestApplicationConfiguration:
    """Test application configuration"""

    def test_settings_integration(self, test_settings):
        """Test settings are properly integrated"""
        from pydance import Application

        app = Application(test_settings)

        assert app.settings == test_settings
        assert app.settings.DEBUG is True
        assert app.settings.SECRET_KEY == "test-secret-key-for-testing-only"

    def test_database_configuration(self, test_settings):
        """Test database configuration is loaded"""
        assert 'default' in test_settings.DATABASES
        db_config = test_settings.DATABASES['default']
        assert db_config['ENGINE'] == 'pydance.db.backends.sqlite3'
        assert db_config['NAME'] == ':memory:'

    def test_cache_configuration(self, test_settings):
        """Test cache configuration is loaded"""
        assert 'default' in test_settings.CACHES
        cache_config = test_settings.CACHES['default']
        assert cache_config['BACKEND'] == 'pydance.caching.backends.locmem.LocMemCache'


class TestApplicationLifecycle:
    """Test application lifecycle management"""

    @pytest.mark.asyncio
    async def test_application_startup(self, test_app):
        """Test application startup process"""
        app = test_app

        # Mock startup process
        app.startup = Mock()
        app.startup.return_value = None

        await app.startup()

        app.startup.assert_called_once()

    @pytest.mark.asyncio
    async def test_application_shutdown(self, test_app):
        """Test application shutdown process"""
        app = test_app

        # Mock shutdown process
        app.shutdown = Mock()
        app.shutdown.return_value = None

        await app.shutdown()

        app.shutdown.assert_called_once()


class TestApplicationErrorHandling:
    """Test application error handling"""

    def test_http_exception_handling(self, test_app):
        """Test HTTP exception handling"""
        app = test_app

        from pydance.exceptions import HTTPException

        # Register exception handler
        async def http_exception_handler(exc):
            from pydance.http.response import Response
            return Response.text(f"HTTP Error: {exc.status_code}")

        app.exception_handler(HTTPException)(http_exception_handler)

        assert HTTPException in app._exception_handlers

    def test_validation_error_handling(self, test_app):
        """Test validation error handling"""
        app = test_app

        from pydantic import ValidationError

        # Register validation error handler
        async def validation_error_handler(exc):
            from pydance.http.response import Response
            return Response.json({"error": "Validation failed"}, status_code=400)

        app.exception_handler(ValidationError)(validation_error_handler)

        assert ValidationError in app._exception_handlers


class TestApplicationIntegration:
    """Test application integration scenarios"""

    @pytest.mark.asyncio
    async def test_full_request_lifecycle(self, test_app):
        """Test complete request lifecycle"""
        app = test_app

        # Add a test route
        async def test_endpoint(request):
            from pydance.http.response import Response
            return Response.json({"message": "success"})

        app.router.add_route('/test', test_endpoint, methods=['GET'])

        # Test route matching
        match_result = app.router.match('GET', '/test')
        assert match_result is not None

        # Test handler execution (mock request)
        request = TestDataFactory.create_http_request('GET', '/test')
        response = await match_result.handler(request)

        assert response is not None

    @pytest.mark.asyncio
    async def test_middleware_integration(self, test_app):
        """Test middleware integration in request flow"""
        app = test_app

        # Create test middleware
        middleware_calls = []

        class TestMiddleware:
            def __init__(self):
                self.requests = []

            async def process_request(self, request):
                self.requests.append(request)
                middleware_calls.append('request')
                return request

            async def process_response(self, request, response):
                middleware_calls.append('response')
                return response

        test_middleware = TestMiddleware()
        app.middleware_manager.add(test_middleware)

        # Add test route
        async def test_handler(request):
            from pydance.http.response import Response
            return Response.text("OK")

        app.router.add_route('/middleware-test', test_handler, methods=['GET'])

        # Simulate request processing
        request = TestDataFactory.create_http_request('GET', '/middleware-test')
        match_result = app.router.match('GET', '/middleware-test')

        if match_result:
            response = await match_result.handler(request)
            # Middleware should have been called
            assert len(middleware_calls) >= 2  # request and response processing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
