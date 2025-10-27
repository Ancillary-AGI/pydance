"""
Performance tests - refactored and modular.

Tests for performance, load testing, and optimization validation.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock

from pydance.testing.test_utils import PerformanceTester, MockDataGenerator, test_config
from pydance.testing.fixtures import performance_config, load_test_data, benchmark_timer, memory_monitor


class TestApplicationPerformance:
    """Test application performance characteristics"""

    @pytest.mark.asyncio
    async def test_response_time_performance(self, app):
        """Test response time performance"""
        # Add a simple route for performance testing
        async def fast_handler(request):
            from pydance.http.response import Response
            return Response.text("Fast response")

        app.router.add_route('/fast', fast_handler, methods=['GET'])

        # Test response time
        async def make_request(app, path):
            from pydance.http.request import Request

            request = Request(
                method='GET',
                path=path,
                headers={},
                query_params={}
            )

            match_result = app.router.match('GET', path)
            if match_result:
                return await match_result.handler(request)
            return None

        execution_time, _ = await PerformanceTester.time_async_function(
            make_request, app, '/fast'
        )

        # Response should be very fast (< 100ms for simple route)
        assert execution_time < 0.1

    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, test_app):
        """Test handling of concurrent requests"""
        # Add test route
        async def concurrent_handler(request):
            from pydance.http.response import Response
            await asyncio.sleep(0.01)  # Small delay to simulate work
            return Response.text("Concurrent response")

        test_app.router.add_route('/concurrent', concurrent_handler, methods=['GET'])

        # Make concurrent requests
        async def make_request(i):
            from pydance.http.request import Request
            from pydance.http.response import Response

            # Simulate request processing
            request = Request(
                method='GET',
                path='/concurrent',
                headers={},
                query_params={}
            )

            match_result = test_app.router.match('GET', '/concurrent')
            if match_result:
                return await match_result.handler(request)
            return None

        # Make 10 concurrent requests
        tasks = [make_request(i) for i in range(10)]
        start_time = time.time()

        results = await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # All requests should succeed
        assert all(result is not None for result in results)

        # Should handle concurrent requests efficiently
        # (This is a basic test - more sophisticated benchmarking would be needed for production)
        assert total_time < 1.0  # Should complete within 1 second

    def test_route_matching_performance(self, test_app):
        """Test route matching performance"""
        # Add many routes
        for i in range(100):
            async def handler(request):
                from pydance.http.response import Response
                return Response.text(f"Route {i}")

            test_app.router.add_route(f'/route_{i}', handler, methods=['GET'])

        # Test route matching performance
        execution_time, _ = PerformanceTester.time_function(
            test_app.router.match, 'GET', '/route_50'
        )

        # Route matching should be fast (< 10ms)
        assert execution_time < 0.01

    @pytest.mark.asyncio
    async def test_middleware_performance(self, test_app):
        """Test middleware performance impact"""
        # Create lightweight middleware
        class LightweightMiddleware:
            async def process_request(self, request):
                return request

            async def process_response(self, request, response):
                return response

        # Add middleware
        test_app.middleware_manager.add(LightweightMiddleware())

        # Add test route
        async def test_handler(request):
            from pydance.http.response import Response
            return Response.text("Middleware test")

        test_app.router.add_route('/middleware-test', test_handler, methods=['GET'])

        # Test with middleware
        execution_time, _ = await PerformanceTester.time_async_function(
            self._make_request, test_app, '/middleware-test'
        )

        # Should still be fast with middleware
        assert execution_time < 0.05


class TestDatabasePerformance:
    """Test database performance"""

    @pytest.mark.asyncio
    async def test_database_query_performance(self, test_database, test_models):
        """Test database query performance"""
        TestUser, TestProduct = test_models

        # Create test data
        for i in range(100):
            user = TestUser(
                username=f'user_{i}',
                email=f'user_{i}@example.com',
                password='password'
            )
            await user.save()

        # Test query performance
        execution_time, users = await PerformanceTester.time_async_function(
            TestUser.objects.filter, username__startswith='user_'
        )

        # Should query efficiently
        assert execution_time < 0.1
        assert len(users) == 100

    @pytest.mark.asyncio
    async def test_database_bulk_operations_performance(self, test_database, test_models):
        """Test bulk database operations performance"""
        TestUser, TestProduct = test_models

        # Test bulk insert performance
        start_time = time.time()

        users = []
        for i in range(50):
            user = TestUser(
                username=f'bulk_user_{i}',
                email=f'bulk_user_{i}@example.com',
                password='password'
            )
            users.append(user)

        # Bulk save
        for user in users:
            await user.save()

        end_time = time.time()
        bulk_insert_time = end_time - start_time

        # Bulk insert should be reasonably fast
        assert bulk_insert_time < 2.0  # Should complete within 2 seconds


class TestMemoryUsage:
    """Test memory usage and leaks"""

    def test_memory_efficiency(self, test_app):
        """Test memory efficiency of application"""
        with memory_monitor() as monitor:
            # Create and destroy many components
            for i in range(100):
                async def temp_handler(request):
                    from pydance.http.response import Response
                    return Response.text(f"Temp {i}")

                test_app.router.add_route(f'/temp_{i}', temp_handler, methods=['GET'])

        # Memory usage should be reasonable (< 50MB increase)
        memory_mb = monitor.memory_mb
        assert memory_mb < 50  # Should use less than 50MB

    @pytest.mark.asyncio
    async def test_no_memory_leaks(self, test_app):
        """Test for memory leaks in repeated operations"""
        # Record initial memory
        import psutil
        import os
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Perform many operations
        for i in range(50):
            async def temp_handler(request):
                from pydance.http.response import Response
                return Response.text(f"Leak test {i}")

            test_app.router.add_route(f'/leak_test_{i}', temp_handler, methods=['GET'])

            # Simulate request processing
            request = Mock()
            request.method = 'GET'
            request.path = f'/leak_test_{i}'
            request.headers = {}
            request.query_params = {}

            match_result = test_app.router.match('GET', f'/leak_test_{i}')
            if match_result:
                await match_result.handler(request)

        # Check final memory
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 100MB)
        memory_increase_mb = memory_increase / (1024 * 1024)
        assert memory_increase_mb < 100


class TestLoadTesting:
    """Load testing scenarios"""

    @pytest.mark.asyncio
    async def test_high_concurrency_handling(self, test_app):
        """Test handling of high concurrency"""
        # Add test route
        async def load_handler(request):
            from pydance.http.response import Response
            # Simulate some work
            await asyncio.sleep(0.001)
            return Response.text("Load test response")

        test_app.router.add_route('/load-test', load_handler, methods=['GET'])

        # Simulate high concurrency
        async def make_request(i):
            request = Mock()
            request.method = 'GET'
            request.path = '/load-test'
            request.headers = {}
            request.query_params = {}

            match_result = test_app.router.match('GET', '/load-test')
            if match_result:
                return await match_result.handler(request)
            return None

        # Make many concurrent requests
        num_requests = 200
        tasks = [make_request(i) for i in range(num_requests)]

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Calculate throughput
        total_time = end_time - start_time
        throughput = num_requests / total_time

        # Should handle high concurrency reasonably well
        assert throughput > 50  # At least 50 requests per second

        # Most requests should succeed
        successful_requests = sum(1 for result in results if result is not None and not isinstance(result, Exception))
        success_rate = successful_requests / num_requests
        assert success_rate > 0.9  # At least 90% success rate

    def test_function_benchmarking(self):
        """Test function benchmarking utilities"""
        def simple_function():
            return sum(i for i in range(1000))

        # Benchmark the function
        results = PerformanceTester.benchmark_function(simple_function, iterations=100)

        # Should have reasonable performance metrics
        assert results['avg'] > 0
        assert results['min'] <= results['avg'] <= results['max']
        assert results['total'] == sum(results.values()[:4])  # min + max + avg + median


class TestResourceOptimization:
    """Test resource optimization"""

    def test_efficient_data_structures(self):
        """Test efficient use of data structures"""
        # Test list vs set performance for lookups
        large_list = list(range(10000))
        large_set = set(range(10000))

        # Set lookup should be much faster
        list_time, _ = PerformanceTester.time_function(
            lambda: 9999 in large_list
        )
        set_time, _ = PerformanceTester.time_function(
            lambda: 9999 in large_set
        )

        # Set should be significantly faster for lookups
        assert set_time < list_time * 0.1  # At least 10x faster

    @pytest.mark.asyncio
    async def test_async_optimization(self, test_app):
        """Test async operation optimization"""
        # Add async route
        async def async_handler(request):
            from pydance.http.response import Response
            # Simulate async work
            await asyncio.sleep(0.01)
            return Response.text("Async response")

        test_app.router.add_route('/async-test', async_handler, methods=['GET'])

        # Test async performance
        execution_time, _ = await PerformanceTester.time_async_function(
            self._make_request, test_app, '/async-test'
        )

        # Should handle async operations efficiently
        assert execution_time < 0.1


class TestScalability:
    """Test scalability characteristics"""

    def test_route_scalability(self, test_app):
        """Test how well the application scales with many routes"""
        # Add many routes
        for i in range(1000):
            async def handler(request, i=i):
                from pydance.http.response import Response
                return Response.text(f"Route {i}")

            test_app.router.add_route(f'/route_{i}', handler, methods=['GET'])

        # Test that route matching still works efficiently
        execution_time, match_result = PerformanceTester.time_function(
            test_app.router.match, 'GET', '/route_999'
        )

        # Should still be fast even with many routes
        assert execution_time < 0.01
        assert match_result is not None

    @pytest.mark.asyncio
    async def test_middleware_scalability(self, test_app):
        """Test middleware scalability"""
        # Add multiple middleware layers
        for i in range(10):
            class ScalabilityMiddleware:
                async def process_request(self, request):
                    return request

                async def process_response(self, request, response):
                    return response

            test_app.middleware_manager.add(ScalabilityMiddleware())

        # Add test route
        async def test_handler(request):
            from pydance.http.response import Response
            return Response.text("Scalability test")

        test_app.router.add_route('/scalability-test', test_handler, methods=['GET'])

        # Test with many middleware layers
        execution_time, _ = await PerformanceTester.time_async_function(
            self._make_request, test_app, '/scalability-test'
        )

        # Should still be reasonably fast with many middleware layers
        assert execution_time < 0.1


# Additional consolidated performance tests from the other file
@pytest.mark.performance
class TestPerformance:
    """Performance tests - consolidated from tests/performance/test_performance.py"""

    @pytest.fixture
    def perf_app(self):
        """Application for performance testing"""
        from pydance import Application
        app = Application()

        @app.route('/')
        async def home(request):
            return {'message': 'Hello World'}

        @app.route('/json')
        async def json_response(request):
            return {
                'users': [
                    {'id': i, 'name': f'User {i}', 'email': f'user{i}@example.com'}
                    for i in range(100)
                ]
            }

        @app.route('/sync')
        def sync_handler(request):
            time.sleep(0.001)  # Simulate some work
            return {'message': 'Sync response'}

        return app

    def test_route_lookup_performance(self, perf_app, benchmark):
        """Test route lookup performance"""
        def lookup():
            route, params = perf_app.router.find_route('/', 'GET')
            return route, params

        result = benchmark(lookup)
        assert result[0] is not None

    def test_middleware_execution_performance(self, perf_app, benchmark):
        """Test middleware execution performance"""
        @perf_app.middleware
        async def perf_middleware(request, call_next):
            # Add some processing time
            await asyncio.sleep(0.001)
            response = await call_next(request)
            return response

        async def run_middleware_test():
            # Mock request
            mock_request = type('MockRequest', (), {
                'method': 'GET',
                'path': '/',
                'headers': {},
                'state': {}
            })()

            # Execute middleware chain
            response = await perf_app.middleware_manager.execute_http_chain(
                mock_request, lambda r: type('MockResponse', (), {'status_code': 200})()
            )
            return response

        async def benchmark_middleware():
            return await run_middleware_test()

        result = benchmark(lambda: asyncio.run(benchmark_middleware()))
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, perf_app, client):
        """Test concurrent request handling performance"""
        start_time = time.time()

        # Make 100 concurrent requests
        tasks = []
        for i in range(100):
            tasks.append(client.get('/'))

        responses = await asyncio.gather(*tasks)
        end_time = time.time()

        # Verify all responses
        for response in responses:
            assert response.status_code == 200

        total_time = end_time - start_time
        avg_time = total_time / 100

        # Performance assertions
        assert total_time < 5.0  # Should complete within 5 seconds
        assert avg_time < 0.05  # Average response time should be < 50ms

        print(f"Concurrent requests: {len(responses)}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average time: {avg_time:.4f}s")

    def test_memory_usage_growth(self, perf_app):
        """Test memory usage doesn't grow significantly"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Make many requests
        async def make_requests():
            for i in range(1000):
                # Simulate request processing
                route, params = perf_app.router.find_route('/', 'GET')
                assert route is not None

        asyncio.run(make_requests())

        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory

        # Memory growth should be reasonable (< 10MB)
        assert memory_growth < 10 * 1024 * 1024

        print(f"Initial memory: {initial_memory / 1024 / 1024:.2f} MB")
        print(f"Final memory: {final_memory / 1024 / 1024:.2f} MB")
        print(f"Memory growth: {memory_growth / 1024 / 1024:.2f} MB")

    @pytest.mark.slow
    def test_large_payload_handling(self, perf_app, benchmark):
        """Test handling of large payloads"""
        # Create a large response
        large_data = {'data': 'x' * 1000000}  # 1MB response

        @perf_app.route('/large')
        async def large_response(request):
            return large_data

        async def test_large_response():
            # This would normally use the client, but for benchmarking
            # we'll just test the route handler
            route, params = perf_app.router.find_route('/large', 'GET')
            if route:
                # Mock request
                mock_request = type('MockRequest', (), {
                    'method': 'GET',
                    'path': '/large',
                    'headers': {},
                    'state': {}
                })()
                result = await route.handler(mock_request)
                return result
            return None

        async def benchmark_large():
            return await test_large_response()

        result = benchmark(lambda: asyncio.run(benchmark_large()))
        assert result is not None
        assert len(result['data']) == 1000000

    def test_database_connection_pooling(self, benchmark):
        """Test database connection pooling performance"""
        from pydance.db.config import DatabaseConfig

        def create_connections():
            configs = []
            for i in range(10):
                config = DatabaseConfig(f"sqlite:///test_{i}.db")
                configs.append(config)
            return configs

        result = benchmark(create_connections)
        assert len(result) == 10

    @pytest.mark.asyncio
    async def test_websocket_connection_performance(self, perf_app):
        """Test WebSocket connection performance"""
        @perf_app.websocket_route('/perf-ws')
        async def perf_ws_handler(websocket):
            await websocket.accept()
            await websocket.send_json({'status': 'connected'})
            await websocket.close()

        # Test WebSocket route lookup
        def benchmark_ws_lookup():
            route, params = perf_app.router.find_websocket_route('/perf-ws')
            return route

        from pytest import benchmark
        result = benchmark(lambda: benchmark_ws_lookup())
        assert result is not None

    def test_template_rendering_performance(self, benchmark):
        """Test template rendering performance"""
        # This would test template engine performance
        # For now, just benchmark string operations
        def render_template():
            template = "Hello {{name}}! Your ID is {{id}}."
            result = template.replace("{{name}}", "User").replace("{{id}}", "123")
            return result

        result = benchmark(render_template)
        assert "Hello User!" in result
        assert "Your ID is 123" in result

    @pytest.mark.asyncio
    async def test_middleware_chain_performance(self, perf_app, benchmark):
        """Test middleware chain performance"""
        # Add multiple middleware
        for i in range(5):
            @perf_app.middleware
            async def chain_middleware(request, call_next):
                response = await call_next(request)
                return response

        async def run_chain():
            mock_request = type('MockRequest', (), {
                'method': 'GET',
                'path': '/',
                'headers': {},
                'state': {}
            })()

            response = await perf_app.middleware_manager.execute_http_chain(
                mock_request, lambda r: type('MockResponse', (), {'status_code': 200})()
            )
            return response

        async def benchmark_chain():
            return await run_chain()

        result = benchmark(lambda: asyncio.run(benchmark_chain()))
        assert result.status_code == 200


# Helper methods
async def _make_request(self, test_app, path):
    """Helper to make a test request"""
    from pydance.http.request import Request

    request = Request(
        method='GET',
        path=path,
        headers={},
        query_params={}
    )

    match_result = test_app.router.match('GET', path)
    if match_result:
        return await match_result.handler(request)
    return None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
