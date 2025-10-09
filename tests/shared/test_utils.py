"""
Shared test utilities for both frontend and backend testing.

This module provides common test utilities, fixtures, and helpers
that can be used across all test files to reduce duplication and
improve maintainability.
"""

import asyncio
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, AsyncGenerator
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Test data factories
class TestDataFactory:
    """Factory for creating test data across different models"""

    @staticmethod
    def create_user_data(username: str = None, email: str = None, **kwargs) -> Dict[str, Any]:
        """Create test user data"""
        return {
            'username': username or f'testuser_{datetime.now().timestamp()}',
            'email': email or f'test_{datetime.now().timestamp()}@example.com',
            'password': kwargs.get('password', 'testpass123'),
            'is_active': kwargs.get('is_active', True),
            'created_at': kwargs.get('created_at', datetime.now()),
            **kwargs
        }

    @staticmethod
    def create_product_data(name: str = None, price: float = None, **kwargs) -> Dict[str, Any]:
        """Create test product data"""
        return {
            'name': name or f'Test Product {datetime.now().timestamp()}',
            'price': price or 29.99,
            'category': kwargs.get('category', 'test'),
            'in_stock': kwargs.get('in_stock', True),
            'created_at': kwargs.get('created_at', datetime.now()),
            **kwargs
        }

    @staticmethod
    def create_http_request(method: str = 'GET', path: str = '/', **kwargs) -> Mock:
        """Create mock HTTP request"""
        request = Mock()
        request.method = method
        request.path = path
        request.headers = kwargs.get('headers', {})
        request.query_params = kwargs.get('query_params', {})
        request.body = kwargs.get('body', b'')
        request.json = kwargs.get('json_data', {})
        return request

# Test assertions and helpers
class TestAssertions:
    """Custom test assertions and helpers"""

    @staticmethod
    def assert_is_valid_json(response_text: str):
        """Assert that response is valid JSON"""
        try:
            json.loads(response_text)
        except json.JSONDecodeError as e:
            raise AssertionError(f"Response is not valid JSON: {e}")

    @staticmethod
    def assert_has_required_fields(data: Dict[str, Any], required_fields: List[str]):
        """Assert that data has all required fields"""
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise AssertionError(f"Missing required fields: {missing_fields}")

    @staticmethod
    def assert_datetime_recent(dt: datetime, seconds: int = 60):
        """Assert that datetime is recent (within specified seconds)"""
        now = datetime.now()
        time_diff = abs((now - dt).total_seconds())
        if time_diff > seconds:
            raise AssertionError(f"Datetime {dt} is not recent (diff: {time_diff}s)")

# Async test helpers
class AsyncTestHelper:
    """Helpers for async testing"""

    @staticmethod
    async def wait_for_condition(condition_func, timeout: float = 5.0, interval: float = 0.1):
        """Wait for a condition to be true"""
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                if await condition_func():
                    return True
            except Exception:
                pass
            await asyncio.sleep(interval)

        raise TimeoutError(f"Condition not met within {timeout} seconds")

    @staticmethod
    async def gather_with_timeout(tasks, timeout: float = 10.0):
        """Gather tasks with timeout"""
        try:
            return await asyncio.wait_for(asyncio.gather(*tasks), timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Tasks did not complete within {timeout} seconds")

# Performance testing utilities
class PerformanceTester:
    """Utilities for performance testing"""

    @staticmethod
    def time_function(func, *args, **kwargs) -> float:
        """Time a function execution"""
        import time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return end_time - start_time, result

    @staticmethod
    async def time_async_function(func, *args, **kwargs) -> float:
        """Time an async function execution"""
        import time
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        return end_time - start_time, result

    @staticmethod
    def benchmark_function(func, iterations: int = 100, *args, **kwargs) -> Dict[str, float]:
        """Benchmark a function over multiple iterations"""
        import time
        import statistics

        times = []
        for _ in range(iterations):
            start_time = time.time()
            func(*args, **kwargs)
            end_time = time.time()
            times.append(end_time - start_time)

        return {
            'min': min(times),
            'max': max(times),
            'avg': statistics.mean(times),
            'median': statistics.median(times),
            'total': sum(times)
        }

# Mock data generators
class MockDataGenerator:
    """Generate mock data for testing"""

    @staticmethod
    def generate_users(count: int = 10) -> List[Dict[str, Any]]:
        """Generate mock user data"""
        users = []
        for i in range(count):
            users.append(TestDataFactory.create_user_data(
                username=f'user{i}',
                email=f'user{i}@example.com'
            ))
        return users

    @staticmethod
    def generate_products(count: int = 10) -> List[Dict[str, Any]]:
        """Generate mock product data"""
        products = []
        categories = ['electronics', 'books', 'clothing', 'home', 'sports']

        for i in range(count):
            products.append(TestDataFactory.create_product_data(
                name=f'Product {i}',
                price=round(10 + (i * 5.5), 2),
                category=categories[i % len(categories)]
            ))
        return products

    @staticmethod
    def generate_http_requests(count: int = 10) -> List[Mock]:
        """Generate mock HTTP requests"""
        requests = []
        methods = ['GET', 'POST', 'PUT', 'DELETE']
        paths = ['/', '/api/users', '/api/products', '/api/orders']

        for i in range(count):
            requests.append(TestDataFactory.create_http_request(
                method=methods[i % len(methods)],
                path=paths[i % len(paths)],
                headers={'User-Agent': f'TestAgent/{i}'}
            ))
        return requests

# Test configuration
class TestConfig:
    """Test configuration management"""

    def __init__(self):
        self.test_database_url = os.getenv('TEST_DATABASE_URL', 'sqlite:///:memory:')
        self.test_redis_url = os.getenv('TEST_REDIS_URL', 'redis://localhost:6379/1')
        self.test_timeout = int(os.getenv('TEST_TIMEOUT', '30'))
        self.test_parallel = os.getenv('TEST_PARALLEL', 'false').lower() == 'true'
        self.test_verbose = os.getenv('TEST_VERBOSE', 'false').lower() == 'true'

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration for tests"""
        return {
            'url': self.test_database_url,
            'pool_size': 5,
            'timeout': 10
        }

    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration for tests"""
        return {
            'url': self.test_redis_url,
            'ttl': 300
        }

# Global test configuration instance
test_config = TestConfig()

__all__ = [
    'TestDataFactory',
    'TestAssertions',
    'AsyncTestHelper',
    'PerformanceTester',
    'MockDataGenerator',
    'TestConfig',
    'test_config'
]
