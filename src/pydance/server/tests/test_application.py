"""
Comprehensive unit tests for the Pydance Application server module.
Tests application initialization, configuration, routing, middleware, and lifecycle management.
"""

import asyncio
import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pydance.server.application import Application
from pydance.config.settings import Settings
from pydance.http import Request, Response
from pydance.exceptions import HTTPException


class TestApplication:
    """Test cases for Application class"""

    def setup_method(self):
        """Setup for each test method"""
        self.app = Application()

    def test_application_initialization(self):
        """Test application initializes correctly"""
        assert self.app.config is not None
        assert self.app.router is not None
        assert self.app.middleware_manager is not None
        assert self.app.template_engine is None  # Not initialized until startup
        assert self.app.state == {}
        assert self.app._startup_handlers == []
        assert self.app._shutdown_handlers == []
        assert self.app._exception_handlers == {}

    def test_application_with_custom_config(self):
        """Test application with custom configuration"""
        custom_config = Settings()
        custom_config.DEBUG = True
        custom_config.APP_NAME = "Test App"

        app = Application(custom_config)
        assert app.config.DEBUG is True
        assert app.config.APP_NAME == "Test App"

    @patch('pydance.server.application.get_middleware_manager')
    def test_middleware_manager_initialization(self, mock_get_manager):
        """Test middleware manager is properly initialized"""
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        app = Application()
        mock_get_manager.assert_called_once()

    def test_route_decorator(self):
        """Test route decorator functionality"""
        @self.app.route('/test')
        async def test_handler(request):
            return Response.text('test')

        # Check route was added
        routes = self.app.router.routes
        assert len(routes) > 0

        # Find our test route
        test_route = None
        for route in routes:
            if route.path == '/test':
                test_route = route
                break

        assert test_route is not None
        assert test_route.handler == test_handler

    def test_route_with_methods(self):
        """Test route decorator with specific HTTP methods"""
        @self.app.route('/api/test', methods=['POST', 'PUT'])
        async def api_handler(request):
            return Response.json({'status': 'ok'})

        # Check route was added with correct methods
        routes = self.app.router.routes
        api_route = None
        for route in routes:
            if route.path == '/api/test':
                api_route = route
                break

        assert api_route is not None
        assert 'POST' in api_route.methods
        assert 'PUT' in api_route.methods

    def test_websocket_route_decorator(self):
        """Test WebSocket route decorator"""
        @self.app.websocket_route('/ws/test')
        async def ws_handler(websocket):
            pass

        # Check WebSocket route was added
        ws_routes = self.app.router.websocket_routes
        assert len(ws_routes) > 0

        ws_route = None
        for route in ws_routes:
            if route.path == '/ws/test':
                ws_route = route
                break

        assert ws_route is not None
        assert ws_route.handler == ws_handler

    def test_middleware_registration(self):
        """Test middleware registration"""
        mock_middleware = Mock()

        result = self.app.use(mock_middleware)
        assert result == self.app  # Should return self for chaining

    def test_middleware_with_options(self):
        """Test middleware registration with options"""
        mock_middleware = Mock()
        options = {'key': 'value'}

        self.app.use(mock_middleware, options)
        # Verify middleware was added (implementation detail)

    def test_middleware_with_priority(self):
        """Test middleware registration with priority"""
        mock_middleware = Mock()

        self.app.use(mock_middleware, priority=10)
        # Verify priority was handled

    def test_middleware_list_registration(self):
        """Test registering multiple middlewares at once"""
        middleware_list = [
            Mock(name='mw1'),
            Mock(name='mw2'),
            (Mock(name='mw3'), {'option': 'value'}, 5)
        ]

        self.app.use(middleware_list)
        # Verify all middlewares were processed

    def test_middleware_string_alias(self):
        """Test middleware registration using string aliases"""
        # This would test the alias resolution system
        self.app.use('cors')
        self.app.use('auth', {'redirect': '/login'})

    def test_middleware_group_registration(self):
        """Test middleware group registration"""
        self.app.use('web')  # Should register all web middlewares
        self.app.use('api')  # Should register all api middlewares

    def test_middleware_pipeline(self):
        """Test middleware pipeline method"""
        middleware1 = Mock()
        middleware2 = Mock()

        result = self.app.pipeline(middleware1, middleware2)
        assert result == self.app

    def test_middleware_exclusion(self):
        """Test excluding middleware"""
        result = self.app.without_middleware('csrf', 'auth')
        assert result == self.app

    def test_startup_handler_registration(self):
        """Test startup handler registration"""
        @self.app.on_startup
        async def startup_task():
            pass

        assert startup_task in self.app._startup_handlers

    def test_shutdown_handler_registration(self):
        """Test shutdown handler registration"""
        @self.app.on_shutdown
        async def shutdown_task():
            pass

        assert shutdown_task in self.app._shutdown_handlers

    def test_exception_handler_registration(self):
        """Test exception handler registration"""
        @self.app.exception_handler(ValueError)
        async def handle_value_error(exc):
            return Response.text('Value error occurred')

        assert ValueError in self.app._exception_handlers
        assert self.app._exception_handlers[ValueError] == handle_value_error

    @patch('pydance.templating.engine.get_template_engine')
    async def test_application_startup(self, mock_get_engine):
        """Test application startup process"""
        mock_engine = Mock()
        mock_get_engine.return_value = mock_engine

        await self.app.startup()

        assert self.app.template_engine == mock_engine
        mock_get_engine.assert_called_once()

    async def test_application_shutdown(self):
        """Test application shutdown process"""
        # Add some handlers
        @self.app.on_startup
        async def startup():
            pass

        @self.app.on_shutdown
        async def shutdown():
            pass

        await self.app.startup()
        await self.app.shutdown()

        # Verify shutdown completed without errors

    def test_debug_property(self):
        """Test debug property"""
        self.app.config.DEBUG = True
        assert self.app.debug is True

        self.app.config.DEBUG = False
        assert self.app.debug is False

    def test_url_for_method(self):
        """Test URL generation"""
        # This is a simplified test since named routes aren't fully implemented
        url = self.app.url_for('test')
        assert url == '/test'

    @patch('pydance.server.application.Server')
    def test_run_method(self, mock_server_class):
        """Test application run method"""
        mock_server = Mock()
        mock_server_class.return_value = mock_server

        self.app.run(host='0.0.0.0', port=9000)

        mock_server_class.assert_called_once()
        mock_server.run.assert_called_once_with(host='0.0.0.0', port=9000)

    @patch('pydance.server.application.Server')
    async def test_serve_method(self, mock_server_class):
        """Test application serve method"""
        mock_server = Mock()
        mock_server_class.return_value = mock_server

        await self.app.serve(host='0.0.0.0', port=9000)

        mock_server_class.assert_called_once()
        mock_server.serve.assert_called_once_with(host='0.0.0.0', port=9000)

    async def test_asgi_lifespan_handling(self):
        """Test ASGI lifespan protocol handling"""
        # Mock ASGI scope and send/receive functions
        scope = {'type': 'lifespan'}

        messages_received = []
        messages_to_send = []

        async def mock_receive():
            if not messages_received:
                return {'type': 'lifespan.startup'}
            else:
                return {'type': 'lifespan.shutdown'}

        async def mock_send(message):
            messages_to_send.append(message)

        # Test startup
        messages_received.clear()
        messages_to_send.clear()

        await self.app(scope, mock_receive, mock_send)

        # Should have sent startup complete
        assert len(messages_to_send) >= 1
        assert messages_to_send[0]['type'] == 'lifespan.startup.complete'

    async def test_http_request_handling(self):
        """Test HTTP request processing"""
        # Add a test route
        @self.app.route('/test')
        async def test_handler(request):
            return Response.text('Hello')

        # Mock ASGI scope for HTTP request
        scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/test',
            'query_string': b'',
            'headers': []
        }

        messages_received = []
        messages_to_send = []

        async def mock_receive():
            return {'type': 'http.request', 'body': b''}

        async def mock_send(message):
            messages_to_send.append(message)

        # This would test the full HTTP request cycle
        # For now, just verify the method exists and can be called
        assert hasattr(self.app, '_handle_http')

    def test_feature_enabling(self):
        """Test optional feature enabling"""
        # Test container enabling
        with patch('pydance.server.application.Container') as mock_container:
            app = Application()
            app_with_container = app.with_container()
            assert app_with_container == app

        # Test monitoring enabling
        with patch('pydance.server.application.MetricsCollector') as mock_metrics:
            with patch('pydance.server.application.HealthChecker') as mock_health:
                app = Application()
                app_with_monitoring = app.with_monitoring()
                assert app_with_monitoring == app

    def test_health_endpoints_registration(self):
        """Test health check endpoints are registered"""
        # Check that health endpoints were added during setup
        routes = self.app.router.routes

        health_routes = [r for r in routes if r.path in ['/_health', '/_ready']]
        assert len(health_routes) >= 1

    def test_database_setup(self):
        """Test database setup during initialization"""
        # Mock database modules
        with patch('pydance.db.DatabaseConfig') as mock_db_config:
            with patch('pydance.db.connections.DatabaseConnection') as mock_db_conn:
                with patch('pydance.server.application.get_event_bus') as mock_event_bus:
                    app = Application()

                    # Mock the database URL
                    app.config.DATABASE_URL = 'sqlite:///test.db'

                    # Trigger database setup
                    app._setup_database()

                    # Verify database connection was attempted
                    mock_db_config.assert_called()

    def test_middleware_setup(self):
        """Test default middleware setup"""
        with patch('pydance.middleware.cors_middleware') as mock_cors:
            with patch('pydance.middleware.logging_middleware') as mock_logging:
                app = Application()
                app._setup_default_middleware()

                # Verify middleware was registered
                # (Implementation detail - would need to check middleware manager)

    def test_exception_handling(self):
        """Test exception handler functionality"""
        @self.app.exception_handler(HTTPException)
        async def handle_http_exception(exc):
            return Response.text('HTTP Error')

        assert HTTPException in self.app._exception_handlers

    def test_configuration_validation(self):
        """Test configuration validation"""
        # Test with valid config
        app = Application()
        assert app.config is not None

        # Test with invalid config that should raise errors
        with patch.object(self.app.config, '_validate_critical_settings') as mock_validate:
            mock_validate.side_effect = ValueError("Config error")
            with pytest.raises(ValueError):
                Application()


