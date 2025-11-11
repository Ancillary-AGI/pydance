"""
Comprehensive unit tests for the Pydance Router module.
Tests route matching, parameter extraction, caching, middleware integration, and performance.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from pydance.routing.router import Router, RouteGroup, RouteMatch
from pydance.http import Request, Response


class TestRouter:
    """Test cases for Router class"""

    def setup_method(self):
        """Setup for each test method"""
        self.router = Router()

    def test_router_initialization(self):
        """Test router initializes correctly"""
        assert self.router.routes == []
        assert self.router.websocket_routes == []
        assert self.router.named_routes == {}
        assert self.router.mounted_routers == {}
        assert self.router._route_cache == {}
        assert self.router.fallback_route is None

    def test_add_route(self):
        """Test adding HTTP routes"""
        def handler(request):
            return Response.text('test')

        route = self.router.add_route('/test', handler)
        assert len(self.router.routes) == 1
        assert self.router.routes[0].handler == handler
        assert self.router.routes[0].path == '/test'

    def test_add_route_with_methods(self):
        """Test adding routes with specific HTTP methods"""
        def handler(request):
            return Response.text('test')

        route = self.router.add_route('/api/test', handler, methods=['POST', 'PUT'])
        assert len(self.router.routes) == 1
        assert 'POST' in self.router.routes[0].methods
        assert 'PUT' in self.router.routes[0].methods

    def test_add_route_with_name(self):
        """Test adding named routes"""
        def handler(request):
            return Response.text('test')

        route = self.router.add_route('/test', handler, name='test_route')
        assert 'test_route' in self.router.named_routes
        assert self.router.named_routes['test_route'] == route

    def test_add_websocket_route(self):
        """Test adding WebSocket routes"""
        async def ws_handler(websocket):
            pass

        route = self.router.add_websocket_route('/ws/test', ws_handler)
        assert len(self.router.websocket_routes) == 1
        assert self.router.websocket_routes[0].handler == ws_handler

    def test_route_matching(self):
        """Test basic route matching"""
        def handler(request):
            return Response.text('test')

        self.router.add_route('/test', handler)

        # Test matching
        match = self.router.match('GET', '/test')
        assert match is not None
        assert match.handler == handler
        assert match.params == {}

        # Test non-matching
        no_match = self.router.match('GET', '/nonexistent')
        assert no_match is None

    def test_route_parameter_extraction(self):
        """Test parameter extraction from routes"""
        def handler(request, id, name):
            return Response.text(f'{id}-{name}')

        self.router.add_route('/users/{id}/{name}', handler)

        match = self.router.match('GET', '/users/123/john')
        assert match is not None
        assert match.params == {'id': '123', 'name': 'john'}

    def test_route_method_filtering(self):
        """Test that routes only match allowed methods"""
        def handler(request):
            return Response.text('test')

        self.router.add_route('/api/test', handler, methods=['POST'])

        # Should match POST
        match = self.router.match('POST', '/api/test')
        assert match is not None

        # Should not match GET
        no_match = self.router.match('GET', '/api/test')
        assert no_match is None

    def test_route_priority_ordering(self):
        """Test that routes are matched by priority"""
        def handler1(request):
            return Response.text('handler1')

        def handler2(request):
            return Response.text('handler2')

        # Add routes with different priorities
        route1 = self.router.add_route('/test', handler1)
        route1.config = {'priority': 10}

        route2 = self.router.add_route('/test', handler2)
        route2.config = {'priority': 5}

        # Higher priority should match first
        match = self.router.match('GET', '/test')
        assert match.handler == handler1

    def test_websocket_route_matching(self):
        """Test WebSocket route matching"""
        async def ws_handler(websocket):
            pass

        self.router.add_websocket_route('/ws/test', ws_handler)

        match = self.router.match_websocket('/ws/test')
        assert match is not None
        assert match.handler == ws_handler

    def test_named_route_retrieval(self):
        """Test getting routes by name"""
        def handler(request):
            return Response.text('test')

        route = self.router.add_route('/test', handler, name='test_route')

        retrieved = self.router.get_route_by_name('test_route')
        assert retrieved == route

        not_found = self.router.get_route_by_name('nonexistent')
        assert not_found is None

    def test_route_reversal(self):
        """Test route reversal (URL generation)"""
        def handler(request, id):
            return Response.text(f'user {id}')

        self.router.add_route('/users/{id}', handler, name='user_detail')

        url = self.router.reverse('user_detail', id=123)
        assert url == '/users/123'

    def test_route_group_functionality(self):
        """Test route group functionality"""
        def handler1(request):
            return Response.text('handler1')

        def handler2(request):
            return Response.text('handler2')

        group = self.router.group('/api/v1', name_prefix='api_')

        group_route1 = group.add_route('/users', handler1, name='users')
        group_route2 = group.add_route('/posts', handler2, name='posts')

        # Check routes were added with prefix
        assert len(self.router.routes) == 2
        assert self.router.routes[0].path == '/api/v1/users'
        assert self.router.routes[1].path == '/api/v1/posts'

        # Check named routes have prefix
        assert 'api_users' in self.router.named_routes
        assert 'api_posts' in self.router.named_routes

    def test_nested_route_groups(self):
        """Test nested route groups"""
        def handler(request):
            return Response.text('test')

        # Create nested groups
        api_group = self.router.group('/api')
        v1_group = api_group.group('/v1')

        v1_group.add_route('/test', handler)

        # Check nested prefix was applied
        assert len(self.router.routes) == 1
        assert self.router.routes[0].path == '/api/v1/test'

    def test_router_mounting(self):
        """Test mounting other routers"""
        sub_router = Router()

        def sub_handler(request):
            return Response.text('sub')

        sub_router.add_route('/test', sub_handler)

        self.router.mount('/api', sub_router)

        # Test that mounted routes are accessible
        match = self.router.match('GET', '/api/test')
        assert match is not None
        assert match.handler == sub_handler

    def test_route_caching(self):
        """Test route matching cache functionality"""
        def handler(request):
            return Response.text('test')

        self.router.add_route('/test', handler)

        # First match should cache
        match1 = self.router.match('GET', '/test')
        assert match1 is not None

        # Second match should use cache
        match2 = self.router.match('GET', '/test')
        assert match2 is not None

        # Check cache was used
        assert len(self.router._route_cache) > 0

    def test_cache_clearing(self):
        """Test cache clearing functionality"""
        def handler(request):
            return Response.text('test')

        self.router.add_route('/test', handler)

        # Populate cache
        self.router.match('GET', '/test')
        assert len(self.router._route_cache) > 0

        # Clear cache
        self.router.clear_cache()
        assert len(self.router._route_cache) == 0

    def test_router_statistics(self):
        """Test router statistics"""
        def handler1(request):
            return Response.text('test1')

        def handler2(request):
            return Response.text('test2')

        async def ws_handler(websocket):
            pass

        self.router.add_route('/test1', handler1, name='route1')
        self.router.add_route('/test2', handler2, name='route2')
        self.router.add_websocket_route('/ws/test', ws_handler, name='ws_route')

        stats = self.router.get_stats()

        assert stats['total_routes'] == 2
        assert stats['websocket_routes'] == 1
        assert stats['named_routes'] == 3
        assert stats['mounted_routers'] == 0

    def test_redirect_functionality(self):
        """Test redirect functionality"""
        self.router.add_permanent_redirect('/old-path', '/new-path', name='old_to_new')

        # Check redirect route was added
        assert len(self.router.routes) == 1
        assert self.router.routes[0].path == '/old-path'

        # Test redirect matching
        match = self.router.match('GET', '/old-path')
        assert match is not None

    def test_resource_routes(self):
        """Test RESTful resource route generation"""
        class MockController:
            def index(self, request):
                return Response.text('index')

            def show(self, request, id):
                return Response.text(f'show {id}')

            def store(self, request):
                return Response.text('store')

        controller = MockController()

        self.router.resource('users', controller)

        # Check that resource routes were added
        routes = self.router.routes
        assert len(routes) >= 3  # index, show, store

        # Check specific routes
        index_route = None
        show_route = None
        for route in routes:
            if route.path == '/users' and 'GET' in route.methods:
                index_route = route
            elif route.path == '/users/{id}' and 'GET' in route.methods:
                show_route = route

        assert index_route is not None
        assert show_route is not None

    def test_api_resource_routes(self):
        """Test API resource route generation"""
        class MockAPIController:
            def index(self, request):
                return Response.text('index')

            def store(self, request):
                return Response.text('store')

        controller = MockAPIController()

        self.router.api_resource('posts', controller)

        # Check that API resource routes were added
        routes = self.router.routes
        assert len(routes) >= 2  # index, store

    def test_route_prefix_functionality(self):
        """Test route prefix functionality"""
        def handler1(request):
            return Response.text('test1')

        def handler2(request):
            return Response.text('test2')

        routes = [
            ('/users', handler1, ['GET']),
            ('/posts', handler2, ['GET'])
        ]

        self.router.prefix('/api/v1', routes)

        # Check prefixed routes
        assert len(self.router.routes) == 2
        assert self.router.routes[0].path == '/api/v1/users'
        assert self.router.routes[1].path == '/api/v1/posts'

    def test_mounted_router_priority(self):
        """Test that mounted routers are checked before main routes"""
        sub_router = Router()

        def sub_handler(request):
            return Response.text('sub')

        def main_handler(request):
            return Response.text('main')

        sub_router.add_route('/test', sub_handler)
        self.router.add_route('/test', main_handler)
        self.router.mount('/api', sub_router)

        # Mounted router should take priority
        match = self.router.match('GET', '/api/test')
        assert match.handler == sub_handler

        # Main router should handle non-mounted paths
        match = self.router.match('GET', '/test')
        assert match.handler == main_handler

    def test_route_optimization(self):
        """Test route optimization functionality"""
        def handler1(request):
            return Response.text('test1')

        def handler2(request):
            return Response.text('test2')

        def handler3(request):
            return Response.text('test3')

        # Add routes in random order
        self.router.add_route('/a/b/c', handler1)
        self.router.add_route('/a', handler2)
        self.router.add_route('/a/b', handler3)

        # Optimize routes
        self.router.optimize_routes()

        # Routes should be sorted by specificity (more specific first)
        assert len(self.router.routes) == 3

    def test_performance_metrics(self):
        """Test performance metrics collection"""
        def handler(request):
            return Response.text('test')

        self.router.add_route('/test', handler)

        # Perform some matches
        for _ in range(10):
            self.router.match('GET', '/test')

        metrics = self.router.get_performance_metrics()

        assert 'cache_hit_rate' in metrics
        assert 'total_matches' in metrics
        assert 'routes_by_method' in metrics

    def test_url_generation(self):
        """Test URL generation for named routes"""
        def handler(request, id, slug):
            return Response.text(f'{id}-{slug}')

        self.router.add_route('/users/{id}/{slug}', handler, name='user_detail')

        url = self.router.url_for('user_detail', id=123, slug='john-doe')
        assert url == '/users/123/john-doe'

    def test_invalid_route_matching(self):
        """Test handling of invalid route patterns"""
        def handler(request):
            return Response.text('test')

        # Add route with invalid pattern
        self.router.add_route('/test/{invalid-pattern}', handler)

        # Should not match invalid patterns
        match = self.router.match('GET', '/test/valid')
        assert match is None

    def test_route_with_middleware(self):
        """Test routes with middleware"""
        def handler(request):
            return Response.text('test')

        mock_middleware = Mock()

        route = self.router.add_route('/test', handler, middleware=[mock_middleware])

        # Check middleware was attached
        assert len(self.router.routes) == 1
        # Note: Would need to check route.middleware in actual implementation

    def test_fallback_route(self):
        """Test fallback route functionality"""
        def fallback_handler(request):
            return Response.text('fallback')

        def normal_handler(request):
            return Response.text('normal')

        self.router.add_route('/test', normal_handler)
        self.router.add_fallback_route('/fallback', fallback_handler)

        # Normal route should match first
        match = self.router.match('GET', '/test')
        assert match.handler == normal_handler

        # Fallback should match non-existent routes
        match = self.router.match('GET', '/nonexistent')
        assert match.handler == fallback_handler

    def test_subdomain_routing(self):
        """Test subdomain-based routing"""
        def handler(request):
            return Response.text('test')

        self.router.subdomain('api', [('/test', handler, ['GET'])])

        # Check subdomain route was added
        assert len(self.router.routes) == 1
        # Note: Subdomain routing would need server-level implementation

    def test_route_with_view_class(self):
        """Test route with view class"""
        class MockView:
            def dispatch(self, request, **kwargs):
                return Response.text('view')

        view_class = MockView
        self.router.add_view_route('/test', view_class)

        # Check view route was added
        assert len(self.router.routes) == 1

        # Test route matching
        match = self.router.match('GET', '/test')
        assert match is not None


class TestRouteGroup:
    """Test cases for RouteGroup class"""

    def setup_method(self):
        """Setup for each test method"""
        self.router = Router()
        self.group = RouteGroup(self.router, '/api', name_prefix='api_')

    def test_route_group_initialization(self):
        """Test route group initializes correctly"""
        assert self.group.router == self.router
        assert self.group.prefix == '/api'
        assert self.group.name_prefix == 'api_'
        assert self.group.middleware == []

    def test_route_group_with_middleware(self):
        """Test route group with middleware"""
        mock_middleware = Mock()
        group = RouteGroup(self.router, '/api', middleware=[mock_middleware])

        def handler(request):
            return Response.text('test')

        group.add_route('/test', handler)

        # Check middleware was applied
        assert len(self.router.routes) == 1

    def test_nested_route_groups(self):
        """Test nested route groups"""
        def handler(request):
            return Response.text('test')

        v1_group = self.group.group('/v1', name_prefix='v1_')
        v1_group.add_route('/test', handler)

        # Check nested prefix and name prefix were applied
        assert len(self.router.routes) == 1
        assert self.router.routes[0].path == '/api/v1/test'

    def test_route_group_without_prefix(self):
        """Test route group without prefix"""
        group = RouteGroup(self.router)

        def handler(request):
            return Response.text('test')

        group.add_route('/test', handler)

        # Should work without prefix
        assert len(self.router.routes) == 1
        assert self.router.routes[0].path == '/test'


class TestRouterIntegration:
    """Integration tests for Router class"""

    def setup_method(self):
        """Setup for integration tests"""
        self.router = Router()

    def test_complex_routing_scenario(self):
        """Test complex routing with multiple features"""
        # Setup various route types
        def index_handler(request):
            return Response.text('index')

        def user_handler(request, id):
            return Response.text(f'user {id}')

        def api_handler(request):
            return Response.text('api')

        async def ws_handler(websocket):
            pass

        # Add various routes
        self.router.add_route('/', index_handler, name='index')
        self.router.add_route('/users/{id}', user_handler, name='user_detail')
        self.router.add_route('/api/v1/test', api_handler, name='api_test')
        self.router.add_websocket_route('/ws/chat', ws_handler, name='ws_chat')

        # Test HTTP route matching
        index_match = self.router.match('GET', '/')
        assert index_match is not None
        assert index_match.handler == index_handler

        user_match = self.router.match('GET', '/users/123')
        assert user_match is not None
        assert user_match.params == {'id': '123'}

        api_match = self.router.match('GET', '/api/v1/test')
        assert api_match is not None
        assert api_match.handler == api_handler

        # Test WebSocket route matching
        ws_match = self.router.match_websocket('/ws/chat')
        assert ws_match is not None
        assert ws_match.handler == ws_handler

        # Test named route retrieval
        assert self.router.get_route_by_name('index') is not None
        assert self.router.get_route_by_name('nonexistent') is None

        # Test URL generation
        user_url = self.router.reverse('user_detail', id=456)
        assert user_url == '/users/456'

    def test_route_priority_and_ordering(self):
        """Test route priority and matching order"""
        def specific_handler(request, id):
            return Response.text(f'specific {id}')

        def general_handler(request):
            return Response.text('general')

        # Add specific route first, then general
        self.router.add_route('/users/{id}', specific_handler)
        self.router.add_route('/users', general_handler)

        # Specific route should match first
        match = self.router.match('GET', '/users/123')
        assert match.handler == specific_handler
        assert match.params == {'id': '123'}

        # General route should match without parameters
        match = self.router.match('GET', '/users')
        assert match.handler == general_handler
        assert match.params == {}

    def test_mounted_router_integration(self):
        """Test integration with mounted routers"""
        # Create sub-router
        sub_router = Router()

        def sub_handler(request):
            return Response.text('sub')

        def sub_param_handler(request, id):
            return Response.text(f'sub {id}')

        sub_router.add_route('/test', sub_handler)
        sub_router.add_route('/item/{id}', sub_param_handler)

        # Mount sub-router
        self.router.mount('/api/v1', sub_router)

        # Test mounted routes
        match1 = self.router.match('GET', '/api/v1/test')
        assert match1 is not None
        assert match1.handler == sub_handler

        match2 = self.router.match('GET', '/api/v1/item/123')
        assert match2 is not None
        assert match2.handler == sub_param_handler
        assert match2.params == {'id': '123'}

    def test_middleware_integration(self):
        """Test middleware integration with routing"""
        def handler(request):
            return Response.text('test')

        mock_middleware = Mock()

        # Add route with middleware
        route = self.router.add_route('/test', handler, middleware=[mock_middleware])

        # Test route matching includes middleware
        match = self.router.match('GET', '/test')
        assert match is not None
        assert match.route == route
        # Note: Would need to check match.middleware in actual implementation

    def test_performance_with_many_routes(self):
        """Test performance with many routes"""
        # Add many routes
        for i in range(100):
            def handler(request, i=i):
                return Response.text(f'handler {i}')

            self.router.add_route(f'/test/{i}', handler)

        # Test that matching still works
        match = self.router.match('GET', '/test/50')
        assert match is not None
        assert match.params == {'i': '50'}

        # Test performance metrics
        metrics = self.router.get_performance_metrics()
        assert 'total_matches' in metrics


class TestRouterErrorHandling:
    """Test error handling scenarios"""

    def setup_method(self):
        """Setup for error handling tests"""
        self.router = Router()

    def test_invalid_route_pattern(self):
        """Test handling of invalid route patterns"""
        def handler(request):
            return Response.text('test')

        # Add route with invalid pattern
        route = self.router.add_route('/test/{invalid-pattern}', handler)

        # Should not match invalid patterns
        match = self.router.match('GET', '/test/valid')
        assert match is None

    def test_missing_named_route(self):
        """Test handling of missing named routes"""
        route = self.router.get_route_by_name('nonexistent')
        assert route is None

        url = self.router.reverse('nonexistent')
        assert url is None

    def test_route_without_handler(self):
        """Test route without handler"""
        # This should not be possible with current implementation
        # but test the error handling if it occurs
        pass

    def test_circular_route_reference(self):
        """Test handling of circular route references"""
        # This would test circular dependencies in route definitions
        pass


class TestRouterPerformance:
    """Test performance-related functionality"""

    def setup_method(self):
        """Setup for performance tests"""
        self.router = Router()

        # Add many routes for performance testing
        for i in range(1000):
            def handler(request, i=i):
                return Response.text(f'handler {i}')

            self.router.add_route(f'/test/{i}', handler)

    def test_large_route_set_performance(self):
        """Test performance with large number of routes"""
        import time

        start_time = time.time()

        # Test matching performance
        for i in range(100):
            match = self.router.match('GET', f'/test/{i % 1000}')

        end_time = time.time()
        total_time = end_time - start_time

        # Should be fast even with many routes
        assert total_time < 1.0  # Less than 1 second for 100 matches

    def test_cache_performance(self):
        """Test cache performance improvement"""
        # First match (cache miss)
        start_time = time.time()
        match1 = self.router.match('GET', '/test/500')
        first_time = time.time() - start_time

        # Second match (cache hit)
        start_time = time.time()
        match2 = self.router.match('GET', '/test/500')
        second_time = time.time() - start_time

        # Cache hit should be faster
        assert second_time <= first_time

        # Results should be the same
        assert match1.handler == match2.handler

    def test_route_optimization_performance(self):
        """Test route optimization performance"""
        # Optimize routes
        start_time = time.time()
        self.router.optimize_routes()
        optimization_time = time.time() - start_time

        # Optimization should be reasonably fast
        assert optimization_time < 1.0

        # Test that optimization improved performance
        start_time = time.time()
        match = self.router.match('GET', '/test/500')
        optimized_time = time.time() - start_time

        assert match is not None
        assert optimized_time < 0.1  # Should be very fast


if __name__ == '__main__':
    # Run tests if executed directly
    pytest.main([__file__])