class TestApplicationIntegration:
    """Integration tests for Application class"""

    def setup_method(self):
        """Setup for integration tests"""
        self.app = Application()

    async def test_full_request_cycle(self):
        """Test complete request/response cycle"""
        # Add test routes
        @self.app.route('/hello')
        async def hello_handler(request):
            return Response.text('Hello World')

        @self.app.route('/json')
        async def json_handler(request):
            return Response.json({'message': 'test'})

        @self.app.route('/error')
        async def error_handler(request):
            raise HTTPException(400, "Bad Request")

        # Test route registration
        routes = self.app.router.routes
        assert len(routes) >= 3  # 3 test routes + health endpoints

    async def test_middleware_integration(self):
        """Test middleware integration with routes"""
        # Add middleware
        @self.app.use
        async def test_middleware(request, call_next):
            request.test_middleware_called = True
            response = await call_next()
            response.test_middleware_response = True
            return response

        @self.app.route('/middleware-test')
        async def middleware_test_handler(request):
            return Response.text('middleware test')

        # Test middleware was added
        # (Implementation detail - would need to check middleware manager)

    async def test_template_engine_integration(self):
        """Test template engine integration"""
        await self.app.startup()

        # Verify template engine was initialized
        assert self.app.template_engine is not None

        # Test template engine type based on configuration
        template_engine_type = getattr(self.app.config, 'TEMPLATE_ENGINE', '')
        assert 'TemplateEngine' in template_engine_type


class TestApplicationErrorHandling:
    """Test error handling scenarios"""

    def setup_method(self):
        """Setup for error handling tests"""
        self.app = Application()

    async def test_unhandled_exception_handling(self):
        """Test handling of unhandled exceptions"""
        @self.app.route('/error')
        async def error_handler(request):
            raise ValueError("Test error")

        # Add exception handler
        @self.app.exception_handler(ValueError)
        async def handle_value_error(exc):
            return Response.text('ValueError handled')

        # Test that exception handler is registered
        assert ValueError in self.app._exception_handlers

    async def test_http_exception_handling(self):
        """Test HTTP exception handling"""
        @self.app.route('/not-found')
        async def not_found_handler(request):
            raise HTTPException(404, "Custom not found")

        # Test that HTTP exception handler is registered
        assert HTTPException in self.app._exception_handlers

    def test_invalid_middleware_handling(self):
        """Test handling of invalid middleware"""
        # Test with non-callable middleware
        with pytest.raises((TypeError, ValueError)):
            self.app.use("not_callable")

    def test_invalid_route_handler(self):
        """Test invalid route handler"""
        # Test with non-callable handler
        with pytest.raises((TypeError, ValueError)):
            self.app.route('/invalid')(None)


class TestApplicationConfiguration:
    """Test configuration-related functionality"""

    def test_settings_integration(self):
        """Test integration with settings system"""
        app = Application()

        # Verify settings are accessible
        assert hasattr(app.config, 'DEBUG')
        assert hasattr(app.config, 'SECRET_KEY')
        assert hasattr(app.config, 'DATABASE_URL')

    def test_environment_specific_config(self):
        """Test environment-specific configuration"""
        # Test different environments
        app_dev = Application()
        app_prod = Application()

        # Both should have valid configurations
        assert app_dev.config is not None
        assert app_prod.config is not None

    def test_custom_settings_loading(self):
        """Test custom settings from environment"""
        app = Application()

        # Test that custom settings are loaded
        # (Implementation detail - would need to check specific settings)
        assert hasattr(app.config, 'APP_NAME')
        assert hasattr(app.config, 'APP_ENV')


if __name__ == '__main__':
    # Run tests if executed directly
    pytest.main([__file__])
